# Next research decision: can target events change the persistence of earlier error effects?

2026-10-28. Selected after the completed human-learning-routes campaign. This is a research choice and an input-only feasibility review, not an executed outcome analysis or a newly launched campaign.

Dispatch update: the user subsequently authorized execution, now active in Astra xhigh thread `01a1847c-b6fa-7c53-8e96-d0d241ca4f47`. See [the exact launching handoff](TARGET_EVENT_CARRYOVER_HANDOFF.md). The review and its validation-exposure record below remain historical.

Completion update: that campaign has finished. The±0.2° contrast remains unresolved; see [the completed report](campaigns/target_event_carryover_2026-10-28/REPORT.md). The current [next-research decision](NEXT_RESEARCH_DECISION_AFTER_CARRYOVER.md) supersedes this historical proposal.

## Decision and concrete goal

Move to randomized motor perturbations. Determine whether a task-irrelevant target event changes how **previous cursor errors influence subsequent reaches**, even on a trial with **no new programmed cursor displacement**, and whether the resulting rule predicts reserved participants and a second laboratory's observations.

The primary contrast is a zero-clamp trial with a target jump versus a zero-clamp trial with a stationary target, conditioned on the preceding signed clamp history. Estimate the response to an earlier clamp over the following one to five reaches. Test whether target events change that response beyond a model in which they only change learning from the current programmed error. Include subsequent common-condition readouts to distinguish a transient movement/readout effect from a longer-lived behavioral change.

This is a tractable part of a consequential question: does apparent success or a changed goal only affect incoming learning, or also control the use and persistence of earlier learning? The intended result is a transferable, quantitative behavioral law. Storage, synaptic retention, reward and attention are possible explanations; none should be declared identified from endpoint angles alone.

## Why move on from the completed human study

The [completed report](campaigns/human_learning_routes_2026-10-28/REPORT.md) establishes that shared target-history prediction transfers to reserved people and schedules. Added condition-history terms provide no demonstrated gain, but the original five-point equivalence claim fails both empirical uncertainty and recovery. Validation is consumed.

A joint sensory/lapse/history model could improve the estimator. It cannot repair nonrandom teaching, separate the bundled intervention, or identify reward history separately from revealed target history. Oracle sensory skill removed one simulated bias while regularization-related attenuation remained. The larger-sample/calibration challenge therefore rejects a tested procedure/design combination, not all possible estimators or a universal information limit. Do not convert it into a claim that more data can never help.

The stronger next empirical opportunity is a within-person manipulation with deliberately varied current and previous inputs. Keep the human and atlas studies completed.

## Verified material and what remains unexamined

Primary source: Tsay et al. (2022), [Interactions between sensory prediction error and task error during implicit motor learning](https://doi.org/10.1371/journal.pcbi.1010005). The public Experiment 2 tables `TE_SPE_data_5Feb2022.csv` and `ControlJump_data_5Feb2022.csv` each contain 20 participant sequences with 100 baseline and 724 main trials. The main sequences include zero clamp with stationary targets or signed target jumps: ±4° in one set and ±8° in the other.

An input-only preflight found 4,550 and 4,521 eligible zero-clamp events, keeping five earlier and five later trials inside a randomized block. Approximately 66–67% immediately follow a nonzero clamp. A deliberately limited matrix containing earlier signed clamps, signed target jump and target-event interactions has rank 13/13 in both sets, with standardized condition numbers 4.80 and 4.70. This verifies variation, **not statistical power or scientific identification**.

All 160 participant-blocks have the same verified structure: 180 trials containing each of nine clamp/jump combinations 20 times, followed by one deterministic zero-clamp/no-jump trial. Each person has a distinct ordered sequence. The paper's description of 24-trial balancing does not match the exported order. Preserve this discrepancy and the actual inputs; do not invent 24-trial randomization permutations. The preflight excludes deterministic terminal trials and history/readout windows crossing the 180-trial boundaries. At each horizon 1–5, each set has approximately 480–520 stationary-target index events and 980–1,060 target-jump index events followed by a stationary-target readout.

An independent source is Al-Fawakhiri et al. (2023), [Exploring the role of task success in implicit motor adaptation](https://doi.org/10.1152/jn.00061.2023), with [public data/code](https://github.com/kimoli/TaskSuccessImplicitAdapt). Its Experiment 3 has 18 sequences of 800 randomized interventions; Experiment 4 has 42 sequences of 864 interventions. They include target-event manipulations, but do not simply duplicate the primary zero-clamp test. Verify shared conditions before specifying the transport endpoint; absent conditions cannot be fabricated into replication.

Acquired files and their exact provenance are in the [source manifest](sources/learning_intervention_feasibility_2026-10-28/source_manifest.json) and [input-only audit](sources/learning_intervention_feasibility_2026-10-28/input_schedule_audit.json). All five CSVs match their pinned Git blobs. No hand-angle effects were calculated in this selection review. Source manuscripts' published aggregate results have been read; raw outcome validation remains available subject to a documented split. Reproduce the input audit with `.venv/bin/python sources/learning_intervention_feasibility_2026-10-28/input_schedule_audit.py`.

## Closest prior work: the contribution must exceed a familiar model comparison

[Kim, Parvin and Ivry (2019)](https://elifesciences.org/articles/39882) already compared learning and retention accounts, including outcome-dependent gains and separate error-driven processes. Their blocked-transfer fits primarily implicated updating, with uncertain retention differences and correlated parameters. This is not the first retention hypothesis.

Tsay (2022) already tested target motion, flicker, task error and distraction, including six quantitative accounts. Al-Fawakhiri (2023) already compared the efficacy of target-size and target-jump manipulations. Neither reproducing their mean next-trial effects nor renaming a distraction effect would advance the question.

The candidate contribution is a **frozen test of propagation of earlier randomized inputs**, exploiting zero-clamp events and later common-condition observations, followed by independent prediction. The bounded source review has not established exhaustive novelty. Check related work and actual analysis code before making a novelty claim.

## Execute a discriminating study

1. **Reconstruct interventions and measurement.** Pin original files and code; establish participant mapping, trial order, exclusions, target jump versus flicker, clamp sign, balancing, and the moment used for the hand-angle readout. Preserve full sequences and mark missing outcomes rather than joining across excluded trials. Match source summaries on development data as an extraction check.
2. **Reserve people and external data before outcome exploration.** Choose the split using input sequences and metadata. Reserve participants from both primary sets or an entire set if recovery supports that stronger extrapolation. Keep the second laboratory's main outcomes untouched until a transport rule and eligible conditions are fixed. Source outcome summaries already read are background, not blind discoveries.
3. **Define an observable estimand.** The primary response is the change in the contribution of an earlier signed clamp to reaches one to five trials after the zero-clamp event. Predeclare the scalar summary, lag window and a practically meaningful angular margin, reporting the whole signed response curve as well. Do not choose a favorable lag, history length or target direction on validation. Report effects in degrees and relative to the ordinary earlier-clamp response.
4. **Make the comparison fair.** Both accounts receive flexible current clamp/jump effects, direct within-movement effects, practice/drift, participant variation and the same signed input history. The restricted account allows target events to modulate current-error updating. The alternative additionally changes propagation of preceding inputs. Start with a stimulus-anchored distributed-lag analysis; use a state-space interpretation only if it adds distinguishable predictions. A two-timescale fixed-retention account is a serious baseline, not an optional straw man.
5. **Separate the important alternatives before interpreting validation.** Simulate the actual sequences with current-gain-only effects, state-dependent perceived error, retention changes, temporary expression changes, direct online correction, correlated motor/observation noise and slow drift. Include matched immediate responses with different later responses. Test recovery in both directions and quantify false positives, coverage and detection on reserved people. Use known generating likelihoods where useful to distinguish an uninformative design from an inadequate estimator. A full-rank matrix is insufficient.
6. **Use the later readouts.** Examine whether the change survives or rebounds on subsequent stationary-target/common-condition reaches. Do not infer erasure from an immediately affected endpoint. Include current and intervening randomized inputs in the observation model, and retain the actual block/balancing constraints in null controls. Avoid treating overlapping reach differences as independent learning observations or using noisy previous reach angle as an error-free latent state.
7. **Predict independently.** After freezing, evaluate the signed curve and primary contrast on reserved participants. Transport the substantive gain-versus-propagation distinction to the eligible independent-laboratory conditions, without fitting that distinction again to the external outcomes. Predefine any permitted baseline/noise calibration. An external dataset with a different manipulation is a transfer test, not an exact replication.
8. **Challenge and reproduce.** Independently reconstruct a decisive statistic from original bytes. Audit leakage, readout timing, sequence dependence and alternative explanations. Save a report, numerical tables, scientific figures, input manifests and an offline reproduction runner in a dedicated campaign directory.

## Boundaries and completion

“Zero clamp” means no imposed cursor offset relative to the original target. It does **not** prove zero internal sensory prediction error: proprioception, the existing motor state and changing target interpretation may create an error signal. A state-dependent perceived-error account could mimic retention changes and must be tested or retained as a limit.

Target motion also changes visual information and task error. A target-event effect is not uniquely reward or success. Endpoint measurements may include online corrections. Persistent behavioral effects alone do not locate a memory or establish neural storage.

A successful positive study would show a reproducible change in earlier-error propagation that a current-error-gain account cannot explain, and correctly predict a withheld behavioral consequence. A successful negative would place a calibrated useful bound after recovery passes. If plausible expression/perceived-error accounts remain indistinguishable, report the observational result and the exact unresolved contrast; do not promote a fitted retention coefficient into a biological fact. If recovery cannot distinguish meaningful effects, narrow or stop this campaign rather than searching many unrelated kernels until one wins.

## Alternatives considered in this review

- **Joint IBL measurement model:** secondary methodological work, not the selected empirical campaign. An adversarial oracle-discrimination/probe-design study would be more informative than another refit of consumed validation.
- **Rapid temporal retiming:** scientifically attractive, but the inspected Wang et al. (2024) release omits corrected movement-onset files and the independently assigned timing variable; participant/trial mapping also differs from the paper. Park it. [Specific source audit](sources/motor_adaptation_feasibility_2026-10-28/AUDIT.md).
- **COIN versus simple motor models:** original work already included dual-/three-rate comparisons and model recovery. No distinct verified test was selected here.
- **Song baseline forecasting and HYPOMAP mixed states:** remain parked/completed for the previously documented reasons.

This recommendation is ambitious about the question and bounded about what the available intervention can establish. No successor thread, paid job, external contact, publication or recurring automation was created during this review.
