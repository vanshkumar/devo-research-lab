# Prospective numerical protocol

Saved2026-10-31 after the permitted small CSV schema/pin inspection and brief source-definition check, before any new model fit or outcome tabulation. All462rows and earlier findings are already consumed. This is a finite exploratory predictive/identification investigation, with no pristine validation or causal treatment inference.

Question: does a first/unique-demonstration term improve joint prediction of courtship participation, opportunity and mating outcome beyond a small courtship/expression account? Does the full joint record identify an underlying preference, rather than selective revelation of it?

## Observation law and units

One row is one recorded trial; the primary source says flies were used once. Trials share recorded dates and unrecorded simultaneous blocks/pictures. Neither date nor recurring device identifies those blocks. Use date separation as a descriptive generalization check and clustered uncertainty proxy, without claiming certified independence/random allocation.

Reconstruct only colors, not supplied copying annotations. Reference is demo1 in T/C1 and demo2 in C2; T must be contradictory. Q has five courtship states: none recorded, one green, one pink, both green first, both pink first. M has three outcomes: no mating recorded, green mating, pink mating. All15 Q-by-M cells remain possible as recording outcomes, including matings without recorded courtship and mating to a male not recorded as courting. Verify first/second ordering, distinct colors and missingness. Do not invent hypothetical choices for nonmatings/single-courter trials. Public definitions support order; no exported timestamps support a hazard/latency model or independent pre-copulation chronology audit.

## Fixed finite comparison

Use a sequential probability factorization for the joint15-cell record: A=any recorded courtship; F=green first given A; D=second courtship given A,F; B=mating given Q; Y=green given Q,B=1. This is a factorization of observations, not a causal ordering claim. No fabricated Y for B=0. Treatment features t=[intercept,T,C2]; z=+1/-1 for reference green/pink; f=+1/-1/0 for green/pink/no first courter. Q is four indicators with none as reference.

Four fixed models, no covariate/architecture tournament:

- Marginal treatment/color baseline: each Bernoulli stage uses t alone; Q and mating/choice associations are not modeled.
- Courtship/expression E: A~t; F~t+z; D~t+f+zf; B~t+Q+zf; Y~t+Q. Social alignment may predict opportunity/participation, but Y has no direct demonstration term once Q is given. This is an observational alternative, not proof of absent learning.
- Primacy P: same as E, with one shared nonnegative g*z in Y for first/unique copying.
- Cancellation C: same as E, with one shared nonnegative g*z in Y only for C1/C2 (zero net conflicting-demo evidence in T). It embodies equal cancellation with common single-demo gain, not all possible updating rules.

All fits are penalized logistic likelihood, fixed ridge1 on all coefficients except intercepts, including g; g>=0. No tuning or model-dependent missingness. Save full fitted coefficients, projected gradients, convergence and15cell predictions. Original penalty/failure results survive any numerical fix.

Freeze leave-one-recorded-date-out (15folds) before fitting. Train only on other dates, predict all observations of held date; dates remain consumed. Score joint log loss per all462trials, mating/courtship components, Y log loss per377observedmatings, and Y per205eligible/main64eligible with Q known. Also score P(Y|eligible,t,z), integrating first-courter order with joint probabilities. Fit the separate eligible-only marginal/primacy/cancellation recipes Y~t(+sharedg*z or g*z*nonT), using the same folds, to show what changes after courtship opportunity is modeled. Report both pooled and equal-date comparisons. A substantive predictive lead requires >=0.01nat per joint trial AND >=0.01nat per eligible choice versus its relevant alternative, paired date-bootstrap95%lower>0, with main-T results separately visible. This chosen scale is an investment rule, not a biological constant or equivalence test. Otherwise bank an inconclusive/negative finite result; do not repair the family.

Paired date-cluster percentile bootstrap5000, seed20261031, from saved out-of-date losses. It describes this date proxy and fixed fitted models; it does not include all model fitting/exploratory-selection uncertainty or certify population coverage. No significance hunt or causal claims.

## Consequential sensitivity / observational witness

For a specified standardized two-courter latent binary preference W, assume consistency Y=W only when eligible E=(both courted AND mated). It is a hypothetical preference, not an observed missing choice. Let e=P(E), q=P(Y=reference|E), theta=P(W=reference). Revelation risk ratio R=P(E|W=reference)/P(E|W=opposite) implies logit(theta)=logit(q)-log(R). Gate probabilities are e*q/theta and e*(1-q)/(1-theta), required<=1.

Prespecify R=1,1.25,1.5,5/3,2,2.5,3 and algebraic tipping R=odds(q) for theta=.5; retain infeasible cases. Reconstruct the complete joint table at each feasible R using a single common noneligible emission kernel h(O|notE), independent of W; keep the empirical/fitted first-courter distribution conditional on eligible Y fixed. This imposes a substantive channel restriction and only one sensitivity degree of freedom after the observed law is fixed. Test equality of every15cell, including recorded one-courter choices/nonmatings, rather than only matching selected rates. Execute both the empirical aggregate T witness and a common-R witness across all six treatment/reference-color contexts generated by the compact fitted P model. A common-R no-average-T-preference solution (solve theta_T=.5) and opposite latent tendency, if feasible, earn a finite identification limit. Failure of feasibility is informative. A flexible observation channel is not established biology, and observational equivalence cannot refute learning. No unrestricted saturation alone is a mechanism conclusion.

One prespecified sensitivity step: compare the revelation assumption with an accept-first/wait account using actual first-courter/order strata. Report the observed first-courter/eligibility/copying cells and whether the direction required by the witness agrees with that account; do not label either causal. No hazard fit without timestamps, no new dataset/ABB/version repair.

## Controls, stopping and resources

Known-count reconstruction must reproduce old205eligible,64T/74C1/67C2 and40/46/42first/unique choices. Probability normalization/all15states and likelihood-factorization checks are mandatory. Numerical controls: finite-difference gradient, repeat fit from distinct initial values/tighter optimization, g=0 nesting and color-label invariance. Run fixed known-generator positive g and zero-g negative controls through the same finite fitting/scoring recipe; these validate that procedure in those cases, not universal power or biology. Check R=1/MAR and e=1 limiting cases of the witness; exact matching includes failure cases outside feasibility.

Stop after this fixed comparison/sensitivity/controls or at ceiling. Deadline21:50:53UTC,75minutes from START;12new public requests/30MBingress/350MBadditional read-decode/1GBRSS/one process and numerical thread. Sources/context/output and blocked/failed passes charged conservatively. Three source tool calls so far contain6source/search commands; reserve1MBingress per command for unknown provider traffic (6MB) plus actual saved response bytes, not an exact network measurement. No further sources currently needed. No protected inputs or original edits. Save actual outputs/code, manifest, accounting, STATE/RESULT/README and proposed learning, then one<=400wordreport to current registry PI and finish.
