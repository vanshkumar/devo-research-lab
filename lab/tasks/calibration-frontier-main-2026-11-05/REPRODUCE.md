# Stage 1 reproduction

Run from repository root. Only original74 source cache/metadata and saved source summaries are used; no evaluation cache, protected objects, archive/network acquisition or shared-record mutation. Repeating this is another charged source read, not a free verification. Stage2 requires separate PI release of MAIN_FREEZE on the same active native goal.

The exact source plan precedes the run. The two completed commands were:

```sh
env PYTHONDONTWRITEBYTECODE=1 OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1 NUMBA_CACHE_DIR=/private/tmp/calibration-frontier-prep-numba campaigns/learning_rule_transport_2026-10-28/.modelenv/bin/python lab/tasks/calibration-frontier-main-2026-11-05/prepare_stage1.py > lab/tasks/calibration-frontier-main-2026-11-05/STAGE1.log 2>&1
```

```sh
env PYTHONDONTWRITEBYTECODE=1 OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1 NUMBA_CACHE_DIR=/private/tmp/calibration-frontier-inspect-numba campaigns/learning_rule_transport_2026-10-28/.modelenv/bin/python lab/tasks/calibration-frontier-main-2026-11-05/check_stage1.py > lab/tasks/calibration-frontier-main-2026-11-05/SOURCE_INSPECTION.log 2>&1
```

Use a fresh temporary Numba cache when reproducing. Python modules are imported as definitions only; no inherited main/reader/save function is invoked that writes old task artifacts. All numerical writes go to this owned directory. The campaign Python3.12 environment supplies the required NumPy/SciPy/Numba without package installation; bytecode and compilation caches go only to the stated permitted temporary location.

PREP_ACCESS and input pins precede source cache decode. SOURCE_FIT_CHECKPOINT records exact bank recovery/rosters, SOURCE_SELECTION the original source selection, SOURCE_PRETRIAL_CHECKS causal actual-history input/omission checks, SOURCE_COUNTS the actual autonomous source counts, SOURCE_PREDICTIVE_CHECKS their reductions, SOURCE_NUMERICAL_CHECKS the future-poison/nonlinear audit, SOURCE_ONE_RESAMPLE its actual source draw and dependent forecasts, SOURCE_INSPECTION the inherited reference and saved-output checks. STAGE1_RESOURCES and SOURCE_INSPECTION carry separate measured CPU/process wall/read/decode counters; FINAL_ACCOUNTING sums them without erasing prior lineage or I/O uncertainty. MANIFEST identifies current code/output bytes. PREPARATION and MAIN_FREEZE are the PI-facing result/future scope.

## Released Stage2

PI released the fixed main at14:28UTC, with author continuation readback14:30:35UTC. AMENDMENT_SCOPE/STATUS reconciled the four-quantity primary versus original632-column stronger family BEFORE new main execution/forecast/score exposure. Original MAIN_FREEZE is preserved. MAIN_ACCESS precedes the certified capped evaluation-cache decode. Every simulator call receives a prefix plus future boundary flags with all other future fields physicallyNaN. Original source/evaluation exposure remains consumed.

The main and independent synthetic-control commands were launched as follows; their resources are measured separately and summed, even where processes overlap:

```sh
env PYTHONDONTWRITEBYTECODE=1 OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1 NUMBA_CACHE_DIR=/private/tmp/calibration-frontier-main-numba campaigns/learning_rule_transport_2026-10-28/.modelenv/bin/python lab/tasks/calibration-frontier-main-2026-11-05/run_main.py > lab/tasks/calibration-frontier-main-2026-11-05/MAIN.log 2>&1
```

```sh
env PYTHONDONTWRITEBYTECODE=1 OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1 NUMBA_CACHE_DIR=/private/tmp/calibration-frontier-controls-numba campaigns/learning_rule_transport_2026-10-28/.modelenv/bin/python lab/tasks/calibration-frontier-main-2026-11-05/main_controls.py > lab/tasks/calibration-frontier-main-2026-11-05/CONTROLS.log 2>&1
```

The completed preservation/reference comparison reads saved aggregate count ensembles only:

```sh
env PYTHONDONTWRITEBYTECODE=1 OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1 NUMBA_CACHE_DIR=/private/tmp/calibration-frontier-reference-numba campaigns/learning_rule_transport_2026-10-28/.modelenv/bin/python lab/tasks/calibration-frontier-main-2026-11-05/verify_main_reference.py > lab/tasks/calibration-frontier-main-2026-11-05/REFERENCE_TO_DEVELOPMENT.log 2>&1
```

Postforecast commands, to run only once complete saved MAIN_COUNTS/MAIN_SOURCE_COUNTS and actual execution receipt exist:

```sh
env PYTHONDONTWRITEBYTECODE=1 OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1 NUMBA_CACHE_DIR=/private/tmp/calibration-frontier-analysis-numba campaigns/learning_rule_transport_2026-10-28/.modelenv/bin/python lab/tasks/calibration-frontier-main-2026-11-05/analyze_main.py > lab/tasks/calibration-frontier-main-2026-11-05/ANALYSIS.log 2>&1
```

```sh
env PYTHONDONTWRITEBYTECODE=1 OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1 MPLCONFIGDIR=/private/tmp/calibration-frontier-plot-mpl .venv/bin/python lab/tasks/calibration-frontier-main-2026-11-05/plot_main.py > lab/tasks/calibration-frontier-main-2026-11-05/PLOT.log 2>&1
```

MAIN_SCORES saves metric arrays for combined streams, each stream, exact GRU and source draws; MAIN_CONTRASTS/FAMILY save the paired animal contributions and complete label mapping. The primary four and full632 analyses use identical frozen pivots/weights/seeds. MAIN_CALIBRATION retains coverage/PIT and mean-ratio/count-pooling diagnostics. MAIN_MONTE_CARLO separates particle-stream effects, source-half effects and nonlinear initialization from animal/site uncertainty. The controls' modest nominal-coverage shortfall is retained in CONTROL_INTERPRETATION; it is not hidden by a new pivot.

For an independent result scientist, MAIN_COUNTS/MAIN_SOURCE_COUNTS plus MAIN_OBSERVED are sufficient to reconstruct proper scores without any author module or raw trial access. BOOTSTRAP_COUNTS and MAIN_FAMILY make the weighting/multiplicity procedure inspectable. Count dimensions, runtime versions and original inputs are pinned in MAIN_RUN_FREEZE and final manifests. Per-animal/draw chunks preserve completed work in case of interruption; do not rerun completed forecasts merely to repair a later report or delivery.

## Numerical refinement and final order

The original main/analyze_main completed first. Files with INITIAL512 suffix preserve all initial results/methods. NUMERICAL_REFINEMENT/REFINEMENT_START record the measured trigger after initial outcomes and before two additional256streams in the PRIMARY condition only. Models, fits, targets, score pivot, weights, margins, inference method/seeds remain unchanged. Other conditions/source draws/exact-prefix challenge are not rerun.

```sh
env PYTHONDONTWRITEBYTECODE=1 OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1 NUMBA_CACHE_DIR=/private/tmp/calibration-frontier-refine-numba campaigns/learning_rule_transport_2026-10-28/.modelenv/bin/python lab/tasks/calibration-frontier-main-2026-11-05/refine_fixed.py > lab/tasks/calibration-frontier-main-2026-11-05/REFINEMENT.log 2>&1
```

```sh
env PYTHONDONTWRITEBYTECODE=1 OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1 NUMBA_CACHE_DIR=/private/tmp/calibration-frontier-refined-analysis-numba campaigns/learning_rule_transport_2026-10-28/.modelenv/bin/python lab/tasks/calibration-frontier-main-2026-11-05/analyze_refinement.py > lab/tasks/calibration-frontier-main-2026-11-05/REFINED_ANALYSIS.log 2>&1
```

The latter writes FINAL MAIN_ANALYSIS and REFINED_SCORES/CONTRASTS/MONTE_CARLO/CALIBRATION(_SUMMARY), plus MAIN_FAMILY_REFINED. The literal632family remains;20refined columns produce652supplementary columns. Do not rerun analyze_main after analyze_refinement when intending the final output: it would overwrite refined results with512results and duplicate data reads. Plot final MAIN_ANALYSIS with the earlier plot command. Three plot passes clarify labels/caption only; PNG/resource FIRST/SECOND versions are retained. Final MAIN_RESULT states gray bands cover primary rows, source dots omit animal uncertainty, and the source envelope does not exclude material gains. Numerical outputs did not change for presentation.
