# Independent original-byte source-score reconstruction

Completed 2026-10-28 America/New_York, after the lead saved the whole-cohort forecast manifest and completed the single frozen source score. This audit opens no external data and never opens SWC_007 values. It reconstructs all 24 primary animals' first 4,000 rows and NYU-21's first 3,000 rows directly from original Parquet columns or NPY slices, independently of mixed_reader.py, campaign.py, learning_models.py and score_campaign.py.

**Passed.** All observed endpoint values and denominators agree exactly.195 numeric comparisons—including the population means, animal/cluster intervals, laboratory and leave-lab-out biases, individual/population CRPS, paired baseline bootstrap intervals and final gate—agree within7.79e-15. The largest discrepancy is summation rounding in the independently implemented explicit-pair CRPS. All 4407 original raw-file SHA256 pins also verify. RECONSTRUCTED.npz preserves observed values, all numerators/denominators and forecast means; RESULT.json gives the full comparison trace and source/freeze hashes.

Native IBL choice coding is preserved: +1 left, −1 right, 0 omission. A stimulus counts only when the missing-side-as-zero signed contrast is exactly ±1 within 1e-9; .5 contrasts do not enter. An omission increments the side denominator and never its correct numerator. Correct side is opposite to signed contrast. Right-choice share and omission share use all 500 opportunities. No psychometric contrast transform changes endpoint eligibility.

The RNN predicts 61.63395% versus observed 54.66396%, yielding observed-minus-forecast bias −6.96999 pp. Its animal 90% interval is[−8.96821, −4.97177] pp; the five-lab cluster sensitivity gives[−11.07031, −2.86967] pp. The prespecified accuracy gate fails. These intervals support overprediction, but the animal 90% interval reaches just inside the −5 pp boundary: do not claim that the true bias is established to exceed 5 pp. The point six-bin MAE is 6.96999 pp, versus 2.27811 pp for growth. Paired RNN mean-curve MAE gain over growth is −4.69189 pp [95% bootstrap −5.66783, −2.84968]. Individual exact-100% CRPS is .05746239 RNN versus .04881489 growth. The original individual gate remains unearned, and this new source gate does not release external outcomes.

## Recorded audit-only repairs

The original frozen reconstruct_scores.py remains byte-identical. Before any audit trial values were read, the lead's release limited NYU-21 to its 1,000 prefix plus four complete 500-trial future bins. The frozen audit script would have requested 3,473 rows. An audit copy under this directory caps that request at 3,000 and adjusts only path constants for its relocated location. AMENDMENT.json contains the exact diff and hashes.

The first audit run then passed all numeric comparisons but stopped because the already recorded pre-scoring wrapper added a finite-subgroup check absent from the frozen audit's final dictionary. The audit copy now independently evaluates the same existing finite requirement. AMENDMENT_GUARD_ALIGNMENT.json records the exact diff and before/after hashes; run_attempt1.log preserves the stopped attempt. All real cells/subgroup estimates are finite, so this alignment changes no statistic or gate decision.

## Reproduction

From repository root, after the recorded lead source release:

```sh
campaigns/learning_rule_transport_2026-10-28/.modelenv/bin/python campaigns/population_learning_transport_2026-10-28/artifacts/coverage/reconstruction/reconstruct_scores_limited.py --released
```

This command verifies frozen inputs and saved forecast/result hashes before any trial value read, appends explicit per-animal reconstruction exposure events, and regenerates the comparison. It requires no network or new model fitting. It must not be used to broaden source/external access. The unmodified frozen code remains the historical source; this audit copy is the exact replay command for the final limited-access reconstruction.
