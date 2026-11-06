# Next research decision after quantitative HYPOMAP

2026-10-28. The user requested that the completed HYPOMAP study return its result to this research-decision context. This review closes that branch and selects a new empirical direction. No successor campaign, goal, thread or automation was started by this review.

## Decision

**Test whether a shared adaptation process predicts later behavior in people taught a task and people who discovered its rules themselves.** Use the newly public human IBL dataset, with held-out participants and stimulus schedules. The question is whether the learning routes differ only in early acquisition, or retain predictive differences in how recent evidence shapes choices after hidden probability changes.

This is a specific behavioral prediction test. It is not a claim that fitted parameters reveal a neural mechanism, that the conditions were randomized, or that the result generalizes to classroom education.

## What the completed atlas result changes

The quantitative campaign directly observed 204/309 C4-313 nuclei with both genes detected, but 195/204 had fewer than ten secondary counts. Only two satisfied the frozen substantial-expression rule, both in one sample; none of 186 Siletti nuclei did. Independent original-byte reconstruction passed. The failed severe-noise model recovery and low-depth sensitivity prevent claiming that endogenous low-level transcription is absent.

That is a completed negative nomination result. Switching to an already inspected neighboring cluster, fitting more latent mixtures, or trying to rescue a signature would not be a new high-value question. Bank the subset and code. Reopen the low-level-transcription question only if a separately motivated question brings an orthogonal same-cell measurement.

Evidence: [completed report](campaigns/hypomap_quantitative_2026-10-28/REPORT.md), [primary donor table](campaigns/hypomap_quantitative_2026-10-28/outputs/abundance/primary_table.csv), [adversarial audit](campaigns/hypomap_quantitative_2026-10-28/experiments/adversarial/AUDIT.md). These were inspected during this review; no campaign reproduction was rerun.

## The proposed empirical question

Participants perform a visual choice task. Some receive task teaching; others discover the rules by playing. Unsignaled blocks change which side is more likely to be correct. The authors already describe early performance improvement, pooled block bias and coarse learning windows. The useful next question concerns adaptation dynamics after those hidden changes.

Compare two explicit accounts:

- **Shared adaptation:** allow individual differences and different early acquisition trajectories, but use one population distribution of later evidence/history updating for both conditions.
- **Persistent condition difference:** allow the teaching/discovery condition to predict later adaptation parameters in addition to sensory sensitivity, lapses, response bias and early acquisition.

The principal endpoint should be held-out prediction of low/zero-contrast choices around probability switches in a fixed later interval, provisionally trials 201–600. Report the observable time course of old-context influence as well as prediction scores. Fix the interval before opening the main outcomes; do not select people or windows because their achieved accuracy matches.

The meaningful advance is a quantitative test of whether the shared-adaptation account transfers across people and schedules. A positive result requires a reliable predictive improvement beyond nuisance/early-learning differences. A negative result requires recovery and precision sufficient to exclude a predeclared meaningful difference. Failure to reject a group effect alone is not equivalence.

## Verified data and protocol

[Hoxha et al. 2026](https://doi.org/10.64898/2026.10.01.755923), posted 8 October, declares the [public Zenodo dataset](https://zenodo.org/records/23072548). The live API, complete small participant metadata and an 8,192-byte prefix of the actual trial CSV were retrieved. The release covers 80 participants and 48,000 trials, with 39 instructed and 41 uninstructed participants. The trial file is 134,562,545 bytes, declared MD5 `5bc8ccf8bdca2e89fc21d20ffb7c1695`; the 44,599-byte participant file matches its declared MD5. Full trial data were not acquired or analyzed.

The CSV header contains subject/session/trial, probabilityLeft, contrasts, choice, feedback, stimulus side, instruction condition, response and movement times, and continuous cursor positions/times. Pupil data are planned for a future release; do not assume they are available from the abstract. Preserve pseudonymous IDs and avoid unnecessary demographic output.

Pinned [task code](https://github.com/cocosys-lab/human_IBL_cursor/tree/47ac8356432972c7e6e5a887f15a7dd2d6c686ad) adds consequential qualifications:

- Teaching bundles written rules, examples and five practice trials. It explains the motor/contrast/feedback mapping, not the changing probability blocks. This is not a verbal-instruction-only manipulation.
- The authoritative builder assigns condition by participant ID modulo four. The exported participant metadata matches that rule in 77/80 cases, with three uninstructed exceptions. Historical assignment and protocol chronology remain to be reconciled. Do not call this randomized.
- Ten pregenerated sequences are assigned by ID digit, but preprocessing changes some IDs. Reconstruct actual sequences from trial arrays instead of trusting the exported digit. Both groups occur within the metadata-based sequence proxies.
- Correctness is determined by the scheduled hidden target side, including zero-contrast trials. There is no fresh choice-independent reward coin flip. On responding trials, normalized choice multiplied by signed correctness should reconstruct the target side. Verify the identity before analysis. Rewarded-choice history and revealed-side history cannot be presented as independently identified mechanisms here.

The [analysis repository](https://github.com/cocosys-lab/2026-human-ibl-analyses/tree/1283c6ddd61fc17d9065a5b017d0e3cfd17535cb) inspected in this review contains descriptive psychometrics, pooled prior bias, response/cursor summaries and 200-trial windows. No exact held-out switch-adaptation comparison was found in that bounded inspection. Full manuscript retrieval returned HTTP429; checking the complete primary account and close prior work is still an initial novelty gate. Generic history effects and abrupt learning are established territory, including [Bruijns et al. 2026](https://www.nature.com/articles/s41593-025-02130-x). This recommendation does not claim discovery of either.

Preserved acquisition evidence: [manifest](sources/human_learning_feasibility_2026-10-28/MANIFEST.json), API metadata, participant metadata, trial-prefix bytes/HTTP headers and pinned task builder. The first raw record was inspected for format; no group outcome comparison has been computed.

## Execution and stopping criteria

1. Reconstruct conditions, exact schedules, feedback coding, omissions and protocol versions. Verify the scientific question is not already answered by the primary work. Freeze a simple primary model comparison and reserve participants, including complete schedules, before examining their outcomes.
2. Start with regularized shared-versus-condition-dependent adaptation models that both allow individual variability. Give them the same sensory/lapse/early-acquisition flexibility. Update latent beliefs chronologically using information available to the participant; never feed the hidden block label to the behavioral predictor. Block labels may define evaluation windows and an explicit oracle diagnostic.
3. Validate on held-out participants and held-out schedules. Do not tune group parameters on the validation choices. Compare a simple fixed history kernel and an explicit context-updating formulation only to the extent model recovery supports their discrimination. Avoid a flexible model tournament on the full dataset.
4. Use the actual schedules for known-effect and null recovery. Measure whether the data can detect practically useful differences in post-switch choices. Cursor data are a secondary motor/behavioral check; cursor endpoints determine choices and are not independent confirmation.
5. Report whether any improvement generalizes across sequences and survives assignment-exception, participant-ID/order and ordinary sensory/motor explanations. Condition association can remain useful, but it does not isolate a causal instruction effect.

Stop or narrow the claim if sequence/protocol reconstruction fails, nuisance structure is inseparable from group, recovery fails, or the apparent finding only repeats published pooled bias. A completed study should deliver a locked predictive comparison, a measured adaptation effect or useful bound, and transparent limits—not another broad proposal.

## A more mechanistic song lead was checked and parked

Scherrer et al.'s August2026 [nCAF preprint](https://www.biorxiv.org/content/10.64898/2026.07.31.740148v1) has public neuronal-contingent-feedback data at [FeeLab/ncaf_paper_code](https://github.com/FeeLab/ncaf_paper_code). The tempting new question was whether pre-feedback neural covariance predicts later off-target plasticity in unseen birds. The source already analyzes training-period correlations and eligibility-kernel transfer, so those are not new projects.

A 13,406,882-byte primary session was downloaded and matched to its Git blob. Its sparse spike tensor was successfully decoded in Python: 17,640 samples ×731 motifs ×391 units, with 69 LMAN single-unit labels. No neural covariance or learning outcome was calculated.

The decisive check undermined the proposed baseline: the code describes the first100 motifs as before feedback, but the actual flags contain38 noise events in those100, starting at motif50. The preceding49 noise-free motifs do not identify feedback-enable time. The inspected export also lacks contingency-enable, threshold-history and catch-trial metadata. This is a specific conflict between a code comment and exported flags, not a demonstration that the paper's main result is wrong.

Park the pre-feedback forecast until adequate baseline timing and contingencies can be verified. Do not relabel early training as baseline. The single-target core also has only four sessions from three birds. [Preserved source/data manifest](sources/ncaf_feasibility_2026-10-28/MANIFEST.json), [schema](sources/ncaf_feasibility_2026-10-28/mat_schema.json), and [decoder](sources/ncaf_feasibility_2026-10-28/decode_preflight.py) make this a reusable feasibility result.

The human study is selected because its required choice/history observations and multiple independent subjects are demonstrably available, while this more mechanistic song test presently lacks its defining baseline.
