# Original plasticity benchmark is executable; joint benefit remains open

**Gate completed. Decision: retain this original small benchmark for a bounded protocol-calibration step; do not launch a main matched-retention campaign yet.** Generic stability–plasticity novelty is closed. The specific functional comparison against strong simple renewal/replay remains unearned, with a concrete protocol in [PROTOCOL.md](PROTOCOL.md).

## Directly earned

The author repository is pinned to commit `3138c5556859e0e2918d40f113b40699b6575cfa` and root tree `803541478812c901d267bd5acd069be20fb824f9`, MIT. All 12 acquired source files match their original Git blob hashes; SHA256 and exact sizes are saved. The original default slowly changing regression task has 20 binary inputs, 15 jointly resampled slow bits per 10,000 examples, 5 fresh fast bits, a fixed 100-LTU target and a 5-ReLU learner. Each context therefore has 32 equiprobable input points, allowing exact old-function scoring without modifying training.

The available system Python has no torch/numpy/tqdm. A transparent standard-library implementation preserves these task equations, original Kaiming distributions, strict target threshold and SGD/MSE update. It uses Python float64/RNG, so this is an independently implemented original-task calculation, **not original author-code execution or exact Torch/seed/float32 replay**.

| Saved run | Learned updates / tasks | Total time | Peak RSS | Independent numerical references |
|---|---:|---:|---:|---|
| [First calculation](FEASIBILITY.json) | 30,000 / 3 | 0.453741333s | 16,613,376 bytes | 128 exact teacher checks; seven 111-parameter finite-difference and scalar SGD checkpoints |
| [Original-scale feasibility](FULL_FEASIBILITY.json) | 1,000,000 / 100 | 12.292169958s | 64,913,408 bytes | 3,232 exact teacher checks; eight 111-parameter finite-difference and scalar SGD checkpoints |

Full-run learning/reference time is 11.399321125s; maximum scaled gradient error is below 3.65e-10, and the separately expressed scalar update agrees within 4.34e-19. Both native learning commands exited 0; full session 50923 ended with exit 0. [Saved-output audit](RESOURCES.json) also exits 0 without rerunning learning. ONE pre-main revision extended the short calculation to the original 1,000,000-update scale; [the amendment](AMENDMENT_1.md) preserves why, scope and both original artifacts.

The old first-context function is measurably learned: in the full run its whole-support MSE falls from 2.013488071 to 0.785890672 after task 0. After task 99 it is 2.414574067, while the current task has 0.490638077 MSE. This is one consumed synthetic SGD stream's diagnostic, not a new forgetting result, matched-retention comparison or plasticity-loss reproduction. Different contexts have different intrinsic difficulty. The short/full streams use the same teacher and are not independent replications. CBP, rehearsal, random renewal, shrink/perturb, bounded cache and all-old-context retention scoring are UNRUN.

## Prior/contribution scope

[Dohare et al., Nature 2024](https://pmc.ncbi.nlm.nih.gov/articles/PMC11338828/) explicitly distinguishes loss of plasticity from forgetting; a retention guarantee must not be attributed to that paper. Its linked repository provides the small source benchmark. [Wang et al., arXiv:2503.20018v1](https://arxiv.org/html/2503.20018v1) uses replay as transformer context, not ordinary sampled rehearsal, and does not compare earlier anti-plasticity methods. [FIRE, arXiv:2602.08040v1](https://arxiv.org/html/2602.08040v1) explicitly studies the tradeoff with past-data access and a weight-distance stability objective. These are close prior, not proof of novelty for the present comparison.

The CVPR2024 collaborative-learning paper's search summary explicitly concerns acquisition and forgetting, but both primary HTML/PDF attempts returned 403. Its precise contribution is still unverified. [PRIOR_GATE.md](PRIOR_GATE.md) and [the operation ledger](PUBLIC_OPERATIONS.json) retain this limitation, all failures and incidental summary exposure. No exhaustive-priority/absence claim or automatic continuation of the blocked source chain is earned.

## What the next investment must buy

Use actual old-task target error on the unchanged original 32-point supports, with initial competence and retention age visible. Test attained new-acquisition/old-risk points against equally informed and resourced rehearsal, random renewal, shrink/perturb and a bounded exact cache. The finite repeated input support makes that cache a serious alternative. An ever-growing oracle table is not a fair lifelong-memory control.

Before a main campaign the PI needs a certified precise prior residual, the pinned CBP experiment configuration/remaining import dependency, independent renewal/utility checks and ONE measured full stream with actual replay/full old-risk scoring. The present 12.29s SGD timing cannot price that entire experiment. Settings, margins, independent stream count, selection and uncertainty must be frozen before new evaluation. Distinct fresh independent challenge is required for any consequential claim. No main campaign, empirical target release or native scientific-goal completion is earned by this gate.

## Resources and exposure

Elapsed through the saved audit: 1,062.36s including orientation, before all three scientific gates. Conservative public count 30/30 includes 29 delivered query/open/file attempts and one pre-tool denied archive request; exactly THREE deliberately screened families. Ingress charge is a 58MB provider allowance including 32,677 exact source bytes; actual provider/redirect/failure ingress is UNCERTIFIED. Additional read/hash/decode has a separate 100MB conservative charge against the 1GB cap; the audit explicitly reads/hashes/decodes 9,005,468 bytes, with context/import/earlier passes included in the allowance. Runtime/toolhost/provider peaks and physical I/O are unknown. The measured maximum scientific RSS is 64,913,408 bytes under the 1GB cap; one process/thread at a time. Dependencies installed 0; archive, public empirical/model payload and protected old raw/fits/target rescoring all 0.

All generated teacher parameters, all slow contexts, 1,050,000 fast indices including unused final blocks, full 4×32 and 101×32 label tables and saved model/boundary predictions are exposed. Total learned updates 1,030,000. Unused generated blocks are not pristine holdouts. The full realization has 101 distinct slow contexts. No observational status or source count resets. [RESOURCES.json](RESOURCES.json) preserves denials, arithmetic/runtime differences and unknowns. [Proposed memory](PROPOSED_LEARNING.md) is for PI integration; shared LEARNINGS was not edited.

Jobs 0 after completed native commands. The single terminal report was DELIVERED successfully to current registry PI `01a19efc-5590-73d2-910e-6920a3a81eaf` without model/thinking overrides; native response returned the same threadId/isError=false. [Terminal report](TERMINAL_REPORT.md) records the disposition. No resend or acknowledgement wait. The existing operator heartbeat and unfinished native scientific goal remain the PI/operator's responsibility.
