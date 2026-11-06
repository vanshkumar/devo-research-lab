# Developmental-environment pilots — prespecified before computation

Date: 2026-10-28. Scope: two synthetic tests; neither is evidence about actual children or educational programs. No external data needed. These are outside the recent worm-dynamics thread.

## D1. Equal exposure, order, and shortcut generalization

Question: Does an apparent easy-to-hard curriculum advantage survive equal exposure, reversed order, shifted evaluation, and convergence on the same pooled convex objective?

Mechanism to distinguish: useful curriculum shaping versus finite-step recency. Synthetic binary task has a stable noisy feature (core) and a context-dependent shortcut. Two training environments have shortcut agreement 0.95 (easy) and 0.50 (hard). Both have identical stable-feature mechanism. All schedules see exactly the same multiset once: easy→hard, hard→easy, shuffle, strict alternating; core-only oracle control. Logistic classifier, L2 regularization, constant step size initially. Evaluate separately at shortcut agreement 0.95, 0.50, 0.05 and report the entire set, not just the flattering environment.

Initial parameters: 40 seeds; 2,000 examples per training context, 10,000 test examples per context; core noise standard deviation 1; shortcut noise standard deviation 0.25; logistic learning rate 0.03; L2 0.01. Minimal one-seed run first; full run afterward. Common full-batch convergence control on the same pooled data uses a strictly convex regularized objective. Optimizer optimality residual and parameter agreement distinguish residual order effects from different objectives. Identical data and initialization are paired within seed.

Interpretation fixed in advance: An order benefit that reverses with evaluation context, or disappears under common convergence, does not establish improved abstract learning. A persistent better worst-context result motivates follow-up only after excluding unequal data exposure and optimizer failure. This linear convex case cannot refute curriculum effects in nonconvex networks, changing plasticity, attention, memory, or humans. No universal easy/hard definition is asserted; labels refer only to shortcut availability here.

## D2. Observational educational gains and causal identification

Question: Can matched observational participation–outcome distributions imply different learning effects?

Construct an exact finite-distribution counterexample before simulation. Selection world: latent ability U∈{0,1}, P(U=1)=0.5; participation T agrees with U with probability 0.8; outcome Y agrees with U with probability 0.9; T has no causal arrow to Y. Causal world: T is fair randomized; outcome probabilities P(Y=1|T=0)=0.26 and P(Y=1|T=1)=0.74. These distributions should agree observationally but differ under randomized intervention: average treatment effects 0 and 0.48. Enumerate exact joint probabilities as the primary check; then simulate observed and randomized samples at N=1,000 and 100,000 across 40 seeds as positive controls.

Additionally use an imperfect pretest X agreeing with U with probability 0.8 in the selection world; quantify residual bias after stratification. This is a limitation illustration, not an observational-equivalence claim including X. If exact enumeration fails, the counterexample is invalid; simulation alone cannot rescue it. If randomization fails to recover known ATEs at adequate N, treat the implementation as failed. No real program efficacy claim follows. This known identification problem is not novel and may be retired once the measurement requirement is made concrete.

## Resource and artifact boundaries

Own only experiments/development/. No paid API, accounts, external messages or uploads. CPU work should be below a few minutes; outputs below 10 MB. Save seeds, dependencies, script, CSV/JSON, source inspection notes, exact reproduction command, observed failures and decisions. Root aggregates shared documents and learnings.
