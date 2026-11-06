# Independent audit of the promoted HYPOMAP result

2026-10-28. Verdict: **the conditional pooled co-detection and donor-capacity bounds pass independent reconstruction; no numerical blocking defect found.** They cannot establish authentic dual-peptide neurons, a social function, human specificity, or a quantitative ambient-RNA/doublet-rate threshold.

## Independent evidence, not model agreement

`audit.py` imports neither atlas/run.py nor atlas/followup.py or their result tables. It reads the original pinned marker, annotation and sample TSVs with standard-library csv. Every original used file is checked against its recorded SHA256 and Git blob at commit `29599fcb13a74a908c986ad69d68fc3e4a3cf6d0`. Integer counts are enumerated using Decimal rounding, independently of the main follow-up's ceil/floor formulas and MILP. Complete binary-set enumeration verifies139 small known-answer marginal cases. Explicit category allocations demonstrate attainability rather than trusting solver success. `audit_result.json` and `donor_zero_witnesses.csv` contain the actual outputs.

## Key result reconstructed directly

C4-313 is named `C4-313 Mid-3 GLU-4 OXT`; annotation N=309. Both marker rows use `comparison=All` and the same C4 identifier. Reported detection fractions are OXT .981 and AVP .663.

| Quantity | Independently recovered value |
|---|---:|
| Feasible OXT-positive count under nearest three-decimal rounding |303 only|
| Feasible AVP-positive count |205 only|
| Minimum overlap |303+205−309=199|
| Maximum overlap |205|
| Observed overlap fraction lower bound |199/309=.6440129|
| Largest donor capacity |74|
| Minimum overlap outside largest donor |199−74=125|
| Two largest donor capacities combined |143|
| Three largest combined |209|
| Minimum number of donors containing some joint detections |3|

Nonzero donor capacities are: `siletti_H18.30.002`74, `znZv1`69, `siletti_H19.30.001`66, `3u5kk`53, `siletti_H19.30.002`46, `tzan2`1. Their sum is309. Other five listed donors contribute0 to this cluster. No donor's identity is assumed to be interchangeable with a sample or an independent population estimate.

For **every specified donor**, its unavoidable overlap lower bound is0: `max(0,199−(309−donor_capacity))=0`. The audit constructs a separate feasible allocation with zero overlap in each chosen donor. These zeros are **not simultaneous**: at least199 joint observations must exist overall in at least3 donors, but marginals alone do not identify which3. A claim that each named donor is confirmed to coexpress would be wrong.

Other reconstructed lower counts are C4-296:86/200; C4-312:258/687; C4-315:138/280. The main outputs agree. Exact half-even rounding, conservative inclusive half-unit buckets, and doubled rounding envelopes preserve the C4-313 gene/donor integers. No half-tie ambiguity affects its result. The bounds are not statistical confidence intervals; they are finite-data constraints under the specified universe and measurement definitions.

## Crucial same-universe assumption

The pinned author code supports a pooled same-cluster interpretation:

- `supplementary_tables.R`15 loads the publication Seurat object;173–178 counts nuclei by cluster from its metadata. Lines183–188 calculate donor percentages as `cells_cluster_target/ncells*100`, rounded to2 decimals. Lines114–120 export significant/specific marker rows without recomputing their detection fraction.
- `12_markers_mrtree.R`40 loads the Seurat object and85 the tree label matrix. At138 onward it sends that object and labels into `findMarkers_tree2`. The30,000-cell draw at116–124 selects **features to test**, not the denominator of a reported gene percentage.
- Two extra helper sources were retrieved from the **same pinned commit** solely to close this definition check. They are saved under this audit folder without modifying the atlas agent's files. `harmonization_functions.R`512–600 sets identities to the tree's cluster level and calls `FindMarkers2.Seurat` for the current node. It does not define a donor-averaged percentage.
- `stratified_wilcoxon_functions.R`284–287 defines pct.1 as the rounded fraction of the cluster's cells whose RNA/data assay value exceeds0. The numerator is not divided by gene-positive cells or averaged across donors. The optional DE sample cap is applied later at347–355, after percentages are computed. Thus its20,000-cell cap does not provide a hidden309-cell downsampling issue here.

This establishes what the code **would mean**, not that every deposited TXT was actually generated from an identical immutable RDS or identical cell barcodes. The two publication-table inputs are loaded as separate files, the annotated comparisons' complete execution history is unavailable, and raw barcode membership was not acquired. The safe result remains conditional on the snapshot annotation and marker percentages referring to the same309 observations. Their shared identifier and exactly feasible integer counts support that premise but do not prove it independently at cell level.

The helper code also assumes label-matrix rows align with metadata when column-binding new identities. This audit did not obtain those objects and cannot check that alignment. There is no evidence here that it failed; it is an execution-provenance limitation, not a demonstrated defect.

## Version and mapping limits

The main analysis explicitly uses the pinned repository's415-C4 snapshot rather than silently equating it with the paper's413-C4 description. The199/309 bound should be attributed to that snapshot. Any claim about final publication-cell assignments or a later mapping requires checking the relevant release, not reusing these exact counts unquestioningly. A1:1 retained mouse correspondence is a cluster-matching graph property, not confirmation that mouse cells co-detect Oxt/Avp or implement the same social algorithm. The overlap calculation itself does not need the mouse mapping.

Filtered marker exports cannot support absence claims for missing genes. Source `p_val_adj<.0001`/specificity filters act after percentage construction; absent AVPR1A rows do not establish absent expression. A top-marker label also cannot turn OXT transcript detection into a behavioral annotation.

## Why “64.4% contamination would be needed” overstates the evidence

The199 lower bound concerns **binary positive calls per observed barcode**. Under an explicit error model allowing false-positive gene calls and assuming genuine OXT/AVP exclusion, at least199 such calls must be corrected to remove overlap. Under a different model where only wholly artifactual joint barcodes can be removed, at least199 barcode removals are needed. Those are legitimate conditional sensitivity statements.

They are not bounds on ambient-RNA **read fraction**, doublet probability, or true dual expression. For a concrete counterexample, take303 genuine OXT-positive observations, six genuine AVP-only observations, and add one false AVP count to199 OXT observations. The reported binary marginals and minimum overlap hold, yet no observation genuinely expresses both genes. Arbitrarily many correctly measured background transcripts can make those199 false reads an arbitrarily small fraction of total reads while the64.4% binary overlap bound remains unchanged. This is a constructed measurement possibility, not a claim that it occurred in the atlas. Conversely, dropout alone cannot create positives but can obscure real coexpression; its rate is not estimated here.

Hence, the multi-donor arithmetic rules out a **single-donor concentration explanation for all observed joint detections**, conditional on the tables' definitions. It does not rule out technical effects shared across donors/studies or demonstrate peptide synthesis/release, connectivity, social behavior, or causality. No untouched donor or independent molecular assay validates those stronger claims.

## Reproduce and stop

From repository root:

```sh
.venv/bin/python campaigns/byrnes_todo_2026-10-28/experiments/audit_atlas/audit.py
```

Only Python standard library is required. `audit.log` captures all decisive values; `audit.stderr` is empty. Original tables/code remain untouched. Additional public helper files were read through the GitHub connector using exact commit URLs; no R code executed, raw cell objects downloaded, accounts created, messages sent or private content accessed. This is a bounded scientific audit, not a new pilot.

Recommended report wording: **In the pinned pooled transcript-detection summaries, at least199 of309 C4-313 observations must be OXT/AVP co-detections, spread across at least3 donors with at least125 outside the largest donor; no individual donor's co-detection is identified by marginals alone. Authentic dual expression and function remain unvalidated.**
