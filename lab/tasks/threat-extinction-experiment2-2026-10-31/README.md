# Experiment2extinction forecast

The frozen20participant test did not certify added cue-specific forecast utility. Primary physiology error rises3.56%, a past-acquisition scaling sensitivity rises0.31%with uncertainty spanning zero, and expectancy chooses identical predictions. Known-effect discrimination is weak(2/100physiology,56/100expectancy). Read [RESULT.md](RESULT.md) before interpreting a negative result as biological equality.

Use the existing repository .venv: Python3.9.6and NumPy2.0.2. All other dependencies are standard library. Scientific scripts set numerical thread counts to1before importing NumPy. No network, high-rate physiology processing or new dependency is needed for offline reproduction.

From repository root, this read-only verification was executed successfully:

```sh
.venv/bin/python lab/tasks/threat-extinction-experiment2-2026-10-31/verify_saved.py
```

It checks source MD5/SHA, both freezes and reconstructed saved forecast losses. Source/author checks were executed with:

```sh
python3 lab/tasks/threat-extinction-experiment2-2026-10-31/certify_sample.py
python3 lab/tasks/threat-extinction-experiment2-2026-10-31/certify_metadata.py
.venv/bin/python lab/tasks/threat-extinction-experiment2-2026-10-31/audit.py pre
.venv/bin/python lab/tasks/threat-extinction-experiment2-2026-10-31/analysis.py pilot
.venv/bin/python lab/tasks/threat-extinction-experiment2-2026-10-31/analysis.py freeze
.venv/bin/python lab/tasks/threat-extinction-experiment2-2026-10-31/controls.py
.venv/bin/python lab/tasks/threat-extinction-experiment2-2026-10-31/analysis.py evaluate
.venv/bin/python lab/tasks/threat-extinction-experiment2-2026-10-31/audit.py post
.venv/bin/python lab/tasks/threat-extinction-experiment2-2026-10-31/contrary.py freeze
.venv/bin/python lab/tasks/threat-extinction-experiment2-2026-10-31/contrary.py score
```

Do not rerun those mutating stages against canonical artifacts: freezes/evaluation stages deliberately reject overwrites. Initial FIRST_DATA_CHECK.json contains an early string-decoder defect, preserved and explained in FIRST_DATA_CHECK_CORRECTION.md; numeric/scoring outputs were subsequently checked. The corrected sample check is SAMPLE_CERTIFICATION.json.

A full offline rerun can create an isolated subdirectory under this owned task path:

```sh
.venv/bin/python lab/tasks/threat-extinction-experiment2-2026-10-31/reproduce.py --name offline_reproduction
```

The full wrapper has not been executed in this allocation; its underlying stages above have. It needs a fresh read/compute budget and writes only the new subdirectory, refusing an existing name. It reuses the cached source certification/design and106,395byte ZIP, regenerates development, controls, frozen predictions and contrary diagnostics. It does not restore validation status or fetch public files. No reacquisition is needed; this assignment's5public-operation cap is exhausted.

Important artifacts: SOURCE_MANIFEST.json and SOURCE_CERTIFICATION.json(source/license/schedule limits); DEVELOPMENT.json(rejected revision); PROTOCOL.md/FREEZE.json/FROZEN_MODELS.json; FORECASTS.json/EVALUATION.json; CONTROLS.json; CONTRARY_PLAN.md/CONTRARY_FREEZE.json/CONTRARY_FORECASTS.json/CONTRARY.json(postvalidation); AUTHOR_AUDIT_PRE.json/AUTHOR_AUDIT_POST.json/FINAL_VERIFICATION.json; RESOURCES.json and STATE.md. Proposed project memory is in PROPOSED_LEARNING.md. Main and contrary bootstrap seeds and all100replicate control results are saved.

Attribute original data to Mertens, Leer, van Dis, Vermeer, Steenhuizen, van der Veen and Engelhard(2019), DOI10.1016/j.jbtep.2018.09.007, OSFdxpb3, CC-BY4.0. The source ZIP is unchanged; task scripts derive forecasts and checks. Raw physiology is not in the archive; no author contact or public publication occurred.
