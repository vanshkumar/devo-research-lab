# Adversarial pre-freeze review

2026-10-28. Scope: current report/protocol, implemented primary estimator/recovery, and secondary two-state model plus development output. Reserved and external outcomes were not accessed. This is an interim claims review; final reserved results require a later check.

## Judgment

The primary analysis and synthetic recovery support an honest statement that the robust sparse observable contrast has weak sensitivity at the chosen 0.2° margin. The successful known-generator oracle rules out describing that failure as a universal absence of information in the released trial sequences. The separately labeled two-state efficiency challenge is justified. Its narrow interval cannot presently establish broad equivalence of target-event propagation across plausible dynamical/readout mechanisms.

No numerical implementation error was found in the state filter or local finite-difference calculation. The remaining concern is which scientific alternatives the model and interval cover.

## A1 — High importance: the narrow secondary interval is structural

`state_models.py` uses one set of three nonlinear transition parameters for all 20 people and both primary sets. Each person has free current-cell gains in two states, direct current-cell endpoint effects, block drift and initial states. Only the fast state's propagation may change on zero-clamp target events; slow-state propagation is event-invariant. Readout is an additive sum of the states plus current-cell terms. The fast retention is bounded .10–.85 and slow retention .86–.995.

The model therefore pools all 720 randomized trials/person and all previous inputs into one event-dependent exponential response law. The primary contrast instead permits separate previous-cell effects and a free five-lag observable curve. These estimate a related scientific quantity under very different restrictions. The model's development θ=+0.024465°, local profile CI [−0.047101,+0.096032] does not override the primary's wide interval.

**Required interpretation:** Any narrow bound is conditional on this dynamical/readout family. Fast-only matched-generator recovery is insufficient. The source auditor is now executing slow-state modulation, transient/rebound and online-expression challenges, with actual-schedule effects calibrated to ±0.2°. If a physically meaningful alternative falsely yields a narrow null interval, general equivalence must be rejected even if the model fits its own generator well.

## A2 — High importance: interior-point flag does not establish regular uncertainty

The development fit has a_slow=.991724745 with cluster-profile SE=.00650077; its upper bound is .995. The estimate lies only .50 SE from the bound, although `near_parameter_boundary=False` because the code uses an absolute .002-distance rule. Its unconstrained parameter interval extends above 1.0. This is a warning about local normal approximations, not proof that θ itself is unstable.

The full profile interval correctly includes nonlinear fitting uncertainty: the conditional person-only SE is .00180449, whereas the full profile SE is .03406439. Never report the conditional interval [.020689,.028242] as the scientific interval. The profile formula is consistent with a participant-level estimating-equation influence expansion: direct person-curve variation minus the nonlinear-score correction. Between-person variability in fitted linear gains contributes to that direct term.

**Required check:** Stratified participant bootstrap and explicit boundary/curvature counts in recovery. CIs from boundary/nonpositive-Hessian fits must be identified, not silently counted as ordinary regular intervals. Conversely, a parameter-boundary flag alone need not invalidate θ if an independently calibrated procedure shows θ remains regular.

## Independent numerical checks

`state_numeric_audit.py` accesses development outcomes only and writes `state_numeric_audit.json`.

- The cumprod/cumsum filtered-input implementation agrees with an explicit chronological recurrence to floating precision.
- Full θ SE is .03406424–.03406444 over finite-difference steps .00025, .0005, .001 and .002. The narrow result is not caused by the selected .001 step.
- Fixing a_slow to .980/.985/.990/.995 and reprofiling the other two transitions gives θ=.020634/.022642/.024091/.025015. Thus the slow-boundary warning does not imply a large point-estimate instability in this particular development sample.
- All three development optimizer starts agree to roughly 1e−6 in parameters. Linear state designs have full rank24 and standardized condition numbers approximately15–25. No obvious local-optimum or rank failure explains the result.

## A3 — Moderate importance: slight in-sample improvement is not independent evidence

The alternative reduces development MSE from6.827295 to6.826534, a gain of0.00076063 degree² (about0.011% of restricted MSE). This is a nested, development-selected comparison. The fitted positive θ is uncertain even under the model. Reserved person-level prediction is necessary; its sign and uncertainty must be reported. A prediction gain alone would still not establish the signed observable effect or distinguish storage from expression/perceived-error correction.

## A4 — Strong primary-recovery distinction is preserved

The primary recovery correctly separates structural actual-schedule truth from noiseless estimator projection. Isolated −0.2/+0.2° perturbations become approximately−0.158/+0.257° once later events act; additional cases calibrate the actual-schedule scalar to ±0.2° without widening the margin. Full-history four-way interventions verify the analytic physical truth.

Primary false-positive rates of3.0–6.7% and coverage93.3–97.0% are broadly compatible with nominal calibration at300replicates, but sensitivity is only11–18% at the actual ±0.2° margin. No interval lies wholly inside±0.2°. Even correctly specified linear controls have low sensitivity. This justifies “insufficient precision for the primary equivalence claim,” not “no propagation change.”

The known-model oracle has high discrimination, including after a current-cell/drift nuisance projection. Therefore a failure of the efficient model on real data cannot be relabeled a universal information-theoretic impossibility. Its strongest defensible limits are conditional model/data discrimination limits and exact equivalences between specified mechanisms.

## A5 — Exact mechanism equivalence is a different result

Fixed intrinsic retention with a state-dependent perceived-error correction can reproduce event-dependent propagation exactly. Dynamic expression can do so as well. With suitably chosen intrinsic/effective retention factors, either modulation direction can arise from nonnegative corrective weights; this does not imply every amplifying synthetic parameterization admits a passive-retention interpretation. The exact endpoint equivalence is sufficient to prevent neural-storage attribution. It does not prevent detection of a behavioral propagation effect.

## Freeze and validation requirements remaining

- Complete secondary calibration/alternative challenges and bootstrap before claiming its interval is calibrated.
- Freeze the secondary model, coefficients, output definitions and interpretation alongside the primary/transfer records before release.
- Keep the primary and secondary results separate in final claims. The signed lag curve and stationary-readout contrast remain necessary.
- Score held-out predictions using development coefficients only. Re-estimation of the prespecified primary observable on reserved people is a separate test.
- Label the external test an extrapolation to nonzero index clamps; it cannot replicate absent zero-clamp conditions. Wide compatibility with a near-zero prediction is not successful transfer.
- Update this review after reserved/external results and the slow-modulation challenge exist. No final scientific verdict is issued here.

## A6 — Confirmed criterion bias under the stipulated colored noise

After the initial review, an independent exact expected-loss calculation established a concrete issue beyond optimizer convergence. With person-specific linear gains profiled out,

E[min_beta ||Y−X_lambda beta||²] = ||(I−P_lambda) mu||² + tr[(I−P_lambda) Sigma].

For independent noise with equal variance and equal model rank, the second term is constant. For colored noise it depends on the temporal orientation of the fitted state columns. Thus a wrong nonlinear retention parameter can lower expected profiled SSE by fitting noise more effectively, despite a correctly specified mean family.

`profile_noise_bias.py` uses only the twenty development input sequences, a known fast-state physical effect of+0.2°, no process noise or drift, and the stipulated AR-mixture endpoint covariance (SD2.5°). All compared full designs have equal total rank800. At parameters(.70,.995,.95), profiling the noiseless mean implies theta=.163675° and increases signal SSE by53.78. However, it reduces expected residual colored-noise SSE by173.60, so expected total profiled SSE is119.82 lower than at the true generating parameters. Under independent noise it is53.78 higher than truth. At(.75,.995,.95), implied theta=.139011° and expected colored-noise total improves132.50 despite signal error190.50.

This is a constructive counterexample to consistency of this unweighted person-profile criterion under the stipulated finite-trial colored-noise regime. It does not prove the entire empirical bias or select a unique repair. Equal parameter counts and participant-cluster sandwich errors do not remove this mean-criterion bias. Covariance-aware fitting or explicit validated simulation calibration would address the issue more directly than additional optimizer starts alone. The task lead and state-model author were informed before validation release.

Full calculation: `state_numeric_audit.json` and `profile_noise_bias.json`; no empirical reserved or external data were accessed.
