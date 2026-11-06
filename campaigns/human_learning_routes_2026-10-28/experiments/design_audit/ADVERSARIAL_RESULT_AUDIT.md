# Independent adversarial result audit

2026-10-28. Validation inspection began only after the lead authorized it and both `VALIDATION_OPENED.json` and the completed primary `summary.json` existed. Earlier design, implementation and synthetic challenges did not inspect real validation choices. This audit owns no primary analysis files.

## Verified result

The original134,562,545-byte CSV matches its declared MD5. Independent reconstruction from the original bytes and saved fit JSON reproduces all23,400 reserved-trial probabilities under all three models with maximum absolute error5.6e-16. The audit imports neither `model.py` nor `analysis.py`. It independently constructs first200 calibration covariates, causal feedback traces, prior choice, sensory/time terms, condition/calibration interactions, Gaussian residual variance and Gauss–Hermite integration. All39 schedule hashes, feedback-side identities and primary switch/omission masks match. There are2,867 responding primary trials.

Independently recovered equal-person condition-minus-shared log-score gain is **−0.0010516370056980623 nats/choice**; maximum participant-score discrepancy is9.1e-17. The reported subject-bootstrap interval is[−0.002910,+0.000723]. Thus the frozen condition-dependent history account did not improve reserved prediction, and the interval does not establish a reliable superiority of either account. Point estimates are negative in both held-out strata and remain negative on removal of any single schedule.

The reported shared-history gain over the no-history baseline is+0.03396 nats/choice,[+0.02457,+0.04306], with a positive point estimate on all ten evaluated schedules. The no-history account already has previous-choice, sensory, time, condition and calibration flexibility. This establishes useful predictive information in the additional target-history basis under the tested model comparison. It does not establish which psychological process generates that information.

## Equivalence is not supported

The standardized condition-history contrast is+2.92 percentage points, with a development-subject-refit interval[−1.19,+7.70] points. That interval crosses the prespecified+5-point boundary. Even if it had fit within the boundary, the pre-validation recovery gate already failed: mean recovery of a−5-point injection was approximately−2.71 points, interval coverage was7/10 in that small nested test, and2/10 boundary injections gave false-equivalence intervals. The five-point target must remain fixed; it cannot be widened to accommodate the observation.

The broader recovery comparison detects positive5-point magnitude, positive5-point shape and negative5-point differences only48%,18% and26% of the time, respectively, under its tested generators; a positive10-point difference is detected94% of the time. These numbers quantify the fitted procedure's discrimination in those simulations. They are not universal power estimates or a biological upper bound.

The independent calibration challenge explains part of the asymmetry. Supplying oracle latent skill removes shared-law proxy bias but reveals attenuation on both effect signs. Wider effect priors reduce but do not eliminate it. Simple rescaling or contrast-aware early summaries do not consistently solve the problem. This supports an honest measured discrimination limit, not a conclusion that teaching and discovery produce identical updating.

## The observed history pattern is repulsive

The shared model's long-history coefficient is negative. More decisively, the prespecified diagnostic removing only pre-switch feedback traces produces a negative old-majority-aligned component: approximately−4.78 points in discovery and−11.91 points in taught participants in the first five trials, remaining negative while attenuating later. Those are model-based components on each group's reference covariates; their difference is not an independently validated teaching effect.

This should be described as target-side-history predictive association and a repulsive long-history component. Do not automatically label it adaptive Bayesian use of block probabilities, perseveration of an old prior, or feedback-specific learning. Visual stimulus exposure, motor/choice processes, sensory adaptation and feedback are correlated in the task; `choice × feedback` recovers the scheduled target side. The independent extraction rules out a simple coding/sign error but cannot identify the psychological mechanism.

The original recovery generators have positive sustained-history influence, unlike this empirical pattern. This audit therefore requested a single post-validation recovery stress test with a repulsive baseline based on development coefficients, preserving the frozen empirical comparison. That check is now complete; the final addendum below records its outcome. Original and supplementary recovery rates, and the additional-observation simulations, remain explicitly conditional on their generators.

## Robustness and remaining objections

The prespecified sensitivity table has negative condition-minus-shared point estimates under both random-SD alternatives, a wider condition-history prior, exclusion of assignment exceptions, common date support, asymmetric sensory saturation, the later301–600 interval, zero contrast only, all later responses and equal schedule/condition weighting. This is useful consistency. It does not turn an interval spanning zero into equivalence, nor make the nonrandom teaching package causal.

Important residual limitations are the approximate joint-MAP fitting criterion, fixed residual distribution, imperfect nuisance/acquisition measurement, potentially shared latent-skill laws that give condition residual proxy value, and only three entirely unseen schedules. The ordinary score interval conditions on the fitted model and realized schedules; the standardized effect interval conditions on reference histories/calibration. Schedule-specific and subject-specific results should remain accessible.

The concrete additional-observation challenge tests160/320 independent simulated people with the same schedule universe, with and without800 extra idealized sensory observations and a wider effect prior. The320-person combined procedure improves overall detection but still misses the80% unseen-schedule target for the negative effect and selects the condition model in5/30 shared-law nulls. It is not a validated prescription. See `SAMPLE_SIZE_CHALLENGE_REPORT.md` for exact counts and scope.

## Recommended conclusion

**Later target-history information transfers to reserved people and schedules, but teaching-condition information supplies no demonstrated incremental predictive gain under the frozen comparison. The study does not establish±5-point equivalence. It identifies a measured, asymmetric discrimination limit and nuisance/measurement alternatives that survive.**

The empirical response pattern should be reported before theoretical adaptation language. A stronger shared-process or causal teaching claim would exceed these results. This is a substantive completed predictive test with an informative failure of equivalence, provided the final report preserves the failed recovery gate and generator qualifications.

Reproduce the independent probability audit with `.venv/bin/python campaigns/human_learning_routes_2026-10-28/experiments/design_audit/independent_validation_audit.py`. Machine-readable evidence and hashes are in `independent_validation_audit.json`.

## Final addendum: repulsive recovery and report review

The requested bounded generator check is complete. I inspected `experiments/repulsive_recovery.py`, `outputs/repulsive_recovery/supplementary/manifest.json`, its report and the main `REPORT.md`. No additional model, fit or simulation was run for this review.

The supplementary simulator takes its shared history and previous-choice means from the saved DEVELOPMENT fit, retains the main simulator's heterogeneity, common latent-skill law and nuisance structure, and recalibrates injected effects using independent synthetic draws. It imports the frozen fitting/evaluation procedures. The manifest records unchanged imported source hashes across execution, convergence of both fits for all400 simulated datasets, separate seeds and explicit post-validation status. No empirical validation outcomes were used to fit or retune a model in this supplement.

Across100 replications per scenario, a positive participant-score interval occurred in1 shared null,44 positive-five-point slow-history shifts,47 negative-five-point shifts and23 five-point redistributions. The negative contrast's true mean was−5.02 points and its estimated mean−2.70. Thus the qualitative discrimination limitation persists in the repulsive regime, although the negative-effect detection rate differs materially from the initial26%. Neither rate is universal task power. No nested effect-interval coverage was estimated in this supplement, and it cannot rescue the failed equivalence gate.

The supplementary null's−8.83-point quantity is the **total history contribution**, aligned with the old majority at zero contrast, relative to removing all history. It differs from the human model diagnostic that removes only pre-switch traces. The accompanying42.52% old-majority probability confirms the intended repulsive response regime. This distinction should be retained when citing the number; it is not a directly comparable estimate of pre-switch memory.

The main report's principal scores, sample counts, percentage-point units, uncertainty qualifications, discrimination claims, calibration diagnosis and additional-observation limitations agree with the inspected evidence. It correctly states that the study tests a bounded prediction procedure and does not prove no better analysis could distinguish the accounts. The recommended minor wording clarification is to call the longer-history component **fitted** and to name the supplementary−8.83-point diagnostic as total history influence aligned with old majority.

**Final audit disposition: no remaining substantive blocker to the report's bounded conclusion.** Target-history predictors transfer; additional condition-history terms show no demonstrated predictive gain; five-point equivalence is unsupported. Numerical reproducibility, subject-level evaluation and adversarial controls support those statements, while causal, mechanism-specific and unrestricted schedule-population claims remain unwarranted.
