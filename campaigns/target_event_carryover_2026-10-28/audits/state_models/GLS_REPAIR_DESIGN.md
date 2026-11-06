# One targeted covariance-aware repair

Fixed before inspecting GLS/FGLS numerical outputs; those processes were launched while this note was prepared. The mean model, parameter bounds, participant gain/drift/initial-state flexibility and primary observable remain unchanged. The original OLS artifacts and forecasts are retained. This is the last bounded model repair, not a search for a favorable effect.

Reason: an independent input-only expected-SSE calculation in `audits/adversarial_review/profile_noise_bias.json` shows that colored noise makes the nuisance-profile criterion depend on retention parameters even when the true signal is fixed. Slower incorrect filters capture enough additional correlated noise to outweigh their signal misfit. Exact empirical multistarts on30 positive-boundary replicates changed theta by at most2.57e-6 degrees, so optimization starts do not explain the failure.

1. **Simulation-only oracle GLS.** Whiten outcomes and every mean-design column with the exact covariance implied by the known generator: SD2.5, AR mixture weights0.35/0.65 and correlations0.70/0.25; additionally include covariance of the0.6-amplitude random-phase sinusoid and random-slope drift. Use actual original-trial distances, including omitted observations and deterministic gaps. Test all14 original positive-boundary false-equivalence cases plus6 other evenly spaced cases. This deliberately selected paired diagnostic is not an unbiased estimate of coverage. Use the exact empirical multistart procedure.
2. **Practical one-pass FGLS.** Fit the OLS restricted model to development. Estimate one common AR1 coefficient as pooled adjacent residual cross-product divided by lagged-residual sum of squares, using finite adjacent observations inside the same randomized portion, clipped to[-0.8,+0.8]. Hold this covariance shape fixed and identical in both GLS mean models. Whitening accounts for observation gaps as phi**gap; missing rows do not create artificial adjacency. This is development training, not validation calibration. Do not use baseline covariance as a proxy for the main phase: the baseline feedback regime and observed serial dependence differ.
3. **Check the full procedure.** Every synthetic FGLS replicate repeats the OLS residual calibration before GLS fitting; it does not receive known noise parameters. Begin with100 null and100 positive-boundary runs; include negative-boundary runs within the same fixed family. Stop after this repair, regardless of success. If broad-shape recovery remains untested for the repaired method, do not claim a general bound. Profile intervals remain conditional on the estimated covariance; empirical full-person bootstrap can include covariance recalibration if useful, but it cannot replace known-truth recovery.

Frozen coefficients go to `outputs/state_models_fgls_frozen_predictions.json`; original forecasts remain `outputs/state_models_frozen_predictions.json`. Reserved evaluation adds only each new person's permitted baseline mean and scores the predefined future-minus-pre-five contrasts. No reserved state, retention, gain or covariance refit is allowed. The primary independent-laboratory transfer remains the separately frozen observable curve; no secondary state estimate replaces it.

Commands (from repo root):

```
.venv/bin/python campaigns/target_event_carryover_2026-10-28/audits/state_models/gls_repair.py oracle
.venv/bin/python campaigns/target_event_carryover_2026-10-28/audits/state_models/gls_repair.py empirical
.venv/bin/python campaigns/target_event_carryover_2026-10-28/audits/state_models/gls_repair.py recovery --reps 100 --scope core
```

Only after the lead's reserved release:

```
.venv/bin/python campaigns/target_event_carryover_2026-10-28/experiments/state_models.py evaluate
.venv/bin/python campaigns/target_event_carryover_2026-10-28/audits/state_models/gls_repair.py evaluate
```
