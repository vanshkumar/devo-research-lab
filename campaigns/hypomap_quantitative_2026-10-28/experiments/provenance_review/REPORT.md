# Source and scope audit

2026-10-28. Focused provenance/literature review, performed without inspecting joint OXT/AVP count outcomes. Original campaign evidence was preserved. This folder owns only source evidence and a metadata reconciliation.

## Findings that affect the analysis

1. **Use processed counts, with study-specific provenance.** The public author's pipeline supports RNA count export, but `raw.X` is not acquisition-raw. CellBender processing is documented for Tadross; the imported Siletti matrix follows a different upstream processing path. Residual contamination cannot be ruled out by the presence of a corrected layer.
2. **Harmonize exported mitochondrial QC units.** A direct code path renames Siletti's fractional `MT_ratio` to Tadross's percentage-style `percent.mt`. Subsequent numerical checks below confirm these mixed units in the current object. Recompute from counts or divide Tadross by100 before comparing fractions.
3. **The modern object agrees with the older repository snapshot at aggregate cluster level.** All 415 neuronal C4 names and sizes match exactly, totaling 166,475 nuclei. The 452 categories in `C4_named` include 37 inherited non-neuronal C3 groups. This reconciles 452 versus 415; it does not reconcile the publication's 413 neuronal clusters/165,815 neurons in cross-species analysis.
4. **The old 309-cell candidate and six donor counts are reproduced in current metadata.** Counts are 74,66,46 Siletti and 53,69,1 Tadross, with donor identities retained in `candidate_comparison_donors.csv`. Exact barcode equality to the old snapshot is not proven because its barcode roster was not part of the old evidence.
5. **Quantitative transcript imbalance has direct primary precedent.** Xi1999 found average dominant/minor ratios of 256 and 182, plus one coexisting neuron at ratio 2. A new binary-overlap claim would be insufficient.

## Code trace and exact evidence

HYPOMAP files are pinned to commit `29599fcb13a74a908c986ad69d68fc3e4a3cf6d0`. Retrieved files, source URLs, byte counts, SHA256 and independently checked Git blob SHA1 are in `code_manifest.json`; all ten source-code blob checks pass. No code in these source files was executed.

| Source location | Evidence | Implication |
|---|---|---|
| [01_read_data.R](https://github.com/lsteuernagel/HYPOMAP/blob/29599fcb13a74a908c986ad69d68fc3e4a3cf6d0/tadross_processing/01_read_data.R), 71,94–103,112–113,201–211 | Tadross reads 10X H5, supplies matrix to Seurat counts, computes mitochondrial percentage, invokes scDblFinder | Counts derive from input H5, whose pre-R CellBender processing is documented by the paper; exported fields do not retain all original QC information |
| [make_merged_data.R](https://github.com/lsteuernagel/HYPOMAP/blob/29599fcb13a74a908c986ad69d68fc3e4a3cf6d0/make_merged_data.R), 61–69,149–158,215–223 | Imports already processed Siletti; renames MT_ratio; copies Tadross RNA counts into new object; merges; drops DoubletClass from selected metadata | Study-specific count/QC provenance; no common correction inferred |
| [Siletti import](https://github.com/lsteuernagel/HYPOMAP/blob/29599fcb13a74a908c986ad69d68fc3e4a3cf6d0/siletti_processing/load_hypoMatrix_and_make_seurat.R),12–21,32–55 | Uses separately exported `hypomatrix.hdf5/sub_matrix`, aligns names to hypothalamic loom metadata by assumed order, creates Seurat counts and normalizes | Code expresses an alignment assumption; no independent execution evidence checks the source submatrix/loom order |
| [19_build_final_object.R](https://github.com/lsteuernagel/HYPOMAP/blob/29599fcb13a74a908c986ad69d68fc3e4a3cf6d0/integration_pipeline/run_scripts/19_build_final_object.R),157–159,180–183 | Clears RNA scale.data and exports RNA with SeuratDisk | Supports counts in H5AD raw.X, conditional on the documented conversion behavior |
| [SeuratDisk Convert documentation](https://mojaveazure.github.io/seurat-disk/reference/Convert.html), “h5Seurat to AnnData/H5AD” | Without scale.data, X receives data and raw.X receives counts | Strong expected mapping, but not a checksum chain from that export to CELLxGENE version af06d70d-a2bc-43c1-8378-bc545bc8ee2c |
| [Siletti qc_functions.py](https://github.com/linnarsson-lab/adult-human-brain/blob/2b5aa12dffb8cc1bcb3979c409cb6ac907546b2e/cytograph/preprocessing/qc_functions.py),6–14 | MT_ratio divides mitochondrial sum by total UMI without multiplying by 100 | Exported cross-study mitochondrial units require direct verification |

Siletti author repository is pinned for code at `2b5aa12dffb8cc1bcb3979c409cb6ac907546b2e`. Its [README](https://github.com/linnarsson-lab/adult-human-brain/blob/main/README.md), preserved with Git blob `bb89671f8b9c24b14b51cf297f66a400ecd5043f`, documents STAR 2.7.10, customized Gencode35 annotation, EmptyDrops_CR cell calling and alternative CellRanger reprocessed matrices. The alternative matrices explicitly contain the same cells, with some zero-total cells. They are a potential processing-sensitivity source, not an independent cohort. `siletti_commands.py` lines299–315 documents DoubletFinder scoring and flags. No CellBender/ambient correction was identified in the inspected Siletti sources; this is not proof that none occurred anywhere upstream.

## Primary-paper evidence and limits

**Tadross et al., Nature2025**, [full inspected Methods and Results](https://pmc.ncbi.nlm.nih.gov/articles/PMC11922758/), DOI10.1038/s41586-024-08504-8. Methods “Sequence alignment, cell calling and quality control” specifies CellBender for their data and subsequent imported Siletti loom; filtering includes scDblFinder and sample/global quality thresholds. Results explicitly discusses C4-296 AVP/TFPI2 with OXT/TH/SCGN, which is distinct from C4-313. Cross-species analysis reports 413 human neuronal clusters, unlike the current object's 415. The paper's smFISH probes include AVP but not OXT; those experiments do not validate same-cell OXT/AVP overlap. The 433,369 final-cell total matches the current object. Paper-level provenance is not a measured residual-error rate.

**Xi, Kusano & Gainer1999**, [PubMed](https://pubmed.ncbi.nlm.nih.gov/10499525/), DOI10.1210/endo.140.10.7054. Primary abstract acquired from the public NCBI EFetch API and preserved as `xi1999_pubmed.xml`. Competitive RT-PCR of individual normal female rat SON neurons had reported sensitivity below30 mRNA molecules/cell. The primary abstract gives mean OT/VP≈256 for oxytocin neurons and VP/OT≈182 for vasopressin neurons, with one coexisting neuron at OT/VP≈2. These are whole-cell measurements in rat, not calibrated numerical cutoffs for human nuclear 10X counts. Full paper was not acquired. Do not substitute the later review's approximate500:1 description for these primary values.

**Li et al., Cell Reports2026**, [primary indexed text](https://pmc.ncbi.nlm.nih.gov/articles/PMC13007250/), “A spatial and projection-based transcriptomic atlas of paraventricular hypothalamic cell types,”45(2):116904. Relevant human comparison reuses Siletti and Tadross, reclustering3,432 SIM1+ nuclei into21 groups; it is dependent evidence. The corresponding [2025 preprint](https://pmc.ncbi.nlm.nih.gov/articles/PMC12633530/) explicitly describes a mouse Esr2-Abcc9 group positive for both Avp/Oxt. Mouse MERFISH measures these high-abundance peptides using separate sequential fluorescence assays with volume normalization and median subtraction. That evidence limits broad novelty/species claims but does not calibrate human counts or prove that C4-313 is the same state. The final article and preprint should not be silently treated as identical versions. Only relevant primary indexed text was inspected; direct PMC pages returned browser checks. A possible exploratory comparison would examine ESR2/ABCC9, RXFP3 and PLA2R1, while clearly labeling these as literature-informed after protocol freezing.

## Reproduction and access record

Run from repository root:

```sh
.venv/bin/python campaigns/hypomap_quantitative_2026-10-28/experiments/provenance_review/reconcile_metadata.py
```

This independently reads the newly extracted metadata and original pinned table, without importing the main analysis or reading any expression matrix. Outputs: `cluster_reconciliation.csv`, `candidate_comparison_donors.csv`, `metadata_reconciliation.json`. The first development run included inherited C3 labels in a C4-only join; this schema mismatch was corrected explicitly by restricting IDs to `C4-`. No expression conclusion depended on the preliminary output.

GitHub source retrieval used the connected read-only GitHub tool and public tree API; primary-paper retrieval used the web tool and NCBI EFetch. The latter returned Xi XML successfully, then an attempted Siletti EFetch retrieval failed DNS. Xi DOI open failed in the web tool; PubMed HTML returned a stripped page. Siletti Science DOI returned403. Li PMC direct pages presented browser checks; indexed primary text remained available. None was bypassed. No atlas bulk downloads, controlled reads, messages to authors or external mutations were performed by this review.

Remaining provenance limits: no retained current CELLxGENE curation script, no exact original input-H5 hashes, no historical barcode roster, no raw droplet/background matrix, and no count correction uncertainties or original per-nucleus doublet scores. These qualify technical interpretation; they do not prevent a quantitative processed-count analysis.

## Subsequent depth and mitochondrial reconstruction

After completing the source review above, the lead disclosed its primary abundance result and requested a bounded investigation of discrepancies between exported `nCount_RNA`/`nFeature_RNA` and recomputed raw counts. The following checks are post-outcome source diagnostics; they are not an untouched abundance replication.

`reconcile_depth.py` independently reads the1476×36924 peptide-comparison sparse matrix, recomputes row sums/features and sums all37 `MT-` genes. Every cell has raw totals and feature counts below the metadata figures. Missing-count fractions span2.40–7.40% in Tadross (median4.34%) and2.51–8.05% in Siletti (median5.23%). This is consistent with feature removal after metadata computation, rather than a random row mismatch. It does not identify which filtering/curation step occurred.

More decisively, mitochondrial counts divided by metadata `nCount_RNA` reproduce exported `percent_mt` after dividing that field by100 in Tadross and leaving it unchanged in Siletti. Maximum absolute fractional errors are2.28×10⁻⁹ and1.26×10⁻⁸ respectively. This numerically confirms mixed units and provides a substantial check of cell/count/metadata correspondence. Small residual error is consistent with float32 storage. It does not prove the correctness of the entire upstream workflow.

```sh
.venv/bin/python campaigns/hypomap_quantitative_2026-10-28/experiments/provenance_review/reconcile_depth.py
```

Detailed per-cell diagnostic fields and study summaries are in `depth_mt_reconciliation.csv` and `.json`. Primary OXT/AVP values are not used in this diagnostic. Use recomputed raw totals as an explicit denominator for this extracted feature universe, with metadata-depth sensitivity where appropriate. The normalized-X small-row comparison is owned by the acquisition worker, avoiding duplicate downloads.
