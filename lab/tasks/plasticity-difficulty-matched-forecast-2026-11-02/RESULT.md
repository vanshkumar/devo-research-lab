# Same-task acquisition ran; random-target assay earns no added decision value

**Decision: CLOSE this fixed paired-state pilot; no main campaign or seed/settings repair.** The proposed assay fails every frozen investment criterion. The evidence is a bounded development result, not a universal diagnostic impossibility or completion of the lab's scientific goal.

Four new independently drawn original SCR teacher/history units each trained two independently initialized original five-ReLU learners through the COMPLETE 1M-update/100-task history. Within each pair, training history, age, learning rule and feedback budget were identical. Both mature states then learned the SAME new task with the SAME 10k input sequence. This removes the preceding pilot's one-state/changing-task design confound. It does not match initial competence or make all four task difficulties identical.

The 20-input/15-slow-bit, 100-LTU teacher, five-ReLU learner, .003 squared-loss SGD and 10k task period follow pinned original source equations. This is float64/Python RNG execution, not author Torch execution, a published-curve replay or a controlled replication of plasticity loss. See [prior/information gate](PRIOR_INFORMATION_GATE.md) and [fixed plan](PILOT_PLAN.md). Same-task future-learnability diagnostics already exist; no generic measurement novelty is claimed.

The target-blind observer knows completed history, weights and the announced next input support, while the fixed latent teacher belongs to the scorer. Known teacher parameters would permit direct simulation and change this forecasting problem. No true future labels, teacher parameters or actual future SGD draws enter target-blind features. The labelled alternatives explicitly buy all32 future support labels. Models are calibrated on preceding tasks10,20,...,90 only, with36 correlated pairs across four units, fixed ridge10 and no future-score selection. Neither the 36 calibration pairs nor the ten probe functions are independent learner samples.

BLIND_FORECASTS was saved04:51:09Z, hash `4e67f5d76faf564fb0dd6673e84a27059b003765e96b68abd2f891aa1c09b6b7`; the pre-feedback nondegeneracy check passed04:52:02Z before the15-minute gate. DIRECT_FORECASTS was saved04:52:38Z, hash `cc420efb43cfa8519654f17e64ca1e430a6e582153485ca31999ae4ac3b3e4fc`; actual acquisition completed04:53:34Z, before the30-minute gate. Script sequencing/native command outputs support this chronology; later hashes are consistency checks, not independent trusted timestamps.

Primary error is squared error in the signed paired difference of log(1+final MSE). Selection regret is actual final MSE of the chosen state minus the better state's final MSE, averaged over four units.

| Frozen forecast | Mean paired forecast error | Correct rankings | Mean selection regret, MSE |
|---|---:|---:|---:|
| Strong history/weight/input-activation baseline | .038906923 | 1/4 | .029045513 |
| Baseline plus ten-function random-target assay | .044451346 | 1/4 | .029045513 |
| Calibrated labelled initial competence | .047255861 | 2/4 | .014845116 |
| Calibrated labelled20k-copy forecast plus baseline | .015071211 | 1/4 | .029045513 |

The assay increases planned forecast error **14.250% versus baseline** and194.942% versus the calibrated full-copy alternative. Its state selections are identical to baseline on all four units, so it supplies no selection-regret increment. The calibrated copy improves score without improving the reported ranking count/regret; these are distinct decision quantities. Initial competence has poorer log-risk forecast error but about half the selection regret; its privileged label access remains explicit.

| Independent unit | Initial MSE, state0/state1 | Final MSE, state0/state1 | Better final state |
|---|---:|---:|---:|
| 0 | 7.2240 / 9.0132 | 1.342784 / .510476 | 1 |
| 1 | 6.1224 / 5.5928 | .947447 / 1.004249 | 0 |
| 2 | 2.7821 / 5.1065 | .445604 / .504438 | 0 |
| 3 | 17.2290 / 11.2300 | 1.050217 / 1.049670 | 1 |

All eight learners improve on their future task, removing81.4–94.3% of initial MSE. Paired initial ordering reverses in two units. The largest final difference,.832308MSE, is already ranked correctly by the simple baseline and assay; the other gaps are.056802,.058834,.000547. Future teacher variances1.3428–3.6318 differ between independent units but are identical WITHIN each pair. The contrast is not uniformly dead: future-support dead fractions are.6–1, with active units in seven of eight states. A one-function forecast changes sign across random functions in unit1; averaging ten does not rescue this failed result. No random-probe precision or population-uncertainty guarantee follows from four units.

Both assay and labelled copy consume20k optimizer steps PER STATE: ten2k random-function copies versus one20k true-task copy. That is twice the actual10k future training budget. The target-blind method requires zero true future labels; labelled methods consume32 unique support labels per pair/128 across this pilot, with20k repeated labelled updates per state. Random-network target generation, ten state copies, support scoring and RNG/storage are additional costs, so matched step counts are not equal total cost. Maximum measured process RSS is47,005,696bytes; the core111float64 parameters are888packed bytes, not total Python/process storage. All copies preserve originals. Preceding calibration costs1.44M extra random-target and1.44M labelled-copy updates, in addition to8M history updates. Final assay160k/copy160k/actual acquisition80k give **11.28M new SGD updates**, plus80k separately evaluated reference updates. Full prepare time91.4685s, direct1.2751s, acquisition/reference1.9035s; complete measured numerical scripts total about94.7s before final artifact filing.

Numerical checks pass: ALL12,928 consumed true support labels agree between integer-threshold and floating source equations;48 checkpoint SGD references/finite-difference checks (maximum scaled derivative discrepancy4.04e-9); ALL80k future updates independently replay (maximum parameter discrepancy6.00e-15); independent scalar initial/final scoring; all four frozen regression fits reproduced with a different Cholesky solver (coefficient discrepancy<=1.12e-16); every forecast score/rank/regret reconstructed. These are within-investigator references, not distinct independent review. Full8M history update-by-update reference is UNRUN.

Four new public operations followed ONE closest-prior program; no source failures, model failures or scientific revision. Charge full15MB new ingress allowance/exact provider traffic UNCERTIFIED and500MB separate read/import/context booking, retaining unknown physical I/O. Preserve prior81operations/429,594,722 ingress allowance/2.3GB separate reads, all old failures/resource qualifications and all development/protected exposure. No protected or old numerical payload was opened. [RESOURCES.json](RESOURCES.json) carries counts, limits, exposure and unknowns; [AUDIT.json](AUDIT.json) carries actual arithmetic. Raw generated states and all support/summary observations remain development forever.

The result earns an executable original-history SAME-task state comparison and a concrete failure of this assay under stronger alternatives. It earns no useful general forecasting effect, causal plasticity mechanism, biological conclusion, optimal direct forecaster, exhaustive priority finding or main protocol. Close this fixed comparison without a generic calibration/repair queue. The PI retains the broad unfinished scientific goal and active operator heartbeat. Jobs0; no shared records were edited. Terminal delivery disposition is saved separately.
