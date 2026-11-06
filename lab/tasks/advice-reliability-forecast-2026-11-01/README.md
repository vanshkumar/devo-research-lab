# Adviser-reliability forecast

[RESULT](RESULT.md) is the entry point. P gains0.36%over strong histories and fails5%. Numerical results are saved, distinct review is pending, and read-cap compliance is **uncertified** (330MBconservative allowance/300MBcap). Further author science is stopped.

Key artifacts: [protocol](PROTOCOL.md), [one amendment](AMENDMENT_1.md), [source manifest](SOURCES.json), [resources](RESOURCES.json), [scores](SCORES.json), [source perturbations](SOURCE_UNCERTAINTY.json), [conditional controls](CONTROLS.json), [within-author audit](FINAL_AUDIT.json), [state](STATE.md).

Original dataset_exp1.xlsx:4,537,480bytes,SHA256cbd91790cb21a6a1c1abda7043dfe96bc9a01d0be2ed51c572a523466d937aa9,https://osf.io/download/jx3fu/. The guide/API listings are preserved. Correct derivative original_typed_rows.json retains nulls, pinned in TYPED_MEASUREMENT_AUDIT.json. source.npz contains source X/y; evaluation_features.npz/evaluation_predictions.npz precede evaluation_scored.npz. Keys id/trial/block/gap align rows; SOURCE_FITS.json names43Xcolumns. B/H/P use first13/42/43columns. Primary trial>=19and finite-observation mask leaves6048source/5794evaluation rows,24/23people. All47people remain included; unavailable current forecasts remain NaN.

Dependencies used: project .venv Python3.9.6/NumPy2.0.2, standard-library ZIP/XML/JSON. Thread environment is1before NumPy import. App-bundled Python/pypdf only extracted the guide. pdftotext/project pypdf were unavailable; external skill reads were hook-blocked. Failures are retained. No downloaded code executed.

Historical commands from repository root:

```sh
python3 lab/tasks/advice-reliability-forecast-2026-11-01/first_data_check.py
python3 lab/tasks/advice-reliability-forecast-2026-11-01/design_gate.py
.venv/bin/python lab/tasks/advice-reliability-forecast-2026-11-01/validate_pipeline.py
.venv/bin/python lab/tasks/advice-reliability-forecast-2026-11-01/analysis.py freeze
.venv/bin/python lab/tasks/advice-reliability-forecast-2026-11-01/analysis.py source
.venv/bin/python lab/tasks/advice-reliability-forecast-2026-11-01/analysis.py predict
```

The last command documents the failed numeric-only reader, with no saved predictions/scores. Original code/freeze remain intact. After the ONEprescoring typed-cell/missingness amendment:

```sh
.venv/bin/python lab/tasks/advice-reliability-forecast-2026-11-01/cache_typed_original.py
.venv/bin/python lab/tasks/advice-reliability-forecast-2026-11-01/validate_typed_source.py
.venv/bin/python lab/tasks/advice-reliability-forecast-2026-11-01/analysis_v2.py freeze
.venv/bin/python lab/tasks/advice-reliability-forecast-2026-11-01/analysis_v2.py finish
.venv/bin/python lab/tasks/advice-reliability-forecast-2026-11-01/final_audit.py
```

finish saves prediction→score→100source perturbations→200controls sequentially in one process with RAM reuse. config.json contains seeds/penalties/criteria. final_audit.py separately reconstructs groupedCV with augmented least squares, primary scores/intervals and two full control examples; it is not independent review/raw-XLSX replay.

These command lists document reproduction, **not permission to resume the stopped worker**. Preserve the bundle before a new authorized reproduction. analysis.py/analysis_v2.py enforce the original12:13Zdeadline; do not change frozen clocks to extend this allocation. A fresh separately bounded reviewer can independently rebuild the raw data or use saved functions. final_audit.py is the runnable cache audit and rewrites FINAL_AUDIT.json, so preserve the original.

INVALID historical interpretations: MEASUREMENT_AUDIT.json, THRESHOLD_FIRST_MISMATCH.json, audited_original_rows.json and audit_measurements.py's numeric-only reader confused shared-string indices with measurements. TYPED_MEASUREMENT_AUDIT.json supersedes their interpretation; failures/bytes/exposure survive. No source corruption was established.

Distinct review, calibrated boundary power/coverage, unique latent mechanism, external-file licensing and complete practice/acquisition chronology remain uncertified or UNRUN.
