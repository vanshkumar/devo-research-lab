# Cross-species history: provisional baseline-dependent transfer penalty

Start with [RESULT.md](RESULT.md). Human-fixed side-history coefficients penalize mouse prediction by .01065nat/choice under a response-history baseline and .000080 after adding physical-stimulus history. This is conditional consumed-data evidence, not a biological equivalence/difference result. **The control batch exceeded the1GB memory cap; science stopped, author audit is unrun and independent review is pending.**

## Inspect without rerunning

- [PLAN](PLAN.md), [original freeze](FREEZE.json), [numerical amendment](NUMERICAL_AMENDMENT.json), [logging](LOGGING_AMENDMENT.md) and [control-summary amendment](CONTROLS_AMENDMENT.md).
- [Allowed source/ID/row manifest](ALLOWED_MANIFEST.json), [authority audit](AUTHORITY_AUDIT.json), [sample](FIRST_SUPPORT.json), [full support/chronology](SUPPORT.json), [input support](INPUT_SUPPORT.json).
- [All predictive summaries](corrected/SUMMARY.json), [B unit scores](corrected/unit_scores_B.csv), [S unit scores](corrected/unit_scores_S.csv), [row map](corrected/scoring_rows.csv), [predictions](corrected/predictions.npz), [fit records](corrected/FITS.json), [actual-input identity/witness](corrected/DIAGNOSTICS.json).
- [Controls](corrected/CONTROLS.json), [control fit records](corrected/CONTROL_FITS.json), [actual peak RSS](corrected/CONTROL_RUN.json), [conservative resources](RESOURCES.json), [sources](SOURCES.md).

## Exact historical commands and future reproduction

Executed from `/Users/vanshkumar/Documents/repos/devo-research-lab`, in order: `certify.py`; `build_inputs.py --sample` (one failed omission-NaN assertion then corrected sample); `build_inputs.py`; `input_support.py`; `freeze.py`; `analysis.py` (stopped on known matrix warnings); `prepare_correction.py`; `analysis_explicit.py` (all science saved, logger path failure); `analysis_explicit.py --controls` (summary guard failure); `resource_snapshot.py`; corrected `analysis_explicit.py --controls` (completed, then memory cap stop). Each Python command used `.venv/bin/python lab/tasks/cross-species-history-2026-10-31/<file>`.

Do **not** run more science under this closed allocation. For a separately authorized reproduction, preserve `corrected/` and the original freeze/amendments first. Existing caches are sufficient; no network or protected evidence is needed. Main numerical command:

```sh
.venv/bin/python lab/tasks/cross-species-history-2026-10-31/analysis_explicit.py
```

This writes `corrected/` deterministically. It uses the frozen data/feature/fold/objective/seed specification plus documented numerical and bookkeeping fixes. Do not rerun `freeze.py` or overwrite historical freeze bytes. `certify.py` regenerates timestamped metadata and is an acquisition audit, not necessary for a score replay; preserve its original output pins. `prepare_correction.py` intentionally refuses to overwrite an existing revised file.

The control command is the same with `--controls`, but **its observed peak is1.129GB and violates this task's cap**. Its existing outputs should be reused; this README does not authorize a rerun or higher memory. `audit.py` is unexecuted draft audit code, not a passing reproduction. No optional full-mouse-window, independent original-byte or dedicated contrast-stratum audit result exists.

Dependencies are the existing Python3.9.6 `.venv`, NumPy2.0.2, pandas2.3.3 and SciPy1.13.1; no installs. Each script sets numerical thread environment to1 before importing libraries. The original `analysis.py` reproduces the known misleading matmul warnings; use the documented explicit-contraction revision. Saved main input products and objective directional checks passed, but do not replace independent scientific validation.
