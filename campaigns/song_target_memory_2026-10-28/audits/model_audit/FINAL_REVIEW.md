# Final adversarial review

2026-10-28. Reviewed the current `REPORT.md`, main figure, `outputs/hvc/SUMMARY.json`, `outputs/empirical_summary.json`, `outputs/recovery_summary.json`, source controls in the Zhao/Roberts audits, frozen HVC/recovery protocols, and the HVC runner/readout. Earlier independent kernel and empirical checks are preserved alongside this file. No expensive simulation was duplicated, and no root file was edited.

## Verdict

**The campaign supports the bounded identification branch of the requested goal, with the limited corrections below.** It does not deliver an untouched empirical model-selection victory, and the report says so. The contribution is more than an arbitrary toy equivalence or a missing download: it joins independently checked primary-intervention constraints, exact finite-summary bounds, a concrete published recurrent-network implementation and stress test, a stronger adult recovery control that limits a convenient intervention mapping, and an explicit conditional functional measurement with recovery and failure controls.

The unresolved cooling arm is clearly separated from quantitative results. The report does not claim unique storage anatomy, a new biological mechanism, universal nonidentifiability, or biological validation of the synthetic estimator. It does not use the synthetic60,000 datasets as60,000 empirical observations.

## Actionable findings reported to root

### 1. Distinguish an empty training-readout window from right censoring

**Priority: medium for artifact correctness; main scientific result unaffected.** In `hvc_model.py`, `training=[length(act[t+last_offset:t+100]) ...]` is empty for the matched400ms protocol because `last_offset=120`steps exceeds100. Its ten `training_readout_ms:null` values are therefore unavailable measurements, not observed sequences that persist to the end of a valid window. The source protocol and100/200ms variants have valid windows. All main report values use separate200-step frozen probes, which are valid, and the reported frozen-probe censor counts are unaffected.

Action: explicitly annotate the400ms training-readout field as unavailable due to the source window, or revise future readout-window handling. Preserve the completed frozen-probe results; a rerun of40 networks is unnecessary to correct this metadata issue. A generic null should not silently mean both censoring and an empty measurement window.

### 2. The third probe need not target the common trace specifically

**Priority: low, mathematical wording.** The rank section says a third selective intervention on the common trace is required. The calculation requires a third *linearly independent* observation or intervention mapping. A validated private-reference or private-motor trace probe could also remove the null direction. The common-trace probe is a sufficient example, not the uniquely necessary route.

Action: replace that sentence with wording such as: “An additional linearly independent measurement or validated selective intervention—such as a probe of the common trace—is needed in this model.” This does not change any rank or equivalence result.

### 3. Surface the irreversible-lesion order limitation in the report

**Priority: low-to-medium, causal scope.** The Roberts source audit states the lesion always followed initial learning/recovery, with no counterbalanced or sham repeated-learning task cohort described. Cell-body ablation was partial, and public lesion counts are not linked to individual behavioral rates. The report properly rejects selective evaluator erasure but omits this additional order/history alternative when describing what a purely local restoring model would predict.

Action: add a short sentence noting fixed pre/post order, task-history/elapsed-time alternatives, and partial projection-cell ablation. The reported paired behavioral change remains real as a source observation; attribution to a perfectly specified pathway intervention remains conditional.

### 4. Minor qualification for the parameter-sensitivity sentence

The report says seed1 rhythmic duration remains100ms over the prespecified learning-rate sensitivity settings, but the η=0 known-effect control gives10ms. The preceding sentence already explains this. For precision, say “over the nonzero-learning-rate and adaptation sensitivity settings.”

## Checks supporting the current claims

**Empirical units and source reconciliation:** the report distinguishes26table elements from25caption elements, pooled11long values from the7/4subgroups, and element summaries from independent birds. It retains the rejected323ms calibration and calls the new249.6→332.2comparison exploratory. It does not use extraction precision as biological uncertainty. The primary assignment bound now uses the source cap3 and matches my independent315×6enumeration. Its finite-summary support-separation claim is correctly conditional on the observed groups being contained in the supplied table. The original paper's bird-level test is acknowledged rather than accused of pseudoreplication.

**HVC implementation:** independent source-to-equation translation and separate scalar-loop checks were already successful. The stress suite holds the actual source parameters fixed, declares a changed PRNG, uses six independently initialized networks per main condition, and keeps repeated probes nested. It does not exploit per-period parameter changes in the source's other script. The changed-spacing comparison is fair as a fixed-model robustness test. It is not an isolated test of an onset-period causal parameter, because elapsed simulation time and spontaneous plasticity opportunities change too; the report explicitly says so. Neither schedule is equated with biological exposure timing. The failure therefore constrains this model's transfer, not motor-scaffold architectures generally.

**HVC measurement:** frozen neural activity is explicitly separated from acoustic duration, and the model's one-step impulse mapping is distinguished from actual light-pulse widths. Right-censored frozen probes are retained. The zero-of-six exact100ms result is supported by durations40,50,80,190,310andonecensored outcome; this is not an almost-identical set failing solely due to an overly precise numerical equality criterion.

**Adult recovery:** caption-defined means are not inverted into paired observations. Group-mean ratios are labelled as such. The report does not replace mean slopes by normalized recovery fractions or claim that0.503versus0.315identifies a recovered-memory fraction. The one-gain diagnostic has a clear calibration/prediction split at the level of observables, while openly remaining exploratory and unable to support a paired likelihood or inferential rejection. Temporal-learning impairment is preserved as a serious alternative to selective target retrieval loss.

**Mathematical scope:** equality is an explicit family under common acquisition/intervention maps, not a fitted likelihood result. The scalar potential construction is not mistaken for a measured neural reward. Shared-versus-private ambiguity is limited to the given observation model; the report explicitly avoids universal impossibility.

**Conditional measurement:** the synthetic estimator recovers the model-assigned feedback/evaluator contribution only with independently known gain and perturbation mapping. The off-target and incomplete-inhibition controls demonstrate failure rather than concealing it. A motor-stored target read out into the same evaluator remains equivalent. In biological use, the statistic by itself would identify a pathway-dependent auditory-feedback contribution; calling that evaluation also requires the proposed tutor-specific score and causal/selectivity checks. The report's qualification is important and must remain in any compact final briefing.

**Presentation:** the main figure correctly labels finite observed summaries, network replicates, nested/censored measurements, extraction-only bars, and invented synthetic noise. No graphical confidence interval is silently presented as a bird-population interval. Source/model-based findings and untested cooling are visually and textually distinct.

## Completion boundary

Within this review's scope, no unaddressed primary numerical error changes the retained24.0ms rounding-robust support gap, the corrected missing-membership bounds, the HVC frozen-probe stress result, or the conditional identification result. The empty training-window artifact requires a metadata/readout correction, not a reversal of the report's conclusion. Reproduction manifests and final command statuses are being completed by root and are not assumed successful here. Marking the bounded campaign complete should follow those actual checks and the narrow report corrections; it should not be described as resolving the underlying biological storage mechanism.
