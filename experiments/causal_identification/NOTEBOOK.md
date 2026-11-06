# Pilot C1 — which subsystem generates recurrence?

**Decision: keep as a methodological constraint and design lesson; retire as a standalone novelty bet.** Completed mathematical counterexample, numerical verification and finite-sample follow-up. No biological mechanism was tested.

## Hypothesis and alternatives
The uncertainty is whether a recurrent-looking neural trajectory plus observed behavior uniquely establishes internal neural recurrence. Alternatives are internal recurrence, recurrence supplied through measured external feedback, or a mixture. The criteria, parameters and expected interpretations were saved in [PLAN.md](PLAN.md) before outcome execution.

## Result and exact argument
Let x[t+1]=A x[t]+B y[t]+e[t], y[t]=x[t], e[t] iid N(0,.1²I), and F=.94 R(.18), a stable 2D rotation. Then x[t+1]=(A+B)x[t]+e[t]. For every A=cF and B=(1−c)F the complete joint observational law of neural x and feedback y is identical, including all lags and spectra, given the same initial distribution. The models differ causally because intervening on y replaces the equation y=x.

For c=1 vs c=0, the paired 2,000-step paths agree exactly in the executed floating-point calculation (maximum x and y deviation 0). Across c=0,.1,…,1 the conditional Gaussian negative log-likelihood was identical at 2029.4808317786426 (constant omitted). The [x,y] regression design has rank 2 rather than 4; its singular values are approximately 19.07,18.17,4.2e−15,2.2e−15. This is an algebraic nonidentifiability, not a low-power failure. The stationary covariance must be .0859106529 I; substitution into the Lyapunov equation leaves max residual 8.54e−19.

A one-step clamp do(y=0), initialized at x=(1,0), predicts means (.924813,.168288) under internal recurrence and (0,0) under external-feedback recurrence. Separation .94 exceeds the innovation SD .1. The exact Bayes classification error for equal priors is Φ(−.94/(2×.1))=1.30e−6. Independent simulated 10,000-trial samples per mechanism produced zero classification errors, which is compatible with, and does not improve upon, that exact probability. The sample mean separation is not an empirical biological effect. Initialization at amplitude one is a deliberately discriminating, readily controlled simulated case.

## Stronger test: independent excitation can repair identification
Set A=.2F, B=.8F and y=x+qz, z iid standard Gaussian and independent of e. Fit A and B jointly by least squares after 200 burn-in samples with 2,000 observations. No estimator or setting was tuned after looking at results. Fifty exploration seeds and fifty separately seeded verification runs were specified in advance. They were executed in the same script; therefore the latter are a fixed-setting verification set, not a post-selection untouched empirical validation set.

Verification seed results (Frobenius errors; across-seed median; B bracket = 10th–90th percentile):

| Excitation q | B error | F=A+B error | Design rank |
|---|---:|---:|---:|
| 0 | .3991 [.3959,.4048] | .01494 | 2 |
| .01 | .4498 [.2150,.5778] | .01490 | 4 |
| .03 | .1507 [.0716,.1925] | .01418 | 4 |
| .1 | .04593 [.02132,.05724] | .01100 | 4 |
| .3 | .01537 [.00706,.01904] | .00559 | 4 |
| 1 | .00458 [.00212,.00571] | .00181 | 4 |

At q=0 the minimum-norm regression arbitrarily divides F nearly in half; B error .399 is not an estimated identifiability bound or an error that more data can necessarily remove. At q>0 the residualized feedback has variance about q²I, so coefficient error scales approximately as .1/(q√T) per coefficient. Actual error scales close to 1/q. Tiny full-rank excitation makes identification possible yet practically imprecise. Larger q also raises state variance, which helps F estimation; the F improvements are not attributable solely to design conditioning.

## Adversarial checks and surviving objection
- The main proposition follows analytically by substitution and equality of conditional densities, independent of any software test. A separate scalar/list recurrence exactly matches the internal-mechanism simulation.
- The strongest objection is correct: this is a restricted deterministic-feedback model, not a universal claim about passive recordings. The planned q>0 controls actively break the nonidentifiability and recover parameters. Known B or known A would also remove the ambiguity. Rich delayed feedback, structural restrictions, or independent process noise in measured behavior can change identifiability; the classic positive results in SOURCES.md matter.
- Direct joint regression and independently computed residualized (Frisch–Waugh–Lovell) B estimates agree to at most 1.2e−14 across all nonzero-q runs. Two different noise-seed sets give the same q/error regime. This validates this known model and estimator, not general nonlinear/noisy partial-observation identification.
- There is no measurement noise in x or y. Ordinary least squares would generally require revision under errors in those variables or innovation–input dependence.
- The simulation is stochastic damped rotation, not a deterministic stable limit cycle. It cannot establish whether a worm has an intrinsic attractor.
- Prior work makes the broad observation established background. The useful campaign contribution is an inspectable counterexample tied to an experimental-design threshold, rather than novelty.

## Commands, execution history and outputs
From repository root:

```sh
.venv/bin/python experiments/causal_identification/run.py > experiments/causal_identification/run.log 2> experiments/causal_identification/stderr.log
.venv/bin/python experiments/causal_identification/plot.py
```

Requirements: Python 3.9+, numpy; figure additionally matplotlib. The workspace dependency lock is maintained by root. Numpy version used: 2.0.2. Seeds and parameters are in config.json. Raw outputs: exact_checks.json, per_seed.csv (600 fits), summary.json, run.log. Figure: excitation_errors.png. No external raw data.

Initial run issue: macOS numpy matmul emitted overflow/invalid/divide-by-zero warnings even though all returned values were finite. The first code and numerical outputs are preserved in initial_blas_run/; initial warning text was observed in the tool output, not captured in a stderr file. We replaced matrix contractions with explicit np.einsum, reran all 600 fits, and got **identical numeric summary values**, with empty stderr.log. This was an implementation check, with no scientific parameter changes. Do not simply suppress such warnings in future investigations.

The wider nonlinear/latent biological question remains open. Next informative action would be to identify a real dataset with randomized known input or body/feedback clamping, and explicitly test whether its excitation spans the neural state directions needed by the proposed mechanism. More passive trajectories alone cannot remove the demonstrated ambiguity without added assumptions.
