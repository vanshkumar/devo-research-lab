# Expanded checks fixed before reading expanded simulation results

The development state fit and 8-person pilot are known: restricted retentions0.73168/0.99168; alternative0.72249/0.99172 with event-fast0.75809; model-implied theta0.02447 and local profile SE0.03406. The slow-retention estimate lies only about0.50 standard errors below its0.995 upper bound. Therefore the local profile interval is model-conditional, and the earlier absolute0.002 boundary flag is insufficient evidence of calibration. Reserved/external outcomes remain sealed.

The initial 20-replicate-per-condition, 8-person recovery pilot is preserved in `outputs/state_models_recovery_pilot.json`; it is not replaced by expanded checks. Noiseless recovery was accurate. Repeated events changed isolated comparator effects away from the actual-schedule0.2-degree boundary, especially for negative modulation; the expanded experiment calibrates the actual-schedule estimand directly.

Expanded checks retain the fitted model and bounds unchanged. They use all20 frozen development schedules, participant gain multipliers drawn lognormally and normalized to mean1, motor/observation SD2.5, generator correlations0.70/0.25, drift0.6, and independent1% outcome omissions. Input histories remain complete.

- 100 replicates: fixed two-state/current-gain-only null.
- 100 each: fast-state modulation calibrated to actual-schedule theta=-0.2 and+0.2 degrees, with retentions0.65/0.97, gains1.0/0.2. The1.0-degree fast contribution is within the development response scale and permits both actual-schedule boundary effects without negative transition factors.
- 50 each: expression on t+1 only, calibrated to theta=-0.2 and+0.2. This exposes the geometric-persistence constraint.
- 50: rebound with+1 degree on t+1 and-1 degree on t+2, giving theta0. This tests whether the geometric model invents a persistent effect from a zero-sum curve.
- 50: direct online expression proportional to current state on spatial-jump trials, without altered storage propagation. True earlier-input index-event interaction at future endpoints is0.
- 50 each: modulation of the slow0.92-retention component in a0.50/0.92 two-state system, gains0.30/0.90, calibrated to theta=-0.2 and+0.2. The restricted two-state structure is supported; the event's location in the slower component challenges the alternative model's fast-only assumption.

For each run save true and fitted theta, interval, coverage, zero-exclusion, interval wholly inside[-0.2,+0.2], false equivalence when true theta is at/outside that boundary, parameters, Hessian status, absolute and SE-scaled boundary diagnostics. Counts at finite replication must include binomial uncertainty. The original margin is unchanged. A narrow interval under a misspecified shape is not a general absence bound.

Separately,200 stratified whole-person bootstrap refits quantify development uncertainty including reoptimized retentions and all participant nuisance. Save every nonlinear parameter vector, theta, optimization success and bound frequency. This differs from the very narrow conditional-on-retentions person interval, which must not be used for substantive uncertainty.

Implementation: `experiments/state_models.py stress --reps100 --altreps50` and `bootstrap --reps200` (actual CLI requires a space after each flag). Checkpoints: `outputs/state_models_stress.json`, `outputs/state_models_bootstrap.json`; logs in this directory. Expanded simulations and bootstrap were launched before this note was written; their numeric results had not been inspected when this design was recorded.
