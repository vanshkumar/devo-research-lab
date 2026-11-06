# Secondary state-model stress review

2026-10-28. This reviews the original unweighted two-state efficiency model. Any later covariance-aware repair needs its own calibration and must remain separately labeled. No reserved or external outcomes were accessed.

## Verdict

The original secondary model detects injected signed effects efficiently, but its nominal interval is not calibrated for broad observable equivalence. At a correctly specified fast-state physical effect of+0.2°,14/100 intervals falsely lie wholly inside±0.2°;4 of those occur among35 fits not flagged diagnostic. Negative fast modulation gives6/100 false-equivalence intervals. Slow-state negative modulation gives10/50. Rebound with true five-lag mean zero is incorrectly declared nonzero36/50 times. The narrow development interval and narrow empirical bootstrap interval cannot be used as general evidence of a small physical propagation effect.

## Full stress results

Each row uses all20development input schedules with synthetic outcomes only. The target physical scalar is calibrated over actual future event histories. Raw counts avoid implying more precision than100/50replicates.

| Challenge | True θ | Mean fitted θ | n | CI covers truth | CI excludes zero | False equivalence | Diagnostic flags |
|---|---:|---:|---:|---:|---:|---:|---:|
| delayed_expression | -0.2 | -0.258 | 50 | 26 | 50 | 0 | 30 |
| delayed_expression | +0.2 | +0.228 | 50 | 43 | 50 | 0 | 29 |
| fast_modulation | -0.2 | -0.194 | 100 | 94 | 100 | 6 | 54 |
| fast_modulation | +0.2 | +0.174 | 100 | 86 | 100 | 14 | 65 |
| fixed_two_state | +0.0 | -0.005 | 100 | 94 | 6 | 0 | 61 |
| online_expression | +0.0 | -0.012 | 50 | 44 | 6 | 0 | 29 |
| rebound | +0.0 | +0.089 | 50 | 14 | 36 | 0 | 28 |
| slow_modulation | -0.2 | -0.152 | 50 | 40 | 48 | 10 | 50 |
| slow_modulation | +0.2 | +0.248 | 50 | 42 | 43 | 0 | 50 |

“False equivalence” means the entire nominal95%CI is inside±0.2° while the generating physical scalar is at the boundary. It is not the same as a failure to detect zero. Every slow-modulation fit is flagged diagnostic; its failure cannot be hidden by reporting only regular fits, because the model never yields a regular fit in that challenge. Conversely, false equivalence in fast positive modulation remains among unflagged fits.

## Optimizer and bootstrap checks

An exact empirical-rule multistart comparison was performed on30positive fast-effect replicates, including20evenly spaced indices and ten worst-bias examples. Maximum change inθ is 2.56e-06°. Therefore the observed recovery failures in this check are not explained by fewer optimizer starts in simulation. Full per-start status and losses are preserved by the model author.

The200stratified empirical participant bootstraps give a narrow percentile interval [-0.037406716811426335, 0.09128743152609972]°, while56/200slow rates hit the upper bound. This demonstrates sampling stability of the fitted criterion in this development sample. It does not repair known-generator bias, misspecification or coverage.

## Confirmed failure mechanism and next requirement

The independent exact expected-loss calculation in `profile_noise_bias.json` shows that colored noise plus person-specific linear profiling can make wrong retention parameters outperform the true parameters in expected unweighted SSE, despite equal model rank and a correctly specified mean family. Cluster-robust uncertainty estimates sampling variation around the fitted criterion; it does not remove this criterion bias.

A bounded covariance-aware or explicitly simulation-calibrated repair is scientifically justified. Any repaired interval must pass independent signed-effect and readout/slow-state challenges before supporting equivalence. A successful repair can supply a conditional bound or frozen prediction; it must not replace the original observable endpoint or silently spend validation on model selection.

Exact source data: `outputs/state_models_stress.json`, `outputs/state_models_optimizer_fairness.json`, `outputs/state_models_bootstrap.json`. Independent physical truth check: `slow_truth_check.json`.
