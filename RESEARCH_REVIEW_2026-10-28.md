# Research review and next investment

**Subsequent outcome:** the quantitative HYPOMAP study proposed below was executed and completed. See [its result](campaigns/hypomap_quantitative_2026-10-28/REPORT.md) and [the subsequent research decision](NEXT_RESEARCH_DECISION_AFTER_HYPOMAP.md). The original review is preserved below.

2026-10-28. Review of the three completed campaigns, their notebooks, source audits, selected numerical outputs and reproduction records. This is a new research recommendation, not an executed successor campaign. Prior campaign results remain unchanged.

## Judgment

The lab has produced useful empirical reconstruction, reproducible calculations and several well-supported limits on inference. It has not yet produced an independently validated new biological mechanism. The recurring bottleneck is a mismatch between the ambitious mechanism question and the information in the acquired data. More elaborate fits to those same summaries will usually preserve that mismatch.

My next investment would be a bounded quantitative HYPOMAP study: **does the apparent OXT/AVP overlap represent substantial expression of both genes, or predominantly very small secondary signals?** Its value is to decide whether the lab's strongest molecular candidate deserves biological validation. It does not promise to explain social behavior or validate the broader theory motivating this folder.

## What has already been accomplished

| Work | Result worth retaining | Consequence for further investment |
|---|---|---|
| General campaign: fly social updating | Reconstructed copying outcomes and a score/denominator discrepancy in the public supplement; quantified uncertainty and a conditional sequence-design contrast | Existing final-choice observations cannot separate updating from attention, expression or courtship selection. ABB design calculations are already done. |
| General campaign: worm and synthetic learning | Baseline correction reverses one tempting forecast conclusion; controlled simulations establish specified learning and identification limits | Four unused worms permit a genuine validation study, but forecast gain would have modest mechanistic significance. Further generic toy demonstrations have low priority. |
| Byrnes campaign: song evaluation | Corrected published dopamine summaries reproduce; acquisition and later evaluation require distinct evidential treatment | No new connection from tutor memory to the critic was identified. More summary correlation analysis cannot supply it. |
| Focused song campaign | Robust observed timing separation despite missing identities; a published HVC model stress test; pathway-control audit; explicit architecture equivalences and measurement-failure controls | The original proposed successor has now been executed. A new advance requires richer within-bird observations or a selective intervention. |
| Byrnes campaign: hypothalamus atlas | In the pinned C4-313 group, at least 199 of 309 observations must register both OXT and AVP, across at least three donors | Binary positivity does not measure substantial joint expression. Per-cell abundance is the next unexamined observable. |

Evidence: [general report](campaigns/general_2026-10-28/REPORT.md), [Byrnes report](campaigns/byrnes_todo_2026-10-28/REPORT.md), [song report](campaigns/song_target_memory_2026-10-28/REPORT.md), [song completion audit](campaigns/song_target_memory_2026-10-28/COMPLETION_AUDIT.md), [atlas notebook](campaigns/byrnes_todo_2026-10-28/experiments/atlas/NOTEBOOK.md). Selected empirical/HVC/atlas JSON outputs and the recorded 16 successful song reproduction stages were inspected; the campaigns were not rerun during this review.

## The proposed study

The contrast is between predominantly OXT- or AVP-expressing populations with small secondary signals, and a reproducible substantial mixed expression pattern. Historical co-detection and the source paper's C4-296 example already exist. Simply finding double-positive barcodes in C4-313 would not be a scientific advance.

1. **Establish the exact measurement.** Extract candidate and comparison cells with donor/source labels, OXT and AVP counts, library size and available quality measures. Resolve the newer object's cluster definitions against the pinned 309-cell result. Determine whether the count layer has undergone CellBender correction. Do not equate an AnnData `raw.X` field with acquisition-raw data.
2. **Measure abundance before building a complex model.** Report per-donor joint count distributions, minor/major expression ratios and overlap as a continuous function of minimum minor-gene count. Check library-size effects and whether any high-abundance tail concentrates in quality outliers. The old group contains six donors with counts 74, 69, 66, 53, 46 and 1; only five support useful within-donor distributions. The atlas-wide count of eleven donors is not this study's effective sample size.
3. **Challenge the signal using explicit nuisance models.** Compare donor- and depth-matched populations; vary background assumptions and simulate mixtures of relevant single-program profiles as doublet sensitivity controls. Other cell types do not identify a validated ambient-RNA ceiling. Agreement across the two input studies is a robustness check, not independent proof against a shared processing artifact.
4. **Only if substantial overlap survives, test a stronger prediction.** Ask whether mixed-abundance cells have a reproducible non-peptide expression pattern across donors, using features selected without OXT/AVP and evaluated on held-out donors. Compare a dominant-program-plus-background model with one allowing a mixed component. Use matched flexibility and show every donor, rather than pooling hundreds of nuclei into independent biological replicates. This is a predictive test of transcriptional structure, not a causal cell-type certificate.

Freeze the main abundance summaries, comparison populations and sensitivity rules before inspecting the new cell-level outcomes. The cluster was selected from all-donor summary data, so subsequent analyses are follow-up to a selected candidate, not an untouched independent cohort replication.

The concrete deliverable is a donor-resolved abundance figure and table, an explicit sensitivity analysis, and a retain/retire/unresolved decision. A positive result would nominate a specific population and expression range for joint single-cell in-situ measurement. It would not establish peptide translation, co-release, a new cell type or a social algorithm. Existing Visium spots cannot supply same-cell validation.

## Feasibility checked during this review

The [author repository](https://github.com/lsteuernagel/HYPOMAP/blob/main/README.md) links public processed objects and the [CELLxGENE collection](https://cellxgene.cziscience.com/collections/d0941303-7ce3-4422-9249-cf31eb98c480). The live collection API reports dataset `a2c833f7-b7f1-4f4d-ad31-cae478b601b7`, version `af06d70d-a2bc-43c1-8378-bc545bc8ee2c`, 433,369 cells, eleven atlas-wide donors and a 5,231,283,640-byte H5AD asset.

A bounded public byte-range inspection confirmed HDF5 metadata for `raw/X`, `raw/var`, and observation fields including `C4_named`, `Dataset`, `Sample_ID`, `donor_id`, `nCount_RNA`, `nFeature_RNA` and `percent_mt`. The complete observation-field listing did not include an exported doublet score or CellBender contamination estimate. Exact category values, candidate barcode correspondence, numeric count values and count-layer processing provenance remain unverified. No full atlas was downloaded and no joint-expression analysis was run.

This materially improves feasibility over a speculative data request. It does not eliminate the measurement limitations. Start with subset extraction; budget any full-object download explicitly if the sparse layout makes small extraction inefficient.

The 272,352 retrieved HDF5 bytes are preserved with inclusive offsets and individual SHA256 values in [the metadata manifest](sources/research_review_2026-10-28/HYPOMAP_METADATA_MANIFEST.json). HEAD values were observed in tool output; HTTP response headers were not saved. No whole-file digest is claimed.

## Decisions that would end or redirect the study

- **Retire the candidate** if its striking binary overlap is overwhelmingly attributable to tiny secondary counts, is unstable across reasonable abundance definitions, or any stronger tail is confined to one donor/study or obvious quality outliers. This weakens the candidate for this research purpose; it does not prove absence of low-level biological transcription.
- **Promote to orthogonal validation** only if substantial expression is reproducible in multiple adequately sampled donors from each source study and survives the prespecified nuisance sensitivities. A distinct non-peptide pattern would strengthen that case.
- **Stop as unresolved** if plausible nuisance models admit both entirely artifactual and substantial biological expression, or if version/provenance prevents a valid comparison. Repeated decontamination of the same processed matrix would not provide independent evidence.

## Why not simply continue song modeling?

The current song work already implements the previously recommended architectural comparison and designs an evaluator-mediation experiment. Executing that intervention requires a biological collaboration. The lab should not turn it into another synthetic-only campaign.

A more attractive computational song question would separate changes in an existing neural sequence repertoire from changes in its acoustic readout. [Mackevicius et al. 2023](https://elifesciences.org/articles/77262) reports longitudinal observations, but already demonstrates pre-existing sequences and tracks pre-tutoring factors forward. A useful successor must go beyond that published result. During this review the declared [Dryad DOI](https://doi.org/10.5061/dryad.j0zpc86km) did not yield an accessible dataset: the public API returned an identifier-cannot-be-viewed response. Synchronized bout-level activity, acoustics and cross-day cell matches have therefore not been verified here. This is an access limitation, not proof the dataset is unavailable everywhere. Reopen this option if those inputs become verifiably accessible.

The four reserved worm recordings offer a cleaner, lower-upside fallback: test population forecast gain beyond rich own-history and measured-behavior baselines. I would keep that secondary, consistent with the user's earlier direction to move beyond an obvious LOOPER continuation.

No new biological result, full data acquisition, author contact, external message or ongoing campaign is claimed by this review.
