# Amendments and exposure ledger

## A01 — 2026-10-28, input/measurement audit before carryover effects
Source audit has inspected development-only algebra among exported columns, not carryover statistics; validation and external outcomes remain sealed. Set A's clamp/target cells are not Cartesian. Refine primary scalar to the half-difference between effects of prior +4° and −4° clamps **with stationary prior target**, using full prior-cell × index-event interactions. Equal mean of reaches t+1…t+5; equal weight of primary sets. The initial compound signed-input projection becomes secondary. Margin remains 0.2°.

Main outcome will subtract the fixed mean of endpoints t−1…t−5 from each future endpoint, for drift/noise reduction. This is a pretreatment contrast, not an estimate of memory state. Missing any of the five baseline endpoints makes that event unavailable; no shortened baseline. Raw endpoint-level sensitivity and level-based ordinary-response denominator are mandatory. Primary endpoint is compensation-positive negative of Hand_raw: the exported unmasked endpoint field, whose acquisition/export preprocessing is not supplied. Existing Hand mask and Hand_dt are sensitivities, not privileged truth. Rebuild chronology; never use supplied Hand_Diff.

Detailed controls/recovery design remains under development; no validation exposure permitted until final freeze.

## A02 — 2026-10-28, after development-only carryover and independent extraction
Primary development θ=−0.1126°, SE0.2049°; level sensitivity−0.1875°; no-jump-readout−0.0304°; source-mask−0.0704°. Ordinary level-based earlier-clamp response+0.7232°. These are exploratory estimates, not reserved tests. Independent full-design SVD reconstruction agrees within~1e−14. No primary or external validation outcomes inspected.

Use Welch–Satterthwaite df for equal-set pooling instead of automatic18; point estimates/SE unchanged. Reserved prediction must load development coefficients, never the contrast re-fit on reserved people. Correct the prediction restriction to remove *all* indexevent×oldinput terms, while retaining index event and signed-event main effects. This fixes the intended model comparison without changing the primary observable fit.

Actual-schedule recovery finds poor sensitivity for the robust sparse contrast despite high known-generator oracle discrimination. Initiate a single matched two-timescale state-model efficiency challenge on development and simulation, with its parameterization frozen before fitting and before any validation. It is secondary and may not replace the original scalar/margin. This is a principled response to demonstrated estimator inefficiency, not permission to select a new primary endpoint.

## A03 — 2026-10-28, secondary model efficiency challenge, validation still sealed
The matched one-fast-event/two-state model gives development θ≈+0.0245°. Its local clustered profile interval and200 whole-fit participant-bootstrap interval are narrow, but the slow retention lies about0.5estimatedSE below its upper bound, and28% of bootstrap fits hit that bound. Expanded actual-schedule controls reveal positive-boundary undercoverage and transient/rebound misspecification. These intervals cannot establish a general±0.2° bound.

An independent input-only expectation calculation shows a specific failure mechanism: colored noise changes the expected residual sum of squares after person-specific input gains are profiled. Equal-rank wrong retention parameters can fit enough extra noise to outweigh their genuine signal error; iid noise does not produce this advantage. This is an inference-procedure problem, not proof the empirical effect is nonzero or an accusation about published condition-average analyses.

A bounded same-family covariance-aware diagnostic is therefore authorized before validation: test known synthetic covariance first, and only then a development-main-residual calibration procedure with its own recovery. Baseline covariance is not silently substituted: measured baseline and main residual autocorrelation differ in sign, consistent with different feedback regimes. Keep primary scalar, margin, eligibility and held-out allocation unchanged. Record all attempted state procedures, preserving failed OLS controls. No effect margin or lag selection may be adjusted to rescue the model.

## A04 — final pre-validation decisions
All primary/transfer recovery and the single covariance-aware state repair are complete before reserved release. Primary level recovery improves SE about28% but remains weak at±0.2; retain the original change-score primary and required level sensitivity. The fixed-timescale slow-memory/strong-drift null does not inflate false positives materially.

The practical FGLS repair uses AR1 estimated from development restricted-model main residuals, frozen across both mean models. Empirical θ≈+.0332° remains a conditional model estimate. Full-procedure recovery gives91%,92%,93%coverage for null,+.2,−.2 and8/100,4/100 false-equivalence intervals at positive/negative boundaries. It does not earn a general equivalence claim. Retain and score both original OLS and repaired FGLS forecasts; do not choose one using validation.

Final evaluator corrections before release: fixed-source prediction-loss intervals use within-source participant variance with Welch df; relative effect uses approximate clustered Fieller with conservative minimum-set df9. All frozen-outcome loaders verify the freeze and file hashes. Independent source reconstruction is ready. Scientific plots will label pointwise lag intervals. These choices precede all reserved/external outcome access.
