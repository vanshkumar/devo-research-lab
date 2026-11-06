# Research strategy reset

Current owner decision after both empirical forecast campaigns: [NEXT_RESEARCH_DECISION_AFTER_POPULATION.md](NEXT_RESEARCH_DECISION_AFTER_POPULATION.md). Preserve the completed prospective benchmark and protected external cohort; select the controlled sensory-evaluator teaching question for next investment. The program selection and dispatch below are the preserved history of the earlier reset, not a direction to restart finished work.

2026-10-28. The user asked for a big-picture reassessment and reminded me that this is my research initiative. This decision supersedes promotion of the motor-assay proposal as the main next project. It does not alter any completed result.

Dispatch update: the user explicitly authorized execution in GPT-6.1 Sol at max. Thread `01a184f0-cc97-7920-8be8-e4e89ef2a164` is active; see [the exact launching handoff](LEARNING_RULE_TRANSPORT_HANDOFF.md). Statements below about review-stage execution/exposure are historical.

## The program I am choosing

**Can a learning rule inferred in one training environment predict how an unfamiliar animal learns under a different training environment?**

Build and test models that can function as prospective virtual learners: initialize from a short early history, expose them to a specified training policy, and forecast acquisition without supplying the real learner's subsequent choices or rewards. The scientific target is transport of a learning process across experience distributions. An important eventual use is predicting consequences of training design; that use must be earned before optimizing or recommending curricula.

The first empirical system is longitudinal mouse visual-decision learning, with standard adaptive IBL training and an independently collected cohort trained without that curriculum. Stay with this system through a decisive test. Controlled simulations provide known-answer tests and isolate assumptions; they support the empirical question.

## Why this is a strategic change

Across six completed campaigns, we have repeatedly selected an appealing hidden mechanism and then tried to extract it from the nearest accessible published endpoint. That produced valuable results: a quantitatively weak atlas nomination, transferable human history prediction, source corrections, exact equivalences and demonstrated estimator failures. It also repeatedly led to small effective samples, missing defining observations, and follow-ups about repairing the preceding study's limitations.

The verification work was necessary. The investment pattern needs changing. A methodological problem uncovered by one study does not automatically deserve the next campaign. The motor-assay identification proposal is now a conditional future branch, rather than the main agenda. Another tight fit, source audit or generic identifiability proof would not by itself justify promotion.

Our demonstrated strengths are mathematical/computational modeling, reliable data reconstruction, chronological prediction and adversarial checks. Our present access to new causal measurements is limited. A large longitudinal system with observable future behavior is a better match. It also lets findings accumulate: the same source cohorts, protocol reconstruction and benchmark can support increasingly consequential tests.

## Concrete first study: change the trainer, freeze the learner

Train a small set of learning-rule models only on standard-curriculum animals. Freeze their update rules and any permitted prefix calibration. Forecast learning in new animals, first under the same protocol and then under the independent no-curriculum protocol.

The central comparison has three arms:

1. **Conditional prediction:** the fitted model receives actual past choices and rewards. Reproduce the relevant published result on development/source holdouts.
2. **Autonomous same-protocol rollout:** after a fixed early prefix, the model samples its own choices and receives rewards determined by its own performance. Check whether the rule generates a credible acquisition trajectory in unseen source animals/laboratories.
3. **Autonomous changed-protocol rollout:** apply the same frozen rule to the external training policy, with the same prefix-calibration allowance and no fitted external learning-rate path.

This tests whether a good observer of learning can also generate learning under a changed stream of experience. A successful transferable model and a reproducible collapse from good conditional prediction to poor autonomous prediction are both potentially consequential. Failure must be localized: simulation/implementation error, same-protocol generalization failure and external transport failure support different conclusions.

## What is already verified

The [official IBL release](https://docs.internationalbrainlab.org/notebooks_external/2021_data_release_behavior.html) documents throughout-training behavior across multiple laboratories. Actual public S3 cache inspection in this review found 154 animals with 3,391 indexed training sessions across nine labs. For 128 animals, Parquet trial tables are indexed for every indexed training session. This is an accessible subset, not proof that every animal's biological training history is complete.

The independent Pan-Vazquez cohort has 22 published non-optogenetic animals. Author day labels support days 1–5 for 20 animals and days 1–20 for 18. Two animals have early-prefix gaps and should remain outside a strict-prefix primary analysis until resolved. The tag also contains optogenetic animals and a few control sessions from them; those must not be silently included in the ordinary-learning cohort.

Public session tables were actually downloaded for early examples from both sources and matched their cache hashes. Their schemas contain stimuli, choices, feedback, reward volume and timing. This was an access/schema/input-metadata check, not a behavioral-effect analysis. Public-source outcome summaries have been read, but new raw learning curves have not been calculated in this review.

Evidence is preserved under [longitudinal-learning feasibility](sources/longitudinal_learning_feasibility_2026-10-28/), including exact caches, author day mapping, source pins, example-file manifest, schemas and cohort counts. No large neural recordings or new experimental collection are required for the first study.

## The novelty bar is stronger than ordinary held-out prediction

Existing work already infers learning rules and forecasts held-out behavior. [Liu, Geadah & Pillow](https://arxiv.org/html/2509.04661v2) evaluates held-out animals and future trials while supplying actual preceding decisions and rewards. Its stated motivation includes using inferred learning rules to understand acquisition. The intended additional test here is autonomous transport under a different training policy. A new train/test split alone would not be sufficient.

[Geadah & Pillow](https://pmc.ncbi.nlm.nih.gov/articles/PMC12621722/) compares inferred learning dynamics across standard and no-curriculum datasets. The inspected analysis fits their trajectories separately. Explaining both after observing them differs from freezing a source rule and predicting the external trajectory. [Pan-Vazquez et al.](https://doi.org/10.1016/j.cub.2024.09.045) already studies neural and behavioral individual differences in the no-curriculum cohort; neither side-specific learning nor pre-existing neural predictors should be claimed as discoveries here.

Verify exact paper/code versions before outcome evaluation. The bounded primary review supports this distinct test; it does not establish exhaustive novelty.

## First discriminating test and investment gates

**First:** reconstruct one published source model and its observation process, and demonstrate the difference between conditional evaluation and free-running simulation on controlled learners. Confirm that action, reward, latent update, omission, stimulus and trainer branches operate causally and that a known transferable rule can pass the evaluation. Then run the same comparison on development/source holdout animals. Keep the external cohort sealed during model development.

Use a fixed early calibration budget. An initial specification to assess using input/coverage information is the first 1,000 task trials, followed by forecasts over 1,000, 3,000 and 5,000 further trials, with one primary horizon fixed before validation. Never choose a cutoff from an animal's retrospectively detected learning inflection. Animals with short, discontinued or incomplete observations need an explicit observation/censoring policy; selecting only eventual successful learners would change the population target.

Predict distributions over observable acquisition curves: side-specific high-contrast performance, response bias and omissions. Display errors in percentage points and use a prespecified proper distributional score for the trajectory. Compare against current competence with stable individual differences, empirical exposure/growth baselines and an established reinforcement-learning rule. Match access to initial calibration and training opportunities. A flexible model must earn its complexity through a material forecast improvement and useful uncertainty calibration.

**Second:** test autonomous prediction on whole source laboratories withheld from development. If the model cannot generate future behavior under its original protocol, it has not earned a curriculum-design claim. Diagnose a concrete failure without launching an unrestricted model tournament.

**Third:** freeze the substantive rule, primary horizon, score, practical improvement criterion and external conditioning policy; execute the no-curriculum transfer test once. Do not fit new external learning-rate trajectories to rescue transport. Report animal-level uncertainty and laboratory-specific results. Simulation repetitions and trials are not independent animals.

Conditional forecasts may legitimately remain useful after autonomous failure. A model that improves prediction only because it consumes the real future learner's intervening behavior has passed a different test. Preserve that distinction without dismissing the earlier work's valid purpose.

## Information and interpretation constraints

- After the prefix, autonomous simulations generate their own actions and reward histories. No actual future choices, inferred learning-rate paths, smoothed behavioral weights or criterion-attainment labels enter their updates.
- Under adaptive training, simulate the trainer's response to the simulated learner. Replaying the real animal's future adaptive contrast/reward schedule can reveal consequences of its future competence. It belongs only in an explicitly conditional diagnostic.
- Under the nonadaptive protocol, verify which inputs are independently assigned and may safely be conditioned on. Specify how session boundaries, training opportunities, reward rules and stopping are handled. A forecast conditioned on realized exposure must be labeled accordingly; it is not an unconditional prediction of calendar-time acquisition.
- Treat no-go/omission observations explicitly. Do not silently recode no response as a right choice to reproduce a source preprocessing convention. Any observation-model change must be applied fairly and its scope reported.
- Shared protocol details, available prefixes and subject inclusion must be established from inputs/metadata. Complete indexed tables do not automatically establish complete pretraining histories.
- The external cohort differs in laboratory, animals, recording procedures and training policy. Successful transport would be informative despite this shift. Failure would not identify curriculum as its sole cause. Same-protocol held-out-lab performance is the important control.
- This study tests predictive learning models. It does not identify a unique synaptic rule, prove a causal benefit of teaching policy, or support direct classroom recommendations.

## What I am shelving and what I am preserving

The assay-identification plan, endpoint reanalyses and general profiled-noise theorem are not the main next project. Preserve their scientific lessons and exact artifacts. Do not consume the remaining motor datasets simply because they are available.

A distinct computational alternative is worth retaining: can a learned sensory evaluator teach a new motor target when the motor repertoire was fixed independently of that target? The bounded code review of [Gong et al.](https://elifesciences.org/reviewed-preprints/111771) identified tutor-derived motor-basis and timing inputs in the simplified RL demonstration. A fair extension would draw exactly reachable targets after fixing the plant, with oracle-reward and exploration-matched controls. That is a credible separate bet, but runtime and the natural-input route are not yet demonstrated. It is not being launched alongside the main program.

## Ownership and next action

I own the choice, protocol, model decisions, execution and stopping decisions under the existing charter. The user does not need to choose between proposals or audit our methods before progress can continue. Initial public data feasibility has already been executed. The next substantive work is the source-model conditional-versus-autonomous pilot, with external outcomes protected.

This strategic review does not itself create an additional app thread or claim the new empirical test has run. It establishes one main program and a concrete falsification test. Subsequent context transitions should preserve that objective rather than restart candidate discovery. The aim is a scientific result about when a learning model remains useful after the training environment changes.
