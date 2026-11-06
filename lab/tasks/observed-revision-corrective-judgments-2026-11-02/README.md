# Observed revision-quality source check — CLOSED before fitting

Read[RESULT.md](RESULT.md) first, then[SOURCE_CONTRIBUTION_GATE.md](SOURCE_CONTRIBUTION_GATE.md). This pass verified one actual paired edit and its seven quality votes, but not its original learner/draft/rater linkage. Closest work already defines this target; no new material correction-decision comparison was earned. Main fitting, held-out scoring, controls and independent review areUNRUN.

The actual corrected native output is[FIRST_DATA_CHECK.json](FIRST_DATA_CHECK.json). Its19/19word lengths, unchanged word multiset and7Better votes come from original pinned CSV record1. The initial22word assertion failure is preserved in[FAILURES.md](FAILURES.md) and[NATIVE_RUNS.json](NATIVE_RUNS.json); success does not erase it.

## Offline reproduction

Python3.9+ standard library only; no numerical libraries, dependencies or seed. From repository root:

```sh
python3 lab/tasks/observed-revision-corrective-judgments-2026-11-02/first_data_check.py
```

The cached ZIP is required. The script verifies its Git blob hash before decoding and reconstructing the same first record. This command recreates the consumed source check; it does not create a fresh holdout or resume this CLOSED allocation.

Saved-report consistency (JSON/link checks, no raw source reread) can be checked with`python3 lab/tasks/observed-revision-corrective-judgments-2026-11-02/check_artifacts.py`; the actual output is`ARTIFACT_CHECK.json`.

The optional original acquisition code is[acquire_first.py](acquire_first.py). It reads at most250001responsebytes, stops if the250000byte cap is exceeded, verifies the exact169209byte object's Git blob, enumerates the ZIP and inspects only its first CSV record. It reuses a cached object when present. Network access was unavailable under the default sandbox; the actual successful download used approved network escalation. Do not acquire V.2, new corpora or repair original learner joins as an automatic continuation of this task.

## Evidence and accounting

- [SOURCE_MANIFEST.json](SOURCE_MANIFEST.json): source trees/blob pins, license scope, protocol meaning, closest prior and25logical public operations including failures.
- [EXPOSURE.json](EXPOSURE.json): whole original ZIP/full666358byteCSV decode versus first-record interpretation; all summary/metadata exposure, protected lineage and unacquired payloads.
- [RESOURCES.json](RESOURCES.json):100MBseparate read/decode allowance,25,169,209byte charged ingress,26,279,936byte largest measured successful native RSS and unresolved provider/failed-pass/physical-I/O accounting.
- [STATE.md](STATE.md): bounded closure and one terminal report status. Proposed shared-memory entry:[PROPOSED_LEARNING.md](PROPOSED_LEARNING.md), for PI integration only.

The scope is internal research only under the source's stated research usage. Website-template MIT licensing is not taken as a dataset license. No source publication, outside contact, paid call, model API, new edit or human experiment occurred. This source closure does not finish the lab's scientific goal or stop its existing heartbeat.
