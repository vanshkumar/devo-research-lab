# Bounded Atanas source audit - 2026-10-28

Read-only audit, not another pilot. Complete relevant pages were extracted with pypdf; PDF page 25 was rendered and visually checked. Source: Atanas et al. (2023), *Brain-wide representations of behavior spanning multiple timescales and states in C. elegans*, Cell 186, 4134-4151. Local source: sources/atanas2023.pdf. PDF page numbers below count the graphical abstract as page 1.

## Primary-source evidence locations and implications

| PDF / printed page | Location | Evidence / implication |
|---|---|---|
| 23 / e4 | Behavioral extraction methods | NIR behavior sampled at 20 Hz, averaged to confocal frames. Velocity, curvature and pumping are processed measurements; angular velocity uses a centered 15-second filter. |
| 25 / e6 | Trace extraction; Bleach correction | Background subtraction, calibration, interpolation and channel division precede a population-wide exponential bleach fit over the entire record. Whole-record preprocessing limits causal forecasting claims. |
| 25 / e6; 28 / e9 | Registration and GFP controls | Authors report 0.3% registration error and little behavioral encoding in GFP controls. These counter the claim that all shared activity is motion artifact; our subset does not independently repeat them. |
| 26 / e7; 34 / e15 | CePNEM; relative encoding strength | Encoding strengths and timescales are fitted model quantities, not independent neural ground truth. Autocorrelated residuals are explicitly modeled. |
| 13-14 / 4145-4146, Figure 6; 34 / e15 | Dynamic encoding analysis | Baseline encoding comparisons use separate recording halves. Encoding changes provide an alternative to stationary forecasting; prediction failure alone cannot distinguish them. |

Source-derived summary above is deliberately below 200 words; no long quotations. The following checks derive from local code/data, not the paper.

## Direct checks on the discovery JSON and campaign code

Inspected data/public/atanas_kim_2023-2022-06-14-01.json only: 109 neurons x 1,600 confocal frames. `trace_array` is per-neuron affine in `trace_original` to maximum absolute residual 3.55e-15. Means are zero to 1.85e-15; population SD is 0.999687451, consistent with unit sample SD. This supports full-record z-scoring for this file, not proof for every file. Neither field should be called raw photons.

An affine check is reproduced by fitting each row's slope from centered covariance divided by variance, fitting its intercept, and taking the maximum residual. In experiments/neural_dynamics/run.py, forecasts restandardize on training indices. Algebraically this cancels an earlier per-neuron affine normalization with positive scale; it cannot undo interpolation or whole-record nonlinear bleach correction. PCA/null analysis intentionally uses full-record normalization, so it is descriptive rather than forecasting.

`timestamp_confocal` has 1,600 entries and median spacing 0.600018875 seconds. `avg_timestep` is 0.010026589, so it must not be substituted for seconds per confocal frame. Root code uses confocal timestamps correctly. `velocity` also has 1,600 entries. `tau_vals` range from 0 to 86.21; their units or mapping to a particular fitted parameter were not independently traced through the exporter. Treat `tau_vals`, `rel_enc_str_*`, `neuron_categorization`, and `encoding_changing_neurons` as derived annotations, not labels for validating a new estimator without provenance checks.

## Audit limit

No raw-image reprocessing, motion-control replication, all-animal affine audit or exporter-code verification was performed. The paper's baseline encoding analyses are relevant background, not validation of our forecast/PCA estimands. No neural or biological conclusion is endorsed by this audit.
