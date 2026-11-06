# Recovery ledger

All outcomes here are simulated. `experiments/recovery.py` reads only `outputs/input_only/trial_inputs.csv` and the locked participant/schedule manifest; it asserts that choice, feedback and response-time columns are absent. It never opens the acquired trial CSV or real development/validation responses.

## Sequence of decisions (2026-10-28, before validation opening)

1. During implementation, the model optimizer was tightened from relative tolerance1e-12 to1e-14, with a maximum absolute gradient requirement. Independent code audit prompted this numerical correction. Model features did not change.
2. `pilot/`: ten simulations in each of five scenarios, no effect-interval bootstrap. The initial positive injections were calibrated on deterministic mean trajectories. Their nominal 5/10 percentage-point differences became approximately4.4–4.5/9.1 points after participant heterogeneity, omissions and the lapse mixture. These pilot results are preserved rather than silently relabeled.
3. The common-law null was strengthened: history coefficients depend on total latent sensory skill, including its group-dependent distribution, under the SAME mapping in both groups. Early calibration is noisy. This asks whether first200 adjustment can actually distinguish a direct history difference from a common sensory–history relationship.
4. `final/`:100 simulations per scenario, six scenarios including a negative5-point injection. The positive/negative injections are recalibrated using ten separate deterministic prior-predictive draws to target mean true differences of+5,+10,+5 and−5points. This adjusts simulation coefficients, not the scientific±5point threshold.
5. Nested effect intervals refit condition-stratified participant bootstraps (20 outer simulations×50 inner resamples; negative5 uses10×50). Sparse schedule×condition cells are not frozen. Fifty inner resamples give coarse interval-tail estimates;20/10 outer cases give imprecise coverage-rate estimates. Report those limitations with the rates.
6. A reporting-label correction separates nominal5point boundary cases from strict equivalence mistakes. The initial `false_equivalence` flag used realized absolute truth≥.045, which can include truths just inside±.05. Final reporting calls that `boundary_interval_inside_margin` and reserves `false_equivalence` for realized absolute truth≥.05. Estimates, intervals, coverage and scores are unchanged. The pre-correction table is preserved when finalizing the in-flight run.

## Generative structure

The simulator retains actual contrasts, scheduled sides, probability sequences, participant allocation and the locked split. Each participant has random response bias, motor persistence, sensory skill and three history weights. Each schedule has a shared random three-dimensional history contribution. Choice is generated from signed categorical contrast evidence, past-choice persistence and chronological feedback-side EWMA history, with explicit lapses and omissions. Teaching/discovery differ strongly in early acquisition and sensory/lapse/motor nuisance structure. The stronger common-law scenarios also include time-varying history and response bias. Feedback is simulated as choice×scheduled-side on responded trials; omissions provide no target-side evidence.

The positive injection begins at trial200 and changes the population history coefficient by condition. Its true standardized effect changes only this direct history term, holds each simulated participant's other traits and history fixed, imposes zero current contrast, aligns by the old majority and averages offsets0–19 equally by validation participant. This exactly matches the fitted observable-standardization mask, but the fitted first200 calibration is an imperfect proxy for latent traits.

This is a deliberately broader generator than the fitted empirical psychometric model. A failure under common-law carryover is a measured limitation of the estimator, not evidence for a direct route-specific adaptation mechanism. The generator is a scientific control, not a claim that these are the participants' true latent traits.

## Files and reproduction

- `final/scenario_definitions.json`: exact injection vectors, scales and calibration draws.
- `final/replicates.csv`: every simulation, seed, true/estimated effect, mean held-out score, subject-bootstrap score interval, optimization quality and any nested effect interval.
- `final/scores_<scenario>_<rep>.csv`: participant-resolved prediction differences.
- `final/truth_<scenario>_<rep>.json`: exact realized true effects and generator diagnostics.
- `final/bootstrap_<scenario>_<rep>.csv`: fitted-effect bootstrap draws.
- `final/summary.json` and `final/manifest.json`: aggregate results and input/config provenance.
- `final/recovery.png` and `final/recovery.pdf`: effect recovery and predictive discrimination, with uncertainty across independent simulations.
- `final_run.log`: progress and final summary.

Run from repository root:

```sh
.venv/bin/python campaigns/human_learning_routes_2026-10-28/experiments/recovery.py --reps 100 --bootstrap-outer 20 --effect-bootstraps 50 --workers 2 --refine-injection --label final_reproduced
```

The protected biological responses are not necessary to reproduce these controls.
