# Acquisition probe reactivity: source/design closure

Read [RESULT.md](RESULT.md) and [CLOSURE.md](CLOSURE.md). The actual calculation verifies the pinned RNN and exposes an unsupported no-feedback shortcut; terminal first-response cohorts remain the strong routine alternative. No main discovery or independent review is earned.

Artifacts:

- [first_calculation.py](first_calculation.py), [FIRST_CALCULATION.json](FIRST_CALCULATION.json): source pins, parameter inventory, constructed histories, branch probabilities, independent scalar/production update agreement, feedback alias and omission controls.
- [design_screen.py](design_screen.py), [DESIGN_SCREEN.json](DESIGN_SCREEN.json): elementary first-response precision/cost illustration and timestamped CLOSE decision.
- [ASSUMPTIONS.md](ASSUMPTIONS.md), [SOURCE_PINS.json](SOURCE_PINS.json): information boundary, import safety, source scope and limited prior access.
- [FAILURES.md](FAILURES.md), [EXECUTION.json](EXECUTION.json), [RESOURCES.json](RESOURCES.json): failed/successful native commands, outputs, accounting and unknowns.
- [STATE.md](STATE.md), [PROPOSED_LEARNING.md](PROPOSED_LEARNING.md): terminal handoff and proposed project-specific memory for PI integration.

Exact native commands from repository root, run sequentially:

```sh
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1 NUMEXPR_NUM_THREADS=1 NUMBA_NUM_THREADS=1 PYTHONDONTWRITEBYTECODE=1 campaigns/learning_rule_transport_2026-10-28/.modelenv/bin/python lab/tasks/acquisition-probe-reactivity-2026-11-01/first_calculation.py
```

```sh
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1 NUMEXPR_NUM_THREADS=1 PYTHONDONTWRITEBYTECODE=1 campaigns/learning_rule_transport_2026-10-28/.modelenv/bin/python lab/tasks/acquisition-probe-reactivity-2026-11-01/design_screen.py
```

The first command initially exited 1 for a missing closing parenthesis; the corrected command and second command exited 0. No installation occurred. Dependencies are the existing .modelenv Python/NumPy/SciPy/Numba, with standard-library modules. Only model parameters are loaded; no saved biological prefixes, target arrays or baseline bank are needed. No random seed is used: this is exact branch averaging on deterministic constructed reference histories, not a Monte Carlo population test.

Original deadline guards remain fixed in the code (first calculation hard stop 16:58:30 UTC; design screen close by 15:53:30 UTC on November 1). Later reproduction requires a separately authorized task/review using its own scope; do not restart this finished worker or modify its historical artifacts to evade those guards. No independent review should be commissioned just to verify a routine reference exercise.

Shared files, source assets and older scientific artifacts were read-only. The task's source/design closure does not complete the PI native goal or retire the continuing heartbeat.
