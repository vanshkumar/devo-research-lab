# Research portfolio — 2026-10-28

All comparisons are exploratory unless a later protocol explicitly freezes a validation set. Counts below refer to substantive tests, not searches. No numerical opportunity score is used. The starting context is interest in mechanistic learning and closed-loop neural behavior, plus the public LOOPER repository found during source discovery; this campaign does not assume its conclusions.

## Candidate questions, before main outcomes

| ID | Uncertainty and why it matters | Closest prior work / accessible material | First discriminating test | Main risk | Initial status |
|---|---|---|---|---|---|
| N1 | Does short-horizon neural prediction show dynamics beyond calcium persistence? Would change what forecast fidelity means. | Brennan et al. 2023 LOOPER; Kato 2015 and Atanas/Kim 2023 processed traces | Blocked forecasts against persistence and per-neuron AR at several horizons | Calcium indicator and preprocessing differ between studies | Pilot |
| N2 | Does apparent low dimensionality require neural coordination, rather than smooth finite traces? Would calibrate manifold evidence. | Kato population dynamics; Theiler-style surrogate tests; same recordings | Independent phase randomization with circle and independent-noise controls; compare dimensionality and prediction | Surrogates destroy nonstationarity too; no topology-specific conclusion | Pilot |
| N3 | Is failure to generalize a scaffold temporal drift or an evaluation failure? Would change which freely moving analyses deserve effort. | Public LOOPER split-half implementation and published validation methods | Inspect preprocessing/transfer definitions; controlled stationary example and purged splits | Full MATLAB LOOPER not available; a proxy cannot falsify LOOPER | Candidate; may deepen N1 |
| L1 | Can variance-driven local learning recover a weak drive-relevant input? Separates representation from innate readout alignment. | Oja rule; synthetic covariance with known PCA/readout optimum | Sweep signal-to-nuisance variance with analytical and supervised controls | Constructed task does not establish biological use | Delegated pilot |
| L2 | Does homeostatic stabilization preserve learning after an environmental switch? Useful stable-versus-plastic tradeoff. | Local normalization/adaptive plasticity literature; known covariance switches | Stationary/switching streams, fixed/decaying/adaptive learning and oracle | Highly rule- and timescale-specific | Delegated pilot |
| D1 | Do curriculum-order gains survive equal exposure and shortcut shift? Tests an education-adjacent mechanism outside recent worm work. | Curriculum/shortcut learning primary work; synthetic environments | Equal examples and compute across ordered/shuffled/alternating schedules, shifted test | No inference about human education | Delegated pilot |
| D2 | Can observed educational gains distinguish selection from learning? Clarifies necessary measurements. | Causal selection/identification literature; constructed observational models | Exact observational counterexample plus intervention control | Counterexample establishes possibility only | Delegated pilot |
| C1 | Can spontaneous neural/behavior loops identify intrinsic recurrence? Matters for interpreting mechanistic claims. | Closed-loop system identification; exact state-space models | Observationally equivalent mechanisms with divergent clamp predictions | Clamp idealization, restricted model class | Delegated pilot |
| B1 | Can public birdsong audio identify tutor-template error learning? Consequential sensory-learning ambition. | Charter's explicit warning; public audio alone | Check required tutor exposure, interventions and neural error measurements | Acoustic phenotype is many-to-one in mechanism | Retire pending appropriately paired measurements; no pilot claimed |
| S1 | Could sparse public-data metadata reveal whether reanalysis supports causal claims? Reusable slow-science infrastructure. | Atanas data availability and DANDI metadata | Audit actual trace, behavior, perturbation and identity fields in downloaded subset | Metadata audit alone is not a scientific pilot | Incorporate into N1 provenance; no separate pilot claimed |

## Pilot record

Initial status before execution was pending. The completed observed record follows; initial candidate decisions above are retained as history. Root owns this aggregate record.

## Added candidate after user steering

S2 — Does conflicting social information produce first-exposure locking, and can trial selection or coding change that judgment? This connects social responses to experience. Closest work: Santiago Araújo et al. 2024; 462 public fly trials and original Rmd; later social-memory/copying studies. First test: recompute outcomes and audit eligibility/color/date. Main risk: one selected experiment cannot establish mechanism or generality. Added after seven pilots and the user's request to avoid over-indexing on LOOPER; the paper result was known, but PLAN was saved before CSV outcomes were inspected.

## Executed portfolio and decisions

Eight substantive pilots were executed. Follow-ups/audits are not extra pilots. Initial protocols and full condition/seed grids remain in the folders. “Retire” refers to campaign investment, not proof a broad hypothesis is false. The earlier pending paragraph is superseded by this observed record.

| ID | Actual test / evidence | Result and controls | Final allocation / reason |
|---|---|---|---|
| N1 | Six discovery animals; chronological neural forecasts at .6/3/12/30s; 10-seed synthetic controls. [Notebook](experiments/neural_dynamics/NOTEBOOK.md), CSVs; [audit](experiments/causal_identification/audit.md). | Plain population ridge loses diagonal AR everywhere; anchored check on first animal reverses 3s comparison (+7.1%). Rotation recovery succeeds at recoverable horizons. | **Revise; stop after bounded check.** Mean-shift/baseline sensitivity defeats absence-of-information inference. Four selected validation worms remain unaccessed. No LOOPER rerun or cohort comparison. |
| N2 | PCA vs39 independent phase/shift surrogates, raw/differences; spectral invariants and controlled processes. | All6 exceed channel-independence coordination nulls; pure sine keeps rank≤2 under phases, so null is blind to that known case. Differencing creates a tiny endpoint artifact despite low p. | **Retain calibration; retire mechanism inference.** Coordination does not establish loops, nonlinearity or intrinsic recurrence. |
| L1 | 20 seeds, Oja vs sample/population PCA, full linear and signal oracle; covariance-shift risk. [Notebook](experiments/local_learning/NOTEBOOK.md). | Nuisance variance4/correlation.8: Oja R² .742 matched→−.248 shifted; full linear .917 shifted. Independent population calculation agrees with PCA outside small eigengap. | **Retire as novelty; retain objective constraint.** Variance alone cannot specify drive relevance. |
| L2 | Stationary/switching streams; constant/annealed/frozen Oja, projected Hebb;9 sensitivity cells, fresh seeds, mean-flow check. | At90°/eta.0025, constant20/20 reaches.9; annealed0/20 in4000samples, both norm≈1. Annealed succeeds in easier regimes. | **Revise; no major promotion.** Stabilization is not adaptation; no universal failure or biological critical period. |
| D1 | 40 paired synthetic datasets, equal exposure/compute,4 schedules; common convex optimum; analytic accuracy. [Notebook](experiments/development/NOTEBOOK.md). | Easy→hard reversed-shortcut accuracy84.05% vs shuffled71.02%; tradeoff on original context; order effect disappears at pooled convergence. | **Revise.** Real finite-step adaptation, insufficient lasting-abstraction evidence; no human data. |
| D2 | Exact binary selection/learning worlds;40 seeds,2 sample sizes; interventions/noisy-pretest; rational proof. | Identical joint(T,Y), observed gap.48; causal effects0/.48. Noisy pretest leaves.353 bias. | **Retire after measurement lesson.** Known identification limitation, no actual student data. |
| C1 | Exact closed-loop equivalence;600 excitation fits, reserved seeds; likelihood/Lyapunov and residualized-regression checks. [Notebook](experiments/causal_identification/NOTEBOOK.md). | Observation identifies A+B, not A/B under y=x. Clamp separates models; excitation restores rank; B error .450→.00458 as q.01→1. | **Promoted methodological follow-up, complete.** Useful design constraint; established background, restricted model, no biological discovery. |
| S2 | Reanalyzed462 fly trials; independent CSV/R-logic audit;5000 date bootstraps;40/80-node GLMM; update-weight profile and exact design power. [Notebook](experiments/social_learning/NOTEBOOK.md). | Eligible40/64 first copies,46/74 early-only,42/67 late-only. Archived response/regression differ from paper target; all-mating main65/120. Gate best in chosen family; equal-evidence relative likelihood.132. | **Promoted empirical follow-up, complete; conditional next-investment recommendation.** Interesting updating question; weak precision, selection, missing blocks and code-version provenance remain. |

## Candidates not executed separately

- N3: proxy/source audit folded into N1. Actual scaffold stationarity unresolved; stopped after user steering, not declared a scientific dead end.
- B1: not investigated. No claim a suitable birdsong dataset does not exist; audio alone cannot identify the charter's internal-template mechanism.
- S1: metadata inspection/source audit done for N1 provenance; not counted as a substantive pilot.

## Search, selection and failed attempts

Initial selection leaned too heavily toward the obvious public LOOPER continuation. User steering changed allocation: no neural validation expansion; a new empirical social-learning question became the main promoted direction. These are exploratory results; no selected effect is presented as independent confirmation or corrected across this entire portfolio.

Preserved failures: sandbox pip DNS; legitimate paper/download access failures; absent Kato file; a false universal phase-null positive-control assumption; local-learning generator bug fixed before main runs; finite-result BLAS warnings checked against explicit contractions; plain ridge conclusion broken by anchored baseline. Full notebooks retain these.

Allocation stopped after social-learning and closed-loop follow-ups plus adversarial review. No external actions or endless successor queue were created.
