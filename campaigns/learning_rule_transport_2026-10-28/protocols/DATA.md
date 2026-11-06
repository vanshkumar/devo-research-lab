# Data allocation, acquisition and exposure boundary

2026-10-28. This record concerns source bytes and chronology. Forecast outcomes and score definitions are owned by the campaign lead.

## Frozen allocation

`SPLIT.json` was written and hashed before the first campaign trial-outcome read. All 154 indexed standard training animals were considered using only cache metadata. The 128 animals with a table for every indexed `trainingChoiceWorld` session were eligible. No future success, behavioral performance or available forecast horizon was used for eligibility. The other 26 animals are explicitly recorded as incomplete-table exclusions.

All eligible animals in hoferlab and wittenlab form the whole-laboratory holdout: 10 and 17 animals respectively. Among the other laboratories, `int(SHA256('learning_rule_transport_2026-10-28:' + subject),16) % 5 == 0` selects the unfamiliar-animal holdout. This yields 74 development animals, 27 unfamiliar-animal holdout animals and 27 whole-laboratory holdout animals. Short histories remain in these allocations. Their later contribution is determined by exposure availability under the lead's frozen censoring rule.

The strict-prefix external allocation is the 20 published nonopto animals with mapped days 1–5. `fip_16` (starts at day 2) and `fip_38` (mapped day 0 followed by day 2) remain excluded from this primary allocation. The thirteen unrelated optogenetic animals, including three with one ordinary task session each, are excluded.

Two previous feasibility examples are recorded in `SPLIT.json`: CSHL034/2019-10-01/001 and fip_13/2021-03-05/001. Prior inspection was limited to schema, row count, byte count and hashes. Development outcomes for CSHL034 have now been opened under this campaign; the external example's outcomes have not.

## Exposure coverage, using footers only

Parquet file metadata supplies row counts without reading trial columns. These counts are in `data/ROW_COUNTS.json`, with per-animal totals, session sizes and version strings in `data/COVERAGE.json`.

| Split | Animals | Ordinary sessions | Trials | At least 1,000 trials | At least 2,000 | At least 4,000 | At least 6,000 |
|---|---:|---:|---:|---:|---:|---:|---:|
| Development | 74 | 1,473 | 860,306 | 69 | 66 | 56 | 49 |
| Animal holdout | 27 | 535 | 306,218 | 26 | 25 | 21 | 19 |
| Whole-lab holdout | 27 | 439 | 252,262 | 22 | 22 | 19 | 16 |
| External | 20 | 453 | 278,074 | 20 | 20 | 20 | 20 |

The original acquisition index also contained 34 `FPChoiceWorld_unconditionedA/B` sessions, all author day 0 in these 20 animals. The exact ordinary external task is `_iblrig_tasks_FPChoiceWorld6.4.2`. Before reading any external outcomes, the primary index was amended to exclude the unconditioned variants from acquisition-trial chronology. Their already-downloaded original bytes are retained sealed; exact metadata is in `data/EXCLUDED_EXTERNAL_PROTOCOL_RECORDS.json`. `data/RAW_ACQUISITION_INDEX.json` preserves the original byte-acquisition list. This exclusion follows task inputs and chronology, not behavior. Day-0 pre-exposure remains a limitation to a claim of biological first exposure.

Complete indexed tables do not certify a complete biological first-exposure history in either source. Source dates/session numbers are retained without inventing prehistory. Multiple sessions on the same external training day are preserved in exact date/number order and retain the published day map. Source `day` in prepared NPZ files is the indexed session ordinal; `session`/`session_index` are zero-based. Use metadata dates for calendar-day grouping, not this ordinal. External `day` is the author's mapped training day.

## Original-byte provenance

The frozen feasibility caches and author day map are reused directly from `sources/longitudinal_learning_feasibility_2026-10-28/`, without refreshing their mutable publication tags. Cache, paper and source-code provenance remains in the source manifest. `data/INDEX.json` contains each relevant session's source protocol, URL, original dataset UUID, published size/MD5 and exact chronology. URLs follow the public S3 UUID filename convention.

5,154 original public objects were acquired, totaling 150,941,721 bytes including the retained external day-0 files. 5,153 matched their frozen cache size and MD5 exactly. One development table had a stale index entry: KS016/2019-08-13/001 was advertised as 47,770 bytes, MD5 `6509885ff13bb361486ef6a57cfd8e82`; the public object is 40,136 bytes, MD5 `17ea8854c15e173458db6e5a27470661`, SHA256 `89744d09a8a4eccb87897ac04574dead039deeae764abc698bee5a1940e6ec67`. Its public S3 object listing independently reports that exact current size and ETag, last modified 2024-09-16. This was resolved from object metadata before reading this animal's outcomes. It is included with the pinned current original bytes, rather than dropping the animal. The stale cache metadata, failed verification attempts, original listing and explicit exception are preserved in `data/DOWNLOAD_MANIFEST.jsonl`, `data/KS016_object_listing.xml` and `data/OBJECT_METADATA_EXCEPTIONS.json`.

Every successful object record includes both local SHA256 and verified public MD5. The manifest is append-only and preserves the initial sandbox DNS failure and the stale-cache attempts. Use the final record per dataset UUID for acquired-byte status. Retrying acquisition honors the explicit original-object exception. No account or access-control workaround was used; standard public HTTPS acquisition needed ordinary network permission outside the sandbox's DNS restriction.

The corrected primary index has 5,120 files: 2,900 trial tables and 2,220 correction/repeat arrays. Repeat numbers are missing for some indexed sessions and remain NaN in the derived table; omissions remain choice 0. Missing repetition metadata is not interpreted as a first presentation.

Source protocol versions span 4.1.3 through 6.4.0. The full split-specific counts are saved in `data/PROTOCOL_VERSION_COUNTS.json`. The two cached indexes contain no `_iblrig_taskSettings.raw.json`; protocol strings alone cannot determine operator reward, gain or manually edited settings. The trainer auditor owns versioned-code reconstruction and residual uncertainty.

## Outcome-access design

Only development tables have been converted to NPZ at initial setup. These contain all 13 raw columns, session indices/boundaries, exact source chronology metadata, source/author day coding and correction-repeat numbers when available. No response is recoded into a left/right choice; the original IBL `choice` codes are +1 left, -1 right and 0 omission. The conversion does not fit latent states or calculate learning curves.

`code/data_io.py` exposes `subjects(split)` and `load_subject(subject, split='dev', purpose=...)`. Development loading needs only NumPy, including in the existing Python3.9 analysis environment. Parquet conversion and metadata coverage use the preserved DuckDB1.4.1 extension with the bundled CPython3.12 runtime. Trial outcomes are logged before original-table opening and on processed-file loading in `protocols/EXPOSURE.jsonl`. Source-holdout conversion/loading requires an explicit existing freeze artifact; external conversion/loading requires a separate explicit external gate artifact. A boolean flag alone does not grant validation access. The lead remains responsible for checking that those files actually declare the requisite scientific freeze/gate.

Before source validation, this boundary was strengthened with `load_prefix_and_opportunities(subject,split,prefix_n=1000,horizon=5000,freeze_path=...,external_gate_path=...)`. It returns `(prefix_dict,future_session_start,metadata)`: only the first 1,000 outcome rows, selected session by session using bounded Parquet SQL `LIMIT`, with correction flags memory-mapped and sliced to that prefix. Future session starts come exclusively from the already pinned footer row counts. No future contrasts, choices, rewards, probabilities or correction flags enter the returned forecast inputs. The metadata marks the exact prefix length, available future exposure and whether the horizon is complete. Tests on short DY_005 and long NYU-07 development histories matched the existing full development NPZ values and future session boundaries exactly. Whole-subject holdout outcomes should be opened for scoring only after forecast artifacts are saved. Initial original-Parquet prefix extraction requires CPython3.12/DuckDB; the returned arrays have no such dependency.

Commands, from repository root:

```sh
PYTHON=/Users/vanshkumar/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3
"$PYTHON" campaigns/learning_rule_transport_2026-10-28/code/acquire_data.py --freeze-only
"$PYTHON" campaigns/learning_rule_transport_2026-10-28/code/acquire_data.py --workers 20
"$PYTHON" campaigns/learning_rule_transport_2026-10-28/code/data_io.py --coverage
"$PYTHON" campaigns/learning_rule_transport_2026-10-28/code/data_io.py --prepare-dev
```

The first command reuses an existing split without rewriting it. Network access is needed only for missing bytes; all scientific modeling/reconstruction can use pinned local bytes offline. Do not run holdout/external outcome preparation while developing methods.
