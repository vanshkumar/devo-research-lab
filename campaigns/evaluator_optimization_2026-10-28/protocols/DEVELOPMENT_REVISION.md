# One actor revision after a failed known-answer control

2026-10-28. Declared after inspecting development plants0/1 and before any held-out plant or revised-actor outcome. The original development processes continue to completion and their complete coordinate-only evidence remains in `results/`. This is an explicit deviation from the initially proposed no-repair/mean75% oracle rule. It changes the actor once; it changes no model, target, plant, reward or protected-data access.

## Decisive observation and algebra

Plant1's true-loss oracle and learned35 actor both choose gain0. Oracle loss falls9.19666→4 and remains there; its shape coordinates never change. The learned35 fixed-gain actor reaches about.0027 loss on the same plant. At gain0 every pure-shape proposal produces identical absent auditory drive and identical cost. Strict coordinate descent cannot traverse that neutral plateau. Longer repetitions of the same polls cannot discriminate reward quality. A pooled75%-mean oracle gate could hide this defining failure even if two other plants succeed.

With centered SD2 features, `L(a,g)=4*(g*g+1-2*g*rho(a))`, where rho is feature cosine similarity to the target. At g0 loss is4 independently of shape. This known-answer degeneracy is an actor/plant interaction, not evidence against the learned circuit. It makes the original assay inadequate for the intended evaluator comparison.

## Single revised rule

Use the same initial action, bounds, greedy acceptance,10 feedback slots per round, local coordinate poll and step schedule. On rounds4,8,... replace the10 local proposals with10 **broad joint proposals**. Each has four motor coordinates uniform[-2,2] and gain uniform[0,2], drawn from a separate RNG seed71000+plantID. Precompute32 such batches for128 rounds, independent of target, evaluator, outcomes and incumbent. All arms receive the same broad programs; fixed-gain sets only their gain to1. Ties retain the incumbent unless a strictly lower candidate exists, then first argmin wins.

A failed broad poll leaves local step unchanged; an accepted broad proposal resets it to.4. Ordinary local failures halve to the same.00625 floor. Thus broad exploration can escape the known zero-gain plateau without target information or an extra query budget. It is favorable derivative-free search, not a claim of biological learning. No alternative schedule, covariance, optimizer or reward repair will be selected after seeing this test.

Run the revised **oracle only** on all three development plants at64 rounds. It must recover>=95% of initial true loss on **each** plant, with no exclusions. If any fail, stop this assay and give the supported stopping decision; do not tune another actor. If this passes, run all six revised development arms, preserve their results, freeze the held-out protocol and code, then evaluate IDs100..111 exactly once at64 rounds. Primary endpoints, half-oracle point criterion and target-specific control intervals remain as declared. The source-trained states may be reused exactly across the original/revised development actors; these are consumed development plants.

The previously declared128-round oracle/learned35 continuation and35-vs140 tutoring challenge remain. The improved exploration control makes them more informative, while neither coordinate-plus-random search nor128 rounds certifies a global optimum.

## Execution and endpoint clarifications before validation

Allow exact memoization of deterministic repeated frozen-circuit queries. Every feedback slot, including cache hits and repeated/clipped actions, still counts. It changes computation only; a nonstudy known-answer replay gives identical full cached/uncached query and trajectory arrays. Record real source calls/cache hits; source hashes and independently selected uncached evaluations check equality. Original code snapshot is `run_development.py`, memoized coordinate implementation is `run.py`, and revised actor is `run_mixed.py`. Scientific outcomes are stored separately in `mixed_results/`.

In addition to the primary normalized endpoint, report absolute terminal MSE, final gain and a **secondary** target-fidelity count (MSE<=.4, one tenth of the target feature energy4). This is frozen after the development suppression observation and before held-out outcomes; large reduction from a bad initial program can otherwise include mere attenuation. No change to the primary hypothesis or exclusion rules follows from this secondary count.
