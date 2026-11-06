# Independent review: accept the fixed benchmark, narrow the mechanism claim

2026-10-31 local. Reviewer01a194fc-0a4f-7192-b2b3-c665d45ef086 is distinct from both source authors. **Accept numerical reliability, bank the failed cue increment, and close further archive fitting.** Common decay weakens the specified known-effect assay; removing common decay still leaves poor physiological detection. These data and models do not establish absent associative updating, equivalence, or a unique habituation mechanism. No new-main-model repair is recommended.

## What was independently reconstructed

The offline reader implements the SPSS byte-code/dictionary format and parses the cached log directly. It imports no author helper. The106,395byte dxpb3v1ZIP matches MD5 and SHA256 in the cached provider listing; source license linkage is CC-BY4.0. [SOURCE_MANIFEST](SOURCE_MANIFEST.json) and [FIRST_CALCULATION](FIRST_CALCULATION.json) contain source pins and actual command output. Original source: Mertens et al.(2019), [paper](https://doi.org/10.1016/j.jbtep.2018.09.007), [Experiment2](https://osf.io/dxpb3/).

Both SAV exports and the log share60unique IDs and matching counterbalancing. The sole blank SCR condition is PP120, with18missing extinction measurements; only that channel is excluded. Raw ratings match all1,980acquisition/extinction SAV entries. Every participant has15acquisition cues,18extinction cues and3later shock rows; no shock row is in extinction. All prefixes contain the first observation of each cue in the first3positions, leaving15predictions. The hash split independently recovers40development/20evaluation IDs, with1/109/110forced development. Physiology retains39/20people; expectancy40/20. Eight participants have all-zero extinction physiology, including2evaluation people. Missingness and zeros are handled as declared.

The actual SCR syntax names extinction cue features6–11 and divides nanoS by1000, recodes amplitudes<=.02microS to0, then applies full-record range correction/square-root for the published analysis. The lab's primary forecast instead square-roots thresholded microS without future range normalization; its sensitivity scales by the past acquisition maximum. All4,665finite supplied scoring checks reconstruct. The actual source syntax/README are saved in SOURCE_SYNTAX.json/SOURCE_README.txt. Supplied physiology was not rebuilt from high-rate traces. The paper's reinforcement/window definitions remain source descriptions: this review does not independently certify shock hardware, event elapsed time or1–8s feature extraction. The README explicitly places approximately9GBraw physiology off-archive; it was not requested.

Independent finite-grid fitting recovers all main parameters, acquisition-US priors, scale refits, and the rejected pooling revision. All9main and5author-contrary pins pass. All900main plus900static-comparison forecast rows reconstruct exactly, including observed values and cue/occurrence alignment; all280main and120static-comparison participant losses match exactly. Main bootstrap intervals and12static bootstrap endpoints match exactly. Future-suffix replacement changes no forecast; alpha0nesting and constant initial-cue limiting cases pass. See [RECONSTRUCTION](RECONSTRUCTION.json), [FINAL_VERIFICATION](FINAL_VERIFICATION.json), and the executed isolated reproduction in reproduction_audit/.

| Frozen outcome | Common MSE | Cue-update MSE | Cue-update error change |
|---|---:|---:|---:|
| Physiology, square-root microS |0.06703996|0.06942762|+3.5616%|
| Physiology, past-acquisition scaled |0.19533889|0.19594671|+0.3112%|
| Expectancy |0.10752266|0.10752266|0%|

Primary common-minus-update gain is−.00238767, conditional participant-bootstrap95%interval[−.00550239,−.00012661]. Scaled gain is−.00060782[−.00150944,+.00024274]. Expectancy's zero difference follows selection of alpha0; it is not an equality confidence bound. Every original utility gate fails. Source-mean expectancy MSE.10532552slightly beats the parametric accounts. Static pooled-prefix comparisons also reconstruct: static MSE.07032598/.20139530/.13542354for primary/scaled/expectancy, all worse than their common curves. This weakens a pure static-denoising explanation, without identifying the biological process.

The bootstrap conditions on development selection/fits and observed participants; it does not propagate source-fitting uncertainty or certify population coverage. Inclusion differs from the publication's nonresponse filtering. The cue law could also describe cue-specific expression; observed forecasts do not identify latent associative storage.

## Highest-value contrary test

The author's400conditional controls were independently regenerated with their saved seed and refitted grids. Every saved scalar, selected alpha, bootstrap-lower indicator, full gate and oracle separation matches exactly. Original null/known-alpha1full-rule counts are2/2of100physiology and0/56of100expectancy. This verifies the reported weak assay rather than repairing it. [CONTROL_RECONSTRUCTION](CONTROL_RECONSTRUCTION.json).

The independent [plan](CONTRARY_PLAN.md) and [implementation freeze](CONTRARY_FREEZE.json) precede the new diagnostic. One matched counterfactual sets common k=0instead of the source k2physiology/k1expectancy. It retains q, alpha1, fixed observed prefixes, nominal20evaluation cue orders, development residual-rank copula, positive frequencies, original fits/baselines/gate, and paired seeds. Nulls are retained. This is a consumed-source synthetic diagnostic, not a new biological experiment or evaluated forecast recipe.

For an unchanged-q/kcommon comparator, cue-update minus common prediction is exp(−kr)(A_c−A_minus)(exp(−alpha n_c)−1). Common decay directly suppresses the cue signal; the floor cancels in this difference. Separately profile the common q/kgrid against the exact generator mean to allow its best approximation. Let S be that mean squared separation and N the exact marginal observation-noise MSE. The ideal-mean expected fractional gain is S/(N+S). This is a comparison within the specified generator/family, not a universal power bound or a calibrated biological signal-to-noise ratio.

For physiology the hurdle generator has positive probability p and conditional positive mean m=mu/p above threshold t=sqrt(.02), giving variance p[m²+(m−t)²]−mu²; expectancy variance is mu(1−mu)/8. Correlations affect finite detection, which is simulated using the original copula. The noise family stays fixed across k conditions, but its mean-dependent variance changes; absolute noise variance is not held constant.

| Independent matched control | Mean ideal oracle gain* | Full-rule alpha1 detection | Corresponding null |
|---|---:|---:|---:|
| Physiology, source k2 |0.505%|5/100 [2.15%,11.18%]|1/100|
| Physiology, k0 |4.522%|9/100 [4.81%,16.23%]|0/100|
| Expectancy, source k1 |14.342%|57/100 [47.22%,66.27%]|1/100|
| Expectancy, k0 |76.322%|100/100 [96.30%,100%]|0/100|

*Mean of100conditional oracle fractions on development-donor prefixes mapped to the evaluation input orders; brackets are finite-replicate Wilson95%intervals for detection. These are independently seeded runs, so the source-kcounts differ from the exact original-control reconstruction above. Paired physiology outcomes:3both/2source-only/6k0-only/89neither. Expectancy:57both/43k0-only.

On the exact development physiology designs, S increases from.00027729to.01539800when common decay is removed, a55.53-fold increase; N also rises from.07206589to.31965823. The ideal fraction increases from.3833%to4.5956%. For the actual consumed evaluation prefixes it increases from1.1996%to7.9078%, showing dependence on the prefix distribution. Under development-donor control designs, removing common decay therefore makes the cue means more distinct but leaves low finite physiology sensitivity. Expectancy is much better separated in the k0counterfactual. All800new records and exact source-design oracles are in [CONTRARY.json](CONTRARY.json); [CONTRARY_SUMMARY](CONTRARY_SUMMARY.json) is compact.

**Inference:** rapid common decay is a consequential masking factor for this chosen contrast-decay alternative. It does not fully explain weak physiology detection: under the retained prefix/noise assumptions, detection remains low even without it. The physiological negative cannot support absent updating, and the favorable expectancy counterfactual cannot be promoted into an empirical fit. Neither alpha1nor this noise law is independently established biological truth. Scale-specific synthetic recovery remains unrun.

## Consequence, limits and exposure

The reliable result is a failed added-forecast recipe and a limited conditional advantage for a common time course. The source paper already distinguishes expectancy/physiology and uses a safety cue; no novelty claim is earned. Close additional rate/architecture/scale repair on these consumed participants. A consequential future mechanism test needs separately justified independent observations or perturbations that constrain expression versus updating, with a discriminating assay demonstrated before interpreting a negative result.

This review decoded all60complete SAV cases again and, additionally, all2,892raw log rows/all10columns, including startup responses, latency and later raw reinstatement entries for all60. Those raw-log observations are now consumed even where not scored; this extends the earlier raw-log audit's acquisition/extinction scope. Separate questionnaire DAT files and the workbook were not opened. All earlier failures, paper-summary exposure and protected targets remain intact.

Additional review charge120,000,000byteswithin140,000,000;0publicoperations/0ingress; largest measured RSS46,809,088byteswithin500,000,000. One early CLI dispatch failure has unmeasured peak and a retained1MBread charge. Prior117MBread/7,151,937ingress/16operations/providerpeakunknown are preserved, yielding237MBadditive read lineage. See [RESOURCES](RESOURCES.json) and [FAILED_PASSES](FAILED_PASSES.md). All processes completed; jobs0. Full all-stage replay wrapper is unrun, while each original independent stage and its isolated audit mode executed. PI retains allocation and the same active heartbeat.
