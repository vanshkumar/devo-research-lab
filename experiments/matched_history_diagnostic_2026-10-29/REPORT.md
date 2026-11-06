# Actual-history tracking remains accurate on the same new-source animals

Completed 2026-10-29. **Postvalidation exploratory diagnostic**, declared before this computation but after the prospective population result was known. It does not replace that result, change any gate or release protected data.

The frozen RNN tracks the same 24 animals' observed histories well: population mean-curve error is **0.628 percentage points**, compared with **6.970 pp** for its previously saved autonomous forecast and **2.278 pp** for saved growth. Thus the earlier comparison's old-cohort/new-cohort difference does not explain away the observed separation between conditional tracking and autonomous prediction.

## Same animals, observations and endpoint

All 24 full-horizon animals from the population campaign are included. Only their already-consumed first 4,000 rows were returned: a 1,000-opportunity prefix followed by 3,000 opportunities in six 500-trial bins. NYU-21, SWC_007, later rows and every external animal were excluded. The endpoint is the correct share at exactly ±100% contrast, separately calculated for each side and then equally averaged. Observed omissions count as failures. Animals and bins receive equal weight.

| Information regime | Population curve MAE | Individual equal-side curve MAE | Individual side-specific curve MAE |
| --- | ---: | ---: | ---: |
| RNN with actual intervening history | **0.628 pp** | **2.497 pp** | **3.663 pp** |
| Saved autonomous RNN | 6.970 pp | 9.029 pp | 18.039 pp |
| Saved autonomous growth | 2.278 pp | 6.967 pp | 17.879 pp |
| Saved prefix persistence | 6.388 pp | 8.522 pp | 18.898 pp |

Population MAE is the mean absolute error of the six cohort means. Individual equal-side MAE averages absolute errors over 24 animals × six bins after averaging the two sides within each cell. Side-specific MAE takes the absolute error before averaging sides; it therefore does not allow left/right errors to cancel. These are different summaries, and none should be substituted for the older campaign's >=50%-contrast endpoint.

The conditional-minus-autonomous improvement in population curve MAE is **6.342 pp**, descriptive paired-animal bootstrap 95% interval **[3.628, 8.434]**. Its individual equal-side MAE improvement is **6.532 pp [5.483, 7.708]**. Conditional tracking also beats saved growth descriptively: population improvement **1.651 pp [0.278, 4.194]** and individual improvement **4.470 pp [3.350, 5.663]**. These postvalidation intervals resample the selected 24-animal mixture; they do not establish arbitrary-laboratory generalization or fresh confirmation.

Observed cohort accuracy across bins is [51.54, 53.04, 55.76, 53.34, 55.58, 58.71]%. Conditional expected accuracy is [51.70, 53.25, 55.22, 54.72, 55.18, 57.63]%. Its scalar observed-minus-predicted bias is +0.047 pp. Conditional within-lab curve MAEs range from 0.666 to 1.809 pp across the five represented labs; the small groups are descriptive, not independent calibration studies.

## What the conditional calculation uses

The RNN starts from the exact saved prefix-calibrated coefficient vector and full recurrent memory. No RNN state optimization, learning-law fit, new baseline selection or autonomous rollout was performed. For every future trial, it receives the observed stimulus, predicts the response, and only then updates using the actual choice and feedback. Actual session-start indicators are retained. Its output is therefore an actual-history diagnostic, **not a prospective acquisition forecast**.

Conditional accuracy is calculated analytically from `(1-p_omit)*p_correct` on the actual exact100% trials. The omission probability is the mean of the original 512-particle prefix-derived growth/omission recipe, with the same subject seed+211 and subject-excluded development donors. Replaying that fixed recipe re-executes its existing last500 prefix nuisance-calibration calculation; it does not fit a new learner or use future observations for omission estimation. Current observed omissions remain failures in the scored target. Actual omitted responses also retain the RNN's existing skip-update semantics.

The conditional recurrence uses the saved central prefix state. The autonomous forecasts are the original 512-particle predictive mixtures, including their prefix uncertainty and generated choices. Consequently, this comparison is not an isolated manipulation of history information with all predictive averaging held identical. Analytic conditional probabilities also avoid fresh response-sampling noise. The result establishes good tracking on the same cohort under the explicitly richer information regime; it does not identify a unique cause of the autonomous miss.

As a separate responding-trial diagnostic, binary next-choice NLL is **0.53447 nats** per animal on average, versus **0.66882** for the original frozen prefix-persistence ensemble queried at the same observed stimuli. The gain is **0.13435 [0.10878, 0.16125]**. Both summaries use the same 71,351 responding trials; the pooled-trial values are 0.53402 and 0.66851. The persistence probabilities come directly from its saved constant weights, so no static fit was rerun. This NLL excludes omissions and is distinct from the omission-inclusive accuracy curves.

## Verification and access

- The original mixed Parquet/NPY reader was explicitly capped at 4,000 rows and restricted to the primary subject list. Its logging was redirected to this experiment. Network and full-subject loaders were disabled. The legacy event name `open_new_source_scored_outcomes` remains in the reader log, but the added analysis field and purpose identify this as reuse of already-consumed observations.
- All returned prefix values, future session boundaries, observed four-metric endpoints and counts match saved production artifacts exactly. All three original population MAEs reproduce within the asserted floating tolerance.
- Independently written scalar GRU equations reconstruct the first 32 predicted probabilities/transitions per animal. Predictions precede current response/feedback assimilation; maximum probability discrepancy is **2.22e-16**.
- All original frozen source/code/model/bank/protocol hashes pass before and after computation, without exclusions. Reused forecast, prefix, calibration and observed-artifact hashes also remain unchanged. Code and inputs are pinned in `RESULT.json` and `SOURCE_PINS.json`.
- The first attempt stopped before trial access because a contemporaneous edit to a frozen prior-work narrative failed its hash check. The owner restored the original file byte-exactly and retained the literature correction elsewhere. The unchanged strict checks then passed. `FIRST_ATTEMPT_STDERR.log` preserves the halt; the successful run's stderr is empty.
- The successful calculation took **2.80 seconds**. It returned 96,000 already-consumed source rows, opened no protected external data, and returned or summarized no later trial values. A Parquet library may internally decompress a containing block; the explicit query/array limits constrain returned rows. Only this experiment directory was written.

## Manuscript implication

The manuscript may now present a same-cohort, same-endpoint contrast: this frozen RNN closely tracks acquisition when supplied actual intervening histories, yet its original autonomous forecast overpredicts the same cohort and loses prospectively to growth. It should not claim that the diagnostic was prospectively frozen, that conditional tracking is a deployable acquisition forecast, or that feedback error accumulation alone caused the gap. Actual future adaptive stimuli, choices and rewards jointly provide information absent from the autonomous run. Session assumptions and the other original limitations remain relevant. This calculation makes no first-ever free-running-prediction or literature-priority claim.

## Reproduction

From the repository root:

```sh
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONDONTWRITEBYTECODE=1 campaigns/learning_rule_transport_2026-10-28/.modelenv/bin/python experiments/matched_history_diagnostic_2026-10-29/run.py
```

The command recomputes only this consumed-source diagnostic and writes within this directory. `PREDECLARATION.md` states the scope and estimators; `RESULT.json` contains full statistics and per-animal checks; `CURVES.npz` and per-animal conditional NPZs preserve the derived probabilities and endpoints. Existing campaign files remain authoritative and unchanged.
