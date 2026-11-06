# Independent review: bank the conditional result; close disk investment

Reviewer `01a195cb-5f1b-7770-adf6-49b1fd8da238`, distinct from author `01a195b0-e0ad-71a2-ae21-413e780d0453`. Registered START 2026-11-01T06:28:34.197Z. The first independent numerical calculation was saved at 06:31:12.262Z, before the 12-minute milestone. Main reconstruction and the prespecified contrary finished at 06:33:19.431Z. No author numerical module was executed/imported; this review used direct projections, observation-matrix SVD, independent KKT face enumeration and a separately implemented scalar-feedback actor.

**Decision:** accept the useful simple-covariance/exposure result, the conditional lack of disk acquisition benefit, and the constructed actuator explanation. Bank them and stop tuning this family. No correction to the author's acquisition counts, conditional bound or allocation decision is needed. A distinct fixed actuator-gain test makes both estimators much less successful, with the privileged oracle still successful. This reinforces the favorable-plant limitation without rescuing the disk evaluator or refuting the original frozen generator.

## What the independent calculations establish

The review reconstructs all 2,560 saved main endpoints from actual hidden plants and accepted actions, and all 2,560 endpoints in the three saved matched interventions. Direct Euclidean projection onto the *declared* disk reproduces every acquisition label. Maximum final-error discrepancy from author main scores is 2.23e-16; matched-intervention maximum is 4.45e-16. The 64 original noisy tutor matrices and motor matrices reconstruct exactly from their saved latent/noise/basis parameters; all supplied goal actions reach the declared disk to floating precision. These checks validate saved synthetic objects, not biological harmlessness.

| Main feedback objective | 3 tutors | 8 tutors | 32 tutors | 128 tutors |
|---|---:|---:|---:|---:|
| Gaussian | 14/64 | 48/64 | 63/64 | 64/64 |
| Tangent residual | 10/64 | 47/64 | 63/64 | 64/64 |
| Learned disk | 12/64 | 46/64 | 63/64 | 64/64 |
| Mean template | 0/64 | 0/64 | 0/64 | 0/64 |
| Privileged true error | 64/64 | 64/64 | 64/64 | 64/64 |

Absent and shuffled feedback each yield 0/64. At 32 tutors Gaussian mean true error is .000861014059 and disk .000809429299, compared with mean-template .125839260111 and initial mean .134008242323. Errors use arbitrary supplied Euclidean feature units. Passing >=95% removal is a practical relative criterion, not zero error or biological tolerance.

Gaussian's Wilson 95% interval is [.916658984,.997236458]; its paired 32-minus-3 acquisition gain is .765625, whole-task bootstrap 95% interval [.65625,.859375]. The original useful-correction rule passes. There are zero disk-only wins and zero Gaussian-only wins at 32 tutors, with exactly the same failure. For fixed methods and iid whole-task generation, the zero-win one-sided exact upper bound is `1-.05^(1/64)=.045729702331`. Since `p_disk-p_Gaussian = p(disk-only)-p(Gaussian-only) <= p(disk-only)`, this excludes the frozen .10 acquisition advantage under this generator. It does not establish equality, an absolute-error equivalence bound, superiority of every possible Gaussian implementation or a general impossibility result. The zero-width paired bootstrap is not the justification for the population statement.

At n32, independently reconstructed costs cover 328,192 scalar queries: first/mean/Gaussian/tangent/disk/absent/shuffled/truth on all 64 tasks. The maximum discrepancy is 3.065e-14, in shuffled feedback; Gaussian/tangent/disk discrepancies are <=3.00e-15. These values came from an SVD of actual centered tutors rather than the author's covariance eigendecomposition. All 80 polling rounds reconstruct exactly from saved feedback for **all 2,560 main trajectories**, including hull/nearest actors: 1,638,400 candidate proposals and 207,360 accepted-state rows, including the initial zero state. Each trajectory has 641 total query slots; the standalone initial query-action array entry was not separately asserted in this policy check. Independent hull/nearest distance formulas and all-n query-cost reconstruction were not run; actor replay for them is a software check, not independent validation of their objectives. All 192 n32 mean/Gaussian/tangent endpoint objectives are within 3.35e-12 of independent box-constrained quadratic optima. Thus their principal failures are not unexplained coordinate-search failures.

## Actuator account and saved interventions

The coupled infinite-tutor mean minimizes `||zstar+C delta||^2+||delta||^2`. An interior optimum therefore obeys `delta=-(I+C^T C)^(-1)C^T zstar`; its perpendicular true error is `||delta||^2/4`. Independent exact box enumeration gives median full true error .128228554918. The unconstrained formula applies to 52 interior cases and agrees with box actions within 7.78e-16. The remaining 12 cases use box solutions. This is the standard quadratic compromise between harmless displacement and meaningful error, not a learned biological mechanism or new theorem.

For the author's coupling intervention, 640 invariant source/goal/basis/coupling arrays match literally; the changed plant/offset equal the specified VQ-only intervention exactly. Reconstructed mean-template success changes 0/64 to 64/64, with mean absolute error .125839260111 to .000201985618. The paired mean decrease .125637274492 has bootstrap interval [.116513642547,.134773963522]. This does not require a common initial-error denominator across plants.

For zero training noise, 704 invariant arrays match literally and the clean tutors reconstruct exactly; Gaussian/tangent at three tutors become 64/64, disk 47/64 and hull 11/64. Three generic noise-free points identify an affine plane, not its finite support. For rounded .001 feedback, 768 invariant arrays match; reconstructed Gaussian/disk/truth acquisitions are 59/60/64. These saved controls support the limited noisy-plane and implementation-precision interpretations. Their query-cost/actor replays were not independently rerun.

All 64 n32 disk endpoints lie inside the *estimated* disk, but this is not a global inactive-boundary result: 792 saved queries across 60 cases lie outside it, and disk/tangent full paths are identical in 59/64 cases. Their final errors and acquisitions agree. Neither this fact nor successful learning establishes accurate support recovery outside the reached endpoints.

## Distinct contrary: keep tutors fixed, weaken meaningful actuator gain

The [review plan](REVIEW_PLAN.md) fixed this intervention before its numerical outcomes: replace VQ by **.1 VQ**, keep UC, the same 32 tutors, center, plane, harmless disk, raw noise and target actions, and reset offset to preserve reachability. Retain the exact 641-slot actor. All 64 consumed cases were used, with no gain sweep, case selection or repair. This changes the motor-plant class, not tutor information or acceptable-output semantics. It is a postvalidation controlled diagnostic and does not replace the original test.

| Feedback | Original acquisitions | Changed-plant acquisitions | Changed-plant mean final error |
|---|---:|---:|---:|
| Gaussian | 63/64 | 6/64 | .001093112570 |
| Learned disk | 63/64 | 5/64 | .001773507100 |
| Mean template | 0/64 | 3/64 | .005228258211 |
| Privileged true error | 64/64 | 64/64 | 1.0611e-12 |

Disk-minus-Gaussian acquisition is -.015625, prespecified whole-task bootstrap interval [-.046875,0], with zero disk-only wins and one Gaussian-only win. The .10 gain criterion still fails. Gaussian's exact box optima also succeed on only 6/64; its actor objective gap is <=2.71e-12. This failure survives solving that stated feedback objective and is not explained by inadequate scalar-query optimization. Mean's actor has a larger worst objective gap (.0007602), but both its actor and exact box optima acquire 3/64. The disk's nonquadratic optimum was not independently solved.

The relative acquisition drop needs context. Median initial error is .001439035959; mean initial error changes .134008242323 to .013524870288, with 19 initial outputs beyond the true disk. Gaussian's mean absolute endpoint error increases only 1.2696-fold, and disk's 2.1911-fold. Mean's absolute error decreases sharply despite only 3 relative acquisitions. Thus the comparison demonstrates fragility of this particular complete-correction target under altered actuator gain and fixed noisy estimation; it is not evidence that the absolute errors grew by the acquisition-rate ratio, or that disk-vs-density mismatch uniquely causes failure. The unchanged oracle establishes reachable correction under the same query budget. No alternative estimator, biological assay, new architecture or actuator-gain tuning was earned.

Contrary actor queries use only feature outputs and the fitted observation model; privileged true error is confined to the labeled oracle and subsequent diagnostics. Contrary gold errors were computed after each completed actor and held in memory before joint serialization; this review does **not** claim a new prediction-before-gold archive chronology. Inputs were already consumed and the intervention was fixed beforehand.

## Information, chronology and scope

Static inspection of the frozen source shows that each model fit receives only its stated nested tutor prefix and supplied sigma/rank. Non-oracle feedback uses that fit and the current sensory output; the hidden plant serves only the action-to-output query. The current target, true center/plane/radius and gold errors do not enter non-oracle evaluation/acceptance. Wrong-task feedback uses a separately seeded tutor model. All conditions are repeated measures on the same 64 independently seeded whole tasks, not extra independent observations. Stored arrays include hidden parameters, but storage does not imply an actor input; no hidden-information leak was found in the inspected path.

All **eight frozen code/protocol hashes** and **four saved prediction-archive hashes** match. Freeze says 06:12:36Z; main saved-index time is 06:12:41Z, with task start/finish records 06:12:38–44Z. Source saves observations/predictions and index before non-oracle gold scoring. This is consistent with the claimed ordering and the PI's separately verified native execution. These files and current digest matches do not independently prove historical wall-clock causality or exclude arbitrary unrecorded prior activity. No historical observation-archive SHA exists; this reviewer did not fill that gap or claim retroactive certification. The initial unmatched RNG controls and their prefreeze fixed-128-draw correction remain preserved.

Feature correspondence, rank two, known isotropic noise, Euclidean units, harmlessness, disk family and favorable reachable plants remain supplied. A density estimate is not itself a biological acceptability law. The evidence concerns this explicit mathematical task. Gong circuit reproduction, unknown rank/noise calibration, natural learning, general support identification and publication novelty remain unestablished. No new literature/source operations or empirical data were used; existing prior-work pointers are inherited, not independently re-searched.

## Resources and unrun work

Separate reviewer conservative scientific read/decode/hash allowance is **226,206,433 / 240,000,000 bytes** including the first calculation, selected single-member reads, four prediction hash reads, eight code pins and 10MB for scientific text/JSON/directories/failed reads/closeout. Largest measured scientific RSS is **218,136,576 / 500,000,000 bytes**; FIRST used 43,892,736. One scientific process and numerical thread at a time, zero public operations/ingress/new dependencies/services, no numerical warnings and zero jobs remain. This is an accounting allowance, not measured kernel IO; runtime/provider internals and rejected-call peaks are unknown. The numerical work finished well before the hard deadline. See [RESOURCES.json](RESOURCES.json) for exact components.

The author's conservative allowance **421,697,685 versus 400MB**, actual IO unknown and compliance **UNCERTIFIED** remain unchanged. Its proposed 14,857,660-byte full hash and second reproduction were unrun. This review validates selected saved science with a separate allocation; it cannot retroactively certify the author's resource use.

Unrun: second full author regeneration; historical observation SHA; independent hull/nearest cost formulas; all-n query-cost reconstruction; independent query replay of the three author interventions; disk nonquadratic optimum in the changed plant; new biological evidence or unknown rank/noise/nonlinear-plant inference. These omissions do not affect the verified primary binary comparisons or the stated contrary's Gaussian box result. Further tuning on these consumed cases is not recommended. The continuing lab and its same active heartbeat are PI-owned and remain active across this review endpoint; all protected targets/exposure/freezes/failures survive.

Artifacts: [FIRST_CALCULATION.json](FIRST_CALCULATION.json), [RECONSTRUCTION.json](RECONSTRUCTION.json), [DERIVED_SUMMARY.json](DERIVED_SUMMARY.json), [CONTRARY.json](CONTRARY.json), [PINS_CHECKED.json](PINS_CHECKED.json), [README.md](README.md).
