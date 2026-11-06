# Learned reliability under context uncertainty: bounded synthetic result

The completed pilot demonstrates a restricted constructive result: a fixed algorithm can identify the fair random transition without its location being supplied, preserve context-dependent deterministic edges after blocked training, and maintain performance when the random transition moves. It also demonstrates a serious failure: early interleaving can prevent context discovery, after which the same mechanism calls deterministic transitions unpredictable. This advances computational feasibility, not quantitative human forecasting.

## What was frozen and tested

[The protocol](FROZEN_PROTOCOL.md) and [code](pilot.py) were hashed at19:18:01UTC before seed27001–27020 generation. Development used only four original-task sequences, blocked/interleaved seeds11/12. The first transition-level implementation produced biased reliability estimates; [its code and result](development_failed_transition_gate.json) remain preserved. One inference refinement reused those same sequences; there was no numeric search or scored-control repair.

All three scored roles share the exact published Simulation2 concentration/stickiness/sparsity values1.7026910310943673/1.8476105399460376/.2112472814674634. Original and oracle are source-faithful SEM replicas; the oracle skips the evaluator-designated random transition. On relocated-noise controls its location is changed explicitly for the oracle. It is an advantaged local-MAP model, not a perfect-performance upper bound. The native Simulation1 parameterization was also reproduced on the original development sequences, separately from this matched comparison; see [native reconstruction](native_development_reconstruction.json).

The learned role compares integrated Dirichlet(.5,.5) likelihoods within inferred schemas with a fair-draw likelihood for each observable outgoing state. Conditional deterministic differences can provide strong evidence even when pooled entropy is maximal. It maintains a filtering posterior over a constant context within each visibly bounded story, and updates one local-MAP context after that story finishes. Noise likelihood is mixed with schema likelihood in proportion to previously learned reliability. Prediction averages current schema transition estimates before applying the same source response softmax. This is an approximate discrete reliability mechanism, not exact joint Bayesian inference or an implementation of every normative model cited by the publication.

Ordinary state identities, two-candidate structure and new-story boundaries are available to every role. Learned code receives no context label, curriculum/family label, noise index or future observation. Its fair-noise and story-persistence assumptions are substantive. Improvements change persistence and posterior averaging alongside reliability; the three-role experiment does not isolate a causal contribution from the gate alone.

## Quantitative results

Each cell is the mean pre-update correct-choice probability (%) at deterministic non-cue transitions in the final40stories, averaged over20new seeds. All200stories per sequence are generated online; no extra training/probe stories were added. Each of the300unpermuted sequences has one exact state-label permutation, for600sequences/1800model runs.

| Family / curriculum | Original, matched | Oracle exclusion | Learned |
|---|---:|---:|---:|
| Original / blocked | 49.73 | 93.13 | 98.10 |
| Original / interleaved | 49.86 | 67.91 | 51.14 |
| Original / early | 49.73 | 93.31 | 98.10 |
| Original / middle | 49.95 | 67.93 | 51.22 |
| Original / late | 49.86 | 67.95 | 51.12 |
| Noise relocated / blocked | 73.98 | 61.46 | 98.12 |
| Fully deterministic / blocked | 82.14 | 82.14 | 98.15 |
| Fully deterministic / interleaved | 82.14 | 82.14 | 82.13 |

Original blocked learned-minus-original gain is48.38pp, paired-seed bootstrap95%interval[48.01,48.75]. Learned-minus-oracle is4.97pp; this is not evidence that an oracle is intrinsically harmful because their inference rules differ. Blocked conditional log losses are.7073/.0916/.0192nats for original/oracle/learned; learned modal accuracy is100%, with the source temperature4link keeping choice probability below100%.

The first5return stories after the intervening40-story block score97.99%learned,93.30%oracle and52.53%original. This is early-return online performance, not a separate no-learning memory probe. Learned final context purity is1.00 in blocked original/relocated/deterministic families, with two active schemas.

The learned original blocked weights are1.000for deterministic signal versus.1165for the random edge; after relocation they remain1.000/.1165. All deterministic blocked edge weights are1.000, including the shared outgoing state whose next state differs by context. Thus this is not merely a pooled-entropy gate.

The failure is equally clear. On original interleaved sequences, learned signal/noise weights average.1251/.1485 and context purity is.5788. In the fully deterministic interleaved control, the specifically context-dependent last edge gets weight.0590 and correct-choice probability50.08%, despite the preceding two edges being learned. There is no irreducible noise there. Failure to discover contexts can masquerade as aleatoric uncertainty. The frozen simple blocked control criteria all pass, but they do not establish universal learned-noise independence.

Synthetic early-minus-late contrast is46.98pp[44.30,48.55]original,24.01pp[23.72,24.31]relocated and16.02pp[15.94,16.08]deterministic. These are stimulus-generator predictions; no human scores or fit were used. The bootstrap describes20-seed Monte Carlo variation and says nothing about human uncertainty or empirical calibration.

## Verification and limits

[The audit](AUDIT.json) passes25checks. All1800metrics independently reconstruct with zero discrepancy; independent beta-function reliability calculations on all600learned runs agree within2.29e-14. All900role/seed state-permutation comparisons are exact. Altered evaluator context/noise labels and future suffixes do not change learned past predictions. Twelve saved runs replay exactly offline; all200deterministic oracle/original pairs are identical. Native source assignments and linked probabilities agree exactly. This is separate mathematical/code checking by the same investigator, not an independent scientist review.

Scientific execution took17.20s; the complete separate audit took39.81s, peaking at134.2MBRSS in one process. No dependencies were installed. Optional plotting could not run because Matplotlib is absent from both the existing model environment and the bundled runtime; tables and machine-readable results are complete. Keep this as a nonblocking rendering limitation.

The strongest limitations are endogenous hard context assignments, fair-noise specificity, constant-context stories, confounded inference changes and failure after interleaved starts. Human response, timing, attention and selection schemas were not opened. Exact source blobs are pinned, but archived Zenodo version correspondence remains unverified; see [the value-blind source report](../../../sources/noise_context_feasibility_2026-10-29/SOURCE_REPORT.md). No empirical transport, biological mechanism, novelty or publication-readiness claim follows.

## Reproduction and decision

Use the existing interpreter, from repo root:

```sh
campaigns/learning_rule_transport_2026-10-28/.modelenv/bin/python lab/tasks/noise-context-feasibility-2026-10-29/pilot.py score
campaigns/learning_rule_transport_2026-10-28/.modelenv/bin/python lab/tasks/noise-context-feasibility-2026-10-29/summarize.py
campaigns/learning_rule_transport_2026-10-28/.modelenv/bin/python lab/tasks/noise-context-feasibility-2026-10-29/audit.py
```

These regenerate only consumed synthetic controls; retain original files/hashes before replay. No new model, human fit or next stage is authorized here.

Recommend one bounded value-blind archived-version/export-schema audit next. It must certify exact code/release identity and complete per-person stimuli, predictions, attention items, omissions and inclusion denominators, including whether threshold0actually covers all recruited completers. A successful audit would make an independently reviewed, source-only-to-mixed quantitative test concretely designable; failure would stop this empirical route. The present task ends with a positive restricted computational asset and unresolved human feasibility, preserving the persistent curriculum-learning question and all protected data.
