"""Synthetic-only checks of causal features, gradients' optimizer and contrasts."""
import json
import tempfile
from pathlib import Path
import numpy as np
import pandas as pd
from scipy.special import expit
from model import (ModelConfig, FitResult, prepare_features, build_design, fit_model,
                   predict_model, predict_adaptation_contrast, log_score)


def synthetic_frame(seed=42, n_subjects=20):
    rng = np.random.default_rng(seed)
    records = []
    for i in range(n_subjects):
        group = i % 2
        side = rng.choice([-1., 1.], 600)
        contrast = side * rng.choice([0., .1, .25, .5, 1.], 600)
        bias = rng.normal(0., .25)
        ch = np.where(rng.random(600) < expit(bias + 2. * np.sign(contrast)), 1., -1.)
        fb = ch * side
        for t in range(600):
            records.append((f'X{i:03d}', t, group, contrast[t], ch[t], fb[t]))
    return pd.DataFrame(records, columns=['subject', 'trial', 'instructions', 'sideContrast', 'choice', 'feedbackType'])


def run():
    frame = synthetic_frame()
    f = prepare_features(frame)
    # EWMA at row zero is blank; next row contains only first-trial feedback.
    assert np.all(f.history[::600] == 0.)
    decay = np.exp(-1. / np.asarray([2., 8., 32.]))
    first = f.rows.iloc[0]
    np.testing.assert_allclose(f.history[1], (1. - decay) * first.choice * first.feedbackType)
    # Current/future responses must not alter a current predictor, and changes
    # after calibration must not alter C. Future hidden labels never enter it.
    altered = frame.copy()
    m = (altered.subject == 'X000') & (altered.trial >= 300)
    altered.loc[m, 'choice'] *= -1
    altered['probabilityLeft'] = np.linspace(0., 1., len(altered))
    altered['stimSide'] = -99.
    fa = prepare_features(altered, f.calibration_transform)
    X, Z, _, _, _ = build_design(f, 'condition')
    Xa, Za, _, _, _ = build_design(fa, 'condition')
    np.testing.assert_array_equal(X[:301], Xa[:301])
    np.testing.assert_array_equal(Z[:301], Za[:301])
    # Group adaptation counterfactual is confined to exactly three columns.
    X0 = build_design(f, 'condition', adaptation_group_override=0)[0]
    X1 = build_design(f, 'condition', adaptation_group_override=1)[0]
    np.testing.assert_array_equal(X0[:, :-3], X1[:, :-3])
    np.testing.assert_allclose(X1[:, -3:] - X0[:, -3:], f.history)
    asymmetric = prepare_features(frame, config=ModelConfig(asymmetric_saturation=True))
    ax, az, anames, _, _ = build_design(asymmetric, 'condition')
    assert asymmetric.nuisance.shape[1] == 12 and len(anames) == 90
    assert 'condition:abscontrast_1' in anames
    np.testing.assert_array_equal(asymmetric.nuisance[:, :8], f.nuisance)
    cfg = ModelConfig(maxiter=1000)
    fit = fit_model(f, 'shared', cfg)
    assert fit.diagnostics['success'], fit.diagnostics
    assert np.isfinite(fit.beta).all()
    p = predict_model(fit, f)
    assert np.all((p > 0) & (p < 1))
    assert log_score(p[f.responded], f.y[f.responded]).mean() > -np.log(2)
    # A deterministic coefficient fixture verifies integration and contrast sign.
    names = build_design(f, 'condition')[2]
    fixed = FitResult('condition', np.zeros(len(names)), np.zeros((20, 5)), f.subjects,
                      names, build_design(f, 'condition')[3], cfg, f.calibration_transform, {})
    fixed.beta[-2] = 1.25
    diff = predict_adaptation_contrast(fixed, f)
    assert np.all(diff[f.history[:, 1] > .01] > 0)
    assert np.all(diff[f.history[:, 1] < -.01] < 0)
    fixed.beta[-2] = 0.
    np.testing.assert_allclose(predict_model(fixed, f), .5, atol=1e-14)
    with tempfile.TemporaryDirectory() as td:
        path = Path(td) / 'model.json'
        fit.save(path)
        loaded = FitResult.load(path)
        np.testing.assert_allclose(predict_model(loaded, f), p, atol=0, rtol=0)
    report = dict(passed=True, seed=42, synthetic_subjects=20, checks=[
        'chronological history before update', 'current/future outcome blindness',
        'hidden-label invariance', 'isolated group adaptation counterfactual',
        'optimizer convergence', 'synthetic sensory signal prediction',
        'known coefficient contrast sign', 'quadrature symmetric zero', 'JSON roundtrip'],
        fit_diagnostics=fit.diagnostics)
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    run()
