# Independent review: accept the finite result, narrow the selection interpretation

2026-10-31. Fresh reviewer `01a193bf-8551-79e3-9fb8-7b342ed7784b`, distinct from author. **Bank the weak predictive result and the explicit identification ambiguity; close further archive fitting.** The numerical claims reproduce. The strongest latent witness requires substantial first-courter interaction in selection and relaxes the earlier global noneligible-emission restriction. It does not demonstrate a biological selection or learning mechanism.

## Independently reconstructed evidence

The original CSV has462rows/15dates,394trials with any recorded courtship,215with two courters,377matings and205eligible choices. All462row joins match. T/C1/C2 eligible/copy counts are64/40,74/46,67/42. The three matings without recorded courtship are source CSV lines2,398,437; they remain recorded outcomes. No single-courter mating chooses the opposite recorded color. Reference is the first demonstration in T/C1 and the sole second-period demonstration in C2. Supplied copying annotations were not used as outcomes. [Counts](COUNTS.json), [rows](ROWS.csv).

An independent feature implementation enumerates the15joint states and evaluates saved fold coefficients; no author estimator/helper was imported or run. Every row's direct15cell probability agrees with its sequential log-likelihood. All1,848saved model-by-trial loss rows reproduce within1.78e−15; aggregate losses within4.45e−16, contrasts within3.34e−16 and eligible-only aggregates/contrasts within1.12e−16. The six full fitted context laws match within5.90e−17. Fifteenfold date separation and each stage's actual training counts check out. Independently reconstructed objective/gradient values for365saved original empirical stage fits agree within1.68e−12/8.11e−15; this review's central-difference gradient check differs by1.47e−9. These validate fixed-coefficient reconstruction, not an independent optimizer run. [Loss comparison](LOSS_COMPARISON.json), [fixed reconstruction](FIXED_COEFFICIENT_RECONSTRUCTION.json), [optimization](OPTIMIZATION_AUDIT.json).

P-versus-E gains0.01140644nat/joint trial with date-bootstrap interval[−0.00093528,0.02461728], and0.02691020nat/eligible choice[0.00036690,0.05540759]. The joint lower bound fails the declared joint-and-conditional rule. P-versus-cancellation also fails. In T, the pooled eligible gain0.02766678has interval[−0.04128108,0.08537416]; equal-date gain is−0.00117989. The eligible-only and first-courter-integrated calculations reproduce too. Dates are an uncertified dependence proxy; fixed-fit resampling excludes refit/exploratory-selection uncertainty and is not calibrated population coverage. This does not support equivalence or a causal treatment effect.

## Full-cell witnesses and the contrary test

W means a hypothetical reference-color preference in a standardized two-courter situation. Only eligible choices are assumed to reveal W. This consistency assumption is not observed missing-choice data.

The empirical T common-R construction independently matches every15cell exactly in rational arithmetic. At R5/3, theta=1/2; at R2, theta=5/11. It retains one global noneligible outcome kernel independent of W. Its latent preference can associate with first-courter category. The compact fitted six-context construction also reproduces, with empirically weighted T no-preference tipping R1.5453637704557108 and R2giving mean theta0.4363191043790261. The weighting is by the actual treatment/reference-color counts, not equal color weights. All six fitted laws normalize and match to floating precision. [Empirical witnesses](EMPIRICAL_WITNESSES.json), [compact witnesses](COMPACT_WITNESSES.json).

The stronger aggregate-T construction imposes W independent of first-courter category F, where F is **reference first, opposite first, or no recorded courtship**. Exact arithmetic verifies identical F marginals under both W types and all15cell equality at theta1/2and9/20. The feasible interval is[23/55,17/23]=[0.418182,0.739130]; theta3/8fails because a required gate exceeds1. This is a compatibility interval for the empirical table under assumptions, not a population interval. Independence is imposed in the aggregate reference-coded T population, not separately certified conditional on every reference color/covariate.

At theta1/2the necessary channel is:

| First courter F | Eligible reference/opposite counts | P(E\|W=ref,F) | P(E\|W=opp,F) | Conditional risk ratio |
|---|---:|---:|---:|---:|
| Reference |23/6of55|46/55=0.83636|12/55=0.21818|23/6=3.83333|
| Opposite |17/18of69|34/69=0.49275|36/69=0.52174|17/18=0.94444|
| None |0/0of18|0|0|Undefined0/0|

The decisive contrary check distinguishes three claims:

1. **Aggregate R5/3 and W–F independence can hold simultaneously.** The stronger theta1/2witness already proves this exactly. A common R across treatment/reference contexts does not mean a common R within F strata.
2. **A common conditional R across the two eligible F strata cannot hold with W–F independence on this empirical law.** Bayes' rule requires `odds(q_F)=odds(theta)*R_F`. Hence every interior theta requires `R_ref-first/R_opp-first = (23/6)/(17/18) = 69/17 = 4.058824`, log interaction1.400893. Both observed choice types exclude degenerate theta0/1; the no-courtship category supplies no defined conditional risk ratio. This dependence is necessary under the stronger assumption, not a selected fitted parameter.
3. **The original single global noneligible kernel cannot also preserve W–F independence.** Its three F-marginal equations require theta5/8,29/23and−17/277respectively, so there is no simultaneous solution. The stronger witness uses a noneligible kernel within each F and permits the global noneligible kernel to depend on W (maximum cell difference0.288264at theta1/2). Do not pool restrictions from the two separate constructions into one apparently mild process.

[Exact contrary evidence and equations](CONTRARY_COMPATIBILITY.json). Positive/null/limiting controls include a feasible synthetic common-conditional-R/W–F-independent law with equal selected rates, MAR, an E=1boundary that excludes R2, and preferred/equal early-acceptance examples. [Controls](EXACT_CONTROLS.json).

## Waiting interpretation and provenance limits

Under independent W/F, eligible consistency, eligibility requiring refusal of the first male, at least as much early acceptance of a preferred first male, and equal later eligibility completion across W within F, waiting implies `q_ref-first <= theta <= q_opp-first`. The survival/completion factors cancel to yield the stated inequality. Actual23/29versus17/35reverses it: difference312/1015=0.307389, saved15date bootstrap[0.138993,0.465620]. Thus that restricted account cannot exactly generate the empirical law. Unverified sequencing, different later completion, preference/order dependence or other channels lie outside it. No latency fields support a hazard mechanism here. [Derivation/counts](WAITING_AUDIT.json).

All9manifest input pins and33stable author-artifact pins pass, including the original CSV, Rmd and saved source responses. Cached source excerpts confirm first/second courtship/mating definitions, one-use flies, unavailable simultaneous block identities and close2018first-courter/choosiness work;2024already reports a primacy trend. Publisher/Dryad checksum linkage is checked against the saved metadata. No new network verification, deployment/assignment certification or final-publication/archive correspondence is earned. [Source evidence](SOURCE_EVIDENCE.json), [source linkage](SOURCE_LINKAGE.json).

Author optimization rechecks are inspected as saved evidence: originals have successful flags; one synthetic and five tighter-fit stage flags remain unsuccessful despite small gradients. Tighter-refit maximum probability/loss changes4.11e−7/1.67e−6are inherited recheck results, not new independent fits. Two review target-definition mismatches (reference-color weighting and bootstrap date frame) were corrected and preserved; neither changes the scientific decision. [Failures](FAILURES.md).

**Investment implication:** bank the weak predictive tendency and this conditional identification result; close archive model repairs. A future empirical proposal would need an independently justified measurement/manipulation that constrains the preference–eligibility channel and chronology. More selected choices alone do not supply that missing constraint. No successor is commissioned by this review. All462rows/old social findings remain consumed, protected/other-branch data unchanged; jobs0. [Resources](RESOURCES.json), [reproduction](README.md).
