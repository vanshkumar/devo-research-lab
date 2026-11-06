# HYPOMAP social-signalling candidate pilot — completed

Date2026-10-28. One substantive empirical pilot for Byrnes to-do§2.5, with controlled analytical checks. PLAN.md saved before downloaded-table outcomes. No novelty claim or evidence for a “social drive” cell function. Decision: **keep as a bounded candidate-nomination result; revise the more ambitious cross-species signalling question until matched expression and donor-level data are available.**

## What was actually analyzed

Pinned author-derived marker/matching/annotation tables, not acquisition-raw cells. 415 granular human C4 clusters,166475 nuclei in annotation table;329 retained matching edges connecting284 human and250 mouse clusters;131 human C4 groups unmatched. Matching/table joins and the separately exported correspondence table agree exactly. Repository and final-paper scope differ by two human clusters/matches; results here are explicitly for this snapshot.

The source export is **not an expression matrix**: adjustedP<.0001 and specificity>1. Hence absent AVPR1A rows do not show absent AVPR1A expression. The predeclared TAC2 query used the mouse gene symbol; human TAC3 is the proper ortholog and was added only after detecting that mistake, clearly exploratory. The full gene list/grid is retained, including these zero hits.

## Observed marker cohorts and mapping

| Gene | Exported C4 marker groups | Unmatched | 1:1 | 1:N | M:1 |
|---|---:|---:|---:|---:|---:|
| OXT |4|1|3|0|0|
| AVP |9|2|6|1|0|
| OXTR |2|1|0|0|1|
| ESR1 |55|10|18|7|20|
| GAL |23|4|6|4|9|
| PRLR |82|18|32|7|25|

These are overlapping descriptive cluster cohorts, not independent subjects and not p-values for cross-species conservation. Naming a population by ESR1/GAL/PRLR does not isolate one neuronal type, let alone one behavior. “1:1” is a retained graph relation under this integration/pruning procedure, not a posterior confidence or function match.

OXT-named C4-313 is a useful candidate:309 nuclei,98.1% detected OXT; it maps1:1 to mouse C465-134 Oxt.Caprin2.GLU-6 at latent-centroid correlation.94356. It contains66.3% AVP detection too; a strict OXT/AVP mutually exclusive partition is incompatible with these observed pooled marginals. This says nothing by itself about peptide release, effective connectivity or social function.

The strongest exported OXTR group is C4-263 RSPO3/TGFBI:90 nuclei,71.1% detected OXTR. Its retained mouse counterpart is C465-38 Tcf7l2.Tbr1.Meis2.Samd3.GLU-2, correlation.72460, shared by three human groups. Human donor contribution is concentrated:61.11% from donor3u5kk. The other exported OXTR group, C4-46 PAX6/SCGN, is unmatched,136 nuclei,20.6% OXTR detection,70.59% from the same donor. These figures prioritize a donor/region-expression audit; they do not establish a human-specific oxytocin receptor circuit. Mouse Oxtr expression in the matched cells is not contained in these tables.

## Predeclared sensitivity and scientific controls

Using every exported marker row, fixed top5 and fixed top20 specificity ranks yields materially different nominations. OXTR appears in zero top5 groups and one top20 group; PRLR in zero top5 but82 full-marker groups. Convenient top-marker-only tables would therefore erase these query genes without establishing their absence. Full outputs and all rank conditions remain in gene_summary.csv and target_marker_rows.csv; no rank was selected to maximize an effect.

Positive identity controls pass: C4-373 maps to two Anxa2.Pomc partners; C4-374 to Ttr.Pomc; C4-355 to five Agrp partners; C4-331 contains an Hcrt-labelled partner among four. The highest-correlated HCRT-group partner is not necessarily the Hcrt-labelled one, illustrating why transcriptomic whole-cell matching and single-gene matching are different questions. Raw join coverage/degree counts independently agree with the second published export.

An additional post-discovery calculation strengthens the OXT/AVP overlap interpretation while preserving its narrow scope. For two events with marginal probabilities p and q, joint detection must lie in[max(0,p+q−1),min(p,q)]. Observed OXT/AVP marginals require at least64.4% co-detection in C4-313, conservatively64.3% allowing both three-decimal rounding errors. Corresponding conservative lower bounds are42.9% in C4-296,37.4% in C4-312 and49.2% in C4-315. This is a pooled transcript-detection bound, conditional on the same cluster universe for both marker percentages. It is not direct joint-cell reanalysis and cannot separate ambient RNA, doublets or donor-specific expression.

Validation: independent stdlib CSV extraction verifies the C4-313 marginals. A sharp integer known-answer construction (100 events,73 and64 positives) achieves both Fréchet endpoints37 and64; exact set enumeration checks the formula. Thus the overlap statement does not rely on a persuasive cluster label. Gene/source summaries were generated independently of any neuronal social-function annotation.

## Interpretation, objections and stop

A concrete useful next target is OXT C4-313, but conservation of its molecular identity and nuclear transcript detections is not conservation of an oxytocin reward algorithm. The OXTR route is more uncertain and needs actual matched receptor expression, donor robustness and regional coverage. The principal surviving objection is that integration, filtered markers, donor composition and pruning can manufacture a convenient mapping; no untouched independent atlas or donor-held-out validation was performed. Both integration inputs and outputs are author-derived. The known-marker controls validate data handling and recover expected identities, not the cross-species biological mapping itself.

No human-specific gene absence, “parenting neuron,” connectivity or species difference in sociality is established. A hypothesis about those mechanisms would require additional measurements, not simply relabeling these clusters. The source paper already emphasizes distinct cell-identity and receptor-expression conservation; this pilot makes the implication concrete for the requested social-signalling candidates.

## Commands and artifacts

From repository root:

```sh
.venv/bin/python campaigns/byrnes_todo_2026-10-28/experiments/atlas/acquire.py
.venv/bin/python campaigns/byrnes_todo_2026-10-28/experiments/atlas/run.py
```

acquire.py is network-free on valid cache reuse; it verifies every original file. Data paths relative to campaign root are in data/atlas/manifest.json. Main scientific outputs: target_marker_rows.csv, target_correspondence.csv, cluster_mapping_summary.csv, gene_summary.csv, co_detection_bounds.csv and summary.json. run.log preserves full summaries; stderr.log is empty. Dependencies: Python3.9+,numpy2.0.2,pandas2.3.3; no additional installation. No randomness in this pilot; no seed needed.

Failure/deviation record: table-scope discrepancy and final-XLSX access failures recorded; TAC2/TAC3 query corrected exploratorily, not retroactively rewritten; co-detection calculation added after observing marginal overlap. No paid resources, accounts, private data, publication or messaging. Root owns aggregate STATE/LEARNINGS, so this worker does not edit them.

## Promoted follow-up: exact integer and donor-capacity constraints

FOLLOWUP_PLAN.md was saved before these calculations. New runnable script followup.py uses the same pinned tables and exact Decimal intervals. Source-code inspection confirms the reported detection fractions are rounded to three decimals before optional test downsampling; donor percentages are rounded to two percentage-point decimals. Thus the rounding model has direct implementation support. The mapping from this repository snapshot to the exact final publication processing version remains unresolved.

Each target's gene-count and donor-capacity intervals contain a unique integer solution given itsN. Results:

| Cluster | N | OXT+ | AVP+ | Minimum joint detection | Minimum outside largest donor | Minimum donors contributing |
|---|---:|---:|---:|---:|---:|---:|
| C4-296 |200|115|171|86(43.0%)|2|2|
| C4-312 |687|273|672|258(37.55%)|0|1|
| C4-313 |309|303|205|199(64.40%)|125|3|
| C4-315 |280|180|238|138(49.29%)|17|2|

For C4-313, the largest donor has74 nuclei, and the two largest donors together143. Since at least199 observations must have both detected transcripts, neither one donor nor two donors can contain them all. However, every *particular* donor has a possible compatible allocation with zero joint detections. That does not mean all donors can simultaneously have zero. It means the summaries require at least three contributing donors without identifying which three or estimating their expression rates.

A four-category integer model (neither gene/OXT-only/AVP-only/both) enforces donor capacities and both global marginals. Independent mixed-integer optimization agrees with every analytic total, outside-largest, contributor-count and donor-specific lower bound. allocation_witnesses.csv records feasible assignments attaining the first three bounds. Fifty-two exact exhaustive small-universe cases independently verify the overlap, capacity and contributor formulas, including no-overlap and high-overlap controls. These are exact implications of the summaries under stated assumptions, not model agreement as biological validation.

An exploratory extension applies the same capacities across source studies. In C4-313, Siletti contributes186 nuclei and Tadross123. The199 joint minimum forces at least76 detected overlaps in Siletti and13 in Tadross. Those cannot all arise from only one input study, but this is a derived aggregate constraint, **not an independent raw-data replication or held-out donor test**. The other three clusters do not force nonzero overlap in both studies.

### What contamination would need to do—and what the calculation cannot say

If the true biological overlap were zero in these barcodes, at least199 false-positive *binary gene calls* would be needed to explain C4-313's overlap, one per necessarily double-positive observation. Or at least199 wholly artifactual barcodes would need to be removed to reduce this guaranteed-overlap bound to zero. contamination_sensitivity.csv gives the full conditional curves: a cap of30 artifactual observations still leaves169 detected overlaps; a cap of10% of309, or30, is an assumption—not a measured artifact rate.

Do **not** read this as “ambient contamination must be64% of the RNA.” A small RNA mass or one residual transcript in many nuclei can create many positive detections. Nor does a low whole-atlas doublet rate settle the selected cluster:199 observations are only0.120% of166475 neuronal nuclei and artifacts may concentrate in a rare selected group. This pilot does not measure an artifact rate, molecule abundance, true coexpression, peptide translation, release, joint projections or social function. Existing CellBender processing is relevant but is not independently assessed here.

### Strongest prior-work/interpretation check

The source review substantially weakens any tempting novelty/biology claim. Earlier primary rat studies already found transcript co-detection, and Xi et al1999 emphasized that qualitative co-detection can coexist with strongly unequal transcript abundance and distinct dominant phenotypes. Lactation/salt-loading studies show that state and assay matter. The older human in-situ study observed segregation but explicitly could not establish whether both genes occur in the same cell. None provides a matched human–mouse quantitative comparison to these summaries. Consequently, our result should change the *measurement question*: whether the human group contains genuinely mixed molecular states with meaningful minor-transcript abundance, not whether a binary gene label alone divides “oxytocin neurons” from “vasopressin neurons.” Source/access limits are in SOURCES.md.

**Decision after stronger test:** retain the exact observation-level constraint and prioritize orthogonal joint, quantitative detection plus artifact checks if this direction receives future investment. Donor concentration alone cannot erase C4-313's pooled overlap; observational/assay ambiguity still prevents a circuit or species-sociality conclusion. No additional data or experiment is promised by this bounded follow-up.

Reproduce the follow-up:

```sh
.venv/bin/python campaigns/byrnes_todo_2026-10-28/experiments/atlas/acquire.py
.venv/bin/python campaigns/byrnes_todo_2026-10-28/experiments/atlas/followup.py
```

Outputs: integer_bounds.csv, donor_bounds.csv, dataset_bounds.csv, allocation_witnesses.csv, contamination_sensitivity.csv, followup_summary.json, followup.log and empty followup_stderr.log. Source-code files newly acquired total about34KB; no additional atlas data downloaded. SciPy1.13.1/HiGHS used for integer optimization, deterministic; no random seed. The script verifies input hashes each run.
