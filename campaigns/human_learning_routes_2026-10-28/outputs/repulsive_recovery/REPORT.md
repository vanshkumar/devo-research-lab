# Supplementary recovery with repulsive shared history

2026-10-28. **Post-validation generator-adequacy audit.** This analysis was requested after the protected biological evaluation had been opened. It changes only a synthetic generator; it does not change the frozen models, split, target windows, metrics or human-data results. All400 outcome datasets here are simulated, with100 repetitions per condition and no nested effect-interval bootstrap.

## Why this additional check was necessary

The initial recovery family assigned positive shared coefficients to the medium/slow history traces: `[0, .35, .9]`. The fitted DEVELOPMENT shared model instead had coefficients `[+.7348223, −.3613247, −1.0621934]` on the2/8/32-trial traces, with previous-choice coefficient`−.1652657` and condition×previous-choice coefficient`−.1637856`. An adversarial audit identified this discrepancy. The original recovery rates therefore describe their specified generator and cannot be presented as empirical task power.

This single additional family uses those exact development coefficients as its shared history and response-persistence means. It retains the original simulator's participant and schedule heterogeneity, sensory/lapse/omission differences, early acquisition, common latent sensory–history relationship and nonstationarity. Its direct condition-history manipulations were recalibrated under this new baseline to approximately±5percentage points. The source is the already fitted `outputs/development/shared_tight.json`; its hash and exact selected coefficients are saved in the supplementary manifest. No new human-data fit was performed.

These changes orient the generator toward the observed direction. They do **not** establish that it is the participants' true generative process or turn the supplementary simulation into another withheld empirical test.

## Result

The shared null actually occupies the intended repulsive regime: its mean zero-contrast history contribution is **−8.83percentage points** when aligned with the old majority, and its corresponding old-majority choice probability is **42.52%** over offsets0–19. These are simulated standardized quantities.

| Synthetic condition | True effect, pp | Estimated effect, pp | Estimate SD, pp | Mean held-out log-score gain | Positive score interval /100 |
|---|---:|---:|---:|---:|---:|
| Shared common-law null |0.00|+0.65|1.80|−0.000201|1|
| Slow-history increase |+5.00|+4.44|1.63|+0.001636|44|
| Slow-history decrease |−5.02|−2.70|1.53|+0.001536|47|
| Fast-to-slow redistribution |+4.96|+4.63|1.64|+0.000727|23|

Effect units retain the frozen definition: change only the condition-history terms, hold nuisance traits and histories fixed, impose zero current contrast, align with the old majority and average the first20 later post-switch trials equally across reserved participants. The score is the frozen low-contrast, first30-trial held-out comparison. A positive score interval means its subject-bootstrap95% lower bound exceeds zero.

The evidence supports three conclusions:

1. The five-point discrimination limitation persists when shared history is repulsive. Detection remains below50% for each tested alternative, while the shared null produces one positive score interval in100 simulations.
2. A true negative five-point contrast is still estimated near−2.7points. Matching the direction of baseline history does not resolve the standardized-effect attenuation identified by the original recovery and oracle-calibration checks.
3. Exact power rates depend on the generator: negative-shift score detection changes from26% in the initial family to47% here. The other matched rates change from48% to44% for the positive slow shift and from18% to23% for redistribution. These conditional rates should not be promoted into a universal empirical task-power estimate.

This audit does not change the biological result and does not rescue±5-point equivalence. It strengthens the specific conclusion that the present frozen procedure has limited discrimination at that scale under more than one plausible history regime. It provides no new interval-coverage or strict-false-equivalence rate in the repulsive regime because nested bootstraps were not repeated here.

## Reproduction and provenance

From repository root:

```sh
.venv/bin/python campaigns/human_learning_routes_2026-10-28/experiments/repulsive_recovery.py --reps 100 --workers 2 --label reproduced
```

The new simulator is `experiments/repulsive_recovery.py`; the frozen primary modules are imported unchanged. The runner hashes `model.py`, `analysis.py` and `recovery.py` before and after the audit and verified equality. Every fit satisfied the numerical convergence criterion. Seeds start at`502610280`, with separate scenario blocks and independent calibration seeds.

`supplementary/manifest.json` records exact development anchors, input/split/source hashes, the synthetic injection calibrations and the post-validation status. `summary.json`, `replicates.csv`, participant score tables and realized-truth tables retain all results, including per-repetition zero-contrast old-majority probabilities, history contributions, accuracy and omissions. The audit is a bounded supplementary generator check; no primary-model retuning or new empirical validation is implied.
