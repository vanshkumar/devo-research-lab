"""Independent development-only feature/prediction audit.

Does not open raw CSV or validation outcomes. Numerical identities use a
different construction of the causal history and scipy integration.
"""
from pathlib import Path
import sys
import json
import math
import hashlib
import numpy as np
import pandas as pd
from scipy.integrate import quad
from scipy.special import expit

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'experiments'))
import model


def main():
    d = pd.read_csv(ROOT / 'inputs/development_numeric.csv', dtype={'subject': str})
    split = pd.read_csv(ROOT / 'protocol/split_manifest.csv', dtype={'subject': str})
    expected = set(split.loc[split.partition == 'development', 'subject'])
    assert set(d.subject) == expected
    f = model.prepare_features(d)
    independent_h = np.zeros_like(f.history)
    independent_prev = np.zeros(len(f.rows))
    for sid, s in f.rows.groupby('subject'):
        # Explicit weighted past sums, unlike the engine's recursive updates.
        evidence = np.asarray([row.choice * row.feedbackType
                               if row.choice in [-1, 1] and row.feedbackType in [-1, 1]
                               else 0. for row in s.itertuples()])
        ch = s.choice.to_numpy()
        for local, idx in enumerate(s.index):
            for k, tau in enumerate([2., 8., 32.]):
                weights = (1 - math.exp(-1 / tau)) * np.exp(-np.arange(local - 1, -1, -1) / tau)
                independent_h[idx, k] = float(np.sum(weights * evidence[:local]))
            independent_prev[idx] = ch[local - 1] if local and ch[local - 1] in [-1, 1] else 0.
    np.testing.assert_allclose(independent_h, f.history, atol=2e-14, rtol=0)
    np.testing.assert_equal(independent_prev, f.nuisance[:, 5])

    # Strictly prospective for t>=200, including current-row response blindness.
    cutoff = 317
    prefix = d.loc[d.trial <= cutoff].copy()
    fp = model.prepare_features(prefix, f.calibration_transform)
    full_x = model.build_design(f, 'condition')[0]
    prefix_x = model.build_design(fp, 'condition')[0]
    take = f.rows.trial <= cutoff
    np.testing.assert_array_equal(full_x[take], prefix_x)
    changed = d.copy()
    future = changed.trial >= cutoff
    changed.loc[future, 'choice'] = -changed.loc[future, 'choice']
    changed.loc[future, 'feedbackType'] = 1234.
    changed['probabilityLeft'] = np.nan
    changed['stimSide'] = 1234.
    fc = model.prepare_features(changed, f.calibration_transform)
    changed_x = model.build_design(fc, 'condition')[0]
    np.testing.assert_array_equal(full_x[take], changed_x[take])

    # Two starts for each actual development fit; no outcomes printed.
    rng = np.random.default_rng(54283)
    results = {}
    for variant in ['shared', 'condition']:
        fit = model.fit_model(f, variant)
        initial = np.r_[fit.beta, fit.random_effects.ravel()] + rng.normal(0, .25, len(fit.beta) + fit.random_effects.size)
        fit2 = model.fit_model(f, variant, initial=initial)
        p = model.predict_model(fit, f)
        p2 = model.predict_model(fit2, f)
        assert fit.diagnostics['max_abs_gradient'] < .001, fit.diagnostics
        assert fit2.diagnostics['max_abs_gradient'] < .001, fit2.diagnostics
        assert abs(fit.diagnostics['objective'] - fit2.diagnostics['objective']) < 1e-5
        assert np.max(np.abs(p - p2)) < 2e-5
        X, Z, names, _, _ = model.build_design(f, variant)
        eta = np.einsum('ij,j->i', X, fit.beta)
        variance = fit.config.random_sd ** 2 * (Z ** 2).sum(axis=1)
        selected = rng.choice(np.flatnonzero(f.rows.trial >= 200), size=20, replace=False)
        quad_errors = []
        for i in selected:
            independent, _ = quad(lambda z: expit(eta[i] + math.sqrt(variance[i]) * z) * math.exp(-z*z/2) / math.sqrt(2*math.pi), -12, 12, epsabs=1e-12)
            quad_errors.append(abs(independent - p[i]))
        assert max(quad_errors) < 1e-6
        results[variant] = dict(max_gradient=fit.diagnostics['max_abs_gradient'],
                                second_start_max_gradient=fit2.diagnostics['max_abs_gradient'],
                                objective_difference=abs(fit.diagnostics['objective'] - fit2.diagnostics['objective']),
                                max_probability_difference=float(np.max(np.abs(p-p2))),
                                max_quadrature_error=max(quad_errors), n_fixed=len(fit.beta),
                                n_random_per_person=fit.random_effects.shape[1])
    report = dict(passed=True, inspected='Development outcomes only; no validation or raw CSV access',
                  development_subjects=len(expected),
                  model_sha256=hashlib.sha256((ROOT / 'experiments/model.py').read_bytes()).hexdigest(),
                  checks=['explicit lag sum matches all recursive histories', 'previous-choice extraction',
                          'prefix truncation invariance', 'current/future choice and feedback invariance',
                          'hidden label removal invariance', 'two-start convex MAP agreement',
                          'adaptive quadrature matches Gauss-Hermite'], numerical=results)
    Path(__file__).with_name('model_audit_results.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
