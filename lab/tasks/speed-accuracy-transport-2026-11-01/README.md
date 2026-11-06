# Speed–accuracy instruction transport

The fixed first-speed-block to next-accuracy-block forecast fails: shared-drift process accuracyMSEimproves14.7%over source-selected ridge, but RTMSEworsens158.1%and mean-RTMAEis221versus123ms. A separate conditional control diagnostic finds that the5ppaccuracy-MAEgate, alone, limits substantial-signal passage to18/100. [Read the result](RESULT.md).

Start with [protocol](PROTOCOL.md)/[single source-only revision](DEVELOPMENT_AMENDMENT.md), [source record](SOURCES.md), [FREEZE](FREEZE.json), [predictions](PREDICTIONS.json), [scores](SCORES.json), [controls](CONTROLS.json), [contrary](CONTRARY.json), [author audit](RAW_AND_PREDICTION_AUDIT.json) and [resources](RESOURCES.json). A fresh independent review is UNRUN. Detailed source/data exposure is in RESULT/STATE; the full release was acquired and decoded before freezing.

The immutable93,156-byte public RData has Gitblob9800773f265db3b30e09ae81b52f612f43527454andSHA256991429ecb0a6711dd32422ee4cff9eb7d3010c9de9434387aa36b8788e573f62. `speed_acc.RData.base64` preserves its GitHub transport. No network is needed to reproduce. Dependencies are projectPython3.9.6plus pinned [requirements](requirements.txt), with rdata/xarray/typing_extensions already in this task's deps/. Original failed additive prescription is retained for inspection; `analysis.py` uses the single revised positive-gain prescription.

Exact original native stages used the following command form (mode develop/freeze/predict/score), with each stage completed sequentially:

```sh
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1 /Users/vanshkumar/Documents/repos/devo-research-lab/.venv/bin/python /Users/vanshkumar/Documents/repos/devo-research-lab/lab/tasks/speed-accuracy-transport-2026-11-01/analysis.py score
```

For a full reproduction, make a separate temporary copy so its new timestamps preserve the saved bundle. The following commands use the existing environment and cached data; `freeze` and `predict` intentionally refuse to overwrite their saved outputs.

```sh
task_repro_dir="$(mktemp -d /private/tmp/speed-accuracy-repro.XXXXXX)"
cp -R /Users/vanshkumar/Documents/repos/devo-research-lab/lab/tasks/speed-accuracy-transport-2026-11-01/. "$task_repro_dir/"
rm "$task_repro_dir/FREEZE.json" "$task_repro_dir/PREDICTIONS.json" "$task_repro_dir/PREDICTION_PIN.json"
task_python=/Users/vanshkumar/Documents/repos/devo-research-lab/.venv/bin/python
export OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1
"$task_python" "$task_repro_dir/first_data_check.py"
"$task_python" "$task_repro_dir/analysis.py" develop
"$task_python" "$task_repro_dir/audit.py" numerics
"$task_python" "$task_repro_dir/analysis.py" freeze
"$task_python" "$task_repro_dir/analysis.py" predict
"$task_python" "$task_repro_dir/analysis.py" score
"$task_python" "$task_repro_dir/audit.py" numerics
"$task_python" "$task_repro_dir/audit.py" reconstruct
"$task_python" "$task_repro_dir/controls.py"
"$task_python" "$task_repro_dir/diagnostics.py"
"$task_python" "$task_repro_dir/finalize_summary.py"
```

`first_data_check.py` recreates participant1original-trial block joins/arithmetic and full nonresponse metadata. `model.py` supplies the density/conditional normalizer/MAP/empirical prescriptions. `analysis.py` fits source people, freezes, predicts from held baselines, then scores. `audit.py` checks formulas/quadrature/raw reconstruction/unchanged future-suffix inputs and target-only cutoff sensitivity. `controls.py` runs the original finite conditional score controls; `diagnostics.py` implements the separately declared postvalidation resolution/influence check. The finalizer verifies pins and saves compact evidence/versions/manual charges; it does not rerun fitting. These are author checks.
