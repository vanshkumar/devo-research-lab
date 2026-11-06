# Source and provenance index — Byrnes to-do campaign

Inspected2026-10-28. Detailed source locations, scopes, hashes and access failures live with each investigation. Public sources only. No author contact, controlled human data, paid APIs, accounts or private uploads.

## Campaign questions

- [Byrnes, Excerpts from my neuroscience to-do list](https://www.lesswrong.com/posts/c6Job6zmT3nABBxK6/excerpts-from-my-neuroscience-to-do-list), original2025, current revised page inspected. We used the active sensory-grounding, hypothalamus, social-circuit and sandbox questions. The heritability item was marked resolved and the colliculus item withdrawn in the retrieved version, so neither was treated as a new open target. The post is an agenda, not evidence for a mechanism.
- [Byrnes, Neuroscience of human social instincts: a sketch](https://www.lesswrong.com/posts/kYvbHCDeMTCTE9TAj/neuroscience-of-human-social-instincts-a-sketch), Oct2026 revision, §§3.2–4 checked before constructing C1. Shared representations and context-dependent learning suppression materially constrain a fair test.
- [Byrnes, I'm confused about innate smell neuroanatomy](https://www.lesswrong.com/posts/ZahzaAXsBatrWNZzE/i-m-confused-about-innate-smell-neuroanatomy), updated discussion inspected as a pointer to Bader and Russo; not sole anatomical evidence.

## Primary evidence actually used

| Investigation | Primary evidence | Exact local provenance and limits |
|---|---|---|
| Atlas | [Tadross et al., Nature2025](https://doi.org/10.1038/s41586-024-08504-8), author HYPOMAP tables at commit29599fcb13a74a908c986ad69d68fc3e4a3cf6d0 | [Atlas sources](experiments/atlas/SOURCES.md); marker export and matching code inspected, raw-cell integration not rerun; repository/final-paper scope mismatch retained |
| Naive visual bias | [Freeland et al., Learning & Behavior](https://doi.org/10.3758/s13420-024-00638-z), four publisher tables | [Imprinting sources](experiments/imprinting/SOURCES.md); full relevant methods/results and untouched tables; nonapproachers missing from supplied tables |
| Learned generalization | [Wang et al., iScience2024](https://doi.org/10.1016/j.isci.2024.110195), [Zenodo10869154](https://zenodo.org/records/10869154) | Same source ledger; open full-text XML and model equations inspected, downloaded Exp1/Exp4/code; short red/yellow archive missing as retrieved |
| Song development | [Kasdin, Duffy et al., Nature2025](https://doi.org/10.1038/s41586-025-08729-1), corrected2026 figure source data | [Song sources](experiments/song_learning/SOURCES.md); corrected tables and manuscript distinguished; raw per-rendition/bird linkage absent from analyzed aggregates |
| Bulb tracing | [Allen unionize definitions](https://alleninstitute.github.io/AllenSDK/unionizes.html), public API; [Bader2012](https://doi.org/10.3389/fncir.2012.00084) | [Olfaction sources](experiments/olfaction/SOURCES.md); source-selected experiments, no volume images or synapse data; Russo2018 abstract only |
| Concept-finder constraint | Source-faithful hypothetical gate; original exact and simulated calculations | [C1 sources](experiments/concept_finder/SOURCES.md); no biological parameter estimates |
| Sandbox | [AI Safety Gridworlds](https://arxiv.org/abs/1711.09883); [Goal Misgeneralization](https://proceedings.mlr.press/v162/langosco22a.html) as established prior | [V1 sources](experiments/sandbox/SOURCES.md); abstracts inspected, no replication of trained agents; finite policy family entirely explicit |

Acquisition manifests in data/*/ record original URLs and checksums. INPUTS.json freezes the actual local evidence used by the offline reproduction. Derived source extraction JSONs are regenerated; no original XLSX/CSV/archive is edited. Author code is inspected as evidence rather than run as instructions. Dataset-derived calculations are this campaign's own analyses; established biological findings are credited to the primary studies. No claim of novelty is made.
