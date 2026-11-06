# C1 — how reliable must the update gate be?

Decision: **revise**, retain an implementation constraint, not a finding about human brains. One synthetic pilot; 1,800 fits are not 1,800 distinct experiments.

Before computation, closer reading of the proposed mechanism changed the test (see PLAN.md): imagined-other states are meant to use a shared feeling code and suppress the predictor update. An arbitrary self/other remapping counterexample would not test that proposal fairly. We therefore gave the decoder the favorable shared-code assumption and varied update-gate contamination.

`run.py` implements self fraction π, self-update sensitivity .9, erroneous imagined-context update probability f, and own/imagined feeling correlation ρ. It fits four-dimensional linear least squares after a random orthogonal rotation. Independent Gaussian query error is computed exactly as squared coefficient error; no query-data tuning occurs. Twenty seeds0–19, sample sizes200/2000, π=.05/.2/.5, ρ=−.5/0/.8, f=0/.01/.05/.2/1 are all retained in per_seed.csv. The Gaussian and homoskedastic assumptions are conveniences, not neuroscience claims.

For n=2000, π=.05, ρ=0, a perfect gate gives median query MSE .000557. A 1% false-update probability gives .03760, 5% gives .23986, and20% gives .65354. A positive-control sample of200,000 recovers the population gain within .00290 and gives perfect-gate MSE2.19e−6. High positive own/other correlation reduces contamination damage; the full grid includes this favorable alternative.

The population gain is

`g = [π t + (1−π) f ρ] / [π t + (1−π) f]`, with t=.9.

Derivation: accepted contexts leave E[zzᵀ] proportional to identity, while cross-moment with the label has unit slope for self samples and slopeρ otherwise. `check.py` independently enumerates a finite signed distribution with rational arithmetic over45 conditions and recovers the same cross-moment ratio. For π=.05 andρ=0, g>.9 requires f<1/190≈.005263. This is a conditional constraint on the toy model. Neither π nor f has been measured biologically here. It illustrates why positive predictive value of the teaching gate matters; generic accuracy can hide contamination when genuine teaching occasions are rare.

Surviving objections: actual representations may not be shared or linear, attention may change representation as well as learning rate, labels may correlate with latent states nonlinearly, and other learning pathways may compensate. The calculation does not identify a brain circuit or refute the entire social-instinct account. Retire as a standalone novelty claim; use as a preregisterable parameter check if a concrete implementation is built.

From repository root:
```sh
.venv/bin/python campaigns/byrnes_todo_2026-10-28/experiments/concept_finder/run.py
.venv/bin/python campaigns/byrnes_todo_2026-10-28/experiments/concept_finder/check.py
```
