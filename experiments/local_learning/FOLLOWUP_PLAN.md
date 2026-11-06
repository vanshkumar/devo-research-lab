# B sensitivity check — frozen after minimal, before main and sensitivity outcomes

2026-10-28. The one-seed minimal case passed stationary controls; constant Oja tracked a 90-degree switch, annealed Oja did not within 4,000 observations. That is partly predictable from effective step size. The strongest objection is that an abrupt orthogonal switch and a selected annealing schedule manufacture a dramatic failure.

Test B on fresh seeds 100–119 with `eta0 in {0.001,0.0025,0.005}` and switch angle `{30,60,90}` degrees. Preserve the 20,000+4,000 exposure budget, stationary controls, eigengap and all metrics. Same independent data streams across methods within each seed/angle/rate; streams differ across seeds. Compare ending alignment, censored hitting counts and stationary errors. This is an exploratory robustness map, not an independent test of a hypothesis selected before seeing any data. It can narrow a claim to a specific angular/horizon regime. A full optimal-schedule or biological homeostasis study is out of scope.

Pre-main implementation inspection found the B generator initially used one fixed RNG whose output shape depended on seed count; changed it to one RNG keyed to each seed before the main sweep. Minimal data are smoke checks only. This ensures held-out sensitivity seeds really receive independent streams, not only different initial weights.

On this machine NumPy 2.0.2 `@` operations raised spurious floating-point warnings for finite small Gaussian arrays. Code now uses non-BLAS einsum for matrix multiplication; no warning suppression. Main outputs must be finite. Minimal run is retained in its own folder rather than overwritten.
