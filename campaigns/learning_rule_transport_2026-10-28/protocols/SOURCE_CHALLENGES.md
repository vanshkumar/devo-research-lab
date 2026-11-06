# Source failure challenges and Monte Carlo precision

2026-10-28. These are diagnostics on the already consumed source holdouts, not new independent validations. All 40 full-primary source animals are retained in the frozen order from `artifacts/results/SUBJECT_ORDER.json`. The external cohort remains sealed. No fitted rule, source bank, uncertainty amplitude or frozen artifact was changed.

## Scope and implementation

`code/source_challenges.py` uses the two frozen rules DNNGLM32 and free-baseline REINFORCE. Every rollout receives only the original first 1,000 trial rows and the same realized next 3,000 session opportunities. Frozen primary forecasts use 512 particles; the predeclared sensitivity families use 256 particles. Per-animal scores compare each sensitivity with both its original primary forecast and the frozen empirical-growth baseline. A prespecified confirmation policy would rerun any non-replay sensitivity with mean gain at least .001 CRPS over growth at 512 particles. None met that trigger.

Alternative initializations are static current-prefix competence and zero initial weights followed by the original prefix updates. Other checks are future daybreak retention .8, reset to the calibrated prefix anchor at each future session, no correction trials, faster/slower contrast-promotion criteria, and fixed future omission probability. The actor, observation definition, feedback semantics, prefix budget, source growth bank and development uncertainty configuration stay fixed. Both tested rules have frozen discrepancy amplitude zero.

The actual-contrast replay deliberately supplies the animal's real future adaptive contrast sequence. It samples its own choices, receives feedback from those sampled choices and updates its own state. The original frozen replay inherited its stochastic trainer's assigned side at forced zero contrast; that side can be biased by the trainer's pending correction state, which is incompatible with a fully exogenous forced schedule. A separately archived correction supplies independent Bernoulli(.5) zero-trial sides. It uses a process-local wrapper of the sampler's returned side, a fixed independent RNG stream `subject_base+823`, and restores the original method in `finally`. Nonzero actual contrasts still determine their own side. Frozen source files and all primary forecasts remain unchanged. Neither version supplies the animal's true future zero choices or feedback. Both are conditional input diagnostics, never autonomous forecasts or transport claims. `BALANCED_REPLAY_AMENDMENT.json` records the correction.

An adversarial review correctly noted that the initial .8 retention diagnostic changed future boundaries while prefix MAP inference still assumed retention 1. A separate coherent check uses `recovery.RetentionAwareModel(base,.8)` for prefix calibration and state uncertainty, plus `.8` multiplication before every future session prediction. Both rules were rerun coherently on all 40 animals at 256 particles. The original future-only diagnostic remains archived and explicitly labeled. Neither check refits the update rule. `COHERENT_RETENTION_AMENDMENT.json` records this postvalidation review challenge.

## Results: no rescue among the bounded challenges

Primary MAP references are CRPS .080517 / high-contrast MAE 16.38 pp for DNN32, and .082889 / 17.19 pp for RL. The growth baseline is .080975 / 16.28 pp. Values below use all 40 source animals and the original observed target definition.

| Source sensitivity | DNN32 CRPS | DNN32 high-contrast MAE | RL CRPS | RL high-contrast MAE |
|---|---:|---:|---:|---:|
| Static current-prefix state | .089014 | 18.61 pp | .093511 | 19.42 pp |
| Zero initial weights, assimilate prefix | .080962 | 16.46 pp | .083148 | 17.29 pp |
| Future-only daybreak retention .8 | .081127 | 17.18 pp | .088454 | 18.99 pp |
| Coherent prefix and future retention .8 | .082394 | 17.43 pp | .088755 | 19.05 pp |
| Reset future sessions to prefix anchor | .085897 | 16.87 pp | .084887 | 17.89 pp |
| No correction trials | .106439 | 20.18 pp | .098249 | 16.70 pp |
| Faster promotion (>35/50 per side) | .081131 | 16.48 pp | .083449 | 17.32 pp |
| Slower promotion (>45/50 per side) | .080601 | 16.35 pp | .083201 | 17.26 pp |
| Fixed omission probability | .081499 | 16.50 pp | .083998 | 17.40 pp |
| Actual future contrasts, original trainer zero side | .112675 | 20.07 pp | .159926 | 26.79 pp |
| Actual future contrasts, independent balanced zero side | .112658 | 20.07 pp | .159941 | 26.79 pp |

No autonomous sensitivity has even .001 mean CRPS improvement over growth. The coherent retention check worsens DNN32 by .001877 versus its primary forecast (95% animal interval [−.003455,.007546] for deterioration; equivalently the saved improvement interval is [−.007546,.003455]). It worsens RL by .005866, with saved improvement interval [−.011677,−.000387]. `SUMMARY.json` and every individual record preserve exact signed comparisons and ordinary 95% animal bootstrap intervals. These diagnostic intervals are not multiplicity-adjusted evidence for a selected replacement model.

Actual future stimulus replay also fails to rescue acquisition, including after correcting the zero-side assignment. Its corrected CRPS differs from the original replay by −.000017 for DNN32 and +.000015 for RL. Therefore the observed gap cannot be repaired merely by handing these actors the true future adaptive contrasts. This does not prove the trainer is perfectly reconstructed or isolate a unique cause. The other checks exclude the tested initialization, boundary, omission and correction alternatives as simple empirical rescues; they do not exhaust all plausible models.

Reward volume and wheel gain are not actor inputs in these published binary-feedback architectures. Fixed-volume or gain changes would be inert in this implementation, so no such simulation is advertised as a robustness test. Real magnitude/gain effects remain outside the model and can still help explain its scope limit.

## Predeclared Monte Carlo challenge

The first six complete source animals by SHA256(subject) are `ibl_witten_11`, `CSHL_013`, `ZM_3001`, `ibl_witten_17`, `SWC_041` and `SWC_034`. DNN32, free RL and growth forecasts were run at 1,024 particles and compared with their original 512-particle forecasts on the identical primary targets.

| Model | Mean CRPS change, 1024−512 | Maximum absolute animal CRPS change | Mean high-contrast MAE change |
|---|---:|---:|---:|
| DNN32 | +.000389 | .003600 | −.073 pp |
| Free-baseline RL | +.000750 | .004692 | −.030 pp |
| Growth | +.000255 | .001719 | +.054 pp |

Individual-animal simulation noise is not negligible relative to very small effects. Group means move much less than the practical source threshold. To honor the extra precision trigger from the frozen plan, DNN16 and growth were also rerun at 1,024 particles for all 40 complete source animals:

- DNN16 CRPS .079967 versus growth .081296; gain .001329, 95% [−.004679,.007394], 1.63% relative.
- The gate's `.00625` lower bootstrap percentile is −.006450.
- DNN16 high-contrast MAE is 17.19 pp versus growth 16.35 pp, a 5.14% deterioration.

The extra precision does not approach the required 10% score improvement and 10% accuracy-error improvement. The source-gate failure is not a rounding error from the initial 512-particle mean. These checks do not convert finite intervals into a universal equivalence claim.

## Artifacts and offline execution

972 forecast artifacts are retained: 720 initial source sensitivities, 80 coherent-retention forecasts, 80 balanced-zero replay forecasts, 80 all-animal DNN16/growth precision forecasts, and 12 additional DNN32/RL forecasts in the hash-selected six. `SCORES.json` contains every paired animal comparison. `MC1024_DNN16_VS_GROWTH.json`, `MC1024_HASH6.json`, `CONFIRMATION_STATUS.json`, `CHALLENGE_DESIGN.json` and amendment files identify all tested choices. The corresponding NPZs retain both raw and primary distributions, latent-weight summaries, trainer pool summaries and counts. Every per-forecast JSON pins its NPZ hash and source freeze/configuration hashes.

```sh
PYTHON=campaigns/learning_rule_transport_2026-10-28/.modelenv/bin/python
SCRIPT=campaigns/learning_rule_transport_2026-10-28/code/source_challenges.py
"$PYTHON" "$SCRIPT" --sensitivities --mc --workers 3
"$PYTHON" "$SCRIPT" --coherent-retention --confirm --workers 3
"$PYTHON" "$SCRIPT" --balanced-replay --workers 3
```

These commands use pinned local data only and resume saved artifacts with checksum checks. They verify the original scientific freeze and never edit it. `--collect-only` aggregates the already saved diagnostics. The one-animal pilot took 10.15 seconds for 18 actor/variant pairs before ordinary three-process execution was started. `SOURCE_CHALLENGES_MANIFEST.json` pins the implementation, helper snapshot and all outputs. Source holdouts are consumed; external choices, rewards and prefix outcomes remain unopened.
