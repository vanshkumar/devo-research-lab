# Close the proposed general bridge as routine prior

Decision at **2026-11-01 14:55:53 UTC**, before the fixed 15:16 prior-screen deadline: **CLOSE this mathematical allocation.** The natural sufficient guarantee is an elementary combination of established sequential policy evaluation, logarithmic-score regret and probability inequalities. Its assumptions expose the same measurement bottleneck already recorded by the joint review. No distinct material claim, new method or independently validated measurement correction survived. Do not commission a review merely to review the reference exercise below.

## The candidate, stated precisely

Let a complete observed history before opportunity t be H_t. A known deployed teacher b_t(a|H_t) chooses stimulus/feedback/protocol action a; p_t(y|H_t,a) is the true response law and q_t the candidate law. Both worlds have the same initial law and teacher, with no hidden teacher information left out of H_t. These are observable conditional laws, not an assumed identified biological state. The teacher may depend on preceding responses.

The target policy pi has the same training teacher through T-1 and forces a specified common probe at T. Its **first response at T** is the target. The probe is terminal for this target; possible learning after that response is irrelevant to it. Input, delay, feedback timing and any context change that affects the current response belong in a. Inserting probes earlier, or scoring later responses after probes, changes the learning intervention and needs a different target policy/response law. Withholding reward alone does not establish that a probe is nonlearning.

Assume (i) the response kernels p and q are invariant under the stated teacher substitution; (ii) the target history/action occupancies are supported by the logging occupancies; (iii) their density ratios are bounded by C; and (iv) the population full-trajectory excess logarithmic loss is known. Assumption (iv) is deliberately stronger than the lab's observed relative score comparisons.

Write D_b = KL(P^b || Q^b), the **absolute population regret from truth**, not a model-to-model score difference. Define

    d_t(h,a) = KL(p_t(.|h,a) || q_t(.|h,a)) >= 0.

The usual chain rule, because the common teacher cancels within each comparison, gives

    D_b  = sum_t E_{P^b}[d_t(H_t,A_t)],
    D_pi = sum_t E_{P^pi}[d_t(H_t,A_t)] <= C D_b.

Every conditional divergence is nonnegative, so changing measure separately at each history/action proves the inequality. One must not multiply a possibly signed whole-trajectory log-likelihood ratio by C and call that a proof. Bounded trajectory importance weights suffice because their conditional expectations bound the prefix occupancy ratios. Jiang and Li's full-history tree representation and importance ratios provide precisely this sequential framework; no visible Markov competence state is needed. [Jiang and Li 2016, sections 3.2.2 and 5](https://proceedings.mlr.press/v48/jiang16.pdf).

For a binary terminal response Y,

    |E_{P^pi}Y - E_{Q^pi}Y| <= TV(P^pi,Q^pi)
                            <= sqrt(D_pi / 2)
                            <= min(1, sqrt(C D_b / 2)).

The second inequality is the standard KL/total-variation inequality; it can also be checked here by projecting onto an event, applying log-sum, and noting that binary KL as a function of its first argument has second derivative 1/[p(1-p)] >= 4 and its minimum zero at p=q. This is a reference derivation, not a new theorem. The KL interpretation of logarithmic-score regret is established proper-score theory. [Gneiting and Raftery 2007, section 4.1, equation 19](https://sites.stat.washington.edu/people/raftery/Research/PDF/Gneiting2007jasa.pdf).

If only the terminal action changes and the same probe has logging probability at least beta at every reachable preprobe history, C=1/beta is sufficient. Earlier occupancies have ratio 1. More explicitly, D_pi is the common training divergence plus the divergence for the forced final probe; the logging law mixes that probe divergence with other nonnegative final-action divergences. For beta=.1, a population D_b <= .0005 natural-log units is sufficient for a .05 response-probability error bound. This is a sufficient condition, **not necessary precision, power, an estimate of the lab's KL, or a sample-size prescription**.

An observable terminal probe mean could also be estimated with the standard importance weight product of pi_t(A_t|H_t)/b_t(A_t|H_t). When only the final action changes, the product reduces to 1{A_T=probe}/b_T(probe|H_T). Its support, variance, independent-trajectory and law-invariance requirements remain. This is standard policy evaluation, not a new correction.

## What was actually checked

`reference_check.py` builds one finite history-dependent learner with two feedback-bearing training responses and a third final response. The teacher's chance of action 1 is 1/5 initially, then 3/5 after success or 1/10 after failure. All 64 logging paths have positive probability. Both worlds update a constructed rational skill state from preceding actions/responses; no empirical data or fitted parameter is involved. The scheduled terminal policy has 32 positive paths.

At 14:54:03 UTC, native exit 0, exact rational enumeration verifies both worlds' importance-weight change of measure, weight mean exactly 1 and exact weighted/unweighted probe-mean agreement. Floating natural logarithms verify both chain-rule identities within 1e-14, the C=10 divergence bound and the zero-error control. True/candidate probe means are .3254137725/.2996053784, a .0258083940 difference. Logging/target trajectory KL are .002003103523/.002745477465; the overlap guarantee is .1000775580. Thus the guarantee is valid and conservative in this check. This is a deliberately small known-limiting-case/reference calculation; it is not a consequential synthetic discovery.

## Why this closes rather than becomes the main result

The banked mouse result is a relative proper score on cell marginals of generated counts/successes, with finite animal/lab uncertainty. It is not a bound on D_b, a full-history response model validation, verified deployed teacher probabilities, or measured common-probe response invariance. Its 3.617% relative point gain therefore cannot be inserted into the formula. An accurate joint observable forecast remains legitimate for that observable target.

The closed empirical source gate did not supply the missing protocol/assignment linkage. Calling these stronger conditions assumptions, then illustrating the standard bound, would not purchase that information. Nor would an off-support or lossy-summary counterexample add to the banked conclusion. The present screen found no nonroutine quantitative contribution or tested measurement improvement beyond those conditions; it did not prove that no such contribution exists anywhere.

The actionable specification, should a separately justified study become available, is to certify the exact probe protocol/timing and teacher propensities, preserve complete histories, and score frozen probe-response forecasts at a fixed opportunity. For comparing learning under different teachers, credible teacher assignment or a justified sequential intervention model is also required. A terminal common probe standardizes a behavioral measurement; it does not by itself identify latent competence or a biological learning rule. These are **requirements to satisfy**, not a recommendation to reopen the closed source search.

No new main claim was frozen, no pre-main amendment or sequence of toy examples was attempted, no independent review is earned, and the canonical PI's native scientific goal remains unfinished. Reallocate rather than extend this routine theorem branch. All prior failures, resources and protected exposure remain authoritative.
