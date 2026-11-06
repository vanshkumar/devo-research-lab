# Reproduce the bounded development

Use the repository root and the original campaign's Python environment. No download or protected inputs. The manifest selects precisely the source and capped fields and ranges listed in CALIBRATION_PLAN. Prefer the saved capped projection for calibration reruns. A rerun of source.py is a fresh read of previously consumed rows and appends to the local ledger, so reproduce in a same-depth copy of this task directory and only with the same access scope. Keep the archived outputs.

```sh
task=lab/tasks/acquisition-reactive-sequence-2026-11-04
python_path=campaigns/learning_rule_transport_2026-10-28/.modelenv/bin/python
export PYTHONDONTWRITEBYTECODE=1 OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1
export NUMBA_CACHE_DIR=$(mktemp -d /private/tmp/reactive-numba.XXXXXX)
export PYTHONPATH="$PWD/sources/longitudinal_learning_feasibility_2026-10-28/tools"
"$python_path" "$task/source.py" plan
"$python_path" "$task/source.py" pilot
"$python_path" "$task/source.py" all
"$python_path" "$task/calibrate.py"
"$python_path" "$task/tracker.py"
"$python_path" "$task/fit_exposure.py"
"$python_path" "$task/sequence.py"
"$python_path" "$task/screen.py"
"$python_path" "$task/joint_control.py"

```

Run the sequence serially. Give each new run its own fresh NUMBA_CACHE_DIR. A rerun using the existing compiled cache with a dynamically imported historical module failed because its cache refers to the synthetic module name <dynamic>. The failure occurred before a new fit and is preserved. Use the saved SEQUENCE_MASSES for a screen-only rerun, which needs no empirical row reads. The original calibration code, before the zero-contrast residual fix, is calibrate_prefx.py. Its bytes match the initial CALIBRATION_FREEZE entry for calibrate.py. The initial results are CALIBRATION_PRE_ZERO_FIX.json. Corrected calibration and tracker choices are pinned in the next freeze. Separate code, data, metadata and timestamp freezes record the stages. Generated joint mass stores axes animal, stress, model, assay, arm, particle half and base-3 path with response categories +1/0/−1. All numerical evidence concerns this declared conditional case.
