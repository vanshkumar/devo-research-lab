# Human forward-history forecast

Main result: under an exact known deterministic source schedule, shared history beats the frozen persistence comparator by **.033894nat/responding choice [.025548,.042306]**, after generating post-prefix behavior. All people are already consumed; this is a postvalidation result. The known future schedule and assumed iid observation law sharply limit the inference. No broader goal completion or independent review is claimed.

- [Concise scientific result and limitations](RESULT.md)
- [Pre-main protocol](PROTOCOL.md), [freeze](FREEZE.json), [feasibility](FEASIBILITY.json)
- [Saved forecasts](FORECASTS.npz), [saving record](FORECAST_META.json), [scores](SCORES.json), [person scores](PERSON_SCORES.csv)
- [Reference checks](CHECKS.json), [scalar/mask and exact omission audit](FINAL_AUDIT.json)
- [Source/data pins](SOURCE_PINS.json), [resource/exposure accounting](RESOURCES.json), [environment](ENVIRONMENT.json), [pause boundary](PAUSE_CHECKPOINT.md)

Original main commands, already executed from repository root:

```sh
.venv/bin/python lab/tasks/human-generated-history-forecast-2026-11-01/feasibility.py
.venv/bin/python lab/tasks/human-generated-history-forecast-2026-11-01/forward.py checks
.venv/bin/python lab/tasks/human-generated-history-forecast-2026-11-01/forward.py freeze
.venv/bin/python lab/tasks/human-generated-history-forecast-2026-11-01/forward.py forecast
.venv/bin/python lab/tasks/human-generated-history-forecast-2026-11-01/forward.py score
.venv/bin/python lab/tasks/human-generated-history-forecast-2026-11-01/audit.py
```

Preserve those original outputs. For a full fixed-fit replay into a NEW task-local directory:

```sh
.venv/bin/python lab/tasks/human-generated-history-forecast-2026-11-01/reproduce.py --out reproduction/verified_offline
```

The replay reuses the frozen source-only observation calibration, runs the reference checks, reconstructs forecasts and scores, and requires exact numerical agreement with saved arrays/settings. It refuses an existing output directory. The replay wrapper's CLI was checked; an additional full replay was **not run** in this allocation because the earned calculation/reference/scalar audits already passed. Its exact replay assertions remain unexecuted. Original scientific commands and actual outputs above are the execution evidence.

Dependencies already present: Python3.9.6, NumPy2.0.2, SciPy1.13.1, pandas2.3.3, openpyxl3.1.5. No dependency installed. Scientific scripts force numerical thread environment limits to1. Seeds and particle counts are fixed in PROTOCOL.md/forward.py. No network is required, and no command opens the original134MB CSV or invokes the old campaign's full reproduction/refitting/recovery.

The source campaign and original cached inputs remain immutable. This task writes only its own directory. All freezes/exposure/failures and cumulative pause accounting remain in force; reproduction is not an automatic continuation or resource refund.
