# Technical alternatives and recovery controls

2026-10-28. The count data do not support a substantial mixed OXT/AVP population replicated across donors. These controls strengthen that nomination decision while preserving uncertainty about the biological origin of very small secondary signals and the two stronger observations. They do **not** establish that all secondary transcripts are ambient, that either rare observation is a doublet, or that true low-level co-transcription is absent.

## Inputs and analysis scope

`inputs/selected_counts.npz` contains the acquired 23,512 × 36,924 sparse count subset, aligned with `selected_obs.csv` and `raw_var.csv`. It retains 309 candidate nuclei; 1,167 nuclei in C4-296/312/315; 10,334 nearby Mid-3 controls with the named peptide clusters excluded; 729 other Mid-3 peptide-labelled nuclei; 6,000 sampled broader neurons; and 4,973 sampled non-neuronal cells. Input provenance and hashes are owned by the acquisition manifest. This analysis uses raw matrix row sums and excludes OXT/AVP from non-peptide depth. All extracted counts are integer-valued. Both source studies are retained. Mitochondrial QC values were not pooled across studies because their original units differ.

Methods were specified in `IMPLEMENTATION.md` before this agent inspected joint abundance; subsequent changes and failures are documented there. The symmetric count-model refinement and additional moderate-noise diagnostics followed observation of the negative abundance result and are explicitly exploratory. The primary frozen abundance grid remains the decisive evidence. There are five adequately sampled donors, not 309 independent biological replicates.

## Empirical nuisance comparisons

For each target cell, each of three control pools was restricted to its donor and the 100 nearest observations by log non-peptide depth (all observations if fewer). The gene that is minor in that target determines which background gene is compared. Mean rates use count sums/exposure sums with a half-count pseudocount; upper 90th/99th percentile rates are deliberately permissive sensitivity scenarios. Negative-binomial dispersion comes from exposure-adjusted control residuals, bounded to shape .05–1,000. Poisson and NB tail probabilities are normalized for the observed minor<=major selection. These are illustrative nuisance distributions, not calibrated ambient contamination estimates or bounds.

Across the 309 candidate observations, **two** satisfy minor>=10 and minor/major>=.10. Under 1× mean matched-control rates, expected numbers satisfying that same rule are:

| Empirical pool | Poisson | Overdispersed NB |
|---|---:|---:|
| Nearby Mid-3 | 22.09 | 11.75 |
| Broader neurons | 1.47 | 2.15 |
| Non-neuronal | 0.020 | 1.02 |

The wide range is the important result. Nearby neuronal pools contain genuine peptide expression and cannot estimate ambient RNA cleanly; a Poisson model also badly understates heterogeneous background tails. Reasonable empirical nuisance choices span the two observed stronger cases. The complete 1/2/5/10/20× grid and every donor are in `outputs/technical/background_sensitivity.csv`; per-cell matches, depth distances, means, quantiles and tail probabilities are in `background_per_cell.csv`. These expected counts do not supply a probability that the cases are artifactual.

Both stronger cases are in **one library, znZv1_S1**. A post-outcome library-local comparison is particularly informative:

| Target OXT / AVP | Non-peptide depth | Near-Mid-3 expected AVP | Broad-neuron expected AVP | Non-neuronal expected AVP |
|---|---:|---:|---:|---:|
| 82 / 25 | 11,624 | 35.47 | 23.61 | 28.93 |
| 65 / 15 | 3,624 | 11.06 | 7.36 | 9.02 |

The library-local pools have 194, 129 and 29 controls respectively. For example, the 29 non-neuronal cells contain 86 AVP counts over 34,756 non-peptide counts. These pools provide a favorable case for residual background: the target AVP counts are on approximately the same scale as library-local control rates predict. They do not prove ambient origin; library-specific true expression, selection and cell-type composition remain confounded. Exact counts, exposures and OXT controls appear in `rare_cases_sample_background.csv`. No empty-droplet measurements are available here.

## Transparent count-model comparison and its limits

The primary auxiliary model conditions on the observed major count M and gene orientation. It models minor m as a negative binomial truncated to 0<=m<=M. Its trace mean is `alpha × q(source,gene) × B + beta_trace × M`, with beta_trace constrained 0–.01. The alternative adds a mixture component with mean ratio .10–1. Both share dispersion and background parameters. Weak priors regularize background multiplier toward 1, dispersion toward the control estimate and mixed prevalence toward small values. Training controls determine source-specific background rates; held-out donor target counts do not enter fitting. Each of the five useful donors is held out in turn. A fixed-AVP analysis restricted to OXT-dominant cells uses the same truncation and gives the same qualitative result.

With the nearby control pool, held-out mixed-minus-trace log scores are:

| Held-out donor | Difference |
|---|---:|
| 3u5kk | +4.80 |
| H18.30.002 | +13.57 |
| H19.30.001 | +5.82 |
| H19.30.002 | −17.55 |
| znZv1 | +96.95 |

This is **not** a replicated substantial-mixing result. The two stronger znZv1 cells contribute +48.07 of its improvement; six additional znZv1 observations with only 5–8 minor counts contribute +46.02. The alternative can help fit a library-specific trace-count tail. Across other background pools, some donor signs reverse. A fitted mixture component is not a biological cell population, and these conditional models do not estimate the joint generative process or uniquely identify artifacts.

The decisive model validation is mixed:

- With very large nearby-control overdispersion, the complete held-out pipeline **fails to discriminate** null and injected mixed populations reliably. The null_control and all mixed simulation generators use NB shape **0.1409951190**; the separate null_overdispersed generator uses shape **0.5**. These generator parameters differ from the training-fold control reference shapes (0.076507–0.101999), which enter weak regularization; fitted real-data shapes are 0.511987–1.385988 for the trace model and 1.586494–2.127479 for the mixed model. Across ten replicates per simulation condition, pooled mixed-minus-trace score ranges overlap; injected 50% prevalence at .25 mean ratio is not reliably recovered. This is a failed positive control for interpreting this model under such broad noise, not evidence against the injected effect.
- Outcome-informed diagnostics with moderate shape10 and non-neuronal background rates succeed: the pooled score is negative in all ten null replicates; positive in 9/10 for 30% mixing at ratio .25; and positive in all ten for 50% mixing at ratio .50 and for 100% mixing at ratio .25. Median held-out donor counts favoring the alternative are 1, 4, 4.5 and 5 respectively.

Thus the model has discriminatory ability in specified lower-noise regimes, but plausible broad nuisance assumptions destroy it. Its fit is **inconclusive auxiliary evidence** and is not used to certify the negative biological claim. `model_heldout_scores.csv`, `model_parameters.csv`, `model_per_cell_scores.csv`, `model_simulation_scores.csv`, `model_simulation_thresholds.csv` and `model_moderate_noise_diagnostics.csv` preserve all results. Ten simulations per scenario describe behavior; they are not precise power estimates.

The original fixed-AVP sensitivity omitted truncation despite selecting OXT>=AVP. Independent review caught this error. Original files with `initial_invalid_sensitivity` suffix are retained solely as a failure record. Both fitting and scoring were corrected, rerun, and all reported sensitivity values use the corrected conditional model. The primary symmetric model always used truncation.

## Direct count recovery and false positives

An independent count-space control adds Poisson minor counts with mean equal to 10%, 25% or 50% of each actual dominant count, preserving its actual original minority signal. It then recomputes major/minor orientation and applies the exact frozen primary rule. All cells in each useful donor, including four peptide-zero znZv1 observations, remain in the denominator. There are 200 simulated draws for each donor/signal level. This is an additive assay-space detectability control, not a reconstruction of biological mRNA synthesis or dropout.

| Donor | Mean detection at added ratio .10 | .25 | .50 |
|---|---:|---:|---:|
| 3u5kk | 32.1% | 77.6% | 89.7% |
| H18.30.002 | 38.3% | 72.7% | 84.8% |
| H19.30.001 | 53.8% | 89.6% | 92.7% |
| H19.30.002 | 60.7% | 95.7% | 98.6% |
| znZv1 | 12.4% | 31.2% | 49.6% |

This confirms that the analysis would detect a common moderately balanced state in the better sampled count distributions. It also exposes a real limitation: the low OXT-count znZv1 donor has much lower threshold sensitivity, especially near the .10 boundary. Negative primary counts cannot exclude arbitrarily weak or rare true mixing. Complete simulated fractions and denominators are in `direct_injection_recovery.csv`.

A separate null removes minor expression and adds a constant Poisson background with mean .5/1/2/5 counts per cell, keeping observed major counts. At mean1, the average of the five donor co-detection fractions is 62.34%, while no substantial case appears in 500 simulations. At mean2 it is 85.22%, with mean primary false-positive fraction .0042%. These constructed nulls demonstrate at the **observed dominant-count scale** how widespread binary overlap can coexist with essentially no substantial abundance. They are not measured ambient rates. Results are in `trace_null_controls.csv`.

## Doublet sensitivity and the rare cases

From the four prespecified peptide populations, pure-parent candidates required dominant>=10 and minor/major<=.01. Every useful donor has both OXT- and AVP-dominant parents; the singleton tzan2 lacks an eligible OXT parent and is explicitly omitted from this simulation. Same-donor parents were combined at 25/50/75% transcript contributions, normalized to actual target-cell total depths and Poisson-resampled as full sparse gene profiles (500 mixtures per donor/weight). Actual summed parent libraries were also evaluated separately.

At target depths, 52–82% of simulated opposite-program doublets satisfy the primary rule in the four more informative donors; znZv1 yields 23–35%. Undiluted summed parents qualify 73–90%. This both supplies a realistic positive control and shows that a doublet can create substantial abundance. It does not estimate an actual doublet rate or identify the rare cases, and it does not cover homotypic doublets or all biological mixtures.

The rare cases have 4,179 and 2,118 detected non-peptide genes. Against the 100 closest-depth nearby Mid-3 cells in znZv1, these are the 45th and 33rd empirical percentiles. They are not obvious complexity outliers in that matched context. Other pools, especially glia, give different percentiles; the full table preserves those differences. The first case appears high compared with all other candidate cells because it has greater depth, illustrating why unadjusted feature count is misleading. Gross QC cannot settle their identity. See `synthetic_doublet_summary.csv`, `synthetic_doublet_examples.csv` and `rare_case_complexity.csv`.

## Judgment and reproduction

The serious remaining objection is real but narrow: a rare, library-local or low-level biological co-transcription state could exist, and this dataset cannot disentangle it from residual background and doublets. That uncertainty does not restore the missing multicohort substantial abundance. The campaign should deprioritize C4-313 as a widespread substantial mixed-program candidate. If future work targets the rare znZv1_S1 pattern specifically, a discriminating measurement is same-cell quantitative OXT/AVP in situ with cell boundaries and background controls, sampling multiple donors and matched peptide-dominant controls. Multicell spatial spots are insufficient.

From repo root:

```sh
.venv/bin/python campaigns/hypomap_quantitative_2026-10-28/experiments/technical/run.py --stage all --reps 10
.venv/bin/python campaigns/hypomap_quantitative_2026-10-28/experiments/technical/extra_controls.py
```

Root `.venv`: Python3.9.6, NumPy2.0.2, SciPy1.13.1, pandas2.3.3. Seeds derive from28102026 and are explicit in scripts. Final stage stderr files are empty. The initial pandas Series.T indexing failure and corrected rerun are preserved. No new source downloads, private data, external messages or paid resources were used by this worker.
