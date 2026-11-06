# Reproduction and inspected outputs

All paths below are in this owned task directory unless a source path is explicit. These are the executed assignment commands, not permission to repeat source consumption, reset budgets or open candidate outcomes. No main simulation or scoring of new evaluation animals ran.

Python3.12/DuckDB uses the already bundled interpreter `/Users/vanshkumar/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3` and the previously pinned local DuckDB1.4.1 under `sources/longitudinal_learning_feasibility_2026-10-28/tools`. Numeric source/planning commands use repository `.venv/bin/python` (NumPy/SciPy). No installation, credentials or paid API was needed.

Executed local/scientific commands, from repository root:

```sh
/Users/vanshkumar/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3 lab/tasks/independent-acquisition-cohort-2026-11-05/qualify_saved.py
.venv/bin/python lab/tasks/independent-acquisition-cohort-2026-11-05/extract_catalogue.py
/Users/vanshkumar/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3 lab/tasks/independent-acquisition-cohort-2026-11-05/qualify_catalogue.py
/Users/vanshkumar/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3 lab/tasks/independent-acquisition-cohort-2026-11-05/qualify_footers.py --plan
/Users/vanshkumar/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3 lab/tasks/independent-acquisition-cohort-2026-11-05/qualify_footers.py
/Users/vanshkumar/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3 lab/tasks/independent-acquisition-cohort-2026-11-05/qualify_footers.py --resume
.venv/bin/python lab/tasks/independent-acquisition-cohort-2026-11-05/plan_discrimination.py
/Users/vanshkumar/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3 lab/tasks/independent-acquisition-cohort-2026-11-05/qualify_aggregates.py --plan
/Users/vanshkumar/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3 lab/tasks/independent-acquisition-cohort-2026-11-05/qualify_aggregates.py --probe=NYU-01
/Users/vanshkumar/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3 lab/tasks/independent-acquisition-cohort-2026-11-05/qualify_aggregates.py --chronology
/Users/vanshkumar/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3 lab/tasks/independent-acquisition-cohort-2026-11-05/source_measurement_probe.py
.venv/bin/python lab/tasks/independent-acquisition-cohort-2026-11-05/criterion_source_screen.py
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python lab/tasks/independent-acquisition-cohort-2026-11-05/criterion_source_fit.py
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python lab/tasks/independent-acquisition-cohort-2026-11-05/criterion_count_counterexample.py
/Users/vanshkumar/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3 lab/tasks/independent-acquisition-cohort-2026-11-05/build_qualified_cohort.py
.venv/bin/python lab/tasks/independent-acquisition-cohort-2026-11-05/focused_design.py
```

`PUBLIC_REQUESTS.jsonl` records every exact publicURL/method/range/received-byte count/ETag/responseSHA and failure, including all programmatic trailer/footer/identity-column/source-probe requests. The transport helper does not decode values; its `payload_values_decoded:false` flag does **not** override later scientific decode recorded in EXPOSURE/SOURCE_MEASUREMENT_PROBE. For initial CLI requests the invocation format was:

```sh
.venv/bin/python lab/tasks/independent-acquisition-cohort-2026-11-05/source_access.py URL LOCAL_NAME --range=bytes=START-END --limit=MAX_BYTES --purpose=DECLARED_PURPOSE
```

The global ZIP central-directory and first13,920,500-byte range extracted ONLY sessions/datasets catalogue entries. QC.json was neither decoded nor fully acquired. Unrevisioned aggregate objects were pinned by the completeS3listing/ETag, never substituted as new animals because their filename/release changed. Old170metadata-listed subjects were initially overexcluded during alias propagation; INITIAL outputs preserve that error, corrected before body access to use the actual154canonical exclusions.

Inspect these actual outputs:

- SOURCE/identity: CATALOGUE_EXTRACTION, ORIGINAL_EXCLUSIONS, ORIGINAL_SESSION_IDS, CATALOGUE_QUALIFICATION, IDENTITY_PATTERN_CHECK and CANDIDATE_ROSTER/OBJECTS.
- Measurement/chronology: FOOTER_ACCESS_PLAN, FOOTER_QUALIFICATION, AGGREGATE_ACCESS_PLAN, AGGREGATE_PROBE_SCHEMA, AGGREGATE_CHRONOLOGY and QUALIFIED_COHORT. Raw footer-only `.pqt` derivatives contain zeros for unavailable data; they are **not behavioral datasets**. Aggregate derivatives fill only session-ID chunks. The separate `_source_only_probe.pqt`/SOURCE_ONLY_ROWS contains the declared NYU-42 sample and remains source-only.
- Planning: DISCRIMINATION and FOCUSED_DESIGN, with literal INITIAL outputs and initial executed code preserved where corrections were needed. No inherited author scoring/simulator module was imported for these calculations.
- Criterion: official IBL_TRAINING_CRITERIA and psychofit_reference source pins, CRITERION_SOURCE_SCREEN/FIT/CHRONOLOGY and CRITERION_COUNT_COUNTEREXAMPLE. `criterion_source_fit_EXECUTED.py` preserves the executed initial reducer; corrected censor summaries were derived from saved source windows without refitting. Reproducing corrected source analysis uses the current script, with the fixed partial-day/censor handling.
- Boundaries/resources: GOAL_START/GOAL_FINAL, actual allowance snapshots, SOURCE_ONLY_ACCESS_PLAN/BYTE_RANGES, EXPOSURE.jsonl, ACCESS_HISTORY, FOOTER_INTERRUPT, LOCAL_FAILURES, FINAL_ACCOUNTING and MANIFEST.

Inline closeout code also checked the identity pattern bytes, performed the recorded no-hit `rg -l -F -f CANDIDATE_IDENTITY_SEARCH.txt` search limited to prior access/exposure/brief/result/review/freeze records, derived longer-horizon source chronology and corrected saved criterion censor summaries. Their exact outputs and correction logic are saved in the named JSON/EXECUTED records. The source search is not claimed exhaustive private-history or biological-alias proof.

No source-only fit, source marker or native completion validates biology by itself. Independent payoff/design review and, if funded, fresh result challenge remain necessary. New evaluation outcomes are unopened and every old/protected cap survives reproduction.
