# Flesch source calibration result — 2026-10-29

**Bounded execution completed at the source stop. Do not release B2/B20 responses.** Actual shared-prescription fits and autonomous source forecasts were implemented. The cross-curriculum question remains unresolved.

All95source people reconcile with the eligibility rule and original task records. A71fit/24whole-person development-check split was frozen before source response extraction. Two declared optimizer starts/model used600SGD+Oja,462value and477growth objective calls. Value/growth converged; both network starts hit their300-call caps.

| Shared prescription | B200 curve MAE | Interleaved curve MAE | Equal-group energy score |
|---|---:|---:|---:|
| SGD + all-input Oja |21.53pp|13.18pp|.45975|
| Context-separated value |**10.20pp**|2.43pp|.21595|
| Exposure growth |10.24pp|2.71pp|**.21400**|

Value/growth MAE uses independently computed exact conditional means at frozen3-node person integration; network/energy use256eligible draws/person. The source-chosen value learner misses the fixed≤10pp B200 criterion. Its development energy gain over growth is−.00196[−.00565,+.00160]. People begin near chance and acquire the blocked rule quickly; this is an acquisition-rate gap, not demonstrated prior knowledge.

**Separate numerical limit:** continuous-person mixture likelihood is underresolved. At unchanged parameters, value fitNLL is18230.32/18155.08/18134.09 at3/5/9Gauss-Hermite nodes, despite stable mean curves. Therefore these are finite numerical fits, not a converged continuous-family result or a refutation of the model classes. Full-pipeline5pp/100-opportunity recovery, null calibration and the sensitivity envelope remain unfinished; no readiness gate is earned.

Reader27, schedule-mask9, complete-timeout14, numerical16 and final17checks pass. Independent reconstruction verifies the trajectory law, original network updates, source scores and exact means. Original failures and numerical repairs are retained.

**Exposure:** ten inputs for176people;228,000original response values for95source people only. Exactly2,430,000target-response bytes were blindly inflated/discarded across two complete passes; **zero target response values decoded**; no target forecasts or scores. Response histories for all81B2/B20 people, Pan20 and other protected targets remain sealed.

[Detailed findings, limitations and cost](DETAILS.md), [exposure](EXPOSURE.json), [stability](SOURCE_STABILITY.json), [independent exact check](../../reviews/flesch-source-calibration-2026-10-29/exact_source_results.json), [reproduction](REPRODUCE.md), [proposed learning](LEARNING_PROPOSAL.md). PI collection from disk/native return suffices. No continuation or successor is launched.
