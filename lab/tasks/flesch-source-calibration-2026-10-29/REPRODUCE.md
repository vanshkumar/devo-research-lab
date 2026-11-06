# Offline reproduction

Use repo root and the existing environment; no dependency was installed:

```sh
PY=campaigns/learning_rule_transport_2026-10-28/.modelenv/bin/python
export NUMBA_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1
$PY sources/flesch_source_calibration_2026-10-29/final_checks.py
$PY sources/flesch_source_calibration_2026-10-29/check_numerics.py
$PY sources/flesch_source_calibration_2026-10-29/source_stability.py
$PY lab/reviews/flesch-source-calibration-2026-10-29/exact_source_check.py
```

The checks use the saved masked source/input NPZ. final_checks also verifies the11pre-response pins and reconstructs safe failure offsets without response conversion. source_stability replays fixedparameters and the same256drawprefix; it does not fit or open targets. It overwrites only its own replay outputs; preserve the original files when conducting a fresh audit. Independent review code/output is owned by the reviewer; run it only as a separately named/archived replay when preserving its original audit matters.

Do **not** rerun acquire/extract/input scripts or fitting merely to reproduce this completed result. They are preserved provenance, not pending work. Original first/second fit traces and parameters are durable; the allowed starts have been used. Exact primary fit objective replay matches within7.3e−12. Old SOURCE_STABILITY_V1.json preserves the pre-repair9-node network numerical failure.

Optional plot_source.py requires matplotlib, which is absent from this environment; no dependency was installed and no figure is part of the required result. Numerical curve tables in SOURCE_STABILITY.json and independent exact_source_results.json are the delivered figure-equivalent evidence.
