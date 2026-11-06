# Sources and dependency pins

No network, download or acquisition occurred in this review. Exact local ingress SHA256/size records are in INPUT_PINS.json. Existing source assets and author/frozen files were read only.

Primary publication: Upadhyay, Lancashire, Moser and Gomez-Rodriguez(2021), *Large-scale randomized experiment reveals machine learning helps people learn and remember more effectively*, [DOI](https://doi.org/10.1038/s41539-021-00105-8), PMCIDPMC8421401. Scheduler and HLR/POWER comparisons predate this review. Literature/provenance scope is inherited from the existing source-only audit; no new literature search or novelty certification was conducted.

Original public code: [Human-Centric-Machine-Learning/spaced-selection](https://github.com/Human-Centric-Machine-Learning/spaced-selection), commitfb197043c287a3d4f76787a19c023b964e823c7d, notebook blob4a578ef357d45908c8717204ef78ed212adff7db. Code was not executed in this review.

Original archive: [public endpoint](https://owncloud.mpi-sws.org/index.php/s/Pgn3Q9N592Z8MgZ/download). Prior receipt572,563,931bytes, SHA256b582da91b05e16dbda0fb14b52118e41b6f0f566a457c8991a0fa2859179c6af. No raw archive pass or redistribution. Archive-specific redistribution license remains unestablished in the saved provenance.

Actual cached scientific inputs:

| Local asset | SHA256 | Review use |
|---|---|---|
| `sources/memory_policy_transfer_2026-10-30/metadata_sorted.npy` | b6ece5e1c7525e0027679b545ab07167772f559adf9cc74c44f405c8f689d9fe | Seven-field projection only |
| `sources/memory_policy_transfer_2026-10-30/opaque_answers/arm_02.tsv.gz` | 77aa272fb8eaf6f8f253002aa417025e53603bd86415eb2830e91b0c394c9f13 | Random-arm focal correct allowlist only |
| `lab/reviews/memory-readiness-2026-10-30/CANDIDATE_READINESS.json` | 33411d594c09d7615a96e71aa4a4255d34c4d299ab3aa25907e12e35f8b23323 | Inherited one-candidate membership/folds |
| `lab/tasks/memory-source-calibration-2026-10-31/source_answers_consumed.npz` | e08913aafe5c3a28a97a5e286295536c05bba7837241cacd28214ef9f07cbbac | Consumed source values for exact frozen replay; target NaNs verified |

Candidate definition/comparison, author protocol/fit/schedules, initial/fitted freezes and exact hashes are in FROZEN_AUDIT.json/INPUT_PINS.json. Upstream prior acquisition/access/exposure remains authoritative; a new review context resets none of it.

Numerical dependencies: Python3.9.6, NumPy2.0.2, SciPy1.13.1; requirements.txt records installed versions. Own algorithm uses independent block-Newton logistic fitting with explicit contractions, full sparse Hessian reference assembly and SciPy positive-definite solves. No author estimator import.
