# Prevalidation adversarial design review

2026-10-28. Reviewer: trainer subagent, after handing off the simulator. This
review is independent of the lead's scoring/baseline implementation and the
model worker's inference implementation; it is **not** an independent second
implementation of the reviewer's own trainer. No empirical choice/reward
outcomes in development, source holdouts or external animals were read for this
review. Files inspected: DEVELOPMENT_PLAN, DATA/SPLIT/COVERAGE, data_io,
learning_models, fit_learning, baselines, rollout and evaluation, plus the
published-recurrence/trainer records. This is a design/code review, not empirical
confirmation.

## Overall judgment before validation

The planned comparison can distinguish conditional behavioral tracking from
autonomous acquisition prediction, conditional on realized task opportunities.
It cannot by itself identify a unique biological update law or isolate
curriculum as the cause of external failure. Preserve the source gate, record
the important scopes below, and fix the nonfinite-forecast score issue before
freezing. Source outcomes remain sealed as of this review.

## Actionable findings

1. **Scored coordinates must be common across models.** In the first reviewed
   `evaluation.score`, validity combined observed finiteness with
   `np.isfinite(samples).all(axis=0)`. A model could silently discard a bin/metric
   when its forecast is NaN. Define coordinates from observed availability and
   a frozen common mask; require finite forecast samples at every scored
   coordinate, or use a predeclared failure penalty. Do not permit a model's
   numerical failure to change its target. High-side simulated empty cells are
   unlikely at500trials but still require explicit handling. The lead was
   notified immediately before validation.

2. **Actual-schedule replay at zero has an unobserved hidden side.** The initial
   replay diagnostic derived side from a signed scalar: zero was thereby
   assigned right by default. At0% contrast, the source trainer still has an
   assigned rewarded side. A signed-zero contrast alone does not safely encode
   it. Retain the simulator's independently generated hidden side at zero,
   rather than reading future real feedback/choice to recover it. This is only
   a conditional-input diagnostic; it must never replace the autonomous primary.

3. **Full-horizon selection defines a conditional population.** Allocation is
  74development+27animalholdout+27wholelabholdout. Footers show48holdouts with
  1,000trials, and40with4,000trials (21animal+19lab). All54allocated animals,
   including six too short for prefix and eight lacking the primary future
   horizon, belong in the disposition table. Report partial observed-bin scores
   for short futures, without extrapolating missing biological outcomes. The
   primary is about animals observed for the full opportunity horizon; longer
   observation can depend on competence, attendance and operator decisions.
   Metadata-based eligibility does not make this censoring ignorable.

4. **Marginal calibration is not joint trajectory calibration.** Equal-weight
   marginal CRPS is proper for the four observable bin summaries. It does not
   test their joint serial dependence. The growth baseline replaces a censored
   development donor separately at each future bin, which can produce a
   noncoherent donor identity through time. This is an explicit marginal
   forecasting algorithm and can remain the primary baseline. The energy-score
   sensitivity is proper for that algorithm's induced path distribution, but
   cannot be offered as validation of a coherent biological acquisition path.
   Avoid joint-calibration claims, and show coverage by bin/metric in addition
   to pooled coverage. Full-horizon-donor sensitivity is optional; it changes
   the donor population and should not silently replace the stated baseline.

5. **Whole-lab transfer requires its own decision.** Nineteen full-horizon
   animals in Hofer/Witten are two held environments, not19independent
   replications of a new-laboratory population. Report each lab separately.
   Animal bootstrap intervals describe this animal mixture, not uncertainty
   over arbitrary new laboratories. A source gate driven only by the21
   held animals from development labs would not demonstrate source-lab
   transport. Require material benefit/useful calibration in the held-lab
   subset before opening the external cohort.

6. **Distinguish skill persistence from all-behavior persistence.** Current
   persistence fixes the prefix sensory/bias GLM but shares the same empirical
   omission-growth forecast used for DNN/RL/growth. This is a sensible matched
   engagement component, but name it 'skill persistence + matched engagement'.
   It is not a constant forecast of every observable. Show side-specific
   high-contrast MAE as well as four-metric CRPS, so an improvement in omissions
   or aggregate response share alone is not described as acquisition success.

7. **Prediction uncertainty is approximate and predictive.** Prefix endpoint
   particles propagate a local Fisher approximation through the causal
   recurrence. It covers three initialization coefficients, not population
   update-law uncertainty. Residual widening must be development-only and
   method-specific under a common selection/leave-self-out policy. It can make
   forecasts empirically calibrated but does not become a posterior over the
   learning law. Report raw and widened forecasts; broad intervals alone do not
   earn the gate. Verify finite-simulation convergence near the practical gate
   threshold rather than merely reporting particle count.

8. **Known-answer controls must exercise the scientific pipeline.** An oracle
   with known parameters is useful but insufficient. A known transferable
   learner should be fitted on synthetic source data, then forecast unfamiliar
   source and fixed-protocol learners after the same prefix-only calibration.
   Fixed competence, ordinary exposure growth and changing engagement controls
   must not systematically earn a false update-law advantage over matched
   baselines. Hidden initialization, corrections, boundaries and censoring
   challenges must be interpreted separately. A failed control localizes a
   measurement/model scope; it must not be buried by a later real-data result.

9. **Conditional-model reproduction has a bounded meaning.** The code
   numerically checks the original published recurrence, including its
   previous-covariate alignment. The scientific comparison uses a new cohort,
   three coefficient mode, bounded hidden size/training, explicit omission
   masking and early-prefix initialization. Call this recurrence/architecture
   reproduction and a conditional forecast test; do not claim exact replication
   of the paper's numerical results unless the original experiment is actually
   rerun. Omissions are scored but skip binary update; this is a reported
   observation-model adaptation, not proof animals do not learn from omissions.

## Checks that passed code/design inspection

- Frozen allocation uses metadata and a deterministic subject hash, protecting
  complete Hofer/Witten laboratories and the20external strict-prefix animals.
  Entirely separate release/cohort exclusions and prior feasibility exposure
  are recorded. No future success selection was used in allocation.
- `rollout.autonomous` primary future input is only a boolean session-start
  vector. Its trainer samples stimulus/side, receives its own generated choice,
  computes feedback, and updates its own adaptive state. No actual future
  contrast/reward schedule is supplied in this mode.
- Conditional `sequence` predicts at trial t before updating from t's actual
  choice/reward. Its curve samples hold real intervening histories fixed and
  are expressly labeled teacher-forced diagnostics, not joint forecast draws.
- Stimulus sign is right-minus-left; raw ALFchoice +1means left,-1right,0no-go.
  Summary accuracy uses `choice == -sign(stimulus)` at |contrast|>=.5. Omissions
  count as accuracy failures, remain a distinct observable fraction and never
  become right decisions.
- All actors receive the same frozen development bank and prefix allowance.
  Baseline growth borrows development changes rather than target future
  behavior. Baseline nearest-neighbor selection uses prefix competence only.
- The marginal CRPS sorting formula has the correct unbiased U-statistic
  denominator n(n-1). Energy score subtracts half the mean pairwise norm.
  Scores and uncertainty resample independent animals rather than simulated
  particles or individual trials as if they were biological replicates.
- Trainer core contrast/correction source methods are stable across audited
  versions, and a source-code recurrence check passes. Settings, body weights,
  wheel plant and hidden biological prehistory remain real uncertainties.

## Required scope in the eventual interpretation

The target is an observable curve indexed by task trials, conditional on the
realized opportunity/session schedule. It is not calendar-time acquisition or
unconditional stopping prediction. Marginal curve distributions, high-contrast
errors and coverage are predictive quantities. Conditional log-score gain may
be real while autonomous forecasts fail; that distinction does not invalidate
the source paper's conditional task. A source failure should be challenged
against development recovery, trainer envelope, initialization and session
assumptions before being interpreted. External failure would bundle lab,
genotype, implants, handling, year and policy, so cannot identify a causal
curriculum effect. Preserve external outcomes if the source gate is not earned.

## Follow-up record

Lead notified of findings1–7 before source validation. The lead accepted
censoring/disposition, marginal-target and matched-engagement wording; code
fixes and exact final gate will be checked against the frozen artifacts before
the independent original-byte reconstruction. This document records the
reviewed state, not an assertion that every proposed change has already landed.

Subsequent prevalidation check: the lead changed `evaluation.score` to derive
validity from observed targets and raise `FloatingPointError` on nonfinite
forecast draws. Independent `code/design_controls.py` passes: sorted CRPS
agrees with an explicit ordered-pair calculation to1.11e-15, a degenerate exact
forecast scores zero to floating precision, nonfinite forecasts are rejected,
a count witness returns exact [.8,.6,.3,.15] metrics, current trial
choice/reward changes cannot change that trial's probability, and omissions
skip the binary recurrence update. Results are in
`logs/design_controls.json`. These synthetic checks read no animal outcomes.
