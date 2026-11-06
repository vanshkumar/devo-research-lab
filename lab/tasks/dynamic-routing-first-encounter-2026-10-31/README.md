# Dynamic-routing first encounters: closed, primary scores unrun

The source gate passes on development, but the immutable evaluation chronology gate fails on two of three mice. Four frozen predictors and all forecasts exist; **no evaluation utility result is earned**. [RESULT.md](RESULT.md) explains the recorded-channel discrepancies and the conditional-control limits.

From repository root, verify cached HTTP response hashes, independent raw decoding, all frozen pins, every saved forecast and the expected scoring stop:

```sh
.venv/bin/python lab/tasks/dynamic-routing-first-encounter-2026-10-31/reproduce_offline.py
```

For a complete author replay of100development fits plus64conditional controls as well:

```sh
.venv/bin/python lab/tasks/dynamic-routing-first-encounter-2026-10-31/reproduce_offline.py full
```

The full command writes refit/control outputs under `reproduction/` and OFFLINE_REPLAY.json; it preserves original frozen files and never computes evaluation losses. The executed full replay exactly reproduces model coefficients and960conditional-control forecast/outcome rows, as well as12,752evaluation probability values. This is an author self-replay, not independent scientific validation.

The task uses the existing Python3.9.6/NumPy2.0.2/SciPy1.13.1 environment and a task-local Numcodecs0.12.1 ARM64 wheel; its published SHA256 is verified before extraction. No shared install was made. The replay can extract that cached wheel if deps is missing. For a different OS/Python ABI, use a compatible trusted Numcodecs0.12.1 installation within a separately authorized reproduction environment; the cached wheel itself is specifically CPython3.9macOSARM64. No network installation is performed by replay.

Key artifacts:

- `FIRST_DATA_CHECK.json`, `UNIT_CERTIFICATION.json`, `CODEC_CHECK.json`: actual development/source verification; initial failed broad catch check remains in FIRST_DATA_CHECK_v0.
- `PROTOCOL.md`, `SCIENTIFIC_FREEZE.json`: scientific choices and twelve stable hashes, frozen before evaluation.
- `DEVELOPMENT_MODELS.json`, `DEVELOPMENT_CV.json`, `DEVELOPMENT_CHECKS.json`: actual fits, choices and input/gradient tests.
- `CONTROL_SUMMARY.json`, `CONTROL_DETAILS.json`, `CONTROL_FORECASTS.json`: specified synthetic generators, all outcomes and limited discrimination.
- `{subject}_FORECASTS.npz`, `FORECAST_PINS.json`: saved main and instruction-ablation forecasts; all remain unscored.
- `EVALUATION_DATA_CHECK.json`, `RESPONSE_DISCREPANCY_AUDIT.json`: failed evaluation gate and actual task-control versus recorded-response evidence.
- `FAILURES.md`, `RESOURCES.json`, `SOURCE_MANIFEST.json`, `EXPOSURE.json`, `ARTIFACT_PINS.json`: failures, manual additive accounting, exact source URLs/content hashes, consumed observations and terminal pins.

`evaluate.py score` is deliberately blocked by the failed frozen gate. Do not bypass it or reclassify these arrays as untouched. `analysis.py development/controls`, `decode_development.py` and `check_development.py` are historical stage implementations that write their original outputs; use the replay command above to preserve frozen evidence. `acquire_fixed.py` and its request lists preserve acquisition commands only: **the96operation allocation is closed; do not rerun network acquisition.**

Data are derived Allen NWB exports, CC-BY-4.0 by each asset's metadata. Task-source commit links are archive assertions, not hardware deployment proof. Raw sensor/neural data, the excluded early session and all protected lab cohorts remain unacquired. No next allocation or independent review is started by these commands.
