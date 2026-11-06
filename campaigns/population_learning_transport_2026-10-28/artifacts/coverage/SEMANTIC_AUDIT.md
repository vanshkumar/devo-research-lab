# Native field semantics and chronology audit

Passed on the already exposed 99,000 rows: 24 primary animals × 4,000 rows plus NYU-21 × 3,000 rows. The independent direct-byte audit uses 247 session fragments, with 63,418 Parquet rows and 35,582 legacy NPY rows. It opens no SWC_007, external, or later source outcomes. The primary frozen reader and scoring code remain unchanged.

All 97,677 responding trials with nonzero signed contrast obey the native IBL convention: choice +1 is left, choice −1 is right, and correctness is choice equal to the negative stimulus sign. This agrees with actual feedbackType > 0 on every such row. There are zero discrepancies in either storage format. All 1,036 omissions have unrewarded feedback. Both formats use exactly −1/0/+1 for choice and −1/+1 for feedback. Zero-contrast trials are excluded from the sign-versus-feedback check because their rewarded hidden side cannot be recovered from zero signed contrast alone.

All intervals are finite and have end ≥ start. Starts and ends never decrease within a session; no adjacent trial pair duplicates both start and end. Each session identifier occurs only once in the reconstructed chronology. The concatenation preserves the indexed date/session-number order, with no cross-session timestamp sorting. Every saved prefix contrast/choice/feedback/interval array and prefix session-start flag matches the original bytes exactly. Every future boundary vector used by all three forecast models also matches the independently reconstructed session concatenation exactly. All 222 between-session boundaries contain the expected clock reset. These resets are handled at the actual session boundaries, never as within-session reversals.

The result rules out a native-choice sign inversion, storage-format feedback reversal, rewarded-omission recoding, duplicate session assembly, or misplaced clock reset as the explanation for the decisive source score. It does not certify complete biological first exposure, raw acquisition clock provenance, or the learning rule itself.

`SEMANTIC_AUDIT.json` contains per-format counts, per-session checks, exact prefix/boundary comparisons, source-result hash and audit-code hash. `SEMANTIC_AUDIT.log` preserves the concise execution result. The script appends same-cap exposure records before every animal read.

From repository root, after the recorded source release:

```sh
campaigns/learning_rule_transport_2026-10-28/.modelenv/bin/python campaigns/population_learning_transport_2026-10-28/artifacts/coverage/SEMANTIC_AUDIT.py
```
