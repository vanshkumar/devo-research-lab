# Independent, outcome-blind recovery challenges

2026-10-28. This module was written without reading any empirical hand-angle column. `check_generators.py` reads only person, trial number, programmed clamp and target jump from the original primary CSVs; all outcome fields are discarded at ingestion. No independent-laboratory outcomes are accessed. The lead owns empirical noise calibration and recovery estimation. These parameters are illustrative, not estimates of participants.

## Interface and timing

`experiments/generators.py` exports

```python
generate(c, j, seed=0, kind='two_timescale', noise_sd=2.5, effect=0.0,
         omission_rate=0.0, retentions=(.65,.97), gains=(.65,.20),
         gain_jump=.40, target_gain=.025, direct_jump=.035,
         direct_clamp=-.025, motor_phi=.70, observation_phi=.25,
         drift_scale=.60, process_sd=0., person_scale=1.,
         empirical_mask=None, zero_clamp_only=True)
```

The returned dictionary contains chronological arrays `y`, `clean`, `state` (two columns), `latent`, `expression`, `noise`, `drift`, `observed_mask`, plus `truth` and `final_state`. `y` is compensation-positive: a preceding +4° clamp causes positive subsequent reach adaptation. The response on trial r is read before the update from c[r], so the first reach reflecting index-event updating is r+1. Within-movement correction can nevertheless depend on the current c/r and j/r. A missing outcome becomes NaN without deleting its scheduled update.

`effect` is the mean of the isolated impulse response over horizons 1–5, in degrees, for the retention/perceived-error cases and reference person. It is NOT a shift in a fitted retention coefficient. The previous trial has +4° clamp and no target jump; the index trial has zero clamp with jump versus no jump; all later inputs are zero/stationary. With fast retention a and single-clamp fast increment b,

δ = effect / [b · mean(a^(h−1), h=1..5)].

The index event adds δ times fast state to the next fast state. Thus the isolated response curve is δb(1,a,a²,a³,a⁴). `person_scale` multiplies learning inputs and this observable effect together; it does not re-fix each person's effect to the reference value.

A positive event transition may exceed one briefly; the realized schedule's mean log multiplier must remain negative. The module rejects negative multipliers and noncontracting schedules of ≥100 trials. This permits transient amplification while preventing an explosive indefinitely repeated supplied schedule. No claim that a conditional multiplier must be a biological probability is made. With defaults, effect ±0.2° gives δ≈±0.60914; both signs are stable on all 40 original schedules.

## Serious alternatives

All kinds share flexible current-input learning, direct endpoint corrections and noise. The fast/slow current increments depend jointly on clamp, target-event presence and signed clamp/jump alignment; an additional signed target-input term exists even at zero clamp. These are deliberately more flexible than constant current-error gain.

| Kind | Storage dynamics | What should the isolated 1–5 curve show? |
|---|---|---|
| `gain_only` | One fixed retention; current cell changes gain | Zero index-event modulation of older input |
| `two_timescale` | Two fixed retentions; flexible current cell gains | Zero modulation |
| `retention` | Zero-clamp event changes fast-state propagation | Signed decaying curve with mean `effect` |
| `perceived_error` | Fixed retention; event alters a new internally perceived state-dependent error | Exactly the same endpoints as `retention` |
| `expression_current` | Fixed storage; event scales current readout only | Effect at index t, zero at t+1..t+5 |
| `expression_next` | Fixed storage; event changes only next endpoint expression | Same t+1 effect as `retention`, zero thereafter |
| `rebound` | Fixed storage; next endpoint effect followed by equal opposite effect | Same t+1 effect; opposite t+2; mean zero |
| `online` | Fixed storage; current clamp/jump and state-dependent within-movement corrections | Zero future modulation in the isolated stationary readout sequence |
| `expression_storage_equivalent` | Fixed storage plus a separate dynamic expression variable | Exactly the same endpoints as `retention` |

The expression alternatives use `effect` to calibrate a matched retention comparator, not to force their own five-lag average to that value. For +0.2° comparator, retention/perceived-error curve is [0.395941, 0.257361, 0.167285, 0.108735, 0.070678]°. `expression_next` is [0.395941,0,0,0,0]°, mean 0.079188°. `rebound` is [0.395941,−0.395941,0,0,0]°, mean zero. Negative examples are sign-reversed. This directly tests a consequential difference after similar immediate effects rather than comparing trivially different first readouts.

`expression_current` and `online` must not be called negative controls for all endpoint interactions: they can alter the older-input/readout relation on future trials whose own target jumps occur. The actual-schedule estimator must adjust current/readout inputs, and the no-jump readout analysis is particularly important. State-dependent current expression also creates old-input×readout-event effects, which a purely additive current-cell nuisance may not fully absorb in finite samples.

## Noise, drift and omissions

The nominal `noise_sd` is the stationary SD of the sum of independent motor AR(1) and observation AR(1) components. Their variance weights are .35 and .65 with default autocorrelations .70 and .25. Slowly varying drift is a sine with period 260 trials plus random linear trend, scaled independently. `process_sd` optionally adds innovation to the fast storage update. A common seed consumes identical streams for all kinds, so coupled comparisons isolate model differences. Baseline/motor variance calibration must be frozen on development data by the lead; no empirical scale was assumed here. Missingness can combine independent random omissions and an externally provided Boolean mask. This does not cover outcome-dependent missingness by itself.

## Exact observational equivalence, not failed statistical power

The retention account's fast state is

X[r+1] = (a + δ E[r]) X[r] + U[r] + η[r],

with E the eligible target event. A fixed-retention account can instead have a fresh perceived-error correction

X[r+1] = a X[r] + U[r] + b e[r] + η[r],
e[r] = −k E[r] X[r],  k = −δ/b.

The two updates are algebraically identical. The slow state, endpoint correction, noise and omissions can be identical too. Both modulation signs are possible mathematically: one corresponds to increased corrective feedback from the existing state, the other to decreased/positive feedback. Behavioral endpoints under these interventions cannot distinguish this unconstrained perceived-error account from a changed propagation coefficient, even with infinite observations. This is a precise limitation on *mechanistic attribution*, not on detecting an observable event-dependent response.

An equally exact storage/expression construction is available. Let stored S follow fixed retention S[r+1]=aS[r]+U[r]+η[r]. Let a separate expression state satisfy

Z[r+1] = (a+δE[r])Z[r] + δE[r]S[r],  Z[0]=0,

and observe X=S+Z. Then X follows the retention recurrence exactly. Such an unrestricted dynamic expression account cannot be rejected with endpoint sequences alone. In contrast, the narrowly defined one-trial expression/rebound alternatives make distinguishable predictions and should be tested rather than dismissed by the general equivalence.

`check_generators.py` verifies equality on all 40 primary schedules for both signs with process noise and 3% omissions. Maximum differences are 3.56e−15° for perceived error and 6.22e−15° for dynamic expression. It also independently evaluates the four-way isolated impulse contrast (old +4/0 crossed with index jump/no jump) and checks the promised 0.2° scalar.

## Essential estimand warning

The isolated impulse truth is not necessarily the finite-schedule linear-projection estimand. Actual schedules have subsequent events that can further modulate a propagated effect, preceding event-dependent gains, nonorthogonal assigned cells, and potentially correlated histories. Therefore a recovery study should report both:

1. Structural isolated impulse truth above, relevant to a specific intervention sequence.
2. The noiseless finite-schedule estimate using the exact proposed estimator, masking and nuisance design, which diagnoses projection/truncation bias.

For repeated-event dynamics, a difference between these truths can be an estimand mismatch rather than biased code. A structural claim requires the corresponding counterfactual/schedule standardization; an observable projection claim must be named as such. Do not calibrate recoverability only to an injected regressor, and do not widen the 0.2° margin to make recovery succeed.

## Oracle discrimination recipe

Use this after estimator recovery has been run; it separates failure of a chosen estimator from lack of information under a specified generator.

1. Generate deterministic means μA and μB on each actual sequence using `noise_sd=0, drift_scale=0, process_sd=0`, holding current-input nuisance parameters identical. First compare retention ±0.2° to the matched-immediate `expression_next` and `rebound` accounts; compare fixed two-timescale to retention; retain retention/perceived-error as the exact-zero-distance control.
2. For the default additive noise with known drift removed, covariance for positions r,s is Σ[r,s]=σ²[.35·φm^|r−s| + .65·φo^|r−s|]. Restrict to available observations without joining time gaps. If process noise is included, derive its transition-dependent covariance or set it to zero transparently for the oracle scenario.
3. Compute D²=(μA−μB)'Σ⁻¹(μA−μB) via a stable linear solver. Across independent people add D². Known-parameter equal-prior optimal classification accuracy is Φ(D/2). Zero D correctly gives .5. A likelihood-ratio simulation using the same covariance can verify this numerical calculation.
4. This oracle knows subject parameters and exact readout/noise law. High accuracy is an upper bound on a practical method's performance and indicates information exists in that stipulated model pair. Low accuracy is only an information limit for that generator/noise/observation scheme, not for all estimators or all plausible human learning models.
5. Unknown participant baselines, slow drift and shared nuisance gains lower discrimination. If claiming a useful bound, also residualize the mean difference against the declared nuisance tangent space or fit nuisance in the likelihood comparison; call this a composite challenge, not the oracle.

The actual-schedule regression recovery should include confidence-interval coverage, false positives for both fixed-retention baselines and direct-expression controls, correct-sign detection for ±effects, bias, and the fraction of intervals wholly inside ±0.2°. Use people as independent replication units. Crossed participant-level heterogeneity should vary gains, noise and event responses, not merely add row noise.

## Reproduce module checks

From repository root:

```sh
.venv/bin/python campaigns/target_event_carryover_2026-10-28/experiments/generators.py
.venv/bin/python campaigns/target_event_carryover_2026-10-28/audits/recovery_design/check_generators.py
```

Output: `audits/recovery_design/generator_check.json`. These checks establish generator timing and algebra; they are not empirical results or estimator recovery.
