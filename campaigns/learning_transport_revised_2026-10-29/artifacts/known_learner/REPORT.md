# The finite grid recovers a known conditional session law

Completed 2026-10-29. The six-value fit selected the true **rho=0.8** in this
prespecified synthetic control. Against independently simulated expected laws,
the recovered prescription's population-curve error is **0.0655 percentage
points** under the standard trainer and **0.1642 pp** under the fixed trainer.
Both are below the frozen 1 pp predictive tolerance. This shows that coherent
prefix processing and autonomous future generation can recover and transport
the specified conditional law. It does not establish biological transfer.

The real-data transition fit selected rho=0.9; this control does not replace it.
The separate decision-rule sensitivity failure also remains a failure. No Pan
prefix or outcome was opened, and no criterion was changed after simulation.

## Exactly what was tested

Seven consumed fitting prefixes represent seven laboratories, with one eligible
subject per lab chosen by SHA256(subject), before simulated outcomes. Each
context supplies only its first 1,000 observed opportunities and the next 3,000
session-start indicators from saved fit artifacts. The control never reads an
actual future response. Its latent generator is the frozen within-session GRU
plus rho=0.8 applied before every subsequent session's first prediction,
including an omitted opportunity.

The truth ensembles use 2,048 particles with subject seed+910000, independently
of the original 256-particle candidate forecasts. All particles generate their
own actions, omissions, binary feedback and trainer responses. Prefix nuisance
calibration and its joint coefficient/memory uncertainty use the same coherent
rho prescription. The six candidate losses use equal labs and equal bins:

| Candidate rho | Mean laboratory curve error (pp) |
|---:|---:|
| 0.5 | 2.8585 |
| 0.6 | 2.2522 |
| 0.7 | 1.3658 |
| **0.8** | **0.4310** |
| 0.9 | 1.2948 |
| 1.0 | 3.3880 |

The declared largest-rho-within-0.001 tie rule selects 0.8. This is recovery of
a known on-grid coefficient in seven fixed prefix contexts. It does not test
learning the GRU from new whole animals or identify a biological parameter.

The selected law then receives fresh 512-particle forecasts under both policies:

| Trainer | Population curve error (pp) | Mean laboratory curve error (pp) | Truth scalar MC SE (pp) | Forecast scalar MC SE (pp) |
|---|---:|---:|---:|---:|
| Standard adaptive | 0.0655 | 0.3753 | 0.0592 | 0.1136 |
| Fixed mixed | 0.1642 | 0.2633 | 0.0382 | 0.0751 |

Population error averages absolute errors after combining the seven equally
weighted contexts; laboratory error takes the absolute value separately within
each context. Their difference is aggregation, not a changed endpoint. These
MC standard errors describe finite simulation only, not animal or environment
uncertainty.

Under the fixed trainer, growth has 19.2018 pp population-curve error. The
recovered law's advantage is **19.0376 pp**. The known generator's mean
fixed-minus-standard contrast is **19.5505 pp**. These are simulated consequences
of the supplied law and trainers, not an empirical curriculum effect.

## Verification and reproduction

[The plan](PLAN.md), code and 57 input pins were frozen before simulation in
[FREEZE.json](FREEZE.json), SHA256
`2342ea5aaef755d2570654fba4349a05f296b944a91cf8d06e128a9d4c7e2616`.
[RESULT.json](RESULT.json) retains every grid loss, per-prefix curve and the
35 generated-forecast hashes. The run took 175.16 seconds with empty stderr.

An independently written scalar aggregation of the saved generated curves
reproduces all nine decisive numerical summaries within 1.31e-16 and verifies
all 35 forecast hashes. See [INDEPENDENT_SUMMARY_CHECK.json](INDEPENDENT_SUMMARY_CHECK.json).
The separate synthetic chronology audit verifies the omitted-boundary,
prediction-before-update and continuous-versus-split conventions.

From repo root, using the existing Python runtime:

```sh
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONDONTWRITEBYTECODE=1 campaigns/learning_rule_transport_2026-10-28/.modelenv/bin/python campaigns/learning_transport_revised_2026-10-29/code/known_learner_control.py --run
campaigns/learning_rule_transport_2026-10-28/.modelenv/bin/python campaigns/learning_transport_revised_2026-10-29/artifacts/known_learner/reconstruct.py
```

The first command regenerates synthetic control outputs only and appends a new
control access record; preserve the original artifacts separately if retaining
their exact container hashes. It neither fits an empirical learner nor accesses
independent actual futures.
