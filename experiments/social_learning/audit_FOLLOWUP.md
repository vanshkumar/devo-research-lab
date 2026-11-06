# Adversarial follow-up review — 2026-10-28

Reviewed FOLLOWUP_PLAN.md, followup.py, followup_summary.json and design_power.csv. No broad sweeps rerun and no root code changed. This is an audit of equations, targets and interpretation; it is not new empirical confirmation.

## Verdict

**No new computational blocker found.** The reported counts, likelihood targets and conditional design calculations have coherent meanings. Required limits on interpretation are detailed below; the public-code discrepancy cannot establish that the published GLMM was actually fitted using that file.

## Gaussian quadrature and regression targets

For date group j the implemented likelihood is the integral of the product of Bernoulli probabilities conditional on a common normally distributed intercept. `hermgauss` approximates the standard-normal integral using nodes `sqrt(2)*sigma*z` and weights `w/sqrt(pi)`; the log-sum-exp is applied **after** summing conditional log likelihoods within each date. These transformations and grouping order are correct. Dropping binomial coefficients is appropriate for individual binary observations.

The three fitted targets correspond to the independent audit:

- archived_script_all: supplied first/unique-coded responses, n=452, with ineligible rows scored zero;
- eligible_first_single: n=205, first/unique copying;
- eligible_last_single: n=205, paper-defined last/unique copying.

The 40/80-node coefficient differences (<5.2e-7) and nll differences (<6e-12) support quadrature convergence for these fits. The sigma→0 check agrees with ordinary logistic nll within 3e-14. The known-parameter synthetic control recovers beta and sigma within its declared bounds. These are appropriate computational controls, not evidence that date random effects recover the actual experimental blocking.

Both eligible fits hit the imposed `log(sigma)=-7` boundary (sigma=0.0009119), effectively the independent-logit limit. Do not describe this as proving no date heterogeneity. Wald p-values are approximate; the Hessian routine can fall back to fixed-effect Fisher information, and uncertainty in near-boundary variance is not regular. If any p-values are quoted, retain the model, date proxy, approximation and outcome convention. Different p-values from the published block-based GLMM are **not an exact failed replication**, because block IDs and final analysis version are unavailable. Matching quadrature orders verifies integration, not these missing design assumptions.

## Behavioral weight family

The model assigns common positive gain g to a single encountered demonstration and `(1-r)*g` to first-demo copying in the conflicting main treatment. Stable color preference enters with opposite signs depending on the first/unique demonstration color. That coding is internally consistent: it describes probability of copying that color, rather than directly coding pink choice.

The profile maximum at r=0 and likelihood ratios for r=1 (0.1323) and r=2 (0.00411) are meaningful **within this constrained family**. They are not posterior probabilities, Bayes factors, causal update weights or direct measurements of memory. The family assumes common single-demo gain across slots/treatments, stable color bias, its link function, and nonnegative g and r in [0,2]. The profile uses independent Bernoulli likelihood on the selected eligible trials and has no subject holdout. Alternative updating/saturation, context-sensitive attention, initial preferences and post-exposure selection can yield similar observed behavior. No conclusion about a neural first-encounter gate follows.

Especially avoid “same copying rate” as evidence of equivalence or absence of updating. Observed rates are close (T 40/64=0.625; C1 46/74=0.6216; C2 42/67=0.6269), but no equivalence margin or equivalence-powered design was specified. Appropriate wording: **the observed first/unique copying proportions are similar, and these data do not resolve the behavioral effect of the second demonstration with useful precision; this does not establish that updating was absent.**

## ABB design power

For sequence A,B,B, a persistent first-encounter gate predicts `P(A)=logistic(g)`; symmetric additive evidence with equal gain per encounter predicts net evidence `-g`, hence `P(A)=1-logistic(g)`. These predictions are correct for those particular extensions to a new sequence. The test threshold is the smallest upper-tail count with size ≤0.05 under the accumulator, and power is evaluated at the gate probability. This is a one-sided simple-versus-simple design calculation, not a generic hypothesis test against chance.

Independently enumerated a saved cell using Python `math.comb` rather than scipy's binomial survival function; its size and power matched floating-point precision. No off-by-one error was found. At the fitted gain the 64-eligible-trial scenario has power about 0.992; that number is conditional on an estimate obtained from the current data, known gain, independent eligible trials, identical sequence gain and those two fixed candidate models. The low-gain scenario materially reduces power. Additional exposures can change attention, time delay, eligibility and g itself; current treatment rates do not validate that transport. Report eligible rather than enrolled n, and do not call this an optimal or mechanistically identifying design.

## Surviving assumptions to carry into final report

Public supplement provenance/final analysis version; absent experimental block IDs; post-exposure eligibility; limited precision of group contrasts; constrained model family and untested extension to longer sequences. The completed analysis supports auditing these assumptions and selecting a more discriminating experiment, not a biological mechanism or a definitive refutation of the original paper.
