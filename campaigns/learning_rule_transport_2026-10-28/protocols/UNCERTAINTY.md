# Bounded forecast-uncertainty challenge

2026-10-28. This calibration was completed before source validation. It uses only the saved development-CV autonomous forecasts and their saved observed curves in `artifacts/forecasts/dev_pilot/`. No source-holdout or external outcomes were opened. It changes forecast dispersion; no learning-rule coefficients, trainer parameters or initial-condition calibration methods are refitted.

## Frozen method and consumer

For each of the six models, compute the 10 development animals' curve residuals `observed - mean(raw forecast particles)` separately for each bin and metric. For animal i, omit i entirely from its residual-donor bank and recenter the other animals' residuals separately by bin and metric. Draw a whole correlated residual trajectory per forecast particle, add it at amplitude λ in the prespecified set `{0,.5,1}`, and clip resulting observable fractions to `[0,1]`. Choose the amplitude minimizing equally weighted animal CRPS over the primary six bins (3,000 future trials); ties favor the smaller amplitude. The same candidate set and scoring procedure applies to every model and both competence baselines.

The final deployment bank uses all 10 development-CV donors. Centering at application makes its pre-clipping mean zero. No empirical mean residual is added. Finite donor sampling and clipping can nevertheless shift forecast means; their separate magnitudes are recorded below. This is a bounded predictive-uncertainty challenge, not proof that arbitrarily widened intervals provide useful learning prediction.

Consumer API:

```python
from uncertainty import apply_calibration
samples_primary = apply_calibration(
    samples, model_name, seed=subject_forecast_seed + 647,
    config_path="campaigns/learning_rule_transport_2026-10-28/artifacts/calibration/CONFIG.json",
)
```

`apply_calibration` accepts no outcome argument and verifies the frozen residual bank's SHA256 before use. The base forecast seed is `20261028 + int(SHA256(subject)[:7],16)`; LOO calibration uses exactly that seed plus 647, equivalent to seed base 20261675. Main forecasts should save raw samples and calibrated primary samples before opening validation outcomes for scoring.

`CONFIG.json` contains each model's selected amplitude, primary horizon, donor IDs, per-cell donor counts, exact residual-bank path/hash and the selection record. Its completed six-model SHA256 is `b77a6f4d2021e5ef8567e1319a242572f76b6fdd861bc7fda10641ef1dab9a84`. The lead's validation-freeze artifact owns the ultimate frozen hash; do not rerun calibration after validation exposure.

## Development results

All 10 animals with saved future curves have the full primary 3,000 future trials. Two additional nested-CV animals lack a sufficient recorded forecast future and supply no residual curve. The 10 are CSHL053, CSHL058, CSHL059, CSH_ZAD_005, CSH_ZAD_007, DY_015, KS002, ZM_1743, ZM_2240 and ZM_2241. No animal is excluded based on its forecast error.

| Model | Selected λ | Raw CRPS | Selected LOO CRPS | Raw → selected high-contrast MAE | Raw → selected 80% coverage | Selected 80% width |
|---|---:|---:|---:|---|---|---:|
| DNNGLM16 | 0 | .066214 | .066214 | 15.46 → 15.46 pp | 84.2 → 84.2% | 37.24 pp |
| DNNGLM32 | 0 | .071383 | .071383 | 13.39 → 13.39 pp | 82.1 → 82.1% | 29.06 pp |
| REINFORCE with free baseline | 0 | .058535 | .058535 | 12.18 → 12.18 pp | 91.7 → 91.7% | 43.15 pp |
| Empirical growth | .5 | .063972 | .063647 | 11.85 → 12.07 pp | 81.3 → 85.4% | 30.81 pp |
| Full-prefix competence persistence | 1 | .113323 | .095678 | 18.91 → 19.43 pp | 37.1 → 76.3% | 31.73 pp |
| Pure reward REINFORCE | 1 | .087831 | .079308 | 16.73 → 17.56 pp | 43.8 → 80.8% | 30.84 pp |

The DNNs and free-baseline REINFORCE do not improve proper CRPS by widening. Pure reward REINFORCE and persistence were overconfident; residual widening improves their distributional scores and coverage while their absolute forecast means remain inaccurate. Growth receives a small dispersion adjustment. These are development calibration/selection results, not independent validation estimates. They do not themselves earn the source or external gate.

The 32-unit DNN's λ=.5 CRPS is .071418 versus .071383 at λ=0, a close development comparison. The discrete candidate rule chooses 0; no seed or amplitude was selected to reverse that comparison.

## Mean shifts and partial histories

For selected positive amplitudes, average absolute total forecast-cell mean shifts (finite donor sampling plus clipping) are .586 pp for growth, 1.519 pp for persistence and 1.078 pp for pure reward RL. The clipping-only absolute contributions are .393/.952/.624 pp respectively. Mean signed clipping shifts in `[left-high accuracy,right-high accuracy,right-choice share,omission]` are:

- Growth: `[-.323,-.727,-.00005,+.187]` pp.
- Persistence: `[-.808,-.710,+.316,+.418]` pp.
- Pure reward RL: `[-.499,-.933,+.115,+.418]` pp.

These shifts are not assumed to be zero or described as an exact preservation of observable means. Raw and calibrated high-contrast MAEs remain separately inspectable. The zero-amplitude models' samples are unchanged exactly.

The residual arrays preserve missing future cells as NaN and carry explicit validity masks. Centering uses available donors; missing donor cells contribute a centered zero residual under the shared `evaluation.apply_discrepancy` policy. All 10 donors cover every primary cell. At later secondary horizons the donor count falls to nine and then eight; those missing tails are not fabricated observed zero errors. This treatment preserves a full donor trajectory but reduces tail dispersion, so primary and longer-horizon calibration should remain distinguished.

`CALIBRATION_AUDIT.json` verifies that no target animal appears among its LOO donors, that effective centered deployment banks have numerical zero means, that selected amplitudes minimize the declared criterion, and that the public consumer produces exactly the shared discrepancy implementation's output. Per-model `*_SOURCE_MANIFEST.json` files hash every input observed curve and autonomous forecast. Input hashes are rechecked after fitting to reject a forecast that changes during calibration.

## Amendment and reproduction record

An initial exploratory run used donor seed base 60439 before the main consumer's seed was communicated. Its complete files are retained under `artifacts/calibration/initial_seed60439/`. The final prevalidation run aligned the LOO seed with the prospective consumer's fixed base+647. All five initial models retained the same selected amplitudes; the 32-unit candidate was then included under the same procedure. This is a recorded implementation alignment before validation, not a seed search.

Offline from repository root:

```sh
campaigns/learning_rule_transport_2026-10-28/.modelenv/bin/python \
  campaigns/learning_rule_transport_2026-10-28/code/uncertainty.py
```

`fit_uncertainty(forecast_dir=None,out_dir=None,models=None)` is callable; a specified model must have forecasts for all available development-CV animals, preventing silent reduction of calibration samples while a candidate arrives. For example, `--models dnnglm32` updates only that model when all ten forecasts are present. `--collect-only` collects saved per-model summaries without fitting. Numerical residual fitting needs NumPy/SciPy only; there is no network access or original-data acquisition in this module. Do not invoke fitting after validation is opened; consume the frozen configuration instead.
