"""Frozen, chronological regularized history-choice predictors.

This module never opens a dataset. Callers supply trials explicitly. Fits are
penalized joint modes, not marginal likelihoods. Unseen-person predictions
integrate a fixed Gaussian residual-coefficient distribution using quadrature.
Only participant-visible contrast and PAST response/feedback enter predictors.
Hidden stimulus-side or probability columns are never used to build a design.
"""
from dataclasses import dataclass, asdict
from pathlib import Path
import json
from typing import Optional

import numpy as np
import pandas as pd
from numpy.polynomial.hermite import hermgauss
from scipy.optimize import minimize
from scipy.special import expit


CALIBRATION_NAMES = ('sensory_first100', 'sensory_second100', 'response_bias_first200', 'omission_first200')
NUISANCE_NAMES = ('intercept', 'contrast_0.1', 'contrast_0.25', 'contrast_0.5', 'contrast_1', 'previous_choice', 'later_time', 'sensory_time')
HISTORY_NAMES = ('history_tau2', 'history_tau8', 'history_tau32')


@dataclass
class ModelConfig:
    taus: tuple = (2., 8., 32.)
    random_sd: float = 0.7
    fixed_sd: float = 2.0
    intercept_sd: float = 3.0
    interaction_sd: float = 1.0
    condition_history_sd: float = 1.0
    fit_start: int = 200
    fit_end: int = 600
    gh_nodes: int = 20
    maxiter: int = 1200
    ftol: float = 1e-14
    gtol: float = 1e-5
    gradient_tolerance: float = 1e-3
    asymmetric_saturation: bool = False


@dataclass
class FeatureData:
    rows: pd.DataFrame
    nuisance: np.ndarray
    history: np.ndarray
    calibration: np.ndarray
    calibration_raw: pd.DataFrame
    calibration_transform: dict
    group: np.ndarray
    y: np.ndarray
    responded: np.ndarray
    subject_codes: np.ndarray
    subjects: list
    config: ModelConfig


@dataclass
class FitResult:
    variant: str
    beta: np.ndarray
    random_effects: np.ndarray
    subjects: list
    feature_names: list
    random_names: list
    config: ModelConfig
    calibration_transform: dict
    diagnostics: dict

    def to_dict(self):
        return dict(variant=self.variant, beta=self.beta.tolist(),
                    random_effects=self.random_effects.tolist(), subjects=self.subjects,
                    feature_names=self.feature_names, random_names=self.random_names,
                    config=asdict(self.config), calibration_transform=self.calibration_transform,
                    diagnostics=self.diagnostics)

    def save(self, path):
        Path(path).write_text(json.dumps(self.to_dict(), indent=2) + '\n')

    @classmethod
    def load(cls, path):
        obj = json.loads(Path(path).read_text())
        obj['beta'] = np.asarray(obj['beta'], float)
        obj['random_effects'] = np.asarray(obj['random_effects'], float)
        obj['config'] = ModelConfig(**obj['config'])
        return cls(**obj)


def _calibration_one(s):
    choice = s.choice.to_numpy(float)
    contrast = s.sideContrast.to_numpy(float)
    trial = s.trial.to_numpy(int)
    responded = np.isin(choice, [-1., 1.])
    vals = []
    for a, b in ((0, 100), (100, 200)):
        mask = (trial >= a) & (trial < b) & responded & (contrast != 0)
        # Empty halves get neutral association; omission conveys absent evidence.
        vals.append(float(np.mean(choice[mask] * np.sign(contrast[mask]))) if mask.any() else 0.)
    early = trial < 200
    good = early & responded
    vals += [float(choice[good].mean()) if good.any() else 0., float(1. - responded[early].mean())]
    return vals


def prepare_features(frame, calibration_transform=None, config=None):
    """Build chronological features for complete participant sequences.

    Pass the DEVELOPMENT ``calibration_transform`` for every validation call.
    If omitted, it is estimated from supplied subjects, so callers must supply
    development subjects only in that case. Covariates are centered but not
    rescaled; their natural association/rate units are fixed across cohorts.
    All persons must include the entire 0..199 calibration interval. Choices
    after 199 never affect C, and current/future choices never affect history.
    """
    config = config or ModelConfig()
    required = ['subject', 'trial', 'instructions', 'sideContrast', 'choice', 'feedbackType']
    missing = set(required) - set(frame.columns)
    if missing:
        raise ValueError(f'Missing columns: {sorted(missing)}')
    rows = frame.copy()
    rows['subject'] = rows.subject.astype(str)
    rows = rows.sort_values(['subject', 'trial'], kind='stable').reset_index(drop=True)
    if rows.duplicated(['subject', 'trial']).any():
        raise ValueError('Duplicate subject/trial')
    subjects = sorted(rows.subject.unique().tolist())
    raw = []
    history = np.zeros((len(rows), 3), float)
    previous_choice = np.zeros(len(rows), float)
    decay = np.exp(-1. / np.asarray(config.taus, float))
    for subject, s in rows.groupby('subject', sort=True):
        trial = s.trial.to_numpy(int)
        if not np.array_equal(trial, np.arange(len(s))):
            raise ValueError(f'{subject}: require complete chronological sequence from trial 0')
        if len(s) < 200:
            raise ValueError(f'{subject}: incomplete first200 calibration')
        if s.instructions.nunique() != 1 or not s.instructions.isin([0, 1]).all():
            raise ValueError(f'{subject}: invalid condition')
        raw.append([subject] + _calibration_one(s))
        ch = s.choice.to_numpy(float)
        fb = s.feedbackType.to_numpy(float)
        indices = s.index.to_numpy()
        hist = np.zeros(3, float)
        prev = 0.
        for j, idx in enumerate(indices):
            history[idx] = hist
            previous_choice[idx] = prev
            valid_ch = ch[j] in (-1., 1.)
            valid_feedback = valid_ch and fb[j] in (-1., 1.)
            evidence = ch[j] * fb[j] if valid_feedback else 0.
            hist = decay * hist + (1. - decay) * evidence
            prev = ch[j] if valid_ch else 0.
    raw = pd.DataFrame(raw, columns=['subject'] + list(CALIBRATION_NAMES))
    if calibration_transform is None:
        center = raw[list(CALIBRATION_NAMES)].mean().to_numpy(float)
        calibration_transform = dict(names=list(CALIBRATION_NAMES), center=center.tolist(),
                                     scale=[1.] * 4, source_subjects=subjects,
                                     convention='development-subject mean centering; fixed natural units')
    else:
        if calibration_transform['names'] != list(CALIBRATION_NAMES):
            raise ValueError('Calibration transform schema mismatch')
        center = np.asarray(calibration_transform['center'], float)
    raw_indexed = raw.set_index('subject')
    cal = raw_indexed.loc[rows.subject, list(CALIBRATION_NAMES)].to_numpy(float)
    cal = (cal - center) / np.asarray(calibration_transform['scale'], float)
    c = rows.sideContrast.to_numpy(float)
    sign = np.sign(c)
    time = (rows.trial.to_numpy(float) - 399.5) / 200.
    nuisance = np.column_stack([np.ones(len(rows))] +
        [sign * np.isclose(np.abs(c), level, rtol=0., atol=1e-8) for level in (.1, .25, .5, 1.)] +
        [previous_choice, time, sign * time])
    if config.asymmetric_saturation:
        nuisance = np.column_stack([nuisance] +
            [np.isclose(np.abs(c), level, rtol=0., atol=1e-8).astype(float) for level in (.1, .25, .5, 1.)])
    if not np.isfinite(nuisance).all() or not np.isfinite(cal).all():
        raise ValueError('Nonfinite feature values')
    choice = rows.choice.to_numpy(float)
    codes = pd.Categorical(rows.subject, categories=subjects).codes
    return FeatureData(rows=rows, nuisance=nuisance, history=history, calibration=cal,
                       calibration_raw=raw, calibration_transform=calibration_transform,
                       group=rows.instructions.to_numpy(float) - .5,
                       y=(choice == 1.).astype(float), responded=np.isin(choice, [-1., 1.]),
                       subject_codes=codes, subjects=subjects, config=config)


def build_design(features, variant='shared', config=None, adaptation_group_override=None):
    """Return X, Z, fixed names, random names and fixed-effect prior SDs.

    ``adaptation_group_override`` takes condition code 0 or 1 and changes ONLY
    the three condition-history columns; sensory/bias/acquisition nuisance
    values remain untouched. This supports an observable standardized contrast.
    """
    if variant not in ('shared', 'condition', 'no_history'):
        raise ValueError(variant)
    cfg = config or features.config
    if tuple(cfg.taus) != tuple(features.config.taus) or cfg.asymmetric_saturation != features.config.asymmetric_saturation:
        raise ValueError('Feature configuration differs; prepare features with this model configuration')
    n, h, c, g = features.nuisance, features.history, features.calibration, features.group
    nuisance_names = list(NUISANCE_NAMES)
    if cfg.asymmetric_saturation:
        nuisance_names += ['abscontrast_0.1', 'abscontrast_0.25', 'abscontrast_0.5', 'abscontrast_1']
    chunks = [n, n * g[:, None]]
    names = nuisance_names + ['condition:' + x for x in nuisance_names]
    priors = [cfg.fixed_sd] * (2 * n.shape[1])
    priors[0] = cfg.intercept_sd
    for k, cname in enumerate(CALIBRATION_NAMES):
        chunks.append(n * c[:, k, None])
        names.extend([cname + ':' + x for x in nuisance_names])
        priors.extend([cfg.interaction_sd] * n.shape[1])
    random = [n[:, 0], np.sign(features.rows.sideContrast.to_numpy(float))]
    random_names = ['intercept', 'sensory_sign']
    if variant != 'no_history':
        chunks.append(h)
        names.extend(HISTORY_NAMES)
        priors.extend([cfg.fixed_sd] * 3)
        for k, cname in enumerate(CALIBRATION_NAMES):
            chunks.append(h * c[:, k, None])
            names.extend([cname + ':' + x for x in HISTORY_NAMES])
            priors.extend([cfg.interaction_sd] * 3)
        random.extend([h[:, j] for j in range(3)])
        random_names.extend(HISTORY_NAMES)
        if variant == 'condition':
            hg = g if adaptation_group_override is None else np.full(len(g), float(adaptation_group_override) - .5)
            chunks.append(h * hg[:, None])
            names.extend(['condition:' + x for x in HISTORY_NAMES])
            priors.extend([cfg.condition_history_sd] * 3)
    return np.column_stack(chunks), np.column_stack(random), names, random_names, np.asarray(priors)


def fit_model(features, variant='shared', config=None, mask=None, initial=None):
    """Penalized joint MAP using later responding trials, analytic gradient.

    ``mask`` may additionally restrict training rows, never expand beyond the
    configured fit interval or include omissions. Fixed Gaussian random SDs are
    part of the prediction procedure, not estimated variance components.
    """
    cfg = config or features.config
    X, Z, names, rnames, sd = build_design(features, variant, cfg)
    trial = features.rows.trial.to_numpy(int)
    use = features.responded & (trial >= cfg.fit_start) & (trial < cfg.fit_end)
    if mask is not None:
        use &= np.asarray(mask, bool)
    X, Z, y, codes = X[use], Z[use], features.y[use], features.subject_codes[use]
    if not len(y):
        raise ValueError('No eligible training responses')
    p, q, ns = X.shape[1], Z.shape[1], len(features.subjects)
    invvar, rinvvar = 1. / sd ** 2, 1. / cfg.random_sd ** 2
    def fun(theta):
        beta, b = theta[:p], theta[p:].reshape(ns, q)
        eta = np.einsum('ij,j->i', X, beta) + np.einsum('ij,ij->i', Z, b[codes])
        val = np.sum(np.logaddexp(0., eta) - y * eta)
        val += .5 * np.sum(beta * beta * invvar) + .5 * rinvvar * np.sum(b * b)
        residual = expit(eta) - y
        gbeta = np.einsum('ij,i->j', X, residual) + beta * invvar
        gb = np.zeros((ns, q), float)
        for j in range(q):
            gb[:, j] = np.bincount(codes, weights=residual * Z[:, j], minlength=ns)
        gb += rinvvar * b
        return float(val), np.concatenate([gbeta, gb.ravel()])
    start = np.zeros(p + ns * q) if initial is None else np.asarray(initial, float)
    if len(start) != p + ns * q:
        raise ValueError('Initial vector wrong size')
    attempts = []
    for attempt in range(3):
        opt = minimize(fun, start, method='L-BFGS-B', jac=True,
                       options=dict(maxiter=cfg.maxiter, ftol=cfg.ftol, gtol=cfg.gtol, maxls=40, maxcor=20))
        value, grad = fun(opt.x)
        attempts.append(dict(success=bool(opt.success), iterations=int(opt.nit), objective=float(value),
                             max_abs_gradient=float(np.max(np.abs(grad)))))
        if np.max(np.abs(grad)) <= cfg.gradient_tolerance:
            break
        start = opt.x.copy()
    quality = bool(np.max(np.abs(grad)) <= cfg.gradient_tolerance)
    diagnostics = dict(success=bool(opt.success and quality), optimizer_success=bool(opt.success),
                       gradient_quality_pass=quality, attempts=attempts,
                       status=int(opt.status), message=str(opt.message),
                       iterations=int(opt.nit), evaluations=int(opt.nfev), objective=float(value),
                       max_abs_gradient=float(np.max(np.abs(grad))), n_responses=int(use.sum()),
                       n_participants=int(len(set(codes.tolist()))), n_fixed=p, n_random_per_person=q,
                       approximation='penalized joint mode; no marginal likelihood used',
                       config=asdict(cfg))
    return FitResult(variant, opt.x[:p], opt.x[p:].reshape(ns, q), features.subjects,
                     names, rnames, cfg, features.calibration_transform, diagnostics)


def predict_model(fit, features, mode='integrated', adaptation_group_override=None):
    """Choice probability, preserving future blindness.

    integrated: population mean plus Gaussian unseen-person residual integrated
      by Gauss-Hermite quadrature, used for reserved participants.
    fixed: population mean only, useful for diagnostics.
    conditional: fitted offsets for training IDs, raises for unseen IDs.
    """
    X, Z, names, rnames, _ = build_design(features, fit.variant, fit.config, adaptation_group_override)
    if names != fit.feature_names or rnames != fit.random_names:
        raise ValueError('Model/design schema mismatch')
    if features.calibration_transform != fit.calibration_transform:
        raise ValueError('Prediction must use the training calibration transform')
    eta = np.einsum('ij,j->i', X, fit.beta)
    if mode == 'fixed':
        return expit(eta)
    if mode == 'conditional':
        lookup = {s: i for i, s in enumerate(fit.subjects)}
        if not set(features.subjects).issubset(lookup):
            raise ValueError('Conditional mode requires fitted participant IDs')
        indices = np.asarray([lookup[s] for s in features.rows.subject])
        eta += np.einsum('ij,ij->i', Z, fit.random_effects[indices])
        return expit(eta)
    if mode != 'integrated':
        raise ValueError(mode)
    variance = fit.config.random_sd ** 2 * np.einsum('ij,ij->i', Z, Z)
    nodes, weights = hermgauss(fit.config.gh_nodes)
    probs = expit(eta[:, None] + np.sqrt(2. * variance)[:, None] * nodes[None, :])
    return np.einsum('ij,j->i', probs, weights) / np.sqrt(np.pi)


def predict_adaptation_contrast(fit, features, mode='integrated'):
    """Return instructed-minus-uninstructed adaptation-only probability shift."""
    if fit.variant != 'condition':
        return np.zeros(len(features.rows))
    return predict_model(fit, features, mode, 1) - predict_model(fit, features, mode, 0)


def log_score(probability, y):
    p = np.clip(np.asarray(probability, float), 1e-12, 1. - 1e-12)
    y = np.asarray(y, float)
    return y * np.log(p) + (1. - y) * np.log1p(-p)
