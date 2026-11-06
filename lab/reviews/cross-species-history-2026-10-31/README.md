# Cross-species-history independent review

Read [REVIEW.md](REVIEW.md). Independent code reproduces the main predictions, fixed-optimum diagnostics, support and history identity. The predeclared contrast check preserves the narrow baseline-sensitive transfer penalty. The saved S controls do not distinguish the planted shared/different effects at the material incremental-gain threshold; no equivalence or biological mechanism follows.

Inspect actual outputs:

- [FIRST_CALCULATION](FIRST_CALCULATION.json): all per-unit losses/Brier scores and mean comparisons.
- [RECONSTRUCTION](RECONSTRUCTION.json): independent histories, folds, support, all 50 ordinary/nuisance objectives and gradients.
- [CONTRARY](CONTRARY.json) and [contrast table](contrast_strata.csv): all fixed-fit contrast, instruction, schedule and lab results, intervals and aggregate composition.
- [CONTROL_ASSESSMENT](CONTROL_ASSESSMENT.json): saved 18-dataset/540-fit assessment without refitting.
- [SOURCE_SAMPLE](SOURCE_SAMPLE.json): one original-human session and one pinned mouse export; original-Parquet numbers unrun.
- [PINS](PINS.json), [RESOURCES](RESOURCES.json), [execution notes](EXECUTION_NOTES.md): exact source/code/artifact pins and preserved failures/accounting.

Historical commands executed after registered START, sequentially from repository root:

```sh
.venv/bin/python lab/reviews/cross-species-history-2026-10-31/first_scores.py
.venv/bin/python lab/reviews/cross-species-history-2026-10-31/reconstruct.py
.venv/bin/python lab/reviews/cross-species-history-2026-10-31/inspect_sources.py
.venv/bin/python lab/reviews/cross-species-history-2026-10-31/strata.py
.venv/bin/python lab/reviews/cross-species-history-2026-10-31/controls_review.py
.venv/bin/python lab/reviews/cross-species-history-2026-10-31/source_sample.py
.venv/bin/python lab/reviews/cross-species-history-2026-10-31/pins.py
```

These are reproduction instructions for a separately authorized allocation, not permission to rerun this finished review. Failed attempts are in EXECUTION_NOTES; reconstruction succeeded before the external `/usr/bin/time -l` wrapper's denied sysctl call. Use Python directly. Never rerun the author's oversized controls or its draft audit. Current scripts use existing .venv Python3.9.6/NumPy2.0.2/SciPy1.13.1, one numerical thread; no installs/network. Reproducing all successful commands alone reads less than this review's charged total because it excludes failed passes and conservative reserves. The reconstructed fit coefficients are reused; no optimizer is refit.

Original author/source/shared records are readonly. All 80 humans / 122 mice remain consumed development, with only manifest-admitted mouse prefixes. Source-sample code hashes the original full human object but interprets only the admitted first 600-row subject006 session. Original source lineage and licenses remain in author SOURCES and the prior campaigns. Human zero contrast/equal-grating and instruction/task differences are source context, not identified causes.
