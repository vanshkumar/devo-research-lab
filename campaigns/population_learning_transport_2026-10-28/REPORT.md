# A frozen learning rule misses a prospective population forecast

Completed 2026-10-28, America/New_York. This is the bounded prospective population campaign authorized after the completed individual-forecast study.

**The frozen RNN overpredicts new-source mean acquisition and loses to the frozen growth baseline. The source gate fails; all 20 protected external animals remain sealed.** Across 24 previously unused source animals, its six-bin mean-curve error is 6.97 percentage points versus 2.28 for growth. Growth's advantage is 4.69 pp, with a paired animal-bootstrap 95% interval [2.85,5.67]. This is an empirical prospective prediction result. The large different-policy prediction remains an audited simulation extrapolation, with no real external transport result.

The population tolerance itself remains partly unresolved: observed-minus-RNN bias is −6.97 pp, with animal 90% interval [−8.97,−4.97] and five-lab cluster sensitivity [−11.07,−2.87]. These intervals establish overprediction under their assumptions but **do not establish that underlying bias exceeds 5 pp**. Multiple other frozen criteria also fail. A future-session perturbation markedly improves mean fit, limiting any unique mechanistic interpretation.

![Prospective population result](/Users/vanshkumar/Documents/repos/devo-research-lab/campaigns/population_learning_transport_2026-10-28/figures/SOURCE_POPULATION_RESULT.png)

## The actual test and its exposure boundary

The old individual gate remains unearned. The RNN was originally a development-fitted, separately frozen **postvalidation architecture challenge**; this campaign did not refit its learning law or restore the old holdouts. The 74 development animals and 48 previously forecastable source animals' complete indexed histories remain consumed.

The genuinely unused candidates were the 26 animals excluded solely for mixed Parquet/legacy storage in the old frozen split. Metadata/header/footer reconstruction certified 24 for 1000 prefix+3000 future opportunities: Hofer 10, MrsicFlogel 6, Angelaki 5, Churchland 2 and Cortex 1. NYU-21 has four complete future 500-trial bins and is secondary. SWC_007 has 517 total opportunities, lacks a prefix, and its values were never opened. The set is selected by file format, not randomly sampled; these are previously represented laboratories, not 24 independent environments.

All 4407 opaque files/47.16 MB match cache size/MD5 and have pinned SHA256 values. All core/auxiliary array lengths and session keys agree. Reward volume is absent from 289 legacy sessions and remains NaN with an availability mask. It is never presented as a measured quantity. The frozen actor uses binary feedback, not water amount or wheel gain.

Before any new prefix, [FREEZE.json](protocols/FREEZE.json) pinned 44 files, the model/bank, coverage, protocol and gate. Its SHA256 is `625535ac5c20fe7301b7dcdec22549fd0a708271cc51dd79df8dee6f5c37a64c`. RNN model SHA256 is `c7f675d18f4143891ed7d2c76d91f74be74da9565fbae5407952768e2c146940`.

Each of 25 eligible prefixes supplied exactly 1000 task opportunities, including omissions. Only 3 initial GLM coefficients were nuisance-fitted by the existing MAP recipe; recurrent memory was prefix-derived, with the existing joint Fisher propagation. Growth retained its recent 500/15-development-neighbor bank; persistence retained all 1000 prefix observations and its frozen prior. No new actor, parameter trajectory, future learning-rate fit or external adjustment was selected.

Each model generated 512 autonomous particles: its own stimuli, choices, omissions, rewards, coefficient/memory updates, adaptive corrections and promotions. Its only realized future information was the session opportunity/boundary vector from metadata. This is a forecast conditional on indexed opportunities, not calendar time, attendance, biological first exposure or outcome-dependent stopping. All 75 source forecasts (72 primary, 3 partial) and 75 source-state fixed-policy diagnostic forecasts were hashed before **any** scored future was opened. [SOURCE_FORECASTS.json](protocols/SOURCE_FORECASTS.json), [the counterfactual manifest](protocols/SOURCE_POLICY_SWAP_FORECASTS.json) and [EXPOSURE.jsonl](protocols/EXPOSURE.jsonl) preserve the order.

The analysis returned only the first 4000 rows of 24 primary animals and first 3000 of NYU-21:99000 unique rows, including prefixes. Later rows and SWC_007 remain unexamined by this analysis. Parquet libraries may internally decompress a block; no later values were returned or summarized. All external prefixes/outcomes remain sealed. [VALIDATION_STATUS.json](protocols/VALIDATION_STATUS.json) is the authoritative completion record.

## Endpoint, fixed gate and controls

The primary endpoint is the equal-side correct share at **exactly ±100% contrast**, omissions as failures, in six 500-opportunity bins after the prefix. It weights animals equally within bins and bins equally. No .5 contrast enters. Every primary animal/bin has both side cells; the minimum side denominator is 32. Empty side cells would use a common model-independent mask, with minimum 80% bin coverage and 15 primary animals. An undefined lab safeguard cannot pass.

The fixed RNN gate required both animal-t and CR1 lab-cluster 90% scalar intervals wholly within ±5 pp, six-bin mean-curve MAE ≤5 pp, maximum bin error ≤7.5 pp, every lab's absolute scalar point bias ≤10 pp, every leave-one-lab-out bias ≤5 pp, and MAE no more than 1 pp worse than the better frozen baseline. Known-answer controls and independent checks were required. The cluster procedure uses five groups/t4 and is a control-checked safeguard, not universally exact inference over arbitrary laboratories. Small groups of 1 and 2 provide no stable laboratory calibration claim.

Exact ±100% precision on the consumed 40 source animals gave residual SD 10.55 pp, rather than 10.25 on the earlier ≥.5 endpoint. At N=24, an animal 90% halfwidth near 3.7 pp was expected. Final controls used actual lab counts and 20000 repeats per construction: empirical/Gaussian errors, greater heterogeneity, fixed/random lab offsets, completion selection, biased means, and cancelling curve errors. The worst acceptance of a known scalar error at or beyond ±5 pp was 4.10%, exact Monte Carlo 95% upper 4.384%. A ±25 pp wrong forecast and opposing ±12 pp bin errors never passed. A low-variance correct forecast passed every control repetition.

The gate is deliberately demanding: correctly centered empirical source-like forecasts pass only 16.34%, Gaussian ones 18.82%. Thus failure alone could be unresolved precision. A full frozen-RNN generative control with independent future streams also passed the expected-law check under both trainers; mean errors were−.025 pp adaptive and−.095 pp fixed. Its noisy 24-animal cohorts passed 26.92% and 94.80%, respectively. These are generator-specific control rates, not real external power. [Method audit](artifacts/method_audit/METHOD_AUDIT.md), [controls](artifacts/method_audit/CONTROLS.json), [known learner](artifacts/learner_controls/RESULT.json).

Pre-scoring static review found that Python's `max` could ignore a non-first NaN subgroup value. A recorded [finite-guard amendment](protocols/SCORING_GUARD_AMENDMENT.json) made the existing finite requirement explicit, leaving the frozen scorer and all complete-data statistics unchanged. All actual cells/subgroups are finite, so it has no effect on the result. A separate [access clarification](protocols/RELEASE_REQUIREMENTS.json) requires independent checks and an external protocol freeze in addition to a provisional performance flag. No external opener was invoked.

## Prospective source results

Bias below is observed minus forecast. Positive means underprediction. These are 24 full-horizon animals, not the partial animal.

| Forecast | Mean forecast | Observed mean | Mean-curve MAE | Maximum bin error | Individual marginal CRPS |
|---|---:|---:|---:|---:|---:|
| Frozen RNN |61.63%|54.66%|6.97 pp|9.90 pp|.05746|
| Frozen growth |56.94%|54.66%|2.28 pp|4.80 pp|.04881|
| Prefix persistence |48.28%|54.66%|6.39 pp|10.42 pp|.07025|

Observed population accuracy across future bins is[51.54,53.04,55.76,53.34,55.58,58.71]%. RNN predicts[54.63,58.15,60.74,63.22,65.48,67.59]%; growth[51.77,54.51,56.31,58.14,59.25,61.68]%. The RNN generates learning but overpredicts every population bin. Its conditional simulation SE for the scalar mean is only .078 pp, separate from animal/lab uncertainty.

RNN observed-minus-forecast bias is −6.970 pp. Animal 95% interval is[−9.382,−4.558]; cluster 95% is[−12.310,−1.630]. The 90% animal upper endpoint is −4.9718 pp, only .0282 pp inside the−5 boundary—less than conditional Monte Carlo SE. Rounding must not turn this into a demonstrated>5 pp bias. The no-release decision also fails curve, maximum-bin, lab, leave-lab and baseline criteria; no borderline endpoint determines it.

Growth's mean-curve MAE advantage is 4.692 pp[2.850,5.668], using the fixed 20000 paired animal resamples/seed 202610282. Its individual marginal CRPS advantage is .008648[.003171,.013889]. These are conditional selected-mixture animal intervals. Persistence's .582 pp mean-curve advantage is unresolved, and individual CRPS instead favors RNN at the point estimate. Do not claim persistence is demonstrably better. The aggregate proper score supplies an additional diagnostic, not a joint trajectory-calibration claim from one cohort.

| Laboratory | N | RNN scalar bias | Growth scalar bias |
|---|---:|---:|---:|
| Angelaki |5|−3.51 pp|+5.00 pp|
| Churchland |2|−6.32 pp|−1.27 pp|
| Cortex |1|−6.02 pp|−2.81 pp|
| Hofer |10|−10.41 pp|−6.96 pp|
| MrsicFlogel |6|−4.50 pp|−.79 pp|

All RNN lab biases have the same sign. Removing any one lab leaves a descriptive growth advantage of 2.77–5.02 pp; the pooled ranking is not solely a Hofer effect. RNN does better in Angelaki and growth in the other four small groups, so uniform lab superiority is not established. The partial NYU-21 sensitivity favors RNN at the point estimate (10.70 pp curve error versus 18.24 growth), but cannot replace the frozen full-horizon population. Side-specific curves, response shares, omissions, all draws/counts and scores are in [SOURCE_RESULT.json](artifacts/results/SOURCE_RESULT.json) and the forecast NPZs.

## What happened to the large policy prediction?

Independent GRU recurrence, sampling, signs and causal update reconstruction reproduce the original four-prefix+25.34 pp policy contrast within 5.55×10⁻¹⁶. The preflight used 64 particles per prefix, not 512. Eight hash-selected consumed prefixes yield+23.87 pp, with substantial prefix variation. Original task AST tests confirm correction-side signs, saved-probability carryover, pool updates and resets.

**Correction dynamics explain much of the simulated magnitude.** Removing adaptive correction shrinks the original-four contrast from 25.34 to 6.15 pp. A balanced fixed 100/50% trainer still gives 19.26 pp over adaptive. Thus this is a closed-loop trainer prediction, not simply an easy-versus-hard contrast claim. Omissions, initial state, future update scale, session retention/reset and a fifth 50% contrast were checked without selecting a new primary. [Policy audit](artifacts/policy_audit/POLICY_AUDIT.md).

On the 24 new source prefix states, **saved before outcomes**, the unchanged model predicts 84.07% under the fixed mixed policy versus 61.63% adaptive: +22.43 pp, conditional Monte Carlo SE .086 pp. Its identical probability-probe contrast is+20.90 pp; the probe adds no training. Growth is approximately policy invariant. This shows the large extrapolation survives new source prefix calibration, but is still a counterfactual simulation, never an observed external policy effect.

Postvalidation challenges further limit interpretation. Prefix-static omissions leave 6.49 pp source mean-curve error. Multiplying weights and memory by .8 at each **future** session boundary reduces it to 2.12 pp(maximum 4.09). The matched fixed-policy perturbation still predicts+18.42 pp over adaptive, with fixed mean 75.21% rather than 84.07%. These are future-only diagnostics with unchanged primary prefix calibration, not coherent alternate prefix/future fits, parameter posteriors, biological retention estimates or earned gates. They show that session assumptions substantially affect both the source miss and extrapolation magnitude. They do not rescue the original prospective recipe. No replacement law or gate was selected. [Diagnostics](artifacts/diagnostics/RESULT.json), [matched retention contrast](artifacts/diagnostics/RETENTION_FIXED_RESULT.json).

Replacing prefix reward metadata by 100µLleaves generated choices/weights exactly unchanged in the two checked cases. This confirms magnitude is inactive in the implementation, not biologically irrelevant. The protected cohort's exact custom acquisition code remains unresolved; primary paper plus previous input-only metadata support the four-contrast policy. A fifth-contrast sensitivity retains a large prediction. None of this certifies all real external sessions.

## Independent verification, prior work and decision

Independent direct-byte reconstruction reproduces all 25 source targets/counts exactly and 195 numeric score/interval/gate/bootstrap comparisons within 7.79×10⁻¹⁵. Native semantics on 99000 rows show zero choice/correctness disagreements with feedback on 97677 nonzero responding trials; all 1036 omissions are unrewarded. All clocks/session boundaries and prefix values agree across formats. No sign inversion, duplicate session or clock-reset error explains the result. [Reconstruction](artifacts/coverage/reconstruction/REPORT.md), [semantic audit](artifacts/coverage/SEMANTIC_AUDIT.md).

Independent simulation replays six new source prefixes×three models×two policies: all 36 sample curves, denominators and curriculum summaries match exactly; coefficient/memory differences are below 3.4×10⁻¹². [Replay](artifacts/policy_audit/production_replay/PRODUCTION_REPLAY.md). A separate adversarial calculation reproduces primary comparisons and confirms the lab-deletion result and session sensitivity. [Adversarial review](artifacts/adversarial_review/RESULTS_REVIEW.md). [Provenance checks](protocols/PROVENANCE_CHECKS.json) verify frozen files, original bytes, forecasts and exposure order.

Closest primary work was checked: [Liu/Geadah/Pillow](https://arxiv.org/html/2509.04661v2) already predicts held-out animals/future choices with actual histories; [Geadah/Pillow](https://pmc.ncbi.nlm.nih.gov/articles/PMC12621722/) already fits acquisition under both curricula separately. The proposed extra contribution was frozen prospective cross-policy population forecasting. It was not completed because the new source forecast failed its release gate. No first-ever, unique synaptic rule, causal curriculum, individual precision or arbitrary-environment claim is supported. [Bounded prior-work audit](artifacts/method_audit/PRIOR_WORK.md).

**Finish at the source gate and preserve external validation.** What changed is a genuine prospective loss for a mean-forecast recipe whose old mean performance was encouraging, plus an audited explanation of the large simulation prediction and its session sensitivity. Accurate conditional observation, old-source mean fit, autonomous acquisition, individual utility and external transport remain distinct. The strongest surviving objection concerns generative session/initial-state assumptions, not a demonstrated impossibility of transferable learning rules. No new campaign or architecture tournament is launched.

## Reproduction

From repository root, the read-only integrity/access check is:

```sh
campaigns/learning_rule_transport_2026-10-28/.modelenv/bin/python campaigns/population_learning_transport_2026-10-28/code/verify.py
```

Independent original-byte score reconstruction and source-only simulation replay:

```sh
campaigns/learning_rule_transport_2026-10-28/.modelenv/bin/python campaigns/population_learning_transport_2026-10-28/artifacts/coverage/reconstruction/reconstruct_scores_limited.py --released
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 campaigns/learning_rule_transport_2026-10-28/.modelenv/bin/python campaigns/population_learning_transport_2026-10-28/code/production_replay.py --cohort source --limit 6
```

These use no network, external outcomes or new fitting. They refresh audit outputs/logs, never historical campaign or primary forecast files. [REPRODUCE.md](REPRODUCE.md) records all commands, versions, known failures, guard amendments and secondary runs.
