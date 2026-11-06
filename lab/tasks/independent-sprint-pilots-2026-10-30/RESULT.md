# Exploratory pilot result: content teaching versus temporal evaluation

Completed inside the finite120-minute block. Numerical work and author checks finished2026-10-31T02:08:47Z; jobs0. All six worm recordings and all three original synthetic tuples were previously consumed. No independent biological validation or global novelty is claimed.

## Chosen question and strongest observed result

Does removing the supplied premotor timing basis prevent a locally learned cancellation circuit from supplying useful teaching, or does it expose a narrower temporal-evaluation limitation? The first matched searches already distinguish these: zero-HVC tutoring/testing succeeds in two of three restricted shape/order tasks and fails in one. A successful restricted search therefore cannot establish that the teacher learned a reliable sequence objective.

Every main actor uses four shared shape coordinates, one of six order actions, known unit gain, a common whole-cycle mean-rate reward and1206scalar feedback slots. All three matched true-feature-error oracles remove>99.5%initial error. Source Gold scores are evaluated offline after circuit-actor search.

| Plant | True-error oracle | Supplied clock | Fixed clock, shifted onset | Reset retained clock | Zero HVC |
|---|---:|---:|---:|---:|---:|
|100|99.5549%|99.7834%|98.1350%|99.7834%|99.5449%|
|101|99.9959%|99.9093%|99.9879%|99.8773%|−3.1940%|
|102|99.6043%|98.6875%|99.3847%|98.6875%|99.4125%|

Entries are initial canonical feature-sequence error removed, not accuracy percentage points. Negative means error increased. The no-clock failure chooses order4; both successes choose order0. This does not establish clock necessity: recurrent dynamics, fixed sensory slots and episode/reset structure remain. Removing premotor input also changes mean drive; the tonic control challenges that confound. Onset reset retains a known relative clock template and is not learned general correspondence.

## First saved falsification: plant100

At exact tutor content, the forward no-clock teacher ranks the target first among the six original choices, with a0.000347Hz margin. Expanding to64 fixed choices ranks the target fifth and selects a wrong order with featureMSE6.6540 and lower circuit cost by0.000973Hz. The retained-clock critic ranks the target first and selects exact order. This is a finite policy-selection counterexample at a privileged fixed content fixture, not a completed64-order joint motor-learning experiment.

Retraining the no-clock circuit on the reversed tutor does not make that reversed sequence preferred: target rank5/6and36/64at exact content. This fails the proposed specific-order preference test in this case; it does not prove absence of every temporal code in the network.

After learned content is fixed, the no-clock duration actor moves0.8→0.7and waveformMSE2.4058→2.6289. The matched waveform-error oracle reaches1.0andMSE0.01641. The retained-clock actor reaches1.01875andMSE0.31047, a useful but biased temporal correction. The tonic actor also reaches0.7. The completed quiet-tail check below addresses the finite-window alternative.

Under the separately seeded source's current-noise assay, the forward no-clock critic selects correct order in9/20and5/20sets at strengths0.1/0.5; the retained-clock critic does so20/20at both. This is a frozen-circuit order-choice assay with conditional quiet reset, not full noisy motor acquisition or calibrated bird noise. The independent frozen Euler port matches source zero-noise mean rates within2.45e−15in this case. Hypothetical scalar readout-noise results are retained separately.

## Worm pilot and allocation

The original first-worm current-only anchored advantage reproduces exactly at the declared tolerance. Giving each neuron five own-history lags changes the3-second comparison: local MSE0.84946versus population-current0.86814. The old roughly7%gain over local-current is therefore not a demonstrated gain over local memory.

Selecting local and population families only on their middle validation windows gives population gains of−7.01%,−7.45%,−0.13%,+15.47%,−4.94%,+4.59%across the six consumed animals; median−2.54%. The shifted-channel control median is−4.31%. In the apparent+15.47%case, persistence also beats both selected fitted models in the final window. These dependent, nonstationary diagnostics do not justify a causal or absence-of-population-information claim. Recipes are refitted within animals, not transferred as weights across animals.

Five known shared-rotation controls retain27.6–34.9%population-current improvement over five local lags; independentAR/AR2controls do not spuriously produce that advantage. The independent direct linear solve agrees with the population eigensolver's predictions within4.40e−14. The longer common-origin local-history ladder and all raw results are saved. Four reserved worm records stay unopened. No heat-response model is fitted here.

## Preserved failures and scope

The original coupled actor's oracle improves only7.206%while several learned critics do much better. This is a failed optimizer control. One target-blind per-order multistart revision passes on all three cases; original code/results remain separate. A reference-only unused-history index issue is corrected and preserved in WORM_REFERENCE_AMENDMENT.md; it did not affect the main/history/control comparisons. The follow-up export error and exact failed-at-export noise arrays are preserved separately; the repair changes serialization only.

The source paper already demonstrates predictive cancellation, irregular supplied premotor timing and simple motor learning. Existing physical vocal RL also precedes this block. The result concerns a restricted teaching recipe and scalar readout after manipulating available timing information. It is not a new general reward theorem, full correspondence mechanism, biological confirmation or an exhaustively verified priority claim. Independent scientific review is a separate PI work unit.

## Reproduction and strategic relevance

See README.md for exact sequential commands, SOURCES.md for source/license/access qualifications, and outputs/ for all actual queries, trajectories, controls and diagnostics. The deeper answer to original ideas1,2and7is in STRATEGY_1_2_7.md. Its first bounded empirical funding preference remains source-calibrated memory-policy prediction; teaching remains the computational bet, and the broad worm state-versus-changing-rules dichotomy requires restricted distinguishable models.

## All-plant temporal challenge

| Plant | Forward no-clock target rank/64 | Reverse-tutor no-clock target rank/64 | Retained-clock target rank/64 |
|---|---:|---:|---:|
|100|5|36|1|
|101|2|33|1|
|102|17|4|1|

All forward no-clock chosen orders have nonzero true error at exact tutor content (MSE6.6540,8.1098,8.1989). These are reachable finite policy counterexamples to reward fidelity. More averaging cannot turn a deterministic wrong minimum into the target. This does not establish failure of every actor or richer readout.

Reverse-tutor target ranks within the original six choices are5,2and1. In102, retraining changes preferred order from forward to reverse. Some acquired order information exists; it is insufficient for reliable ranking of the expanded policies. The network is not certified permutation-invariant or devoid of temporal memory.

All no-clock and tonic duration actors shorten0.8→0.7and worsen waveform error. Every waveform oracle reaches1.0. Retained-clock corrections are useful but biased in two cases:

| Plant | Retained-clock final duration | No-clock final waveform MSE | Retained-clock MSE | Oracle MSE |
|---|---:|---:|---:|---:|
|100|1.01875|2.62892|0.31047|0.01641|
|101|0.98750|2.54711|0.19235|0.001694|
|102|1.00000|2.65158|0.02332|0.02332|

Adding700ms quiet reproduces every original prefix score exactly and preserves all wrong no-clock/tonic duration preferences. No-clock final-minus-target gaps remain−0.002472,−0.011977,−0.006582Hz at2000ms. Retained-clock residual biases persist too. The declared finite window-truncation alternative fails this check; no infinite-window claim follows.

At source current-noise0.1, no-clock correct-order fractions are45%,20%,50%; at0.5they are25%,30%,35%. Retained-clock fractions are100%in all six comparisons,20sets each. These are dependent fixed-case assays with limited binomial precision, not biological replication or full noisy motor acquisition. The hypothetical scalar readout-noise tables are saved separately.

## Acquired teaching and verification

The two successful cases were selected explicitly for untutored falsification. Matched untutored searches remove1.637%and9.180%initial sequence error versus99.545%and99.412%after tutoring. Canonical content MSE is7.64488/8.60475untutored versus0.03556/0.05052tutored. This supports acquired target-specific teaching in those cases, not an unbiased population tutoring-effect estimate. In failed case101, canonical content MSE is0.00367: its complete-sequence failure is principally wrong ordering.

Author checks reconstruct gold losses for17searches within3.56e−15and replay every query/trajectory exactly from saved scalar feedback. Corrected worm references match within2.23e−15; direct solve agrees within4.40e−14; separately coded source dynamics match zero-noise costs within2.45e−15. Failed-at-export and repaired-run seeded noise arrays agree exactly. These are implementation consistency checks, not independent scientific signoff.

The earned result separates useful acquired content feedback and partial order memory from reliable temporal evaluation. Universal clock necessity is falsified by successful zero-HVC teaching; successful restricted learning still does not establish learned general correspondence. Supplying a relative timing template strongly improves the assays while retaining some reward bias. Scientific payoff is an exploratory recipe boundary and sharper allocation, not a completed biological mechanism or new general theorem.

Single best next step: an independent reconstruction of the64-order/duration counterexamples, including the longer readout and102's positive reverse-tutor preference, before funding a new learned temporal-context mechanism. Reuse consumed assets; this worker launches no reviewer or successor.

Resources:15specific public text commands/queries, no new numerical/biological dataset;15MB conservative public-text reservation, exact wire counts unavailable. Scientific reads417,000,703bytes at verification, below1GB; MANIFEST.json records final hashing charges. Serial processes/two-thread settings;35-rendition source arrays estimated below1GBagainst4GBceiling, measured control peaks about273MB. Main-batch full-process peak was not captured. Final allowance61%remaining, one primary window/no secondary; no credits spent/reset. Jobs0.

![Teaching pilot](/Users/vanshkumar/Documents/repos/devo-research-lab/lab/tasks/independent-sprint-pilots-2026-10-30/outputs/TEACHING_RESULT.png)

![Worm pilot](/Users/vanshkumar/Documents/repos/devo-research-lab/lab/tasks/independent-sprint-pilots-2026-10-30/outputs/WORM_RESULT.png)
