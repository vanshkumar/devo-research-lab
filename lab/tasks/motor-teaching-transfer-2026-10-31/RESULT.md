# Motor teaching-error transfer: source-only result

**The consumed source experiments do not support one calibrated quantitative teaching-error rule without additional context and shape assumptions.** A matched4-degree target-to response ratio changes from0.890 in TsayA to0.343 in Al-Fawakhiri Figure3 after an additive endpoint-expression control. Figure4's42 individual-outcome records remain undecoded; no target score or transport success is claimed.

## What this run observed

All58 previously consumed source people were available: TsayA/B20each and Figure3's18. The decisive matched-geometry comparison uses TsayA20 versus Figure3_18. Each person is an independent analysis unit; files plus personIDs define identity. No baseline, terminal/cross-block transition or cross-person difference enters the current-response analysis. Exact retained counts are **14,318 TsayA,14,320 TsayB and13,204 Figure3 (41,842 total)**. No data-dependent smoothing defines the primary outcome.

| Source/control | TsayA jump-to/stationary ratio | Figure3 ratio | Figure3 minus TsayA |
|---|---:|---:|---:|
| Saturated current-input response |0.864 [0.750,0.987]|0.371 [0.140,0.666]|−0.493 [−0.756,−0.176]|
| Current plus next input-cell effect |0.890 [0.781,1.013]|0.343 [0.132,0.613]|−0.547 [−0.789,−0.257]|
| Source-style transformed-angle / literal-author-mask medians |0.846|0.304|−0.542 [−0.794,−0.239]|

Intervals are participant bootstraps conditional on these consumed archives and analysis choices. Their population coverage and laboratory variation are uncalibrated. This is retrospective source evidence, not an untouched cross-laboratory validation.

The source-normalized forecast also fails after granting both methods the same stationary-response calibration from the other17 Figure3 people. A fixed Tsay ratio predicts jump-to responses with MSE1.148degree², versus0.422 for a simple Figure3-specific intervention ratio fitted on the other17; gain0.725 [0.293,1.162]degree². That last interval is a fixed-fit bootstrap of paired losses and omits some source/training uncertainty. The aggregate stationary-calibrated residual is−0.900degrees [−1.611,−0.342]. See [ENDPOINT_CONTROL.json](ENDPOINT_CONTROL.json), including all18 predictions and losses.

The literal Tsay `SPEdisruptTElinear` functional form, calibrated on the two consumed Tsay sets, estimates sigma13.574degrees, jump gain0.950 and TE slope0.00969degree/degree. Three initializations reach SSE0.094648. Source bootstrap ranges are broad for sigma[10.845,31.819] and touch the gain/slope boundaries. With Figure3 stationary amplitude supplied, this prescription forecasts a0.887 jump-to/stationary ratio (bootstrap[0.780,0.957]), versus the measured0.343. This grants a favorable lab-specific amplitude calibration rather than demanding identical overall motor gain. The equation is taken from pinned author code; fitting these consumed source inputs is a new diagnostic, not a reconstruction of the authors' original broad-geometry fit. See [PRESCRIPTION_CHECK.json](PRESCRIPTION_CHECK.json).

## Strongest contrary checks

An endpoint can contain a transient input-dependent expression term. We therefore fit each person's full current and next input cells separately:

`DeltaH = intercept + A(current cell) + B(next cell)`.

Under the explicit additive observation model `H_t = state_t + E(input_t)`, current effects have the form`U−E` and next effects`E`; odd signed contrasts of`A+B` cancel arbitrary additive cell-specific endpoint expression. This leaves the ratio mismatch at least as large. A synthetic control on the actual source cell supports recovers contrasts with additive endpoint perturbations approaching3degrees to7.55e−15. The actual fits have full identifiable current/next design rank and maximum normal-equation residual4.39e−11. This does **not** exclude state-dependent/nonadditive endpoint effects, perceived-goal changes, history dependence or other protocol differences.

Raw means, raw medians, the Tsay original Hand mask, within-person Hand_dt transitions, boundary-safe supplied Hand_Diff and both literal/intended external outlier masks retain the mismatch. The supplied difference is only a control: it agrees with boundary-safe Hand_dt differences to5e−6, and its known cross-person contamination remains excluded. No preprocessing variant is promoted because it is favorable. See [MEASUREMENT_SENSITIVITY.json](MEASUREMENT_SENSITIVITY.json).

The initial finite source run emitted known-environment matmul warnings. Explicit finite einsum contractions produce the same coefficients, forecasts and losses (maximum difference0), with no repeated warnings. The first output is retained, and every pass is charged. TsayB's success coefficient is explicitly unidentified because that regressor is zero; its minimum-norm zero is not evidence of no success effect.

## Why Figure4 stayed masked

Every nonzero consumed source clamp is4degrees. Figure4 has1.75,3.5,5.25,7,8.75,10.5degrees and no exact magnitude overlap. Three odd, monotone, saturating response curves coincide exactly on all source inputs yet differ by1.3506source-response units at10.5degrees. The published function accepts an empirical sensory response independently for each clamp; the consumed subset does not supply the six new amplitudes.

There is also no stationary large-target hit manipulation in the consumed sources. Adding its signed feature leaves source design rank4unchanged, whereas the Figure4 input design increases from rank2to3; the feature is nonzero on12,096Figure4 Hit exposures. Two explicit target-size extensions of the same source fit—Hit follows Miss, or Hit follows Jump-To—have exactly identical source predictions and different target predictions. All108 shape/gate/condition witness rows are saved, unscored, in [SOURCE_COMPATIBLE_TARGET_WITNESSES.csv](SOURCE_COMPATIBLE_TARGET_WITNESSES.csv). Their purpose is identification, not a model tournament.

**This is not a proof that every normalized transport hypothesis is impossible.** A multiplicative success-gain rule calibrated on Figure3 alone could be frozen and tested. It would add outcome/measurement invariance assumptions, and the publication-level size/jump discrepancy is already known. This block therefore retains the individual records instead of selecting such assumptions after reading their published answer. [SOURCE_ONLY_PROTOCOL.md](SOURCE_ONLY_PROTOCOL.md) and the immutable [SOURCE_ONLY_FREEZE.json](SOURCE_ONLY_FREEZE.json) explicitly do not release outcomes. [SUPPORT_WITNESS.json](SUPPORT_WITNESS.json) verifies the frozen calculation and records every Figure4 input-only ID.

## Prior knowledge, inference and allocation

[Kim2019](https://elifesciences.org/articles/39882) already formalizes separate outcome gains on updating/retention. [Tsay2022](https://journals.plos.org/ploscompbiol/article?id=10.1371/journal.pcbi.1010005) combines target-motion attenuation and task error; the pinned code supplies the tested prescription. [Al-Fawakhiri2023](https://doi.org/10.1152/jn.00061.2023) already reports unequal size/jump effects. No novelty is claimed for those mechanisms or discrepancy.

This run adds the quantitative matched-source failure, its measurement controls and executable source-compatible prediction alternatives. They justify withholding confidence in an intervention-independent quantitative coefficient. Timing/instruction/salience, preprocessing provenance and perceived-goal changes remain possible explanations; these data do not identify a unique cause or imply absent implicit adaptation. The additive control is a diagnostic, not a return to the parked carryover/storage fitting program.

**Recommendation:** independently review this source failure and support witness, bank the finite result, and reallocate rather than repair the held experiment by selecting a sensory curve, size gate or source cohort. A future restricted normalized test would require a separately motivated scientific claim beyond the already reported discrepancy. No collection recommendation, correspondence or successor experiment was initiated.

## Preservation and execution

Sources stay read-only and byte-pinned. Figure4 individual HandAngle/HandError/MT/RT/behavioral flags were discarded before conversion; all42 input-only IDs and36,288exposures are recorded. Optional210-person geometry outcomes stay CLOSED. Public paper summaries and all old scientific exposures/failures remain exposed. No other branch or protected target was opened.

Authoritative [RESOURCES.json](RESOURCES.json):400,000,000conservatively charged additional scientific read/decode/hash bytes,2,000,000charged ingress bytes,6logical public operations, peak recorded successful RSS87,834,624bytes, one sequential scientific process/numerical thread and jobs0. Historical motor bytes are inherited separately, never reset to zero. [EXPOSURE.json](EXPOSURE.json), [SOURCE_MANIFEST.json](SOURCE_MANIFEST.json), [VERIFICATION.json](VERIFICATION.json) and [README.md](README.md) give exact details and reproduction. Full raw replay is supplied but was not run again inside this tranche.
