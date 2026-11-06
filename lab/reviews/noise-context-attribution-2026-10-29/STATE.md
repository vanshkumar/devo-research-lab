# Noise/context attribution review

Status: COMPLETE. Durable independent review returned; no jobs running, successor or continuation launched.

Reviewer: existing durable chat `01a1885c-3822-7bc0-88b7-e5fd7343299a`, assigned GPT-6.1 Sol/max; the new task is already reserved by the PI. Earlier HABITS work is complete and is not resumed.

Start: 2026-10-29 20:52:50 UTC (16:52:50 America/New_York). Deadline: 2026-10-29 21:17:50 UTC (17:17:50 local). One process, at most 2 GB and five minutes simulation runtime; no network, installs, new chats, subagents, fitting, new primary model, or automatic continuation.

Completed: froze COMPARISON.md/ablation.py before execution; ran the sole from-trial-one reliability=1 ablation on 240 consumed seed/family/curriculum inputs and their exact state permutations, with paired full-model reruns (960 runs). All 480 full reruns match frozen saved predictions/weights/assignments exactly. One pre-execution amendment cached saved arrays once; original hash and reason are retained in FREEZE.json. No post-result model/metric change.

Main finding: blocked full/ablation probabilities are both about98.10%; original interleaved improves51.14%→98.10% without gating. The full-minus-ablation effect is−46.97pp, paired-seed95%interval[−48.53,−44.30]. Relocated/deterministic interleaved effects are−23.99/−16.02pp. This isolates the weighting prescription's contribution, including initial .5 reliability and its effects on later assignments; it does not split prior versus reliability learning, or persistence versus averaging.

Checks: independent reviewer AUDIT.json passes45checks, including source pins/native chronology, independent scores and beta evidence, pre-observation/future/evaluator-label causality, and exact state permutations. Combined simulation/audit72.24s, peak180.37MB, one process at a time; no jobs running. Files remain separate from originals. No human arrays/headers, archives, personal fields, Pan20, Flesch81 or HABITS future data opened. Fresh manually checked allowance68%remaining; no credit/reset.

Decision: REVISE attribution and investment. The blocked gain belongs to the retained story-level inference package; reliability weighting largely induces interleaved failure and early/late ordering here. This is a reliable component diagnostic, not actual quantitative human transport. Retain the matched ablation as a strong baseline. One bounded value-blind archive/schema audit is worth consideration only to design a falsifiable source-fixed human full-versus-ablation comparison. No automatic gate correction, renewed exhausted source search, human fitting or protected access.

Outputs: REVIEW.md, RESULT.md, COMPARISON.md/FREEZE.json, separate ablation.py/ABLATION.json/prediction and metric files, audit.py/AUDIT.json, AUDIT_NOTES.md, EXPOSURE.json and PROPOSED_LEARNING.md. All45independent checks pass; no post-result change to the frozen model/comparison. Proposed learning is for PI integration after rereading current shared LEARNINGS. The earlier HABITS task remains complete/collected and was not resumed.

Completion: 2026-10-29 21:05:58 UTC; elapsed 788 seconds from recorded start, below25minutes. Final manual allowance remains68%; no credits/reset. PI collects disk/status; no completion-message permission workflow or app message. Stop here. The persistent learning-across-curricula question remains unresolved.

Only this review path is owned. PI owns shared root state/registry/LEARNINGS. Return durable REVIEW, STATE, audit/ablation code/results, EXPOSURE and proposed specific learning; stop after return. No cross-chat completion message is required.
