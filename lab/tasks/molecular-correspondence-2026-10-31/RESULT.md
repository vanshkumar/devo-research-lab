# Molecular correspondence: a held-gene claim is not earned

2026-10-31. Bounded pilot completed with a substantive finite obstruction test. The primary54-receptor prediction experiment was **not run**: published matching uses many of those receptors, and no compatible donor-resolved, non-target matching matrix was acquired within the request allocation. This is not evidence against conserved biology or a defect claimed in the original atlas paper.

The useful result is narrower: the published POMC receptor tables support only a selected, conditional comparison. On five receptors shared by three POMC subtype tables, the published correspondence ranks third among all six within-POMC pairings. Its gene-centered squared error is0.184699 versus0.190566 for a conditional per-gene POMC class mean, a3.079%reduction. All five receptors entered the cross-species integration. These data do not validate prediction of genes withheld from correspondence inference.

## Closest prior and exact assay

[Tadross et al., Nature2025](https://pmc.ncbi.nlm.nih.gov/articles/PMC11922758/) is the direct prior. It already compares human/mouse POMC and AGRP receptor expression and distinguishes cell-type matching from expression conservation. Its Figure4 presents log-normalized averages and selects up to ten marker-enriched receptors per species. Receptor discordance is therefore established context; the present audit is not a newly discovered general species difference.

We pinned [HYPOMAP commit29599fcb13a74a908c986ad69d68fc3e4a3cf6d0](https://github.com/lsteuernagel/HYPOMAP/tree/29599fcb13a74a908c986ad69d68fc3e4a3cf6d0). Twelve tree/source artifacts have exact SHA256 pins; eleven code/feature/table files also match the tree's Git blob SHA1 and byte size. The original329-edge mapping covers284human/250mouse groups. Preserve its415-versus413human-cluster snapshot difference from the paper; neither labels nor historical outputs were repaired.

The merge script converts mouse genes through `scUtils::convert_species_seurat` using Ensembl August2020/release101, intersects shared genes, normalizes, and intersects species' variable-feature sets. Its commented TF-only setup and active references to TF objects mean it is not independently certified as a clean standalone executable pipeline. The exact conversion-helper implementation and strict one-to-one ortholog rule were not reconstructed. We use literal source-supplied gene pairs in the small-table comparison.

The scVI script copies raw counts and subsets to the supplied features before training an80-dimensional joint representation with sample batch and species/dataset covariates. The matching script correlates cluster-average coordinates and prunes with inherited parent labels. Human C4 and mouse C465 identities already come from published clustering. The receptor plotting function then selects the union of enriched receptors from either species, adds specified receptors manually, and queries these same populations. New scoring of that output does not remove either feature reuse or selection.

## Direct feature and selection measurements

The prespecified panel is54neuropeptide/hormone receptors, including LEPR. It is a scoped biological panel, not an exhaustive receptor ontology. [Frozen protocol](PROTOCOL.md), [pre-comparison schema clarification](SCHEMA_CLARIFICATION.md) and [FEATURE_AUDIT.json](FEATURE_AUDIT.json) preserve choices and timing.

| Published feature set | Total features | Panel receptors present |
|---|---:|---:|
| Cross-species integration |1,404|24/54|
| Human clustering feature list |2,500|18/54|
| Either list |—|27/54|

Absence from these lists does not certify independence from feature selection, normalization, cluster construction or previous inspection. Rebuilding a readout after removing receptors would leave the original representation dependent on them.

The three POMC tables share CALCR/Calcr, GLP1R/Glp1r, LEPR/Lepr, NPY1R/Npy1r and PTGER3/Ptger3. Four are prespecified panel targets; all five are cross-species features. CALCR, GLP1R and LEPR are also in the human feature list. Only five common pairs are available because the original tables used scenario-specific marker selection; missing rows are not zero expression. Across all four acquired tables,70rows represent40distinct gene pairs and229cluster-expression values. These are aggregated source outputs with no donor/sample columns.

## Actual finite comparison

Use three human POMC subtypes: C4-373, C4-374 and C4-375. The source's leading mouse matches are C465-122, C465-125 and C465-124, respectively. C4-373 also has a second mouse match. Following the source ratio's first-column rule, the primary finite comparison uses its leading match; no outcome-driven choice or equal-weight amalgamation of the two mouse subtypes was performed. All source columns remain preserved.

Scores use the supplied log-normalized expression scale, without a second logarithm. Each subtype and gene has equal weight. Centering subtracts each gene's mean across the three POMC groups separately within each species. Thus the class-mean baseline is an in-sample, deliberately strong conditional reference using the human table; it is not a deployable predictor. Global-neuron correction uses source-supplied means without a fitted coefficient.

| Conditional score | Five common receptors | Four prespecified targets |
|---|---:|---:|
| Published pairing, raw MSE |0.608326|0.662950|
| Published pairing, POMC gene-centered MSE |0.184699|0.224347|
| Conditional class/gene-mean baseline MSE |0.190566|0.234913|
| Reduction over that baseline |3.079%|4.498%|
| Published pairing rank among six |3/6|3/6|
| Reduction after global-neuron abundance correction versus global-only baseline |0.285%|−0.102%|

All six permutations preserve complete mouse expression vectors and per-gene abundance while staying within POMC identity. For the five-gene panel, their centered MSEs are:

| Mouse groups for human rows373/374/375 | Centered MSE |
|---|---:|
|122/125/124, published|0.184699|
|122/124/125|0.144245|
|125/122/124|0.260009|
|125/124/122|0.178490|
|124/122/125|0.305599|
|124/125/122|0.264534|

The best permutation is a post-hoc comparison, not an adopted biological mapping. The published pairing beats the mean of the six permutation losses by17.149%, but two permutations fit these selected receptors better. A positive finite advantage exists; neither unique receptor fidelity nor a held-gene advantage is established.

The small net class-mean improvement is heterogeneous: per-gene loss improvements are CALCR−0.139932, GLP1R−0.012733, LEPR+0.182663, NPY1R+0.012265 and PTGER3−0.012929. This does not identify a mechanism or establish absence of subtype information. With complete panels, centering subtracts a constant species/gene offset from every permutation's raw loss, so it cannot change their ordering; that invariant was explicitly verified.

No biological confidence interval or permutation p-value is reported. Three aggregated subtype groups and five selected genes are not independent donor replicates. AGRP supplies a distinct broad-class table, but its selected panel is not a balanced matched/null matrix and was not used to manufacture a cross-class success.

## Verification, limitations and decision

[COMPARISON.json](COMPARISON.json) contains actual expression vectors, every permutation, per-gene losses and source-column choices; [PERMUTATIONS.csv](PERMUTATIONS.csv) is a compact export. A separately written standard-library scalar reconstruction agrees with NumPy within2.22e−16; loss-decomposition identities agree within1.67e−16. All15source ratios reconstruct within4.67e−15 and repeated global means agree exactly. The self-correspondence positive control has a unique zero loss; an abundance-only negative control ties all permutations. [SCALAR_VERIFICATION.json](SCALAR_VERIFICATION.json) records these checks and exact exposure. This is a second implementation by the same investigator, not independent scientific review.

The exact missing object is compatible human and mouse expression on **non-target ortholog features plus receptor outcomes, with donor/sample and class identifiers**, sufficient to rebuild correspondence under exclusions. A faithful source-linked ortholog map and processing definitions are also needed. The existing human count subset is peptide-focused and has no mouse matrix; its full186MBcompressed/approximately685MBdecoded selected matrix was not reread. The reused full human asset is5.23GBand was not downloaded. No new raw-cell payload was read.

Both Cambridge DOI page opens failed in the web tool. One final capped DataCite request confirms the human deposit [1810/373636](https://www.repository.cam.ac.uk/handle/1810/373636), open access and CC BY4.0, but returns empty sizes/formats and no content URL. That establishes neither missing deposited matrices nor their size. At20charged requests, further acquisition stopped. No compatible matrix was certified within this allocation, so independent matching, donor replication and the primary54-receptor prediction remain unrun.

**Recommendation:** bank the circularity/selection audit and finite POMC check; do not promote these published tables as withheld-gene validation. Any later investment should first obtain small, source-linked donor-by-cluster pseudobulk matrices for both species, then freeze a rebuilt match excluding the entire target panel from selection, normalization and matching. Retain published-cluster conditional status and independent donor evaluation. Re-scoring the current selected table cannot resolve the original question. A fresh PI-allocated reviewer can cheaply challenge the pins, source dependencies and six-permutation result.

## Accounting and protected observations

START19:18:30UTC; numerical/scalar checks complete19:29:30UTC, before20:48:30deadline. No jobs remain. [ACCOUNTING.json](ACCOUNTING.json) preserves successful/failed requests and reread charges.20requests are charged, including one failed sandbox DNS request and conservative DOI redirect allowances. Charged new ingress20,165,421bytes comprises165,421measured GitHub/DataCite bytes plus20MBweb-source allowance; exact web-provider network bytes are unavailable. Charged additional read/decoded bytes191,451,239include150MBwhole-run context/runtime/documentation/output reserve and40MBweb read/decoded allowance. These are conservative charges, not an exact network/OS meter. Highest instrumented scientific-process RSS27,885,568bytes; one process and one numerical thread at a time.

Prior HYPOMAP3,277,786,552range bytes, all original cell/summary exposure, failures and frozen files remain intact. No range-cache payload was reread. Existing memory lineage7,774,826,112/8GBis unchanged. Pan20, Flesch81/B2/B20, later HABITS, all memory targets and the four reserved baseline worms remain closed. No old branch repair, successor dispatch, heartbeat change or external contact occurred.
