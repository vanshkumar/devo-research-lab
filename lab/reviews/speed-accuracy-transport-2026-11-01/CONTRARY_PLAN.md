# One predeclared nondecision-map challenge

Declared 2026-11-01 after the independent first raw calculation and inspection of the saved prescription; before calculating this alternative. Assignment START08:35Z, hardSTOP09:20Z. This is the review's ONE contrary experiment, not a replacement primary test or a model tournament.

Question: does the original source-driven positive gain, which forces all individual target nondecision times toward the same .03-second floor, materially determine the failed latency transport? The alternative adds ONE source-estimated intercept while preserving the original source/held baseline parameters, drift rates, boundary-distance transport, source people, valid-response likelihood, empirical reference and scoring.

Let `tmin` be the minimum of the nine saved SOURCE baseline nondecision times. Replace the original gain map with

`t0_target = .03 + max(0, h + g*(t0_baseline - tmin))`.

Estimate two log boundary-distance factors in the original [.5,3] bounds, `g in [0,2]`, and `h in [0,.7]` from the nine SOURCE block-2 raw records only. For each source person constrain `.03+h+g*(t0_baseline-tmin) <= min(source_target_valid_RT)-.005`. Since source differences are nonnegative, the max is inactive in fitting. The original map is nested at `h=g*(tmin-.03)`; `g=0` permits a common source target delay. The floor handles a held baseline below the source range using no held future values. Held target RT minima never set constraints.

Use independently implemented conditional Wiener likelihood, Gauss-Legendre192 for fitting, and two fixed deterministic feasible starts: original saved P boundary factors/gain with its equivalent h, and factors1.3/g0/a constant h at half the smallest source upper allowance. Run SLSQP, maximum250 iterations/start, ftol1e-8. Retain the feasible lowest source objective, report both outcomes and constraint residuals. If numerical convergence is inadequate, keep the partial failure rather than changing the map or search. Reconstruct final forecasts at256/384 nodes and check any consequential quadrature discrepancy. No data-dependent model changes, extra starts, source deletion, quality multiplier or other alternatives.

Evaluate once on the already consumed eight target people, against the ORIGINAL source-selected reference and ORIGINAL joint rule. Also report source likelihood change, all original/changed endpoint losses and MAEs, per-person delay/prediction changes, and the original conditional person-bootstrap interval. A favorable result would show prescription dependence on a specific source-learned delay map; it would not repair the frozen failure, establish biological nondecision times, earn generalization, or identify shared evidence quality. A failure narrows this particular alternative only. Source-baseline/held-baseline full optimizer refits, source-resampling uncertainty and full-pipeline controls remain UNRUN.

Keep all predictions in the owned review directory. No network/new payload/dependency. Total separate review scientific-read/decode/hash allowance350MB, RSS800MB, one process/thread, stop09:20Z. Conservative first-stage charge30MB; audit100MB, contrary70MB and final reads/reporting30MB are reserved within that cap, including failed passes if any. These are manual allowances, not OS IO measurements.
