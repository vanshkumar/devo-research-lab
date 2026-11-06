# Molecular-correspondence pilot

Read [RESULT.md](RESULT.md) for the decision. Published correspondence does not supply a held-gene test:24of54prespecified receptors entered cross-species features. A real five-receptor/three-POMC-group comparison ranks the published pairing third of six and gives3.08%conditional gene-centered improvement over a class/gene mean. This is selected aggregate evidence; independent gene prediction and donor validation remain unrun.

All new files are scoped here. BRIEF.md belongs to PI and is unchanged. Original source/data assets elsewhere are read-only. No additional public request is authorized within this pilot:20charged requests have been used.

## Offline reproduction

From repository root, use the existing Python3.9.6 environment and NumPy2.0.2. No package installation, atlas access or network is required:

```sh
env OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1 .venv/bin/python lab/tasks/molecular-correspondence-2026-10-31/feature_audit.py
env OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1 .venv/bin/python lab/tasks/molecular-correspondence-2026-10-31/compare_tables.py
env OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1 .venv/bin/python lab/tasks/molecular-correspondence-2026-10-31/verify_result.py
```

The analysis is deterministic and enumerates every permutation; no stochastic seed is used. These commands overwrite their generated outputs and add explicit local reread charges. `feature_audit.py` also reads the old118,660-byte mapping table at `campaigns/byrnes_todo_2026-10-28/data/atlas/matched_clusters_scviCorPruned.tsv`. Other expression inputs are the pinned small files in `sources/`.

Acquisition is intentionally separate. `source_audit.py inventory` reproduces the initial small metadata inventory/file-size checks. Connector payloads in CONNECTOR_RECEIPTS*.json preserve exact text, imported byte-for-byte and Git-verified; SOURCE_MANIFEST.json records the tree/source pins. WEB_RECEIPTS.json preserves primary-paper evidence and failed DOI page opens, with conservative provider-byte/request allowances. ACCOUNTING.json contains the complete request ledger including the final capped DataCite metadata response. Do not rerun network acquisition as part of numerical reproduction.

## Artifacts

- [PROTOCOL.md](PROTOCOL.md), frozen SHA25670b50038972587e60173c4ac7d0ede63e51d079be7e6c9a0998dd9b1e68c86b4; [SCHEMA_CLARIFICATION.md](SCHEMA_CLARIFICATION.md) records pre-comparison units, first-mouse-column handling and fixed-target restriction.
- [FEATURE_AUDIT.json](FEATURE_AUDIT.json), exact feature overlap and available common-panel coverage.
- [COMPARISON.json](COMPARISON.json), actual vectors, source identities, baselines, all six permutations and positive/negative controls; [PERMUTATIONS.csv](PERMUTATIONS.csv), compact comparison export.
- [SCALAR_VERIFICATION.json](SCALAR_VERIFICATION.json), second implementation, source/hash/ratio checks, finite loss identities, gene contributions, exposure and deposit metadata.
- [SOURCES.md](SOURCES.md), source scope, processing and licences; [SOURCE_MANIFEST.json](SOURCE_MANIFEST.json), exact pins; [ACCOUNTING.json](ACCOUNTING.json), finite-resource ledger.
- [STATE.md](STATE.md), ownership, completed/unrun work and report delivery; [PROPOSED_LEARNING.md](PROPOSED_LEARNING.md), scoped proposal for PI integration only.

Donor-level uncertainty remains unmeasured: there are no donor columns in these four receptor tables. No biological uncertainty interval, novel conserved mechanism or independent-review certification is implied by successful numerical reproduction.
