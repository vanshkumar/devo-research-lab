# Development plan (not a validation freeze)

Written 2026-10-28 before opening new raw outcome values. The model and metric specification below may be amended using development animals and controlled cases only. Preserve amendments and their timing. The authoritative source split is `SPLIT.json`.

The substantive model set is a published additive neural update to a Bernoulli GLM (Liu/Geadah/Pillow DNNGLM), canonical REINFORCE with fitted reward baseline, prefix competence persistence and an exposure/growth forecast. A small DNN parameter budget and matched initial observation model are preferred. Extra model families require a concrete failure diagnostic and are not a tournament.

Candidate calibration is the first 1,000 indexed task trials, with future 1,000/3,000/5,000 trial horizons. Determine the primary horizon and bins from metadata coverage and development behavior only. Score side-specific high-contrast accuracy (including omissions as failures), right response fraction and omission fraction. Each simulation generates its own task inputs and histories, conditional on session opportunity boundaries. Curves are observable summaries from generated trajectories, not inferred latent weights.

Use a proper distributional score on the curve forecast, display mean absolute errors in percentage points and calibration of predictive intervals. Compare paired animal-level differences and laboratory-specific results. Simulation replicates and trials are not independent animals. Forecast intervals must include plausible individual/prefix uncertainty as well as action randomness; calibrate residual uncertainty on development only.

Before any source validation, write `FREEZE.json` and `FREEZE.md` containing exact models, artifacts/code hashes, permitted prefix calibration, trainer policy/envelope, target/horizon/bin, score weights, practical gain threshold, calibration gate, censoring/empty-cell treatment, seeds/replicates and all amendments. Evaluate animal and whole-lab holdouts separately as well as combined. Source gate requires material advantage over the strongest matched competence/exposure baseline plus useful calibration; the external cohort is not a fallback search.

Controlled recovery must include a known transferable update rule, no-learning competence, ordinary exposure growth, changing engagement, heterogeneous initialization, trainer mismatch and session reset assumptions. Numerical agreement with original source recurrence and independent original-byte reconstruction accompany the scientific checks.
