# Independent estimator and development-extraction review

2026-10-28. Reviewed `experiments/analysis.py`, `protocol/INITIAL_DECISIONS.md`, `protocol/AMENDMENTS.md`, `protocol/split.json`, and development-only outputs. No validation or external outcome values were accessed. This review covers the candidate implementation before final recovery/freeze; it does not certify an empirical conclusion or final validation code not yet written.

## Decision

The development primary statistic is correctly implemented and independently reproduced from original CSV bytes. The fixed half-contrast, person/block fixed-effect span, cluster score covariance, and cross-horizon scalar aggregation are algebraically sound. Initial prediction-model restriction was too permissive for its intended label; the lead corrected it during this review. Remaining requirements are calibrated inference with ten people per set, clear treatment of prediction versus validation refitting, and a small degrees-of-freedom correction when combining sets.

## Independent original-byte reconstruction

`audits/independent_extraction/reconstruct.py` reads original source CSVs, selects development participant IDs before accessing `Hand_raw`, constructs chronological events independently, and estimates a direct full-design least-squares regression by SVD. It imports no lead analysis code. It uses an alternative fixed-effect parameterization: an intercept and linear slope for every person/block, omitting the lead's shared block effects plus participant sum-contrast coding. The resulting column space is identical; the computation does not rely on the lead's QR nuisance residualization.

| Quantity | Independent result | Absolute difference from lead |
|---|---:|---:|
| Equal-set primary scalar | −0.11258452284355366° | 9.02e−16° |
| Primary scalar SE | 0.20491475624582373° | 2.78e−16° |
| Maximum of ten individual lag-effect differences | — | 2.72e−15° |
| Maximum of all 90 prior-cell × index-event coefficients | — | 1.53e−14° |

Set A scalar is −0.0173420101°, SE 0.335505267°. Set B is −0.207827036°, SE 0.235364494°. These are development estimates, not validation findings. The lead's then-current combined 95% interval is [−0.543094451°, +0.317925405°]. It does not establish either a nonzero effect or ±0.2° equivalence.

There are 2,076 eligible development events in A and 2,060 in B at each main horizon. No eligible development event is excluded by the `Hand_raw` nonfinite/90-degree rule. Full designs have rank 166, 174, 182, 190 and 198 at horizons 1–5 in each set, with full-design condition numbers about 104–137. No rank deficiency was found. A fixed-effect change of basis can change condition numbers, so these values should not be directly compared with the input-only 13-column preflight condition number.

Source hashes, IDs, individual lag results, all cell-event coefficients, curve covariance and comparison hashes are saved in `audits/independent_extraction/development_Hand_raw_change_all.json`. The inspected lead result's SHA256 is `449f0519cb1c02b75255a6e75bf882be14e62dec28ee2422f655e7e1e0128289`; the code hash recorded at independent completion is `3082148e804b9c67d97016f614a3fc42250c821a6bcff471414f914821a129e5`. Subsequent lead changes require a new comparison record rather than treating this hash as a final freeze.

## Items checked

| Item | Assessment |
|---|---|
| Chronology | Full `TN=1...824` arrays asserted. Index locations 20–174 inside each 180-trial randomized portion preserve all 20 past nuisance inputs and five future endpoints; terminal probes are excluded. |
| Primary contrast | Nine prior-cell × centered-event coefficients; fixed `.5*gamma[(+4,0)]-.5*gamma[(-4,0)]` is exactly the intended signed half-contrast with prior target stationary. |
| Event centering | `J−2/3` is a harmless reparameterization because the model has a saturated prior-cell main-effect basis. It does not assume event probability is exactly 2/3 within every local context for regression fitting, and it is not a randomization test. |
| Target-direction nuisance | Index signed jump and its prior-cell interactions allow distinct signed-direction associations while the primary coefficients describe the direction-averaged event effect. |
| Marginal secondary contrast | Weights `c/4/6` correctly give half the difference between the average of three +4 cells and the average of three −4 cells. In set A this remains a compound clamp/target-history contrast. |
| Pretreatment subtraction | Future endpoint minus fixed mean of five pre-index endpoints is implemented consistently; supplied `Hand_Diff` is not used. |
| Nuisance input histories | Saturated lag-1–5 input cells, two weighted lag-6–20 cell tails, and future/current input-cell indicators are present. They are model assumptions, not a guarantee against every slower/nonlinear history. |
| Participant variation | Participant/block level and linear drift vary freely. Cluster covariance admits within-person dependence and heterogeneity. Input-response slopes are pooled; heterogeneity in those slopes must be included in recovery. The estimator is not the arithmetic mean of independently estimated person effects. |
| Main/sensitivity eligibility | Main horizons share the same finite future window and fixed five-preceding-endpoint requirement. Stationary-readout eligibility may differ by horizon; cluster score columns retain the same person order and therefore remain alignable. |
| Cluster covariance | Lead uses the Frisch–Waugh–Lovell interaction influence operator, sums residual scores by person, and applies `G/(G−1)*(n−1)/(n−p)`. This matches direct full-design CR1 sandwich covariance. |
| Scalar covariance | Summing cross-lag person scores and taking `sqrt(mean(curve_covariance))` gives the SE of the equal five-lag mean. It correctly retains overlap/correlation among lag estimates. |
| Angular sign | Code uses `−Hand_raw`, so its declared interpretation relies on the source audit's same-geometry sign convention. Computational sign is internally consistent with a compensatory response to positive programmed clamp. Endpoint interpretation still permits online corrections. |

## Issues found and their status

### 1. Initial prediction restriction already allowed earlier-input propagation — corrected

The original `predict_fit` restricted model used the complete `N` matrix, including old-lag-2–5 × index-event terms and prior-cell × signed-index terms. That comparison only tested the added symmetric immediately preceding cell interaction. It could not be described as current-input-only versus propagation.

The lead changed prediction fitting during review: restricted features now exclude `older*` interactions and prior-cell × signed-index interactions, retain the index signed-jump main effect, and add `Z.sum(axis=1)` as the index-event main effect. The full design contains all of these restricted terms because the summed `Z` column is a linear combination of its nine prior-cell-event columns. The pair is nested. Both retain the same base input, readout and time nuisance terms; the additional terms represent history-dependent index effects.

The primary inference fit should continue including older-input interactions as nuisance; its scientifically fixed contrast is conditional on that flexible history. Do not conflate the inferential model's nuisance restriction with the separate predictive restricted model.

Even the corrected predictive pair is a finite distributed-lag observational comparison. A separate actual-schedule two-timescale/current-gain generator is needed to test whether truncation or representation makes an allowed mechanistic null look like propagation. The exact perceived-error alternative in `DESIGN_CHALLENGE.md` remains observationally equivalent to certain propagation laws.

### 2. Validation model refitting must not be called held-out prediction — pending final evaluator

The generic `run` function initially defaults to `save_predictions=True`, and its CLI can run `--part validation`. That execution re-estimates regression coefficients and writes them to a file named `..._predictions.json`. A reserved-data re-estimation of the **fixed observable contrast** is legitimate and planned, but those newly fitted coefficients are not held-out predictions.

The lead acknowledged this and plans validation execution with `save_predictions=False`, plus an explicit evaluator that loads frozen development coefficients. Verify that final evaluator and saved freeze hashes before release. It should apply the same input feature ordering, baseline subtraction, endpoint sign and eligibility rule, form both forecasts without validation fitting, and report paired prediction-loss differences by person. If a future endpoint is predicted by adding the observed five-pretrial baseline to the predicted change, state clearly that this is a frozen conditional forecast using past outcomes, not a wholly stimulus-only forecast.

A small guard improvement is warranted: `load(part='all_inputs', inputs_only=False)` currently bypasses the validation check because the guard tests only `part=='validation'`. No such outcome access was observed in this audit. Assert that `all_inputs` requires `inputs_only=True` to prevent accidental exposure in recovery code.

### 3. Combined-set degrees of freedom — small correction recommended

The standard error for the equal-set average is correct: `sqrt(SE_A^2+SE_B^2)/2`. Automatically setting the t reference degrees of freedom to `G_A+G_B−2` assumes more common variance information than is present when the sets have separate clustered variance estimates. Use a Welch–Satterthwaite reference,

`df = (v_A+v_B)^2 / [v_A^2/(G_A−1)+v_B^2/(G_B−1)]`, where `v_s=SE_s^2/4`,

or a conservative minimum cluster df. In development, Welch df is 16.1313 instead of 18. The resulting 95% interval is [−0.546697323°, +0.321528277°]. This changes no substantive conclusion. Freeze the rule before validation and use it in recovery.

### 4. Small-cluster influence and uncertainty — recovery is essential

There are only ten people per set in development and ten reserved per set. The largest person's contribution to estimated scalar variance is 48.9% in A and 43.4% in B. This is not evidence of a data error, but it shows why reach-count asymptotics are inadequate. Recovery should include heterogeneous participant gains, drift and noise; report CI coverage and false positives for the exact CR1/t procedure. A leave-one-person-out sensitivity or appropriately implemented small-cluster/wild-bootstrap sensitivity can check whether a final conclusion depends on one participant. Do not select a favorable uncertainty method after observing validation.

### 5. Outcome-based exclusion — harmless in inspected main development, document later

Requiring all future endpoints to be finite and within 90 degrees is a complete-case selection based on post-index outcomes. It can in principle create event-dependent selection. Here it excludes zero primary development events, so it does not explain the development result. Save equivalent counts by source, input cell and index event at validation; preserve the fixed rule and report sensitivity if missingness is appreciable. The exported masked `Hand` sensitivity may have different selection properties; it should not be elevated over the unmasked endpoint merely because its result is narrower.

## Reproduction

```sh
.venv/bin/python campaigns/target_event_carryover_2026-10-28/audits/independent_extraction/reconstruct.py
```

The script supports `--level`, `--stationary`, and later `--part validation`; the latter asserts that the lead's validation release record exists. It never opens independent-laboratory files. As of this review, only the default development reconstruction has been run. Reserved and external outcomes remain sealed.

## Review follow-up before outcome release

Subsequent source inspection confirmed that the lead implemented the recommended Welch rule, automatically disables `save_predictions` when `part=='validation'`, and added `assert inputs_only` for `part=='all_inputs'`. These address issues 2–3's implementation hazards. The final frozen-coefficient evaluation remains a separate artifact to verify when available. The transfer compatibility calculation also now uses a variance-based df rather than a hard-coded 26.
