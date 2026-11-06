# Count pooling preserves a cohort advantage, but joint superiority is unresolved

2026-11-01. Author `01a19734-d25e-7bb3-8e81-85110583eb56`, start21/samecycle13. This is postvalidation work on the same24 consumed animals. Distinct independent review is pending. All work remained task-local; manuscripts, historical campaigns and earlier author/review outputs were read-only.

The saved RNN has3.62% lower joint count–success energy score than saved growth, but the paired animal and five-laboratory intervals cross zero, only12/24animals improve, and removing Hofer reverses the point contrast. The small point advantage also occurs with correctness removed. Thus the RNN's improved count-pooled cohort accuracy is real under that changed functional, but does not establish reliable joint forecast superiority, calibrated acquisition prediction or a uniquely useful learning mechanism.

## Evidence and the fixed comparison

[FIRST_CALCULATION.json](FIRST_CALCULATION.json) independently verifies all48 original RNN/growth ensemble pins, all24 RNN arrays against the earlier independent reconstruction, and integer success/opportunity identities. Each method has24×512×6×2 paired endpoint cells. There are34378 actual exact100 opportunities; omissions remain incorrect. Original first4000rows/animal,1000prefix/3000future/six500-opportunity bins and equal side/bin/animal weights are preserved. No original raw rows were reread.

[DESIGN.md](DESIGN.md) and complete [comparison objects](COMPARISON_OBJECTS.npz) were frozen13:11:52Z before any new joint or growth count-pooled score. Each cell maps its paired opportunities N and successes K to `(K,N-K,500-N)/500`. The Euclidean energy score, normalized by sqrt(2), evaluates this joint count–success distribution. Its exact finite512-point empirical forecast score is averaged equally across sides, bins and animals. The one additional reference is count-only CRPS for N/500 using the same draws. Neither a model nor a loss scale was selected after these results.

This score evaluates the **joint count/success law within each bin/side**. It does not evaluate all cross-bin or cross-side dependence in an entire generated trajectory. Paired (N,K) and (N,K/N) contain the same information here because every observed/generated N is positive. This establishes adequate saved pairing for the declared question, not a likelihood or posterior-calibration certificate.

## Joint result and its uncertainty

Energy/CRPS scores below are normalized opportunity-proportion scores, **not percentage-point accuracy errors**. Lower is better. Positive growth-minus-RNN favors RNN.

| Fixed calculation | RNN | Growth | Growth minus RNN | Paired-animal95% percentile interval | Five-lab CR1/t95% sensitivity |
|---|---:|---:|---:|---|---|
| Main joint energy |0.05092214|0.05283320|0.00191106|[−0.00257953,0.00704309]|[−0.00804996,0.01187208]|
| ONE count-only reference |0.04243107|0.04472119|0.00229012|[−0.00190436,0.00711305]|[−0.00640845,0.01098868]|

The main relative point gain is3.617%; the count-only gain is5.121%. These different scores must not be subtracted to infer an isolated correctness contribution. Main animal Student-t95% is[−0.00331342,0.00713553]. Bootstrap uses20000 paired animal draws/seed2026110101. These are descriptive fixed-recipe, selected-cohort intervals; postvalidation functional selection and consumed observations prevent untouched-validation interpretation. They do not certify interval coverage or new-laboratory transport.

Main per-lab contrasts are Angelaki−0.00173530 (5animals), Churchland−0.01416037(2), Cortex−0.01999923(1), Hofer+0.00823917(10), MrsicFlogel+0.00341169(6). All leave-one-lab-out contrasts are positive except removing Hofer:−0.00260902. Five unequal clusters give limited environment information, not laboratory equivalence.

Numerical integration is a separate issue. The fixed U-statistic correction changes the main contrast to0.00192114, only0.00001008 above the primary V-score contrast. Paired delete-one particle MC SE is0.00032642;8disjoint64-particle U-contrasts range0.00101514–0.00306632, all positive. The approximate MC-only95% range around the U contrast is[0.00128136,0.00256092]. Particle resolution is smaller than animal/lab variation; none of these quantities is biological uncertainty or calibrated posterior coverage. Full objects/terms/pseudovalues are in [RESULT.json](RESULT.json) and [SCORES.npz](SCORES.npz).

## Both original and changed accuracy functionals

| Method/functional | Population curve MAE(pp) | Individual equal-side MAE(pp) | Individual side MAE(pp) |
|---|---:|---:|---:|
| RNN, original mean of particle ratios |6.969991|9.028951|18.039431|
| Growth, original mean of particle ratios |2.278105|6.966767|17.879177|
| RNN, pooled generated successes/opportunities within each animal/bin/side |1.052554|5.888673|17.448593|
| Growth, same count pooling |2.269678|6.926479|18.159034|

The changed-functional RNN cohort point advantage over growth is1.217124pp. No interval/coverage claim was earned for this MAE contrast; the joint-score intervals concern a different functional and cannot be transferred. Earlier conditional sampled MAE0.619495pp remains the prior tracking diagnostic, not an autonomous competitor in this test.

Both methods have negative count–accuracy covariance in **all288cells**. Ratio-pooling identity errors are below1.82e−15probability units. Growth's population MAE barely changes under pooling, yet its six cohort-bin forecasts switch from overprediction in every bin to underprediction in every bin. A similar MAE therefore does not mean a similar forecast or negligible count coupling. RNN's mean-opportunity prediction error is29.891counts per animal/bin/side versus31.238growth; mean-success prediction error is14.049 versus13.577. Those descriptive errors and the count-only reference do not identify a unique source of the joint score contrast.

## Reconstruction and limitations

[FINAL_AUDIT.json](FINAL_AUDIT.json) uses separately written counts-to-category reconstruction, SciPy unordered pair distances, a sorted scalar count-CRPS identity, four complete scalar integer-count distance sums, exact delete-one checks and independent scalar bootstrap/cluster reconstruction. All576 joint/count cell scores agree within5.552e−17; uncertainty differences are below6.1e−18. Integer/paired-asset/pin/timestamp checks, permutation invariance and analytic point-mass limits pass. A fixed-count correctness change has positive joint score and zero count score, so the declared joint score does retain correctness information. This is within-author implementation verification, **not distinct independent scientific review**. Warnings are empty.

The endpoint records identify finite joint predictive scores for the observed counts/successes and the arithmetic effect of count weighting. They do not separately identify trainer, feedback, learning, attendance or biological causes. Session opportunities/boundaries are historically conditioned inputs; biological first exposure and unobserved stopping/attendance remain uncertified. Source-parameter uncertainty, full-path joint scoring, coverage, new held-out observations and count-pooled MAE uncertainty remain UNRUN. Equal prefix weights are not a future-likelihood-conditioned posterior. No primary gate or source/external release was changed.

Firstnumeric13:05:20Z, design freeze13:11:52Z, main output13:12:08Z and final audit13:14:33Z all precede the original deadlines/hardstop13:56:15Z. Native first/freeze/main/audit exits are0; jobs0. Final conservative read/hash/decode allowance is123783434/200000000bytes; peakRSS148275200/800000000bytes. One scientific process/thread, zero publicops/downloads/ingress/new raw rows. Physical I/O remains unknown. Failed start20's zero numeric payload and5000000byte allowance remain preserved; an environment-recording inline command was denied before execution and then run as a scoped file. All prior resources, including author220MB/nativeexit120 and separate review347704984bytes/393756672RSS/failed compiler pass/physical-I/O unknowns, remain historical and separate.

## Investment recommendation and precise wording

Commission a fresh independent review of the paired-output provenance, score interpretation and consequential count-only alternative before integrating this result. Bank the small, uncertain relative joint advantage without treating the1.053ppcohort summary as a repaired acquisition forecast. Further fitting, a new gate or more tuning on this consumed cohort is not supported by this result.

Suggested wording after review: “Applying the same count pooling to frozen growth forecasts gave population-curve MAE2.270pp versus1.053pp for RNN. A separately frozen postvalidation score of paired opportunity/success distributions gave RNN a3.62% point improvement, but its animal and five-laboratory uncertainty intervals included zero; only12of24animals improved, and a count-only reference also favored RNN slightly. These results retain the count-pooled cohort agreement while leaving reliable joint acquisition-forecast superiority unresolved. They neither replace the original expected-ratio target nor repair its failed gates.”
