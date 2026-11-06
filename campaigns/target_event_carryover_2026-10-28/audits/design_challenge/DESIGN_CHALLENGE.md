# Outcome-blind design challenge

2026-10-28. Author: bounded independent design-challenge agent. Ownership is this audit directory only. No hand-angle outcome was stored, calculated, or displayed. This is a methodological audit and input-only computation, not the study's final protocol. The lead owns the final freeze and all empirical analysis.

## Recommendation that changes the primary estimand

Use the contrast for a preceding **stationary-target** trial. At index trial `t`, require programmed clamp `c[t]=0`; compare a target jump against no jump. Let the immediately preceding target be stationary, `j[t-1]=0`. For each future horizon `h=1,...,5`, define

`delta[h] = 1/2 { [E(y[t+h] | J[t]=1, c[t-1]=+4) - E(y[t+h] | J[t]=0, c[t-1]=+4)] - [E(y[t+h] | J[t]=1, c[t-1]=-4) - E(y[t+h] | J[t]=0, c[t-1]=-4)] }`,

with the eligibility conditions above and a frozen common distribution/adjustment of other inputs. `J[t]=1` averages both signed index jumps. This is a signed half-difference: the change in the contribution of one +4-degree previous clamp relative to the signed midpoint, in degrees of hand angle. It is **not** the full +4-versus−4 contrast, which is twice as large. It need not equal a +4-versus-zero contrast under a nonlinear input-response law.

The scalar is `theta = mean(delta[1:5])`. Display all five signed estimates and their covariance-aware uncertainty. A positive or negative answer is allowed. The mean can cancel a rebound, so the curve must accompany it; a small mean alone does not mean that all lag effects are small. Keep a secondary shape contrast such as `mean(delta[3:5])-delta[1]` explicitly secondary if desired.

Why refine the original all-previous-clamp projection before outcomes? The actual input cells in set A are:

| Previous clamp | Possible previous target jumps |
|---|---|
| −4 | −8, −4, 0 |
| 0 | −4, 0, +4 |
| +4 | 0, +4, +8 |

Set B has the Cartesian grid of clamp `−4,0,+4` and jump `−8,0,+8`. Consequently a marginal signed previous-clamp contrast in A also changes previous target motion. Saturating *main* previous-cell effects does not fix an omitted previous-target-motion × index-event interaction. A full previous-cell × index-event interaction with a fixed half-contrast between `(c=+4,j=0)` and `(c=−4,j=0)` answers the intended cursor-error question. Retaining all previous cells in the fit helps nuisance estimation; the contrast still draws its essential identifying information from those two cells. This qualification must not be hidden by claiming that all observations supply equal information.

The original normalized-clamp × index-jump projection remains a useful secondary measure of compound programmed-input propagation. Set B's marginal contrast is additionally useful because its previous clamp and jump geometry vary independently. Do not elevate a selected secondary result over the fixed primary after seeing outcomes.

### Practical margin and relative size

A prespecified ±0.2-degree margin for `theta` is a transparent operational threshold: it is 5% of the 4-degree programmed precursor and can be consequential relative to a subdegree adapted response. It is not a field-established negligible-effect threshold and should not be described as one. Do not enlarge it when recovery is poor. Also report the ratio to the ordinary previous-clamp response, estimated from **endpoint levels**, with uncertainty. If that denominator is near zero, report the degree scale and denominator separately rather than an unstable percentage. A CI inside ±0.2 is only useful as calibrated equivalence if null/positive-control recovery supports coverage and sensitivity at this margin.

## Modest observational analysis

Use actual chronology, retaining missing rows. An eligible index and its intended past/future window must stay within the same randomized 180-trial portion; deterministic terminal probes must not be treated as randomized events. Missing outcomes do not join otherwise nonadjacent trials. All analysis selections and calibration rules should be fixed before reserved outcomes are opened.

Fit each source set separately and combine with equal set weight. Use participant as the uncertainty unit and account for the covariance of all five horizons when taking their mean. Participant-block intercepts/linear drift, flexible lagged input-cell responses, intervening input-cell responses, and current readout-cell effects should be matched between restricted and propagation models. Do not use lagged observed hand angle as an error-free memory state. Include signed index jump and allow signed-index-jump × old-input nuisance terms if direction symmetry is not imposed by the frozen scientific estimand. If only a symmetric target-event contrast is estimated, make that averaging explicit.

The distributed-lag coefficient is a specified finite-dimensional projection unless stronger causal assumptions are justified. The actual balancing rule creates dependence among assignments. The exported sequences support 180-trial balancing, not the paper's unverified 24-trial permutation scheme. Do not permute individual event signs independently or claim an exact randomization test without acquisition code supporting that distribution. Simulate on the actual input sequences, including fixed two-timescale histories, to measure omitted-tail bias.

### Fixed pre-index subtraction

The lead proposed `D[t,h] = y[t+h] - mean(y[t-1],...,y[t-5])` to reduce drift. This can be appropriate for the **index-event interaction**: under valid assignment adjustment, the same pretreatment quantity cancels in the event contrast. It is not the same as estimating a latent state from noisy hand angles. It also does not automatically preserve the ordinary main previous-clamp response, because the precursor can affect the subtracted endpoints.

Requirements: verify the chronology; use the fixed five weights; specify how missing baseline endpoints affect eligibility; do not average a variable number of observations silently; apply the identical transform in recovery; include correlated noise and overlap in uncertainty; retain endpoint-level sensitivity. Finite schedule dependence plus omitted history can prevent exact empirical cancellation, which is a reason for the level sensitivity and actual-sequence controls. The relative-effect denominator belongs to the level analysis.

Never subtract `y[t]`: that index endpoint can contain the treatment's online effect, creating an artificial persistent difference in `y[t+h]-y[t]` even when later endpoint levels are unaffected.

## What stationary readouts do and do not buy

The accompanying script independently reconstructs support using only `SN,TN,clamp_size,tgt_jump_size`.

| Set | All eligible index events | Previous target stationary | No-jump readout, h=1 | Previous and readout stationary, h=1 | Every future target stationary through h=5 | Previous and every future target stationary through h=5 |
|---|---:|---:|---:|---:|---:|---:|
| A | 4,550 | 1,540 | 1,483 | 494 | 13 | 6 |
| B | 4,521 | 1,517 | 1,525 | 496 | 16 | 6 |

At h=2–5, the previous-and-readout stationary count remains 476–529 per set. These are useful common-condition endpoints. Requiring **all** intervening targets stationary destroys long-horizon support. Main readout-only restrictions therefore marginalize over or adjust the actual intervening assigned inputs; they do not measure five undisturbed free-decay probes. For causal interpretation, the readout condition is an assigned input, whereas post-index observed movement/latency is a possible mediator and should not be conditioned on casually.

A no-jump readout removes a contemporaneous target-jump readout artifact such as `d(j[t+h])`. It does not remove an event's lingering expression effect, its effect on subsequent learning, or state-dependent perceived-error correction. Future intervening events can themselves modulate the earlier state's influence; both model classes need matched treatment of that environment.

## Exact retention/perceived-error equivalence

Consider the storage interpretation

`x[t+1] = a[J[t]] * x[t] + b[J[t]] * c[t] + q(j[t])`.

Now hold intrinsic storage retention fixed at `a_star` and define a state-dependent perceived error

`e[t] = c[t] - lambda[J[t]] * x[t]`,

`x[t+1] = a_star * x[t] + b[J[t]] * e[t] + q(j[t])`.

Choosing `lambda[J] = (a_star-a[J])/b[J]` makes the two recurrences **identical**. For positive gains, taking `a_star >= max(a[0],a[1])` permits nonnegative correction weights for either direction of target-event modulation. In particular, zero programmed clamp does not force perceived error to zero: it becomes `-lambda[J]*x[t]`.

The script checks both directions on all 40 actual 824-trial schedules. It uses `a_star=.97`, storage retentions `.92/.78` or `.78/.92`, gain `.20`, and a shared signed-jump term `.015*j`. Corresponding perceived-error weights are `.25/.95` or `.95/.25`, both in `[0,1]`. Maximum path discrepancies are `1.33e-15` and `2.66e-15` degrees. These values illustrate a parameter identity, not a fit or a claim that these are the empirical parameters. The identity itself applies to any supported parameter mapping.

With the same initial state, observation law and noise law, the likelihoods coincide. An oracle likelihood-ratio test has no discriminating information for this exact pair, regardless of sample size or no-jump readout filtering. Adding an identically distributed process innovation on both sides preserves the identity. Both interpretations can produce a nonzero observable propagation effect. Therefore a positive observable test can reject a restricted *programmed-current-input-only* model but cannot by itself identify storage retention against this perceived-error account.

For multiple states, the same ambiguity can hold component by component when a state-dependent error signal may enter each state. With only one shared perceived-error scalar and specified observation geometry, the matrix restriction can be testable: a correction of form `K[J] H x` has rank at most one. Do not claim that *every* arbitrary multi-state retention matrix is equivalent under that narrower model. Conversely, proving the scalar equivalence is enough to defeat a unique storage claim from a compatible scalar fit.

## Serious testable alternatives and recovery targets

| Generator | Required role | Diagnostic consequence |
|---|---|---|
| Fixed one-state retention, flexible current input-cell gains | Null | Event on zero programmed clamp must not create a spurious old-input interaction unless state-dependent current error is explicitly present. |
| Fixed fast/slow states, different input-cell gains | Stronger null | Slow omitted tails, changing fast/slow mixture and schedule balance must not be mistaken for an index propagation change. |
| Index-specific retention or equivalent perceived-error correction | Positive behavioral control | Recover both signs of the observable scalar/curve; do not classify the perceived-error parameterization as a false positive for a behavioral effect. |
| Pure contemporaneous online endpoint correction | Measurement null | Changes y[t], not future state; it should not create future level effects. |
| One-reach delayed expression modulation | Immediate-effect matched challenge | Match the h=1 propagation effect but remove it at h>=2; the estimator should distinguish the rebound if information permits. |
| Expression modulation decaying over several reaches | Harder challenge | Can match a retention-like lag curve; quantify the limit instead of assuming a later no-jump endpoint rules it out. |
| Endpoint correction feeding a later state-dependent update | Strong alternative | Can create persistent effects without a direct storage change. |
| Correlated process/measurement noise, slow drift, omitted endpoints | Robustness | Use the identical eligibility, baseline subtraction and participant-level inference in every run. |

Recovery should report bias, CI coverage, sign error, null rejection and detection at ±0.2 degrees, not merely correlation between fitted and true parameters. Predefine how a generator's parameters are calibrated to the observable scalar: a retention parameter change is not itself a degree-scale effect. Distinguish true counterfactual finite-schedule effects from the estimator's projected target if nonlinear interactions prevent their equality. Preserve a comparison at empirical development noise and a low-noise diagnostic; low-noise success alone does not establish real-design sensitivity.

### Oracle discrimination

For a pair of known generators with matched immediate effects, simulate their full joint trajectory distributions on the actual schedules. If Gaussian with common covariance `Sigma`, `D^2 = (mu1-mu0)' Sigma^{-1} (mu1-mu0)` measures the information available to an ideal test. With equal priors, optimal classification error is `Phi(-sqrt(D^2)/2)`; at a 5% one-sided Neyman–Pearson threshold the power is `1-Phi(1.645-sqrt(D^2))`. These formulas concern that specified pair and covariance, not all plausible models.

Use this to separate estimator failure from limited information: high oracle discrimination with poor regression recovery calls for a principled estimator repair; low oracle discrimination at the original margin is a design limitation for that pair. Exact retention/perceived-error equivalence gives `D^2=0`, so no estimator repair can solve that mechanistic ambiguity. The empirical question about observable propagation remains worth testing.

## Held-out prediction and independent transfer

Separate two outcomes on reserved primary participants: (1) re-estimation of the fixed observable contrast with its fixed inference procedure, and (2) prediction by development-fitted restricted/propagation models, with permitted baseline calibration fixed in advance. Refitting all gains on validation and then calling the comparison held-out prediction would spend the holdout. Average paired loss differences by participant; thousands of overlapping event windows are not independent replication units.

External data have no randomized zero-clamp main index trials. They cannot replicate the primary contrast. A transfer rule must extend the inferred propagation law to nonzero current clamps, with the current-input learning contribution already determined on eligible primary nonzero-clamp cells. That additional invariance assumption is a substantive transfer hypothesis and should be frozen explicitly. Shared clamp magnitude alone is insufficient if target geometry, flicker, prior input cells or endpoint readout differ.

If an external flicker or geometry has no primary analogue, do not silently set its effect to zero or refit its gain on external main outcomes while calling the entire prediction untouched. Define an eligible context, an explicit nuisance-only calibration scheme before opening outcomes, or state that a strictly quantitative transfer is unsupported. The source-measurement agent owns the detailed eligibility audit. A failed external extrapolation limits transport; it does not erase a primary within-design effect.

## Reproduction and exposure

Run from the repository root:

```sh
.venv/bin/python campaigns/target_event_carryover_2026-10-28/audits/design_challenge/input_only_challenge.py
```

Outputs: `input_only_challenge.json`. The script preserves original CSVs and records their SHA256 hashes. It reads CSV records and immediately retains only the four allowed input/identity fields; no behavioral value participates in a computation. Its algebraic simulations generate their own states. The first numerical demonstration used unequal gains with larger implied error weights; before final audit, it was replaced with equal gain `.20` to demonstrate that the same identity also holds with both perception weights within `[0,1]`. This is a purely synthetic presentation change, with no empirical outcome inspection.

No root learning/state file was edited, to respect assigned ownership. Project-specific lessons worth considering at campaign completion: set A's clamp/jump support is not Cartesian; a marginal signed-clamp interaction therefore needs a fixed prior-target contrast for a cursor-specific claim. Stationary readout and an entirely stationary future path are quantitatively different eligibility rules in these sequences.
