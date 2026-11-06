# Source-fixed category generalization: failed utility

The frozen local-context exemplar prescription failed the blocked-to-interleaved forecast. On 21 different people and 504 new-item responses, its choice loss was 4.52% worse than a matched exposure/spacing exemplar and 3.42% worse than an empirical generalization map. It predicted 42.47% accuracy against 54.56% observed. All 21 single-person deletions retain both point penalties. This is a failure of this finite source-fixed prescription. It does not establish absent human learning or absent biological contextual encoding.

## Design and observations

Public Carvalho–Goldstone 2014 Experiment 1 high-similarity records contain 43 complete people and one partial record. We fitted only 22 people whose FIRST curriculum was blocked, then forecast 21 different people whose FIRST curriculum was interleaved. Each contributed 288 actual labeled training opportunities and 24 intended-new test responses. No training-accuracy exclusion was applied; the original paper excluded 15 of 44 high-similarity people using training performance. ID 41 was excluded solely for its incomplete 308-row input record. The paper counterbalanced order; the released alternating IDs do not independently certify random assignment. Using first curricula avoids prior-curriculum carryover. This comparison conditions on recorded opportunities and does not estimate a causal instructional effect.

P stores each exposure with a feature encoding determined by its immediately preceding feature/category relation. B has the same frequency/spacing/forgetting/decision/lapse terms with all context encodings fixed to1. E is a source-standardized empirical softmax using similarity, feature likelihood, frequency, recency and spacing; leave-one-source-person-out selection chose ridge1. All models receive identical actual training exposures/feedback labels and test-item geometry. Evaluation training choices and all test choices are excluded from fitting inputs. The supplied96-item workbook maps actual names to eight nominal segment features; arbitrary feature IDs are compared for equality, never subtracted as perceptual distances. P is derivative of SAT-M's idea, not a reproduction of its2022published fit.

Actual original arithmetic ran at09:12:04.826755UTC, before the20-minute deadline: participant20's two288-exposure histories link to19/24and6/24new correct responses. This establishes executable linkage, not a group effect. Preparation then failed because source IDs8/30each saw23of24nominal training-pool items. Their old-pool f01/b04probes were actually unseen. ONEexplicit pre-evaluation amendment selected intended-new item numbers09–16for EVERY person, each verified absent from actual training. The two extra unseen source probes remain auxiliary. All actual unequal frequencies were retained. Freeze was09:22:29.184248UTC; design/disagreement gate passed before30minutes. Probabilities and conditional controls were saved before real scoring at09:24:20.155929UTC.

## Frozen test

Utility required at least 5% negative log likelihood (NLL) reduction relative to BOTH B/E, positive lower 95% paired-person-bootstrap gain endpoints (2,000 draws, seed 20261101), and absolute pooled accuracy bias at most .10.

| Model | Source NLL | Evaluation NLL | Brier score | Predicted correct probability |
|---|---:|---:|---:|---:|
| Local-context P |1.012443|1.055839|.641518|.424742|
| Exposure/spacing B |1.040714|1.010227|.603629|.498665|
| Empirical E |1.050587|1.020935|.611304|.446263|

Observed evaluation accuracy is 275/504 = .545635. P gains −4.515% [−12.108%, +2.673%] against B and −3.419% [−9.574%, +2.736%] against E; its bias is −.120893. Both relative/interval conditions and calibration fail. Intervals condition on fitted 22-person sources and actual exposure schedules; they do not provide source/population uncertainty or establish equivalence.

Before real scoring, mean absolute probability disagreements were .0973 versus B and .0879 versus E. If P generates answers, its conditional expected gains are 6.41% and 5.47%. The FULL decision passes 61/100 conditional P controls and 0/100 E null controls (seed 20261102). This shows moderate finite sensitivity. Full-source recovery, power at the 5% boundary, population heterogeneity calibration and interval coverage remain untested.

## Verification and contrary

verify.py imports no analysis code and implements scalar arithmetic from the original DAT/workbook bytes within this author context. It matches all 9,288 source/evaluation probability scalars within 7.217e−16, source objectives, E standardization/stationary gradient, evaluation gain intervals and all 200 control decisions. Eight freeze pins and the prediction pin verify. This is within-author reconstruction; a distinct independent scientific review remains UNRUN.

The highest-value postvalidation contrary scores ALLthreepre-existing P source solutions without refitting or replacing the original. Their source/held-out NLLpairs are1.012443/1.055839(selected),1.013602/1.043202and1.039177/1.008567. The worst source solution gives a small favorable held-out point change (about.16%versusB) and better calibration, but allthreefail the full rule. Source-selection/local-solution sensitivity is material. Global optimum certification and source-person resampling remain UNRUN. No evaluation-based repair occurred; the single development revision was already consumed before freeze.

## Prior work and limits

The [2014 paper](https://pc.cogs.indiana.edu/papers/blockedinterleaved.pdf) already reports descriptive curriculum/category-structure effects. The [2022 SAT-M paper](https://onlinelibrary.wiley.com/doi/full/10.1111/cogs.13128) fits local encodings jointly across curricula. This source-only held-person/held-curriculum forecast differs from those fits, but novelty is unestablished and it does not refute the published model. The [public deposit](https://osf.io/s87tf/) and SOURCES.md document provenance.

All44new DAT members were acquired/hashed/decoded before evaluation; numerical interpretation occurred in stages. ID20's entire672rows are consumed development. The528source/504evaluation new responses and43first-training feedback histories are consumed. Old-probe responses/second curricula/partial41remain acquired-decoded auxiliary exposure, except20's second curriculum already interpreted. Both workbook geometry sheets and the canonical three-category CSV were decoded; low-similarity participant files were not acquired. Published summaries preceded freezing. Hash ordering is not independent proof of historical nonaccess.

Unequal observed frequencies differ from nominal equal repetitions; conditioning on actual recorded exposures avoids imposing nonexistent balance. Two nominal-old-but-unseen source probes, partial41and the supplied2024workbook mapping are provenance facts, not a uniquely identified recording-error cause. Pixels, acquisition software, calibrated psychological distances and independent assignment were not reconstructed. OSF node_license=null; external-file redistribution licensing remains uncertified. No biological equality, universal forecast impossibility or absent representation follows.

Recommendation: bank this frozen failed conditional forecast and close further recipe tuning on the consumed high-similarity release. A distinct fresh independent review is earned; its highest-value contrary is source-estimation/selection stability or original-input reconstruction, retaining postvalidation status and the primary failure. A subsequent investment needs separately justified defining evidence or a different consequential question, not automatic archive repair.

## Records and resources

PROTOCOL.md/AMENDMENT_1.md/FREEZE.json define the test; FIRST_DATA_CHECK.json/NOVELTY_AUDIT.json/PREPARE.json/GATE.json preserve source gates. predictions.npz/PREDICTION_PINS.json precede SCORES.json. CONTROLS.json, VERIFICATION.json and CONTRARY.json preserve checks. README.md gives commands; MANIFEST.json pins27core artifacts and all downloaded inputs. PROPOSED_LEARNING.md awaits PI integration.

Conservative charges: 24 attempted public operations of 32; ONE empirical/TWO primary families; 20MB ingress of 25MB (389,684 native bytes observed; browser/redirect/provider traffic unknown); 200MB additional read of 300MB. Largest measured process RSS was 84,885,504 bytes against 800MB; failed-pass/toolhost peaks and physical I/O remain unknown. One process/thread and zero jobs remain. No dependencies, extensions, contact, publication, spending or old/protected empirical payloads were introduced. Root shared records and the heartbeat were not edited. The SAME ACTIVE PI heartbeat continues across this endpoint under the human reserve rule.
