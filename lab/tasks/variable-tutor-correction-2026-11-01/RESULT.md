# Variable tutors can guide correction; simple covariance captures the useful gain here

The frozen experiment supports useful complete scalar-feedback learning from variable tutors in this explicitly constructed family. It does **not** support investing in the learned disk evaluator over a strong simple Gaussian baseline. The largest contrary result is that removing sensory–motor coupling makes a mean template successful on every case. Variation by itself did not create a universal need for a new evaluator.

This is a computational design example with supplied feature correspondence, nuisance rank, noise scale and harmless-variation semantics. It is not an acoustic/biological result, a reproduction of Gong's cancellation circuit, or a novelty claim. Independent scientific review is pending; all checks below are author checks.

## What was tested

Each of64new whole tasks has a six-feature tutor, an unknown two-dimensional harmless-variation disk, noisy tutor observations and a hidden four-action linear motor plant. The plant can reach the correct disk but its actions couple harmless and meaningful changes. Every actor sees the same stated tutor prefix and641scalar feedback slots; none receives the plant, target, gradient or per-rendition nuisance labels. Exact-feedback predictions and all actions were saved before non-oracle endpoint gold scoring. Acquisition means >=95%removal of initial true squared distance to the disk, not exact zero error.

The [protocol](PROTOCOL.md) and eight artifact pins were frozen at06:12:36Z on2026-11-01, before generating evaluation seeds2000–2063. First finite calculation finished06:04:12Z, ahead of06:15milestone. Main evaluation ran06:12:38–44Z. Development used three FIRST tasks and12other tasks; only one development revision was made. Evaluation cases/criteria/models were not repaired after scoring.

## Direct observations

Acquisitions out of64independently generated tasks; columns are repeated conditions on those same64tasks.

| Feedback objective | 3 tutors | 8 tutors | 32 tutors | 128 tutors |
|---|---:|---:|---:|---:|
| First template | 1 | 1 | 1 | 1 |
| Mean template | 0 | 0 | 0 | 0 |
| Regularized rank2Gaussian | 14 | 48 | 63 | 64 |
| PCA tangent residual | 10 | 47 | 63 | 64 |
| Learned finite disk support | 12 | 46 | 63 | 64 |
| PCA exemplar convex hull | 10 | 22 | 62 | 64 |
| Nearest exemplar | 2 | 5 | 14 | 31 |
| Absent / shuffled tutor | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 |
| Privileged true-error actor | 64 | 64 | 64 | 64 |

At32tutors the Gaussian acquisition rate is98.44%, Wilson95%interval[91.67,99.72]%; mean error removal99.05%. The paired acquisition increase from3to32tutors is76.56percentage points, whole-task bootstrap95%interval[65.63,85.94]. The frozen useful-correction/exposure criterion passes. These are conditional iidgenerator intervals, not biological population estimates or calibrated universal sample requirements.

The learned disk and Gaussian have identical32-tutor binary acquisition outcomes:63successes and the same single failure. The frozen >=10ppdisk-investment gain fails. Zero disk-only wins among64tasks gives a one-sided exact95%upper bound4.573%on the probability of a disk-only win, which bounds its acquisition-rate advantage and excludes the frozen10ppadvantage in this generator. The degenerate paired bootstrap[0,0]alone would not justify population equivalence. Absolute errors differ: mean endpoint error.00080943for disk versus.00086101for Gaussian. No absolute-error equality or general architectural impossibility follows.

## Consequential contrary tests

**Motor coupling:** Hold the exact tutor vectors/latent variation/noise/target actions fixed and remove C from x=mu+Uz*+(VQ+UC)(a-a*). Mean-template success changes0/64to64/64at32tutors. Its mean absolute endpoint error falls.12583926to.00020199; paired improvement.12563727,95%bootstrap[.11651364,.13477396]. Gaussian remains63/64. Both plants' true-error actors succeed64/64. Initial full errors can differ across plants because of finite support; the absolute endpoint comparison is therefore the clearest measure.

The reason is an actuator tradeoff, not a failure to average correctly. With infinitely many tutors and an unconstrained interior optimum, the mean objective chooses delta a=-(I+C^TC)^(-1)C^Tz*, sacrificing meaningful accuracy to reduce harmless offset. True off-plane error is norm(delta a)^2/4. Exact box optimization confirms the formula on52interior cases and handles12boundary cases; median infinite-tutor mean error remains.12822855. Setting C=0 removes this compromise. This standard quadratic fact explains the constructed effect; it is not new mechanism evidence.

**Training measurement noise:** With the same latent uniforms, raw noise arrays and motor plants, setting sensor noise to0makes Gaussian/tangent succeed64/64with only3tutors; with noise.08they succeed14/64and10/64. Three noncollinear noiseless examples identify the affine plane, but do not identify its finite extent: the learned disk then succeeds47/64and hull11/64. This separates noisy geometry estimation from finite-support estimation. The main high-exposure disk/tangent equality is consistent with the fitted boundary being inactive; it does not validate support recovery in general.

**Scalar resolution:** At nearest-.001query costs, fixed32tutors/.08sensor noise and the original plants, Gaussian success falls63/64to59/64; tangent/disk60/64. True-error feedback still succeeds64/64but reaches less precise endpoints. This demonstrates an implemented feedback/actor dependence, not a scale-invariant information limit; the declared methods use different fixed cost normalizations.

## Numerical reliability, failures and limits

[AUDIT.json](AUDIT.json) reconstructs all3,281,920main/contrary query costs exactly, all action paths exactly, and gold errors within1.45e-15. Mean/Gaussian/tangent box-constrained quadratic optima were reconstructed by81active-set enumerations: maximum actor objective gap7.83e-12. Thus the template failure and large exposure effect are not explained by those actors failing to optimize their stated quadratic objectives. Matched-intervention checks verify960literalarray equalities. Development audit separately covers538,440costs/180matchedarrays. Nonquadratic costs reuse their author implementation for replay; that is software integrity, not independent algorithmic validation.

The first contrary-development calls changed maximum RNG draw length32versus128and therefore did not retain the same tutor observations. Those `development_decoupled`/`development_noiseless` outputs remain as unmatched failed controls. The technical fix always draws128then selects prefixes; corrected `_matched` controls passed before freeze. FIRST's n16generation survives with its original `run_initial.py`; it is not silently relabeled the corrected generator. No numerical warnings occurred in these scientific processes. An ordinary awk context read was rejected by the existing shell-composition hook; bounded ordinary reads completed without changing controls. A later ordinary rg read of the large SCORES.json was rejected by its context-size bound; no workaround/payload reread followed.

**Read-budget compliance is not certified.** Post-hoc accounting found that lazy repeated NPZ observation access in the audit yields a conservative application read/decode/hash allowance421,697,685bytes, above the400,000,000cap. This is an upper allowance, not measured actual IO or proof of a421.7MBtransfer. A further14,857,660byte whole-bundle hash pass was proposed in the ledger but was NOTexecuted. Payload reads/hashes stopped on that finding; no scientific rerun or larger allocation followed. Frozen protocol/code pins were checked before main execution; prediction pins were already reverified in the saved audit. ARTIFACTS.json references those existing pins instead of claiming a new full-bundle SHA pass. Preserve this resource uncertainty alongside the results. Largest measured scientific RSS236,470,272bytes is below its800MBcap; provider/runtime IO and provider peaks remain unknown. Public usage7operations/THREEtargeted families/4MBcharged ingress includes the CAPTCHA failure; actual provider transfer is unavailable. See READ_LIMIT_STOP.md and RESOURCES.json.

The priors do substantial work: aligned Euclidean features, rank2, isotropic known noise, a convex disk of acceptable outputs and favorable reachable plants. Harmlessness is assumed, not inferred from tutor recurrence. A source distribution's density and the organism's acceptable set need not coincide. No biological tolerance labels, independent natural tasks, unknown-rank/noise calibration, nonlinear vocal plant, cancellation-circuit training or alternative architecture were tested. Extrapolation outside this family remains unrun. No old empirical payload/protected target was opened. All generated development/evaluation observations, endpoints, wrong-task controls and summaries are consumed and may not be relabeled fresh validation.

## Allocation decision and provenance

Bank the positive conditional teaching/exposure result and the negative disk-investment result. Close further metric/architecture tuning on these cases. The most useful next action is a fresh independent reviewer challenging the claim-to-information match, finite-boundary/actuator explanation and conditional inference using the saved bundle. A distinct biological or computational allocation would need new consequential evidence about what variation should be tolerated, rather than more fits to this consumed family. PI decides subsequent lab work; the continuing lab/heartbeat remains active above its reserve.

Closest checked primary families: [Gong etal., predictive cancellation](https://elifesciences.org/reviewed-preprints/111771), [Simard etal., tangent distance](https://papers.nips.cc/paper_files/paper/1992/hash/26408ffa703a72e8ac0117e74ad46f33-Abstract.html), and [Ho/Ermon, GAIL](https://arxiv.org/html/1606.03476). Learned evaluation, invariant distance and distribution matching are established ideas; this run neither implements GAIL nor establishes publication novelty. See [SOURCES.json](SOURCES.json), [ANALYSIS.json](ANALYSIS.json), [RESOURCES.json](RESOURCES.json), [README](README.md) and [freeze](FREEZE.json) for versions, resources, exact reproduction and limitations. No active jobs remain.
