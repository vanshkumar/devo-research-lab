# Independent memory source-calibration review

Read [REVIEW.md](REVIEW.md). The frozen primary calculation is independently reproduced; preserve the failed calibration gate and park this fixed candidate. A predeclared precision/influence diagnostic shows that both nominal bias half-widths exceed.10even at zero point bias, and all ten single-ID deletions retain joint failure. Targets remain sealed. Coverage and transport are untested.

- [METADATA_RECONSTRUCTION.json](METADATA_RECONSTRUCTION.json): independently reconstructed14schedule arrays and all four primary population counts.
- [EARLY_NUMERICAL.json](EARLY_NUMERICAL.json): early independent numerical execution evidence.
- [PREDICTION_RECONSTRUCTION.json](PREDICTION_RECONSTRUCTION.json): independent block-Newton source fits, all54inner fits, selection, losses and coupled source covariance.
- [FROZEN_AUDIT.json](FROZEN_AUDIT.json): exact frozen-coefficient replay, ten actual-history checks, independent sparse/dense/Schur reference numerics and ten pins/chronology checks.
- [DIAGNOSTIC_PLAN.md](DIAGNOSTIC_PLAN.md), [PRECISION_INFLUENCE.json](PRECISION_INFLUENCE.json): predeclared contrary test, every ID deletion and limitations.
- [COMPACT_RESULTS.json](COMPACT_RESULTS.json): concise independently optimized summaries; exact frozen results are separately in FROZEN_AUDIT.
- [INPUT_PINS.json](INPUT_PINS.json), [SOURCES.md](SOURCES.md), [ACCOUNTING.json](ACCOUNTING.json), [EXPOSURE.json](EXPOSURE.json): provenance, ingress/decoding charges and inherited exposure.
- [REVIEWER_FAILURES.md](REVIEWER_FAILURES.md): preserved unseen-item correction and denied inline inspection.
- [STATE.md](STATE.md), [PROPOSED_LEARNING.md](PROPOSED_LEARNING.md): closeout and scoped memory proposal for PI integration.

Successful commands, from `/Users/vanshkumar/Documents/repos/devo-research-lab`:

```sh
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python lab/reviews/memory-source-calibration-2026-10-31/independent_review.py metadata
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python lab/reviews/memory-source-calibration-2026-10-31/independent_review.py science
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python lab/reviews/memory-source-calibration-2026-10-31/independent_review.py audit
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python lab/reviews/memory-source-calibration-2026-10-31/independent_review.py summary
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python lab/reviews/memory-source-calibration-2026-10-31/independent_review.py finalize
```

The science command also ran once before the correction described in REVIEWER_FAILURES; its read charges are retained. The script is independent of `calibrate.py`; original author code was read/pinned but not imported or executed. Python3.9.6, NumPy2.0.2, SciPy1.13.1 were preinstalled; no installation/network. The calculation is deterministic; there is no simulation seed because no stochastic recovery was run. Thread environment variables are set to1before numerical imports.

The metadata stage reads the full pinned67,265,856-byte NPY once and projects only seven authorized fields. `independent_schedules.npz` contains metadata only, including sealed-target mask metadata. The science stage decodes only the consumed source focal correct values from random shard2. The audit uses the permitted source-derived answer array and verifies target entries are NaN. No target predictor/score path is used.

These are reproduction records, not permission for an additional pass. Stage guards, exact deadline, existing read ledger and150MBreview/8GBinherited caps remain in place. Do not delete guards/reset ledgers to replay expired work. Any separately authorized future reproduction must preserve consumed observations and arrange a new bounded allocation through the PI. `summary`/`finalize` read only own saved outputs. Finalization hashes owned artifacts without reopening original scientific inputs.
