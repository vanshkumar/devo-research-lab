# Same-cohort actual-history diagnostic

Declared 2026-10-29 before this diagnostic is computed. This is explicitly **postvalidation exploratory analysis of consumed observations**, not a new prospective test, gate amendment, model repair or external release condition.

## Question and permitted information

On exactly the 24 full-horizon subjects in the completed population campaign's SOURCE_RESULT.json, does the same frozen RNN track the actual future history substantially better than its previously saved autonomous forecast? The primary comparison uses the same exact ±100% contrast endpoint, 1,000-trial prefix and six subsequent 500-opportunity bins. NYU-21 and SWC_007 are excluded. No subject's rows at index 4,000 or later may be returned; no external prefix/outcome or other cohort is opened.

The conditional diagnostic receives each observed future stimulus and, only after predicting that trial's response, updates from its observed choice and feedback. It starts from the saved RNN prefix endpoint coefficients and full recurrent memory. It is an actual-history diagnostic, not an autonomous forecast or an isolated intervention on choices alone. The fixed RNN is never fitted. All prior gate decisions remain unchanged.

## Fixed calculations

1. Reuse the completed campaign's capped mixed-format original-byte reader with stop=4000. Redirect its exposure log into this experiment. Require the same 24 subjects and exactly 4000 rows each. Check saved prefix arrays, future session boundaries, observed endpoints and all side counts against saved production artifacts.
2. Run the frozen RNN sequence once per animal, starting from its saved endpoint/hidden memory and predicting before updating. Do not optimize the initial state or learning rule. Independently reconstruct the first 32 scalar GRU transitions and probabilities in direct equations.
3. For primary conditional curves, average expected correct probability `(1-p_omit)*p_correct` on the animal's actual exact100% trials, separately by side; then average sides equally. Omissions count as failures in the observed endpoint. `p_omit` is the mean of the original 512-particle growth/omission initialization, with the original subject seed+211 and donor exclusion. Re-evaluate only the unchanged existing last500 prefix nuisance-calibration recipe needed to reproduce omission donor matching; no new learner, baseline, hyperparameter or future fit is selected.
4. Compare conditional expected curves with the saved 512-particle autonomous RNN and growth means, against exactly the same observations. Report population six-bin curve MAE, animal/bin curve MAE, side-specific animal/bin MAE, scalar bias and paired differences. Report descriptive paired-animal percentile intervals using 20000 bootstrap draws, seed20261029; they concern this selected mixture and this postvalidation calculation, not arbitrary labs or new confirmation.
5. Additional diagnostic: responding-trial binary choice NLL for the conditional RNN versus the frozen prefix-persistence ensemble, using its saved weights and the same observed future stimuli. No static fit is rerun for this comparator. Report equal-animal and pooled-trial summaries. This binary NLL excludes omissions and is separate from the omission-inclusive primary curve.
6. Disable network and all full-subject loaders. Only this experiment directory may be written, including bytecode/Numba caches and exposure records. Pin all reused code/model/bank/freeze/forecast identities and verify unchanged source hashes after execution. No new autonomous rollouts are run.

## Interpretation

Good same-cohort conditional tracking would remove the simple old-cohort/new-cohort confound from the manuscript's information-regime comparison. It would not identify why autonomous forecasts differ: real future adaptive inputs and outcomes convey information absent from autonomous simulation. Poor same-cohort conditional tracking would require weakening the manuscript's matched-regime claim. Either outcome is retained without tuning, additional animals or a replacement gate.
