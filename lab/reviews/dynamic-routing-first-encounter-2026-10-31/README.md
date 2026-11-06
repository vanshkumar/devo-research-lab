# Offline independent dynamic-routing review

The exported response channels disagree at three rows, independently reproduced from cached compressed columns. None is a selected first encounter; two hypothetical input differences affect only later global response traces. The frozen evaluation gate still prevents all real-data scoring. See [REVIEW.md](REVIEW.md) for the conclusion and its limits.

From the repository root, run these **sequentially**:

```sh
.venv/bin/python lab/reviews/dynamic-routing-first-encounter-2026-10-31/independent.py first
.venv/bin/python lab/reviews/dynamic-routing-first-encounter-2026-10-31/independent.py audit
.venv/bin/python lab/reviews/dynamic-routing-first-encounter-2026-10-31/independent.py support
```

All three were executed successfully. They write only this review directory, perform no network access and never compute real evaluation losses. Execution of a closed assignment requires its existing authorization; these commands document reproduction and do not authorize a restart or new grant. Author files remain immutable; do not run their stage/replay scripts as an independent reconstruction.

Dependencies are the existing repository Python 3.9.6/NumPy 2.0.2 environment and the cached pinned Numcodecs 0.12.1 CPython 3.9 macOS ARM64 wheel. The script verifies its SHA256 against the saved package pin and extracts only to review-local `deps/`; `support` also checks the cached PyPI reference. No shared install was made. The wheel is platform specific; another platform needs a separately authorized compatible environment. Numerical and codec threads are set to one.

- `FIRST_CALCULATION.json`: 2,132-row independent raw-column reconstruction; review-local decoded NPZs preserve this product.
- `CONTRARY_PLAN.md` / `CONTRARY.json`: predeclared source-row/window/controller and first-encounter-history test.
- `PINS_AND_FREEZE.json`: exact source URLs/hashes, stable artifacts, 12 frozen hashes and timing/guard verification.
- `SOURCE_SUPPORT.json`: source units, descriptions, licenses, trusted-codec and Git blob checks.
- `FORECAST_RECONSTRUCTION.json`: 12,752 probability checks and past-only/privileged-label invariance.
- `CONTROL_RECONSTRUCTION.json` / `GENERATOR_SUPPORT.json`: all saved synthetic arithmetic and independently regenerated truths/outcomes.
- `FIRST_RESOURCES.json`, `AUDIT_RESOURCES.json`, `SUPPORT_RESOURCES.json`: measured process peaks and scoped read/decode/hash lists; final `RESOURCES.json` adds conservative manual charges.
- `EXPOSURE.json`, `UNRUN_CHECKS.md`, `STATE.md`, `PROPOSED_LEARNING.md`: consumed status, limitations and PI handoff.
- `REVIEW_PINS.json`: terminal hashes of this review's source, reports and independent products; mutable delivery status is excluded.

Primary, secondary, ablation, stratum and uncertainty evaluation scores remain **uncomputed**. Conditional controls are synthetic and do not establish a known 0.05-nat effect or calibrated biological inference.
