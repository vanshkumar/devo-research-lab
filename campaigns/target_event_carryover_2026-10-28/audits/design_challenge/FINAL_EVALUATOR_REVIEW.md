# Final evaluator, ratio, freeze and figure review

2026-10-28. Reviewed candidate `evaluate.py`, `ordinary_response.py`, `freeze.py`, `figures_tables.py`, and the in-progress report. Reserved and external outcomes were still sealed at review. No new empirical outcome analysis was performed. This is a code/method audit; numerical state-model adjudication is assigned elsewhere.

## Frozen prediction evaluation

The corrected development prediction fit and `prediction_evaluation` use matching feature arrays:

- Full prediction: `[N,Z]` times the frozen full coefficient vector.
- Restricted prediction: `[N[:,restricted_keep], sum(Z)]` times its frozen vector.
- `restricted_keep` excludes older-clamp × index-event and prior-cell × signed-index interaction features, while retaining current input and direct signed-index effects. The summed interaction column is the centered event main effect.

`prediction_evaluation` loads `protocol/PREDICTORS_all.json` or `PREDICTORS_stationary.json` and does **not** fit any validation coefficient. It builds outcomes as the same compensation-positive future endpoint minus the five-pretrial mean used in development. Positive reported gain means restricted MSE minus full MSE, hence improvement of the propagation model. Dimensions vary correctly with horizon and are separately frozen for each primary file/horizon/readout. The sorted input-cell ordering is deterministic and verified within each set; final hashes should protect this ordering against later code edits.

The zero-change comparator predicts the future endpoint by the mean of the five pre-index endpoints. It is a meaningful simple conditional forecast. Its addition before freeze avoids accepting an expensive model solely because it beats another poorly generalizing model. Report both model MSEs and this baseline; gain over the restricted model is not by itself evidence of better prediction than persistence. The forecast uses pre-index outcomes through this fixed baseline, so describe it as a frozen **conditional** forecast rather than entirely input-only forecasting.

Each person's MSE is first averaged equally over horizons, then each person receives equal weight. This handles repeated/overlapping event windows at the intended replication unit. The initial evaluator's interval treated all 20 persons as an unstratified sample. Since the scientific target fixes equal A/B weights, use separate per-set paired-loss means/variances and Welch combination, matching the observable effect. This recommendation was sent before freeze. It matters more if source sets have different loss variances; it does not change the point estimate with ten persons per set.

## Ordinary response and relative effect

The ordinary-response denominator correctly uses **endpoint levels**, not the pre-index-subtracted outcome. It computes the previous +4/−4 stationary-target half-contrast at a stationary zero-clamp index (`event−2/3 = −2/3`, signed index=0).

Let `W` map outcomes to the interaction coefficients and `w_N` represent the previous-cell nuisance half-contrast. The code's full contrast weight is

`w = w_N − (w_N Z) W − (2/3) v W`.

This is algebraically the nuisance coefficient contrast after subtracting `Z beta`, evaluated at the stationary index event. Its direct cluster scores use the full model residual and the same CR1 correction. Reference-cell coding causes no omitted constant because the +4/−4 contrast sums to zero.

The ratio numerator uses change-outcome scores, while the denominator uses level-outcome scores. Averaging each person's scores over horizons and summing their cross-products within set, then multiplying by the equal-set factor 1/4, is the correct cluster-sandwich cross-covariance. The differing outcome transformations do not invalidate the covariance; their shared people and trials are exactly why the cross-product is needed. Participant ordering is stable under the saved split.

The Fieller quadratic is correctly implemented:

`A = nu² − t² V(nu)`,

`B = −2 theta nu + 2 t² Cov(theta,nu)`,

`C = theta² − t² V(theta)`.

Bounded roots are returned when `A>0` and the discriminant is nonnegative. Returning no bounded interval otherwise is appropriate; it should be described as an unbounded/disjoint Fieller confidence set rather than silently suppressing denominator uncertainty. If an exactly zero denominator were encountered, avoid a division-by-zero exception and report the point ratio unavailable.

This is an **approximate clustered Fieller interval**, not an exact finite-sample t interval. The initial code chose the smaller of the two component Welch degrees of freedom, which is not guaranteed to be the df of every linear combination `theta−r*nu`. A simple prespecified conservative alternative is the minimum set cluster df (nine with this split), or explicit labeling of the existing approximation. This is a reporting/calibration issue; the coefficient/covariance algebra itself is correct.

## Freeze integrity

One concrete mutation-order bug was found: `freeze()` originally checked whether `FINAL_FREEZE.json` already existed **after** recomputing and writing both predictor files and the transfer prediction. A repeated call would change frozen artifacts and only then fail. Move the existence guard to the very beginning, before any write or development recomputation. The lead was notified before freeze.

Before opening outcomes or scoring predictions, verify the saved `FINAL_FREEZE.json` hashes, or have a release procedure explicitly check and record that verification. A release-file existence check alone does not establish that the model and analysis being run still match the frozen versions. A mismatch should require a documented amendment stating prior outcome exposure; it should not be silently ignored or fixed by rerunning the freeze over itself.

The freeze correctly copies newly recomputed development coefficients after the restriction fix and saves the source-A transfer curve without external calibration. It hashes the analysis, ordinary-response, evaluator and plotting scripts along with split, decisions, amendments, analysis protocol, frozen predictors and transfer prediction. Audit scripts are separate independent checks and need not become scientific model inputs, but should retain their own reproducible records.

## Figures, tables and report scope

Primary lag plot intervals correctly combine the two independent set covariance diagonals with equal weights and Welch df. The hard-coded divisor nine is valid for the frozen ten-per-set split; the final report should verify that every set still has ten contributing participants. Scalar intervals come from the saved covariance-aware five-lag summaries. The ±.2-degree band is placed on the scalar panel, not misused as a simultaneous bound on individual lags. Figure captions must state that lag bars are **pointwise 95% intervals**, not a simultaneous five-lag band.

The ordinary-response and external-transfer figures likewise use appropriate per-set/person t reference intervals. The ordinary figure title currently asserts that the earlier-error signal is present; a neutral title such as “Earlier-clamp response on stationary index trials” avoids prewriting what the validation result will show. Axis text should retain the method's signed half-contrast meaning, especially if “+4-degree contribution” is used as shorthand.

The combined 40-person estimate is correctly labeled descriptive, because development informed analysis choices. It is an equal four-stratum average, with covariance and Welch combination treating development/validation participants as distinct. It must not be called another untouched confirmation.

The report draft appropriately separates development evidence, pending reserved/external tests, observable propagation, and exact storage/perceived-error ambiguity. Its oracle discussion correctly distinguishes an inefficient robust estimator from an intrinsically uninformative dataset. Its transfer section correctly treats external nuisance fitting as measurement of a frozen target contrast, not refitting the predicted substantive effect. Preserve these distinctions in the completed report. No novelty, storage localization, reward specificity, or exact external zero-clamp replication claim is justified by the current measurement design.

## Remaining review actions

The lead should resolve the mutation-order guard and verify hashes at release/evaluation; document the prediction pooling and Fieller reference rule chosen before release; label pointwise intervals; then execute the reserved tests. Independent original-byte reconstruction is ready once release occurs. No methodological need to inspect reserved outcomes early was found.

## Pre-release resolution check

Subsequent source inspection confirmed the lead moved the no-overwrite guard to the start of `freeze()`, added `verify_release` to check both the freeze record hash and each frozen artifact before reserved loading, changed prediction-loss pooling to equal-set Welch summaries, and changed Fieller's reference to the minimum set cluster df with explicit approximate-interval wording. These resolve the main implementation recommendations above. The pointwise-interval caption and neutral ordinary-response title are presentation recommendations to carry into the final figures/report. No reserved outcomes were accessed for this follow-up check.
