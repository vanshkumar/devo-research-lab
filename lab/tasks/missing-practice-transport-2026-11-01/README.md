# Missing-practice transport: exact histories and measurement requirements

Read `RESULT.md` for the result and scientific limits. The main worked example shows a uniform target-width guarantee below 0.10 with one calibrated return probe and at most one missing event. Two missing events admit a 0.12848 gap. A directional-retention counterexample then shows why one probe alone needs an unverified symmetry assumption; one extra teaching event and a probe recover the missing direction in the expanded toy class.

The computational environment is Python 3.9 or later, standard library only, one process at a time, no numerical worker threads, no randomness, no network calls during reproduction. Exact Python version, resources and failures are in `RESOURCES.json`.

Key artifacts:

- `PROTOCOL.md`, `config.json`, `FREEZE.json`: choices and pins saved before main computation.
- `first_calculation.py`, `FIRST_CALCULATION.json`: early exact rational enumeration and attaining histories.
- `main.py`, `BOUNDS.json`: continuous-parameter identified sets, witnesses, measurement partitions, monotone envelopes, calibration enclosures and controls.
- `POSTVALIDATION_NOTE.md`, `reference_checks.py`, `REFERENCE_CHECKS.json`: separately implemented checks and the directional-retention contrary/intervention result.
- `PROOFS.md`: assumptions, sharpness, observation likelihoods, numerical caveats and extra-intervention derivation.
- `BOUNDS_TABLE.csv`, `MEASUREMENT_TABLE.csv`: compact numerical tables.
- `SOURCES.json`, `RESOURCES.json`, `ARTIFACT_PINS.json`: primary-source identifiers/exposure digest, limitations/resources and saved artifact hashes.
- `LEARNING_PROPOSAL.md`: owned proposal for PI integration; shared memory was not edited.
- `STATE.md`, `DELIVERY_STATUS.json`: completion and one-report return status.

Reproduce in a new owned subdirectory so the original frozen evidence survives. From any shell, run these commands in order; `mkdir` deliberately requires a new directory. The example uses the repository's current absolute path. All public source lookups are excluded from reproduction.

```sh
TASK_DIR=/Users/vanshkumar/Documents/repos/devo-research-lab/lab/tasks/missing-practice-transport-2026-11-01
REPRO_DIR="$TASK_DIR/reproduction-01"
mkdir "$REPRO_DIR"
cp "$TASK_DIR/first_calculation.py" "$TASK_DIR/main.py" "$TASK_DIR/reference_checks.py" "$TASK_DIR/summarize.py" "$TASK_DIR/config.json" "$TASK_DIR/PROTOCOL.md" "$REPRO_DIR/"
python3 "$REPRO_DIR/first_calculation.py"
python3 "$REPRO_DIR/main.py"
python3 "$REPRO_DIR/reference_checks.py"
```

The numerical bounds/witnesses should match, allowing normal floating precision. Timestamps, generated hashes involving timestamps, native RSS and Python platform strings will differ. The generic zero-missing envelope's documented 50,000-box limit is retained; the separate algebraic control gives its exact zero. `summarize.py` can then regenerate tables and local pins after copying any narrative/source files desired into the reproduction directory; its resources describe the original allocation.

Every simulated case is consumed development evidence. No protected empirical target is released, no source is reacquired, and no publication/independent-review claim is implied by the reproduction.
