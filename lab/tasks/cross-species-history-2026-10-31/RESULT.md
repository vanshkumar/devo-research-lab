# A cross-species history-transfer penalty depends strongly on the observation baseline

2026-10-31 local. **Partial author result; resource stop; independent review pending.** Scientific execution stopped when the completed control run reported 1,128,546,304 bytes peak RSS, exceeding the 1GB cap. No additional science, original-byte audit, model repair or successor was run afterward. Saved fits and scores are inspectable evidence, not independent signoff.

The narrow result is a conditional prediction comparison: **human-fitted revealed-side history weights lose 0.01065 nat/choice in mice against a strong response-history baseline, but that penalty falls to 0.000080 when the baseline also represents past physical stimulus side.** Neither version earns positive history-transfer utility. This baseline dependence cautions against attributing the original transfer penalty to a species-specific biological update. It does not prove that stimulus adaptation explains behavior, that feedback is unused, or that a common biological law holds.

## What was compared

The exact consumed-record certificate is [ALLOWED_MANIFEST.json](ALLOWED_MANIFEST.json): 80 human sessions, the original 74 development mice plus 48 fully consumed source mice. Only the first 6000 rows of each admitted mouse were extracted. The input pass reconstructed 48,000 human and 617,203 mouse rows; no new cohort, protected outcomes or raw download. Mouse NPZ hashes match old exposure records, and per-session identities/chronology match the old source index. Human numeric derivatives inherit the previous campaign's frozen extraction and independent reconstruction; this run's planned fresh original-CSV audit was **not executed**.

The main comparison uses opportunities 200–599, at least 32 rows into a session, at exact common numerical absolute contrasts {0,.25,.5,1}. Shared-support cells require both species, multiple units and multiple human schedules; the scored responding subset contains **16,619 human choices from 80 people and 39,709 mouse choices from 122 mice**. Numerical contrast equality does not establish matched sensory difficulty or physical stimulus equivalence. Human contrast .1, an important difficult condition in the previous human analysis, has no exact mouse match and is outside this test.

Five folds hold whole human schedules together and hold mouse animals out within labs. All data are consumed development; these splits do not restore validation. First-200 summaries are the only individual calibration. Prediction may use preceding test choices/feedback, and is conditional on actual stimuli/history, not an autonomous learner.

B includes separate discovery/taught/mouse sensory and response/exposure effects, previous choice and choice EWMAs. It is a **no-added-revealed-side-history baseline**, not an agent without any history. H adds one common coefficient vector on revealed-side EWMAs at 2/8/32 opportunities; T separates human and mouse coefficients. Human-fixed and mouse-fixed freeze source history coefficients while fitting target nuisance only on other target units. The predeclared adversarial step S adds task-specific physical-stimulus-side EWMAs to the same baseline. [PLAN.md](PLAN.md), [FREEZE.json](FREEZE.json), [feature names](corrected/FEATURES.json).

## Saved predictive results

Entries are equal-unit log-score gains, nat/choice, on common support. Positive favors the first account. Brackets are 95% **conditional, fixed-fit** resampling intervals: human schedule/person and mice within their observed labs. They omit refit/model-selection uncertainty and are not certified biological coverage bounds. The predeclared material point margin was .005 nat/choice; null/small gains are not equivalence.

| Baseline / contrast | Human | Mouse |
|---|---:|---:|
| B: shared H − B | +.000809 [−.000525,+.001846] | −.001924 [−.002884,−.001051] |
| B: task-specific T − H | +.000325 [−.001468,+.002059] | +.001843 [+.000915,+.002868] |
| B: human-fixed − B | +.001131 [−.001701,+.003570] | **−.010652 [−.012720,−.008768]** |
| S: shared H − S | +.000883 [+.000024,+.001927] | +.000068 [−.000205,+.000321] |
| S: task-specific T − H | −.000060 [−.000316,+.000178] | +.000239 [−.000003,+.000533] |
| S: human-fixed − S | +.000859 [−.000178,+.002114] | **−.000080 [−.000403,+.000222]** |

The task-specific account's gain over human-fixed in mice is .010570 [.008620,.012718] under B and .000386 [.000048,.000794] under S. Under B, mouse-specific history itself gives −.000081 [−.000202,+.000050] against B. Thus a poor imposed human coefficient vector does not imply useful new mouse feedback updating. The stronger input-history control greatly narrows this particular failure without earning a transferable positive update signal.

The complete predeclared scopes (all exact common-contrast rows, zero and high contrast), Brier scores, leave-one-lab/schedule summaries, per-unit losses and all predictions are saved in [SUMMARY.json](corrected/SUMMARY.json), [B unit scores](corrected/unit_scores_B.csv), [S unit scores](corrected/unit_scores_S.csv) and [predictions](corrected/predictions.npz). Dedicated per-contrast audit tables and the optional extended mouse exposure-window sensitivity remain unrun.

## The actual-input observation alternative

Every responding nonzero-contrast input has `choice × feedback = physical stimulus side`: zero mismatches across the extracted data. Human reward-side and revealed-side encodings therefore do not identify distinct mechanisms. More generally, the implemented histories satisfy, to <5.5e−16 in the primary rows,

`revealed history = physical-side history + responding-zero revealed history − omitted-nonzero physical history`.

This is a tested actual-input identity, not a general impossibility theorem. Adding (1,1,1) to revealed coefficients and subtracting it from stimulus-history coefficients changes logits only through those residual channels. Their observed combined shift RMS is .2922 in humans and .1077 in mice; the average worst-case logistic probability-shift bound is .04932 and .00686 respectively, with large possible shifts on some rows. 26,798 of 40,418 responding mouse rows have residual below 1e−12. These facts show uneven separation of the two histories; they do **not** show exact equality on every row or establish a latent storage/readout equivalence. [DIAGNOSTICS.json](corrected/DIAGNOSTICS.json).

Mouse `probabilityLeft` is an adaptive anti-bias/correction field. The 227,931 within-session changes in these prefixes are descriptive encodings, not homologues of the 831 human scheduled block changes. Correction trials may repeat contrast magnitude without repeating side. The early `repNum==1` diagnostic was mislabeled “no_repeat,” corrected in code before freeze, and never used for fit/selection. [Input support](INPUT_SUPPORT.json), [trainer methods](../../../campaigns/learning_rule_transport_2026-10-28/protocols/TRAINER.md).

## Checks, failures and unfinished validation

- Frozen original code/protocol remain intact. Initial NumPy matmul warnings were investigated on finite actual feature matrices: explicit products agree within 5.55e−17 (forward) and 9.09e−13 (transpose). Optimization/prediction were changed to explicit contractions without scientific changes. History reconstruction, current/future suffix invariance and directional-gradient checks passed in the saved diagnostics. All fitted records and their convergence diagnostics are saved; no independent optimizer reconstruction has been earned. [Numerical audit](corrected/NUMERICAL_AUDIT.json), [amendment](NUMERICAL_AMENDMENT.json), [fits](corrected/FITS.json).
- The corrected main pass saved both model sets, scores, 50 fitted records and predictions, then failed only on the resource logger's input path. That one-line bookkeeping fix changed no score. Main peak RSS was consequently not recorded. The first controls pass subsequently failed while requesting a deliberately absent transfer column in its summary; a guard was corrected before its restart. Failed passes remain charged and documented; no favorable run replaces them silently. [Logging amendment](LOGGING_AMENDMENT.md), [control amendment](CONTROLS_AMENDMENT.md).
- All 18 fixed-design synthetic datasets (six null, six shared +1.5*h8, six human +1.5*h8 / mouse −1.5*h8) and both baseline families completed, with 540 ordinary control fits saved. These condition on recorded predictors/omission masks; they are not complete generated learning processes. Detailed [control scores](corrected/CONTROLS.json) and [fits](corrected/CONTROL_FITS.json) are archived. The final [control resource log](corrected/CONTROL_RUN.json) reports **1,128,546,304 bytes peak RSS**, exceeding the 1GB cap. Stop was immediate on reading that completed-run record. No calibrated recovery, meaningful-effect sensitivity or biological interval coverage is claimed; a final compact control assessment was not performed after the resource stop.
- [audit.py](audit.py) was written before the limit was observed but **never executed**. It does not supply original-byte verification or independent prediction reconstruction. A separate independent scientist has not yet reviewed these results. Optional larger-window fitting, low-level original-Parquet audit and further source verification remain unrun.

Conservative additional-read/hash/decoded charge is **650MB of 750MB**, including all failed passes and repeated cache loads. Eight logical public operations used literature/code only; reserve the full20MB ingress cap because provider transport was not directly metered. No raw acquisition, external contact, paid API, new framework or old-file edit. All old exposure/failure/freezes and protected targets remain unchanged. [Resources](RESOURCES.json).

## Prior work and decision

Cross-species history dependence is established: Fernandez/Fengler/Urai's author repository describes a common history-dependent evidence-accumulation strategy; the IBL behavioral paper analyzes prior success/failure and task standardization; Weilnhammer et al. analyze sensory/history weighting in humans and mice. This result is not a replication/refutation of a diffusion model, a first discovery of shared history, or a species-specific mechanism result. New primary full-text attempts hit 403/challenge/404; literature priority remains limited. [Sources](SOURCES.md).

**Recommendation:** bank this as a provisional observation-model sensitivity, with the memory-cap breach and unfinished validation explicit. Do not fund new mouse-rule tuning or consume protected cohorts from this transfer penalty. The single most useful next step is a fresh, bounded independent review of the saved source-fixed penalty and its S-control, including score reconstruction, actual contrast/support coverage and whether the declared controls discriminate the relevant alternatives. That review must decide whether anything stronger is warranted; this author dispatches no successor and performs no further science under this allocation.
