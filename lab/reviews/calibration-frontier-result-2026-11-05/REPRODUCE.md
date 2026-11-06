# Independent acquisition-forecast result review

Run from the repository root using the existing campaign Python3.12 environment. The review imports no main-author scoring, inference or simulator module. All writes are confined to this review directory; all empirical inputs are saved derived counts, authorized aggregate targets or existing access/summary records. No original trial/archive/protected data is opened by these commands. Rerunning is another charged read/calculation, not an exposure or resource reset.

Use this common command prefix:

```sh
env PYTHONDONTWRITEBYTECODE=1 OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1 campaigns/learning_rule_transport_2026-10-28/.modelenv/bin/python
```

Append the script and argument below. Each actual execution used that prefix and redirected stdout/stderr to its named `.log` in this review directory.

| Script and argument | Outputs / purpose |
|---|---|
| `independent.py fixed` | FIXED_CACHE, FIXED_RECONSTRUCTION, FIXED_RESOURCES: all64 fixed/stream/exact-prefix scores, original source-selection scores, primary bootstrap and diagnostic summaries |
| `controls.py` | INDEPENDENT_CONTROLS, CONTROL_RESOURCES: original seven known-law controls independently reconstructed, missingness enumeration and added joint-boundary/source/state cases |
| `one_active_boundary.py` | ONE_ACTIVE_BOUNDARY and resource receipt: PI-requested composite-null cases with one useful-benefit boundary active |
| `final_challenge.py fixed` | FIXED_FAMILY: early120-column fixed-condition/reference/numerical/interaction reconstruction |
| `source_batch.py 16` | Score completed source chunks0–15 once; cache metrics in source_independent/; SOURCE_BATCH_16_RESOURCES |
| `source_batch.py 24` | Score newly completed chunks16–23 once; reuse0–15; SOURCE_BATCH_24_RESOURCES |
| `final_challenge.py source` | Score24–31 once, reuse0–23 and independently assemble the complete frozen632-column family; SOURCE_FAMILY_PREAUTHOR, SOURCE_SCORE_CACHE and resource receipt |
| `source_falsification.py` | SOURCE_FALSIFICATION: original-condition headroom and same-draw strong ordinary explanation for the largest apparent GRU point gain |
| `refined_check.py` | Reconstruct the one prespecified1024-particle refinement from actual pooled counts, with original632 retained and augmented652; REFINED score cache/diagnostics/resources |
| `compare_refined.py` | Compare independent1024/additional512 scores and652 vectors/bands with actual author outputs, inspect refined calibration/integration summaries |
| `final_challenge.py final` | After actual final author RESULT, compare independent fixed/source scores and632 contribution vectors with saved author outputs, retaining independent results and final resource receipt |
| `resources.py` | Consolidate actual receipts, continuous elapsed time, preserved failures and separately labeled context/image/startup estimates |

For example:

```sh
env PYTHONDONTWRITEBYTECODE=1 OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1 campaigns/learning_rule_transport_2026-10-28/.modelenv/bin/python lab/reviews/calibration-frontier-result-2026-11-05/one_active_boundary.py > lab/reviews/calibration-frontier-result-2026-11-05/ONE_ACTIVE_BOUNDARY.log 2>&1
```

The source-falsification calculation was first executed as an inline Python command with exactly the saved script's arithmetic; the standalone file preserves that executable calculation. Its first relative-path receipt failure and the corrected execution are recorded separately. The initial controls version and its resource receipt are preserved as V1, with the corrected additional stationary-state case described in EXECUTION_NOTES. The external time-l wrapper failed after successful fixed science and was not used as a reason to repeat it.

The1024 check needs the original generated512 trajectories because MAE and empirical energy cannot be pooled by averaging old/new scores. Its one justified read of MAIN_COUNTS is separately charged; it never reconstructs original trial targets or reruns simulation. All source-draw counts are read only once by this review; subsequent source work uses owned score vectors.

All bands retain whole-animal pairing, the original40/24 strata/weights, the frozen linear10% score-margin contrast,2pp accuracy margin and bootstrap seeds. Original632, primary4, refined primary4 and supplemented652 are different reported scopes, not candidate pivots to select after seeing a pass. No controls or code agreement establish biological replication or exact nominal95% coverage.

Native creation/readback is GOAL_START; checkpoints preserve the same goal/accounting. Scientific resource receipts count explicit file bytes plus decoded array bytes. Continuous elapsed time includes waiting, separately from process wall and native goal time. Context/import/provider/physical-I/O uncertainty and all inherited lineage costs remain. Proposed project memory is supplied only in RESULT for PI integration.
