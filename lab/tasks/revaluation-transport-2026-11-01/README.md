# Revaluation transport source audit

Source/design allocation CLOSED. Original participant calculation and all forecast stages UNRUN. Read[RESULT.md](RESULT.md),[FIRST_DATA_CHECK.json](FIRST_DATA_CHECK.json),[SOURCES.json](SOURCES.json),[RESOURCES.json](RESOURCES.json).

Offline reproduction from repository root, Python3.9+ standard library:

```sh
python3 lab/tasks/revaluation-transport-2026-11-01/inspect_source.py
python3 lab/tasks/revaluation-transport-2026-11-01/audit_source.py
```

The first reconstructs source inventories. The second checks cached SHA256/original Git-blob pins and writes SOURCE_AUDIT/FIRST_DATA_CHECK with gate_passed=false. Neither executes notebooks nor reads imaging payload. Exact connector sources already match; guarded terminal-LF restoration applies only when the original blob proves a copied LF nonoriginal. Generated timestamps/RSS may vary.

`acquire.py` records one explicit bounded public retrieval, not a continuing job. Source versions and exact attempts appear in[SOURCES.json](SOURCES.json)/[PUBLIC_OPERATIONS.md](PUBLIC_OPERATIONS.md). Do not automatically redownload or extend this closed allocation. No frozen empirical predictions exist; no dependencies, services or scheduler added.
