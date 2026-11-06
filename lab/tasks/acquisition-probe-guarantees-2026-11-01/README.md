# Acquisition validation and scheduled probes: closed at the prior screen

[RESULT.md](RESULT.md) gives the decision; [CLOSURE.md](CLOSURE.md) supplies the standard derivation and its missing measurement inputs. There is no new scientific main claim or empirical result.

Reproduce the single finite reference calculation from repository root with Python 3.9+ (standard library only):

```sh
python3 lab/tasks/acquisition-probe-guarantees-2026-11-01/reference_check.py
```

The command rewrites `FIRST_CALCULATION.json` with the same mathematical outputs and fresh runtime/time metadata. Exact rational enumeration checks 64 logging paths; natural logs use Python `math`. No random seeds, external packages, data or network are needed. The original execution is preserved in [NATIVE_EXECUTION.json](NATIVE_EXECUTION.json); [RESOURCES.json](RESOURCES.json) and [FINAL_AUDIT.json](FINAL_AUDIT.json) document this original run. Do not rerun after closure merely to repair prose or reporting; any later scientific execution remains subject to lab authorization.

[PRIOR_PINS.json](PRIOR_PINS.json) records the two primary bibliographic versions, equations and URLs, with no original-byte certificate. [PUBLIC_OPERATIONS.json](PUBLIC_OPERATIONS.json) distinguishes the six charged operations from unknown backend traffic. [ASSUMPTIONS.md](ASSUMPTIONS.md), [FAILURES.md](FAILURES.md) and [STATE.md](STATE.md) preserve the information boundary and early stop. [PROPOSED_LEARNING.md](PROPOSED_LEARNING.md) is for PI integration; the worker did not write shared memory.
