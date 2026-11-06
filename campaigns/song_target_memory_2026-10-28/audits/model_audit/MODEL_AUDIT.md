# Independent identification audit

2026-10-28. This audit makes an analytical and computational contribution; it is not an empirical source reanalysis. The source reconstruction and the root's empirical calibration are separate. `PRE_SPEC.md` records choices before the synthetic results. `run_audit.py` uses no target-study numerical outcomes.

## Finding

The verbal categories “stored evaluative reference,” “altered motor dynamics,” and “shared representation” are not mutually exclusive at the level measured by the identified duration interventions. There are explicit, nontrivial implementations of all three with the same entire scalar practice trajectory, not only the same adult endpoint. Additional passive target decoding and motor timing measurements still cannot establish whether two functional readouts arise from one trace or synchronized copies. Selective causal access to the trace, or a narrower biological model with independently validated exclusions, is required for that question.

This does **not** imply that every reference or motor mechanism fits the data, that manipulations are biologically nonspecific, or that the interventions are uninformative. They constrain what can be written, when the input pathway is necessary, and which temporal coordinates are plausible. A hearing-independent autonomous motor learner can be rejected by an auditory-feedback dependence control without rejecting a motor scaffold that needs auditory calibration. A wall-clock sensory reference can fail a tutoring-clock manipulation without rejecting a sensory reference stored in clock ticks.

## Operational mechanisms and an exact equivalence family

Let d be experienced duration, c_T the clock speed during tutoring, c_P clock speed during later production, φ a monotone duration encoding, a the effective write gain, and η a practice gain. An acquired code follows

`z_next = (1−a) z + a φ(c_T d)`.

Natural and artificial tutors can enter the same update with different a. Acquisition-pathway removal can set a=0. Removal after acquisition can leave the downstream z intact while blocking subsequent writing. **These are explicit intervention mappings, not facts inferred from a deficit or a lesion name.** An alternative model locating z in the removed cells would erase z and give a different prediction. Anatomical targeting, timing, and surviving downstream activity decide whether that alternative is appropriate.

Three distinct implementations are possible:

| Implementation | Stored state | Practice computation | Acoustic readout |
|---|---|---|---|
| Reference | r in encoded auditory coordinates | Compute encoded mismatch r−w; update w by η(r−w)+innovation | φ⁻¹(w)/c_P |
| Motor | q, a motor equilibrium, written as q_next=φ⁻¹((1−a)φ(q)+aφ(c_Td)) | Autonomous relaxation of encoded motor state toward φ(q); no evaluative signal is read | physical motor state/c_P |
| Shared | z used by sensory and motor readouts | A common code drives practice toward z; sensory readout can decode z as well | φ⁻¹(w)/c_P |

For r=z=φ(q), these have identical acoustic paths. The reference update is gradient ascent on a quadratic score in w. In physical-duration coordinates this corresponds to a nonconstant metric/preconditioner for nonlinear φ; it is not an assertion that unpreconditioned acoustic error descent has the same path. The motor version has the same stable dynamics without calculating an evaluative score. Its timing scaffold need not determine spectral content or practice eligibility.

The independent code implements the reference iteratively, the motor model by repeated physical-state transformations, and the shared model by a closed-form recurrence. Across 1,000 random curricula, three encodings (linear/log/square-root), three lesion timings, tutor/production clock factors, and 60 practice steps, the greatest discrepancy was **1.91×10⁻¹⁴**. The encoding×lesion combination is crossed. This is numerical verification of an algebraic equivalence, not three separately fitted biological models.

If auditory input is necessary for plasticity, a common hearing-dependent gain η(H) can appear in any of these mechanisms. That extension is compatible with both tutor-error guidance and permissive auditory calibration. It should be supported by a serious biological implementation rather than inserted solely to evade a control. The root's independently inspected sequence-formation model is the appropriate place to assess such support. The present code does not claim to reproduce deafened birds.

## A broader scalar result and its boundary

For a smooth one-dimensional expected learning drift `dx/dn=f(x,z)`, define

`R(x,z)=∫ f(u,z) du`.

Then `∂R/∂x=f(x,z)`. A direct motor vector field and a learner explicitly using that reward gradient have the same expected path. A stable isolated fixed point is a local maximum of R. Equal innovations give equal path distributions. For the checked nonlinear family `f=−(x−z)−b(x−z)^3`, `R=−(x−z)^2/2−b(x−z)^4/4`; 4,812 independent finite-difference checks gave maximum error 2.31×10⁻⁹.

This result applies to a scalar effective state with the stated access to that state. It does not identify an actual neural reward signal. It does not prove equivalence of arbitrary multidimensional, history-dependent, partially observed mechanisms. In multiple dimensions nonzero curl can reject a simple Euclidean gradient field, though preconditioning, auxiliary state, and stochastic learning complicate that test. The current intervention observable is principally duration, so the scalar limitation is consequential rather than a claim about the whole song system.

## Cooling identifies coordinates more readily than architecture

A complete tutoring write gives z=φ(c_TD). Later production gives

`D_pupil/D_tutor = c_T/c_P`.

Cooling during tutoring with c_T<1 and ordinary later production c_P=1 therefore yields shorter imitations in all three internal-clock implementations. An external-time reference with an unaffected encoding predicts ratio 1. The effect would distinguish those coordinate assumptions, not motor storage from a reference expressed in clock ticks.

For quantitative use, c_T must be calibrated in the relevant tutoring state. The effect of cooling on adult singing duration is not automatically a measurement of the auditory acquisition clock. Attention, synaptic plasticity, developmental stage, and rewarming must be controlled. The audit uses dimensionless clock grids only; it does not fit the empirical cooling outcome.

## Why two readouts still do not reveal one versus two traces

Consider a local additive decomposition into private reference r, private motor trace m, and common trace s. The functional reference is S=r+s and functional motor prior is M=m+s. A practice endpoint combining the two with known weight w is

`Y = wS + (1−w)M = wr + (1−w)m + s`.

Exposure strengths, write-gate lesions, and clock factors can change a common input multiplier without changing this column direction. Such endpoints identify one composite. A directly calibrated evaluator-target probe observes S, and a motor-dynamics probe observes M, raising the rank to two. But the transformation

`(r,m,s) → (r−h,m−h,s+h)`

leaves Y, S, and M unchanged. The code's singular-value/rank calculation confirms ranks **1 → 2**, with null residual 5.55×10⁻¹⁷. In a nonnegative example, 61 allocations spanning common contribution s=0…0.6 have readout spread only 2.22×10⁻¹⁶. An independently selective readout or intervention on s gives rank three; treating an unvalidated intervention as that row assumes the answer.

The additive calculation is a local model, not a universal neural decomposition. A separate nonlinear construction makes the same point: duplicate a shared trace into two copies, give the copies identical acquisition rules and common input, and route one to each readout. Observations are unchanged until an intervention separately reaches a copy. Correlated errors across sensory and motor readouts are evidence about coupling, but common input and correlated noise remain alternatives to a single physical trace.

## A discriminating test of functional evaluation

The useful target is narrower and more causal: **does a tutor-specific evaluative reference contribute to subsequent practice updates?** This can be tested even when the memory's storage coordinates remain ambiguous.

Measure a small delayed change in timing after auditory feedback shifted by δ, crossed within each bird with a candidate evaluator pathway active or inhibited. Match immediate motor output, acoustic exposure, and exploration, and measure the after-effect after ordinary feedback has returned. A local model is

`Δx = κ[(1−α)(M−x) + αE(S−x−δ)] + nuisance + noise`,

where κ is an independently calibrated total plasticity gain, α the fraction attributable to the selected evaluator route, and E=1 for active, E=0 for complete selective inhibition. Symmetric auditory shifts ±δ give the per-bird estimator

`α_hat = [(Δ_active,− − Δ_active,+) − (Δ_inhibited,− − Δ_inhibited,+)]/(2δκ)`.

Bird intercepts and additive inhibitory suppression cancel. Trials remain nested within birds; population uncertainty is a t interval over independent birds. This estimator identifies a feedback-sensitive *functional contribution*. If inhibition efficacy is e, it instead estimates eα. If κ is unknown, the estimable quantity is καe; dividing by an assumed κ does not create identification.

Combine this interaction with tutor-specific evaluative tuning measured for identical heard stimuli and matched motor state. For quadratic score `V(a)=−λ(a−S)^2`, with independently calibrated curvature λ, symmetric probes ±p identify `S=[V(p)−V(−p)]/(4λp)`. A generic amplitude/familiarity response or an uncalibrated linear response bias can mimic a target shift; passive decoding alone is inadequate. Demonstrating that inhibition abolishes the tutor-specific component of learning gives stronger evidence than either a decoder or a feedback response alone. The present calculations do not establish an available neural probe with those properties.

### Executed recovery and sabotage controls

The prespecified grid contains **60,000 synthetic datasets** over 6/12/24 birds, 10/50 repeats per condition, two noise levels, and α=0/.25/.5/.75/1. Ninety-five-percent interval coverage was 93.2–96.6%. In the illustrative low-noise case (12 birds, 50 repeats/cell), α=.25 had RMSE .0613 and positive-interval detection 96.5%; the α=0 positive false-positive rate was 2.1%. Higher-noise/smaller designs recover poorly; the entire grid is in `functional_gain_recovery.csv`. These are invented dimensionless noise regimes, **not a sample-size recommendation for birds**.

An analytical sampling check gives RMSE `σ/(δκ√(n×repeats))`=.06124 and noncentral-t detection95.96% for that nominal α=.25 case. Across the full grid, the largest simulated-versus-analytical detection discrepancy is3.01percentage points with1,000 simulated datasets/cell. This check was added after the simulations as a validation, without selecting or changing the design grid.

Symmetric evaluative probes in a separate illustrative design (12 birds per target, 50 repeats/side) recovered a unit target difference with mean 1.0011 and RMSE .0421. This verifies the estimator under its score assumptions, not the biological availability of a scalar value signal.

Two deliberately unfavorable controls bound the inference:

1. Incomplete inhibition halves α_hat when efficacy is .5. An auditory-dependent off-target inhibitory effect of gain .05 produces apparent α=.5 at κ=.1 even when the intended evaluator contribution is zero. More birds cannot cure that exclusion failure.
2. A motor-stored target m read out online as S=m yields **exactly the same evaluative tuning and update law** as a sensory-stored reference r=S. Thus even a successful functional mediation test does not decide the memory's original storage coordinate. It would constrain a pure evaluator-free motor hypothesis and establish a real evaluative function, while leaving the motor-stored-reference/shared alternatives alive.

## Recommended claim boundary

Duration copying, conflict dominance, write-pathway timing lesions, and tutoring-clock changes should be interpreted as constraints on acquisition, consolidation, and temporal representation. They do not uniquely identify a comparator architecture. The concrete next measurement should establish **tutor-specific evaluative mediation at matched sensory and motor states**, with an independently justified perturbation map. A target decoder, another adult endpoint comparison, or more samples from the same intervention is insufficient to locate storage.

There is no novelty claim for scalar potential equivalence, shared-code ambiguity, feedback adaptation, or factorial mediation. The contribution is to apply their exact limitations to this campaign's intervention/readout structure and to show quantitatively which proposed discriminants work only after adding exclusions.

## Reproduction and audit history

From repository root:

```sh
.venv/bin/python campaigns/song_target_memory_2026-10-28/audits/model_audit/run_audit.py
```

Outputs: `audit_results.json`, `equivalence_cases.csv`, `functional_gain_recovery.csv`. Environment and script SHA256 are recorded in JSON. Saved stdout/stderr correspond to the executed final script; stderr is empty. The first implementation accidentally coupled encoding and lesion labels through the same modulo; this was corrected to cross the factors before reporting. The equivalence result and fixed recovery grid were unchanged. No public downloads, paid resources, private data, or external messages were used by this audit.
