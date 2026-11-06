# Saved count–accuracy audit

RNN's count-pooled cohort MAE is1.052554pp versus growth2.269678pp. Its joint opportunity/success energy score improves3.62% at the point estimate, but animal/lab intervals include zero. A count-only reference also slightly favors RNN. Distinct independent review is pending. See [RESULT.md](RESULT.md) for the interpretation and limits.

## Inspect

- [FIRST_CALCULATION.json](FIRST_CALCULATION.json): actual command/stdout,53input pins, independent reproduction, paired integers and initial resources.
- [DESIGN.md](DESIGN.md), [RESOURCE_PLAN.json](RESOURCE_PLAN.json), [FROZEN_PLAN.json](FROZEN_PLAN.json): prescore functional, one reference, uncertainty, fixed limits, code/design/asset pins and13:11:52Zfreeze.
- [ENDPOINTS.npz](ENDPOINTS.npz): original paired successes/opportunities/ratios and observed targets for2methods×24animals×512particles×6bins×2sides.
- [COMPARISON_OBJECTS.npz](COMPARISON_OBJECTS.npz): complete prescore category vectors and corresponding integer pairs. Method axis0=RNN/1=growth; side axis0=negative100/1=positive100. Category axis=correct exact-side, incorrect exact-side, other opportunities. No cross-method resampling or unpaired joint-path reconstruction.
- [RESULT.json](RESULT.json), [SCORES.npz](SCORES.npz), [MAIN.stdout](MAIN.stdout): scores, terms, original/count-pooled accuracy, biological/laboratory/numerical diagnostics, per-cell values, particle pseudovalues and fixed blocks.
- [FINAL_AUDIT.json](FINAL_AUDIT.json): independent within-author scalar/SciPy/sorted-CRPS/uncertainty/limit/pin checks. This is not an independent reviewer verdict.
- [RESOURCES.json](RESOURCES.json), [ENVIRONMENT.json](ENVIRONMENT.json), [SOURCE_MANIFEST.md](SOURCE_MANIFEST.md), [STATE.md](STATE.md): reproducibility, provenance and terminal handoff.

## Exact native commands used

From repository root, each command was run separately, with no concurrent scientific process. Existing Python3.12.14/NumPy2.3.5/SciPy1.18.1 were reused; no dependencies were installed. Numerical thread variables are part of each native command.

```sh
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1 NUMEXPR_NUM_THREADS=1 PYTHONDONTWRITEBYTECODE=1 campaigns/learning_rule_transport_2026-10-28/.modelenv/bin/python lab/tasks/learning-forecast-count-joint-audit-2026-11-01/first_calculation.py
```

```sh
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1 NUMEXPR_NUM_THREADS=1 PYTHONDONTWRITEBYTECODE=1 campaigns/learning_rule_transport_2026-10-28/.modelenv/bin/python lab/tasks/learning-forecast-count-joint-audit-2026-11-01/freeze.py
```

```sh
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1 NUMEXPR_NUM_THREADS=1 PYTHONDONTWRITEBYTECODE=1 campaigns/learning_rule_transport_2026-10-28/.modelenv/bin/python lab/tasks/learning-forecast-count-joint-audit-2026-11-01/compare.py
```

```sh
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1 NUMEXPR_NUM_THREADS=1 PYTHONDONTWRITEBYTECODE=1 campaigns/learning_rule_transport_2026-10-28/.modelenv/bin/python lab/tasks/learning-forecast-count-joint-audit-2026-11-01/final_audit.py
```

Original date guards remain in frozen execution code. For later reproduction, use the saved paired objects and the untimed scalar/reference equations in final_audit.py within a newly authorized review's own scope. The completed allocation is not a future run authorization. No raw reread or learner trajectory regeneration is necessary. Saved source pins and ordering evidence are consistent with the documented freeze; they are not independent proof of historical nonaccess.

[PROPOSED_LEARNING.md](PROPOSED_LEARNING.md) is for PI integration; shared LEARNINGS and registry were not edited here. All historical gates/protected observations/failures remain unchanged. The lab heartbeat remains active across this endpoint.
