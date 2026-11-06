# Assigned-teacher/common-probe source gate

Read [RESULT.md](RESULT.md) first. This is a **closed, unsuccessful source gate**, not an acquisition forecast. Actual original data were acquired, but the required independent teacher-assignment/acquisition/common-probe calculation was not earned.

`FIRST_DATA_CHECK.json` preserves actual failed native outputs and observed phase counts. `first_data_check.py` is the saved failed analysis, intentionally not advertised as passing; its current assertion fails because the file-order development learner is kids2A while the checker expected kids2B. The earlier adult-count failure is retained in FAILURES.md. Do not run it for new science without a new authorized allocation.

Dependencies: project `.venv/bin/python`, Python3.9.6 standard library; no new packages. The original CSV and input snapshots are saved here, so no network is needed to inspect the record. To reproduce **only hashes and the recorded closeout**, from the repository root:

```
.venv/bin/python lab/tasks/assigned-teacher-common-probe-2026-11-01/record_closeout.py
```

This reads saved bytes, never decodes participant CSV rows, and is **not** a replacement measurement milestone. Inspect [PUBLIC_OPERATIONS.json](PUBLIC_OPERATIONS.json), [SOURCE_TREE.json](SOURCE_TREE.json), [SOURCE_PINS.json](SOURCE_PINS.json), [RESOURCES.json](RESOURCES.json) and [FAILURES.md](FAILURES.md) for exact source paths, original Git IDs, local SHA-256 pins and limits. Source text copies have normalized whitespace; the original CSV bytes match their declared blob. No seeds/model/evaluation outputs exist because those stages were unrun.
