# Protocol v1 review and input-only coverage

2026-10-28. Reviewed `protocol/ANALYSIS_PROTOCOL_v1.md`, `SPLIT_LOCK.json`, `split_manifest.csv`, and input-only trial arrays. No choices, feedback, RTs or validation responses inspected.

The locked design is sensible and matches the independent recommendations. All ten actual schedules have both conditions. Three whole schedules are held out (25 participants); another 14 people are held out on seven familiar schedules. Development has 41 participants. Prefix participant006 is confined to development. The v1 plan correctly restricts eligible switches to those starting at zero-based trial200 or later, with a most-recent-switch rule.

Independent reconstruction from input arrays gives the following **opportunities before omissions**, unlike a response count:

| Partition | Condition | Low contrast offsets0–29 | Low contrast offsets0–19 | Zero contrast offsets0–29 |
|---|---:|---:|---:|---:|
| Development | Discovery | 1554 | 1077 | 460 |
| Development | Taught | 1345 | 944 | 393 |
| Familiar-schedule validation | Discovery | 501 | 350 | 148 |
| Familiar-schedule validation | Taught | 501 | 350 | 148 |
| Unseen-schedule validation | Discovery | 908 | 644 | 277 |
| Unseen-schedule validation | Taught | 985 | 694 | 305 |

Reproduce: `.venv/bin/python campaigns/human_learning_routes_2026-10-28/experiments/design_audit/check_input_coverage.py`.

The five-percentage-point standardized response margin is ambitious but scientifically interpretable. For perspective only, a raw first20 low-contrast group difference with independent Bernoulli observations near0.5 would already have a pooled-validation95% halfwidth about4.3 percentage points (994 versus1044 opportunities); subject dependence, omissions and schedule replication can widen it. The standardized model contrast is a different estimand and can be more precise. This calculation neither proves power nor justifies changing the margin.

The selected model includes condition-specific signed contrast categories, response bias, previous choice and time trends, plus calibration covariates predicting both nuisance and history weights under a common relationship. This gives a suitable compact predictive test. Signed contrast categories provide empirical sensory/asymptote flexibility; they are not separately identified lapse probabilities.

## Required numerical and inference checks

1. The penalized logistic MAP fit is convex with fixed positive prior scales. Check finite data/objective, max absolute gradient below1e-3, and agreement from at least two starts on objective/predictions for the decisive development fit. Do not infer convergence from an optimizer success flag alone.
2. Preserve warnings. If the known Mac numerical warning recurs, compare explicit contractions and finite checks before suppressing anything.
3. Frozen residual-SD sensitivity should include a factor0.5 and2 around the primary scale. If one common scale is used for differently scaled features, record feature scales.
4. Integration over a fixed residual prior conditioned on calibration features is an approximate conditional population predictor. It is not an individual posterior fitted from all200 calibration outcomes unless an explicit posterior calculation occurs. Both accounts must use the same procedure.
5. For the standardized response-effect interval, bootstrap whole development participants and refit. A person sampled twice must receive two replicate IDs, or frequency weights must multiply both their likelihood and their random-effect penalty. Duplicating rows under a single ID with one penalty changes the shrinkage model.
6. Use at least200 replicates for a final bootstrap interval where local cost allows. Quantify simulation coverage and bias at zero and near±.05; an interval narrow because of fixed-prior shrinkage is not empirical equivalence. Parametric simulation conditional on fitted priors is evidence only within that tested generator family.
7. A fixed-trained-model participant bootstrap of validation paired scores gives uncertainty conditional on the fitted model and realized schedules. It does not include training-set variation. Label it and pair it with schedule-resolved results, development refit sensitivity and recovery.

Awaiting final model implementation for adversarial leakage and extraction review. No blocking issue found in v1 text; implementation and recovery remain essential.
