# Two local-learning pilots — completed 2026-10-28

These are controlled synthetic reproductions of limitations, not evidence that a biological learning circuit works this way. Main choices were frozen in PLAN.md before outcomes. Root did not promote this direction for the campaign's major follow-up.

## Reproduce

From repository root:

```sh
.venv/bin/python experiments/local_learning/run_pilots.py --minimal
.venv/bin/python experiments/local_learning/run_pilots.py
.venv/bin/python experiments/local_learning/run_pilots.py --followup
.venv/bin/python experiments/local_learning/analytical_check.py
MPLCONFIGDIR=experiments/local_learning/.mplconfig .venv/bin/python experiments/local_learning/make_figure.py
```

Actual numerical runs used Python 3.9.6, numpy 2.0.2. Plotting additionally uses matplotlib. Main run took about 2 CPU wall seconds; the full robustness grid took about 10. No external data or APIs. Outputs are CSV, JSON and PNG; no large arrays retained. Initial minimal output is preserved; rerunning minimal with current code intentionally incorporates the generator correction below.

## A. Variance learning and a drive-relevant signal

Uncertainty: can an unsupervised variance bottleneck lose a target that remains linearly recoverable from its input, and can correlated training environments hide that loss? Alternative: apparent loss could be a broken Oja implementation rather than its objective.

Procedure: eight-dimensional randomly rotated Gaussian observations, target-bearing signal variance 1.0625, nuisance variance 0.25/1/4/16, training signal–nuisance correlation 0 or 0.8. One-dimensional Oja representation; separate calibration decoder; independent matched and nuisance-decorrelated tests. Twenty seeds, 20,000 training, 4,000 calibration and 6,000 observations per test distribution. Exact sample PCA, known population covariance, full linear regression and oracle signal axis are controls. Raw rows: outputs/pilot_a.csv (640 rows).

| Condition | Oja matched R² | Oja shifted R² | PCA shifted R² | Full regression shifted R² |
|---|---:|---:|---:|---:|
| nuisance variance 4, independent | -0.00035 | -0.00042 | -0.00047 | 0.94067 |
| nuisance variance 4, training correlation 0.8 | 0.74189 | -0.24831 | -0.24078 | 0.91700 |
| nuisance variance 16, training correlation 0.8 | 0.66793 | -0.54939 | -0.54593 | 0.91700 |

All entries are medians over seeds. Oja's minimum squared alignment to the known population principal axis was 0.9953 outside the small-eigengap condition (variance 1, correlation 0). Thus the dramatic loss survives an exact PCA control and is not failed optimization. At the small gap Oja's minimum alignment was only 0.8362 and exact sample PCA's 0.9438: that regime must not be summarized as uniform convergence.

Adversarial check: analytical_check.py independently derives the 2×2 eigenvector and population decoder risks without using the Oja fit or an eigensolver. Its predicted population R² differs from median sample-PCA R² by at most 0.00898 outside the small-gap condition; outputs/analytical_check.json preserves every comparison. The conclusion follows from a specified variance objective and test covariance shift; it does not test any actual innate drive, reward-modulated rule, neural nonlinear representation or high-dimensional bottleneck.

Decision: **retire as a discovery candidate; retain as a validated constraint**. Maximizing variance alone cannot be assumed to align learned representations with drive relevance. This expected analytical counterexample is not a new mechanism. A real follow-up would require specifying which drive-associated signal a proposed local rule can actually access.

## B. Stable weights and nonstationary adaptation

Uncertainty: does bounded weight norm diagnose useful continued adaptation? Alternative: failure after an orthogonal switch could be a singular initial condition or a poor selected rate, rather than a general failure of plasticity.

Procedure: four-dimensional Gaussian input eigenvalues 4,1,0.25,0.25, twenty independent seed streams. After 20,000 observations, rotate dominant axis 90° and observe another 4,000. Compare constant Oja (eta 0.0025), annealed Oja (eta 0.0025/(1+t/1000)), frozen Oja and projected Hebbian learning. The latter is explicitly a global normalization control, not a local rule. Include stationary streams with the known dominant axis. Raw rows: outputs/pilot_b.csv; time series in outputs/pilot_b_trajectories.csv.

| Rule | Stationary final squared alignment | Switched final alignment | Reached 0.9 after switch | Median first crossing |
|---|---:|---:|---:|---:|
| Constant Oja | 0.99764 | 0.99764 | 20/20 | 556.5 samples |
| Annealed Oja | 0.99990 | 0.00124 | 0/20 | censored at 4,000 |
| Frozen Oja | 0.99713 | 0.00210 | 0/20 | censored |
| Projected Hebb | 0.99778 | 0.99778 | 20/20 | 562.5 samples |

All rules retained norms near 1. The annealed rule had lower stationary error while tracking the orthogonal switch much more slowly. First crossings alone can be transient; ending alignment and full trajectories are also provided.

Exploratory sensitivity was frozen after the one-seed smoke check in FOLLOWUP_PLAN.md: fresh seeds 100–119, eta 0.001/0.0025/0.005, angles 30°/60°/90°. Nine cells × four rules × two environments × twenty seeds = 1,440 rows in followup/pilot_b_sensitivity.csv. Constant Oja reached 0.9 in all 180 switched runs. Annealed Oja **did** adapt in easier regimes: all twenty reached 0.9 for 30° at eta 0.0025 and 0.005, and for 60° at eta 0.005. At the original eta 0.0025, ending median alignment was 0.9761/0.8163/0.00226 for 30°/60°/90°. This rules out a blanket claim that annealed Oja cannot adapt.

The independent mean-flow constraint uses `tan(theta_new) = tan(theta_initial) exp(-eigengap * sum(eta))`. It predicts 0.97620 and 0.82006 ending alignment at 30° and 60°, close to observed 0.97610 and 0.81629. At exactly 90°, noiseless flow starting exactly on the old axis remains orthogonal; stochastic noise seeds escape. followup/ode_check.json records the approximation and its limitations. This is a finite-horizon adaptation-cost result under specified schedules, not a proof of biological aging, a critical period or universal rate superiority.

Decision: **revise/retain as a constraint, do not promote as a major research direction**. Stabilization, adaptation speed and represented objective are distinct requirements. Follow-up would need a nonstationary environment with meaningful learning timescale and an online rate-selection rule, rather than a large undirected sweep.

## Failures and deviations preserved

- Original minimal B generator used a fixed RNG with seed-count-dependent array shape. Before main outcomes it was corrected to one RNG per seed, ensuring sensitivity seeds have distinct input streams. No main conclusions use the initial minimal B numbers.
- Small finite matrix products with numpy 2.0.2's BLAS `@` emitted overflow/divide warnings despite finite outputs. Code uses explicit non-BLAS einsum; main.stderr.log and followup.stderr.log are empty. No warning filtering was used.
- Original Oja PDF mirrors timed out, publisher access only exposed the abstract. The exact update is independently inspected in Chou & Wang's primary analysis, Definition 1.3, equation (1.4); see SOURCES.md.
- No inferential p-values over these known synthetic regimes, no claim of novelty, no biological validation, no published/private uploads, no paid resources.

State: both pilots and bounded robustness check complete. Next action for reproduction: run commands above. No blocked job or outstanding computation.
