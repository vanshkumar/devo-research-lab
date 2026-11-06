# Surprise/history next-response forecast

The specified short history gains1.43%[−.34%,2.77%]over the strong baseline on19held participants, failing the frozen5%joint rule. See RESULT.md. This is an author result awaiting fresh independent review.

From repo root, run the exact offline audit against immutable saved evidence:

```sh
.venv/bin/python lab/tasks/surprise-history-forecast-2026-11-01/verify.py
```

It verifies18freeze pins, reconstructs8,968targets and the source approximate reference from original MAT files using scalar arithmetic, replays B/H forecasts and their losses, and checks the cached control fitter against the direct selected ridge. It writes VERIFICATION.json only; scientific inputs, source weights and scores stay immutable. This command has actually passed. It is numerical self-audit, not independent scientific review.

To reproduce all200conditional controls in a **new** output directory while preserving original outputs:

```sh
.venv/bin/python lab/tasks/surprise-history-forecast-2026-11-01/reproduce_controls.py lab/tasks/surprise-history-forecast-2026-11-01/reproductions/full-controls
```

The original200-control batch is complete; a second full batch through this convenience runner is UNRUN. The runner uses the exact frozen controls.py with only its output/input directory redirected to copies of the two immutable feature arrays, then compares saved numerical summaries. It creates no service or scheduled work.

The executed original stages, in order, were acquire.py/inspectors, first_data_check.py, fix_split.py, data.py, develop.py, source_validation.py, freeze.py, evaluate.py predict, evaluate.py score, controls.py, contrary.py and verify.py. Their timestamps and failed passes are retained. Do not rerun splitting/freezing as a claim of a new holdout or overwrite the saved failure. The prediction and scoring programs deliberately refuse to overwrite their original outputs; the original freeze also enforces its historical deadline.

- BRIEF.md: original owner/question/resource envelope.
- SOURCES.md/ACQUISITIONS.json: public source/license/version records, failed acquisition attempts and pinned raw responses.
- FIRST_DATA_CHECK.json: actual first472-update arithmetic, one development person.
- SPLIT.json/PROTOCOL.md/FREEZE.json: identity split, complete feature/fitting/control prescriptions and pins before evaluation.
- model.py/data.py: past-only source models/features and original decoding; fitted_B.npz/fitted_H.npz: source-only learned weights.
- DEVELOPMENT.json/SOURCE_VALIDATION.json: development choices, chronology/units/safe-law and grid checks. INITIAL_* preserve the numerical failure before correction.
- predictions.npz/PREDICTION_MANIFEST.json/evaluation_truth.npz:8,968frozen keyed forecasts, before separate scoring. SOURCES marks raw compressed-byte exposure versus interpreted values.
- SCORES.json/CONTROLS.json/CONTRARY.json/VERIFICATION.json: main, fixed-generator controls, one consumed-record attribution check and actual self-audit.
- RESOURCES.json/EXPOSURE.json/STATE.md/LEARNING_PROPOSAL.md: final resources/exposure, return state and proposed shared-memory entry.

All angular model inputs are float64 radians; exported raw angles are degrees. NumPy and SciPy versions/Python are recorded in RESOURCES.json. One numerical thread is set before importing NumPy in data.py. The source approximate recurrence adapts upstream getTrialVarsFromPEs_cannon.m by Nassar/Bruckner/Frank under GPL-3.0; its original full license is retained as source_license.source. The empirical archive is CC0; article CC-BY4. No EEG payload was acquired.
