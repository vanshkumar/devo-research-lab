# Development-only extraction controls and noise calibration

These controls use the frozen 10+10 development people. No primary-validation or external outcomes were copied or parsed. Script: `audits/source_measurement/development_controls.py`; numeric tables: `source_controls_condition_medians.csv`, `source_controls_people.csv`, `source_controls_extraction.csv`, `source_controls_noise.csv`, and `source_controls_summary.json`.

Within-person supplied Hand_Diff agrees with rebuilt adjacent Hand_dt differences to 0.000005 degrees maximum, with exactly matching interior missingness. The script separately records literal source complete-case summaries, boundary-correct interior summaries and randomized-within-portion summaries. This preserves the distinction between reproducing the source and using its preprocessing for the campaign.

The randomized-portion extraction control averages compensation-positive condition medians equally across signed ±4-degree current clamps. Spatial jumps are pooled equally across their signed cells, including jump-to/past in set A and jump-away/past in set B. These are known **current-input** effects, not the campaign's earlier-input propagation result. Intervals are person-level t intervals with 9 degrees of freedom per set.

| Readout difference | Set | Stationary current target | Spatial-jump current target | Jump minus stationary, 95% CI |
|---|---|---:|---:|---:|
| Exported unmasked endpoint | A | 1.879° | 1.367° | -0.512° [-1.022,-0.003] |
| Exported unmasked endpoint | B | 2.065° | 1.586° | -0.479° [-0.851,-0.107] |
| Rebuilt Hand_dt | A | 1.546° | 1.086° | -0.460° [-0.829,-0.092] |
| Rebuilt Hand_dt | B | 1.586° | 1.271° | -0.315° [-0.533,-0.097] |

Source detrending therefore changes response amplitude materially; the unmasked endpoint supports a real current-error response, and both exported endpoints retain the expected target-jump attenuation.

Recovery calibration descriptors (medians over people):

| Descriptor | A | B |
|---|---:|---:|
| Baseline linearly detrended robust SD | 2.455° | 2.272° |
| Baseline difference robust SD / sqrt(2) | 2.618° | 2.583° |
| Baseline detrended lag-one correlation | -0.167 | -0.217 |
| Main adjacent-difference robust SD | 3.497° | 3.164° |
| Main block-detrended robust SD | 3.249° | 3.294° |
| Main block-detrended lag-one correlation | 0.384 | 0.566 |
| RMS linear drift over a 180-trial portion | 4.607° | 2.825° |

Robust SD is 1.4826022 times median absolute deviation. Baseline feedback is veridical: its negative serial correlation can reflect corrective control and is not necessarily the main-phase motor-noise process. Main-phase differences and serial correlations contain true programmed-input effects and state dynamics; they must not be treated as pure observation noise. A total motor/observation SD around2.5° is empirically motivated, with heterogeneous noise and slow drift requiring stress tests.

The external Figure3 sign convention is established from code alone: `reachAngle=HandError` at line72, STL=next-current at line115, and positive-clamp STL is negated before combining signs at lines173–177 of the pinned analysis script. Thus `y=-HandError` aligns with primary `y=-Hand_raw`. Its jump-to definition is TargetJump=ClampAngle (lines60–61).

Recommended narrow transfer estimand: carry primary set A's absolute signed old-input modulation curve to Figure3's no-jump versus jump-to index comparison, conditioning on index clamp sign and full preceding/intervening input cells. Average the external comparison equally over current ±4-degree clamps and retain the primary prior-stationary ±4-degree half-contrast. This explicitly tests invariance of a target-event propagation effect when current clamp changes from0 to±4. Current-error learning can be estimated as nuisance; the carried modulation curve cannot be refitted and still count as a prediction. FalseStart can indicate absent target exposure, so a frozen omission sensitivity should distinguish assigned inputs from completed exposures.
