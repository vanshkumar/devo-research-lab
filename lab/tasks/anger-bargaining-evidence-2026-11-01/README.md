# Anger bargaining source/design allocation

Read [RESULT.md](RESULT.md) first. The allocation is closed after original-response calculation and a source-support reproduction; the mechanism comparison was not earned.

From `/Users/vanshkumar/Documents/repos/devo-research-lab`, cached-data reproduction uses Python 3 standard library only:

```sh
python3 lab/tasks/anger-bargaining-evidence-2026-11-01/first_data_check.py
python3 lab/tasks/anger-bargaining-evidence-2026-11-01/source_reconstruction.py
```

Each command rewrites its corresponding generated JSON timestamp; scientific values should match. No random draws or seed are used, no additional dependencies are needed, and no network request is required. Results describe exposed Study 1 data, not an untouched test. To preserve historical files, run a copied task directory in a separate scratch location and compare values while excluding timestamps/RSS. Do not rerun acquisition or continue this closed source allocation automatically.

`first_data_check.py` drops the two Qualtrics export rows, checks one active condition per response and computes original demand summaries. `source_reconstruction.py` joins clean id to one-based original participant position, checks seven fields, identifies exclusions and independently computes conventional factorial contrasts from four means/residual variance. Its reconstruction is independent of execution of the author's Rmd, but remains an author-run source audit, not an independent lab review. The initial first-check CSV decoding used splitlines; the separate reconstruction uses StringIO and reproduces counts/means on proper multiline CSV records.

`sources/` contains the small paper-linked originals and pinned metadata/provider outputs. `SOURCE_MANIFEST.json` gives hashes and retrieval provenance; `SOURCES.md` lists primary families/access limitations. `FETCH_LEDGER.json` records every local retrieval attempt, including initial DNS failure and redirected downloads. `EXTERNAL_OPERATIONS.json` records provider operations. `RESOURCES.json` separates measured local quantities from conservative allowances and unknown provider/redirect quantities. `PROTOCOL.md` is the retrospective source/design stop, not a fabricated pre-outcome main freeze. `LEARNING_PROPOSAL.md` is for PI integration only.

Raw original CSV contains auxiliary and coded ID fields; the reports do not reproduce the original ResponseIds or Prolific IDs. All acquired Study 1 bytes/decoded fields are consumed. Raw/clean Study 2/3 tables were listed but not acquired; their published summaries were exposed. No old empirical payloads were read.
