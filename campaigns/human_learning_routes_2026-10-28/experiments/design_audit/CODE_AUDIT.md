# Independent implementation audit before validation

2026-10-28. This audit used input-only arrays and `inputs/development_numeric.csv` for the41 development participants. It did not open the original full trial CSV or any validation response file. Model reviewed: `experiments/model.py`, SHA256 `b4226924dfe4702620c303642cb4988057d76a41d006d908023675b9a1e91a9f`. These findings apply to that version and the primary model configuration; later source changes require a rerun.

## Result

No outcome leakage was found in the later-trial feature construction. Independent explicit lag-weight sums matched all causal EWMA histories to floating precision. The tests also verified previous-choice extraction, prefix truncation, and invariance of trial317 prediction features to changes in trial317 and all later responses/feedback. Setting hidden probability values to NaN and hidden sides to an absurd value changed no predictor. First200 calibration summaries are prospective only for trials200 onward, as required by the protocol; early returned predictions must not be interpreted prospectively.

Both accounts have the same63 fixed-effect columns and five random coefficients per person, with the condition account adding exactly three condition×history columns (66 total fixed effects). Sensory/asymptote, time, response persistence and calibration covariates are identical. Both include a common association of calibration with history. New-person predictions integrate the same Gaussian residual distribution. The adaptation-group override changes only the final three columns.

The first audit caught a modest optimizer stopping issue: a second-start development fit declared success at maximum gradient0.00477. The model owner tightened `ftol` from1e-12 to1e-14 and added bounded warm restarts plus a gradient-based success criterion. Rerun results:

| Check | Shared | Condition |
|---|---:|---:|
| Primary fit maximum gradient | 0.0000505 | 0.0000387 |
| Second-start maximum gradient | 0.0002983 | 0.0000351 |
| Difference in objective across starts | 1.12e-10 | 3.64e-12 |
| Maximum predicted-probability difference | 1.71e-6 | 1.08e-6 |
| Maximum GH20 versus adaptive-quadrature error | 1.47e-8 | 5.87e-8 |

The default fitting procedure passed. No warning suppression was introduced. See `model_audit_results.json` for machine-readable evidence. Reproduce using `.venv/bin/python campaigns/human_learning_routes_2026-10-28/experiments/design_audit/audit_model.py`.

## What this does not validate

- The fitting criterion is penalized joint MAP, not integrated hierarchical likelihood. Fixed random-effect scales and shrinkage can affect the estimated condition contrast; held-out prediction and scientific recovery are necessary.
- Calibration covariates condition a population prediction. Integrating an unconditional Gaussian residual around that population prediction does not infer an individual posterior from the full calibration sequence. The two accounts use the same approximation, which limits the mechanistic interpretation rather than invalidating their comparison.
- Signed contrast categories flexibly represent the average sensory response and saturation but do not separately identify lapse rates, and the individual sensory residual is a common sign coefficient across nonzero contrasts. Recovery with heterogeneous sensory/lapse shapes and the frozen SD sensitivities is important.
- The code audit does not establish uncertainty coverage, power at the five-percentage-point margin, or absence of unmeasured assignment/protocol confounding.
- A bootstrap with duplicated people must preserve one prior penalty per resampled copy. Reusing an original ID while simply duplicating trial rows is not the same procedure.
- Only three complete stimulus schedules are reserved. Conditional participant-level precision does not imply precision for an unrestricted population of schedules.

Awaiting final recovery outputs, uncertainty implementation and validation scoring for an adversarial result audit. Passing these numerical and leakage checks is a necessary prerequisite, not the scientific conclusion.
