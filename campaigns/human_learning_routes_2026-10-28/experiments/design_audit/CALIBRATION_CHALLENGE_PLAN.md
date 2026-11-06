# Pre-validation calibration challenge

2026-10-28. Trigger: strengthened synthetic common-law null and negative-five-percentage-point recovery show that noisy first200 sensory summaries may leave condition acting as a proxy for latent skill; regularization may also attenuate direct condition effects. Real validation remains closed. This is a bounded synthetic measurement diagnosis, not a search over held-out empirical outcomes.

Use three already defined generators (`carryover_null`, `slow_05`, `slow_minus05`) and the fixed injection scales in `outputs/recovery/final/scenario_definitions.json`. Keep each generated600-trial dataset identical across eight diagnostic variants. Use30 independent replicates per generator, with seeds `302610280 + 10000*scenario_index + replicate`, distinct from the main recovery seeds. A two-replicate smoke run checks execution; the30-replicate run supplies the comparison.

| Variant | First two calibration covariates | Diagnostic purpose |
|---|---|---|
| association | Original first/second100 choice×stimulus-sign means | Baseline |
| association_z | Same means, scaled by development standard deviation | Isolate overly restrictive prior in natural association units |
| psychometric_z | Regularized first/second100 sensory slopes, development-scaled | Improve contrast adjustment using available early choices |
| oracle_skill | True latent shared skill; second covariate zero | Isolate measurement error, acknowledging unavailable knowledge |
| oracle_skill_wide3 | Same true skill, condition-history priorSD3 | Separate residual regularization from measurement error |
| independent_200 | Sensory skill from200 extra independent choices | Optimistic additional-measurement diagnostic |
| independent_800 | Skill from800 extra choices | Same |
| independent_3200 | Skill from3200 extra choices | Same |

Other calibration covariates (early response bias and omission rate), fixed nuisance capacity, random effects and later evaluation remain the same across shared and condition models. Every calibration center/scale is estimated from development people; validation covariates use that transform. Replaced covariate names remain API-compatible, but their semantics are recorded here.

The psychometric slopes use the generator's known signed contrast basis (coefficients0.4,0.8,1.6,2.7 at contrasts0.1,0.25,0.5,1), with intercept, prior choice and all three history traces as regularized nuisance predictors. They are a best-case contrast-aware summary, not a data-derived psychometric function selected on validation. Separate fits to the first and second100 preserve acquisition information.

The oracle latent skill is reconstructed from the generator's first seeded draw, confirmed with the model owner: `u ~ Normal(0,.55)` and `shared_skill = u + (.23/.22)*(condition−.5)`. This is exactly the common-law history covariate, not an estimated outcome.

The additional sensory observations are an **optimistic measurement-information experiment**. They assume a fully learned task, equal allocation across signed nonzero contrast levels, the generator's known lapse probability, no history influence, and joint estimation of response bias and sensory scale. The same3200 generated choices supply prefixes200 and800. Thus their results do not by themselves specify the number of trials needed in an ordinary serial task with unknown lapse, changing skill or history effects.

Outcomes: paired held-out predictive gain, participant-bootstrap detection, standardized effect bias/dispersion, convergence and correlation of the sensory summary with latent skill. No effect-bootstrap coverage is claimed by this diagnostic. Main recovery still governs coverage; an oracle point-estimate improvement does not establish valid uncertainty.

Decision: prefer a realistic calibration change only if it materially improves both null behavior and positive/negative recovery without using protected responses. If oracle/independent measurements help but realistic summaries do not, quantify the measurement limitation. If oracle with wider prior still fails, attribute the remaining issue to model/finite-sample discrimination rather than sensory measurement alone. Keep the five-percentage-point scientific boundary fixed.
