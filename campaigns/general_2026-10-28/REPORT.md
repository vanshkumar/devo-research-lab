# Research campaign: what should be pursued next?

2026-10-28. **Completed bounded campaign: eight substantive pilots, two promoted directions with stronger follow-up and adversarial checks. No new biological mechanism established.** The strongest empirical next direction is experience-dependent updating of a social preference, provisionally using fruit-fly behavior. It emerged after the user redirected effort away from the obvious LOOPER continuation. The strongest established result is a reproducibility discrepancy in a public supplement, plus a precise account of what the behavioral observations can and cannot distinguish.

## Main finding: a plausible social-update gate, weak mechanism identification

In a public experiment, observed first-demo copying after contradictory demonstrations is 40/64 (62.5%); early-only copying 46/74 (62.2%); late-only 42/67 (62.7%). Similar proportions fit an account in which the first encountered social information dominates. They do **not** establish equivalence or absence of updating. Main-minus-early-only is 0.34 percentage points, with date-bootstrap95% interval [−15.7, +15.1] points. The original rounded binomial results reproduce exactly; the main preference's two-sided p = 0.05994. These are the original experiment's subjects, not independent replication. [Primary paper](https://pmc.ncbi.nlm.nih.gov/articles/PMC11295924/), [reanalysis account](experiments/social_learning/NOTEBOOK.md).

The supplied outcome column and original Rmd need special care. For the conflicting treatment they encode *first*-demo copying; the paper defines *last*-demo copying. The Rmd's regression also passes 452 nonmissing responses, including 247 ineligible trials as zeros, while its per-group descriptive loop filters to 205 eligible trials. A second implementation reconstructed R's missing-value logic directly from the untouched CSV and matched every supplied annotation. This is an **archival score/denominator discrepancy**, not proof the published analysis used this exact version or that the paper's conclusion is false. Exact model/version provenance and experimental block IDs are absent. [Independent audit](experiments/social_learning/audit_NOTEBOOK.md).

All-mating first/unique copying is 54.2% / 53.9% / 49.6% across the three groups. This matters, but changes the estimand: one-courtship matings need not represent a female choosing between two actively courting males. Conditioning could select observations or mediate genuine preference. The data cannot decide that causal issue. Color stratification preserves the eligible tendency; date resampling broadens its uncertainty. [Saved rates](experiments/social_learning/rates.csv), [inclusion counts](experiments/social_learning/inclusion.csv).

![Social learning results](/Users/vanshkumar/Documents/repos/devo-research-lab/experiments/social_learning/social_learning.png)

Eligible intervals above are percentile bootstraps of 15 recorded dates, 14 with main trials. Dates are a proxy for missing experimental blocks. Orange estimates concern all matings, with a different eligible population. PanelB is a constrained behavioral likelihood profile, not a posterior over mechanisms.

## Stronger follow-up and the surviving objection

A model gives a single demonstration log-odds gain g and a contradictory second demonstration relative weight r, with stable color bias. r=0 is first-encounter gating;1 is equal evidence/cancellation;2 is a recency alternative. The best fit is r = 0, g = 0.506. Equal evidence has relative likelihood 0.132 to the best fit; recency 0.00411. This favors weak later influence **within the specified family**. Common gain across treatments, selected-trial independence and the link function are consequential assumptions. Context-sensitive attention, saturation, initial preferences and selection remain alternatives. These are neither probabilities of cognitive mechanisms nor measured synaptic weights. [Full profile](experiments/social_learning/weight_profile.csv).

We independently checked the outcome reconstruction and follow-up equations. Logistic-normal date likelihoods agree at 40/80 quadrature nodes within 5.2e−7 on coefficients; the zero-variance limit and known-parameter recovery controls pass. Eligible date-variance fits hit the lower bound; approximate Wald results are not exact reproduction of the reported block-based R model. These checks establish computational meaning, not the unavailable experimental assumptions. [Adversarial review](experiments/social_learning/audit_FOLLOWUP.md), [follow-up results](experiments/social_learning/followup_summary.json).

A conditional design calculation makes the ambiguity useful: after A,B,B exposures, a persistent first gate and symmetric accumulation predict opposite preferences. At fitted gain, 64 independent eligible trials give about 99.2% power in a specified one-sided simple-versus-simple test. At weaker gain g = 0.2, 64 give 47.1% and 200 give 85.6%. This is an executed exact-binomial calculation, not a new animal experiment or a validated sample-size recommendation: gain uncertainty, clustering, exposure time and changed eligibility could dominate. [Calculation](experiments/social_learning/design_power.csv).

Contrary context was checked. A 2021 study found limited copying support under another protocol/line; a 2025 study provides genetic rescue evidence for a different five-consistent-demonstration long-term-memory paradigm. Neither settles contradictory updating, and our reanalysis does not overturn all social-learning evidence. Exact inspected locations and access limits are in [SOURCES.md](SOURCES.md).

## Second promoted result: feedback can create observational ambiguity

For x[t+1]=Ax[t]+By[t]+e[t], y[t]=x[t], passive trajectories identify F=A+B. Internal recurrence(A=F,B=0) and externally supplied recurrence(A=0,B=F) have exactly identical observational laws. With F=.94R(.18), their executed paired paths agree exactly; design rank 2/4; conditional likelihood agrees. A simulated feedback clamp produces distinct predictions. This is an algebraic known-model constraint, not an empirical worm or human mechanism.

The stronger test breaks the ambiguity deliberately: y=x+qz with independent excitation. Across 600 fits including reserved seeds, feedback-parameter error falls approximately 1/q: verification median 0.450 at q = 0.01, 0.0459 at 0.1, 0.00458 at 1. Analytical equality/Lyapunov checks, an independent scalar recurrence and residualized regression support the result. The strongest objection is built into the controls: known parameters, richer noise or independent excitation can restore identification. Universal passive-recording impossibility would be false. Prior closed-loop identification work makes the broad result established background. [Evidence and reproduction](experiments/causal_identification/NOTEBOOK.md).

## Portfolio actually tested

| Pilot | What was learned | Decision |
|---|---|---|
| Neural forecast | Initial ridge failure reverses at 3 s under an anchored baseline on one animal | Revise; no no-information claim |
| Neural surrogate dimensionality | Coordination exceeds independent-channel nulls; pure sine exposes null blindness | Retain calibration, retire mechanism inference |
| Local variance learning | Oja/PCA can discard a drive-relevant signal despite good matched prediction | Retire novelty, retain objective constraint |
| Plasticity after switches | Unit norm coexists with poor tracking; annealed learning succeeds in easier regimes | Revise; no universal failure |
| Curriculum order | Equal-exposure order changes robustness/context fit; pooled convex convergence erases order | Revise; no human inference |
| Educational selection | Identical observed gains admit zero or positive causal effects | Retire after measurement requirement |
| Closed-loop identification | Exact ambiguity and an excitation-dependent recovery regime | Promoted follow-up complete |
| Fly social updating | Suggestive first-information dominance, coding/inclusion discrepancy and imprecise update contrast | Promoted empirical follow-up complete |

Full candidate ledger, alternatives, controls, decisions, initial expectations, failed attempts and source links: [PORTFOLIO.md](PORTFOLIO.md). The local-learning sensitivity grid was already underway before main allocation; it is retained without inflating pilot counts.

## What changed relative to the starting material

The initially empty lab now contains runnable tests rather than proposals. The public LOOPER questions did not become the campaign's centerpiece: baseline checks undermined a tempting negative interpretation, and no nonlinear-loop or cohort result was established. Four reserved worms remain untouched, rather than being consumed to polish that line. The social-learning direction was newly selected during this campaign; its archival mismatch and conditional update model are new to this investigation, not claimed new to science. The local/education simulations narrowed promising-sounding stories into explicit objective, finite-horizon and measurement constraints.

## Where the user's attention would be valuable

Audit the intended social-copying score, code version and trial-selection estimand first. The question is whether preference should be operationalized only after both males court, and how post-exposure courtship relates to the underlying choice process. Resolving it is more valuable than optimizing a richer model against the same binary outcome.

Recommended next research action: if that audit survives, choose a controlled multi-exposure updating experiment with balanced A,B,B sequences, timing/single-exposure controls and behavior recorded before male competition. Current likelihood/power computations explain why that could distinguish specified accounts; they do not authorize running it or contacting anyone. Independent sequence evidence or a credible explanation of selection/version provenance would strengthen the recommendation; a demonstrated measurement/analysis artifact or consistently weak learning would reduce it. No successor service, messages or publication were created.

## Reproduce and inspect

From `/Users/vanshkumar/Documents/repos/devo-research-lab`:

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -r experiments/requirements.lock.txt
.venv/bin/python experiments/reproduce.py
```

On a fresh checkout without the original public inputs, use `experiments/reproduce.py --fetch` instead. Existing inputs are hash-verified and all analyses run offline by default. Source PDFs are not needed to rerun calculations; supplied metadata/hashes document their provenance. The scripts regenerate selected result files; original CSV/JSON/Rmd remain untouched. Minimal historical runs and failed attempts are preserved separately. Reproduction logs/status are under experiments/reproduction/; seeds/configurations are in individual plans/scripts. The neural check uses six processed baseline recordings, not acquisition-raw movies; no Kato or LOOPER execution is claimed.

The environment installed ordinary scientific dependencies in .venv. Recorded data occupy about 50 MiB, sources 19 MiB, experiments 5 MiB before final logs; no large remote corpus, account, paid compute/API, private upload, messages, publication or permission change was used. The only real environmental obstacles were documented access/dependency issues resolved through legitimate alternatives or recorded as limits. The bounded campaign is complete; unresolved biological and provenance questions are scientific limitations and conditional next choices, not unfinished promised experiments.
