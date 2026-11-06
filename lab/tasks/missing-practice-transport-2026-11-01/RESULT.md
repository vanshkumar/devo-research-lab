# Missing practice and a new curriculum: a worked measurement comparison

A bound on hidden practice can constrain a new-curriculum forecast in the declared synthetic model. After two calibrated source-endpoint scores, one calibrated return probe gives worst-case target ambiguity below **0.083** when at most **one** teaching event is missing. With two missing events, compatible mechanisms already differ by **0.12848**, exceeding the frozen **0.10 skill-score** criterion. The useful result is this conditional measurement requirement and its explicit counterexamples; no biological or general identification claim is earned.

The strongest additional check narrows the recommendation: one return probe covers only one direction of interference. Allowing direction-specific retention leaves an attained **0.18665** target gap despite complete source records, known counts and the return score. A separately executed extra teaching event/probe observes the missing direction.

## What was fixed and observed

The learner has two skills, initially zero. Teaching task A increases its skill by alpha_A times its remaining distance to one and multiplies B's skill by retention; B teaching is analogous. Gains are fixed across curricula. The main model assumes the same retention in both directions, between 0.5 and 1. A nonlearning calibrated probe reads skill on a known scale. These assumptions are explicit synthetic choices.

The source teaches an A block, then a B block. Its retained teaching log contains two certificates per task, failure then success, with success meaning pre-update skill at least 0.5. Recording can depend on outcomes/history. The last event in each block is retained. An external guarantee bounds the **total** missing teaching events by K; arbitrary unrecorded task switching is excluded. The target is mean pre-update skill during 12 fresh-state alternating A/B teaching events.

The main comparison explicitly buys two compulsory calibrated observations: skill 0.75 just after each task's own block. Conditional on actual block count n, this fixes the gain to 1 − 0.25^(1/n). Counts and recording remain unknown. Without those two calibrated scores, the original binary certificates with K=4 permit target scores **[0.123946, 0.833333]**. They do not provide the narrower main information set for free.

## Finite-horizon bounds and measurement design

The following numbers use the two calibrated source scores and arbitrary omissions. A count audit reports actual event totals by task. The return probe measures A after the B block without updating it. Its relation is r = 0.75 × retention^(B count). Probe-design bounds cover **all compatible probe outcomes**, rather than only one favorable realized score.

| Missing-event cap K | Source target interval | Worst width after count/full-source audit | Worst width after calibrated return probe |
|---:|---:|---:|---:|
| 0 | [0.259277, 0.671875] | 0.412598 | 0, algebraically identified |
| 1 | [0.231861, 0.671875] | 0.412598 | [0.082218, 0.082227] |
| 2 | [0.204444, 0.671875] | 0.412598 | [0.128481, 0.128491] |
| 3 | [0.186346, 0.671875] | 0.412598 | [0.156598, 0.156607] |
| 4 | [0.168248, 0.671875] | 0.412598 | [0.174643, 0.174652] |
| 8 | [0.123946, 0.671875] | 0.412598 | [0.277790, 0.277796] |

The bracket in the last column encloses the worst **diameter**, with an attained lower bound and a computed monotone-envelope upper bound. It is not a target interval or confidence interval. Each source interval has attaining histories and recording mechanisms. Larger K preserves the K=2 counterexamples, so a uniform 0.10 guarantee under arbitrary omissions fails for every K≥2. Re-auditing already retained certificates removes no mechanisms: the observed label has likelihood one under every compatible world.

At K=4, the prespecified return score 81/256 leaves a finite set of target points between **0.272799 and 0.419821**, width **0.147022**. It must not be substituted for the worst-case design calculation. A binary return certificate is weaker: its possible outcomes leave diameter suprema **0.335483** and **0.289258**. The failure outcome has an open parameter boundary; its upper value is explicitly a supremum.

An outcome-specific logging guarantee changes the answer. If **every successful teaching certificate is retained**, the two source endpoint scores force each true block length to be two or three events. Even with K=4, the calibrated-return worst diameter is then **[0.094127, 0.094135]**, passing the same criterion. This is an additional verified guarantee a deployment would need, not something inferred from its retained successes.

A count audit **plus** the calibrated return identifies both gains and shared retention exactly in the main model. With known reference counts (3,3), bounded error of ±0.04 in each of the three calibrated scores gives a target-diameter upper enclosure **0.072540**; an attained width is 0.072537. This is the largest error tested, not an estimated maximal tolerance or population coverage claim.

## Strongest contrary result and added intervention

The source never measures loss of B while A is practiced, because B begins at zero. In the postvalidation directional model, fix both counts at three, both gains at 1 − 4^(−1/3), and A's retention on B at 0.75. B's retention on A can be 0.5 or 1. Both mechanisms reproduce the **complete own-task source score trace**, the calibrated endpoints, and A's return score 81/256. Their alternating-curriculum targets are respectively **0.283086428 and 0.469738412**. Monotonicity makes these sharp attained endpoints for this fixed-count sensitivity case.

After that source, execute **one known A teaching event**, then a compulsory nonlearning B probe. B's measured score is 0.375 or 0.75 in the two witnesses; dividing it by the pre-event B score recovers the missing retention direction. The event simulator executes the full A update from the nonzero source state, and both recovered parameterizations reproduce the target. This costs an additional intervention and calibrated observation. It does not establish that biological probes are nonlearning or that state-dependent interference is identified.

## Reliability, limitations and allocation

The first exact rational calculation completed at **05:02:59 UTC**, before the 05:15:11 checkpoint. Its coarse parameter grid is preserved. The one development revision replaced that grid with continuous parameters and explicitly priced the calibrated observations. Main choices were frozen before computation. The directional sensitivity was recorded afterward and is labeled postvalidation; it does not replace the main class or margin.

Closed-form bounds have constructive witnesses and proofs in `PROOFS.md`. Checks include 216 formula/event comparisons, incompatible observations, omitted-position brute force, exact limiting cases, 80-digit roots, 12,023 separately implemented probe observations, and feasible coupled calibration triples. The largest high-precision target discrepancy in the independent root reconstruction was 1.11e−16. These are author checks, not independent review. The generic K=0 envelope hit its 50,000-box limit with an upper bound 1.2246e−5; the saved failure remains, alongside the separate exact zero proof.

Manski's partial-identification work and Kallus–Zhou's robust policy evaluation already establish the broader bounding ideas. This bounded source check earns no novelty or complete priority claim. Manski's direct page returned 403; its abstract was available. Licenses and original PDF bytes were not independently certified. No empirical datasets, old raw observations or protected targets were opened. Five public operations, a conservative 5 MB ingress charge and 20 MB additional-read charge are recorded; provider wire bytes/peaks remain unknown. Largest measured local scientific RSS was 23,298,048 bytes; no jobs remain.

Bank this as a conditional design calculation. It shows exactly how total-count guarantees, success-complete logging and direction-specific probes change ambiguity. It supplies no reason to release protected archive outcomes or assume a complete log validates curriculum transport. If the PI finds the calculation consequential, a fresh bounded mathematical review should challenge the observation partitions, sharpness and worst-case envelopes before wider use. Independent review, stochastic sampling calibration, empirical validation and state-dependent learning/retention are unrun.
