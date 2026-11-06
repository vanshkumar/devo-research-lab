# Independent prospective source simulation replay

2026-10-28. All six SHA256-first saved source prefixes were replayed after the lead released the complete `SOURCE_FORECASTS.json`. No raw new-source or external files and no scored future outcomes were read. The local EXPOSURE.jsonl records saved-prefix access and the manifest hash.

The independent implementation reconstructs seven prefix recurrences from the saved W0 (central plus/minus three finite-difference directions), computes likelihood Fisher information and propagates joint GLM/hidden covariance. After verifying the covariance, it uses the saved covariance for identical finite Monte Carlo orientation. The actor recurrence, fixed-policy sampler, side-specific exact 100% summaries and probes are independent of the production campaign code. Standard-policy trainer sampling is the pinned implementation, independently audited against original source methods in the policy audit.

All three frozen models were regenerated with 512 particles, the saved subject seed and saved session opportunities for each animal. The 18 forecast sample arrays, counts and curriculum-pool fractions match exactly. Every model's state checkpoints and latent probes agree to the small numerical differences below. This confirms correct simulation of the stated forecast recipe; it is not biological calibration or an independent empirical cohort.

Subjects: CSHL_012, SWC_022, NYU-12, SWC_020, SWC_011, SWC_017.

| Quantity | Maximum absolute difference |
| --- | ---: |
| samples | 0 |
| counts | 0 |
| weights | 1.722e-12 |
| hidden_final | 1.681e-12 |
| probe100 | 1.039e-13 |
| pool_fraction | 0 |
| Prefix weight_endpoint_error | 1.332e-15 |
| Prefix hidden_endpoint_error | 5.551e-16 |
| Prefix covariance_error | 9.663e-13 |
| Prefix factor_error | 0 |

Reproduction from repository root:

```sh
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 campaigns/learning_rule_transport_2026-10-28/.modelenv/bin/python campaigns/population_learning_transport_2026-10-28/code/production_replay.py --cohort source --limit 6
```

`SOURCE_RESULT.json` records every forecast hash/error, prefix uncertainty comparison, manifest hash and both independent code hashes. Replayed NPZs preserve reconstructed predictions. Standard output and empty stderr are retained as SOURCE_RUN.log and SOURCE_STDERR.log. No pinned code or forecast changed.

## Fixed-policy source swaps

A second post-freeze numerical audit replays the same six saved source-prefix states under the four-contrast fixed trainer. This is a simulation swap, not real external data. All 18 fixed-policy sample arrays, counts and pool fractions match exactly. The independent fixed sampler draws its own contrasts/sides in the production random-number order; binary rewards are reconstructed from each generated choice. The largest state/probe differences are samples=0, counts=0, weights=3.36e-12, hidden_final=1.68e-12, probe100=1.79e-13, pool_fraction=0. No raw new-source future or protected external value was read.

```sh
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 campaigns/learning_rule_transport_2026-10-28/.modelenv/bin/python campaigns/population_learning_transport_2026-10-28/artifacts/policy_audit/production_replay/FIXED_SWAP_REPLAY.py
```

FIXED_SWAP_RESULT.json, per-model NPZs, stdout and empty stderr preserve this audit. This script was added after the scientific freeze for independent numerical checking only; no scientific setting, primary forecast or frozen file changed.
