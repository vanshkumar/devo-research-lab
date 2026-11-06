# Adversarial review of the prospective source result

2026-10-28, America/New_York. The lead authorized review of saved primary outcomes, generated forecast draws and aggregate results after the source forecast manifest was sealed and source scoring completed. This review opened no raw new-source trial file and no protected external file/value. Original-byte reconstruction and independent simulator replay are separate checks owned by the other reviewers.

## Defensible conclusion

**The frozen RNN did not forecast this new-source cohort's average acquisition accurately enough to earn the prespecified transport release. It also performed materially worse than the frozen exposure/growth comparator.** On24previously unused animals, its six-bin cohort curve error is6.970pp versus2.278pp for growth. The growth advantage is4.692pp, paired animal-bootstrap95%interval[2.850,5.668]pp. This is a prospective source-mixture prediction result with a real baseline loss, beyond a purely low-power failure to certify accuracy. It does not test the protected different-policy cohort.

Keep the separate practical-bound statement: the data **do not establish that the underlying population bias exceeds5pp**. Observed-minus-RNN bias is−6.970pp, animal90%interval[−8.968,−4.972]pp and lab-cluster90%interval[−11.070,−2.870]pp. Both overlap the−5ppboundary. The animal upper endpoint is only0.0282ppinside that boundary, smaller than the simulator's0.0776ppconditional Monte Carlo SE. Rounding it to−5.0must never become a claim of demonstrated>5ppbias. Wider95%intervals also exclude zero but overlap−5pp. An observed error on this cohort and uncertainty about a population accuracy bound are distinct facts.

## Independent aggregate checks

From `SOURCE_ARRAYS.npz` and the three models' generated512-particle forecast files, an independent calculation reproduced:

- Equal-side/equal-bin mean error and both animal/lab-cluster intervals.
- The20,000replicate paired mean-curve-MAE comparisons using seed202610282.
- Unbiased Monte Carlo marginal CRPS, its paired differences and bootstrap intervals.

Maximum numerical discrepancy from the saved source result was1.39e−16. `RESULTS_CHECKS.json` records hashes, exact values and the calculation's scope. All144animal/bin primary endpoints and all subgroup scalar estimates are finite; the minimum actual side denominator is32. The static review's undefined-subgroup edge case therefore had no effect on this result.

## Baselines, concentration and surviving objections

Growth also improves individual marginal CRPS by.008648 over RNN, paired animal-bootstrap95%interval[.003171,.013889]. This supports a loss in the tested forecast recipe beyond the selected mean statistic, but remains an animal-resampling result conditional on the selected source mixture. It is not replicated evidence over arbitrary new laboratories.

Persistence has6.388ppmean-curve error. Its advantage over RNN is only.582pp, interval[−4.555,+5.280]pp; individual CRPS instead favors RNN at the point estimate, with an interval spanning zero. Do not claim that persistence is demonstrably better or that the RNN generates no learning.

All five laboratory scalar RNN errors are negative, with the largest miss in Hofer(10animals,−10.409pp). The pooled growth ranking survives deleting any one lab: its mean-curve advantage ranges2.766pp(dropHofer) to5.022pp(dropMrsicFlogel). This descriptive deletion check argues against the ranking being solely a Hofer effect. Ranking is not uniform within laboratories: RNN beats growth by1.488pp in Angelaki(n5), while growth wins the other four small groups. Lab groups of1and2cannot establish stable lab-mean accuracy.

The RNN overpredicts every population bin, from3.082ppin the first future bin to8.872ppin the last, with a9.897ppmaximum miss in bin5. Multiple frozen checks fail: both scalar intervals, mean/maxbin errors, one lab safeguard, leave-lab safeguards and baseline noninferiority. Known-answer controls pass. No single borderline confidence endpoint determines the no-release decision.

The source set is selected by historical file-format coverage and contains previously represented labs. Indexed starts do not certify biological first exposure; conditioning on realized opportunities does not forecast stopping. The result cannot identify whether the miss arose from environment reconstruction, prefix/observation nuisance assumptions, latent cohort differences or the inferred update law. Primary omission probabilities are shared across models; overall observed omissions are.90%versus.51%forecast, but these all-trial rates do not by themselves isolate the exact100%endpoint contribution. Avoid a unique mechanistic explanation.

**Session assumptions materially change the miss.** The lead's source-only postvalidation diagnostic multiplies both GLM coefficients and hidden state by.8at each future session boundary, while retaining the primary prefix calibration. That recipe reduces mean-curve error from6.970pp to2.124pp; maximum bin error becomes4.089pp. I independently reaggregated the saved sensitivity draws and confirmed those values. Holding omission probabilities at their prefix level leaves6.493pperror. The session result is the strongest surviving objection to attributing the primary miss to an intrinsically nontransferable inferred rule. It is a changed future transition prescription, tested after seeing validation outcomes, with an unchanged prefix recipe; it is neither coherent prefix-and-future calibration under that prescription nor a newly earned gate or identified biological retention mechanism.

The pre-outcome source-state counterfactual forecasts retain a large fixed-minus-adaptive gap on these24new prefixes:22.435pp in observed-style exact100%simulations and20.899pp in the identical probability probe. That confirms the original four-prefix extrapolation was not merely their selection or a mismatch of test contrasts. A subsequent matched128-particle sensitivity applies the same future-only.8weight/hidden retention to both policies. It predicts75.208%fixed versus56.788%adaptive, a difference of18.420pp(conditional Monte Carlo SE.140pp). Independent reaggregation of both saved NPZs agrees within2.78e−17; `RETENTION_FIXED_CHECK.json` records the hashes and source-order provenance. The contrast therefore survives this prescription, but its magnitude changes substantially. Neither version observes a real policy effect or earns a new release gate. Replacing prefix reward-volume metadata by100µLleaves generated paths exactly unchanged in the two checked cases; this verifies the implementation's omission of magnitude as an actor input, not biological irrelevance of reward amount.

## Decision

Keep the20protected external animals sealed. The large frozen fixed-minus-adaptive simulation prediction remains an audited extrapolation, not real predictive transport evidence or a falsified causal policy effect. Finish this campaign with the prospective source loss, its limits and completed independent checks. A replacement actor or a post-outcome relaxed gate would be a different study.

## Final report review

The draft main report accurately preserves the6.97versus2.28ppprospective result, the unresolved5ppunderlying-bias boundary, the session-prescription sensitivity, the prior individual failure and the absence of external transport evidence. No material scientific correction was needed. The lead was asked to distinguish the75total source forecasts into72full-primary plus3partial forecasts and to complete the linked validation/reproduction records before delivery. This is a completed source-gated campaign once those audit records are saved; the conditional external experiment is correctly left unexecuted after failure, rather than presented as unfinished authorized validation.
