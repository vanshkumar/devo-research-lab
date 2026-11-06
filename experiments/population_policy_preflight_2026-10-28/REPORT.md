# Frozen-model policy-swap preflight

2026-10-28. **The policy prediction is large enough to justify a separately frozen population transport test.** This is a simulation diagnostic, not evidence that the prediction is correct or a revision of the failed individual-forecast gate.

Four previously consumed source animals were selected by SHA256(subject): ibl_witten_11, CSHL_013, ZM_3001, and ibl_witten_17. Each had 64 paired particles, the same first 1,000-trial calibration and 3,000 future opportunities under both policies. The main run took 6.40 seconds. No external prefix/outcome or source post-prefix outcome was loaded. The RNN reused its saved fitted W0; its full prefix-derived recurrent memory and existing joint uncertainty propagation were retained. The fixed development growth bank and its existing last-500-trial nuisance-calibration recipe were replayed. No learning-rule parameters were fitted.

| Six-bin mean accuracy | Adaptive policy | Fixed mixed-contrast policy | Fixed minus adaptive |
| --- | ---: | ---: | ---: |
| RNN, identical ±100% realized trials | 58.14% | 83.48% | +25.34 pp |
| Growth, identical ±100% realized trials | 56.82% | 56.69% | −0.13 pp |
| RNN, identical ±100% probability probe | 59.66% | 83.57% | +23.91 pp |
| Growth, identical ±100% probability probe | 56.80% | 56.80% | 0.00 pp |

Accuracy averages left and right equally and treats omissions as failures. Probability probes are read-only queries to the model and deliver no training or feedback. Their difference from realized adaptive-trial accuracy reflects state-dependent task sampling, so both are retained.

The RNN's realized ±100% policy contrast has conditional Monte Carlo SE 0.57 pp; the probe contrast has SE 0.52 pp. All four source-prefix contrasts are positive, ranging from +24.42 to +26.74 pp for realized accuracy. The fixed-policy RNN-minus-growth gap is +26.79 pp, conditional Monte Carlo SE 0.53 pp. These are numerical simulation errors conditional on four selected prefixes and a frozen model, **not biological uncertainty, calibration intervals, or external-cohort power**.

On the campaign's original >=50% metric, fixed-policy RNN-minus-growth remains +26.79 pp because this fixed policy's only high contrast is 100%. That is substantially larger than the root source-only, optimistic N=20 scalar threshold of 6.42 pp for 80% power. Transported source residual variance is an assumption; neither four source prefixes nor the threshold establish actual external sensitivity. Nevertheless, a near-zero curriculum prediction is no longer the reason to reject a prospective population test.

## Input and implementation checks

- The fixed generator uses uniform [1, .25, .125, .0625] contrasts, independent equal-probability sides, no correction trials and no performance-based promotions. It is the existing Pan-like mixed policy, not an all-high-contrast curriculum. Existing `protocols/TRAINER.md` documents agreement with the paper and previously inspected first-session input metadata; the custom acquisition source remains unavailable. This run performs no additional external inspection.
- The two arms begin with identical source-calibrated learning state and uncertainty. They differ in generated curriculum after the prefix; this is a source-animal policy intervention diagnostic, not yet an actual external-animal forecast.
- Future choices, correctness and learning updates are generated recursively. Session boundaries come only from already-pinned opportunity counts. Acquisition dates, stage labels and future observed outcomes never enter the rollout.
- The RNN receives binary correctness, not physical reward volume, wheel gain or elapsed time. The prediction therefore cannot certify invariance to those between-study changes. Future opportunities and boundaries are conditioned on, not predicted.
- A same-seed, same-64-particle standard-policy rollout for ibl_witten_11 was checked against the original frozen `rnn_rollout.autonomous` API: all original-metric values match exactly, maximum difference 0. This verification also reused saved calibration without fitting a learner.
- The mean original-metric prediction across these four animals is 57.96% at 64 particles versus 59.49% in their existing 512-particle files. The exact API check rules out a custom-rollout discrepancy; the small preflight is not a replacement for the original production forecasts.

## Decision

Proceed only as a **new, explicitly population-level forecast transport question**: does the frozen learning rule predict the mean acquisition trajectory under a different observed training protocol? Preserve the original failed individual gate. Freeze the new estimand, population calibration criterion, outcome-access sequence, predictive comparison and rejection rule before any fresh outcomes. A fresh source population check can test mean-curve calibration independently of these consumed histories. Keep external outcomes sealed until that check passes and prefix-only external forecasts establish material model separation under the actual external initial states.

The scientific payoff is a direct and potentially sharp falsification: a rule that matches mean source acquisition predicts a much faster fixed-policy acquisition than exposure alone. If this survives prospective calibration and external scoring, it is stronger than generic within-protocol prediction. If it fails, the conclusion concerns this frozen rule's transport, not proof of which biological learning mechanism is correct. External success would also not identify a causal curriculum effect because the cohorts and protocols differ beyond contrast allocation.

Stop if fresh source mean calibration fails, external-prefix forecasts collapse the model separation, or input-only protocol checks invalidate the fixed generator. Do not repair the latent state, tune the law, select a favorable time window, or reinterpret a failed external comparison within the same confirmation cohort.

Artifacts: `PLAN.md`, `run.py`, `RESULT.json`, `PARTICLES.npz`, and the local `EXPOSURE.jsonl`. Only this experiment directory was written.
