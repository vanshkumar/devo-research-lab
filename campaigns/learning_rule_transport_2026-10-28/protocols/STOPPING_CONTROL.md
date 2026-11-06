# Outcome-dependent termination challenge

This is a postvalidation synthetic scope check, not a new empirical validation or a model-selection opportunity. It reads no real external data.

The original recovery controls had fixed500-trial sessions and independent censoring. A fresh reviewer correctly noted that they do not validate outcome-dependent opportunity selection. `code/stopping_control.py` therefore imposes training termination on histories generated causally by the known transferable learner and standard trainer. Histories up to the terminal event remain valid closed-loop histories; later counterfactual rows do not enter scores.

An initial85%criterion never removed a primary horizon; it was ineffective as a selection challenge and is preserved in `INITIAL_85_PERCENT_PILOT.json`. A75%criterion was then fixed and evaluated on a **new independent seed8739**,24animals. After at least four500-trial sessions, training stops after two consecutive sessions with high-contrast accuracy>=75%, or three consecutive sessions below45%; maximum exposure is6000. This design is deliberately exploratory and strongly selects on learning. Forecasts use the rule previously fitted on independent synthetic source animals, the same first1000prefix and the retained opportunity boundaries.

Termination occurs at2500trials for3animals,3000for10,3500for10 and5000for1. Only **one** animal has the complete3000-trial future. Its bootstrap interval is intentionally marked unavailable: a degenerate one-animal bootstrap is not precision. All24animals retain scored partial bins.

Across partial observed futures, the fitted rule has CRPS.014077, high-contrast MAE2.468pp and80%coverage85.26%; growth has.018381and3.400pp. Paired score gain is.004305[.002881,.005888]. This bounded example retains known-rule forecast value while exposing how sharply a complete-case sample can shrink. It does not validate real IBL response-time, fatigue, session-duration or operator stopping, and must not be quoted as a full-horizon informative-censoring recovery.

The predictor is an operational opportunity-conditioned recipe. It does not update its latent state posterior using the likelihood of the observed termination event. Source conclusions therefore concern measured forecasts under that recipe, not a complete causal conditional simulator or unconditional calendar-time learning.

Reproduce offline with the campaign model interpreter and `code/stopping_control.py`. Original syntheticNPZs, seeds, terminal dispositions, forecast samples and scores are retained under `artifacts/stopping_control/` and `artifacts/recovery/synthetic/stopping_challenge/`.
