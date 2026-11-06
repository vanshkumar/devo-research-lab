# Adversarial numerical and scientific audit

2026-10-28. Verdict: **the observed-count result and decision not to nominate C4-313 pass independent reproduction. A claim that biological co-transcription is absent, or that contamination has been identified as its cause, would fail this audit.** No unresolved numerical blocker to the narrower decision was found.

The reviewer had already seen the principal outcomes and contributed the separate provenance review; this is an independent implementation and adversarial assessment, not blinded review or independent biological replication. Files in this directory are the reviewer's own outputs. No acquisition or analysis functions were imported.

## Original-byte reproduction

`audit.py` implements a read-only, offline byte stream over the original public HDF5 cache. A missing range fails without any network request. Each accessed range is rehashed against its saved SHA256 and checked for its offset, size, URL, HTTP206 status and Content-Range; all accessed responses have one ETag and S3 version ID. HDF5 metadata selects the candidate rows directly from `obs/C4_named`, identifies the unique OXT and AVP columns in `raw/var`, and reads each candidate's original CSR pointer interval, indices and values. Python integer sums and rational threshold comparisons are separate from the sparse-matrix/float-ratio analysis implementation. Every row is checked for finite, nonnegative integer values and duplicate feature indices. Barcode/donor/source/sample identity is read directly from HDF5.

- Original source: https://datasets.cellxgene.cziscience.com/af06d70d-a2bc-43c1-8378-bc545bc8ee2c.h5ad (5,231,283,640 bytes).
- Verified 311 accessed ranges, totaling 326,045,112 distinct cached bytes; `accessed_byte_manifest.json` preserves every SHA256 and response version. This is not a full-file digest or a new authentication of the original HTTP responses.
- OXT: column20708, ENSG00000101405; AVP: column20709, ENSG00000101200. Original shape433369×36924. Per-row decompressed CSR index/data hashes are in `independent_candidate_counts.csv`.
- All309 candidate row IDs, barcodes, donor IDs, source labels, sample IDs, gene counts, actual row sums and feature counts match the abundance output. All1,512 donor/threshold-grid entries match exact rational arithmetic. No boundary-classification discrepancy was found. The exact median ratio .003300330033 differs from the float32 display only at rounding precision.

| Source / donor | N | Joint positive | Primary substantial | Median minor | Median major |
|---|---:|---:|---:|---:|---:|
| Tadross / tzan2 | 1 | 1 | 0 | 1 | 2 |
| Tadross / znZv1 | 69 | 24 | 2 | 0 | 17 |
| Tadross / 3u5kk | 53 | 23 | 0 | 0 | 77 |
| Siletti / H19.30.002 | 46 | 38 | 0 | 2 | 240 |
| Siletti / H18.30.002 | 74 | 56 | 0 | 1 | 87.5 |
| Siletti / H19.30.001 | 66 | 62 | 0 | 3 | 1769 |

Overall:303 OXT-positive,205 AVP-positive,204 joint; median minor1,280/309 minor≤5. Primary substantial requires minor≥10 and minor/major≥.1:2/309; the additional minor/actual-total≥.001 condition retains both, while minor≥20 retains one. Both are in **znZv1_S1**:

| Original row / barcode | OXT | AVP | Actual total | Actual features |
|---|---:|---:|---:|---:|
| 260474 / znZv1_S1_GTTAGTGCACATATGC-1 | 82 | 25 | 11731 | 4181 |
| 261693 / znZv1_S1_GATGCTATCGTAGAGG-1 | 65 | 15 | 3704 | 2120 |

No donor meets the frozen ≥10 cells and ≥20% criterion, before any artifact model is invoked. There are zero qualifying Siletti nuclei out of186. Those are descriptions of the measured, selected nuclei, not population prevalence estimates.

## Strongest challenge: false negatives at low peptide counts

The operational criterion deliberately asks for substantial *observed* counts. It is not calibrated to a fixed latent transcription ratio across donors. In znZv1,22/69 nuclei have measured major<10 and64/69 have major<100. A minor-only injection at a fixed major<10 cannot satisfy both genes≥10 at any minor abundance.

`sensitivity_review.py` independently calculates exact Poisson-addition probabilities from the independently extracted counts, including the possibility that the injected secondary becomes the new major. It uses all nuclei, including peptide zeros, and compares its expectation with the technical agent's200-replicate simulation. Across15 donor/ratio conditions, the largest deviation is2.325 Monte Carlo standard errors. This supports the implementation of that specific detectability control.

| Added Poisson mean / measured major | znZv1 expected recovery | Other four useful donors: range |
|---|---:|---:|
| .10 | 12.81% | 32.44–60.63% |
| .25 | 31.26% | 72.84–95.72% |
| .50 | 49.83% | 84.72–98.67% |

These are assay-scale injections on the observed baseline, not estimates of biological sensitivity. At a true mean ratio exactly on the .10 boundary, even deep Poisson observations pass the ratio cutoff only roughly half the time. Requiring20% observed positives therefore does not provide80% or95% power for20% latent mixture prevalence. For example, under a deliberately idealized zero-minor baseline,20% independently mixed znZv1 cells with Poisson mean ratio.25 would yield only3.51 expected observed positives; the donor requires14. `analytic_injection_recovery.csv` makes the assumptions explicit and gives the Poisson-binomial count-criterion probabilities. This invalidates an absence inference, while leaving failure of the prespecified nomination rule intact.

A post-outcome descriptive check limits the scope of the low-count objection: among cells with measured major≥100, there are25 Tadross and122 Siletti observations, median minor1 and3 respectively, and zero primary substantial observations. This supports the description of a predominantly small secondary signal in the exported matrix. It is a selected high-count sensitivity, not a new replication or latent-expression test.

## Technical alternatives: what they establish

The code was reviewed for outcome selection, conditioning, training/test separation, threshold handling and simulation denominators. Model rates use training donors' controls; the held-out donor's candidate outcomes are not used for fitting. Source-specific rates still come from the same atlas, with few donors, and depend strongly on the chosen control population. Matching nearby controls or their upper tails does not establish ambient RNA: these controls can express the peptides genuinely.

The main conditional mixture does improve held-out likelihood. For the nearby-control model, its total gain is103.59 log units, of which96.95 comes from znZv1;48.88 of that donor's gain is contributed by observations with minor<10 and48.07 by the two primary cases. Excluding znZv1, gains across the three control pools are6.64,−2.42 and13.29. Thus neither 'the null model wins' nor 'the improvement proves a reproducible substantial mixed state' is justified. A regularized component with a mean ratio≥.1 and a highly dispersed distribution is not the same object as an observed substantial class or a biological cell type.

The empirical-dispersion simulations are an important failed validation, preserved in `technical_audit_result.json`: the empirical-control generator uses NB shape.140995 (the additional null sensitivity uses.5), and even injected30–50% mixed components are not reliably distinguished. Positive versus negative score alone is especially uninformative:7/10 basic-null simulations have positive total gain, but the median gain is only.00020. With10 replicates, no reliable false-positive probability or power estimate is available. The large real-data gain exposes a limitation of that background model, but the failed positive controls prevent interpreting it as biological mixture evidence. Final moderate-noise diagnostics with shape10 favor the alternative in0/10 null,9/10 ratio.25/prevalence.30, and10/10 of the two stronger-effect simulations. These outcome-informed diagnostics apply to easier scenarios and cannot validate the real nuisance model retroactively. Their non-neuronal generation rates differ from the nearby-control fitting rates; this is a behavior check, not a calibrated model-selection test.

Same-sample controls for the two retained observations can predict secondary-count means in the observed range, so contamination remains a viable sensitivity scenario. Those controls contain real cell expression and were inspected after seeing the rare cases; they cannot label either nucleus as contaminated. Synthetic opposite-program doublets frequently produce substantial counts at the observed depths (for znZv1,23.4–35.0% of depth-matched mixtures;84.4–90.0% of summed parents). This demonstrates technical compatibility, not the frequency of such doublets in the target. The two real cells do not both show exceptional non-peptide complexity against depth-matched nearby neurons (45th and33rd percentiles); complexity neither proves nor excludes doublets. No exported doublet/contamination score is available.

One material review finding was corrected by the technical owner: the initial fixed-AVP sensitivity selected AVP≤OXT but omitted the selection's truncation. It is now fitted and scored with the appropriate CDF normalization; original invalid-sensitivity outputs are retained and excluded from inference. The main symmetric model always used truncation. Documentation was also reconciled with its actual mixed-ratio parameter bound [.1,1]. These corrections do not affect the primary abundance results. Direct-injection denominators were corrected to retain peptide-zero cells; this audit compares the explicit recorded denominator, not the smaller conditional-model denominator.

## Signature, uncertainty and provenance limits

The conditional non-peptide signature branch is ineligible. Independently reconstructed labels give two positives in one donor. Holding znZv1 out leaves239 adequately sampled training nuclei with zero positives; all other useful held-out donors have zero positive test labels. Candidate-only, donor-held-out ROC evaluation cannot answer the intended reproducibility question. `signature_eligibility.csv` records each fold. A classifier would add no valid positive-class replication.

The binary cell-bootstrap implementation is mathematically equivalent to resampling observed binary labels. A zero-positive donor therefore has an interval[0,0]; that is a property of the empirical bootstrap, **not a zero prevalence bound**. As an illustration only, independent Bernoulli sampling with perfect detection would instead give one-sided95% zero-case upper limits about4.0–6.3% for the individual useful zero-positive donors. Neither calculation handles donor heterogeneity, technical detection or selection, and pooling186 Siletti nuclei cannot create a human-population interval. No population absence statement should be made.

All309 raw totals are below metadata nCount_RNA (maximum deficit6581), and all raw feature counts are lower (maximum candidate deficit1281). Direct mitochondrial sums reproduce the study-specific metadata unit mismatch: percent for Tadross, fraction for Siletti. The six-row normalization audit additionally finds X≈log1p(raw×10000/metadata_nCount), not normalization by the exported raw row total. Together these support a larger pre-export feature universe and row alignment; exact feature-removal and correction provenance remain unresolved. Source code documents Tadross CellBender processing but does not prove identical correction for Siletti, or supply a bytewise export chain. Integer raw.X is therefore called stored unnormalized counts, not acquisition-raw molecules.

Current415 neuronal C4 groups match the old source table's labels and sizes, but publication413/165815 cross-species scope and historical barcode identity remain unresolved. This audit uses the explicit version and directly selected309 current C4-313 rows. It does not generalize to all hypothalamic OXT/AVP populations or replace existing C4-296 work.

## Reproduction and disposition

Run from the repository root after the acquisition cache and technical outputs exist:

```sh
campaigns/hypomap_quantitative_2026-10-28/.venv/bin/python campaigns/hypomap_quantitative_2026-10-28/experiments/adversarial/audit.py
campaigns/hypomap_quantitative_2026-10-28/.venv/bin/python campaigns/hypomap_quantitative_2026-10-28/experiments/adversarial/sensitivity_review.py
```

`audit_result.json` contains the extraction, identity, exact-grid and eligibility results with input hashes; `technical_audit_result.json` records analytical recovery, technical comparisons and hashes. Standard output/error records are retained. Both scripts write only this review directory and make no network calls.

**Disposition:** use the narrow conclusion that this selected C4-313 export is dominated by tiny secondary counts and does not warrant nomination as a reproducible substantially mixed population under the frozen criteria. Retain low-level biological transcription versus ambient/technical signal as unresolved, including the poor minor-count sensitivity of znZv1. No further classifier is warranted. The numerical audit is complete; causal attribution, latent absence and broad human-population inference are outside what these data identify.
