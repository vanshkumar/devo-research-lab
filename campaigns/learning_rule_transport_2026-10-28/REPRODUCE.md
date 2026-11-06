# Offline reproduction

Run from `/Users/vanshkumar/Documents/repos/devo-research-lab`. All original bytes, model weights, forecasts, seeds, code and uncertainty banks are local. External outcome values are unnecessary and must remain sealed unless a future authorized study changes that status.

## Tested full main-forecast reproduction

```sh
campaigns/learning_rule_transport_2026-10-28/.modelenv/bin/python campaigns/learning_rule_transport_2026-10-28/reproduce.py --replay all
campaigns/learning_rule_transport_2026-10-28/.modelenv/bin/python campaigns/learning_rule_transport_2026-10-28/rnn_reproduce.py
```

Both commands were executed successfully. The original runner regenerated288forecasts in48source animals, exactly matching every raw/calibrated curve and latent coefficient array. The RNN runner regenerated48forecasts, exactly matching curves, coefficients, GRU memory endpoints, counts and trainer summaries. Maximum differences were0. Both block Python network connection entrypoints and verify frozen artifacts. The original runner also independently reconstructs scores from original Parquet bytes. Its local-byte hash pass includes external files as bytes only, never decoding their outcomes.

Results:

- `artifacts/offline_reproduction/RESULT.json` and`FORECAST_REPLAY.json`.
- `artifacts/rnn/offline_reproduction/RESULT.json` and`FORECAST_REPLAY.csv`.
- `protocols/RECONSTRUCTION.md` and`RNN_RECONSTRUCTION.md` describe independently implemented original-byte target, score and conditional-recurrence checks.

The first command took278seconds on this host; RNN replay took186seconds. These are observed runtimes, not guarantees. Faster score-only reproduction:

```sh
campaigns/learning_rule_transport_2026-10-28/.modelenv/bin/python campaigns/learning_rule_transport_2026-10-28/reproduce.py --replay none
```

Default outputs go to separate reproduction folders; main validation forecasts are not overwritten. Preserve the code/model freeze hashes. The RNN runner reads only the original1000trial prefixes and footer opportunities, not real future choices/rewards.

## Environment

Reference: macOSarm64, CPython3.12.14, NumPy2.3.5, SciPy1.18.1, Numba0.68.1, DuckDB1.4.1. The campaign `.modelenv` is retained; its Python comes from the app's bundled runtime. Model fitting additionally used Torch2.15.0. Scientific plotting used the existing repository Python3.9 environment and Matplotlib. Torch is not needed for forecast replay.

`requirements-replay.txt` contains the minimal numerical/Parquet dependencies for recreating a replay environment on another host. The full observed `artifacts/models/requirements-model-lock.txt` records the existing environment, including unrelated inherited app packages and a local app-package URL; it is telemetry, not a portable installer specification. On a different platform install matching ordinary packages; do not copy the pinned Darwin DuckDB extension to a different ABI. The preserved feasibility wheel/source manifest documents its original extraction and official package hash. Bit-exact results are demonstrated on this host; portable floating-point tolerances are checked by the runners.

## Main experiment and analysis commands

The freeze file is mandatory for protected source data. These commands resume existing artifacts; use a fresh tag in a copied campaign for regeneration that must not overwrite archived evidence.

```sh
campaigns/learning_rule_transport_2026-10-28/.modelenv/bin/python campaigns/learning_rule_transport_2026-10-28/code/run_forecasts.py --split animal_holdout --models persistence,growth,reinforce,reinforce_pure,dnnglm,dnnglm32 --particles 512 --tag source_animals --freeze campaigns/learning_rule_transport_2026-10-28/protocols/FREEZE.json --calibration campaigns/learning_rule_transport_2026-10-28/artifacts/calibration/CONFIG.json
campaigns/learning_rule_transport_2026-10-28/.modelenv/bin/python campaigns/learning_rule_transport_2026-10-28/code/run_forecasts.py --split lab_holdout --models persistence,growth,reinforce,reinforce_pure,dnnglm,dnnglm32 --particles 512 --tag source_labs --freeze campaigns/learning_rule_transport_2026-10-28/protocols/FREEZE.json --calibration campaigns/learning_rule_transport_2026-10-28/artifacts/calibration/CONFIG.json
campaigns/learning_rule_transport_2026-10-28/.modelenv/bin/python campaigns/learning_rule_transport_2026-10-28/code/source_results.py
campaigns/learning_rule_transport_2026-10-28/.modelenv/bin/python campaigns/learning_rule_transport_2026-10-28/code/rnn_results.py
```

RNN source commands (their outputs are retained in the matching log files):

```sh
campaigns/learning_rule_transport_2026-10-28/.modelenv/bin/python campaigns/learning_rule_transport_2026-10-28/code/rnn_rollout.py --split animal_holdout --tag rnn_source_animals --model campaigns/learning_rule_transport_2026-10-28/artifacts/rnn/rnnglm32_nested_best.npz --particles 512 --horizon 5000 --freeze campaigns/learning_rule_transport_2026-10-28/protocols/RNN_FREEZE.json --calibration campaigns/learning_rule_transport_2026-10-28/artifacts/rnn/calibration/CONFIG.json
campaigns/learning_rule_transport_2026-10-28/.modelenv/bin/python campaigns/learning_rule_transport_2026-10-28/code/rnn_rollout.py --split lab_holdout --tag rnn_source_labs --model campaigns/learning_rule_transport_2026-10-28/artifacts/rnn/rnnglm32_nested_best.npz --particles 512 --horizon 5000 --freeze campaigns/learning_rule_transport_2026-10-28/protocols/RNN_FREEZE.json --calibration campaigns/learning_rule_transport_2026-10-28/artifacts/rnn/calibration/CONFIG.json
```

Do not pass a failed-source-gate decision as an external access grant. No `EXTERNAL_ACCESS_EARNED.json` was created.

## Refit provenance, not required for offline replay

Fitting uses development data only. Commands below document substantive fixed fits; original checkpoints, histories and logs are retained. They must be run in a copy because fitting writes artifact aliases/allocation files. Do not overwrite the frozen evidence. A fresh NPZ container can have a different ZIP timestamp/hash even when its numerical arrays agree.

```sh
campaigns/learning_rule_transport_2026-10-28/.modelenv/bin/python campaigns/learning_rule_transport_2026-10-28/code/fit_learning.py --rl --stable-gain --end 6000
campaigns/learning_rule_transport_2026-10-28/.modelenv/bin/python campaigns/learning_rule_transport_2026-10-28/code/fit_learning.py --rl --pure-reward --end 6000
campaigns/learning_rule_transport_2026-10-28/.modelenv/bin/python campaigns/learning_rule_transport_2026-10-28/code/fit_learning.py --dnn --hidden 16 --end 6000 --epochs 1000 --check-every 25 --seed 221 --truncation 500
campaigns/learning_rule_transport_2026-10-28/.modelenv/bin/python campaigns/learning_rule_transport_2026-10-28/code/fit_learning.py --dnn --hidden 16 --end 6000 --epochs 1000 --check-every 25 --seed 337 --truncation 500
campaigns/learning_rule_transport_2026-10-28/.modelenv/bin/python campaigns/learning_rule_transport_2026-10-28/code/fit_learning.py --dnn --hidden 32 --end 6000 --epochs 1000 --check-every 25 --seed 443 --truncation 500
campaigns/learning_rule_transport_2026-10-28/.modelenv/bin/python campaigns/learning_rule_transport_2026-10-28/code/fit_rnn.py --fit --end 6000 --epochs 1000 --check-every 25 --seed 557 --tag main
```

DNN selected16seed221epoch1000 and32seed443epoch950. RNN selectedseed557epoch975 after executing all1000epochs. `MODEL_SELECTION.json`/`RNN_SELECTION.json` preserve the development-only decisions. RL bounded±1.5and±10baseline pilots, short DNN smoke fits, optimizer repairs and all source-code equivalence checks remain in logs. No held-out outcome selected model weights/checkpoints.

## Controls, challenges and figures

The recovery pipeline's exact historical rollout is preserved in`artifacts/recovery/code_snapshot/`; that version predates strengthening real-source persistence from last500toall1000prefix observations. Its archive and forecast scores reproduce the reported control numbers. Regenerating with current source code changes that one baseline; the positive comparisons against growth are unaffected. Follow`protocols/RECOVERY.md` and its manifest rather than silently replacing historical artifacts.

`protocols/SOURCE_CHALLENGES.md` supplies commands for all972sensitivity/precision forecasts, including coherent retention, the balanced-zero diagnostic and all40DNN16/growth1024particle runs. `protocols/STOPPING_CONTROL.md` preserves the postvalidation independently seeded termination challenge and its one-animal full-horizon limitation. These are diagnostics on consumed source outcomes, not new untouched validation.

Plotting, with the existing repository Matplotlib:

```sh
.venv/bin/python campaigns/learning_rule_transport_2026-10-28/code/plot_results.py
.venv/bin/python campaigns/learning_rule_transport_2026-10-28/code/plot_rnn_results.py
```

PNG and PDF figures are under`figures/`. Do not regenerate any real external learning curve; its bytes are held for a future independently justified test.
