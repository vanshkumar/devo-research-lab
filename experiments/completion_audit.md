# Independent completion and scientific-claims audit

Date: 2026-10-28. Scope: read charter, REPORT.md, PORTFOLIO.md, SOURCES.md, STATE.md, relevant notebooks/audits and current substantive outputs. No new pilots, parameter searches, source collection or root-file edits. This audit reviews the completed evidence; model agreement is not empirical confirmation.

## Verdict

**No blocking scientific or reproduction gap found in the final account.** Eight substantive pilots and two promoted directions with stronger follow-up are supported by runnable artifacts. The empirical conclusion is conditional and appropriately weak: the archive discrepancy is demonstrable, while a neural or behavioral first-encounter gate is not established.

At inspection, STATE.md was stale (seven pilots and social outcome not yet known), and LEARNINGS.md remained empty. Root is already assigned to finalize these. **Those two completion actions remain necessary before declaring all charter deliverables finished.** They do not require more experiments. No other necessary change was identified. The audit does not authorize any next external experiment, message or publication.

## Charter-to-artifact map

| Charter requirement | Actual artifact / executed evidence | Assessment |
|---|---|---|
| Capabilities, boundaries and workspace instructions | Charter preserved; environment and initial failures in STATE/notebooks; isolated dependency lock | Documented; no invented access or telemetry |
| Roughly 8-12 distinct candidates | PORTFOLIO initial N1/N2/N3, L1/L2, D1/D2, C1, B1, S1, plus later S2 | Eleven serious candidates; outside recent worm reading represented |
| About 6-8 substantive pilots | N1 neural forecasts; N2 surrogate dimensionality; L1 variance learning; L2 switch adaptation; D1 curriculum; D2 selection; C1 closed-loop; S2 fly updating | Eight actual computational tests; metadata/search and follow-ups are not inflated into pilots |
| Questions, alternatives, controls, interpretation, commands, decisions | Per-folder PLAN.md and NOTEBOOK.md; social/local FOLLOWUP_PLAN.md; causal fixed-setting verification protocol | Outcomes, failed controls, revisions and negative findings retained |
| Adaptive selection and two stronger directions | Causal 600-fit excitation regime; fly trial audit, date bootstrap, model/profile and exact design calculation | Stronger tests executed; local sensitivity is explicitly extra calibration |
| Scientific validation and adversarial checks | Known-effect controls; causal algebra/Lyapunov/residualized regression; development analytic integration/rational proof; social independent row reconstruction, quadrature convergence, zero-variance limit, parameter recovery and independent binomial enumeration | These test scientific estimands or known answers; not merely software execution |
| Actual empirical evidence | Public fly CSV/Rmd with source hashes and six processed neural records | No raw-image, Kato, LOOPER, human-learning or independent biological replication claim |
| Provenance and contrary findings | SOURCES.md plus individual source notes; public pinned data and unchanged source files | Access limits and unavailable final model/block provenance stated |
| Reproducibility | experiments/reproduce.py; requirements.lock.txt; acquisition scripts; seeds/configs; experiments/reproduction/ | Entire current pipeline actually completed successfully |
| Lightweight notebook, restartable state, final briefing | REPORT.md, PORTFOLIO.md, SOURCES.md, experiments/ exist; STATE and LEARNINGS require root finalization | No infrastructure substituted for investigation |
| Respect user steering | Report centers empirical social learning and methodological identification; neural result capped after adversarial baseline | Four reserved worms remain untouched; no new LOOPER-centered expansion |

## Reproduction status actually observed

`experiments/reproduction/execution.json` contains **17 completed steps, all returncode 0**. Every per-step `.stderr` file is empty. `experiments/reproduction.log` ends with `CENTRAL_EVIDENCE_CHECKS PASS`. These are observed final results, not assumptions based on a launched process. The execution record gives exact commands and runtimes, including data verification, all pilot scripts, analytical/independent audits, social follow-up and figures.

Reproduction entry point from repository root:

```sh
.venv/bin/python experiments/reproduce.py
```

The acquisition scripts and source hashes support reconstruction from public inputs using the report's `--fetch` instructions. This audit checked the successful existing-input run; it did not test a fresh environment installation or repeat public downloads. Cross-platform bitwise equality is not asserted.

## Quantitative spot checks against substantive outputs

| Reported claim | Checked artifact | Finding |
|---|---|---|
| Fly eligible first/unique copying 40/64, 46/74, 42/67 | social_learning/summary.json and rates.csv | Matches; last-demo main score is 24/64 |
| Main exact two-sided binomial p=.05994 | summary.json known-answer enumeration | 0.05994118956699923; independent enumeration differs by 1.4e-17 |
| Main-minus-early contrast about .34 percentage points; date interval [-15.7,+15.1] | summary.json | Observed difference .33784 points; interval [-15.6603,+15.1123] |
| Archived regression n452, eligible n205, 247 ineligible zeros | independent audit_NOTEBOOK.md/audit_counts.json and followup_summary.json | Coherent with independent R-NA reconstruction; zero row mismatches reported |
| Constrained model best r=0, gain .506; relative likelihood .132 / .00411 | followup_summary.json weight_family | .5063522; .1323464 and .00410895 |
| Quadrature coefficient agreement within 5.2e-7; zero-variance control | followup_summary.json | Maximum 5.1152e-7; zero-SD nll error 2.84e-14 |
| Conditional ABB power 99.2% at fitted gain/N64; 47.1% at g=.2/N64, 85.6% at N200 | design_power.csv | .9917765, .4705998, .8556587 |
| Closed-loop observational path equality, rank2/4, error about1/q | exact_checks.json, summary.json, per_seed.csv | Path error0; rank2; 600 fits; verification B medians .44981/.045927/.004578 at q=.01/.1/1 |
| Anchored neural check reverses 3s comparison | causal_identification/neural_audit_check.csv | Population MSE .866193 vs diagonal .932043, 7.065% reduction; one animal only |
| Local Oja matched .742 to shifted -.248 versus full linear .917 | local_learning/outputs/summary.json | Matches v=4/rho=.8 medians; deliberately restricted constructed task |
| Equal-exposure curriculum .8405 vs .7102 under shortcut reversal | development/results/summary.json and analytic_audit.json | Matches; unique pooled optimum and analytic accuracy checks retained |

Minor floating arithmetic differences such as the causal likelihood spread of 4.55e-13 are consistent with the report's numerical-agreement wording; exact algebra supplies the law-equivalence argument. No substantive discrepancy between the checked reported values and current regenerated outputs was found.

## Strongest surviving objection

The empirical recommendation rests on one selected behavioral experiment with unknown final code/version and true block structure, post-exposure eligibility, imprecise group contrasts and a constrained likelihood family. A coding/denominator discrepancy in the deposited version does not prove the published model used that version, and similar copying proportions do not establish equivalence or no updating. The report states these limits and prioritizes auditing score/provenance/estimand before another experiment. This is the appropriate conditional recommendation.

For the causal direction, the counterexample deliberately makes feedback identical to observed state; independent excitation or known structure restores identification. It establishes a restricted possibility and a recovery regime, not universal impossibility. The report carries this qualification. Neither analytical agreement nor successful reproduction elevates either direction to a new biological mechanism.

The final briefing should preserve those distinctions, link the existing artifacts, and stop after root finalizes STATE/LEARNINGS. Remaining uncertainty is scientific and provenance-related, not a reason to extend the campaign indefinitely.

## Root closure after this audit

STATE.md and LEARNINGS.md were subsequently finalized and read in full by root. STATE now records eight pilots, both completed promoted follow-ups, successful full reproduction, no outstanding necessary computation, and conditional scientific uncertainties. LEARNINGS contains five dated project-specific entries in the requested Observation/Action/Confidence format. Root verified these files are nonempty, all17 execution return codes are zero, per-step stderr is empty, and all four reserved validation inputs remain absent. The latest regenerated social figure was visually inspected after correcting a clipped label. The two administrative completion actions identified above are therefore closed; no additional scientific claim is inferred from their closure.
