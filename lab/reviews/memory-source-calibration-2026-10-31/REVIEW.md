# Independent review: accept the source calculation and park the fixed candidate

The failed source-calibration decision is reproducible. **Accept the numerical source result and preserve the stop; narrow its interpretation to failed certification.** The evidence does not demonstrate gross average miscalibration, absent recorded-practice information, equivalence, or failed cross-policy transport. No target response, prediction or score was used.

Reviewer `01a19352-1977-7192-9401-a1d6bccd4b99` is distinct from author `01a19340-cb3d-71e2-9c8e-24a8ac823f9d`. START was2026-10-31T18:56:42UTC; deadline19:41:42UTC. Scientific execution finished before19:04UTC. This is one bounded independent review, not a new model or repaired gate.

## What was independently reconstructed

[independent_review.py](independent_review.py) never imports the author's estimator. It projects only UID/item/time/install/arm/count/ordinal from the pinned metadata, then separately reconstructs focal histories, counter-gap brackets, intervening recorded-row counts, the fixed support cells and source item bank. All14resulting schedule arrays agree exactly with the author's saved metadata arrays. Primary counts reproduce1,116/485/1,472/1,432reviews and36/10/29/23IDs; see [METADATA_RECONSTRUCTION.json](METADATA_RECONSTRUCTION.json). Candidate membership and earlier stable German/B/global identity eligibility are inherited from the pinned candidate, not recertified by interpreting excluded auxiliary fields. This is not a new population search.

The reviewer reads the pinned random-arm shard with an exact ordinal allowlist, converts only the75fit+15validationIDs'35,373focal binary correct values, and blindly discards other rows/fields. Independently constructed success/failure and person-history features use strictly preceding focal answers; first focal answers initialize histories but are not scored. Delay uses observed time, and other practice counts every recorded intervening row, including ineligible items. Ten actual source-history checks independently count preceding successes/failures and verify that changing current/future answers leaves earlier features unchanged. Features are past-only, but inclusion remains selected with future metadata.

An independent block-Newton optimizer with explicit Hessian contractions reconstructs all54inner fits in the frozen3×3common grid and the final pair. It selects the same **k=16/item precision64**. Maximum joint grid-score difference from the author is1.249e−6. At the more tightly converged optimum, source-repeat probabilities differ by at most1.399e−5; final parameter differences are at most4.569e−5. These small optimization differences do not change the result. They are a numerical verification of the same objective, not an accepted replacement fit; see [PREDICTION_RECONSTRUCTION.json](PREDICTION_RECONSTRUCTION.json).

Using the **actual frozen coefficients** as inputs to the independent feature/scoring/uncertainty code reproduces the author's executed primary loss, bias, Brier and uncertainty summaries within1.11e−16. [FROZEN_AUDIT.json](FROZEN_AUDIT.json) preserves this exact replay separately from independent optimization.

## The frozen source result

There are485primary reviews from10appIDs, with equal weight per ID. IDs are not certified distinct biological people.

| Frozen primary quantity | Item-local baseline | Added recorded practice |
|---|---:|---:|
| Equal-ID log loss | .572986798 | .565283788 |
| Equal-ID Brier loss | .194195339 | .191701990 |
| Mean prediction minus answer | −.027097393 | −.016782418 |
| Nominal95%absolute-bias upper envelope | **.145087857** | **.122139287** |
| Five-bin ECE | .031363397 | .041596488 |

The paired log-loss gain is **.007703010nat/review, nominal95%[−.021150820,.036556839]**. Augmented-minus-baseline Brier upper bound is about.009179, below.02. Both ECE limits pass. Both absolute-bias envelopes fail the frozen.10criterion, so the conjunctive source gate fails. Neither the positive gain nor a different passing component substitutes for that gate.

The gain's evaluation-ID variance is.0001571402, versus coupled source-estimation variance.000005549985. Covariance matters: at the independent optimum, the two source contribution variances sum to.0000364307before coupling, but their signed cross-covariance reduces the paired source term to.00000554988. The code reconstructs both signed cluster influences; treating the fitted models as independently estimated would be wrong. Degrees of freedom are9, not484.

The repeated-review diagnostic uses4,096rows/15IDs and gives about.007721nat gain with an interval spanning zero. It is a consumed-source diagnostic, not a replacement primary population or evidence of transport.

## One contrary diagnostic: precision and ID influence

[DIAGNOSTIC_PLAN.md](DIAGNOSTIC_PLAN.md) was saved before the source calculation. The diagnostic tests whether broad true average miscalibration is needed to explain this failure. It does not alter observations, predictors, the accepted cohort or thresholds.

For the exact frozen calculation, the bias envelopes decompose as

`absolute point bias + nominal cluster-t half-width`.

The half-widths alone are **.117990464/.105356869**, already greater than.10. Thus algebraically centering each point bias at zero while retaining its observed dispersion/source-estimation variance still fails certification. This is a finite precision decomposition, not a generated calibrated data control or evidence that true bias is zero.

[PRECISION_INFLUENCE.json](PRECISION_INFLUENCE.json) then deletes each of the ten evaluation IDs once, holding the independently reconstructed source coefficients fixed and recomputing evaluation weights, gradients and source covariance. **All10deletions fail the joint gate.** The smallest baseline/augmented envelopes are.106845/.101531, obtained after omitting ID2467. Across deletions, point gains range.001962–.018184nat, but every nominal gain lower bound remains negative. The diagnostic uses the independently converged same-objective coefficients, whose small difference from the frozen coefficients is quantified above; it is not a new fitted prescription or repaired primary result.

The primary IDs contribute5–202reviews each but each receives10%weight. Both models have six negative and four positive ID biases. Their estimated ID biases vary widely (roughly−.329to+.162baseline), which includes binary sampling noise and history dependence; those values do not estimate ten noiseless underlying biases. A single universally bad ID is not enough to explain away the gate failure, and no deletion is promoted into a new cohort.

This strengthens the imprecision interpretation while preserving uncertainty about model adequacy. It does not prove that the models are calibrated, that true average bias lies within.10, or that practice is informative/irrelevant.

## Integrity and numerical reliability

All ten initial/fitted freeze references match their current bytes, including protocol, author code, candidate definition/comparison/JSON, saved fit and source schedule/fit-answer pins. Saved chronology is ordered: initial freeze18:46:46.657UTC; source fit18:47:00.974; fit freeze18:47:00.975; validation access18:48:41.064; validation result18:48:41.548. The executed source-reader ordering agrees. This is an audit of pinned files, saved times and code order, not independent OS-level certification of historical access.

The original NumPy warnings and author's audit remain preserved. Independent full sparse Hessians agree with explicit block contractions within1.819e−12; full and Schur solutions agree within1.085e−18; score-gradient finite differences agree within3.628e−13. All values are finite and both Schur complements are positive. These checks support the finite numerical calculation; they do not establish statistical coverage.

The first reviewer pass stopped in an optional repeat-wide diagnostic because its scorer did not yet assign zero effect to an unseen validation item. The primary result and grid had completed. The scorer was corrected to the frozen zero-effect rule and the pass repeated with every original read charge preserved. [REVIEWER_FAILURES.md](REVIEWER_FAILURES.md) also records one denied inline inspection; the scoped-script route completed without changing any guard.

## What remains unearned

Actual-schedule known-answer recovery, null/boundary false-positive calibration,80%sensitivity at a true.02nat effect and the broader initialization-generator sensitivity were not run by the author and are not earned by this review. The cluster-t/sandwich/delta intervals are nominal and conditional on selected hyperparameters, fixed item bank, supplied observation law and fitted model. Ten heterogeneous app IDs, possible item/environment dependence and uncalibrated selection behavior limit their interpretation.

Recorded practice is a lower bound. Undetected items/tails, unknown pre-period experience and response-dependent engagement/retrospective selection remain unresolved. Current field semantics/provenance rely on the existing source audit; this review does not independently certify an uninspected cumulative converter. No causal interference, complete memory state, biological mechanism, autonomous policy benefit or cross-policy portability follows.

The2021Upadhyay etal. study already compares schedulers and HLR/POWER. This is a reproducible conditional source-model/gate audit, with no claim of a new forgetting curve or global scientific priority. See [SOURCES.md](SOURCES.md).

## Accounting and investment judgment

Final review charge is **136,488,919additional bytes**, including a20MBcontext/code/output-QA envelope, full compressed ingress and inflated/decoded bytes, and the failed pass. Inherited7,638,337,193plus this charge gives **7,774,826,112/8,000,000,000bytes**. No new acquisition. Two original random-shard scans plus one consumed-source derived-answer load reinterpret106,119correct values in total; these are the same35,373values, not new participants. All90candidate source IDs and91full-lineage source IDs remain consumed. Target values/predictions/scores, auxiliary/reply values and other protected datasets remain0. Peak observed scientific-process RSS205,668,352bytes, one process/one numerical thread at a time; jobs0.

**Bank the successful masked pipeline and independently verified failed certification; park this fixed candidate without model/cohort/gate repairs or target release.** The broader measured-history/transport question stays unresolved. The next allocation belongs to the PI: use this evidence to compare other consequential directions, rather than consuming sealed targets to resolve a source-precision failure. Completing this bounded review does not pause the lab or its heartbeat.
