# Independent review reproduction

The fixed reassignment was specified before calculating its result. For each recorded `(lab, cohort)` pair in the released primary qualification, reassign the intact early forecast across that block by a uniform permutation. `cohort` is the frozen project grouping (`public_subject_aggregate` or `ASD_project`). Use the same permutation for recent100 and GRU and for both signs. Keep all 192 equally weighted. Uniform permutations allow fixed points, including the necessary fixed point in each singleton. This preserves the original empirical distributions, target pairs and group weights in every permutation. Compute the exact expectation from every forecast-to-target score in its block. Use the double-centered paired score-gap matrix for its exact permutation variance. This is one descriptive postvalidation calculation with fixed forecasts and fixed observations.

The reconstruction sorts qualified sessions by date, number and UUID, joins to the physical deposited identity runs, and independently counts observed correct choices for each sign of unit nominal contrast. It keeps the literal subtraction calculation for the affected-target sensitivity. Only the declared eight trial fields and permitted session identities are projected. Test the pinned forecast-boundary function by itself on reconstructed, amended and deliberately poisoned views, and compare with the actual stored prefix/allocation cache. The primary score code implements the mixed-state distance directly through sorted positive ratios and missing-state terms. It does not import the author simulator or score modules. Historical author outputs are comparators after reconstruction.

Use the existing campaign `.modelenv` Python and locally available DuckDB module. Run from repository root with `PYTHONDONTWRITEBYTECODE=1 OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1`. The chronology stage makes one local whole-body hash pass plus one projection pass. The score stage reads the saved forecast count chunks once. Reproduction is a new charged read of already consumed data and requires an applicable release. No network requests are needed.

The terminal successful commands were:

```sh
export PYTHONDONTWRITEBYTECODE=1 OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1
review_dir=lab/reviews/independent-confirmation-result-2026-11-05
review_python=campaigns/learning_rule_transport_2026-10-28/.modelenv/bin/python
"$review_python" "$review_dir/reconstruct.py" CHRONOLOGY_VERIFIED
"$review_python" "$review_dir/score_review.py"
```

The original failed chronology run used the default `CHRONOLOGY` tag and decoded the first NYU-02 body before stopping at a metadata key lookup. The corrected run reads its failed receipt for the prior charge. Its empty object ledger was retained under `CHRONOLOGY_INITIAL_DECODE.jsonl` because the exception occurred before the first ledger row. The failed run's resource receipt records the projection and read charges. The commands above create new files with exclusive receipts. A separately released replay uses a fresh sibling directory at the same depth, a copy of the exact scripts and failed receipt, and the replay's authorized elapsed boundary in `records.py`. Inspect the small saved reduction and JSON outputs directly for ordinary evidence collection. [Terminal jobs and charges](RESOURCES.json)

`RECONSTRUCTED_TARGETS.npz` contains the independently counted mapped and literal windows, the unit keys and labels. `REVIEW_REDUCTIONS.npz` stores the per-animal pooled and stream scores in the order V, U, MAE, paired D, batch U scores, and the blocked early cross-score matrices ordered recent100 then GRU. Cross-block entries are NaN by design. The matrix diagonals are the observed paired risks. The all-pairs mean of each within-block square, averaged using block sizes divided by 192, gives the reassigned risks. The JSON contains the frozen inference, the literal sensitivity, the source and calibration checks, and the complete reassignment decomposition. [Independent results](REVIEW_CALCULATION.json) · [Chronology and exposure](CHRONOLOGY_REVIEW.json)
