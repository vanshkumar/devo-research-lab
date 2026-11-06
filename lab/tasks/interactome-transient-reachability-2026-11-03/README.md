# Full original2019 reference and finite-input reachability pilot

Read [RESULT.md](RESULT.md). The exact279-neuron release executes and reproduces the relevant~2s sustained-input reference. ONEnewexperiment, frozen before evaluation, finds no material late motor-state or later-challenge difference after its2sforwardinput ends. BANKreference/CLOSEthis specific recipe; no biological-memory/global-attractor conclusion.

- [PROTOCOL.md](PROTOCOL.md), [CONFIG.json](CONFIG.json), [FREEZE.json](FREEZE.json): unchanged pre-evaluation declaration/actual timestamp and hashes.
- [MODEL_REFERENCE.json](MODEL_REFERENCE.json): full source semantics/assets/parameters, actual original-source and independent numerical reference.
- [PILOT_RESULT.json](PILOT_RESULT.json), [PILOT_SUMMARY.csv](PILOT_SUMMARY.csv): all fixed outcomes, controls and numerical precision. `seed{0,1}_{baseline,finite,sham,drive}.npz` retain all rawstates/times. `seed0_literal_*.npz` retain the tighter exact-source references. The default/FWDreferenceNPZs and primary differenceNPZs are also retained.
- [OUTPUT_AUDIT.json](OUTPUT_AUDIT.json): independently expressed scalar score/exponential checks. [OUTPUT_INVENTORY.json](OUTPUT_INVENTORY.json) is the scientific-output inventory at audit time; later closeout records are intentionally additional.
- [SOURCE_MANIFEST.json](SOURCE_MANIFEST.json), [RESOURCES.json](RESOURCES.json), [NATIVE_EXECUTION.json](NATIVE_EXECUTION.json), [FAILURES.md](FAILURES.md), history/: provenance/exposure/nativeexits/resources/failedbytes. [PROPOSED_LEARNINGS.md](PROPOSED_LEARNINGS.md) is for PIintegration; sharedmemory unchanged by worker.

Existing runtime only: workspace `.venv/bin/python`3.9.6, NumPy2.0.2/SciPy1.13.1. Numerical thread environmentvariables are set1 before imports. No dependencies installed. Original source/BSD3license live read-only at sibling `connectome-persistence-contrast-2026-11-03/sources/`; current fixed source assets/presets and exactpins live in sources/. No saved_dynamics or recordings are dependencies.

Inspection/revalidation of saved artifacts, with NOnewpilot:

```sh
cd /Users/vanshkumar/Documents/repos/devo-research-lab
.venv/bin/python lab/tasks/interactome-transient-reachability-2026-11-03/verify_closeout.py
```

Historical execution was reference.py → freeze.py → pilot.py (gridfailure) → preserve_grid_failure.py → pilot.py --resume-grid-fix (allprimarysaved/literalclippingfailure) → complete_saved.py → audit_outputs.py. The failures are part of the result. Do not rerun the one-time preservation/freezing/consumed-run scripts over their saved receipts.

For a separately authorized FUTURE reproduction, this command stages a NEWempty output directory, uses the SAMEfrozen protocol and validated numerical clipping driver, and leaves the original outputs intact:

```sh
cd /Users/vanshkumar/Documents/repos/devo-research-lab
.venv/bin/python lab/tasks/interactome-transient-reachability-2026-11-03/reproduce.py --output /Users/vanshkumar/Documents/repos/devo-research-lab/lab/tasks/interactome-transient-reachability-2026-11-03/reproduction/new-authorized-run
```

The reproduction entry point was statically checked, not executed here; the actual original/reference/pilot/audit commands and exits are recorded separately. It imports precisely the executed functions plus the successful one-sided literaldriver. A future distinct reviewer should instead use its own authorized path/bounds and independent implementation; author reruns are not independent scientific review. All present realizations are development forever.
