# Long-memory null sensitivity

2026-10-28. The original frozen primary estimator was applied to synthetic outcomes on the20reserved participants' **input sequences only**. No empirical reserved outcome was accessed and the original3,900-replicate recovery was not changed.

The generator has fixed fast/slow retention(.65,.995), gains(.65,.30), flexible current-cell learning, direct current endpoint effects, 3° colored motor/observation noise, gain/noise heterogeneity, fast process noise SD.08°, and the original fixed3% omission mask. Slow retention.995 has a half-life of approximately138trials, well beyond the estimator's20-trial nuisance history. The two drift settings use the same300random seeds, so these are paired challenges rather than600independent simulation draws.

| Slow retention | Drift scale | Mean estimated θ | Mean noiseless projection | Mean SE | False positive | Coverage of true θ=0 |
|---|---:|---:|---:|---:|---:|---:|
| .995 | .6° | +.000353° | −.007831° | .231344° | 17/300 (5.67%) | 283/300 (94.33%) |
| .995 | 3.0° | +.000625° | −.007831° | .231504° | 17/300 (5.67%) | 283/300 (94.33%) |

The binomial95%interval for false positives is3.34–8.92%. Neither scenario produces a95%interval wholly inside±.2°. These controls show no substantial false-positive inflation from this particular longer-memory/stronger-drift combination on the actual balanced schedules. They do not establish recovery for every long-memory, outcome-dependent missingness or nonlinear state/readout process. Sensitivity at.2° remains weak as documented in the main recovery.

Reproduce from repository root:

```sh
.venv/bin/python campaigns/target_event_carryover_2026-10-28/experiments/recovery_slow_null.py --reps 300
```

Full summary and binomial intervals: `recovery_slow_null_summary.json`. Per-replicate outputs: `recovery_slow_null_drift_0.6.json`, `recovery_slow_null_drift_3.0.json`. Log: `../logs/recovery_slow_null.log`.
