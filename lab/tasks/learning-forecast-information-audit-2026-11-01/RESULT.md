# Matched averaging preserves the observed-history/autonomous gap

2026-11-01. Completed postvalidation investigation of the already consumed24animals. Owner01a19700-04e5-7cb0-a307-916da01ed33b; PI01a196fa-cdbf-7783-9662-2028e1a839a4. Independent review is pending. No original forecast, endpoint, acceptance gate, frozen file or manuscript was changed.

**The known averaging difference does not explain the same-cohort contrast for this frozen recipe.** After matching the original512joint prefix-state draws and response-generation stream, conditional population-curve error is **0.6195pp**, versus the saved autonomous **6.9700pp**. The remaining difference is **6.3505pp**, paired-animal descriptive95%interval **[3.6220,8.4285]**. An analytic mixture control gives0.62808pp, almost identical to the saved central-state analytic0.62756pp. This calculation removes a specific numerical/averaging alternative; it does not establish a unique biological or feedback mechanism, autonomous forecast utility, or external transport.

## Same observations, law and endpoint

Only the original24full-horizon population animals' already consumed first4000rows each were returned:1000prefix plus3000future,96000total. Future scoring uses34378exact±100%opportunities,288animal/bin/side cells, six500-opportunity bins. Actual omissions remain failures in the corresponding denominators. Sides, animals and bins receive the original equal weights. All raw prefix arrays, observed targets/counts and session boundaries match the saved artifacts. NYU-21, SWC_007, later rows and every external/protected animal were excluded.

The saved checkpoint, prefix estimates, joint uncertainty map, omission process and primary session retention of one are unchanged. The original rank-three prefix uncertainty is reconstructed from saved w0/covariance/cap and exact frozen finite-difference propagation, without invoking the RNN's prefix optimizer. The existing last500prefix ridge-one logistic nuisance calculation is replayed solely inside the original fixed omission donor recipe; its mean omission probabilities match the historical conditional probabilities before the new future calculation. No new learner, initial-state optimization, hyperparameter choice, donor bank or nuisance recipe was fitted or selected.

For every conditional particle, the current response is predicted and sampled on the actual stimulus, then the recurrent state assimilates the actual choice and feedback. These current generated responses are used for scoring and do not drive the observed-history state update. All512particles retain equal weights. The original response RNG uses512response uniforms then512omission uniforms per opportunity, with the original seed+101. The autonomous comparison uses its existing saved generated-history samples. Its stimulus sequence and endpoint counts are generated; the conditional sequence and counts are observed. That difference is part of the information regime.

## Results

All errors below are percentage points; the first row is inherited evidence. The analytic mixture is the one additional averaging/sampling control.

| Information and averaging | Population curve MAE | Individual equal-side MAE | Individual side MAE |
|---|---:|---:|---:|
| Saved central-state conditional, analytic |0.62756|2.49657|3.66285|
| Matched512conditional, generated scoring responses |**0.61950**|**2.50554**|**3.67292**|
| Matched512conditional, analytic scoring control |0.62808|2.49601|3.66244|
| Saved512autonomous, generated histories/responses |**6.96999**|**9.02895**|**18.03943**|

The matched individual equal-side improvement is6.5234pp[5.4821,7.6910]. The population improvement remains3.4361–7.3867pp when each of the five laboratories is omitted in turn. These summaries describe the selected cohort; laboratories with one or two animals are not independent calibration studies.

The analytic conditional mixture differs from the saved central-state cohort forecast by at most0.00206pp in any bin. Its population MAE differs by0.000524pp. Current-response sampling changes the matched conditional population MAE by−0.00859pp and changes any cohort-bin prediction by at most0.04838pp. The primary matched gap is consequently close to the saved6.34243pp gap; the small difference is not a new learning improvement.

Finite-particle uncertainty is separate from animal uncertainty. Whole paired512particle paths, resampled within each fixed animal for2000draws, give a numerical95%percentile range **[6.2054,6.5065]pp** for the matched population gap. Conditional sampled cohort-bin standard errors are0.0257–0.0289pp; autonomous errors are0.0581–0.1279pp. These are numerical mixture diagnostics conditional on fixed histories and estimates, not biological confidence, coverage guarantees or fresh validation. The20000paired-animal intervals use the original seed20261029 and concern this selected animal/laboratory mixture.

## Verification, execution failure and resources

Reconstructed initial draws reproduce **all24original autonomous ensembles' samples and counts exactly**, with recorded weight/hidden comparisons also passing. This links the reconstructed uncertainty and omission recipes to the actual saved autonomous forecasts rather than merely their advertised metadata. All recorded direct scalar GRU/probability comparisons are below1e-10; omission-state invariance, identical-state/zero-uncertainty limits, scalar endpoint sums, finite probabilities and session/prefix/count checks pass. Both complete original strict freeze checks pass unchanged. Every relevant saved input pin is rechecked after the calculation.

Complete per-animal trial probabilities, generated scoring choices, actual inputs and per-particle side-cell predictions were saved before new cohort scores. `MATCHED_PREDICTIONS.npz` is pinned by the pre-score manifest. Large generated trial-file whole hashes are UNRUN; their bytes and side-array hashes are retained. `SAVED_SCORE_AUDIT.json` independently reconstructs180persisted scalar scores with direct scalar summation, maximum discrepancy7.905e-14pp, with native exit0. This is an additional within-author check, not the distinct independent review.

**The main native exit was120**, after all numerical outputs/checks were saved at12:16:35Z. The author's Tee logger was left installed after its log targets closed; interpreter-shutdown flushing failed. The executed source and failure are preserved. No science was rerun to hide that nonzero exit. The first numerical reconstruction, resource plan and saved-score audit exit0; `WARNINGS.json` is empty. See `EXECUTION_NOTES.md`. Treat the science-phase completion and unclean process shutdown separately.

First actual calculation12:07:10Z precedes its12:20:57Zdeadline; the design/resource plan was frozen by12:10:15Z before its12:30:57Zdeadline. Main calculation elapsed123.667seconds; fixed hard stop13:35:57Z was respected. Conservative whole-task read/hash/decode charge is **220000000bytes** against400000000, including both strict freeze passes, containing-file/decoded allowances, repeated reader metadata, saved-score verification and closeout margin. Peak main process RSS **369885184bytes**, below800000000. One scientific process/numerical thread at a time; ZEROpublicoperations/downloads/ingress; jobs0. Physical I/O and exact internal containing-Parquet-block decoding remain unknown. All earlier exposure/failures remain inherited.

## Implication and next decision

The existing manuscript's observed-history versus autonomous distinction survives matching the documented averaging and scoring-response treatment. The richer regime still jointly supplies adaptive stimuli, past choices, feedback and observed endpoint counts; this study does not isolate any one component or identify feedback-error accumulation as the cause. Primary autonomous forecasts still lose to growth and both original gates remain failed. The separate future-only retention diagnostic and original environmental/omission/selection limitations are unchanged. No new architecture, fit, target release, novelty or broad biological claim is earned.

A distinct fresh Sol/max independent review is justified. Its most consequential check is that the two regimes really share the original joint prefix particles, omission path and response RNG while retaining prediction-before-update, followed by an independently reconstructed matched score. It should challenge finite sampling and the observed-versus-generated count interpretation without adding a second learner/retention repair or extending observations. If verified, bank this narrow result and close this averaging explanation for this fixed comparison; do not spend another author run on logger cleanup or model tuning.

Proposed manuscript text, for PI consideration after review: “In a later postvalidation diagnostic, the original512-particle prefix uncertainty and generated-response averaging were matched across the two information regimes. Conditional population-curve error remained0.619pp against6.970ppautonomous (difference6.350pp; descriptive paired-animal95%interval3.622–8.429). The analytic conditional mixture gave0.628pp. Thus the previously documented averaging difference did not account for the contrast in this recipe; actual stimuli, choices and feedback remained jointly different, so no unique causal source was identified.” Preserve the old central-state diagnostic as its historical method.

All numerical outputs, input identities, design, resources and reproduction are indexed in [README.md](README.md). Same ACTIVE30minute PI heartbeat continues; this completed allocation does not stop the lab.
