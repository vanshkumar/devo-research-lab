# Reproduce the BCI source check

The allocation closed at its source/design gate. It produced a measured decoder/unit reconstruction for one public session; no adaptation forecast or biological hypothesis test was performed. Read RESULT.md first.

From the repository root, using the existing Python 3.9.6 environment and NumPy 2.0.2/SciPy 1.13.1 packages:

```sh
python3 /Users/vanshkumar/Documents/repos/devo-research-lab/lab/tasks/bci-repertoire-forecast-2026-11-01/first_data_check.py
```

This command is offline, uses the pinned cached example, requests one numerical thread, and overwrites only the generated FIRST_DATA_CHECK, FIRST_DATA_CHECK_SUMMARY and MATRIX_VALIDATION outputs. It does not load afterLearning into returned arrays. Output timestamps and measured RSS may differ; there is no random seed or model fitting. Assertions verify source decoder consistency and the derived progress roundtrip bound. The saved initial version intentionally retains the incorrect direct progress-unit comparison; use the command above for the resolved check.

```sh
python3 /Users/vanshkumar/Documents/repos/devo-research-lab/lab/tasks/bci-repertoire-forecast-2026-11-01/finalize_sources.py
```

The second command reconstructs eight exact licensed text files from saved connector responses and checks their Git blob hashes. It repeats no measured neural calculation. The MAT pin was checked during acquisition and is checked again by first_data_check.py. SOURCE_MANIFEST.json records nine source pins and 18 saved connector responses. Original code remains in sources/golub_code/ with its BSD license; no downloaded MATLAB code was executed.

The acquisition entry point is inspect_example.py. With the cached file present it performs no network operation and preserves the original acquisition ledger. If the file is missing it attempts exactly one pinned HTTPS download capped at 1,000,000 bytes; this session's first sandbox DNS failure is retained separately. Do not reacquire for ordinary reproduction. The script adds the repository's existing Python 3.9 package directory; requirements.txt states package versions for a separately prepared compatible environment.

The original fixed allocation was START 04:39:18.157 UTC, source gate 04:59:18.157 UTC, deadline 06:09:18.157 UTC on November 1, 2026. Source failure closed it early. Running a new empirical study, acquiring another family, or treating the example as independent validation is outside these reproduction commands and this closed allocation.

FIRST_DATA_CHECK_INITIAL.json, first_data_check_initial.py and SOURCE_CHECK_HISTORY.md preserve the units mistake, failed tighter factor-progress tolerance and environment matrix warnings. MATRIX_VALIDATION.json shows finite inputs/outputs and matmul/einsum agreement; successful decoder checks are separate from the failed study gate. RESOURCES.json records manual operation charges, unknown provider quantities and raw/summary exposure. PROPOSED_LEARNING.md is for PI integration into shared memory.
