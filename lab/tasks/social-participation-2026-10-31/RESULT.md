# Joint participation and social choice: a small predictive lead, unresolved preference

2026-10-31. Completed bounded investigation; all462original rows and old findings remain consumed exploratory evidence. **The primacy term survives in point prediction, but fails the declared joint decision rule. The complete recorded outcome distribution does not identify the sign of a standardized latent preference under the stated selection channels. A simple accept-first/wait explanation is challenged rather than established.** Independent review is still required.

## What the record actually supports

The unchanged27,854-byte CSV matches its Dryad/publisher SHA256. Reconstruction independently recovers64/74/67eligible trials and40/46/42first/unique choices in T/C1/C2. There are377matings,394trials with any recorded courtship,215with two recorded courters,205with two courters and mating, and3matings with no recorded courtship. Those three remain their own observed states; no choices were imputed for nonmatings. No single-courter mating chooses the other recorded color.

The joint observation has15possible recorded states: five courtship patterns (none, one green/pink, both green/pink first) crossed with no/green/pink mating. [RECONSTRUCTION.json](RECONSTRUCTION.json) and [reconstructed.csv](reconstructed.csv) retain all rows/states. The CSV has courtship order but no courtship/copulation timestamps; a latency/hazard mechanism is unrun. One row is one trial, with one-use flies according to Methods. Simultaneous blocks and picture identities are missing; dates/devices do not recover them, and treatment random allocation is uncertified.

## Actual predictive comparison

[PROTOCOL.md](PROTOCOL.md) preceded all new fits. Four fixed models use penalized logistic factors for any courtship, first color, second courtship, mating and mating color. The expression model predicts opportunity/participation from treatment, demonstration alignment and courtship state, with no direct demonstration term in choice after courtship is given. Primacy adds one shared nonnegative first/unique-demo coefficient to choice. Cancellation gives the single-demo groups that coefficient and zero conflicting-demo evidence in T. This is a small specified family, not an exhaustive mechanism comparison. Fixed ridge1; no tuning or model search.

All15recorded dates were left out in turn before fitting their predictions. This is consumed-data exploratory separation. The table reports natural-log loss; lower is better. “Eligible choice” conditions on actual courtship state and mating and contains no fabricated choices.

| Model | Joint/all462 | Choice/all377matings | Choice/205eligible | Choice/64Teligible |
|---|---:|---:|---:|---:|
| Marginal treatment/color |2.672881|0.700287|0.704940|0.714575|
| Courtship/expression E |2.190597|0.413927|0.715198|0.709371|
| Primacy P |2.179191|0.399949|0.688288|0.681704|
| Cancellation C |2.184480|0.406431|0.699896|0.715441|

P gains **0.011406nat/joint trial** over E, date-bootstrap95%interval **[-0.000935,0.024617]**, and **0.026910nat/eligible choice** [0.000367,0.055408]. The prespecified rule required at least0.01nat on both targets and positive lower bounds; joint uncertainty fails it. P versus cancellation gains only0.005289joint [-0.003936,0.016083] and0.011608eligible [-0.009133,0.033460]. No clear primacy-versus-cancellation winner is earned.

For T alone P gains0.027667eligible-choice nat versus E [-0.041281,0.085374]; equal-date gain is **-0.001180**, compared with the positive pooled result. Modeling participation has not explained away the point tendency, but neither has it made that tendency robust. E's large0.482284joint gain over the marginal baseline comes from participation and single-courter choice associations; E slightly worsens eligible choice. Joint fit alone would have hidden that failure.

The separate eligible-only primacy model has loss0.678763, versus cancellation0.689587; gain0.010824 [-0.013263,0.035846]. Integrating first-courter order out of the joint model also preserves the small point lead. [COMPARISON.json](COMPARISON.json) includes every fixed comparison, equal-date results and5000paired date resamples; [CV_LOSSES.csv](CV_LOSSES.csv) retains individual losses. These intervals use an uncertified date proxy and omit refitting/exploratory-selection uncertainty; they are not calibrated population coverage or equivalence bounds.

## An explicit ambiguity, with a consequential restriction

Define W only hypothetically as preference in a standardized two-courter situation. Assume observed color reveals W when eligible; outside eligibility it does not. If e is eligibility, q selected reference choice and R the eligibility risk ratio between W types,

`logit(P(W=reference)) = logit(q) - log(R)`.

For T, e=64/142 and q=40/64. R=1 gives latent preference0.625; R=5/3 gives0.5, with eligibility probabilities0.56338versus0.33803; R=2 gives0.45455. Each construction reproduces **all15observed joint cells**, retaining nonmatings and single-courter choices. The substantive restriction is a common noneligible emission distribution independent of W; the eligible first-courter distribution conditional on choice is retained. This is one sensitivity degree of freedom after the observable law is fixed, not an estimate of biological selection.

It also works on the compact fitted P law: one common R=1.545364 across all six treatment/reference-color contexts gives mean T latent preference0.5; R=2 gives0.436319. All six joint distributions remain identical, with numerical error<=8.33e-17. [SENSITIVITY.json](SENSITIVITY.json) saves every emission matrix, prediction and infeasibility/limiting control.

The prespecified first-courter sensitivity was made concrete prospectively in [FIRST_COURTER_CHECK_PLAN.md](FIRST_COURTER_CHECK_PLAN.md), after the main result, and remains postvalidation. Requiring **W independent of first-courter category within T** narrows the feasible latent preference interval to **[0.418182,0.739130]** for the observed table. This is an algebraic compatibility interval under assumptions, not a confidence interval. Both0.5and0.45still reproduce all cells exactly while preserving identical first-courter marginals across W;0.375fails because a required eligibility probability exceeds1.

The stronger no-preference witness is demanding: when the reference male courts first, eligibility must be0.83636for reference-preferring versus0.21818for opposite-preferring types (risk ratio3.8333). When the opposite male courts first, the corresponding values are0.49275and0.52174 (ratio0.9444). Thus the aggregate5/3ratio should not be advertised as a universally mild or independently supported selection process.

Under an additional simple accept-first/wait account—independent W/first courter, at least as much early acceptance of a preferred first male, and equal eligibility completion after waiting—selected copying must satisfy `q(reference-first)<=theta<=q(opposite-first)`. Actual T rates are23/29=0.79310versus17/35=0.48571, the opposite order. Difference0.30739has descriptive date-bootstrap interval[0.13899,0.46562]. This challenges that restricted account; it does not prove learning, causal selection or all waiting models false. [FIRST_COURTER_SENSITIVITY.json](FIRST_COURTER_SENSITIVITY.json) retains the successful and failed witnesses; [FIRST_COURTER.json](FIRST_COURTER.json) shows the contrasting control-group strata.

## Reliability, prior work and decision

Known-generator g=1recovers1.02349and positive joint/eligible leads; g=0recovers0with leads around1e-9. Gradient finite differences agree within2.65e-9; all15probabilities normalize and factorized/direct likelihoods agree. Reinitialized tighter fits of all105empirical fold/model combinations change six-context probabilities by<=4.12e-7and held-row losses by<=1.68e-6. All original empirical optimizer flags were successful. The original one non-success flag is reproduced in a synthetic marginal fit with projected gradient9.53e-7; tighter rechecks introduce five additional line-search flags with gradients<9.2e-7. Flags are preserved, not called convergence. Color relabeling/restarts differ<3.5e-8. [CONTROLS.json](CONTROLS.json), [CHECK_RUN.json](CHECK_RUN.json) and detailed rechecks separate numerical reliability from scientific identification.

The2024primary paper already reports a primacy trend and selects two-courter matings; the2018Monier et al. study already models first-courter identity, double courtship and choosiness and discusses exclusion through early acceptance. This run adds an explicit finite comparison and constrained full-record witnesses, not a novel general selection principle. Sources and immutable pins are in [SOURCES.md](SOURCES.md)/[MANIFEST.json](MANIFEST.json). Archive/publication-version correspondence remains unresolved; no publication refutation or neural mechanism is established.

**Recommendation:** bank the weak predictive preference signal plus the quantified identification limit; do not invest in further fitting of this archive to infer updating versus expression. The next useful allocation is an independent audit of the full-record/first-courter witnesses and the fixed comparison. Any later empirical proposal needs a separately justified measurement that constrains the preference–expression channel, not merely more selected choices or old ABB power. No new experiment/data acquisition is authorized by this result. Jobs0; lab continuation/heartbeat remain PI responsibilities.

Exact execution/resource accounting is in [RESOURCES.json](RESOURCES.json). Recorded successful-process peak75,579,392bytes;6public source commands across3toolcalls, with conservative ingress/read allowances and failed passes preserved. No protected inputs, original edits, outside contact, credits/reset or other branch repair occurred.
