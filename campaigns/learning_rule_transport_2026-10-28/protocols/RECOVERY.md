# Controlled recovery and localized failure tests

2026-10-28. These tests use synthetic animals only. No empirical source-holdout or external outcomes were opened by this work. The original synthetic NPZ bytes, generator parameters, seeds and SHA256s are retained in `artifacts/recovery/synthetic/*/GENERATOR.json` and the corresponding per-animal files. `code/recovery.py` is the runnable implementation.

## Question and design

Can the exact autonomous trainer, prefix-calibration and scoring pipeline recognize a truly transferable learning rule, and distinguish that result from ordinary exposure forecasting or changing response engagement?

The positive generator is the source-style three-coefficient REINFORCE rule, with right/left/bias learning rates `[.006,.006,.003]`, action-independent reward baselines `[-.2,-.2,-.2]` and transformed contrast features identical to the empirical rule. Independent animals have slightly variable starting sensory weights and normally distributed bias (SD .5). Choices are generated before rewards; reward comes from the causal `VectorTrainer`'s own stimulus and generated choice. Omission probability is a persistent logit-normal individual trait near 7%; omissions are observed, unrewarded and skip the binary update. Sessions contain 500 trials. The first 1,000 trials calibrate initial conditions; forecasts generate their own next 5,000 actions, feedback, learning updates and adaptive trainer decisions. The primary score uses the first 3,000 forecast trials, in six 500-trial bins.

There are 24 adaptive-source training animals, 24 unfamiliar adaptive-source test animals and 24 independently initialized fixed-protocol test animals. No fixed-protocol update law is fitted. Each forecast receives the same prefix allowance and the same realized number/boundaries of training opportunities. The fixed protocol has four nonzero contrasts and fixed 3 µL correct-choice reward. Source-only empirical growth and persistence baselines share observation/engagement uncertainty, prefix access and trainer information with the learning models.

The primary proper distributional score is the shared `evaluation.score`: marginal CRPS averaged equally across side-specific high-contrast accuracy (omissions count as failures), right-choice share, and omission rate, then across available bins. Accuracy errors below are in percentage points. Intervals on score differences resample independent synthetic animals; interval calibration is evaluated on observable trajectory cells and is descriptive, not a claim that cells are independent animals.

## Positive recovery: the empirical fitting procedure also passes

Two fits deliberately separate questions. A known-training-initialization fit tests numerical likelihood recovery; a stronger challenge uses the exact empirical `fit_rl(...,stable_gain=True)` procedure, including its static estimate from the first 200 training trials, without supplying generator initial weights. Both forecast new test animals using only the 1,000-trial prefix MAP procedure, with local calibration uncertainty propagated through the causal recurrence. Baseline sensory parameters need not be exactly recovered to pass the observable forecast test.

| Forecast / cohort | CRPS | Growth CRPS | Gain over growth, 95% animal interval | High-contrast MAE | 80% coverage | 95% coverage |
|---|---:|---:|---|---:|---:|---:|
| Exact empirical fit, new source animals | .013941 | .018002 | .004061 [.002772,.005506], 22.6% | 2.45 pp | 86.6% | 98.1% |
| Exact empirical fit, fixed protocol | .024301 | .027085 | .002784 [.001564,.004102], 10.3% | 5.08 pp | 83.7% | 95.8% |
| Known-init fit, new source animals | .013632 | .018002 | .004370 [.003020,.005883], 24.3% | 2.40 pp | 85.8% | 97.7% |
| Known-init fit, fixed protocol | .023759 | .027085 | .003326 [.002048,.004717], 12.3% | 5.02 pp | 82.5% | 95.0% |

Persistence CRPS is .075672 on new source animals and .067082 on the fixed protocol. The source-trained oracle gives .013605/.023740; the known-init fit nearly reproduces it. Its fitted learning rates are `[.006058,.005864,.002947]`, close to the generator. Its fitted baselines `[-.493,-.369,-.170]` differ more substantially; expected autonomous coefficient drift from an action-independent baseline cancels, and such parameters are not the validation target. The empirical initializer yields rates `[.005754,.006001,.001945]` and different baseline terms but retains useful observable forecasts. Exact values, optimization records and every animal score are saved.

The pipeline therefore can detect material autonomous improvement from a known transferable rule, including after the specified policy change and unknown test-animal initialization. This is a positive control for a bounded generator family; it does not prove that every real learning law is identifiable or that every plausible biological regime has adequate power.

## Negative-generator controls

Each control has 24 independent source training and 24 new test animals, with its own source-only growth/omission bank and the same fitting and forecast budget. No real data are used.

| Generator | Fitted rule CRPS | Persistence | Growth | Interpretation |
|---|---:|---:|---:|---|
| Fixed competence | .015596 | .016843 | .017608 | Fitted reward gains shrink to their lower bound. Improvement over the strongest baseline is .001246, below .002. |
| Exposure growth without reward updates | .018715 | .067491 | .015034 | Fitted rule beats persistence but loses to growth by .003681, 95% [.001131,.006690]. |
| Changing engagement, fixed responding competence | .016143 | .016631 | .017165 | Shared engagement forecasting explains improvement; added learning gain over the strongest baseline is .000488. |

These controls demonstrate why growth and persistence must both be considered. On fixed competence, a learning fit using all 1,000 prefix trials can beat the noisier last-500-trial growth baseline by .002011 without demonstrating learning. Against the stronger persistence baseline its gain is below the practical boundary. Prefix-estimation precision is a concrete reason to include full-prefix persistence as an empirical sensitivity; it is not a transferable update-law discovery. The controls do not establish unique mechanism identification or a universal false-positive rate.

An exact action-marginalized witness in `INVARIANT_CONTROLS.json` verifies that a pure response-likelihood evidence filter has zero expected coefficient update under its own generated actions, whereas reward-contingent REINFORCE has directional sensory updates. Omission updates are exactly zero. Zero expected coefficient drift does not imply constant expected choice probability after nonlinearities; this witness checks the distinction between teacher-forced observation and endogenous learning.

## Challenges and known-assumption rescues

All challenges use 24 new synthetic animals and the same rule frozen from the positive source training cohort.

| Challenge | Fitted-rule CRPS / 80% coverage | Result |
|---|---|---|
| Hidden initial bias SD increased from .5 to 1.2 | .014303 / 83.9% | Prefix-only calibration retains improvement over growth (.028975). |
| True coefficient retention .8 at each daybreak, but forecast assumes 1 | .038725 / 53.5% | A correct learner equation fails when daybreak dynamics are misspecified. |
| Same .8 retention supplied to prefix calibration and future simulator | .013771 / 84.5% | Correcting this one known assumption rescues .024954 CRPS [.022527,.027188]. |
| True trainer has no correction trials, forecast uses corrections | .017285 / 77.1% | Trainer mismatch degrades calibration and forecast quality. |
| Correct no-correction trainer supplied | .015957 / 82.6% | Matched-trainer rescue .001328 [.000487,.002258], smaller than daybreak effect. |
| Independently censored exposure, including 650-, 900-, and 1,000-trial histories | .012876 / 88.2% among 12 with 3,000 future trials | Short animals remain in manifests; available full-bin forecasts are scored separately. No success-based deletion. |

The matched retention rescue uses `RetentionAwareModel.sequence` for correct prefix initialization and `autonomous(weight_retention=.8)` before future session predictions. The correction rescue changes only `trainer_options={'correction':False}`. These rescues demonstrate localization in controlled cases. They do not establish which assumption is wrong in real animals or justify fitting those assumptions to held-out outcomes.

## Monte Carlo and retained artifacts

The primary synthetic run uses 128 particles. A prespecified first-six-animal check per protocol uses 512 particles, retaining full forecast samples for both runs. Mean CRPS changes for known-init fitted learning are +.00000096 in source and +.0000540 in the fixed protocol; growth changes are +.0001287/+.0000329. These are well below the .002 practical score boundary and the observed positive-control improvements. Individual-animal differences can be larger: the largest fitted-rule change is .001003, and baseline changes reach .002831. Do not mistake a stable group average for exact individual Monte Carlo convergence. The empirical study uses a separate higher-particle convergence check.

`SCORE_SUMMARY_p128.json`, `PAIRED_COMPARISONS_p128.json`, `MONTE_CARLO_CONVERGENCE.json`, `MATCHED_ASSUMPTION_RESCUES.json` and per-group score JSONs contain complete numbers. `forecasts/` retains sampled observable curves, original synthetic observed summaries and cell counts. `KNOWN_TRANSFER_RECOVERY.png/.pdf` shows the exact empirical-fit positive control; error bars resample animals. The figure was rendered and visually inspected. Plotting uses the repository's existing Python3.9 Matplotlib; numerical fitting uses the isolated campaign model environment. An initial plotting attempt in the model environment failed for lack of Matplotlib and is retained in the log; this did not affect numerical controls.

## Offline commands

From repository root, using only local dependencies and pinned/generated bytes:

```sh
RECOVERY=campaigns/learning_rule_transport_2026-10-28/code/recovery.py
PYTHON=campaigns/learning_rule_transport_2026-10-28/.modelenv/bin/python
"$PYTHON" "$RECOVERY" --generate --fit --fit-nulls
"$PYTHON" "$RECOVERY" --evaluate --groups learn_same,learn_external --particles 128
"$PYTHON" "$RECOVERY" --evaluate --groups learn_hidden,learn_reset,learn_no_correction,learn_censored,fixed_test,growth_test,engagement_test --particles 128
"$PYTHON" "$RECOVERY" --evaluate --groups learn_same,learn_external --particles 512 --max-animals 6
"$PYTHON" "$RECOVERY" --rescues
"$PYTHON" "$RECOVERY" --fit-pipeline --evaluate --groups learn_same,learn_external --particles 128
"$PYTHON" "$RECOVERY" --summarize --convergence
.venv/bin/python "$RECOVERY" --figures
```

The group order in these commands defines the recorded forecast seed families; retain that exact order for fresh regeneration. Each group score record also stores its exact seed. Evaluation resumes already saved model/animal/horizon results. To test clean recomputation without altering archived evidence, copy the campaign or point a separate reproduction script at the retained NPZs. No network access or external data are required.

Version distinction for exact historical regeneration: these control forecasts were generated before the source study strengthened competence persistence from the recent 500 trials to the full 1,000-trial prefix. `code_snapshot/` preserves that control-era implementation. Fresh generation using the later source-frozen rollout strengthens the persistence comparison and therefore changes that historical baseline's values; it does not change the positive control's principal comparison against growth. Exact historical control score replay should use the retained forecast samples or place the archived modules in a separate scratch campaign layout. Do not overwrite either the historical controls or the source-frozen implementation. The source campaign's offline runner separately reproduces decisive forecasts under its own later scientific freeze.
