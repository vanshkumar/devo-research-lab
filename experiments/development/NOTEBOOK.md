# Development pilots: executed account

Date: 2026-10-28. Status: both complete as small synthetic pilots; neither promoted to a main campaign result. PLAN.md was written before computation. Root owns the campaign recommendation and shared files.

## Reproduce

From repository root:

```sh
.venv/bin/python experiments/development/run.py --minimal
.venv/bin/python experiments/development/run.py
.venv/bin/python experiments/development/audit.py
```

Dependency: NumPy 2.0.2 (actual run), Python 3.9.6. `audit.py` uses only the standard library. Final full simulation runtime was 3.07 seconds. Configurations and executed seed list are in `results/config.json`; seeds 0–39 are Monte Carlo repetitions, not independent empirical subjects. All output tables preserve the explored conditions; there was no parameter search beyond the frozen initial configuration. Tests were not used to tune the model.

The first minimal run produced spurious NumPy/Accelerate matmul floating-point warnings on finite inputs. A separate 4,000×3 random matrix check gave finite results and maximum difference 8.9×10⁻¹⁶ from explicit einsum. Main matrix contractions were changed to einsum; the minimal and full runs were then repeated without warnings. No scientific condition was changed. `minimal/` contains the final minimal run, while this paragraph preserves the initial implementation issue.

## D1 — exposure order and robust feature use

Hypothesis/alternatives, initial parameters, and expected interpretations are in PLAN.md. Each schedule saw the same 4,000 examples exactly once. There were 40 independently generated training datasets with paired schedule comparisons within each. Stable core: signed label plus N(0,1) noise. Shortcut: signed label multiplied by a context-dependent sign, plus N(0,0.25²) noise. Training shortcut agreement was 0.95 in the “easy” context and 0.50 in “hard.” Difficulty names refer solely to available correlation here.

Mean accuracy across seeds (percent; across-seed SD shown in parentheses):

| Protocol | Test shortcut 0.95 | Test shortcut 0.50 | Test shortcut 0.05 |
|---|---:|---:|---:|
| One pass easy→hard | 84.18 (1.13) | 84.09 (0.38) | 84.05 (1.14) |
| One pass hard→easy | 95.72 (0.18) | 64.78 (2.17) | 34.08 (4.20) |
| One pass shuffled | 91.64 (0.83) | 81.32 (0.96) | 71.02 (2.53) |
| One pass alternating | 91.56 (0.60) | 81.39 (0.74) | 71.21 (1.99) |
| Common pooled convergence, every schedule | 91.62 (0.38) | 81.47 (0.44) | 71.37 (0.88) |
| Known core-only oracle | 84.17 (0.33) | 84.17 (0.32) | 84.22 (0.26) |

The final neutral context encourages core use and is useful under shortcut reversal. Reversing order makes the classifier lean strongly on the shortcut and wins when that shortcut remains valid. The order effect disappears when the same pooled regularized objective is optimized to convergence: maximum between-schedule parameter distance 1.19×10⁻⁸; maximum gradient norm 1.01×10⁻⁹. The objective is strictly convex because L2 applies to all three coefficients, including intercept, so a unique optimum is expected analytically. Convergence is therefore an informative control, not a competing claim that more optimization necessarily improves robust test performance.

Adversarial/independent check: `audit.py` analytically integrates the known Gaussian-mixture test distribution using `math.erf` and compares it with the sampled test accuracy for every saved classifier. Maximum sample–analytic difference: 0.01387 (2.93 binomial standard errors); all 1,080 correlated table rows lie within three of their marginal sampling SEs. The known core oracle accuracy is analytically Φ(1)=0.8413447. This validates the numerical reading of the constructed task; it is not empirical confirmation.

Decision: **revise, do not promote**. This pilot provides a concrete warning: reporting an easy→hard gain alone cannot distinguish adaptation to the final context from a lasting advantage in representation learning. It does not establish that the order benefit is useless; the chosen final exposure produces real robustness in this task. It also does not challenge nonconvex curriculum learning, human learning, resource development, memory constraints, or Bengio et al.'s experiments. A serious developmental program would need an empirical task, operational definition of complexity, and a stronger learning model. Those additions are not justified merely by this synthetic effect.

## D2 — observational educational gain is not identified by participation and outcome

Both constructed worlds have exactly the same observed joint distribution:

| | Y=0 | Y=1 |
|---|---:|---:|
| T=0 | 0.37 | 0.13 |
| T=1 | 0.13 | 0.37 |

In the selection world, ability U is a fair bit, participation agrees with U 80% of the time, and outcome agrees with U 90% of the time. No intervention on participation changes outcome. In the direct-effect world, participation is randomized and raises success probability from 0.26 to 0.74. Both observational gaps are 0.48. Their average treatment effects are 0 and 0.48.

Primary validation: exact enumeration in run.py matched up to floating arithmetic (5.6×10⁻¹⁷); independent `fractions.Fraction` enumeration in audit.py proved all four entries equal exactly, with observed gap 12/25. Simulations were positive controls for the estimator, not the proof of equivalence.

At N=100,000 per repetition, 40 seeds:

| World/design | Mean estimated contrast | Across-seed SD | Exact population contrast |
|---|---:|---:|---:|
| Selection/observational | 0.48057 | 0.00282 | 0.48 |
| Direct/observational | 0.48032 | 0.00261 | 0.48 |
| Selection/randomized | 0.000030 | 0.00312 | 0 |
| Direct/randomized | 0.47952 | 0.00272 | 0.48 |
| Selection/noisy-pretest stratified | 0.35403 | 0.00274 | 6/17 = 0.35294 |

N=1,000 results, including all 40 repetitions and all designs, are also retained. The pretest is an additional noisy proxy agreeing with U 80% of the time. Its adjustment reduces the bias but does not remove it. The two original worlds were only constructed to match (T,Y); equality including this new proxy is not claimed.

Decision: **retire after extracting the measurement requirement**. The exact counterexample is a reproduction of a well-known identification limitation, not a new scientific finding or an empirical educational effect. Adding more samples of participation and outcome cannot choose between these two worlds. A real research design needs randomization, an appropriate quasi-experiment, sufficiently informative pre-exposure covariates plus an explicit identification assumption, or a sensitivity analysis. This does not imply that every observational educational study is uninformative.

## What remains and what does not

Both pilots fulfill their bounded computational tests and have positive controls. Neither has a real educational dataset, an estimate of an actual human learning mechanism, or evidence of scientific novelty. The recommended campaign allocation is to the root agent's empirical neural-data direction if its controls support it. Only revisit development after identifying a concrete measurable learning outcome and a dataset/design capable of distinguishing the relevant mechanisms.
