The controlled pilot is complete; human-data feasibility remains incomplete. Learned reliability and context filtering remove the supplied noise-location flag after blocked training, but often fail after interleaved starts. This is computational feasibility, not human transport or a first Bayesian curriculum-prediction claim.

The [protocol](FROZEN_PROTOCOL.md) and [code](pilot.py) were frozen before 20 new seeds per family/curriculum condition, with 200 stories each. Three hundred sequences plus exact state permutations produced 1,800 three-role runs. Four development sequences and one inference refinement were used; the failed first attempt remains preserved.

All roles share published Simulation 2 parameters. Final deterministic-transition correct-choice probabilities are:

| Blocked synthetic family | Original | Oracle | Learned |
|---|---:|---:|---:|
| Original task |49.73%|93.13%|98.10%|
| Noise moved later |73.98%|61.46%|98.12%|
| Context-dependent deterministic |82.14%|82.14%|98.15%|

Original-task learned gain is 48.38 pp [48.01, 48.75], a paired-seed Monte Carlo interval. Signal/noise weights are 1/.116; state permutations are exact. Early-return performance remains 97.99%. However, original interleaved performance is 51.14%, and the fully deterministic interleaved last edge is wrongly downweighted to .059. Undiscovered context still masquerades as noise. Persistence and posterior averaging changed alongside reliability, so gains do not isolate the gate.

[Separate audit](AUDIT.json): 25 checks pass; all 1,800 scores reconstruct exactly, reliability agrees within 2.29e-14, causal/evaluator-label tests pass, 12 runs replay exactly, and native source probabilities/assignments match. [Details and reproduction](TECHNICAL_REPORT.md). Simulation: 17.20 s; audit: 39.81 s, 134.2 MB RSS, one process.

[Source availability](../../../sources/noise_context_feasibility_2026-10-29/SOURCE_REPORT.md): live-tree model/util/parameter blobs are pinned exactly; Zenodo 10695055 metadata access failed. Manifests show threshold-0/90 original/replication/mixed files. No header or payload was opened. Recruitment completeness, attention/omission fields and deployment chronology remain uncertified. Eight remote attempts are exhausted.

Recommend one bounded value-blind archive/schema audit before any human fitting. Exact archived identity and complete per-person input/response/attention chronology and inclusion denominators would make a separately reviewed, summary-informed source-to-mixed test designable. No successor is launched.

[Exposure](EXPOSURE.json): zero human-response values; Pan20/Flesch81/HABITS boundaries unchanged. No installs, spend, contact or reset. Telemetry: 70→69% remaining. [Proposed learning](PROPOSED_LEARNING.md) awaits PI integration.
