# Recovery result: predictive specificity survives, five-point equivalence does not

2026-10-28. These are **simulated outcomes on the actual stimulus schedules and locked split**, not results from the protected human responses. Six hundred complete simulated datasets were fit and evaluated. An additional5,500 participant-bootstrap refits assessed effect-interval behavior. Every recorded optimization satisfied the absolute-gradient requirement of.001.

The score comparison detected a true approximately10-percentage-point slow-history difference in94/100 simulations and produced positive score intervals in only3/100 and5/100 shared-adaptation null simulations. At the prespecified5-point scale, however, detection ranged from18% to48% according to the response pattern and direction. The standardized-effect estimator and its uncorrected bootstrap intervals also showed consequential shrinkage and incomplete coverage. **This procedure cannot support a general±5-point equivalence claim.**

## Complete simulation results

Effect units are percentage points of old-context-aligned choice probability, standardized to zero current contrast over the first20 post-switch trials and averaged equally over reserved participants. “Score detected” means the lower bound of the participant-bootstrap95% interval for condition-minus-shared log score is above zero. For nulls it is a false-positive count; for positive controls it is conditional detection power.

| Generative condition | True mean | Estimated mean | Estimate SD | Mean held-out log-score gain | Score detected /100 |
|---|---:|---:|---:|---:|---:|
| Shared history; strong sensory/lapse/motor/acquisition differences |0.00|+0.90|1.71|+0.000020|5|
| Shared sensory–history law plus nonstationarity |0.00|+0.91|1.88|−0.000121|3|
| Slow-history increase |+5.00|+4.81|1.72|+0.002080|48|
| Fast-to-slow history redistribution |+4.98|+4.64|1.86|+0.000693|18|
| Larger slow-history increase |+9.97|+7.98|1.71|+0.007829|94|
| Slow-history decrease |−5.00|−2.71|1.76|+0.000966|26|

These power estimates are conditional on the specified generator and existing ten schedules, including three entire held-out schedules. They are not universal guarantees for every process with the same mean effect. In particular, a mean five-point effect does not uniquely specify the post-switch response trajectory or predictive information available in the low-contrast evaluation trials.

![Recovery and predictive discrimination](/Users/vanshkumar/Documents/repos/devo-research-lab/campaigns/human_learning_routes_2026-10-28/outputs/recovery/final/recovery.png)

## Interval calibration

Intervals refit the development model after sampling participants within condition. The validation histories and calibration observations are held as the standardization reference. Twenty independent simulated datasets per cell received50 bootstrap refits; the negative5-point cell received ten. These small outer/inner counts make interval-rate estimates coarse, but they expose clear failure cases.

| Generative condition | Nested datasets | Coverage of realized truth | Effect interval excludes zero | Strict false equivalence |
|---|---:|---:|---:|---:|
| Nuisance null |20|17/20|3/20|0/20|
| Common-law null |20|18/20|2/20|0/20|
| +5 slow |20|17/20|15/20|2/20|
| +5 redistribution |20|17/20|17/20|0/20|
| +10 slow |20|15/20|20/20|0/20|
| −5 slow |10|7/10|5/10|2/10|

Strict false equivalence requires an interval wholly inside(−.05,+.05) while the **realized** true absolute effect is at least.05. The early implementation used.045 to identify nominal five-point injections. That was corrected before interpreting final rates; `replicates_before_reporting_correction.csv` retains the old labeling and `reporting_correction.json` records hashes. Effect estimates, intervals, true values, score results and coverage were unchanged. Two additional redistribution cases have intervals inside the margin but truths just inside five points; these are coverage failures, not strict equivalence mistakes.

The negative case is especially informative: a real mean−5.00-point difference is estimated at only−2.71points, and two of ten nested intervals incorrectly exclude differences as large as the true effect. A small observed point estimate or an ordinary bootstrap interval inside the margin therefore cannot establish shared adaptation using this pipeline.

## What was challenged and what remains limited

Both nulls include different sensory, lapse, motor and early-acquisition trajectories across conditions, heterogeneous participants and schedule effects. The common-law null additionally makes history weights depend on total latent sensory skill under the same mapping in both groups. Different sensory distributions can consequently produce different marginal history distributions without a direct condition-specific adaptation term. First200 behavioral covariates are noisy measurements of those traits.

The simulator uses an explicit lapse mixture and time-varying history weights, while the fitted model uses empirical sensory/asymptote flexibility and a fixed history basis. The model is intentionally challenged beyond an exactly matched simulator. The separate calibration challenge in `experiments/design_audit/calibration_challenge/` tests improved first200 measurements, an oracle latent-skill covariate and wider group-history regularization. It distinguishes residual sensory-proxy bias from shrinkage/link mismatch; merely adding more independent sensory observations does not monotonically restore recovery.

One supplementary single-seed diagnostic varied the condition-history coefficient prior SD from1 to2 to4. For the10-point slow-history case, the estimated effect rose from7.32 to8.53 to8.90points. This identifies a contribution of regularization but is not a replacement analysis or a selected primary model. Its full record is `prior_diagnostic_one_rep.json`.

The valid inference from these controls is narrower than “the data cannot detect anything”: large slow-history differences are readily detected and shared-nuisance null score false positives are modest. What fails is the stronger inference that nonsignificant prediction improvement or a small regularized effect proves equivalence at five points. Distinguishing smaller shifts requires more informative independent observations and a validated estimator; the exact needed observations depend on whether the alternative changes history amplitude, redistributes the kernel or changes its direction.

## Reproduction and provenance

Run from the repository root:

```sh
.venv/bin/python campaigns/human_learning_routes_2026-10-28/experiments/recovery.py --reps 100 --bootstrap-outer 20 --effect-bootstraps 50 --workers 2 --refine-injection --label final_reproduced
```

`final/manifest.json` records inputs, split hash, configuration, seeds and runtime. `scenario_definitions.json` records every synthetic injection and its independent calibration. `replicates.csv`, the participant score tables, true-effect tables and saved bootstrap draws support every aggregate above. The injection calibration used separate deterministic prior-predictive draws and kept the scientific±5-point threshold fixed. The initial ten-replicate pilot and the later reporting correction remain inspectable.

The engine never opens the acquired human outcome CSV. Its input loader asserts the absence of choice, feedback and response-time columns; all these outcomes are generated within the simulation. The efficient bootstrap construction was checked against full independent feature reconstruction to1e-15 on simulated data (`implementation_checks.json`).
