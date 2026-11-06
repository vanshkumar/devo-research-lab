# C1: when an interoceptive concept finder identifies a source

Saved before computations, 2026-10-28. Target is a necessary statistical assumption in the proposed concept-finder/attention architecture, not a full simulation of Byrnes's model or a biological mechanism.

Let learned activations z=M[s,o] mix own-state s and inferred other-state o with arbitrary invertible M; a primitive physiological teaching signal y measures s. Predictor maps z→y. If o=s during learning, identifying own-state vs other-state is impossible without structure/independent variation: infinitely many coefficient vectors agree observationally. If o=ρs+sqrt(1−ρ²)u, full-rank learning becomes possible but weakly excited directions may generalize poorly when ρ changes. A scalar gain in y can be confounded with M scale, so claim only predictions/source separation conditional on known generator.

Minimal/positive controls: exact rank/linear algebra for ρ=1; independent data ρ=0 must recover known unmixing with sufficient samples; true scalar decoder should predict held-out signals. Alternatives: global arousal proxy, source-specific teaching signal, independent social/own variation, and attention masking that does/does not actually change training covariance.

Run 20 discovery seeds, T=200/2000, ρ∈{0,.8,.98,1}, noise SD .1, random rotation and rescaling. Train LS (and ridge if justified as reported exploratory), test matched covariance and independent own/other signals. Units are synthetic independent runs, not neurons/people. No inferential biological p-values. Report conditioning, coefficient errors and held-out MSE.

Predictions before outcomes: rank-deficient observations cannot uniquely label own/other source; full-rank noisy data should recover given enough independent excitation. Attention that only rescales the same co-varying observations should not repair rank; an intervention that decorrelates sources should. Neither success nor failure establishes that actual human circuits use this decoder, and the source theory need not claim arbitrary identifiability.

After discovery, if promoted, freeze verification seeds and investigate nonlinear feature robustness / source-dependent teaching feedback and a strong alternative. Do not interpret agreement of model reviewers as confirmation.

## Pre-computation source correction

Closer inspection of the *current* sketch §§3.2/4 shows the intended mechanism more specifically: train only while attending to actual self interoception; query a shared feeling-code during imagined other states; suspend updating during those queries. The initial rank example above is a general boundary case, not a faithful complete implementation of that claim. Main pilot therefore tests this actual gating proposal with best-case shared codes, then a representation-compatibility sensitivity. This correction precedes numerical outcomes.

Self-teaching fraction π∈{.05,.2,.5}; imagined-state label correlation ρ∈{−.5,0,.8}; false-positive update gate f∈{0,.01,.05,.2,1}, T∈{200,2000},20 seeds. True self gate sensitivity .9. Physiology target is s; when self-attending the active representation encodes s, otherwise it encodes imagined o with physiology correlated atρ. Both use exactly the same feeling-code in main test. Fit a linear least-squares best-case predictor from accepted samples (not a claim of neuronal implementation); independent query target is o. With equal variances, population gain is [π*.9+(1−π)*f*ρ]/[π*.9+(1−π)*f]. Verify that equation and known-positive perfect-gate case before interpreting failure. Compare unconditionally updated f=1 and source-oracle gate f=0. Held-out seeds if promoted; do not tune a biological gate rate or claim these hypothetical rates are measured.
