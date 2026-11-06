# Learning-forecast information audit

Read [RESULT.md](RESULT.md) for the conclusion and [DESIGN.md](DESIGN.md) for the pre-calculation estimators. This is a postvalidation investigation on the same24consumed animals, with no new fitting recipe or protected release. Independent review is pending.

**Result:** matching512joint prefix particles and generated scoring responses preserves a6.3505ppconditional/autonomous population-error gap. Conditional0.6195pp; autonomous6.9700pp; analytic conditional mixture0.62808pp. See [RESULT.json](RESULT.json) and [AUDIT.json](AUDIT.json).

## Artifacts

- [FIRST_CALCULATION.json](FIRST_CALCULATION.json): original numeric errors, exact endpoint counts, command, pins and initial resources; native exit0 at12:07:10Z.
- [FROZEN_DESIGN.json](FROZEN_DESIGN.json): design/code/input identities saved before new predictions.
- [PREDICTION_MANIFEST.json](PREDICTION_MANIFEST.json): complete24prediction files saved before new cohort scoring, sizes/side-array pins, and endpoint-file hash.
- [MATCHED_PREDICTIONS.npz](MATCHED_PREDICTIONS.npz): observed targets, saved central expectation, and all512autonomous/conditional sampled/conditional analytic side-cell predictions. Axes for particle arrays are animal, particle, bin, side; sides areleft/right. These are omission-inclusive probabilities/shares, before conversion to percentage points.
- `predictions/SUBJECT.npz`: complete512×3000conditional right-response probabilities and scoring choices,512×6omission probabilities, actual signed stimuli/choices/positive-feedback/session starts, initial/final correlated coefficient-memory states, endpoint predictions/counts and observations. Actual ALF choice−1right/+1left/0omitted. Generated scoring choices are not assimilated in conditional state updates.
- [UNCERTAINTY_DRAWS.npz](UNCERTAINTY_DRAWS.npz): saved paired-animal and separate within-animal particle perturbations.
- [SOURCE_PINS.json](SOURCE_PINS.json): relevant saved artifact/design/code identities; the original complete freeze is checked by the executed code without exclusions.
- [RESOURCE_PLAN.json](RESOURCE_PLAN.json), [RESOURCES.json](RESOURCES.json), [CLOSEOUT_RESOURCES.json](CLOSEOUT_RESOURCES.json): planned containing-file/decoded charges, main measured resources and cumulative220MBcloseout charge; physical I/O remains unknown.
- [SAVED_SCORE_AUDIT.json](SAVED_SCORE_AUDIT.json):180independently scalar-reconstructed persisted scores/native exit0; [EXECUTION_NOTES.md](EXECUTION_NOTES.md) preserves the main logger's shutdown exit120.
- [PROPOSED_LEARNING.md](PROPOSED_LEARNING.md): proposed shared-memory entry for PI integration. Workers do not edit shared LEARNINGS.

## Reproduction and environment

Use the existing repository runtime `campaigns/learning_rule_transport_2026-10-28/.modelenv/bin/python`. The executed pipeline uses Python/NumPy/SciPy/Numba/DuckDB from that environment; no packages were installed. All scientific execution requires an active authorized bounded assignment under the lab policy. This package does not authorize another start.

To reconstruct **only persisted final scores**, without raw data, models, optimizer calls or new trajectories:

```sh
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1 NUMEXPR_NUM_THREADS=1 PYTHONDONTWRITEBYTECODE=1 campaigns/learning_rule_transport_2026-10-28/.modelenv/bin/python lab/tasks/learning-forecast-information-audit-2026-11-01/reproduce_scores.py
```

The saved native execution exited0, checking180numbers within7.905e-14pp and the original executed code/design pins. This command writes only SAVED_SCORE_AUDIT.json in the task path.

Historical exact commands, each from repository root:

```sh
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1 NUMEXPR_NUM_THREADS=1 PYTHONDONTWRITEBYTECODE=1 campaigns/learning_rule_transport_2026-10-28/.modelenv/bin/python lab/tasks/learning-forecast-information-audit-2026-11-01/first_calculation.py
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1 NUMEXPR_NUM_THREADS=1 PYTHONDONTWRITEBYTECODE=1 campaigns/learning_rule_transport_2026-10-28/.modelenv/bin/python lab/tasks/learning-forecast-information-audit-2026-11-01/resource_plan.py
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1 NUMEXPR_NUM_THREADS=1 NUMBA_NUM_THREADS=1 PYTHONDONTWRITEBYTECODE=1 campaigns/learning_rule_transport_2026-10-28/.modelenv/bin/python lab/tasks/learning-forecast-information-audit-2026-11-01/run.py
```

The main command is retained as executed and enforces this assignment's fixed13:35:57Zhard stop. It saved all scientific outputs before an exit120from its log wrapper during interpreter shutdown. Do not advertise this as a clean exit or rerun it for status repair. Future separately authorized reconstruction should read the frozen implementation, use the saved inputs/estimates, retain the original scientific controls, and restore logging streams before closing their targets. Seeds: original subject hash offsets101/211/313/419; paired-animal20261029; paired-particle20261101. Precise draw order and fixed nuisance replay are in DESIGN.md and run.py.

Original model/bank/prefix/forecast files and manuscript are read-only. Raw observations are accessed only through the original whitelist+4000-row-capped offline reader. Source data/public acquisition identities and inherited license/deployment/first-exposure caveats remain in the original campaigns, referenced by the strict freeze and source pins; there was no new public acquisition.
