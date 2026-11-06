"""Exploratory precision gate using consumed source forecasts only.

Reads saved original-source observations and frozen model simulations. Never
imports a raw-data loader and never reads the protected Pan cohort. Gaussian
power numbers are source-analog approximations, not empirical external power.
"""
import json
from pathlib import Path
import numpy as np
from scipy.stats import norm

ROOT = Path(__file__).resolve().parents[2]
C = ROOT / "campaigns/learning_rule_transport_2026-10-28"
OUT = Path(__file__).resolve().parent
ids = json.loads((C / "artifacts/results/SUBJECT_ORDER.json").read_text())
allocation = {r["subject"]: r for r in json.loads((C / "protocols/SPLIT.json").read_text())["standard"]}
observed, rnn, growth = [], [], []
for subject in ids:
    animal = allocation[subject]["split"] == "animal_holdout"
    base = C / "artifacts/forecasts" / ("source_animals" if animal else "source_labs")
    recurrent = C / "artifacts/forecasts" / ("rnn_source_animals" if animal else "rnn_source_labs")
    with np.load(base / (subject + "__observed.npz"), allow_pickle=False) as f:
        observed.append(f["observed"][:6, :2].mean(axis=1))
    with np.load(recurrent / (subject + "__rnnglm32.npz"), allow_pickle=False) as f:
        rnn.append(f["samples_primary"][:, :6, :2].mean(axis=(0, 2)))
    with np.load(base / (subject + "__growth.npz"), allow_pickle=False) as f:
        growth.append(f["samples_primary"][:, :6, :2].mean(axis=(0, 2)))
y, m, g = map(np.asarray, (observed, rnn, growth))
if y.shape != (40, 6) or not np.isfinite([y, m, g]).all():
    raise RuntimeError("Unexpected primary source shape or missing value")
residual = y - m
scalar = residual.mean(axis=1)
sd = float(scalar.std(ddof=1))
gap = float((m - g).mean())
cov = np.cov(residual, rowvar=False, ddof=1)
rng = np.random.default_rng(202610281)
draws = rng.integers(40, size=(20000, 40))
by = y[draws].mean(axis=1)
bm = m[draws].mean(axis=1)
bg = g[draws].mean(axis=1)
mae_gain = np.abs(by - bg).mean(axis=1) - np.abs(by - bm).mean(axis=1)
result = dict(
    scope="Exploratory source-analog precision assessment; all 40 source animals already consumed; no external data opened",
    scalar="Equal-bin mean of the two side-specific high-contrast correct shares over the next 3000 task opportunities",
    n_source=40,
    mean_curves=dict(observed=y.mean(axis=0).tolist(), rnn=m.mean(axis=0).tolist(), growth=g.mean(axis=0).tolist()),
    population_mean_curve_mae=dict(rnn=float(np.abs(y.mean(axis=0)-m.mean(axis=0)).mean()), growth=float(np.abs(y.mean(axis=0)-g.mean(axis=0)).mean())),
    bootstrap_mean_curve_mae_gain=dict(point=float(np.abs(y.mean(axis=0)-g.mean(axis=0)).mean()-np.abs(y.mean(axis=0)-m.mean(axis=0)).mean()), interval95=np.quantile(mae_gain,[.025,.975]).tolist(), note="Selected-model, same-source descriptive bootstrap; not fresh confirmation"),
    source_rnn_scalar_residual_sd=sd,
    source_average_rnn_minus_growth_forecast=gap,
    source_residual_covariance=cov.tolist(),
    prospective_source_analog=[])
for n in [20, 26, 40]:
    se = sd / np.sqrt(n)
    gap_z = abs(gap) / se
    power = float(norm.sf(norm.ppf(.975)-gap_z)+norm.cdf(-norm.ppf(.975)-gap_z))
    result["prospective_source_analog"].append(dict(
        independent_animals=n, scalar_mean_se=se, approximate95_halfwidth=norm.ppf(.975)*se,
        approximate_effect_for80percent_two_sided_power=(norm.ppf(.975)+norm.ppf(.8))*se,
        gaussian_power_for_current_source_model_gap=power,
        note="Assumes independent animals and transport of centered source residual variance; no lab-shift or model-selection uncertainty included"))
summary = OUT / "RESULT.json"
summary.write_text(json.dumps(result, indent=2) + "\n")
print(json.dumps({k:v for k,v in result.items() if k!="source_residual_covariance"}, indent=2))
