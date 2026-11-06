# Methods specification awaiting final hash freeze

Written before any new source-validation outcomes. `FREEZE.json` will activate the exact specification after development capacity and uncertainty checks. Nothing here authorizes opening external outcomes without a source gate.

## Population, prefix and opportunity target

Metadata allocation is74development,27unfamiliar animals in development labs,27animals in the two wholly reserved Hofer/Witten labs. Development is nested62fit/12tuning animals. All models use the same fit allocation; no eventual learning criterion enters eligibility. All128source animals with trial tables at every indexed training session are retained in the disposition. Twenty external animals are protected; fip_16/fip_38 remain excluded for prefix gaps. The target begins at first indexed training, not certified first biological exposure.

Calibration is exactly the first1000task rows, including omissions. Forecasts cover the next1000,3000(primary),5000task opportunities, in nonoverlapping500-trial bins. Full primary coverage exists for40reserved animals(21animal-holdout,19lab-holdout);48have the prefix plus at least one scored bin. Report all54allocated animals,6too short for calibration,8without the complete primary horizon, partial observed-bin scores and per-horizon denominators. Full-horizon selection is conditional on continued observation, which may depend on performance. Do not impute unobserved cessation outcomes.

The primary forecast conditions on realized counts/boundaries of task opportunities, obtained from Parquet footers and chronology. It predicts neither calendar time nor stopping. Prefix readers return only prefix outcome rows plus future boundary booleans; forecasts are saved before future scoring reads. Future stimuli, real actions/rewards, smoothed states/rates and performance labels are not passed to the autonomous function.

## Small model set and information matching

- Published DNNGLM with three GLM coefficients(right contrast,left contrast,bias), two ReLU hidden layers;16units with two seeds, plus source-default32unit capacity challenge. Checkpoint selection uses nested development conditional likelihood only. Both widths are reported; no held-out tuning.
- REINFORCE with a fitted source-style reward baseline. Stable gain parameterization is algebraically equivalent to a baseline/step-size rule. Pure reward-driven REINFORCE fixes that baseline to zero as a canonical control.
- Competence persistence uses every prefix observation in a static three-coefficient GLM with the same Gaussian coefficient prior. An earlier last500version is preserved as a development pilot. This full-prefix improvement was made after fixed-competence recovery exposed a precision advantage for dynamic rules using all1000observations.
- Empirical exposure/growth draws future500-trial changes from15development neighbors matched on recent prefix competence/engagement, anchored at the test animal's recent-prefix fit. Donor censoring is handled per bin with observed development opportunities. This is a marginal predictive baseline, not a coherent biological donor trajectory.

All actors share the same source-derived future engagement component. Omission probability is calibrated from the last500prefix outcomes with a beta half-count prior, then receives a frozen development donor's exposure-indexed logit changes. Omissions are separate scored observations and failures of high-contrast accuracy; their binary choice-weight update is skipped. Thus the persistence actor is **skill persistence plus matched engagement**, not constant behavior in every channel.

Dynamic actors calibrate only their three initial coefficients by prefix-only likelihood, with a fixedN(0,2I)prior and bounds. Their update law is never refitted to a test animal's future. Local Fisher uncertainty is propagated through the causal prefix recurrence; simulations additionally sample actions, engagement and trainer randomization. This is approximate predictive uncertainty, not a posterior identifying a unique law. A bounded zero-mean development-residual calibration challenge may be frozen before validation; raw forecasts must remain visible.

## Autonomous trainer and conditional arm

The standard trainer initializes its buffers/pool from permitted prefix inputs/actions/rewards/repNum. It then selects its own stimuli, computes reward from its own generated choice and updates its own adaptive contrasts/corrections/session reward. Versioned original-code checks and a known-answer recovery test precede validation. Primary daybreak behavior carries coefficient state across sessions. Unknown biological prehistory, wheel dynamics, body weight/settings and operator behavior remain scoped uncertainties.

The external generator is fixednonzero contrasts1,.25,.125,.0625 with independent half-side assignment and3µL correct rewards, after the source gate. No external learning-rate path or update law is fitted. The only permitted external individual calibration is the same1000prefix and omission allowance. Differences in lab,genotype,implantation,handling,year and policy are bundled.

Conditional prediction uses actual preceding test actions/rewards, predicts before the current outcome and reports animal-averaged sequential binary response log loss. Its curve samples hold actual histories fixed and are only diagnostic; their curve scores are not joint autonomous forecast scores. Actual adaptive-schedule replay is another explicitly conditional diagnostic, never the primary.

## Targets, score and useful-prediction gate

Per500trial bin: left high-contrast correct share, right high-contrast correct share(|contrast|>=.5;omissions count as incorrect), right-choice share among all trials, omission share. Empty observed high-side cells are missing under a common observation-defined mask. Nonfinite forecast draws at a scored coordinate are errors, not grounds to drop that coordinate. Report both sides, metric/bin calibration and absolute high-contrast errors in percentage points.

The primary proper score is the mean marginal CRPS, equally weighting the four metrics and available bins, then animals. The Monte Carlo U-statistic estimates E|X−y|−.5E|X−X'|. Marginal calibration is not joint trajectory calibration. Energy score is a diagnostic of the forecast algorithm's induced path distribution. Animal bootstrap intervals describe the sampled animals, not millions of independent trials or arbitrary new laboratories.

Before validation, the source gate will require a candidate rule to improve CRPS materially over the matched growth/competence baselines, improve actual high-contrast forecast accuracy, maintain useful marginal calibration and succeed in the wholly reserved lab subset. At least10%relative and.002absolute CRPS improvement and10%relative high-contrast MAE improvement(absolute MAE<=15pp) define material overall benefit. Calibration requires nominal80%interval coverage in70–95%of cells, including high-contrast cells separately. Whole-lab aggregate needs at least5%CRPS benefit,no high-contrast MAE worsening and a positive mean score benefit in each of Hofer/Witten. All candidate/baseline comparisons and uncertainty will be reported; the final freeze specifies multiplicity/gate calculation. Wide intervals alone cannot pass.

## Challenges fixed before outcomes

Known transferable learners are fitted with the exact empirical optimization/initialization and must forecast both protocols. Fixed competence, ordinary exposure growth and changing engagement must not manufacture a material advantage over their strongest baselines. Initialization heterogeneity, correction mismatch, known daybreak retention/rescue, stochastic forecasts, omission masking and censoring are separate checks. Recovery demonstrates a broken daybreak assumption can cause failure; real-data sensitivities therefore include unchanged/.8retention/reset, static versus MAP prefix state, no correction and fast/slow promotion. Actual-input replay localizes trainer versus actor contributions without becoming an autonomous test. Report1k/5k horizons, lab and prefix-competence strata, cache-left-edge start and raw/calibrated uncertainty. These are challenges, not opportunities to refit a new law on validation.
