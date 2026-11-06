# Motor teaching-error transfer, 2026-10-31

**Source-only result:** the4-degree jump-to/stationary response ratio is0.890 in consumed TsayA and0.343 in consumed Al-Fawakhiri Figure3 after an additive endpoint-expression control. A calibrated published prescription predicts0.887 for Figure3 even after stationary amplitude calibration. The difference survives mean/median and source-pipeline controls. Source-compatible sensory curves and stationary-hit extensions give different Figure4 forecasts, so its42 individual-outcome records remain undecoded. Optional210-person geometry stays closed.

Read [RESULT.md](RESULT.md), [STATE.md](STATE.md), [EXPOSURE.json](EXPOSURE.json) and [RESOURCES.json](RESOURCES.json). The scientific summary is [source_transfer.png](source_transfer.png) / [source_transfer.pdf](source_transfer.pdf); neither panel contains Figure4 outcomes. [SOURCE_ONLY_FREEZE.json](SOURCE_ONLY_FREEZE.json) freezes the source-only support test and explicitly does not release target outcomes.

From repository root, verify frozen bytes and reconstruct the decisive saved scalars without reading a raw CSV:

```sh
.venv/bin/python lab/tasks/motor-teaching-transfer-2026-10-31/reproduce.py
```

Actual default verification is saved in [REPRODUCE_CHECK.json](REPRODUCE_CHECK.json). [VERIFICATION.json](VERIFICATION.json) also verifies coefficient/forecast/loss equality after warning correction and exact additive-expression generator recovery.

A separately allocated full scientific replay uses the four permitted cached CSVs, no network, no optional210-person payload and no Figure4 outcome decoding:

```sh
.venv/bin/python lab/tasks/motor-teaching-transfer-2026-10-31/reproduce.py --sources
```

This supplied mode was **not run again in the original tranche**. It charges approximately270MB additional scientific read/decode/hash allowance and takes a few seconds on this environment. It writes into a fresh owned`replay/<UTC>/`directory, compares all declared scientific outputs and leaves frozen originals intact. Run it only within an appropriately allocated scientific block; do not exceed the original600MB cap by automatically adding it to the completed400MB charge.

The actual execution order was source_support.py; source_analysis.py (initial warnings, explicit-contraction correction and final supported-cell flags); endpoint_control.py; prescription_check.py; measurement_sensitivity.py; source-only freeze; support_witness.py; artifact-only finalize.py and reproduce.py. The first source-analysis warning artifact is retained. No failed gate or exposure is reset.

Files:

- `source_support.py` / `SOURCE_SUPPORT.json`: pinned schemas/input support and three source-equivalent saturation curves; no outcome conversion.
- `source_analysis.py` / `SOURCE_ANALYSIS.json`: all58 consumed source people, small prescribed regressions and source-only model diagnostics. The TsayB success coefficient and out-of-support predictions are flagged.
- `endpoint_control.py` / `ENDPOINT_CONTROL.json`: saturated current/next cells, all per-person coefficients and the matched-source/LOO diagnostic.
- `prescription_check.py` / `PRESCRIPTION_CHECK.json`: one published functional form, three starts, sigma profile and500source bootstraps.
- `measurement_sensitivity.py` / `MEASUREMENT_SENSITIVITY.json`: all mean/median/mask/difference controls, with no favorable subset selection.
- `support_witness.py` / `SUPPORT_WITNESS.json` / `SOURCE_COMPATIBLE_TARGET_WITNESSES.csv`: rank/support proof, paired target extensions, exact generator control and input-only IDs.
- `SOURCE_MANIFEST.json`: original repository/code pins, source links and bounded literature operations. The original CSVs remain in the existing read-only source directory.
- `LEARNING_PROPOSAL.md`: one specific proposed entry for PI integration; shared memory was not edited by this worker.

Python3.9.6, NumPy2.0.2, SciPy1.13.1, Matplotlib3.9.4 and threadpoolctl3.7.0 are already available in the repository `.venv`; no dependency installation occurred. Exact runtime versions are in REPRODUCE_CHECK. All code sets one numerical thread. Participant bootstrap intervals are conditional and have no certified population coverage. This is a source-readiness result with separate independent review still pending, not a completed Figure4 validation.
