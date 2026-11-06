# Bounded adversarial audit of neural-dynamics pilots

2026-10-28. Read-only outside this directory. Inspected experiments/neural_dynamics/{run.py,PLAN.md,selection.json,discovery_forecasts.csv,control_nulls.csv,discovery_nulls.csv,discovery_quality.json}, source dataset documentation and **only the first discovery raw JSON** for small checks. No validation JSON was opened. Work capped at the user's steering away from over-emphasis on LOOPER. This audits forecast/dimensionality calibration, not a LOOPER reproduction.

## Consequential correction: original ridge failure does not establish zero population information

In forecasts(), population ridge is penalized toward a zero coefficient matrix and hence toward the old training target mean. Persistence is instead a strong unpenalized identity model. Under drift or slow calcium dynamics these priors differ substantially. The original population-vs-diagonal comparison can answer which fitted models predict better; it cannot establish whether the population contains information beyond own-channel history. The diagonal comparator is also a direct h-step scalar regression on the current frame, not an autoregression on a rich history.

An **exploratory adversarial check**, fixed before its own outcome, fit future-minus-current residuals with ridge centered on persistence. It used the same train/tuning/test cuts, a fixed grid {.01,.1,1,10,100,1000,1e6}×n_train, and both population and diagonal residual models. Only first discovery worm 2022-06-14-01; four pre-existing horizons; no model sweep or validation use. Output is neural_audit_check.csv.

| Horizon | Original population MSE | Original diagonal MSE | Persistence MSE | Anchored population MSE | Anchored diagonal MSE |
|---|---:|---:|---:|---:|---:|
| .6 s | .6594 | .3934 | .3218 | .3321 | .3179 |
| 3 s | 1.3139 | .9863 | .9204 | .8662 | .9320 |
| 12 s | 1.6666 | 1.5135 | 1.8254 | 1.5037 | 1.4429 |
| 30 s | 1.8788 | 1.7636 | 2.1695 | 1.6629 | 1.6320 |

At 3 s the anchored population model improves on the fairly anchored diagonal by 7.07%, reversing the sign of the original comparison. Other horizons favor the anchored diagonal. No general positive claim is established by one selected exploratory worm/horizon. The decisive audit lesson is to **retire blanket absence-of-population-information language**. If this pilot is retired, describe the result as a calibration failure of a simple forecast family and a mixed exploratory correction. A population effect claim would require fixed, fair own-history baselines and independent animal validation; do not enlarge the present pilot merely to manufacture one.

Reproduce small check: `.venv/bin/python experiments/causal_identification/neural_audit_check.py`. Exact code and stdout are retained here. This residual formulation uses training means only and zero future/test data for tuning.

## Phase null: what passes, what it cannot see

The surrogate implementation preserves each channel's DFT amplitude (and fixed DC/Nyquist coefficients), while independently randomizing other Fourier phases across channels. The circular-shift implementation preserves marginal distribution/circular autocorrelation and disrupts relative channel timing. Both are competent nulls for coordinated structure beyond individual spectra **under stationarity/circular boundary assumptions**. They are not mechanism-specific nulls.

Concrete analytical limitation: if every channel is an arbitrary linear combination of the same single-frequency sine and cosine, independent phase changes leave every surrogate in the same 2D subspace. Thus top-3 variance remains 1 even after cross-channel phase randomization. The raw pure-sine control's real/null top-3=1 and nonsignificant p therefore show blindness to this narrowband class, not evidence that there is no coherent oscillator. Tiny floating-point ties near exactly 1 also make the precise raw sine p-value arbitrary; interpret invariance rather than its digits.

The broadband positive controls are informative: noisy rotation and **shared external broadband drive** both reject the phase/shift null at the finite Monte Carlo floor (.025 with 39 surrogates). This establishes sensitivity to shared temporal structure, while the externally driven control explicitly prevents interpreting rejection as autonomous recurrent loops. A single independent-AR realization for dimensionality has non-significant p; it is a sanity control, not an estimated false-positive rate over realizations.

Additional concrete caution: np.diff removes one sample (1600→1599). The exact periodic sine is then no longer aligned to the DFT frequency grid. Its differentiated real top-3 remains essentially 1 but surrogate top-3 falls to .999863; both nulls give p=.025 for that tiny finite-endpoint change. This illustrates leakage/boundary sensitivity and why the differencing result must be interpreted by effect size, not only nominal p. It is not a useful new biological effect or a failure of a known biological control. The large discovery real-null gaps can be reported as coordination, with nonstationarity and shared-motion/common-input objections remaining.

With 39 surrogates the smallest attainable p is **.025**, never p<.025. Outcomes cover two metrics × two transforms × two nulls × multiple worms. Use the frozen primary comparison and report the full matrix; do not present selected exploratory p-values as independently confirmed or as a multiple-testing-corrected family.

## Chronological split: valid separation, limited information

For n=1600 and dt≈.6 s the code's training targets end at frame 909, validation origins begin at 1010, validation targets end at 1149, and test origins begin at 1250, for all four horizons. Input/target pairs therefore do not cross the splits. The split uses approximately 30 s on each side of each boundary, yielding ≈60 s total separation, rather than 30 s total. No temporal leakage bug found in these indices.

At 30 s there are only 90 tuning origins (≈54 seconds of origins) and 300 test origins. These are overlapping, autocorrelated forecasts; they are not 90 or 300 independent trials. Selecting among six ridge penalties on the short tuning segment can be noisy, especially under distribution drift. Report animals as units and avoid frame-based standard errors/p-values. This is within-animal chronological prediction assessed on several animals, not cross-animal transfer of one model.

standardize() estimates mean/SD from the first 60%, including training-side purged frames. This does not use validation/test outcomes, but means the purge excludes model pairs rather than every preprocessing observation. The good-channel mask checks finiteness over the entire record: transductive channel inclusion in principle. All inspected discovery values are finite and no channels were dropped, so this does not explain the current result.

## Full-record source z-scoring: affine normalization cancels here

If the source trace is z=(raw−full_mean)/full_sd, a subsequent training-only standardization exactly cancels those full-record affine statistics. Thus this is **not automatically test leakage**. On first discovery worm, trace_original and trace_array are per-channel affine equivalents to max residual 5.33e−15; after standardize(first60%) their values differ by at most 2.49e−14. A concrete affine invariance check succeeds.

This check does not certify all upstream calcium extraction, artifact correction, denoising, or interpolation as causal. Any source smoothing using future samples would remain an issue for real-time forecasting, although the chronological gaps prevent simple adjacent-frame overlap across splits. Retain the processed-data provenance limitation. For the full-record PCA/surrogate descriptive analysis, using full-record scale is intentional and has no train/test interpretation.

## Remaining implementation details worth reporting

- Forecast origins are converted from seconds with median dt; actual timestamps vary roughly .525–.675 s per sample in discovery. Labels should say approximate horizons or report actual elapsed-time distributions; this small jitter does not create leakage.
- Method name diag_ar1 means direct h-step regression on x[t], not recursive AR(1) prediction or a multi-lag own-history model. Make that clear in claims.
- Frame shuffle uses the same permutation for all channels; PCA invariance is mathematically expected and useful as an implementation check. It is not a scientific null for cross-channel coordination.
- Existing cached download files in acquire.py are SHA256-recorded but not checked against the pinned Git blob on reuse. Initial downloads were blob-checked; a future rerun on a changed cache would silently accept changed bytes. Before publication-grade reproduction, verify the cached blob too, or instruct reuse only with verified manifest hashes. This is a restart reproducibility issue, not evidence that current files are corrupted.

No additional neural work is recommended within this campaign after the above limitations are incorporated. The pilot has done useful calibration work, and the user's requested wider portfolio should take priority.
