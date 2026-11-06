# Frozen comparison: natural timing support versus artificial edits

Prepared after the first-six-recording development calculation, before scoring later recordings. All dates UTC. Main freeze is the hash manifest written by `freeze.py` before `evaluate.py main`.

## Question and scope

Can repeated, manually annotated natural `abc` phrases supply a statistical timing target that accepts later natural renditions but penalizes declared changes? Strong alternatives: a single average template or nearest exemplar suffices; flexible alignment earns tolerance by deleting temporal information. Natural renditions are observations, not known optimal targets. Designed edits are assay inputs, not measured biological mistakes or judgments of perceived quality. Scores ranking an edit below its original are finite assay failures only under the declared reference-rendition convention; an edit can move toward another legitimate rendition.

The first6 chronological files contain27 `abc` occurrences. `abc` is the most frequent consecutive trigram with three distinct nonintroductory labels (count ties lexical), chosen without metric results. Feature vector is the positive five intervals `[duration_a,gap_ab,duration_b,gap_bc,duration_c]` in seconds, transformed by natural log. Source human labels and segmentation are supplied equally to every evaluator. They use acoustic structure AND sequence context; this is a symbolic timing assay, not an acoustic recognition result or a discovered representation. No desired edit magnitude or reference timing is passed into an evaluator.

## Allocation and fitting

Sort the39 CSV recording filenames chronologically (fixed date, zero-padded clock, acquisition suffix). First19 are teaching (including6 development); next10 are main evaluation; final10 are reserved for one predeclared test/revise step. File lists and annotation hashes are frozen. Extract nonoverlapping `abc` occurrences only, advancing3 after a match. Keep all positive intervals; invalid/nonmonotone intervals stop the affected comparison. No file or rendition is dropped based on performance.

One identified bird/day is the biological unit. Recording/phrase summaries are descriptive; no bird-population confidence interval or significance test. Repeat-rich recordings have equal total fitting/calibration weight, divided among their phrases. Teaching parameters and leave-one-recording-out 95th-percentile score thresholds are fitted solely to first19 files. Threshold quantiles give equal total weight to each recording. These are finite calibration thresholds, not guaranteed 95% future coverage. Main acceptance/edits are also averaged equally across recordings, with rendition counts disclosed.

Fixed metrics, no hyperparameter tournament:

1. `prototype`: root mean squared log-interval difference from the equal-recording mean template.
2. `nearest`: minimum RMS log-interval difference to any teaching example; calibrate excluding the whole same recording.
3. `covariance`: Mahalanobis RMS using teaching covariance, fixed20% diagonal shrinkage and variance floor(0.002)^2. No shrinkage selection.
4. `free_tempo`: minimize template RMS over one additive log-tempo shift (subtract mean log residual). This is ordinary global alignment; it is mathematically invariant to global scaling.
5. `shuffled_covariance`: same covariance recipe after independently permuting the five interval positions within each teaching example, fixed per-example hash seed. This retains the interval pool while destroying position-specific teaching; it is not another natural tutor.
6. `absent`: constant zero timing cost. This control cannot give corrective timing ranks.

For sequence, ordinary learned exact label order is an explicit separate gate, not mixed into timing distance. Every ordered method rejects non-`abc`; an order-erased/bag gate accepts permutations. Sequence success is therefore a supplied-label positive control, not evidence for a novel sequence mechanism. Do not claim improvement from artificial arithmetic penalties or target-derived label inference.

## Challenges and interpretation

For each main held rendition, evaluate original and multiplicative changes at factors0.8,0.9,0.95,1.05,1.1,1.2 applied to (a) all five intervals, (b) duration_b, (c) gap_ab, (d) duration_c. Hold all other intervals fixed; nonoverlap/positivity is preserved. Also reverse and cyclically rotate label sequences. These are controlled feature edits; no resynthesis/acoustic realism or recorded biological error is claimed.

Report equal-recording natural acceptance, edit rejection at the fitted threshold, strict paired cost increase and ties separately for every edit direction/magnitude/component. Strict rank tolerance1e-12 in dimensionless score. Main practical criterion, declared here: >=90% later natural acceptance AND >=80% rejection for each of the eight20% timing challenges (four locations by two directions), plus >=80% strict ranking on each. Report every failure; a pooled winner cannot erase a failed component. Smaller edits probe the tolerance/correction tradeoff; they do not change the gate. No multiplicity-adjusted population statement. Known-answer checks: exact fit/template scores, free-tempo scale invariance, true log-edit distance, absent/shuffled tutoring and independent direct-versus-optimized score checks. No full motor acquisition is attempted, so no actor or learned acquisition claim.

## One allowed revision, with untouched final10

After main output, decide whether a simple finite tempo constraint repairs the known alignment tradeoff without discarding natural variation. Only allowed revision: `bounded_tempo`, combining unchanged free-tempo residual distance with a penalty outside the min/max teaching range of mean log-interval tempo. If pursued, write the exact formula/code in REVISION.md and hash-freeze before opening final10 CSV rows. No threshold/gate relaxation, motif change, covariance retuning, source extension or new architecture. Test original metrics on that same final10 alongside the revision. Preserve main failures. This step is optional if main evidence removes its value.

Source acquisition closes after this freeze; no further public operation is needed. Twelve-operation/35 MB/250 MB/650 MB/one-process-one-thread/deadline limits remain cumulative. Public-source result-text charges are conservative allowances rather than measured backend transport. Preserve partial parser attempts and unmeasured failed-pass peak.
