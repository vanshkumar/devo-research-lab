# Independent design audit before validation

2026-10-28. Audit owner: `design_audit` native subagent. No trial outcomes, full trajectories or group performance summaries were inspected for this document. The parent owns acquisition, exact schedules, final protocol and execution. These are recommendations, not a claim that the final protocol already implements them.

## What the test can establish

The primary question is whether condition carries incremental predictive information about **later responses to recent evidence**, beyond the same participant heterogeneity, sensory response, lapse, response-bias and acquisition flexibility. A predictive improvement would be an association under this teaching package and allocation procedure. A null comparison is informative only with demonstrated sensitivity on actual schedules and an explicit bound on an observable response contrast.

Do not equate a history-kernel coefficient or fitted time constant with a neural learning mechanism. Different kernels can predict almost identically on long blocks. Reconstruction/recovery must address prediction, observable response contrasts and parameter recovery separately.

## Protected evaluation

Recommended locked split, assuming ten sufficiently replicated actual schedules:

1. Reconstruct schedule identity from the complete input arrays (signed stimulus contrast, scheduled target side and `probabilityLeft`), retaining a separate block-only hash. Do not use last ID digit as the definitive schedule label.
2. With a saved seed selected before outcomes, reserve three complete schedules as unseen-schedule validation. Balance only input-derived coverage, group counts and protocol era; enumerate a predefined acceptable set rather than choosing a favorable seed after outcomes.
3. From the seven remaining schedules, reserve one participant per condition per schedule where available. This is unseen-participant/seen-schedule validation. The remaining participants form development/training, likely around 42 rather than all 80.
4. Force the participant from the already inspected trial prefix into development. If its entire schedule would otherwise be held out, redraw using the frozen rule and record why. Downloading bytes is not outcome inspection; decoding or plotting the prefix is.
5. Report seen-schedule and unseen-schedule validation separately and together. A strong transfer claim needs the same direction on both and no domination by one schedule. With only three unseen schedules, uncertainty about a population of schedules will remain wide; participant precision does not repair that limitation.

If actual schedules or recovery show the locked split insufficient **before validation**, a frozen leave-one-schedule-out procedure is defensible. All consequential model selection must use a separate development subset or inner training folds. Each scored participant's complete schedule must be absent from that fold's group fitting. In that case write clearly that held-out outcomes are used as training outcomes in other folds under a frozen algorithm; they were not a single globally untouched test set. Naive fold-standard-error bars are invalid because training sets overlap. The primary paper [Bengio and Grandvalet (2004)](https://www.jmlr.org/papers/v5/grandvalet04a.html) establishes the general variance-estimation limitation; use this as a reason for transparent uncertainty, not as a reason to avoid testing.

## Endpoint to freeze

Use one-indexed trials 201–600. A switch is a genuine change between the two biased probabilities; transitions from an initial unbiased block are a distinct secondary diagnostic. Select primary evaluation trials by inputs only: absolute contrast at most 0.125 (subject to verification of the actual discrete levels), trial offsets 0–29 after each switch, censored at the next switch and trial 600. Offset zero denotes the first trial under the new schedule probability. Specify contrast handling for exact zeros and signed floating values.

Responding trials enter the binary choice score. Omissions must remain in a denominator/coverage table; do not replace them with random choices or silently discard subjects with many omissions. A secondary three-category response/omission model or inverse-coverage stress test can reveal whether selective response masks differences. Predeclare a minimum scored-trial count if necessary from input coverage alone; do not exclude low-accuracy participants.

For each held-out participant compute

`d_i = mean_t [log P_condition(y_it) - log P_shared(y_it)]`

over their primary trials. The primary point estimate is the equal-participant mean of `d_i`, in nats/choice; also publish the trial-weighted value and each participant's denominator. Report Brier difference and calibration as secondary diagnostics. Equal-participant weighting prevents people with fewer omissions from silently determining the estimand.

Publish old-majority-aligned choice curves in offsets 0–4, 5–9, 10–19, 20–29 and a preswitch reference, equal-weighting participants and explicitly reporting counts. These curves are descriptive because realized stimulus contrast/side and participant mix can differ across bins. Publish a model-standardized curve with identical current contrasts, common histories and common nuisance values separately.

## A simple matched model family

Use a regularized logistic history model with participant intercepts, sensory coefficients and history coefficients. A compact history basis can use causal exponential traces with fixed time constants 2, 8 and 32 trials (or fixed log-spaced lag bins). It represents recent evidence over multiple scales without making the learning-rate label carry the entire scientific claim.

Predictors at trial `t` may use current visible signed contrast, time/acquisition basis and **strictly past** choice/feedback. A feedback-reconstructed target side is available only after a responding trial if the feedback rule and response coding are known. Never use current correctness, scheduled current hidden side at zero contrast, block probability or time since hidden switch to predict ordinary choices. Hidden block labels define windows only. A block-label predictor is an explicitly labeled oracle diagnostic.

The two models share all terms and random-effect treatment. Both allow condition-specific sensory functions, lapse/asymptotic errors, motor/response bias, and early acquisition trajectories. Both allow the same distribution of participant-level history deviations. The shared model constrains later group means of history coefficients to agree. The alternative adds only condition-by-later-history mean terms, with the same regularization scale as comparable effects. If early condition-history interactions are allowed, confine their basis to the first 200 trials or use a frozen decay whose residual after 200 is explicitly measured.

For lapse handling, either use a bounded mixture `P = lapse_left + (1-lapse_left-lapse_right)*sigmoid(eta)` with regularized participant/condition lapse terms, or use a sufficiently flexible signed contrast function that allows distinct high-contrast asymptotes, and label the latter empirical lapse flexibility rather than literal lapse probabilities. A single linear contrast coefficient alone does not adequately represent different psychometric saturation. A two-sided motor bias should not be mistaken for a symmetric lapse.

For a held-out person, use the first 200 trials as a permitted calibration interval. Fit/infer participant effects using only this interval while holding group parameters fixed. Integrate the posterior/random effects for later prediction where feasible; if using MAP, report it and include its shrinkage bias in recovery. Do not fit their individual parameters using trials 201–600 and call those later choices withheld. Updating a participant posterior after each observed later response is acceptable only under a frozen strictly chronological filter identical in both models; keep a no-later-refitting sensitivity so different online adaptation speeds are not confused with group effects.

**Acquisition carryover pitfall:** placing sensory/acquisition covariates in the current choice logit is not equivalent to explaining history-weight differences by acquisition. A shared relationship `history_weight = f(sensitivity, early_acquisition)` can create different marginal group history weights if the groups' sensitivity distributions differ. Include frozen calibration-derived sensitivity/acquisition predictors of history coefficients in both models, or run a strong common-law recovery null and label the remaining ambiguity. Avoid conditioning the cohort on achieved matching accuracy.

## Observable practical-equivalence target

Proposed meaningful response scale: a 0.05 absolute difference in standardized old-majority choice probability averaged over the first 20 trials after a switch at zero/low contrast. This is interpretable as one additional old-context choice per 20 otherwise comparable ambiguous decisions. It is a design judgment, not a literature-established minimal important difference.

Define standardization before validation. Apply the two condition-specific **adaptation components** to the same actual input history distribution, with nuisance coefficients fixed to a pooled reference and random effects drawn from the same distribution. The resulting condition contrast isolates the fitted adaptation component; it is not a causal effect of teaching. Report the signed average and a noncancelling magnitude (e.g. RMS probability difference) so early/late reversals cannot cancel. The five-percentage-point boundary applies to the predeclared scalar, not to whichever post hoc bin looks smallest.

An alternative score threshold can be calibrated from simulations at that response scale, but log-score gain has no universal conversion to percentage-point adaptation differences. A shared-model score win cannot establish response equivalence by itself. Equivalence requires a two-sided uncertainty interval contained in the frozen response margin, plus adequate recovery for both positive and negative injected differences. If this fails, report the measured interval/ambiguity and the additional participants or schedules needed under the calibrated simulation.

## Recovery that can justify a conclusion

Use the actual input schedules, split, scoring mask, condition counts and omissions mechanism. Generate complete chronological responses and feedback under each simulation; do not simulate history-dependent choices while retaining empirical choices as predictors. Run the whole fitting, permitted calibration and scoring procedure.

Predeclare a grid including:

- Shared adaptation with individual and schedule heterogeneity; different condition sensory sensitivity, asymmetric lapses, response bias and early acquisition.
- Shared adaptation with participant history coefficients correlated with sensory sensitivity/acquisition under the same relationship in both conditions.
- Shared nonstationary later history weighting that changes with trial number equally in both conditions; schedule composition can otherwise manufacture group interactions.
- Meaningful condition differences of both signs calibrated to the five-percentage-point observable scale, and a larger ten-percentage-point effect. Include a change of history magnitude and a change of kernel shape/time course.
- Misspecified context-inference generator with a shared rule, to reveal whether the chosen history family produces spurious condition gains because group nuisance differs.

For each, save score gain distribution, sign/threshold detection probability, fitted response-contrast bias and interval coverage, and rate of a false equivalence conclusion. Use at least 100 replications for the decisive regimes if compute permits; with 100, uncertainty near a 5% false-positive rate remains about several percentage points. Use fewer only as a preliminary implementation check. Failure to recover a meaningful effect triggers a pre-validation amendment to measurement/model or a quantified discrimination limit, not automatic equivalence.

## Uncertainty and strongest challenges

For a single fixed trained model and fixed realized schedules, use participant resampling, stratified by condition and schedule as replication permits. Resample whole participant trajectories and paired model scores. This supports a conditional finite-schedule interval. Add schedule-level score tables and leave-one-validation-schedule-out sensitivity; do not imply three schedules reliably estimate an unrestricted schedule population.

A generalization interval across schedules should resample schedules and then subjects within schedule, refitting training models when targeting algorithm rather than fixed-model uncertainty. This hierarchy is nested here if each participant receives one schedule. Do not apply a crossed bootstrap by default. With very few schedule clusters report instability directly; a small-sample t interval over schedule means may be conservative but is not a cure for weak replication.

Assignment is not random. Label permutation is not a causal randomization test; any permutation control must state its exchangeability assumption and hold schedule/protocol strata fixed. Principled sensitivities exclude the three assignment exceptions, add participant-ID/order/era covariates and interactions selected from protocol evidence, reweight conditions to common schedule coverage, and examine zero contrast separately. A result driven by exceptions or a single sequence is weak.

Report remaining high-contrast accuracy, lapse proxies, reaction time and omission differences without selecting matched-accuracy subgroups. Cursor endpoints are algebraically linked to choices and are useful only as extraction/motor checks. An independently coded re-extraction of trial indices, switch windows and the paired log score is valuable; another model's agreement is not independent empirical validation.

## Audit gates before opening validation

- Immutable manifest records raw checksums, prefix exposure, exclusions, split seed and participant/schedule lists.
- Model feature builders cannot read hidden probability except in the evaluator; truncating all data after `t` leaves prediction at `t` unchanged.
- Changing current/future choices, feedback or hidden sides leaves current prediction unchanged.
- Early calibration and later prediction use group parameters trained only on development participants/schedules.
- Model nuisance features and random-effect treatment are identical; history condition terms are the only intended difference.
- Recovery uses the actual evaluation process and supports the intended margin or explicitly establishes its inadequacy.
- Protocol, code, seeds, hyperparameters and reporting thresholds are hashed before the reserved outcome file is opened.
- Every subsequent change is a dated amendment that distinguishes bug correction from outcome-driven new analysis.

## Audit status

Initial methodological audit complete. Awaiting inputs-only schedule overview and the parent's chosen protocol/code for an independent implementation and leakage review. No validation outcomes inspected.
