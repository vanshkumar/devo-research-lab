# Closed-loop causal identifiability — frozen pilot plan

Written 2026-10-28 before experiment execution. This is a mathematical counterexample plus a finite-sample design study, not an empirical biological result or novelty claim.

## Question and discriminating test
Can a recurrent-looking neural trajectory, even when paired with a behavioral feedback trace, uniquely locate the recurrence inside the neural subsystem?

Use a fully observed, discrete-time Gaussian model: x[t+1] = A x[t] + B y[t] + e[t], y[t] = x[t] + q z[t], with e independent N(0, 0.1² I), z independent N(0,I). x and y have dimension two. Fix F=0.94 R(0.18 radians). Under q=0, only F=A+B is identified. Compare internal mechanism (A=F,B=0) and feedback mechanism (A=0,B=F). Same x[0] and noise must produce identical x and y paths. Any convex decomposition A=cF,B=(1-c)F must have identical observational conditional likelihood. Analytic design rank must be 2, not 4. A behavior/feedback clamp y=0 must produce different conditional means: F^h x[0] versus zero for h>=1. This is not a proof that real worm feedback is deterministic or that observational identification is universally impossible.

## Minimal case and planned substantive tests
1. Minimal: T=20, seed=1, compare two extreme mechanisms and design rank.
2. Exact counterexample: T=2,000, seed=101; report max paired-path deviation and likelihood differences across c=0,0.1,...,1. Compare independent direct recurrence with model recurrence.
3. Clamp positive control: 10,000 independent one-step trials at x[0]=(1,0), same noise coupling for paired contrast; also compute exact standard error and distributional separation. Do not use shared noise to overstate empirical detectability: classification error must use independent one-step samples.
4. Excitation follow-up (planned in advance): true A=0.2F, B=0.8F, T=2,000, burn-in=200, seeds=1000..1049, q in {0,0.01,0.03,0.1,0.3,1}. Ordinary least squares jointly fits A,B with intercept omitted (zero mean known). Report Frobenius errors, singular value ratio, and closed-loop F error. At q=0 use minimum norm solution but call it arbitrary, not consistent identification. q>0 should remove exact rank deficiency; weak excitation may leave finite-sample estimates unreliable.

## Interpretation and adversarial checks
- Exact paths/likelihoods and analytical rank establish nonidentifiability in this class only.
- Claiming universal failure would be invalid: closed-loop identification can succeed with rich input/noise or known controller/model restrictions (see prior work).
- In full rank cases OLS conditional on x,y should be valid because innovation e[t] is independent of contemporaneous x[t],y[t]. Independently recompute B using residualized excitation (Frisch-Waugh-Lovell) and A from F minus B. Compare coefficients to direct OLS.
- Hold back seeds 2000..2049 for exact same settings, with no parameter changes, as a reproducibility/generalization check if this becomes a promoted direction. These are simulations from the same known model, not independent biological confirmation.
- Expected practical consequence: observational dynamic summaries should avoid causal interpretation without specifying which independent excitation, intervention, or structural constraints identify mechanism. Quantify rather than merely assert the limitation.

## Resources / reproduction
Numpy only; optional matplotlib for a static research figure. No public dataset needed. Run from workspace with `.venv/bin/python experiments/causal_identification/run.py`. Save config, per-seed CSV, exact-check JSON and summary JSON in this folder. No money, accounts, API billing, private files, uploads, or messages.
