# Fig3 transfer audit and outcome-blind recovery

2026-10-28. No independent-laboratory behavioral outcome was accessed. `load_external(inputs_only=True)` retained input/identity fields and supplied zeros for design construction; every analyzed endpoint below was generated synthetically. This audit imports the lead's transfer design but independently generates full chronological synthetic trajectories and batch-computes cluster scores. It is separate from the original-byte empirical reconstruction of primary development data.

## Transfer estimand and code review

The candidate transfer asks whether the primary set-A zero-clamp propagation contrast transports to **nonzero ±4-degree current clamps**, comparing external NoJump with JumpTo. It retains the fixed prior-stationary-target +4/−4 half-contrast and the equal-weight future horizon 1–5 scalar. This requires invariance to the current programmed clamp and laboratory/task implementation. It is not a zero-clamp replication.

The inspected `transfer.py` correctly:

- Uses Figure3 `TargetJump==0` for stationary and `TargetJump==ClampAngle` for jump-to.
- Keeps `.01` flicker as a distinct input-cell category in past/intervening/readout nuisance terms; it is not treated as a small spatial target shift.
- Uses all eight historical clamp/condition cells, including jump-away and flicker, while restricting the index to NoJump/JumpTo.
- Allows current clamp sign, current clamp sign × event, and sign × event × previous-cell nuisance. Thus the primary `Z` contrast averages over current ±4 clamp signs rather than attributing a current-error response to old input.
- Constructs the same prior-stationary +4/−4 half-contrast from eight prior-cell × centered-index-event coefficients.
- Keeps chronological rows and uses complete past/future windows; the four 200-trial epochs are nuisance drift epochs, not claimed randomized blocks.
- Uses the source-audited endpoint `−HandError` when released. The audit did not inspect those values.

The lead's frozen substantive prediction is the development set-A lag curve/scalar. Measuring the external contrast by fitting an already-frozen nuisance/estimand specification is legitimate evaluation of that prediction; it is not a prediction of every external endpoint without fitting. Keep this distinction explicit. No external effect estimate should be fed back into the transported substantive prediction.

Compatibility of an external CI with an uncertain near-zero development estimate is not positive predictive confirmation. Report the signed observed external contrast, its precision, the frozen prediction and the difference between them. A source prediction with large uncertainty supports only a weak compatibility test. The original compatibility implementation used t df=26; the reviewer recommended Welch–Satterthwaite df from the independent source-A and external scalar variances, matching the correction to primary set pooling.

## Input support and rank

| Readout | h=1 | h=2 | h=3 | h=4 | h=5 |
|---|---:|---:|---:|---:|---:|
| All future readouts | 6,966 | 6,966 | 6,966 | 6,966 | 6,966 |
| Stationary readout | 1,651 | 1,673 | 1,687 | 1,603 | 1,634 |

The residualized eight interaction columns have rank eight at every horizon. Their condition numbers are 1.13–1.18 for all readouts and 1.25–1.44 for stationary readouts. Full-model ranks are 221–249 and 215–243 respectively. Restricting the current readout to a stationary target makes six readout-cell indicator directions unavailable, which explains the lower nuisance rank; QR correctly removes those redundant directions. Rank confirms support, not power.

## Synthetic generator and targets

The recovery script uses the actual 18-person Figure3 input sequences and synthesizes complete 904-trial endpoint arrays. The fixed-retention base state is

`x[t+1] = .8*x[t] + gain[cell[t]]*c[t]`,

with gains `.14,.08,.09,.12` for no jump, flicker, jump-to and jump-away, plus direct current endpoint terms `0,.03,.12,-.07` times clamp sign. Each participant's response amplitude varies with lognormal SD .25. Noise contains an AR(.55) component with marginal SD 2.2° and independent SD 1.3°, multiplied by participant noise heterogeneity with log SD .15. Slow sinusoidal and linear drifts are added. This is a development-scale synthetic noise choice, **not** an estimate of external noise or a universal task-power calculation.

For every eligible NoJump/JumpTo index, a signed stimulus

`(J[t]−.5) * c[t−1]/4 * I(j[t−1]=0)`

enters each of the next five endpoint levels, multiplied by an assigned coefficient of −0.2°, zero, or +0.2°. Contributions from overlapping events are added to form one consistent trajectory. This creates a direct known five-reach propagation kernel with either sign. The exact analysis then subtracts its five-pretrial baseline and fits the actual observed input history.

Because overlapping contributions and omitted longer interactions can shift a finite-design projection slightly, the script reports both the assigned coefficient and the noiseless estimator projection. For assigned coefficients −.2,0,+.2, those projections are −.196163,+.000546,+.197255° for all readouts and −.202402,−.000616,+.201170° for stationary readouts. The discrepancy is small here; it is not silently defined away by changing the recovery truth.

There are 300 independent simulated populations per assigned coefficient, seed `2026102817`; the same noise draws are reused across coefficient signs to reduce Monte Carlo noise in their comparison. Every synthetic population contains all 18 participants. No values approach the 90-degree exclusion threshold. The batch coefficient/score computation agrees with lead single-fit functions to at most 3.1e−16 for the tested synthetic trajectory.

## Recovery result

| Readout | Assigned scalar | Mean estimate | Empirical SD | Mean cluster SE | 95% CI coverage | Zero rejected |
|---|---:|---:|---:|---:|---:|---:|
| All | −0.2° | −0.1909° | 0.1041° | 0.1131° | 96.3% | 31.0% |
| All | 0° | +0.0058° | 0.1041° | 0.1128° | 96.0% | 4.0% |
| All | +0.2° | +0.2025° | 0.1041° | 0.1128° | 96.0% | 38.3% |
| Stationary | −0.2° | −0.2018° | 0.1980° | 0.1944° | 95.7% | 13.3% |
| Stationary | 0° | +0.0000° | 0.1980° | 0.1942° | 95.3% | 4.7% |
| Stationary | +0.2° | +0.2018° | 0.1980° | 0.1944° | 95.0% | 17.3% |

Median 95% interval widths are about .466–.467° for all readouts and .818–.819° for stationary readouts. At the null, only 2.7% of all-readout intervals and zero stationary intervals fall entirely within ±.2°. Wrong-signed significant estimates occur in 0/300 all-readout positive/negative runs and 1/300 for each stationary sign. Monte Carlo uncertainty remains: with 300 replicates, a rate near 5% has SE about 1.3 percentage points, and a rate near 35% has SE about 2.8 points.

This is a useful calibrated procedure for the tested linear effect and noise generator, with low sensitivity at the frozen practical margin. It does not justify interpreting a nonsignificant external result as no transfer, and it does not certify all perceived-error, multi-timescale or expression alternatives. Those remain part of the primary campaign's broader recovery/identifiability analysis. Conversely, these controls show that the external design is not rank-deficient or intrinsically incapable of returning an observable contrast; it yields that contrast with finite precision.

## Reproduction and artifacts

```sh
.venv/bin/python campaigns/target_event_carryover_2026-10-28/audits/transfer_check/recovery.py
```

Outputs are `outputs/transfer_recovery/recovery.json` and `recovery.log`. JSON records source/code hashes, generator parameters, individual lag means, noiseless curves, complete support/rank diagnostics, calibration and power. Re-running does not require external outcome release and must retain `inputs_only=True`.

The separate empirical primary reconstruction is ready for post-release validation:

```sh
.venv/bin/python campaigns/target_event_carryover_2026-10-28/audits/independent_extraction/reconstruct.py --part validation
```

It asserts a validation release file and reads only the designated validation participants. This command had **not** been executed when this review was written. Independent-laboratory empirical outcomes also remain sealed.
