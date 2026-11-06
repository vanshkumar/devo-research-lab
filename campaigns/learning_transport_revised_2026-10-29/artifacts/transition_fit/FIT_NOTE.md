# Finite shared session-transition fit

Completed 2026-10-29. This fit uses consumed source development evidence only. It does not earn an old gate or expose independent target data.

The fixed grid selected **rho=0.9**. The equally weighted mean of laboratory six-bin population-curve errors is **3.9909 pp**, versus **4.4262 pp** at rho=1. This is a development comparison within fitting data, not a transport result or a biological retention estimate.

| rho | Equal-lab curve MAE (pp) |
|---:|---:|
| 0.5 | 8.4410 |
| 0.6 | 7.5102 |
| 0.7 | 6.2683 |
| 0.8 | 4.8742 |
| 0.9 | 3.9909 |
| 1.0 | 4.4262 |

Of 62 allocated fitting animals, 46 had the full 1,000-prefix/3,000-future opportunity horizon. The 16 short histories remain individually documented in FIT_DISPOSITION.json. Each returned history is capped at 4,000 already-consumed rows. The 46 eligible histories span 7 labs. Every grid cell recomputed prefix MAP/Fisher calibration under its own transition, then generated 256 autonomous future particles with common historical seeds.

The 6×46=276 forecast grid completed in **443.39 seconds**. FIT_STDERR.log is empty. The selected [model](../../model_session_transition.npz) has SHA256 `c914494c5c8680c1989242d539912f686442dd59c5b64d609efc436834e03f5d`. No within-session GRU parameter was fitted.

Synthetic chronology checks: rho=1 reproduces the old sequence exactly; splitting at an omitted session-first opportunity reproduces continuous processing exactly; attenuation occurs before prediction and survives omission; vectorized versus scalar recurrence differs by at most 2.22e-16. The initial runtime benchmark failure on 402-row IBL-T1 is retained in FIRST_BENCHMARK_FAILURE.md; the successful metadata-selected NYU-07 benchmark changed no fit prescription.

The next finite comparison uses the separately specified 64 consumed source animals. The broader cross-curriculum question remains unresolved by this fit.
