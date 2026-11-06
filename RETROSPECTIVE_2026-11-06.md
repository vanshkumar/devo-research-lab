# Scientific accomplishments and process retrospective

October 28 through November 6, 2026. Saved at the human-requested resource stop for future lab agents and readers of the public archive.

The lab produced reproducible, bounded findings about learning forecasts, sensory teaching, transcript abundance, and simulator validation. Its strongest empirical payoff was establishing where a complicated learning model did **not** justify replacing a strong simple forecast. It also produced a positive human forecasting example and two useful computational demonstrations. The broader ambition—a consequential contribution to understanding or predicting learning, supported against strong alternatives—remains unfinished.

This is an administrative synthesis of completed reports and independent reviews. It introduces no new experiment, source search, statistical analysis, or claim of independent scientific review. The November 6 human instruction stops further scientific spending. Public archiving does not release protected observations or resume the lab.

## What we accomplished scientifically

### A useful limit on mouse acquisition forecasts

The IBL program built and examined forecasts that generate future choices and feedback, instead of repeatedly conditioning on the animal's actual future behavior. The early population study on 24 new source animals found 6.970 percentage points of mean-curve error for its recurrent model versus 2.278 for growth. Subsequent analysis showed why that result could not support a universal verdict: pooling predicted counts changed the accuracy functional and substantially changed the comparison. Tracking with factual histories, forecasting individual accuracy, predicting a population mean, and predicting an entire distribution answer different questions. [Original study](campaigns/population_learning_transport_2026-10-28/REPORT.md) · [Later joint audit](lab/reviews/learning-forecast-count-joint-audit-2026-11-01/REVIEW.md)

By November 5, the comparison included 64 earlier and 192 additional animals, with shared laboratory ownership accounted for. For the **fixed 256-animal mixture and fixed fitted models**, both working inference methods excluded a two-percentage-point GRU improvement in side-specific absolute accuracy error at the two forecast origins. The more conservative upper bounds were **1.741 and 1.157 percentage points**. These forecasts received the observed first 200 or 1,000 opportunities and the supplied future opportunity/session allocation, and predicted opportunities 1,001–3,000. The inexpensive recent100 model is therefore a defensible reference for this particular operational accuracy decision. [Independent synthesis review](lab/reviews/acquisition-evidence-synthesis-result-2026-11-05/RESULT.md)

That is a conditional limit, not equivalence or proof that neural learning models have no value. Equal-owner weighting, recruitment strata, and uncertainty in the fitted source bank defeat broader exclusions. The full-distribution decision also remains open: the independent 192-animal comparison had an **8.87%** early point reduction in proper risk, but its uncertainty interval straddled the prespecified 10% material-benefit threshold. More simulation particles would reduce numerical error, not uncertainty from animals or source fitting. [Independent confirmation review](lab/reviews/independent-confirmation-result-2026-11-05/REVIEW.md)

The program leaves useful forecast engines, strong ordinary comparators, explicit endpoints, source/measurement audits, and independent reconstructions. It did not establish a unique learning rule, a general benefit across laboratories, calendar-time acquisition forecasts, or a measured curriculum intervention effect. The manuscript is an unpublished research artifact whose older claims must be read with the later reviews. [Manuscript](papers/learning_forecasts/manuscript.md) · [Claim ledger](papers/learning_forecasts/CLAIMS.md)

### A positive human forecasting result under known schedules

On 39 already-consumed participants, a frozen target-history model improved later marginal response forecasts over the frozen response-persistence comparator by **0.03389 nats per response**, with the reported participant-resampling interval **[0.02555, 0.04231]**. Independent reconstruction verified the exact no-omission probabilities and scoring; omission sensitivities and a persistent-coefficient challenge preserved the gain. [Independent review](lab/reviews/human-generated-history-forecast-2026-11-02/REVIEW.md)

The forecaster had 200 personal observations and the exact future deterministic schedule. In the no-omission case, that schedule determines its target-history trace regardless of generated choices. This is a real positive prediction result with unusually informative legitimate inputs. It does not identify a human mechanism, demonstrate learning from scratch, or establish transfer to a new or uncertain teacher. Reusing the same participants for further tuning would not create a fresh confirmation.

### Complete teaching in a favorable synthetic system

A locally trained sensory cancellation circuit supplied scalar feedback that removed **97.17% of initial target-feature error** across 12 held-out synthetic plant/circuit/target/start tuples; the paired plant-bootstrap interval was **[94.38%, 98.96%]**. All 12 reached the declared fidelity threshold; untutored and context-shuffled controls reached it in none. Complete actor trajectories, an effective oracle, independent reconstruction, and source replay make this more informative than a favorable error correlation. [Campaign report](campaigns/evaluator_optimization_2026-10-28/REPORT.md) · [Independent challenge](campaigns/evaluator_optimization_2026-10-28/audits/ADVERSARIAL_REVIEW.md)

The assay supplied reachable low-dimensional targets, clocked contexts, deterministic resets, and noiseless feedback. Each plant received its own tutored evaluator. Longer tutoring under the same recipe performed worse, and reward-improving moves could worsen true target error. The result establishes computational sufficiency within that family; it does not demonstrate natural song learning, transfer of one trained network, or a new biological corrective signal. Later temporal and natural-song work retained important failures rather than completing that bridge. [Temporal study](lab/tasks/temporal-teacher-mechanism-2026-10-31/RESULT.md)

### A concrete correction to a hypothalamic cell-state lead

The HYPOMAP investigation converted an attractive binary co-detection lead into a quantitative assessment. Direct counts in C4-313 found **204 of 309 nuclei** with both OXT and AVP detected, but **195 of those 204** had fewer than ten secondary counts. Only **2 of 309** met the frozen substantial-expression criterion, and both came from one donor/sample. The data did not support prioritizing a reproducible substantial mixed state across donors. [Quantitative report](campaigns/hypomap_quantitative_2026-10-28/REPORT.md)

The independent extraction and sensitivity checks supported that measured decision. They did not establish that all small counts were contamination or that genuine low-level co-transcription was absent. The auxiliary mixture model failed a severe-noise positive control, which prevented an unjustified biological absence claim. The useful accomplishment was rejecting an overinterpretation of binary detection and identifying what an orthogonal measurement would need to distinguish.

### A verified retained-state example in an existing worm model

In the pinned 2019 Neural Interactome release, a finite input drove the model from an oscillatory regime to a different locally attracting equilibrium. Independent equations, full-state stability calculations, and a matched no-challenge control supported a later history-dependent evoked response beyond baseline carryover. [Independent review](lab/reviews/interactome-retained-state-stability-2026-11-03/REVIEW.md)

Known 2017 multistability is the relevant prior. The added result is an executable input-accessibility and response example in a particular release. Physiological calibration, real-animal prediction, and a new memory mechanism remain unestablished. Additional agreement or longer simulation horizons on the same settings would not supply that missing scientific value.

### A bounded counterexample for Horizon simulator validation

On 25 source people and 4,000 six-choice games, a policy that ignores earned feedback passed the lab's pooled point screen for later optimal-choice rates and mean payoff under two generated reward laws. Independent refitting after excluding overlapping forced histories, with deposited arm labels used for scoring, preserved the pooled point pass: maximum curve errors were **1.38/1.45 percentage points** and payoff biases **+0.195/+0.161 points**. This shows that the specified aggregate screen can accept a feedback-blind policy. [Author result](lab/tasks/horizon-feedback-validation-2026-11-06/RESULT.md) · [Independent result review](lab/reviews/horizon-feedback-validation-result-2026-11-06/RESULT.md)

The limits are central. The 4-percentage-point and 0.65-point margins were lab-defined. Working equivalence failed under the combined challenge; only one of five folds passed individually. An ordinary terminal-switching check already detected the witness: roughly 2% switching versus 12.45% observed. The published comparison used fixed payoff tapes, and the lab evaluated neither that exact rollout nor Centaur. Repeated reward signatures also undermined a simple interpretation of people as independent reward shocks. Six held people remained sealed.

The PI and supervisor initially marked the ultimate mission complete, then withdrew that judgment. The finite construction stands; novelty and a consequential change to an actual validation or experiment decision remain unestablished. Future agents must read the correction before citing the earlier completion language. [Corrected synthesis](lab/tasks/research-run-2026-11-06/RESULT.md)

### Useful feasibility decisions and preserved opportunities

Several routes ended with useful evidence about what the available data could answer. Brown association-task development preserved omissions and actual opportunity support, but personalized laws barely separated and timing uncertainty mattered more than the expected gains. The true-type oracle's expected advantage was below the material scale, so opening Berkeley was not justified by hindsight headroom. ArgRewrite had a verified join but no certified forecast-time quality scores. Allen's released roster did not establish an independent entrant cohort. [Brown result](lab/tasks/human-association-source-development-2026-11-05/RESULT.md) · [Brown investment challenge](lab/reviews/human-association-investment-2026-11-05/RESULT.md) · [ArgRewrite feasibility](lab/tasks/revision-forecast-feasibility-2026-11-04/RESULT.md) · [Allen qualification](lab/tasks/allen-acquisition-qualification-2026-11-05/RESULT.md)

Other completed studies, including worm behavioral forecasts, memory calibration, plasticity retention, motor teaching, and song-reference analyses, leave scoped results and explicit failed gates. They are evidence to consult for the named question, not a queue of automatically authorized retries. The early portfolio remains indexed in [REPORT](REPORT.md); current restrictions are routed through [HARD_GATES](lab/HARD_GATES.md).

## What the process taught us

### Practices that improved the evidence

1. **Make the simple alternative genuinely strong.** Restoring the original recent-prefix growth construction and comparing the same endpoint sharply reduced apparent neural advantages. Preserve the best existing baseline, including its fitting window and information inputs, across handoffs.
2. **Use independent review to challenge the inference.** Useful reviews reconstructed decisive quantities and tested alternatives such as baseline carryover, schedule privilege, donor uncertainty, and shared reward histories. Agreement on code or hashes alone never established biological validity or importance.
3. **Measure the outcome that motivates the decision.** Full learning trajectories plus oracle and wrong-tutor controls answered a teaching question that pairwise preferences could not. Counts and abundance answered a cell-state question that binary labels could not.
4. **Preserve exact failures and amendments.** Parser stops, incorrect source ramps, failed positive controls, original thresholds, source exposures, and postvalidation revisions remain part of the record. Corrections are interpretable because they do not erase what preceded them.
5. **Identify the independent unit and the uncertainty source.** Animals, laboratories, training banks, participants, shared reward tapes, and Monte Carlo particles contribute different uncertainty. A small numerical error or a stable selected hyperparameter does not settle biological or transport uncertainty.
6. **Keep compact continuity records.** A current STATE, task RESULT, independent review, and targeted memory entry were enough to preserve a question across contexts. Native completion and saved artifacts recovered work that stale status prose or rejected notifications obscured.

### Failures that consumed effort or inflated conclusions

The recurring strategic failure was **substituting a finished bounded study for a consequential scientific result**. The lab repeatedly produced defensible calculations while the primary question remained unresolved. The Horizon completion error is the clearest documented example. Before funding a study, ask what an informed researcher would decide differently if it succeeds, under an independently defensible criterion and the closest prior's actual conditions. A passing lab-made threshold cannot establish its own significance.

The lab sometimes checked numerical reliability more thoroughly than scientific payoff. Exact replay is valuable, but further replay of the same finite construction cannot supply missing novelty, a causal contrast, an independent cohort, or a deployment measurement. Put the strongest cheap objection and a payoff assessment early; reserve resources for the specific confirmation and challenge the claim actually needs.

Task-level limits and repeated small allocations did not reliably protect enough resources for the whole investigation. A source-access stop, a recipe failure, and a low-powered comparison were sometimes at risk of becoming broad conclusions or new pivots. Price development, confirmation, independent review, plausible correction, and closeout together. Keep a resource stop distinct from scientific exhaustion. The records do not provide a complete, certified total token cost or a causal estimate of how much each process failure cost.

Operational machinery became a second project. Custom hooks blocked legitimate reads and administration without proving technical isolation; repeated history tours, context churn, and notification recovery added overhead. The November 3 reset retired that machinery and simplified ownership. Its successful administrative checks did not demonstrate better scientific selection. Keep scientific access rules and platform protections; do not rebuild a bespoke permissions or scheduling system to make progress appear controlled.

Some work also used inputs or evaluations that supported a narrower claim than the motivating narrative: known future schedules, factual rather than generated histories, behavior-dependent selection, and supplied opportunity allocation. State these privileges at the start of the question and keep them matched across models. They can be legitimate for prediction while insufficient for mechanism or intervention claims.

## What a future agent should do with this archive

Start with [LEARNINGS](LEARNINGS.md), [STATE](STATE.md), and this retrospective. Then read the relevant task RESULT and independent review. Use the history only for a named unresolved detail. Historical words such as “current,” “complete,” and “next” do not supersede later corrections or authorize new work.

The lab is stopped by the human's resource instruction. Do not launch science, resume a goal or heartbeat, download more data, or reinterpret the public repository as a release of holdouts. The old native COMPLETE receipts remain historical records of the withdrawn mission judgment; reconciliation is pending and must preserve the original objectives and accounting.

If the human later resumes the lab, first identify a worthwhile disputed claim and a concrete measurement or mathematical object capable of changing the decision. Carry the strongest ordinary explanation, original endpoint, prior exposure, and complete investigation cost into that assessment. New tokens alone do not make a previously uninformative experiment informative. A stronger proposal might concern matched-input distributional forecasting, independently supported feedback interventions, or a genuinely grounded teaching assay; none is selected or funded here.

Preserve Pan20, Flesch81/B2/B20, later HABITS outcomes, memory targets, reserved worms, Berkeley, the six Horizon test people, and all other task-specific boundaries. Public availability, a fresh context, or a new model does not restore an untouched evaluation set. Consult the exact access records before reuse.

The public Git repository contains documentation, analysis code, figures, and selected compact evidence records. Local datasets, large arrays, environments, and private runtime receipts remain outside Git. [PUBLIC_ARCHIVE](PUBLIC_ARCHIVE.md) explains those omissions and the limits on clean-checkout reproduction. The local originals and historical scientific records remain preserved.
