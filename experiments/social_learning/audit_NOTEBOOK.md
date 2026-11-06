# Independent audit of social-learning data and archived code

Completed 2026-10-28 by local_learning agent. Bounded read-only analysis of public artifacts, with new audit outputs only. The original Rmd was **not executed**. This audit does not fit or reproduce the mixed model; root's follow-up has that responsibility.

## Inputs and independence

Read data/social_learning/data_primacy.csv and primacy_bias_script.Rmd directly. The audit reconstruction imports neither run.py nor its outputs. It uses Python standard-library csv, exact integer binomial enumeration and explicit R three-valued logic. Independent source check: [Santiago Araújo et al. (2024)](https://pmc.ncbi.nlm.nih.gov/articles/PMC11295924/), §§2.4–3. The paper defines copying of the last/unique demonstration, eligibility after copulation following both males' courtship, and reports group n of 64/74/67. Its statistical section describes experimental blocks, whereas the shipped CSV contains date/device without an explicit simultaneous-block column.

File SHA256:

- CSV: `0f723df5825865d214e3064c1e16f0e489211f25e45f3eb34e7dfb5c4ebf568b`. Matches the saved Dryad version 296766 file metadata independently inspected in data/social_learning/dryad_files.json.
- Rmd: `25e478b8f018da79edf5ab32b2b685d2b097949fed71c737aa85b0a98dd029a8`. Provenance from saved manifest: publisher Figshare file 46746186. This audit does not establish that this exact file was the analysis used for the published numbers; resolving code-version history is a material limitation.

Reproduce from repo root:

```sh
.venv/bin/python experiments/social_learning/audit_reconstruct.py
```

## Independently reconstructed counts

| Group | All trials | Paper-eligible n | First/unique copies | Last/unique copies | Exact two-sided p against 1/2 |
|---|---:|---:|---:|---:|---:|
| T | 142 | 64 | 40 | 24 | 0.05994118957 |
| C1 | 168 | 74 | 46 | 46 | 0.04739297550 |
| C2 | 152 | 67 | 42 | 42 | 0.04980011429 |

Eligibility totals 205/462 and the binomial p-values reproduce the reported rounded values. Main treatment two-sided p is unchanged when first and second scores are complemented; correct p alone cannot validate orientation of the response. The observed first preference is 40/64 = 0.625. This audit confirms that behavioral tendency; it does not independently establish learning mechanism, imprinting or cross-species generality.

## Exact archived-code discrepancy

The line references below use `nl -ba data/social_learning/primacy_bias_script.Rmd` and the hash above.

1. Lines 138–139 and 154–155 define double-courtship copying. If the double-courtship indicator is false, their `ifelse` returns zero even if the equality is missing: in R, `FALSE & NA` is false. If both courtships occur but mating is absent, equality remains NA and that score is NA.
2. Lines 160–171 choose first-demonstration copying for T and C1, second/unique copying for C2. The main treatment is therefore complemented relative to the paper's last-demo outcome.
3. The per-group descriptive loop **does** filter for both courtship and mating: lines 263–285. However, `select_bar = c(1,1,2)` at line 269 also chooses first-demo main copying for its bar. This differs from the published last-demo definition.
4. `data_sub <- data` at line 243 retains all 462 rows. Lines 348–350 pass that unfiltered object to the treatment GLMM, with `copy_dc_bin` as response and date as a random intercept. The loop mutates `data_sub2`, not `data_sub`; there is no subsequent eligibility filter or score complement before the model.

Literal reconstruction of the model's nonmissing responses:

| Group | Archived response n | Archived successes | Noneligible rows included as zero |
|---|---:|---:|---:|
| T | 140 | 40 | 76 |
| C1 | 164 | 46 | 90 |
| C2 | 148 | 42 | 81 |
| Total | 452 | 128 | 247 |

Ten double-courtship trials lacking a mating remain NA; they would be omitted by ordinary complete-response model handling. Every row of the supplied `copy_dc_bin`, including NA status, matches this literal reconstruction: **zero mismatches** across all 462 rows. Thus the stored annotation cannot be substituted for the paper-defined outcome without checking inclusion and orientation.

## Verdict and surviving uncertainty

**Confirmed archival reproducibility discrepancy.** The supplied Rmd would analyze a different response and denominator from the paper's stated main comparison. The raw eligible counts and binomial results nevertheless reproduce the paper. It is unwarranted to infer that the published conclusion is false, that the published GLMM used this exact archived code, or that a corrected model must have a particular p-value. A later/unarchived script, manual subset or change of outcome coding could explain the mismatch. Date is also not a verified reconstruction of simultaneous experimental blocks.

Recommended bounded next action: root should compare explicit outcome/inclusion variants under the same model and quadrature settings, while labeling date-cluster models as sensitivity analyses. An exact reproduction of published mixed-model values requires the final analysis version and block IDs. This audit's output can justify reviewing provenance, not accusing an error in the scientific record.

Artifacts: audit_counts.json preserves counts/hash, audit_row_reconstruction.csv preserves row-level inclusion and both outcome conventions, audit_run.log contains the actual printed output, and audit_reconstruct.py is the independent implementation.
