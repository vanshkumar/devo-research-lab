# Two-state model challenge and covariance repair

2026-10-28. Development-only model work is complete and freeze-ready. No reserved primary or external behavioral outcome was accessed. Both secondary versions will be evaluated; neither replaces the preregistered observable, its 0.2° margin, or the independent-laboratory prediction.

The development model-implied mean lag-1–5 effect is +0.0245° with ordinary least squares (OLS) and +0.0332° after one-pass feasible generalized least squares (FGLS). Their local profile intervals are narrow, but they are **model-conditional intervals, not a general absence bound**. Actual-schedule recovery identifies a colored-noise profiling bias, asymmetric boundary behavior and sensitivity to alternative response kernels. The targeted covariance repair improves the matched positive-boundary result, from 14/100 to 8/100 false-equivalence intervals, without establishing robust calibration. This is a completed bounded attempt to extract a low-dimensional propagation law, not evidence that the experimental schedules contain no information.

## Scope and matched mean models

The frozen development split is ten participants from each Tsay source: TE_SPE SN3,4,6,8,9,11,13,14,16,20; controljump SN1,5,6,9,11,12,13,15,16,20. `analysis.load` enforces the split before endpoint conversion. Simulation work reads only input schedules and generates new outcomes.

The endpoint is compensation-positive `−Hand_raw`, with the finite baseline mean subtracted. This is an exported unmasked endpoint, not verified acquisition-raw movement data. All 180 randomized trials in each of four portions remain in the latent chronology. Missing or |angle|>90° observations are omitted from loss, not from state updates. Portion-specific initial states handle prior history without pretending the deterministic probes are randomized observations. Four intercepts and four linear drifts per person absorb offsets and slow changes.

The two parallel states have common retention parameters across participants, with fast retention in [0.10,0.85] and slow retention in [0.86,0.995]. The alternative adds one fast-state retention on zero-clamp spatial-jump trials, bounded [0.01,1.35]. Its difference from ordinary fast retention can have either sign. The restricted and alternative models have identical 40 linear coefficients per person: eight current-cell gain contrasts per state, eight direct current-cell endpoint terms, four portion intercepts, four portion drifts, and two initial-state amplitudes per portion. `(clamp,jump)=(0,0)` is the reference cell. The gain parameterization therefore respects the nine actually available cells in each source rather than inventing a factorial design.

Variable projection solves the linear nuisance at each shared nonlinear vector. The empirical restricted fit uses three starts, and the alternative uses the restricted optimum plus signed event-retention shifts. Bounds and starts are documented in [DESIGN.md](DESIGN.md). The estimand is half the difference between prior stationary +4° and −4° input gains, multiplied by the event-retention change and actual subsequent transition products, then averaged equally over lags1–5 and people. Later stationary-target readouts and isolated no-future-event curves are also saved. Direct current-cell effects cancel from this counterfactual contrast.

The local uncertainty calculation includes changes in profiled gains and shared retentions via a participant-cluster sandwich and numerical derivatives, centered within source. It does not hold nonlinear parameters fixed. Nevertheless, its linearization can fail at parameter boundaries or under misspecification. `diagnostic_only=false` means only that a simple absolute-distance and Hessian check did not flag the fit; it is not proof of coverage.

## Development estimates and identifiability

| Quantity | OLS | One-pass FGLS |
|---|---:|---:|
| Fast retention | 0.72249 | 0.57177 |
| Slow retention | 0.99172 | 0.98724 |
| Fast retention at zero-clamp jump | 0.75809 | 0.62720 |
| Mean lag-1–5 effect, degrees | +0.02447 | +0.03315 |
| Local full-profile SE | 0.03406 | 0.02291 |
| Local model-conditional 95% interval | [−0.04710,+0.09603] | [−0.01498,+0.08128] |
| Slow upper-bound distance / local SE | 0.504 | 1.097 |
| Correlation of fast/event-retention estimates | 0.844 | 0.886 |

OLS lag curve: [0.04163,0.03041,0.02221,0.01622,0.01185]°. FGLS: [0.07396,0.04321,0.02523,0.01474,0.00861]°. OLS later-stationary-readout mean is +0.02448°, essentially the same on these schedules. The OLS in-sample MSE improvement is only 0.000761 deg² per endpoint. OLS and whitened FGLS losses use different metrics and must not be compared directly as model selection scores.

The OLS conditional-on-retentions SE is 0.00180°; this is not an acceptable uncertainty estimate for the fitted law. A 200-replicate stratified whole-person OLS bootstrap, with the nonlinear fit repeated, gives percentile interval [−0.03741,+0.09129]° and SD0.03060°. The slow retention reaches its upper bound in 56/200 samples; some parameter reaches a bound in 62/200. All bootstrap optimizers report success. The empirical slow retention is just 0.50 local SE from its upper bound, even though it is outside the code's absolute 0.002 proximity flag. The bootstrap is useful for empirical instability, but does not repair failures under known truth.

## Recovery on actual schedules

The original pilot is preserved in `outputs/state_models_recovery_pilot.json`: three noiseless cases and 20 noisy repetitions for each of null and signed effects on eight actual development schedules. Within-family noiseless reconstruction is accurate to less than 2e−7°; this verifies algebra, not statistical calibration.

The expanded OLS challenge has 600 repetitions using all 20 development schedules. Matched generators have fixed retentions 0.65 and0.97, signed actual-schedule target effects calibrated to ±0.2°, person gain variation with lognormal SD0.20 and normalized mean1, 1% missing observations, noise SD2.5°, an AR mixture with correlations0.70/0.25 and weights0.35/0.65, and 0.6-scale drift. Actual future event products enter truth, rather than an isolated exponential approximation. Alternative kernels include delayed expression, a +1°/−1° next-two-trial rebound whose mean lag-1–5 effect is zero, online expression and slow-state propagation. An independent four-way intervention reconstruction verifies the slow-state truth calculation within 1e−12.

Here “false equivalence” means a nominal 95% interval lies wholly inside [−0.2,+0.2]° when the true effect is on or outside the boundary. “Zero excluded” is a false positive when truth is zero. Counts are conditional on these particular generators, not universal task power.

| OLS generator | True effect | N | Mean estimate | Coverage | Zero excluded | False equivalence |
|---|---:|---:|---:|---:|---:|---:|
| Fixed two-state | 0 |100|−0.0046|94|6|—|
| Fast propagation |−0.2|100|−0.1937|94|100|6|
| Fast propagation |+0.2|100|+0.1743|86|100|14|
| Delayed expression |−0.2|50|−0.2577|26|50|0|
| Delayed expression |+0.2|50|+0.2284|43|50|0|
| Rebound |0|50|+0.0894|14|36|—|
| Online expression |0|50|−0.0116|44|6|—|
| Slow propagation |−0.2|50|−0.1523|40|48|10|
| Slow propagation |+0.2|50|+0.2477|42|43|0|

At the positive fast boundary, false equivalence is 14% (Wilson95% interval8.5–22.1%). Four of 35 fits not flagged by the local diagnostic still falsely support equivalence. Both slow-state challenges flag every fit, but this does not rescue the one-fast-law model: the negative slow effect is biased toward zero and fails equivalence in10/50 cases, while the positive slow effect is biased upward. Rebound produces36/50 false positives despite a true mean zero. Details, boundary counts, Hessian flags and SE-scaled slow-bound distances are in `state_models_stress.json` and `state_models_stress_summary.json/.csv`.

## Why OLS fails, and the single repair

Optimizer shortcuts do not explain the OLS positive-boundary bias. Thirty positive-boundary repetitions, including the largest misses, were repeated with the exact empirical multistart procedure. All180 starts succeeded; the largest theta change was2.57e−6°, and the same11 selected cases remained false-equivalence cases. Starting five severe misses at the true generating parameter also returned the biased optimum, with theta changes below7e−7°.

The independent expected-SSE calculation identifies a concrete criterion bias. For profiled linear nuisance with projection P depending on retention λ,

`E[SSE(λ)] = ||(I−Pλ) μ||² + tr((I−Pλ) Σ)`.

With colored noise, the second term varies across candidate retentions. On the actual schedules, a wrong parameter vector (0.70,0.995,0.95) implying theta0.1637° instead of the true0.2° adds53.78 signal SSE but captures173.60 additional noise SSE, improving the expected OLS criterion by119.82. Equal-rank white covariance removes this advantage. This is a nuisance-profile/noise interaction, not merely a local-optimizer failure or a parameter-bound issue. See `audits/adversarial_review/profile_noise_bias.json/.py`.

The one targeted repair retains exactly the same mean models and nuisance. [GLS_REPAIR_DESIGN.md](GLS_REPAIR_DESIGN.md) was saved before reviewing repair outputs:

1. Oracle GLS uses the exact simulated AR-mixture plus drift covariance, selected observed rows and original-trial distances. It rechecks all14 OLS positive false-equivalence repetitions plus six other repetitions with exact empirical multistarts. False equivalence falls from14 to6 among these20, and mean theta shifts +0.01434°. This deliberately selected paired diagnostic is not an unbiased coverage estimate; individual unlucky samples need not be repaired by knowing covariance.
2. Practical FGLS estimates one common AR1 coefficient from the restricted OLS **development main-phase** residuals, then fixes that shape for both models. It uses within-portion adjacent residual cross-products divided by lagged sum of squares, clipped to[−0.8,+0.8]. Whitening uses original-trial gaps. The empirical estimate is phi0.26487. Baseline covariance is deliberately not used: baseline veridical-feedback dynamics have negative serial dependence, unlike the main phase.
3. Each synthetic FGLS repetition repeats the restricted OLS residual calibration and both GLS fits. Recovery therefore tests the practical procedure rather than supplying it with oracle covariance.

| FGLS generator | True effect | N | Mean estimate | Coverage | Zero excluded | False equivalence | Slow at upper bound |
|---|---:|---:|---:|---:|---:|---:|---:|
| Fixed two-state |0|100|−0.00317|91|9|—|45|
| Fast propagation |+0.2|100|+0.18616|92|100|8|46|
| Fast propagation |−0.2|100|−0.20435|93|100|4|37|

Positive-boundary FGLS false equivalence is8% (Wilson95% interval4.1–15.0%); negative is4% [1.6–9.8%]. There are three positive false-equivalence cases among47 unflagged fits and three negative cases among60 unflagged fits. All300 saved alternative optimizer starts succeed. FGLS positive-case mean estimated phi is about0.334, below the generator's AR-mixture lag-one correlation0.4075; the profiled mean model has already absorbed correlated variation. Thus the practical repair reduces bias but cannot be described as exact covariance recovery. Null coverage91/100 and the remaining boundary errors support caution.

FGLS recovery used one start per fit for speed; OLS multistart equivalence was directly checked, but an analogous FGLS multistart comparison was not run. FGLS alternative-kernel recovery and an empirical FGLS bootstrap were not run. Local FGLS intervals condition on the estimated covariance shape. These explicit limitations prevent promoting its narrow development interval into a general bound. No further family or tuning search was undertaken.

## Frozen prediction and evaluation

Both versions freeze nonlinear parameters and source-average gain, direct-effect, drift and initial-state coefficients. Only each new person's permitted first100-trial baseline mean is added. `predicted_full` explicitly replaces main outcomes by zeros before constructing a design; scoring eligibility is separate. Across all20 development people and all four model/version combinations, replacing every main outcome with arbitrary values and NaNs changes forecasts by exactly0. A +1° baseline shift changes all forecasts by +1° to numerical precision (<1.8e−15).

Scoring uses zero-clamp index events inside the prespecified portion interior and all five future endpoints relative to the fixed prior-five mean. It computes person-average squared-error differences, then equal-source mean gain with within-source participant variances and Welch–Satterthwaite degrees of freedom. Source summaries are retained. A fabricated-data check verifies that between-source level differences do not inflate within-source uncertainty. No reserved parameter, state, gain or covariance fitting is allowed.

Final implementation/frozen-file hashes and invariance evidence are in `outputs/state_models_freeze_readiness.json`. Refreshing script provenance after the forecast guard and score-summary amendment changed neither development parameter vectors nor curves. Pre-refresh artifacts remain under `*_before_provenance_refresh.json`.

After the lead creates `protocol/VALIDATION_RELEASE.json`, run from the repository root:

```sh
.venv/bin/python campaigns/target_event_carryover_2026-10-28/experiments/state_models.py evaluate
.venv/bin/python campaigns/target_event_carryover_2026-10-28/audits/state_models/gls_repair.py evaluate
```

These write `outputs/state_models_validation.json` and `outputs/state_models_fgls_validation.json`. Report both versions, without choosing a winner based on reserved outcomes. The independent-laboratory transfer continues to use the separately frozen primary development curve.

## Scientific interpretation and artifact map

The models demonstrate that this schedule supports algebraically identifiable low-dimensional propagation parameters in noiseless matched settings, while real-scale colored noise and flexible participant nuisance can bias their estimated observable. A narrow fitted interval is not enough to bound a broad biological phenomenon. Conversely, estimator failure does not establish an absence of experimental information. The primary observable and its separately tested recovery remain the basis for the main claim.

Even a successful propagation prediction would not distinguish stored-state loss from state-dependent perceived-error correction: `a*x + b*(c−lambda_J*x) + d_J = (a−b*lambda_J)*x + b*c + d_J`. Endpoint behavior alone cannot choose between these descriptions. The [source/measurement audit](../source_measurement/AUDIT.md) documents that measurement and intervention limit, along with exact source transformations and external geometry/sign conventions.

Reproducible evidence:

- `experiments/state_models.py`: mean model, derivative uncertainty, OLS fit/recovery/bootstrap, frozen forecasts and evaluator.
- `audits/state_models/gls_repair.py`: oracle GLS, empirical one-pass FGLS, full-procedure recovery and evaluator.
- `audits/state_models/finalize.py`: development-only forecast invariance, summary tables, fit-provenance comparison and fixed-source scoring check.
- `outputs/state_models_development.json`, `state_models_fgls_development.json`: complete fits and person coefficients.
- `outputs/state_models_recovery_pilot.json`, `state_models_stress.json`, `state_models_stress_summary.json/.csv`: original and expanded OLS recovery.
- `outputs/state_models_optimizer_fairness.json`, `state_models_true_start_check.json`: optimization checks.
- `outputs/state_models_bootstrap.json`:200 whole-person OLS refits and boundary outcomes.
- `outputs/state_models_gls_oracle.json`, `state_models_fgls_recovery_core.json`, `state_models_fgls_recovery_summary.json/.csv`: covariance-repair evidence.
- `outputs/state_models_frozen_predictions.json`, `state_models_fgls_frozen_predictions.json`, `state_models_prediction_invariance.json`, `state_models_freeze_readiness.json`: final pre-release forecasts and verification.

Suggested project-specific learning for the lead's root LEARNINGS update: on these Tsay schedules, profiling40 participant-specific coefficients under colored noise changes expected residual noise capture across retention parameters; exact multistarts preserve the resulting positive-boundary bias. A same-family residual-AR1 FGLS repair reduces but does not eliminate calibration failures. Future reuse should preserve the actual-schedule signed-boundary and alternative-kernel recovery, and should not convert local state-model intervals into broad carryover equivalence.
