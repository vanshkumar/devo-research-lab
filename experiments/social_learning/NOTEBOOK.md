# Social information updating — completed bounded investigation

Date: 2026-10-28. Decision: retain as the campaign's strongest empirical direction for a conditional next research action; do not claim a new biological mechanism. PLAN.md preceded CSV outcome inspection; FOLLOWUP_PLAN.md was frozen after the initial reanalysis and before its follow-up computations. All findings are exploratory reanalysis of the same experiment. No untouched subject validation exists.

## What changed a judgment

A first-encounter gate is compatible with this social-choice experiment, but the observations do not establish that the second encounter was ignored. Early-only copying is 46/74 (.6216), late-only 42/67 (.6269), and first copying after conflicting demonstrations 40/64 (.625). The main-minus-early-only difference is .00338, with date-cluster bootstrap95% interval [−.1566,.1511]. Similar observed rates are not equivalence. Main first-copying exact two-sided binomial p=.059941; date-bootstrap interval [.4833,.7581]. The latter uses15 recorded dates (14 with main trials), not known independent experimental blocks.

The most firm new-to-this-campaign finding is an **archival score/denominator discrepancy**: supplied copy_dc_bin records first-copying for T, while the paper defines last-copying. Literal reconstruction of the shipped Rmd's regression includes452 responses,247 from ineligible trials as zeros; the paper's behavioral index concerns205 eligible trials. Independent audit code confirms every stored response, including ten missing values, against R's three-valued Boolean semantics. This does not prove the published analysis used this exact version, or that its biological conclusion is false.

## Data, outcome and provenance

Original462 rows are unchanged at data/social_learning/data_primacy.csv. Publisher Figshare46746183 matches Dryad version296766 SHA256 exactly. Rmd46746186 matches publisher/Zenodo MD5. See SOURCES.md and manifest.json for exact URLs/hashes. Direct Dryad downloads failed403/401; public publisher supplement succeeded legitimately. No authentication, account creation or access bypass.

The sample has142 conflicting-pair,168 early-only and152 late-only trials. Eligibility requires both courtship colors and mating color present; reconstructed courtship colors are distinct. Eligible counts64/74/67 and paper-defined last/unique copies24/46/42 reproduce the reported rounded binomial tests. Standard-library csv reconstruction and exact combinatorial enumeration agree with the pandas/SciPy analysis.

The CSV has date/device but no explicit simultaneous-block or picture ID. We cannot reconstruct published blocks from device IDs (devices recur). Missing temperature/humidity/pressure is recorded; these are not outcome-derived covariates we selected into a favorable model. Assignment is described as balanced; inspected material does not establish a random treatment allocation procedure. No source-derived neuronal or psychological label is treated as ground truth.

## Selection and competing explanations

Among all matings, main first-copying is65/120=.5417; early-only69/128=.5391; late-only64/129=.4961. All-mating choice and choice after both males courted are different estimands: including one-courtship trials changes the female's opportunity to choose. The sensitivity does not invalidate the published conditional estimand. Conversely, conditioning on post-exposure courtship cannot by itself establish an unconditional learning effect.

Main choice-by-eligibility table among matings: first-color choices40 eligible/25 excluded; opposite choices24 eligible/31 excluded. Association odds ratio2.067, exploratory Fisher p=.0664. It neither proves selection bias nor removes it: courtship could mediate genuine preference. First-courter agreement among main matings is.800, versus.6406 in eligible trials. Raw diagnostics remain in courtship_diagnostics.csv; they are not a fitted causal mediation analysis.

Color balance does not explain away the selected main tendency: first-green21/32, first-pink19/32. Equal-color main estimate equals.625; bootstrap interval [.4728,.7586]. Leave-one-date-out main estimates range.5789–.6557, but this stability is not independent replication or a tight uncertainty bound. Hypothetical completion bounds for choices in all recorded trials are deliberately broad and do not define real choices for flies that never mated.

## Regression audit and stronger computational checks

followup.py integrates a logistic-normal random date intercept with40-point Gauss–Hermite quadrature and checks80 points. Coefficients differ<5.2e−7, negative log-likelihoods<6e−12. The sigma→0 limit matches ordinary logistic likelihood within2.9e−14. A known-parameter3000-trial/100-date simulation recovers beta[−.3,.8] as[−.3541,.8795] and dateSD.6 as.5733; this validates the computational method in a controlled case.

Three targets were explicitly compared:

| Target | n | C1 vs T / C2 vs T approximate Wald p | Caveat |
|---|---:|---|---|
| Shipped-script first/unique plus ineligible zeros |452|.811/.901|Different target/denominator from paper |
| Eligible first/unique |205|.967/.982|Common first/unique reference; similar rates, not equivalence |
| Eligible last/unique |205|.00425/.00437|Paper's outcome convention; date is not unavailable block |

These are our Gaussian-quadrature fits, not an execution of R/lme4's Laplace algorithm and not reproduction of its reported block-based p=.026/.025. Both eligible fits hit the logSD lower bound(−7), effectively ordinary logistic regression; this is not evidence that dates have no heterogeneous effects. Near-boundary Wald inference is approximate. The counts/source-code reconstruction is stronger evidence of the archival discrepancy than comparing these p-values. Independently reviewed equations/targets and caveats: audit_FOLLOWUP.md.

## What a constrained behavioral family says

For a single encountered demonstration, log-odds of copying are g plus stable color preference. In the conflict group they are(1−r)g plus color preference. r=0 denotes first-encounter gating,1 equal evidence/cancellation,2 a selected recency alternative. Profile grid r∈[0,2],201 points; all choices preserved in weight_profile.csv. Best r=0, g=.50635; equal-evidence relative likelihood.13235 and recency.004109. These are likelihood ratios to the best fit within this family, not Bayes factors, probabilities of mechanisms, measured synaptic weights or causal estimates. Common single-demo gain, stable color bias, selected-trial independence and the chosen link are substantive assumptions.

A saturating/context-dependent updater, earlier preferences, attention, memory versus expression, and post-exposure selection are not excluded. The literature also contains both contrary copying studies and neural intervention evidence for a different five-consistent-demonstration/long-term-memory paradigm. Two conflicting demonstrations cannot settle that broader field. No novelty claim is made for the general identifiability problem or social primacy hypothesis.

## Executed design calculation and stopping point

For a new A,B,B sequence, a persistent first gate predicts P(A)=logistic(g); symmetric additive evidence predicts logistic(−g). Conditional exact one-sided size≤.05 calculations distinguish these *specified* extensions: at fitted g,64 eligible independent trials yield power.9918; at g=.2,64 yields.4706 and200 yields.8557. This is not an optimal design, an actual new animal experiment, or validated transport of gain across sequences. Gain uncertainty, changed exposure duration/attention, clustering and eligibility could materially reduce power. It is useful because the candidate models give opposing predictions rather than another ambiguous two-exposure fit.

Recommended next action: first audit the intended score, experimental blocks and version of the published analysis. Then, if justified, compare balanced A,B,B and matched timing/single-exposure controls with behavior measured before male courtship and transparent inclusion. That is a conditional recommendation, not an authorized external experiment or contact. Evidence that all-mating/eligibility changes reflect a specified real choice mechanism, or an independent controlled sequence replication, would change the recommendation. This bounded campaign stops here.

## Reproduction commands

From repo root, with the isolated scientific environment:

```sh
.venv/bin/python experiments/social_learning/acquire.py
.venv/bin/python experiments/social_learning/run.py
.venv/bin/python experiments/social_learning/audit_reconstruct.py
.venv/bin/python experiments/social_learning/followup.py
MPLCONFIGDIR=$PWD/.mplconfig .venv/bin/python experiments/social_learning/plot.py
```

The acquisition script verifies caches as well as new files; it requires network only if originals are missing. seeds20261028(date bootstrap),1509(GLMM control). Configurations otherwise explicit in PLAN/FOLLOWUP_PLAN and scripts. Results: inclusion.csv, rates.csv, bootstrap.json, reconstructed_trials.csv, annotation_checks.csv, weight_profile.csv, design_power.csv, followup_summary.json, audit_*. Source and code claims independently checked; stdout/stderr logs saved. Empty main/follow-up stderr; no results suppressed.

Figure social_learning.png/svg is generated from saved outputs; eligible intervals are date-cluster percentile bootstraps. Orange all-mating estimates target a different population and deliberately have no interval displayed. PanelB is conditional likelihood, not a mechanism posterior.
