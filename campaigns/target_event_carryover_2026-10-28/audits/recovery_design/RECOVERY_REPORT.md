# Recovery and discrimination results

2026-10-28. Final inference uses Welch–Satterthwaite degrees of freedom across the two independent sets, each with ten person clusters. All 3,900 simulations used **reserved input sequences only**. No empirical reserved or external outcome was accessed. Prior fixed-df results are preserved in `outputs/recovery_df18/`; estimates and standard errors are unchanged by the interval amendment.

## Result

The robust primary observable estimator has approximately calibrated intervals in the tested challenges but insufficient sensitivity to a 0.2° mean modulation. At actual-schedule physical effects of approximately −0.2° and +0.2°, zero was excluded in 17.7% and 11.0% of simulations, respectively. No simulation in any scenario produced an interval wholly inside ±0.2°. A null empirical result from this estimator therefore cannot support the prespecified equivalence claim.

This is an estimator/design tradeoff under the tested noise regime, **not a universal information limit**. An oracle using the correct generative mean and Gaussian noise law discriminates the same ±0.2° physical alternatives from fixed retention with >99.99% accuracy. Even after removing flexible current-cell learning, current-cell endpoint and block-drift directions, oracle accuracy remains >99.99% for the negative and >99.98% for the positive case. The lead therefore pursued a separately labeled low-dimensional efficiency repair.

By contrast, a fixed-retention model with state-dependent perceived-error correction produces exactly the same endpoints as retention modulation. Its oracle accuracy is 50%. This is an algebraic mechanistic ambiguity, distinct from the weak primary estimator. An unrestricted dynamic expression state supplies a second exact equivalence.

## Simulation controls

- 300 replicates per scenario; 20 people, actual reserved schedules, source-file/SN keys preserved.
- Endpoint noise SD 3° before the five-prior-reach mean is subtracted; development differenced residual SD ranged 2.79–3.09°. This is a conservative calibration, not a fitted full noise model.
- Independent motor and observation AR(1) components (variance shares .35/.65; correlations .70/.25), slow sinusoidal/linear drift, fast-state process noise SD .08°, lognormal gain variation with log SD .20 and noise variation with log SD .15.
- Fixed, independent 3% outcome omissions with seed194192; scheduled updates and original time gaps remain. This is conditional-on-mask recovery, not an outcome-dependent missingness analysis.
- Exact frozen-estimator scalar/cluster-score operators are verified against direct five-lag fitting; largest numerical discrepancy is 1.1e-16°.
- Physical truth is computed from explicit preceding-clamp/index-event counterfactuals and actual intervening transitions. Sixty full-chronology checks match the analytic formula within 2.78e−16°. Noiseless projection is separately evaluated with process, observation and drift noise removed.

## Numeric results

All angles are degrees. Coverage is for the physical scalar; rejection is two-sided exclusion of zero. Percentages have binomial uncertainty recorded in `summary.json`. The correctly specified linear controls are event-level regression controls, not physical reaching models.

| Scenario | Physical truth | Mean estimate | Noiseless projection | Mean SE | Coverage | Reject zero |
|---|---:|---:|---:|---:|---:|---:|
| two_timescale_null | +0.000 | -0.019 | -0.008 | 0.228 | 95.0% | 5.0% |
| gain_only_null | +0.000 | -0.016 | -0.009 | 0.230 | 97.0% | 3.0% |
| online_null | +0.000 | -0.019 | -0.006 | 0.228 | 93.7% | 6.3% |
| expression_current_positive | +0.000 | +0.023 | +0.016 | 0.234 | 93.3% | 6.7% |
| retention_negative | -0.158 | -0.213 | -0.192 | 0.233 | 95.0% | 13.0% |
| retention_positive | +0.257 | +0.282 | +0.262 | 0.230 | 95.0% | 22.7% |
| expression_next_positive | +0.079 | +0.114 | +0.099 | 0.229 | 94.0% | 8.3% |
| rebound_positive | +0.000 | -0.006 | +0.005 | 0.232 | 95.3% | 4.7% |
| actual_margin_negative | -0.200 | -0.221 | -0.241 | 0.235 | 94.3% | 17.7% |
| actual_margin_positive | +0.200 | +0.219 | +0.210 | 0.231 | 96.7% | 11.0% |
| specified_linear_0.0 | +0.000 | -0.002 | +0.000 | 0.231 | 95.0% | 5.0% |
| specified_linear_-0.2 | -0.200 | -0.214 | -0.200 | 0.228 | 95.7% | 12.7% |
| specified_linear_0.2 | +0.200 | +0.227 | +0.200 | 0.227 | 95.3% | 17.3% |

The four fixed-storage/direct-expression nulls have false-positive rates of 3.0–6.7%, with their 95% binomial intervals containing 5%. Physical-scalar coverage across all challenges is 93.3–97.0%, so the tested coverage discrepancies are modest at 300 replicates. Neither coverage nor low false positives supplies sensitivity: correctly specified ±0.2° regression controls also detect only 12.7–17.3%.

## Isolated impulse versus actual schedule

With the original generator, isolated ±0.2° effects become actual-schedule means −0.158° and +0.257° because subsequent events further attenuate or amplify the previous input. The estimator also differs from the physical effect: negative-case noiseless projection is −0.192°. This distinction is retained rather than calling the estimator output its own truth.

The additional `actual_margin` cases fix the scientific margin at ±0.2°. Fast gain was set to .90° (slow gain .20°) to permit a −0.2° actual-schedule effect without a sign-reversing transition; the isolated input effect was solved before simulation. The negative and positive isolated reference values are -0.246849° and +0.171650°. Participant gain variation then produces small replicate variation about the prescribed population/reference effect. These additional cases supplement the original scenarios; they do not overwrite them or change the practical threshold.

## Oracle and strongest alternative

Known Gaussian noise uses the same 3° endpoint SD and the two AR components; process noise is set to zero for the oracle, and drift is known absent. Available main-trial endpoints retain their original time gaps. The conditional means and participant parameters are known. Thus oracle results are optimistic information checks for stipulated model pairs, not power estimates for human data or a validation of those models.

| Pair | Oracle accuracy | After nuisance projection |
|---|---:|---:|
| fixed_vs_negative | 0.99992838 | 0.99980932 |
| fixed_vs_positive | 1.00000000 | 0.99999994 |
| negative_retention_vs_transient | 0.99091315 | 0.98745513 |
| positive_retention_vs_transient | 0.99999900 | 0.99998604 |
| positive_retention_vs_rebound | 1.00000000 | 1.00000000 |
| retention_vs_perceived_error | 0.50000000 | 0.50000000 |
| fixed_vs_actual_minus02 | 0.99999688 | 0.99998737 |
| fixed_vs_actual_plus02 | 0.99998560 | 0.99991059 |

The nuisance projection spans free cell-specific gains at two fixed timescales, direct current-cell endpoint effects, and participant/block intercepts and linear drift. It does not make unknown time constants, non-Gaussian noise or readout mechanism known. The exact perceived-error equivalence survives all such projections because its mean difference is zero.

## Reproduction

```sh
.venv/bin/python campaigns/target_event_carryover_2026-10-28/audits/recovery_design/check_generators.py
.venv/bin/python campaigns/target_event_carryover_2026-10-28/audits/recovery_design/physical_truth_check.py
.venv/bin/python campaigns/target_event_carryover_2026-10-28/experiments/recovery.py --reps 300
.venv/bin/python campaigns/target_event_carryover_2026-10-28/audits/recovery_design/oracle.py
.venv/bin/python campaigns/target_event_carryover_2026-10-28/audits/recovery_design/write_report.py
```

Final scenario arrays, summary JSON/CSV and oracle calculations are in `outputs/recovery/`; logs are in `logs/recovery.log` and `logs/recovery_oracle.log`. Analysis source hash and development calibration-source hash are included in `summary.json`. The 3,900-replicate run took 115.3 seconds in the existing workspace environment.
