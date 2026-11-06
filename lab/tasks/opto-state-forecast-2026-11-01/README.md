# Optogenetic pre-state forecast allocation

**Outcome: source-gate partial stop; no forecast utility result.** Start with `RESULT.md`, `FIRST_DATA_CHECK.json`, `METADATA_CHECK.json` and `GATE.json`.

The first real fluorescence table is cached as `0_gcamp.txt` with its five matching files. Files `1_*` and `2_*` are metadata only. Public URLs and content hashes are pinned in `SOURCE_MANIFEST.json` and individual acquisition/failure records in `ACQUISITION.json`. The external data license was not established; no publication or redistribution authorization is inferred from the article's license.

The analysis uses Python 3 standard library only: no third-party dependencies, model seeds, parallel workers, numerical threads or charged services. The archived source code is inspected as text and is never imported or executed.

The original successful arithmetic command was:

```sh
python3 lab/tasks/opto-state-forecast-2026-11-01/first_check.py
```

To replay the numerical check from the cached, immutable source objects without overwriting the saved result:

```sh
python3 /Users/vanshkumar/Documents/repos/devo-research-lab/lab/tasks/opto-state-forecast-2026-11-01/first_check.py --output /tmp/opto-first-check-replay.json
```

Shapes, finite counts, time differences, window counts and numerical means should match `FIRST_DATA_CHECK.json`; timestamps/RSS are runtime metadata. The output-path option was added during closeout; that additional replay was not executed after the gate stop. `metadata_gate.py` reproduces the metadata/source-code inspection. `inspect_sources.py` and `inspect_schema.py` document the original code/schema reads; their generated text is cached.

Acquisition was performed by `acquire.py` and `acquire_records.py` using exact listed public URLs, with one bounded retry after an identifier timeout. These scripts preserve failed attempts and cap application bytes. They are reproduction records, not authorization for new network acquisition. `acquire_records.py` refuses existing objects. `ACQUISITION.json` pins the publication-linked v1.1 code archive (MD5 `40d87e790193d38528b4ba0cecf23e8c`) and all retrieved bodies. The 113-record count is inferred from 678 six-field files; no independent-animal mapping was established by that arithmetic.

`UNRUN.json` explicitly records the absent scientific stages. `PROPOSED_LEARNING.md` is for PI integration into shared memory. `STATE.md` records terminal delivery status. No shared lab records were edited by this worker.
