# Independent recurrent-model source reconstruction

2026-10-28. This is an independent numerical reconstruction of the separately frozen RNN architecture challenge. The original source holdouts were already consumed before that architecture was added; these results are explicitly postvalidation diagnostics, not an untouched confirmatory source comparison. No external prefixes, choices, rewards or learning curves were opened.

The RNN freeze SHA256 is `a4bcaac21b1302d0527daa31df119bd64b38c7389fcdd8d9323f7eecad5cd652`. The original scientific freeze and all files nested under it, the RNN export, separate calibration and source-audit artifacts were verified unchanged. The original independent reconstruction remains intact.

## Independent paths

`code/independent_rnn_reconstruction.py` reuses only the earlier independent original-Parquet reader, target builder and explicit unordered-pair CRPS scorer. Their implementation hash is checked against the original pinned snapshot. It imports no lead RNN model or RNN rollout recurrence. Original source reads remain bounded to the first 6,000 rows per animal, with original byte-size/MD5/SHA256 verification and exact session chronology. It waits until a subject's RNN forecast, conditional probabilities, observed summaries and scores exist.

All 48 source animals with a prefix plus at least one future bin were reconstructed; 40 have the full primary 3,000-trial future. The same original 518 session tables and 254,306 bounded rows underlie this check. The six shorter allocated source histories remain in the original disposition record. Every high-side count, omission, right-choice fraction and observed curve matches the RNN scorer's saved targets exactly.

## GRU, weight and causal-input reconstruction

The frozen exported matrices are loaded directly. Starting from the saved prefix-calibrated three coefficients and zero 32-dimensional GRU memory, the independent implementation computes:

1. The current right-choice probability from current GLM weights and the pinned transformed-contrast features.
2. After a responding choice, the input vector containing current weights, contrast, constant, session-start flag, native right-choice indicator, positive-feedback indicator and positive-contrast indicator.
3. GRU reset/update/candidate gates in the published/PyTorch order, including reset multiplication of the hidden candidate contribution and its hidden bias.
4. Two rectified layers applied to the updated hidden state, followed by the scaled additive three-coefficient update.

No-response rows hold both weights and recurrent memory. Current response/reward are used after the current probability is saved. A direct perturbation of the current response and feedback leaves that trial's probability unchanged. An explicit omission witness holds both states exactly. Prefix recurrent memory is carried into the future; it is not silently reset at forecast onset or new sessions.

Across 48 animals, maximum differences are:

| Check | Maximum absolute difference |
|---|---:|
| Prefix weight endpoint | 2.22e−15 |
| Prefix hidden endpoint | 6.11e−16 |
| Every future conditional probability | 7.22e−16 |
| Every future conditional weight | 5.11e−15 |
| Final conditional hidden state | 8.88e−16 |
| Current-trial perturbation probability | 0 |
| Omission weight/hidden hold | 0 |
| Reconstructed forecast/diagnostic score | 1.53e−16 |
| Sequential conditional NLL | 2.22e−16 |

There are 432 independently reconstructed score rows: 48 animals × three horizons × primary autonomous, raw autonomous and conditional diagnostic arms. The independent NPZs retain probabilities, latent weights, prefix hidden endpoints and 500-trial hidden checkpoints. These checks support correct implementation and source input timing; they do not establish that a fitted latent state is a unique biological mechanism.

## Independent primary magnitudes

The recurrent model gives the strongest point estimate among the tested frozen architectures, but still does not meet the practical source gate.

| Primary 3,000-trial result, 40 animals | RNN32 | Empirical growth |
|---|---:|---:|
| CRPS | .075339 | .080975 |
| High-contrast MAE | 15.75 pp | 16.28 pp |
| 80% coverage, all four metrics | 88.85% | 86.35% |
| 80% coverage, high-contrast accuracy only | 84.79% | 81.25% |
| Mean 80% width, all four metrics | 43.57 pp | 38.82 pp |
| Mean 80% width, high-contrast accuracy only | 60.63 pp | 53.41 pp |

RNN improves CRPS by 6.96% and high-contrast MAE by 3.24% over growth. The absolute CRPS gain is `.005636`, canonical animal-bootstrap 95% `[-.001407,.013065]`; the five-candidate/two-baseline screen's `.005` lower percentile is `−.003630`. The interval allows useful positive effects. The conclusion is that prespecified utility was not earned, not that all transferable learning laws are absent.

Against competence persistence, CRPS improves .029072 [ .014466,.044673 ], or 27.84%; accuracy error improves 23.50%. A growth baseline is therefore decision-bearing here.

In the reserved Hofer laboratory (9 full animals), RNN CRPS is .078000 versus growth .077860, slightly worse. In Witten (10), it is .077608 versus .088897, better. Combined reserved-lab CRPS is .077794 and high-contrast MAE 15.89 pp. In the separate unfamiliar-animal group (21), CRPS is .073118 and MAE 15.62 pp. `LAB_STRATA.json` preserves every laboratory result; two reserved labs do not quantify arbitrary new-lab uncertainty.

Conditional prediction remains much more accurate: NLL .528045 nats/responding choice versus .682517 for the existing frozen prefix-persistence point on the same future stimuli. Conditional sampled-curve high-contrast MAE is 2.30 pp, compared with autonomous 15.75 pp. These conditional curves fix the real preceding histories and are diagnostic; their curve scores are not joint autonomous trajectory scores.

## Bootstrap ordering audit

Canonical bootstrap ordering is exactly `artifacts/results/SUBJECT_ORDER.json`: unfamiliar-animal IDs alphabetically, then reserved-lab IDs alphabetically. Both implementations use seed 891 and 10,000 resamples. The current root and independent canonical mean/95% interval/gate-lower results differ by at most 1.57e−17.

An earlier root/review rendering used global alphabetical order. The independent witness reproduces its growth-gain interval `[-.001110,.013038]` exactly. A fixed Monte Carlo index stream maps to different animals after reordering, so finite bootstrap quantiles change slightly while the mean and the target resampling distribution do not. `BOOTSTRAP_ORDER_AUDIT.json` preserves both explicit 40-ID orders, quantiles, unchanged means and the canonical cross-implementation comparison. The canonical interval above is authoritative; the alternative is a reproducibility witness, not another selected uncertainty estimate.

## Offline reproduction and provenance

```sh
campaigns/learning_rule_transport_2026-10-28/.modelenv/bin/python \
  campaigns/learning_rule_transport_2026-10-28/code/independent_rnn_reconstruction.py --overwrite
```

The command uses original local source bytes and frozen exports only. `--collect-only` recomputes aggregate scores and the ordering audit without rereading trial outcomes or refitting anything. Per-animal `records/` include original queries/hashes and frozen forecast hashes. `NUMERICAL_DIFFERENCES.json`, `INDEPENDENT_SCORES.json`, `INDEPENDENT_SUMMARY.json`, `PAIRED_COMPARISONS.json` and `LAB_STRATA.json` contain full results. `RNN_RECONSTRUCTION_MANIFEST.json` pins this implementation and outputs. Initial source reconstruction and all external outcomes remain preserved.
