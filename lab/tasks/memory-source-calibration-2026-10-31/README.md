# Memory source calibration — stopped at its frozen calibration gate

Read [RESULT.md](RESULT.md) first. Added recorded practice gives a small, imprecise source-validation gain; the10-IDprimary sample does not certify the declared absolute calibration tolerance. Park the fixed candidate. No target answers/predictions/scoring or known-answer recovery were run.

- [PROTOCOL.md](PROTOCOL.md): exact equations, finite grid, gates, uncertainty, intended/unrun recovery and resource limits.
- [calibrate.py](calibrate.py): masked metadata/source reader, history construction, finite source fits, source-validation assessment.
- [SYNTHETIC_CHECKS.json](SYNTHETIC_CHECKS.json), [METADATA_CHECK.json](METADATA_CHECK.json): actual chronology/masking checks and exact frozen-population reconstruction.
- [SOURCE_FIT.json](SOURCE_FIT.json), [SOURCE_VALIDATION.json](SOURCE_VALIDATION.json): actual fit, once-only assessment, all uncertainty and declared diagnostics.
- [numeric_audit.py](numeric_audit.py), [NUMERIC_AUDIT.json](NUMERIC_AUDIT.json): explicit-contraction/finite-difference audit of observed matrix-product warnings.
- [INITIAL_FREEZE.json](INITIAL_FREEZE.json), [FIT_FREEZE.json](FIT_FREEZE.json), [FINAL_CHECKS.json](FINAL_CHECKS.json): original and verified final pins; no frozen bytes changed.
- [source_data_manifest.json](source_data_manifest.json), [EXPOSURE.json](EXPOSURE.json), [ACCOUNTING.json](ACCOUNTING.json): provenance, permissions/exposure, conservative read charges.

Original successful commands from repository root `/Users/vanshkumar/Documents/repos/devo-research-lab`, sequentially, with one scientific process at a time:

```sh
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python lab/tasks/memory-source-calibration-2026-10-31/calibrate.py checks
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python lab/tasks/memory-source-calibration-2026-10-31/calibrate.py fit
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python lab/tasks/memory-source-calibration-2026-10-31/numeric_audit.py
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python lab/tasks/memory-source-calibration-2026-10-31/calibrate.py validation
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python lab/tasks/memory-source-calibration-2026-10-31/closeout_integrity.py
```

The last command only audits saved pins/exposure/accounting and does not interpret a response array, refit or rescore. It includes a one-time retrospective NPZ-inflation charge correction; do not rerun it against this ledger. A shell-redirection attempt was denied before execution; the plain validation command above succeeded once and its captured output is [validation.command-output.txt](validation.command-output.txt). No permission/guard/configuration was changed.

Python3.9.6, NumPy2.0.2, SciPy1.13.1 were already installed. `requirements.txt` lists their numerical dependencies; no installs/network were needed. Numerical libraries are set to one thread. Inner folds use frozen learner-hash digits16:24mod3; fitting is deterministic. Seeds and exact budgets for the unrun recovery are in PROTOCOL, not earned outputs.

`safe_schedules.npz` contains allowed focal metadata for all candidate groups. `fit_answers.npz` contains consumed source-fit answers; `source_answers_consumed.npz` additionally contains consumed validation answers. Actual target entries are NaN. These files remain local source-analysis artifacts; they do not authorize target access or a new holdout. The code reconstructs source features from preceding answers and fixes the item bank from fit metadata. The original scripts retain their actual deadline and once-only guards; a future independently scoped reviewer must honor the existing access/exposure constraints. This README is a reproduction record, not automatic permission to rerun expired work or delete guards.

Scientific stop: preserve the failed gate and all consumed IDs. PI may audit/collect this failure and reallocate; the lab heartbeat continues under its existing authorization. No worker successor or background job was launched.
