# Local learning pilots — frozen before simulation outcomes, 2026-10-28

Owner: local_learning agent. All claims from these tests are computational claims about specified linear rules, not evidence for a biological circuit or novelty.

## A. Does variance learning preserve a drive-relevant representation?

Question: a one-dimensional unsupervised bottleneck can retain large variance while discarding a weak variable useful to a downstream drive. Does training correlation obscure that failure?

Generate eight-dimensional Gaussian observations by a random orthogonal rotation of signal `s = y + 0.25 eps`, nuisance `n = sqrt(v)*(rho*y + sqrt(1-rho^2)*eps)` and six independent noise coordinates (SD 0.1). Drive target `y ~ N(0,1)`. Sweep nuisance variance `v in {0.25,1,4,16}` and training correlation `rho in {0,0.8}`. Test on independent matching data and independently generated data with `rho=0`. No biological annotations are used.

Compare Oja's update `w <- w + eta*z*(x-z*w)` (one neuron), exact sample PCA (positive algorithmic control), full linear least squares and an oracle signal-axis bottleneck. Fit the scalar decoder on a separate same-distribution calibration sample, never on test. Exact covariance supplies the top-eigenvector check; do not mistake a correct PCA answer for task adequacy.

Before outcomes: Oja should agree approximately with PCA away from nearly degenerate eigenvalues. When an independent nuisance has larger variance than the signal, both should lose drive information although full linear regression retains it. With correlated nuisance, matching-distribution performance may look better than shifted performance. Failure to learn the known top axis makes the relevant result inconclusive. A result just confirming these analytical predictions is a reproduced limitation, not a promoted new mechanism.

Minimal case: one seed. Main sweep: 20 independent rotation/data seeds, 20,000 training observations, 4,000 calibration and 6,000 test observations, `eta=0.01/(1+v)`; no hyperparameter selection from test performance. Record norms and covariance alignment.

## B. Does stabilization imply continued adaptability?

Question: Oja's stabilizing weight-dependent term can maintain bounded weights, but does an annealed learning rate impair tracking after a covariance switch?

Use 4D independent Gaussian input. Covariance eigenvalues `(4,1,0.25,0.25)`. At sample 20,000 rotate the dominant axis by 90 degrees; continue for 4,000 samples. Compare constant Oja `eta=0.0025`, annealed Oja `eta=0.0025/(1+t/1000)`, and frozen Oja after switch. Include a stationary environment with the same streams/seeds and the known post-switch principal axis as controls. Start all methods from the same random normalized vector. Global unit-norm projection is a separate stabilizing control with the same constant Hebbian step; it is not called a local rule.

Before outcomes: all stabilized methods should learn the stationary dominant axis. Constant plasticity should adapt more quickly than annealed/frozen plasticity, at a cost of more stationary fluctuation. Stable norms alone cannot diagnose useful adaptation. Because schedules are chosen in advance, no claim of universally optimal rate is possible. If constant plasticity fails in the switch condition, examine tracking horizon and positive controls rather than claiming all local learning fails.

Minimal case: one seed. Main: 20 seeds. Save alignment every 100 samples, norm and first crossing of squared post-switch axis alignment 0.9 (censored if unreached). No external empirical claims or human/animal learning recommendations follow from this model.

## Possible follow-up

Promote at most one direction after comparing informativeness with the wider campaign. Most likely these pilots establish constraints rather than new research bets. If A is informative, analytically derive its population covariance and inspect a covariance-normalized target-association baseline; if B is informative, test step-size sensitivity with held-out seeds and switch angles. Label any follow-up exploratory and freeze its choices before computation.

## Resource and reproduction

Use workspace `.venv/bin/python`, numpy only. CPU seconds/minutes, no data download. Commands and versions will be recorded in README.md and JSON outputs. Root owns aggregate campaign artifacts.
