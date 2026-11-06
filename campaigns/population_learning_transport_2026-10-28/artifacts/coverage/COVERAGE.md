# Prospective new-source metadata and byte audit

Completed 2026-10-28 America/New_York (metadata result UTC2026-10-29T01:46:35). No new animal trial values, prefixes or learning curves were read. The audit reads opaque bytes for cryptographic verification, NPY headers for dtype/shape, and Parquet footers/schema for names/types/row counts only. No original campaign artifact or exposure record was changed.

The exact26 animals excluded for incomplete Parquet coverage supply **24 primary eligible animals** with at least1000 prefix+3000future task opportunities. The original 944 indexed training sessions are recoverable without a chronology gap in their indexed core fields:655 Parquet sessions and289 legacy NPY sessions,511,906total indexed opportunities. Every one of4407 requested files matches the public cache's byte size and MD5; SHA256 values pin the downloaded bytes. Total opaque bytes47,164,543. Every requested NPY core/auxiliary first dimension matches the session's row count; legacy intervals are Nx2. Parquet contains all seven required scalar columns (including the two interval components). Subject/date/session-number triples are unique, so sorting by date then session number is unambiguous.

| Laboratory | Primary animals | Coverage limits |
|---|---:|---|
| hoferlab |10|SWC_007 has517total opportunities, lacking1000-prefix|
| mrsicflogellab |6|none by indexed row count|
| angelakilab |5|NYU-21 has3473total:1000-prefix+2473future, four complete500 bins|
| churchlandlab |2|CSHL056 has4245total, still full primary|
| cortexlab |1|one animal cannot establish laboratory calibration|

Coverage selection is based on opportunity counts, not learning. All26 dispositions remain in RESULT.json. These animals were selected by historical storage format, not sampled randomly; their five labs were already represented. Indexed continuity does not certify complete biological first exposure or absence of unindexed task history. Full-horizon availability can depend on behavior/stopping; conditioning on realized opportunities is an operational forecast target rather than a full causal stopping model.

Reward volume is present in all655 tables and absent from all289 legacy sessions. The new reader returns NaN and an explicit `rewardVolume_available` Boolean mask for unavailable legacy values. It never substitutes binary feedback or nominal task reward as a measured volume. This is compatible with the frozen actor's binary-feedback input, but cannot test volume-sensitive learning.

The entire original EXPOSURE.jsonl was searched for each exact quoted subject ID; none of these26 names occurs. Prior consumed-source status and the external20 sealed status are unchanged. Noel's separate release was not accessed by this audit.

## Reader and access boundary

`code/mixed_reader.py` is a separate original-byte implementation. Public APIs require an existing prospective freeze and append the new campaign exposure ledger before decoding. `load_prefix_and_opportunities(subject,prefix_n=1000,horizon=3000,freeze_path=...)` returns the exact permitted prefix, future session-start vector derived solely from row counts, and metadata. `load_scored(subject,stop=4000,freeze_path=...,forecast_manifest=...)` additionally requires an existing saved-forecast manifest and reads only the requested first4000 rows. No full-history processed NPZ is created. NPY prefix slicing uses read-only memory mapping. Parquet SQL LIMIT returns only selected rows; the library can internally decompress a column block, but future values are neither returned to the analysis nor summarized.

A synthetic three-session fixture verifies prefix truncation within a session, future session starts, omission preservation, session ends, missing-volume masks, and denial without a freeze or saved-forecast manifest. It uses generated arrays only. READER_FIXTURE_TEST.json records the result.

The initial network request failed under sandbox DNS restrictions; the exact public-data acquisition succeeded after normal approved network escalation. The first header pass exposed a NumPy2 private-API mismatch; switching to the public versioned header readers fixed it before any trial values were accessed. ACQUISITION_NOTES.json preserves both failures. No source-model or scientific protocol setting was chosen from those failures.

## Artifacts and reproduction

`INDEX.json` pins exact requested dataset IDs/URLs and local paths; all dataset IDs match the prior prospective inventory. `BYTE_MANIFEST.json` contains sizes, MD5 and SHA256. `FILE_METADATA.json` contains NPY header/Parquet schema and row counts. `SESSIONS.json` reconstructs date/session chronology and per-session paths. `RESULT.json` provides full per-animal eligibility and counts; `MANIFEST.json` pins these outputs and reader source.

From repository root:

```sh
campaigns/learning_rule_transport_2026-10-28/.modelenv/bin/python campaigns/population_learning_transport_2026-10-28/code/mixed_reader.py --coverage
```

With bytes present, this rerun verifies hashes and metadata entirely offline. It appends a metadata-only exposure event and refreshes timestamped audit summaries; it does not decode values. The immutable raw file pins do not depend on that timestamp.
