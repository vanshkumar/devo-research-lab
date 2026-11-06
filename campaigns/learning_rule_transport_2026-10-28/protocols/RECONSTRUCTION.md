# Independent original-byte source reconstruction

2026-10-28. This reconstruction was authorized only after the scientific source-validation freeze. `FREEZE.json` SHA256 is `c0141244ac43d240f858956917e3b2b661c72a01a4bddbccdb3974a818b5741f`. Every source model, data index, trainer/score implementation and uncertainty configuration listed in that freeze was hash-verified unchanged before execution. No external animal's raw choice, reward, prefix or learning curve was opened.

## Independent paths and access boundary

`code/independent_reconstruction.py` imports none of the lead's `data_io`, `rollout`, `evaluation` or `learning_models` functions. It independently reads original public Parquet tables in indexed date/session-number order, with SQL limits giving at most the first 6,000 task rows per animal. Before every table read it verifies the local original object's byte size, published MD5 and pinned SHA256. It independently reconstructs session boundaries, signed contrasts, native choices, omissions and feedback. No processed trial NPZ is used as an input.

The reader rejects any subject outside the frozen source holdouts. It waits until all six autonomous forecast files, observed summaries and scoring products exist for that animal. `FORECAST_BEFORE_SCORE_AUDIT.json` independently checks the append-only ledger: every source animal's six forecasts were saved before its first whole-subject outcome load. The main scorer converts whole source tables after saving forecasts and then scores the requested first 5,000 future trials. This independent path opens only the first 6,000 original rows. No future outcomes enter an autonomous forecast in this reconstruction.

48 source animals have the 1,000-row prefix plus at least one 500-trial future bin; all 48 were reconstructed. All 54 originally allocated animals remain in `SOURCE_DISPOSITION.json`. The six shorter histories have metadata-only dispositions. There are 47 full 1,000-future-trial animals, 40 full primary 3,000-future-trial animals (21 animal holdout, 19 reserved-lab animals), and 35 full 5,000-future-trial animals. All 48 partial futures are separately retained. No success-based animal exclusion was introduced.

Original reads covered 518 source session tables, 22,409,202 original file bytes and 254,306 bounded original task rows. Per-table URLs/dataset UUIDs remain in the frozen index; query limits, session chronology, original hashes and paths are copied into `original_provenance/`. The previously resolved KS016 cache exception is a development animal and is not among these source holdouts.

## Targets and distributional scores reconstructed

High-contrast targets use `abs(contrastRight - contrastLeft) >= .5`, preserving the original missing-side convention. Left correctness is native choice +1, right correctness native choice -1; no-response choice 0 remains in both denominators as a failure. Right-choice share and omission share use all 500 task trials. Empty high-side cells remain missing. Counts and all target fractions match the lead's saved observed arrays exactly for every reconstructed animal.

Marginal CRPS is independently evaluated with explicit unordered pair distances:

`mean_i |sample_i - observation| - sum_{i<j}|sample_i-sample_j| / (N*(N-1))`.

This avoids the lead implementation's sorted-coefficient formula. Metric, bin and animal averaging, quantile coverage, interval width, high-contrast MAE and joint energy are independently implemented. All 1,728 autonomous/raw score rows (48 animals × six models × three horizons × two forecast versions) match the lead: maximum absolute CRPS difference `4.440892098500626e-16`; MAE, high-contrast MAE, coverage, width and energy differences are zero.

## Independent primary magnitudes

These are the frozen primary distributions (`samples_primary`), including each model's development-selected uncertainty amplitude. The unit of inference is an animal; there are 40 full primary animals.

| Model | CRPS | High-contrast MAE | 80% coverage, all metrics | 80% coverage, high contrasts | Mean 80% interval width |
|---|---:|---:|---:|---:|---:|
| DNNGLM32 | .080517 | 16.38 pp | 83.4% | 79.6% | 36.55 pp |
| DNNGLM16 | .079955 | 17.24 pp | 85.6% | 78.8% | 43.55 pp |
| Free-baseline REINFORCE | .082889 | 17.19 pp | 92.3% | 87.7% | 52.72 pp |
| Pure reward REINFORCE | .103005 | 20.48 pp | 70.1% | 61.0% | 32.28 pp |
| Empirical growth | .080975 | 16.28 pp | 86.4% | 81.3% | 38.82 pp |
| Full-prefix competence persistence | .104411 | 20.59 pp | 75.8% | 67.1% | 34.99 pp |

For the published-primary DNN32, growth-minus-model CRPS gain is `.000458`, animal-bootstrap 95% `[-.009719,.010584]`, or 0.565% relative improvement. High-contrast MAE worsens from 16.28 to 16.38 pp. The other candidates' mean CRPS gains over growth are `.001019` (DNN16), `−.001914` (free-baseline RL), and `−.022030` (pure reward RL). These calculations independently show no material overall improvement over growth under the frozen primary criterion; they do not establish equivalence of model classes or rule out every useful learning law.

Bootstrap replay uses 10,000 resamples, seed 891, with animal-holdout IDs alphabetically followed by lab-holdout IDs alphabetically. The exact 40-animal order, individual gains, ordinary 95% intervals and the frozen gate's `.00625` lower percentile are saved in `PAIRED_COMPARISONS.json`.

## Whole-laboratory localization

| Reserved source laboratory | Full-primary animals | DNN32 CRPS | Growth CRPS | DNN32 high-contrast MAE | Growth high-contrast MAE |
|---|---:|---:|---:|---:|---:|
| Hofer | 9 | .078132 | .077860 | 14.98 pp | 14.86 pp |
| Witten | 10 | .081659 | .088897 | 17.21 pp | 18.18 pp |
| Both reserved labs | 19 | .079988 | .083669 | 16.15 pp | 16.60 pp |

The direction differs by reserved laboratory. In the separate 21 unfamiliar-animal holdout, DNN32 CRPS is .080996 versus growth .078537; MAE is 16.58 versus 15.98 pp. `LAB_STRATA.json` retains every source lab/model result. Animal resampling does not turn two reserved laboratories into a precise estimate of arbitrary new-lab transport.

## Independent conditional recurrence and causality checks

For DNN32 and free-baseline REINFORCE, the reconstruction loads only the frozen parameter arrays and the saved prefix-calibrated starting weights. It independently executes the original 1,000 raw prefix rows, verifies the saved prefix endpoint, and then predicts each future trial before updating with that trial's native response, reward indicator and session-start input. The DNN uses the pinned contrast transform and its two rectified layers; RL uses its frozen reward/baseline update. Omissions skip the binary update. No lead model functions are imported.

Every prefix endpoint, future probability and future latent weight matches exactly in all 48 animals. The reconstructed sequential binary-response NLLs match exactly at every horizon. Flipping a current response and feedback cannot change that same trial's predicted probability in the independent recurrence; the numerical current-trial difference is zero. The actual preceding responses/rewards do affect later conditional states. This verifies causal teacher-input timing, rather than treating a software success flag as model reproduction.

Across the 40 full primary animals, conditional DNN32 NLL is `.527342` nats per responding choice and free-baseline RL NLL is `.530071`. Evaluating the existing frozen prefix-persistence point on the same future presented contrasts gives `.682517`. Conditional improvements are therefore `.155176` and `.152446` nats/response, respectively. The conditional sampled-curve high-contrast MAEs are 2.47 and 2.25 pp, versus autonomous 16.38 and 17.19 pp. Those sampled conditional curves fix the real future histories: their curve scores are diagnostics and are not autonomous joint predictive distributions. This distinction is central to interpretation.

## Artifacts and offline command

`INDEPENDENT_SCORES.json`, `INDEPENDENT_SUMMARY.json`, `CONDITIONAL_RECONSTRUCTION.json`, `LAB_STRATA.json`, `SOURCE_DISPOSITION.json`, `NUMERICAL_DIFFERENCES.json` and per-animal `records/` contain the full reconstruction. `original_targets/` retains the independently reconstructed original rows and summaries; `conditional_probabilities/` retains independent probabilities and weights. No model was fitted or selected by this module.

```sh
campaigns/learning_rule_transport_2026-10-28/.modelenv/bin/python \
  campaigns/learning_rule_transport_2026-10-28/code/independent_reconstruction.py --overwrite
```

The command is offline: it consumes pinned local original Parquet bytes and frozen forecast artifacts only. It verifies the scientific freeze before reading. `--collect-only` recomputes aggregation from independent saved per-animal records without reopening trial outcomes. `RECONSTRUCTION_MANIFEST.json` pins this independent implementation, its outputs and the exact original/forecast provenance. The external cohort remains sealed.
