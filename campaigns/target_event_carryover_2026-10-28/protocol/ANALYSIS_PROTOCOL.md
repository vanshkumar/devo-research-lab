# Observable analysis specification (development stage; final hash freeze follows controls)

Date: 2026-10-28. The inputs-only split and A01 define the target before development carryover inspection. This document specifies the implemented analysis. All reserved and external outcomes remain sealed while this specification is tested on development and synthetic responses.

## Estimand and units

For a zero-clamp index trial t, contrast target-jump versus stationary target effects on y[t+h], h=1,…,5. At the preceding trial, compare c[t−1]=+4° and −4° with j[t−1]=0. Divide that difference of differences by two. Average the five signed lag contrasts equally, and average sets A/B equally. Positive means increased compensation to the earlier positive clamp; negative means decreased compensation. This is a signed half-contrast relative to the ±4 midpoint, not necessarily +4 versus zero under a nonlinear response.

Primary scalar practical margin ±0.2°. Full lag curve, later stationary-target readouts, set estimates, ordinary prior-clamp level response, relative ratio and uncertainty accompany it. The scalar may cancel a rebound, so scalar equivalence alone would not establish small effects at every lag. People are replication units. No automatic sign requirement.

## Endpoint, chronology, and inclusion

Use y=−Hand_raw, the exported unmasked endpoint angle. Do not call it acquisition-raw. Preserve all824 chronological records per person and key person by (source_file,SN). Index t is inside one of the four180-randomized-trial portions, local zero-based position20…174. Thus20 preceding and5 following input rows remain within the portion; deterministic terminal probes are excluded. Primary eligibility requires c[t]=0, allfive pre-index endpoints and allfive future endpoints finite and within±90°. No interpolation, row compaction, source Hand_Diff or movement/latency adjustment. The index endpoint y[t] is never subtracted or used as a memory state.

Primary dependent variable is y[t+h]−mean(y[t−1],…,y[t−5]), fixed five weights. Endpoint levels are a required sensitivity and the ordinary-response denominator. Other sensitivities: existing Hand missing mask, unspecified source Hand_dt transform (clearly labeled), and no-jump READOUT j[t+h]=0. Stationary readout does not imply stationary intervening trials or zero current readout clamp.

## Model and inference

Separate least-squares models for each set/horizon. Nine actual input-cell categories are defined from original schedule, never assumed Cartesian. Nuisance: input-cell indicators at t−1…t−5 and t+1…t+h; two normalized cell-history sums across lags6…20 with decay.8/.95; participant-by-portion intercept and linear drift; signed index jump and its previous-cell interactions; older signed clamps at lags2…5 interacted with index event. Target terms: complete nine previous-cell × [index jump−2/3] interactions. Primary contrast is half(+4,0 cell coefficient minus−4,0 cell coefficient). Marginal signed previous-clamp contrasts are secondary compound-input measures in A.

QR nuisance projection and unregularized target least squares; rank checked. CR1 participant-cluster covariance, factor G/(G−1)*(n−1)/(n−rank). Cross-lag covariance comes from the same participant scores; scalar SE uses the full five-by-five covariance. Set intervals use t(G−1). Equal-set interval uses Welch–Satterthwaite degrees of freedom. No trial-level independent-sample intervals or invented exact randomization test. Primary CI is95%; full-curve pointwise intervals are descriptive, not five independent confirmatory tests. A calibrated equivalence statement requires the entire scalar95%CI inside±0.2 and successful controls, a conservative criterion relative to90%TOST.

For ordinary prior-clamp response, use the level model, half-contrast of preceding stationary-target±4 cells with index event set to0. Relative effect is scalar/ordinary scalar; use joint participant score covariance and approximate clustered Fieller intervals with conservative minimum set cluster degrees of freedom (9) if the denominator is stable. Do not divide the change-score main effect.

## Reserved prediction

Development fits two common-stimulus/time predictive regressions, without participant-specific coefficients. Restricted model includes flexible past/current/intervening input-cell effects plus index event and signed event main effects; excludes all old-input × index-event interactions. Full model adds all such interactions. Both otherwise share basis and drift flexibility. Predict the same fixed change-score on reserved people with coefficients frozen on development. No validation gain/noise/retention fitting for these predictions. Report equal-set, participant-averaged MSE difference (restricted minus full), per-set paired-loss summaries and Welch uncertainty. Prediction is a separate check from re-estimation of the fixed observable contrast.

A matched two-timescale state model is an explicitly secondary efficiency/alternative-model challenge, fitted only on development and frozen separately before reserved evaluation. It cannot replace the primary contrast or its margin. Parameter retention is not the scientific endpoint.

## Recovery and interpretation

Actual schedules, not regenerated Bernoulli assignments. Current-gain-only, fixed two-state retention, direct online effects and current expression are nulls. Both retention signs, equivalent state-dependent perceived error, delayed expression and rebound are positive/challenge laws. Include correlated motor/observation noise, person heterogeneity, drift and omissions. Distinguish isolated impulse truth, realized-schedule counterfactual truth, and noiseless regression projection. Examine bias, coverage, false positives, sign errors and detection; do not call failure equivalence. Known-Gaussian oracle comparisons establish whether a failing estimator is discarding available information. Exact storage/perceived-error likelihood equivalence is a separate mechanistic limit.

## Independent laboratory

Use Figure3 only (18 people); Figure4 and optional210-person primary geometry remain unconsumed. The transfer prediction is the development setA prior-stationary-clamp lag curve, unchanged in degrees, extended to nonzero±4 index clamps with JumpTo versus NoJump. This is an explicit invariance hypothesis, not exact zero-clamp replication. Allother input conditions, including flicker and JumpAway, remain in the chronological nuisance basis; their coefficients are estimated solely to measure the external conditional contrast. The substantive interaction prediction is never refitted. This is a quantitative prediction of an observable contrast, not a prediction of every external endpoint.

External y=−HandError; same finite±90 bound and fixed five-pre-endpoint subtraction. Eligible index TrialNum124…898, j=0 or j=c; old clamps±4 with prior targetstationary define contrast. All20 earlier and5later inputs inside exposures104…903. Four200-exposure epochs serve only as drift basis, not assumed randomization blocks. Eight input cells; lag5/tail20 basis as primary; current clamp sign and clamp×indexevent terms allow flexible current-error effects; signed-current/index-event×priorcell terms allow direction differences. Full priorcell×indexevent target basis, event centered.5. Person-cluster covariance. Both allreadouts and stationaryreadouts. Frozen expected curve and uncertainty saved before release. Report independent measured curve and difference from prediction with both laboratories' participant uncertainty. Unsupported transport or wide compatibility is not confirmation.

## Prespecified influence diagnostic

Independent development audit found that individual people contribute up to49% of a set's estimated variance. For reserved primary data, report all leave-one-person-out scalar estimates (equal weight of sets retained), without using deletion to choose the final estimate or interval. Record inclusion counts and loss of events due to endpoint/missingness masks. This is an influence diagnostic, not another confirmatory test.

The pre-index mean itself is a fixed negative-control outcome. By linearity, subtract the change-model interaction and participant scores from the identical level-model interaction/scores. This diagnoses chance or unmodeled-history association of the later assigned event with pretreatment endpoints; it is not a causal effect on the past. Apply the same five-horizon aggregation and clustered interval, and report regardless of sign. This diagnostic was specified after development level/change results and before validation, and cannot replace the primary endpoint.
