# Independent model audit — design frozen before simulation

2026-10-28. No numerical target-study outcomes were used to select this audit. Root subsequently supplied two calibration medians; they are not used here. All numerical values below are dimensionless synthetic design values, not bird estimates. Scope: scalar duration learning, acquisition lesions, competing tutors, and clocks during acquisition/production.

## Claims to test

1. A common acquisition state with a writable gate admits reference, motor-attractor, and shared-readout implementations with equal observed timing paths. Demonstrate across nonlinear duration encodings, sequential conflict, pre/post acquisition gate lesions, and independent tutoring/production clock changes. This is an exact restricted-class construction, not a finding that all biological versions fit equally well.
2. A whole scalar learning vector field can be represented as a potential gradient. Numerical examples supplement the analytical derivation; they do not establish neural implementation.
3. Adding passive target tuning and direct motor timing readouts improves identification of two functional targets but cannot distinguish a common trace from two copies unless an intervention selectively reaches one trace. Quantify rank and the null direction. A claimed selective common-trace intervention without an independent selectivity check is circular.
4. A randomized within-bird auditory-feedback shift crossed with evaluator-pathway inhibition can recover the *functional contribution* of that pathway to error-sensitive practice, given exclusion restrictions. Combine it with tutor-specific evaluative tuning at matched motor output. This cannot distinguish a sensory-stored target from a target read out of a motor trace.

## Fixed numerical checks

- Seed 21873; 1,000 randomized curriculum/clock/encoding cases, 60 practice updates each.
- Nonlinear encodings: linear, log, square root. Positive timing state; trial-by-trial common innovations. Acquisition update in encoded coordinates. Lesion removes future writing, not consolidated state. This is a mapping assumption to audit against methods.
- Functional-gain recovery: total calibrated relaxation gain κ=0.1; evaluator fractions α∈{0,.25,.5,.75,1}; auditory shifts δ=±0.2; n∈{6,12,24} independent birds; 10 or 50 repeated trials per cell; Gaussian trial SD∈{0.03,0.1}; bird intercept SD=.08; inhibition main effect SD=.05. 1,000 generated datasets per combination.
- Estimator: each bird's difference of auditory-shift slopes between pathway-active and inhibited conditions, divided by κ. Population interval uses a two-sided t interval over birds, never trial-level pseudoreplication. Record coverage, RMSE, and detection of positive α. Recovery with incomplete inhibition estimates α times efficacy, not α itself.
- Negative-control sabotage: a motor-stored target feeds the same evaluator at readout. It must remain exactly indistinguishable from a sensory-stored target on every proposed behavioral/evaluator measurement. An off-target auditory-dependent inhibition effect must demonstrate lost causal selectivity.
- Evaluator tuning: symmetric fixed feedback probes at ±.4 with quadratic score, q∈{−.5,+.5}; calibrate score curvature separately. 12 birds/group, 50 probes/side, score SD=.3. This demonstrates statistical precision under invented noise, not required animal sample size.

## Exclusions required for interpretation

Auditory feedback shifts must not change the immediate motor rendition or exploration distribution before the measured update; inhibition must not change the delivered auditory error, direct motor plasticity, or a parallel auditory-sensitive controller; delayed after-effects must be measured with ordinary feedback restored. Target-specific score tuning must be obtained at matched heard acoustics and motor state, with score curvature/gain controlled. Independent units are birds. Violations are analyzed, not hidden by fitting.

No proposal here claims a presently feasible cell-type-selective perturbation. The decisive uncertainty is perturbation specificity and functional mediation, not a nominally large sample or a passive memory decoder.
