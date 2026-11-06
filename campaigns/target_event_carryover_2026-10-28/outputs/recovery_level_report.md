# Recovery of the prespecified endpoint-level sensitivity

2026-10-28. This is a calibration of an already required sensitivity, not a replacement primary. All900simulations use reserved **input schedules only**, with the exact same masks, person/noise draws, generators and seeds as their paired original change-score runs. No empirical reserved outcome was accessed. The frozen nuisance design, prior-cell contrast and CR1/Welch inference remain unchanged. Only the dependent variable is y[t+h], without subtracting the fixed five-pre-index endpoint mean. Original pre/future validity requirements remain.

The linear operators were independently checked against direct five-lag fitting. Physical actual-schedule truth remains the same because the subtracted endpoints are pretreatment; noiseless finite-schedule regression projections are reported separately.

| Scenario | Physical mean θ | Mean estimate | Noiseless projection | Mean SE | Coverage | Excludes zero | Correct-sign detection |
|---|---:|---:|---:|---:|---:|---:|---:|
| Fixed two-state null | 0° | +.0057° | +.0062° | .1652° | 94.0% | 6.0% | — |
| Negative actual-margin effect | −.2003° | −.1708° | −.1818° | .1693° | 94.3% | 16.3% | 16.0% |
| Positive actual-margin effect | +.2003° | +.1816° | +.1804° | .1671° | 97.3% | 13.0% | 13.0% |

Each scenario has300replicates. Mean standard errors are approximately28%lower than the corresponding primary change-score standard errors. This precision improvement does **not** resolve the practical-margin test: correct-sign detection remains13–16%, compared with17.7%/11.0% for negative/positive change-score cases, and no endpoint-level interval is wholly inside±.2°. Lower variance and changed finite-schedule projection bias both affect detection; the endpoint-level result must not be selected just because one empirical estimate or simulation direction is favorable.

This control supports reporting endpoint levels as a useful sensitivity while retaining the original primary and its limitation. It does not establish a broad null or precise equivalence under the distributed-lag procedure. These are conditional simulations with the same colored noise, heterogeneity, drift and omissions as the original core recovery.

Reproduction:

```sh
.venv/bin/python campaigns/target_event_carryover_2026-10-28/experiments/recovery_level.py --reps 300
```

Summary with binomial intervals: `recovery_level_summary.json`; individual runs: `recovery_level_two_timescale_null.json`, `recovery_level_actual_margin_negative.json`, `recovery_level_actual_margin_positive.json`. Log: `../logs/recovery_level.log`. Runtime approximately34seconds in this environment. Original3,900-replicate artifacts are untouched.
