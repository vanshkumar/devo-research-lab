# Quantitative subset acquisition and measurement provenance

2026-10-28. Acquisition owner: native `acquire` subagent. Root owns inference. Original historical campaign files were read but never changed. No joint OXT/AVP count outcomes were inspected before root announced `PROTOCOL.md` frozen. This acquisition agent inspected metadata, sparse structure and then stored-count integrity/normalization, leaving biological joint-abundance analysis to root.

## Source and preserved bytes

Public CELLxGENE HYPOMAP collection `d0941303-7ce3-4422-9249-cf31eb98c480`, collection version `4cd099c6-014b-4032-a30b-a26ae8b74905`, dataset `a2c833f7-b7f1-4f4d-ad31-cae478b601b7`, dataset version `af06d70d-a2bc-43c1-8378-bc545bc8ee2c`. Asset: https://datasets.cellxgene.cziscience.com/af06d70d-a2bc-43c1-8378-bc545bc8ee2c.h5ad . The collection identifiers inherit the reviewed manifest; the actual asset bytes/version headers were checked anew.

`inputs/acquisition_manifest.json` indexes 3,126 verified cached HTTP206 ranges totaling **3,277,786,552 downloaded HDF5 bytes**. The whole asset is 5,231,283,640 bytes; it was **not** downloaded completely, and no whole-file SHA256 is claimed. Each range has its own original response headers, inclusive offsets and SHA256 in `inputs/range_cache/*.json`; corresponding `.bin` files are unchanged server bytes. All successful responses report the same ETag `"82e4ce858a83a561008d9a1baa8ddf74-624"` and S3 version `UEApVhO1WbRsSgPruR0.jWedaV7W4ppN`, matching the review. The 272,352 preserved review bytes in all nine old ranges were independently compared with the newly obtained overlapping bytes and agree exactly. `logs/acquire_ranges.jsonl` retains every successful response and four initial DNS failures.

Before acquisition, root observed 614GiB free disk; its sandbox memory query failed. Sparse row streaming was used throughout, never a dense whole-atlas load. An initial optional `get_storage_size()` inspection unexpectedly traversed distributed HDF5 chunk metadata and fetched unnecessary ranges. It was interrupted and removed; all bytes remain included in the total above. The metadata-stage cache, including that failed efficiency experiment, was 1,020,202,424 bytes. This is an acquisition overhead, not hidden biological data selection. Remaining extraction reused the cache.

## Identity reconciliation and subset contract

The HDF5 contains 433,369 observations with unique barcode index, 36,924 genes and 1,150,647,101 sparse nonzero positions in both X and raw/X. X and raw/X are separate CSR objects. `inputs/obs.csv` exports all 31 observation fields plus source `row_index`; `inputs/var.csv` and `raw_var.csv` preserve feature metadata and source `column_index`. No global `is_primary_data` filter was applied.

C4-313 remains exactly 309 observations, named `C4-313 Mid-3 GLU-4 OXT`, C3-112. Donor counts are 74 `siletti_H18.30.002`, 69 `znZv1`, 66 `siletti_H19.30.001`, 53 `3u5kk`, 46 `siletti_H19.30.002`, and 1 `tzan2`. Siletti contributes186 and has `is_primary_data=False`; Tadross contributes123 and has True. The three prespecified comparison sizes also match the pinned table: C4-296200, C4-312687, C4-315280. Matching names/counts does not prove old barcode identity: the old inputs are aggregate tables without barcode lists. Current452 non-null C4 labels include inherited non-neuronal labels; see the independent source review for neuronal415 reconciliation.

OXT uniquely maps to `ENSG00000101405`, zero-based column20708; AVP to `ENSG00000101200`, column20709. Gene ordering is `raw_var.csv` order, never guessed from symbols.

The metadata-only implementation clarification agreed with root before count inspection was to retain all12,539 Mid-3 cells, and sample broad backgrounds in the six target donors. Library-depth deciles are computed within each donor across its entire atlas using metadata `nCount_RNA`; ties are deterministically ordered by original source row. Seed28102026 samples at most100 per donor/decile/pool, excluding all Mid-3 cells from the broad-neuronal pool to avoid overlap, all OXT/AVP-named groups and the four prespecified peptide groups. Non-neuronal controls use C0 other than `C0-3 Neuron`. The nearby pool contains all other Mid-3 cells excluding those peptide groups. Sampling is described by `inputs/selection_manifest.json`, and row-specific `pool_sampling_probability` is exported.

- `peptide_counts.npz` and `peptide_obs.csv`: all1,476 candidate/comparison rows, 6,799,442 nonzeros.
- `selected_counts.npz` and `selected_obs.csv`: all23,512 selected rows, 85,585,956 nonzeros. Pools: candidate309, peptide_comparison1167, near_mid310334, other_mid3_peptide729, broad_neuronal6000, non_neuronal4973.
- Rows are in ascending source `row_index` order. Feature order is all36,924 rows of `raw_var.csv`.
- Obs exports add `raw_total` (actual selected raw/X row sum) and `raw_nfeature` (actual nonzero count), retaining original metadata values separately.
- `*_extraction_manifest.json` protects subset bytes, sizes and SHA256. Separate verification confirmed the1,476 peptide rows are exactly identical inside the23,512-row export, unique barcodes, canonical sparse structure, and exact agreement of stored actual totals/feature counts with the matrices. This consistency check is not independent biological validation.

## What the numbers measure

All85,585,956 extracted nonzero values are positive, finite and integer-valued float32 (minimum1, maximum17,576; zero noninteger values). No rounding was applied. This establishes the stored count scale; it does **not** establish acquisition-raw provenance. The source-code investigation in `experiments/provenance_review` distinguishes Tadross CellBender correction from imported Siletti processing and the incomplete curation chain.

Actual raw/X sums are smaller than metadata nCount_RNA in every peptide row. Median deficits are1,135 counts/5.23% for Siletti and403/4.34% for Tadross; peptide relative deficits range2.4–8.05%. Across all selected cells the maximum absolute deficit is16,260 counts and2,399 features. The protocol uses actual raw_total for new compositional estimates and retains metadata depth for sensitivity.

A diagnostic requested after discovering this mismatch read normalizedX for the first three source-order peptide cells from each study. `inputs/normalization_check.csv` and `normalization_check_vectors.npz` preserve the exact six rows/vectors. For all six, X agrees with `log1p(10000*raw/nCount_RNA)` to maximum absolute error1.14e-7–2.38e-7; use of actual raw_total instead gives0.0442–0.0553 discrepancy. Their X/raw nonzero indices agree. This supports a larger preexisting feature universe for metadata normalization and a later restricted feature export; it does not identify removed genes or prove the exact curation sequence.

The source reviewer identified incompatible percent_mt units in source merge code. Exported percent_mt is preserved as supplied. Recompute mitochondrial fractions from available MT- genes and actual totals for cross-source analysis; do not pool these metadata values as if units were verified identical. Such recomputation remains conditional on the exported feature universe.

## Reproduction and environment

From repository root, in order:

```sh
campaigns/hypomap_quantitative_2026-10-28/.venv/bin/python campaigns/hypomap_quantitative_2026-10-28/experiments/acquire.py metadata
campaigns/hypomap_quantitative_2026-10-28/.venv/bin/python campaigns/hypomap_quantitative_2026-10-28/experiments/acquire.py select
campaigns/hypomap_quantitative_2026-10-28/.venv/bin/python campaigns/hypomap_quantitative_2026-10-28/experiments/acquire.py peptide
campaigns/hypomap_quantitative_2026-10-28/.venv/bin/python campaigns/hypomap_quantitative_2026-10-28/experiments/acquire.py selected
campaigns/hypomap_quantitative_2026-10-28/.venv/bin/python campaigns/hypomap_quantitative_2026-10-28/experiments/acquire.py normalization_check
campaigns/hypomap_quantitative_2026-10-28/.venv/bin/python campaigns/hypomap_quantitative_2026-10-28/experiments/acquire_verify.py
```

Valid existing ranges are hash-checked and reused. Acquisition reads the public URL only when a needed cached block is absent. Metadata and selection reruns regenerate exports; count extraction restores added raw_total/raw_nfeature fields. Use finalized files directly for ordinary analyses.

Isolated campaign environment: Python3.9.6, NumPy2.0.2, SciPy1.13.1, pandas2.3.3, h5py3.14.0/HDF51.14.6, requests2.32.5. Initial pip and acquisition failed sandbox DNS; ordinary package installation and public reads succeeded through approved escalation. No credentials, accounts, paid resources or controlled data were used. urllib3 emits a LibreSSL compatibility warning; HTTPS requests succeeded with certificates verified and every content range/size/hash checked. No numerical matrix warnings occurred during acquisition. The normalization diagnostic initially failed only while JSON-printing NumPy int64 values after saving results; dtype-safe serialization fixed it and a cache-only rerun succeeded. The original failing stderr is retained separately.
