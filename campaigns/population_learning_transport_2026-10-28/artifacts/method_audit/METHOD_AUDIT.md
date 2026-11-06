# Population gate audit before new-source exposure

2026-10-28, America/New_York. This audit used only the original 40 already-consumed primary source animals and their development-fitted frozen model. It opened no new-source or protected external prefix/outcome. The new metadata-only coverage audit establishes 24 primary animals in five previously represented labs, with counts 5/2/1/10/6. Those counts replace the prospective feasibility estimate of 26 animals.

## Endpoint and precision actually checked

`code/gate_audit.py --precision` reconstructs the exact requested observed endpoint from the archived consumed-source arrays: on each 500-opportunity bin after the 1,000-opportunity prefix, average the left and right correct shares among trials with absolute contrast exactly 1. Omissions are failures. Each animal/bin has equal weight. All 40 consumed controls have both side cells in every bin. This differs from the old campaign's absolute contrast ≥.5 endpoint.

The RNN and growth simulations use the original model, saved prefix calibrations, development donor bank, autonomous trainer and generated outcomes, with 128 particles each. No actor is fitted. The consumed-source observed mean curve is [.53850,.57879,.60795,.64300,.67014,.70051]; the RNN curve is [.54693,.57737,.60323,.62764,.65087,.67384]. Population curve MAE is 1.264 pp for RNN versus 4.289 pp for growth. The observed-minus-forecast scalar bias is +0.983 pp and the animal scalar residual SD is **10.547 pp**. This is an exploratory precision anchor, not an independent test of the new target.

At N=24 this variance gives an approximate 90% animal-t halfwidth of 3.7 pp. The ±5 pp population tolerance is therefore difficult to certify even when the true forecast is accurate. Conditional Monte Carlo precision of the simulator does not remove this population uncertainty.

## Recommended frozen release gate

Apply every check to the one selected frozen RNN, with no learner tournament:

1. The 90% Student-t interval for mean animal scalar error lies wholly within [-.05,.05]. This is the conventional pair of one-sided 5% equivalence tests, not failure to reject zero.
2. A second 90% interval using CR1 lab-cluster sandwich SE and a t distribution with G−1 degrees of freedom also lies wholly within [-.05,.05]. For scalar animal errors z_i and their overall mean z̄, the variance is G/(G−1) × Σ_g[Σ_{i∈g}(z_i−z̄)]²/N². There are five labs, hence four degrees of freedom. This is a control-checked sensitivity safeguard with few clusters, not a universal exact confidence procedure.
3. Population six-bin MAE ≤.05; maximum absolute bin bias ≤.075.
4. Every represented lab's scalar point bias is within ±.10; every leave-one-lab-out pooled scalar point bias is within ±.05.
5. The lead's separately specified baseline noninferiority, completeness and simulation/reader controls must also pass. Adding those requirements can only reduce acceptance relative to the controls below.

The singleton lab check is a safeguard on one observed animal, not evidence of that lab's mean calibration. The target is the selected source mixture, conditional on observed opportunity coverage. Five labs do not become 24 independent environments. No gate here licenses an individual-utility claim, unique learning mechanism, causal curriculum effect or general new-lab guarantee.

## Known-answer calibration and what failure would mean

`CONTROLS.json` contains 20,000 repeats per generator/bias at the actual fixed lab counts. Six-dimensional residuals preserve the consumed-source bin covariance. Checks include Gaussian residuals; centered empirical residual resampling; greater animal heterogeneity; fixed lab biases; random shared lab shifts with SD6 pp; and a completion-selected population. The stopping example explicitly targets the population that completes the horizon; it does not infer missing futures for discontinued animals.

The final gate's worst acceptance of a known scalar error at or beyond ±5 pp is **4.10%**, at the +5 pp boundary in the low-variance control. Its exact binomial Monte Carlo 95% upper bound is 4.384%. The ordinary empirical-variance +5 pp control passes 2.735%. Known ±25 pp errors and a zero-scalar curve with opposing ±12 pp early/late errors never pass in 20,000 repeats. A low-variance known-zero-error case (the source residual scale multiplied by .25) passes all 20,000 repeats. These are estimator controls, not a substitute for a simulator/reader positive control using an actual transferable learner.

**The gate has low power at empirical heterogeneity.** A true-zero-bias forecast passes only 16.34% of empirical controls and 18.82% of Gaussian controls. More animal heterogeneity, fixed offsetting lab errors, or common random lab variation lowers this further. The scalar animal interval alone passes approximately 47% of correct empirical forecasts. In random shared-lab controls it can also accept a +5 pp error too often; the extra cluster and subgroup safeguards reduce false releases. Neither individual interval has a general finite-sample coverage guarantee for every possible distribution.

Consequently, a failed gate can be a decisive miss only if the actual errors/intervals establish a practical discrepancy. A wide interval or a subgroup point check failure means release was not earned, **not that the forecast was scientifically falsified**. Report effect sizes, both intervals, curve shape and all failed checks before choosing that interpretation. Do not relax the tolerances after new outcomes.

## Reproduction and artifacts

From repository root:

```sh
campaigns/learning_rule_transport_2026-10-28/.modelenv/bin/python campaigns/population_learning_transport_2026-10-28/code/gate_audit.py --precision --controls --particles 128 --repetitions 20000 --counts 5,2,1,10,6
```

`CONSUMED_SOURCE_EXACT100.npz` stores exact observed curves, side counts and all RNN/growth forecast particles for independent checks. `SOURCE_PRECISION.json` records old processed-byte/model/bank hashes and runtime. `CONTROLS.json` is authoritative for the final dual interval gate. The N26 and animal-only N24 control files are explicitly preserved preliminary stages. Logs and stderr are local. No historical model/data artifact was changed.
