# Independent review of the matched acquisition-forecast calculation

**Verdict: verify the original numbers; narrow the interpretation.** The 6.350495 pp conditional/autonomous population-error gap reproduces independently. The one predeclared count-weighting contrary reduces that gap to 0.433059 pp under a different averaging estimand. Read [REVIEW.md](REVIEW.md) before interpreting either result.

## Evidence map

- [FIRST_CALCULATION.json](FIRST_CALCULATION.json): first independently scalar-reconstructed endpoint scores, targets/counts, pins and resources; nativeexit0at12:30:05Z.
- [DESIGN.md](DESIGN.md), [FROZEN_PLAN.json](FROZEN_PLAN.json): reconstruction, resource and ONEcontrary declaration, with the preserved precomparison compiler amendment.
- [AUDIT.json](AUDIT.json):24original prefix/raw/session/particle/omission/autonomous/conditional checks, full scalar reference paths and two full saved trial-array comparisons.
- [RESULT.json](RESULT.json), [RECONSTRUCTED_ENDPOINTS.npz](RECONSTRUCTED_ENDPOINTS.npz): reconstructed targets/counts and autonomous/conditional particle ensembles. Axes are animal, particle,500-opportunity bin, side; side orderleft/right. Shares are0–1before ppconversion. Autonomous counts are generated exact100opportunities; observed counts are fixed actual opportunities, omissions included.
- [UNCERTAINTY_AUDIT.json](UNCERTAINTY_AUDIT.json): reconstructed20000paired-animal draws and2000within-animal paired-particle perturbations. These intervals apply to the original estimand only.
- [CONTRARY.json](CONTRARY.json): the single predeclared mean-of-ratios versus ratio-of-summed-counts comparison. [FINAL_AUDIT.json](FINAL_AUDIT.json) independently recomputes it using integer correct counts and scalar sums, and verifies source/design/resource pins and saved ordering.
- [CODE_AUDIT.md](CODE_AUDIT.md): information flow, original modules used as objects under test, equal-prefix-mixture scope, author failure and unrun checks.
- [SOURCE_PINS.json](SOURCE_PINS.json), [RESOURCE_PLAN.json](RESOURCE_PLAN.json), [RESOURCES.json](RESOURCES.json): inputs, whole containing/read/decode/hash budgets, failed-pass charge and final347704984/350000000bytecharge; peakRSS393756672/800000000.
- [FAILED_FIRST_EXECUTED_review.py](FAILED_FIRST_EXECUTED_review.py), [FAILED_FIRST_FROZEN_PLAN.json](FAILED_FIRST_FROZEN_PLAN.json), [FAILED_FIRST_STOP.json](FAILED_FIRST_STOP.json), [FAILED_PASS_RESOURCES.json](FAILED_PASS_RESOURCES.json), [ORIGINAL_RESOURCE_PLAN.json](ORIGINAL_RESOURCE_PLAN.json): preserved failed scalar-reference compilation and its40610718bytecharge. The unchanged original task's nativeexit120after saved science is a separate author failure.
- [EXECUTION_NOTES.md](EXECUTION_NOTES.md), [STATE.md](STATE.md), [PROPOSED_LEARNING.md](PROPOSED_LEARNING.md): native completion, bounded handoff and PI memory proposal. [TERMINAL_REPORT.md](TERMINAL_REPORT.md) contains the one authorized terminal report.

## Exact historical commands

Repository root was `/Users/vanshkumar/Documents/repos/devo-research-lab`. Runtime was the existing Python3.12environment under campaigns/learning_rule_transport_2026-10-28/.modelenv, with NumPy/SciPy/Numba/DuckDBalready present; no installation or network access occurred. These are historical commands, not authorization to repeat consumed science or overwrite frozen records. The main script retains this assignment's fixed13:29:05Zdeadline. A separately authorized reproduction must preserve pins, owned outputs, access controls and a new bounded budget.

```sh
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1 NUMEXPR_NUM_THREADS=1 PYTHONDONTWRITEBYTECODE=1 campaigns/learning_rule_transport_2026-10-28/.modelenv/bin/python lab/reviews/learning-forecast-information-audit-2026-11-01/first_calculation.py
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1 NUMEXPR_NUM_THREADS=1 PYTHONDONTWRITEBYTECODE=1 campaigns/learning_rule_transport_2026-10-28/.modelenv/bin/python lab/reviews/learning-forecast-information-audit-2026-11-01/resource_plan.py
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1 NUMEXPR_NUM_THREADS=1 PYTHONDONTWRITEBYTECODE=1 campaigns/learning_rule_transport_2026-10-28/.modelenv/bin/python lab/reviews/learning-forecast-information-audit-2026-11-01/amend_resources.py
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1 NUMEXPR_NUM_THREADS=1 NUMBA_NUM_THREADS=1 PYTHONDONTWRITEBYTECODE=1 campaigns/learning_rule_transport_2026-10-28/.modelenv/bin/python lab/reviews/learning-forecast-information-audit-2026-11-01/review.py
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1 NUMEXPR_NUM_THREADS=1 PYTHONDONTWRITEBYTECODE=1 campaigns/learning_rule_transport_2026-10-28/.modelenv/bin/python lab/reviews/learning-forecast-information-audit-2026-11-01/final_audit.py
```

The first main execution used the source preserved as FAILED_FIRST_EXECUTED_review.py and exited1during compilation. The successful executed review.py is pinned in FROZEN_PLAN and unchanged. First calculation/resource inventory/amendment/successfulmain/finalscalar audit all exited0. No second learner, parameter search, retention change, target release or gate calculation was run. Source data/version/license/deployment limitations remain inherited from the frozen campaigns, whose manifests/pins are referenced by this review. Historical campaign, manuscript and author files were read-only.
