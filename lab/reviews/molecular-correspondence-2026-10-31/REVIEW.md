# Molecular correspondence: computation accepted, aggregate interpretation narrowed

2026-10-31. Independent reviewer01a19378-2516-7c41-a127-aaa8101e7060, distinct from the investigator. **Accept the source/selection obstruction and finite numerical reconstruction. Describe the five-receptor result as heterogeneous agreement with a small net gain.** The original donor/held-gene experiment remains unrun.

The new predeclared contrary check changes the emphasis: omitting CALCR makes the published correspondence first among six pairings with a35.039%centered gain; omitting LEPR gives rank4and−28.500%gain. The all-five3.079%gain combines substantial opposing receptor contributions. This supports the author's existing heterogeneity caveat and rules out interpreting the aggregate as uniformly weak subtype information. Neither omission is adopted as a new panel or biological correspondence.

[RECONSTRUCTION.json](RECONSTRUCTION.json), [RECEPTOR_INFLUENCE.json](RECEPTOR_INFLUENCE.json), [SUMMARY.json](SUMMARY.json) and [all42permutation rows](PERMUTATIONS.csv) contain the actual calculations. [PLAN.md](PLAN.md) preceded both reviewer calculations. I wrote a separate Python standard-library implementation using scalar loops/math.fsum, without importing or inspecting the author estimator's implementation. Only after independent reconstruction did [final_check.py](final_check.py) compare the author's saved outputs: all36raw/centered/global losses across the two frozen panels agree within2.22e−16; class/global baselines agree within2.78e−17. All15main source rows, including every alternative mouse column, agree exactly.

The primary article already distinguishes the questions. In the saved primary excerpt it says, “Although correlations are useful in identifying conserved clusters between species, they cannot be used to explore conservation of gene expression” (provider L317). Figure4uses selected marker receptors (L301–302), and the text already contrasts human CALCR with mouse Glp1r in the matched POMC population (L319). [SOURCE_EXCERPTS.md](SOURCE_EXCERPTS.md) preserves this evidence without new requests. This review does not attribute a withheld-gene claim to Tadross et al., Nature2025, [DOI10.1038/s41586-024-08504-8](https://pmc.ncbi.nlm.nih.gov/articles/PMC11922758/), or establish novel species discordance.

Direct independent membership counts are24of54targets among1,404cross-species features and18among2,500human exported features,27in their union. The three POMC tables share CALCR/Calcr, GLP1R/Glp1r, LEPR/Lepr, NPY1R/Npy1r and PTGER3/Ptger3. All five are in the cross-species feature export; CALCR, GLP1R, LEPR and NPY1R are the four fixed targets. CALCR, GLP1R, LEPR and PTGER3 are also in the human feature export: four common receptors, including three fixed targets. Exact membership lists and the frozen54-symbol set are saved in RECONSTRUCTION.json. These counts establish source-input reuse; absence from a feature list would not certify independent selection, labels or normalization.

The source path converts/intersects species genes, normalizes expression and intersects variable-feature sets; scVI then subsets raw counts to supplied features and trains the joint representation. Cluster matching averages coordinates within existing human C4/mouse C465 labels and uses inherited parents during pruning. The receptor function selects markers from either species and manually adds Glp1r/Lepr. Exact inspected files/lines and limits are in [SOURCE_DEPENDENCIES.md](SOURCE_DEPENDENCIES.md). I did not execute this pipeline or inspect scUtils conversion/feature helpers, their full deployment environment, a trained checkpoint or an independently pinned one-to-one ortholog map. The merge snapshot references TF objects whose construction is commented out. Thus the source-linked dependence is clear, while exact historical execution is not independently certified.

The numerical assay uses the supplied log-normalized average-expression values directly, with no second logarithm. The source's misleadingly named pct_ratio_adj is actually log2(human/leading mouse), without global subtraction or a detection-percentage interpretation. All70ratios reconstruct:67finite differences are at most1.07e−14, and three−Infvalues match zeros in the numerator. Repeated source global means agree exactly. All70selected rows/40pairs/229cluster values,140global values and70ratios were already consumed; this review creates no new donor or validation unit.

The saved329-edge mapping covers284human/250mouse groups. Descending similarities independently reproduce the source column order: human373→mouse122(.945262), then123(.892275);374→125(.873568);375→124(.780550). Primary scoring retains122/125/124. All other columns remain in the source/output. This verifies the source-first convention; an alternative-mouse sensitivity was not performed. The historical415-versus413cluster-snapshot warning remains unresolved, not repaired.

| Fixed conditional score | Five common receptors | Four fixed targets |
|---|---:|---:|
| Raw MSE |0.608325577|0.662949692|
| Separately gene-centered MSE |0.184699266|0.224346848|
| Human POMC class/gene-mean baseline |0.190566086|0.234912659|
| Centered improvement |3.078628%|4.497761%|
| Published rank among six |3|3|
| Global-only baseline MSE |0.529554711|0.601970093|
| Global-corrected prediction MSE |0.528044571|0.602582524|
| Global-corrected improvement |0.285172%|−0.101738%|

The class baseline uses the same observed human table and is an in-sample conditional reference, not a trained or deployable predictor. The global correction is fixed H_global+M_cluster−M_global. All six permutations preserve complete mouse vectors and gene abundances. Original centered losses in source-row order122/125/124,122/124/125,125/122/124,125/124/122,124/122/125,124/125/122are respectively0.184699266,0.144245397,0.260009090,0.178490407,0.305599023,0.264534210. The published pairing is17.149%better than the mean permutation loss, so even the original aggregate has a finite positive advantage by that comparator. No best alternative is adopted.

The single contrary diagnostic deletes each common receptor once, preserving the original source-first rule and complete retained vectors:

| Omitted receptor | Centered baseline gain | Global baseline gain | Rank/6 |
|---|---:|---:|---:|
| CALCR |35.038714%|34.057095%|1|
| GLP1R |4.428269%|0.784897%|3|
| LEPR |−28.499733%|−13.788064%|4|
| NPY1R |1.895289%|−2.214260%|3|
| PTGER3 |4.497761%|−0.101738%|3|

Across the original five genes, per-gene class-baseline-minus-published losses are CALCR−.139931592, GLP1R−.012732763, LEPR+.182662972, NPY1R+.012264627 and PTGER3−.012929143. LEPR/NPY1R support the mapping on this table, while three genes oppose it under this metric. CALCR has negative cross-species centered covariance−.059615356; LEPR has positive covariance+.110161524. For every gene the gain equals twice covariance minus mouse variance. Removing CALCR gives absolute gain.042316423on its changed four-gene baseline; removing LEPR gives−.038332218. Different deletion percentages have different denominators. The diagnostic reveals cancellation and panel sensitivity, not a newly validated subset, causal explanation or biological absence/equivalence.

Controls pass independently: self-correspondence has a unique zero loss, while an abundance-only mouse matrix ties all six losses at.190566086. Raw-minus-centered loss is the same species/gene mean offset for every permutation; fixed global correction likewise changes all permutation losses by a constant. The average centered permutation loss equals human plus mouse centered variance. Maximum invariant residual across all fixed/deletion panels is2.22e−16. Numerical reliability does not establish scientific identification. The three selected subtype averages and genes are not independent donors; no p-value or biological confidence interval is earned.

[PINS.json](PINS.json) verifies12source-manifest SHA256/size pairs,11Git blobs against commit29599fcb13a74a908c986ad69d68fc3e4a3cf6d0's saved tree,34stable artifact hashes and two old helper Git blobs. [FINAL_CHECK.json](FINAL_CHECK.json) also verifies all three small old mapping/annotation input pins. Original files were not rewritten. Code/result pins are in [REVIEW_ARTIFACT_PINS.json](REVIEW_ARTIFACT_PINS.json); mutable coordination records are excluded.

Recommendation to PI: bank the verified finite calculation and source-selection audit; add the receptor-cancellation result to synthesis. Further re-scoring of these selected means cannot earn the primary test. The most valuable prerequisite for any separately funded continuation is compatible source-linked non-target/receptor expression for both species with donor/sample and class identifiers, adequate ortholog/processing provenance, and matching rebuilt under target exclusions. Published clusters would still condition that test. No compatible object was established by the author's bounded acquisition; that is not proof it is absent from the deposit or biologically impossible.

All work finished within the registered35minutes. [ACCOUNTING.json](ACCOUNTING.json) charges73,081,679review read/decoded bytes including70MBconservative context/runtime/source/code/output/failed-call reserve; instrumented peakRSS15,810,560bytes; no network requests or raw-atlas/range-cache payloads, one scientific process/thread, jobs0. Both final-verification passes are charged. Historical author191,451,239read/decoded bytes,20,165,421ingress/20requests, HYPOMAP3,277,786,552range bytes, memory7,774,826,112bytes and all protected/consumed observations remain intact. Five ordinary hook-denied reads/searches are recorded; no scientific pass failed. No successor, heartbeat, infrastructure, correspondence, credit or target-release action is authorized by this review.
