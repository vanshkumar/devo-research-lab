# Independent scoring and uncertainty audit

2026-10-28. Reviewed `analysis.py` and `run_study.py` before validation opening. The executable check reads input-only schedules and creates explicitly synthetic alternating choices with deterministic omissions. It never reads raw or validation responses.

## Executed checks

`audit_analysis.py` independently reconstructs switch positions, old-majority sign, offsets and primary eligibility for all80 actual schedules/participant assignments. It confirms the independent opportunity counts in `input_coverage.csv`, tests omission masking, computes paired log scores with scalar Python arithmetic, and verifies equal participant aggregation. These checks passed.

Zero-current-contrast standardization removes all current contrast/sensory-time fixed columns and the random sensory-sign term while keeping evidence histories and calibration covariates fixed. The standardized adaptation effect equals the independently computed mean of each person's old-majority-aligned condition-history-only contrast. This passed.

The old-context diagnostic subtracts `H_at_switch × exp(-offset/tau)` from each history basis. Independent direct summation of evidence beginning at the switch matches the residual to4.5e-16. This is a correctly labeled oracle-aligned diagnostic of the model's feedback-trace component. It leaves previous-choice effects and calibration unchanged and is not an experimentally identified causal effect of old context.

Machine-readable hashes/results: `analysis_audit_results.json`. Reproduce: `.venv/bin/python campaigns/human_learning_routes_2026-10-28/experiments/design_audit/audit_analysis.py`.

## Issues reported to lead before freeze

1. `attach_split` initially returned as soon as a `schedule` column existed, even if `partition` was absent. Input-only arrays have precisely that schema; a synthetic scoring call failed with `KeyError: partition`. The primary numeric extraction path may not encounter it. Recommended fix: require both fields before returning, otherwise merge only missing fields and validate existing schedule labels. The audit fixture uses an explicit partition merge.
2. `curves()` initially lacked the protocol's promised10-trial preswitch descriptive reference.
3. `coding_audit()` initially classified every non-±1 choice as an omission. Recommended explicit validation of allowed omission codes rather than silently accepting arbitrary invalid values.
4. Failed bootstrap fits were initially recorded but still included in the interval. Require convergence or a documented retry/failure rule; a failed numerical fit cannot silently count as a successful statistical resample.

These are pre-validation findings. See later amendments and source hashes for resolution; this document preserves the initial audit record.

## Material uncertainty limitation

Development has14 schedule×condition cells, sizes1–4, totaling41 participants. The S07 taught cell is a singleton. Resampling separately within all14 cells omits singleton uncertainty and can substantially understate participant sampling variance. For an elementary equally weighted mean with common independent variance, the expected empirical bootstrap variance is scaled by `(41−14)/41 ≈ 0.659` relative to the true variance. That illustrative calculation does not give the exact bias for the nonlinear MAP contrast, but establishes why the concern is concrete. Labeling the interval conditional on finite schedules does not repair unobserved within-cell participant variation.

Recommended primary refit interval: resample development people within condition, preserving group counts and the observed universe of schedules while allowing sample schedule composition to vary. Retain fixed schedule×condition resampling as a sensitivity and provide schedule-resolved checks. If the fixed-cell interval is retained as primary, scientific recovery must demonstrate adequate coverage for that procedure before claiming equivalence. An interval from only the narrower method should not be selected because it fits the equivalence boundary.

The effect-refit bootstrap also fixes validation reference histories and calibration covariates. It therefore targets an effect standardized over those reference people/history realizations, conditional on that reference distribution. It does not capture full variation from new reference participants or new schedules. This is acceptable if stated, but cannot be presented as an unrestricted population bound.

Validation score bootstrap resamples paired whole-person scores with group and validation-stratum counts fixed. This supports uncertainty conditional on the fitted models and realized schedules. The additional schedule/participant bootstrap and leave-one-schedule summaries challenge sequence domination but have only three entirely unseen schedules. These qualifications should remain visible in the report even if the point estimate is compelling.

## Status

No scoring-mask, chronological information, or counterfactual-trace arithmetic error found. Uncertainty revisions and recovery coverage remain the substantive gate. No validation outcomes inspected.
