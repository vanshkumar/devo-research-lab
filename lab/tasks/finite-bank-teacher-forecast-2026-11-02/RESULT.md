# CLOSE — a small shared-environment forecast effect

November 2, 2026. **The finite bank measurably widens this source-prior reward forecast, but neither predeclared materiality threshold is reached. The effect also occurs without learning and is closely reproduced by a Gaussian common-drift control. Close this allocation rather than fund a human refit or a claimed correction.** This is a conditional simulation result; no actual participant outcome, fitted-results object or future logged path was read.

## What was tested

The linked Kool2016 task draws one1000-entry N(0,.025²) bank and reuses it across all four reward probabilities, including practice/main. It initializes main probabilities from eight equally likely arrangements of [.6,.4] and [.25,.75], then applies its literal two-statement reflection into[.25,.75]. We compared this law with fresh iid Gaussian increments, keeping the initialization, reflection and125main opportunities identical.

The fixed learner is the original source's hybrid SARSA/model-based rule, initialized at Q=0 as its likelihood function specifies, with the entire factorized bounded parameter prior in set_opts.m. It is a source-prior predictive ensemble, **not newly inferred human parameters or a validated population distribution**. The forecast receives no practice observations; integrating the bank's unconditional prior is lawful. Main learner initialization is explicit and does not assert that humans forget practice. Conditional forecasts after informative practice/prefix observations were not tested.

The [pretest protocol](PROTOCOL.md) froze one configuration, root seed2026110201,131072independent virtual experiments, the first65536 for prediction and final65536 for evaluation. Parameters and nonteacher uniforms are paired across laws. Each virtual experiment is the independent sampling unit. A uniform-choice control and a Gaussian random-mean control were frozen with it; no policy/parameter/horizon/seed search or pre-main revision occurred. See [freeze](FREEZE.json), [actual run](MAIN_RUN.json), [full results](SUMMARY.json).

## Results

All rewards refer to the full125trial main block. Coverage evaluates the SAME iid-forecast integer interval[53,81] under each law; its iid coverage exceeds90% because counts are discrete.

| Teacher law | Mean hybrid rewards | Predictive SD | Coverage of iid interval |
|---|---:|---:|---:|
| Source finite bank | 67.061 | 8.942 | 89.522% |
| Fresh iid approximation | 67.161 | 8.443 | 91.284% |
| Gaussian common-mean control | 67.069 | 8.926 | 89.420% |

Bank minus iid expected reward is **−.1004**, Monte Carlo99%[−.1462,−.0546], versus the frozen **one-reward** boundary. Its coverage change is **−1.7624percentage points**, MC99%[−2.0402,−1.4846], versus **five points**. The effect is resolved and small under these declared investment cutoffs; it is not zero, a universal equivalence bound or evidence that all future uses are safe.

Predictive variance rises **12.175%**, ratio1.12175/MC99%[1.11106,1.13245]; SD increases.4992reward[.4577,.5407]. These are useful specifications to retain, even though they do not cross this study's primary investment gates. A postvalidation distribution-free Monte Carlo check using two empirical-CDF DKW bounds plus a union bound gives a conservative99%absolute coverage-change upper bound **4.4668points**, still below the original five-point boundary. It holds uniformly over interval cutoffs, avoiding reliance on unaccounted quantile estimation. This is numerical uncertainty about the implemented distribution, not biological sampling confidence.

## The strongest simple explanation survives

For bank entries G_j, write mu=mean(G). Its prior SD is.025/sqrt(1000)=.00079057. Distinct increment draws have covariance Var(mu)=.025²/1000. The first exact calculation gives unreflected cumulative variance sigma²[t+t(t−1)/1000] and between-option covariance sigma²t²/1000; at124updates this is12.3%extra variance and.11042cross-option correlation. An independent exhaustive small-bank multiplicity calculation agrees. Reflection changes the numerical consequence, so this identity was not treated as the practical result.

The Gaussian control retains a common mu and adds independent residual noise of SD.025sqrt(1−1/1000). It matches all increment means/variances/distinct-event covariances while removing finite-support collisions and random empirical higher moments. Its hybrid predictive SD is8.926 versus8.942 for the bank; bank/control variance ratio1.00354/MC99%[.98674,1.02034]. Their coverage difference is.1022points[−.2940,.4985]. This supports ordinary shared-environment uncertainty as the important explanation at the tested resolution, rather than an effect that requires bank discreteness.

With **uniform random choice and no learning**, bank/iid reward variance ratio is1.14932[1.13946,1.15919], with SD8.166versus7.617. The bank effect therefore does not require an inferred learning rule. The exact ensemble mean is62.5by symmetry; all three simulated conditional means and total-variance identities pass their numerical known-answer checks. This does not prove that the hybrid's entire effect is identical to the uniform effect or identify a biological cause.

## Closest actual implementation and claim limits

[Gijsen et al.2022](https://pmc.ncbi.nlm.nih.gov/articles/PMC9586964/) already simulates fitted choices. We inspected its actual code at commit86327886bbc13d6a3a93f2861335a8b1fd507df8. The [environment generator](https://github.com/SamGijsen/AI2step/blob/86327886bbc13d6a3a93f2861335a8b1fd507df8/utils/twostep_environment.py), with its pinned helper, uses fresh truncated normals and also differs in initialization. Its model constructor calls that generator. Crucially, the [MLE path](https://github.com/SamGijsen/AI2step/blob/86327886bbc13d6a3a93f2861335a8b1fd507df8/MLE.py) passes observed actions/outcomes to perform_trial, replacing generated interaction observations. The teacher-law difference is therefore **not evidence that its conditional fitted likelihood is changed**. The exact call site for the paper's20-run simulation analysis is not in the inspected tree; its published simulation output/result impact remains unverified. Our controlled iid arm isolates only the bank approximation and is not a reproduction of that library's whole environment.

No novelty or published-error claim is earned. This is conventional latent shared-environment dependence priced in one source-specific predictive calculation. The task source's exact deployed version and external code/data licensing remain uncertified; code inspection is not deployment proof. No human fit, empirical test, acquisition-transport result or independent adversarial review was performed. The original question about behavior-inferred learning rules supporting useful acquisition forecasts remains unresolved.

## Reliability, failures and resources

The [first calculation](FIRST_CALCULATION.json) ran nativeexit0 at21:58:36.168UTC, before22:11:29. The [independent scalar reconstruction](REFERENCE_CHECKS.json) matches all16constructed experiments/three laws: all actions/Q/totals exact, choice probabilities within3.33e−16 and expected totals within1.43e−14. Independent branch reflection agrees on20001gridpoints; zero drift makes the laws identical and gives uniform mean62.5/variance31.25 exactly. The main batch exited0 at22:06:02.622UTC; no failed scientific execution or repeat batch occurred. The [postvalidation audit](POSTVALIDATION_AUDIT.json) reads only saved experiments and retains every frozen pin. These within-author checks establish numerical agreement, not independent scientific review.

Eight requested public operations/TWOmethod families/5MBconservative ingress allowance/200MBseparate additional read-hash-decode booking against250MB/maximum measured scienceRSS131792896bytes against800MB. One scientific process/thread; jobs0. Exact known read components and allowances are in [resources](RESOURCES.json). Complete physical I/O, provider/runtime/host peaks and transfer bytes remain unknown; the allowances are not certification of those quantities. [Failed tool paths](FAILURES.md) and [native exits](NATIVE_EXITS.json) are preserved. The predecessor's full typed raw/auxiliary exposure survives unchanged; no human MAT/cache was reopened and all protected/closed datasets remain closed.

Research decision: retain the bank/random-effects distinction in any later legitimate simulator, but **do not invest further in this particular approximation concern or tune on this simulation family**. Reopening would require a separately justified material conditional-bank or behavior-forecast consequence; the present point spread alone does not supply it. No automatic next experiment is requested. PI retains the scientific investment decision, unfinished native goal and active operator heartbeat. One bounded terminal report follows; this worker then finishes.
