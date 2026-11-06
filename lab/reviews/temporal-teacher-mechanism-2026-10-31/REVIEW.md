# Independent review: temporal teacher, corrective fidelity and metric coupling

Reviewer: research-only chat `01a1885c-3822-7bc0-88b7-e5fd7343299a`, distinct from the main investigator. Reviewed main study: `lab/tasks/temporal-teacher-mechanism-2026-10-31`. All numerical review work uses already consumed synthetic cases 400–407. Originals, protected observations and shared lab records are unchanged.

**Decision: accept the restricted numerical result and stop the current added-temporal-state necessity claim.** The population prototype supplies substantially useful feedback in this assay, but it sometimes prefers worse timing at imperfect content. The independent contrary test shows that generic feature-metric compensation can produce these preferences while the measured timing contrast remains distinct. Neither these failures nor the successful ordered-memory control establish a need for a new temporal mechanism. Preserve this result and its reproduction artifacts; do not launch another state/readout repair on this evidence alone.

## What was independently checked

The review began with an executable reconstruction of the reported 400 pair, before broadening the audit. `review_core.py` independently constructs sensory waveforms, integrates simultaneous Euler E/I equations and computes the 1200-coordinate prototype score. The pinned upstream `models.py` is executed separately for equation checks; the author's task integration, actor and segment-loss helpers are not imported. No teacher or readout is fitted.

`audit_logs.py` separately implements the fixed actor. It reproduces every proposal and all 37 retained decisions for all 64 case/critic histories: **238,208 scalar queries**, 3722 per history. This verifies how recorded scalar feedback drives the search. It does **not** independently recompute every recorded neural feedback value, and is not a rerun of the neural campaign. All recorded gold values are recomputed from an independent waveform-energy/prefix-integral calculation; direct samplewise waveform checks cover fixed query indices, each best visited point and final/reference programs. Maximum disagreements are 7.11e-15 for all logged gold and 3.55e-15 for direct cross-checks. All 260 explicit audit checks pass.

The audit verifies the 13 main freeze-file hashes, eight complete tuples and critic denominators, target waveform reconstruction from stored truths, the 64 distinct-order menu, scheduled durations and repeated-emission cases. Saved freeze/generation records and source ordering support generation after the freeze; a retrospective file audit cannot prove that no historical preview occurred. Tutoring itself is inspected in source and saved models, not independently rerun.

One documentation distinction survives: the actor actually chooses ties/improvements at 1e-14, as specified in the pre-main development revision and implemented in frozen code. Some protocol/configuration text says 1e-12; 1e-12 also appears in diagnostic tolerances. The independent replay uses the actual 1e-14 rule. This mismatch does not change the reproduced results, but the actual rule should be cited.

## Positive result and complete denominators

Acquisition requires error removal >=95%, final registered waveform MSE <=0.1 and stretch error <=0.02. Removal uses the common initial-shape/order 1/stretch 0.8 reference; that reference need not have been queried by the actor. Observable order is checked from the generated waveform, allowing equivalent identities in repeated-emission cases.

| Critic | Acquisition | Correct observable order | Mean error removal | Mean finalMSE | Final minus best-visitedMSE>0.01 |
|---|---:|---:|---:|---:|---:|
| Raw rate |0/8|1/8|10.984%|1.706528|8/8|
| Normalized rate |0/8|1/8|−0.153%|1.913658|8/8|
| Population prototype |4/8|7/8|86.269%|0.271229|7/8|
| Fixed-circuit prototype |5/8|8/8|96.105%|0.078055|4/8|
| Ordered sensory memory |8/8|8/8|99.9993%|0.00001308|0/8|
| Full sensory template |8/8|8/8|99.9993%|0.00001308|0/8|
| Static input moments |1/8|1/8|3.675%|1.812368|7/8|
| True-error oracle |8/8|8/8|99.9993%|0.00001308|0/8|

The population-minus-raw paired mean is 75.285 percentage points of error removal; a 10,000-resample common-case bootstrap gives 95% interval [52.744,94.852]. Fixed-minus-tutored prototype is 9.836 points, [−0.011,24.431]. These intervals describe eight synthetic whole tuples, not biological uncertainty or independent query trials. A population prototype is a useful restricted teacher here. The eight-case comparison does not establish that circuit plasticity is generally harmful or unnecessary.

For the population teacher, final/best visited MSE by case is 400: 0.040098/0.000100; 401: 0.112742/0.038943; 402: 0.186052/0.186052; 403: 0.040022/0.000097; 404: 0.018232/0.000048; 405: 0.272771/0.099612; 406: 0.040082/0.000077; 407: 1.459832/0.922653. Thus the seven worse-than-visited selections are real, including four successful acquisitions. Case 402 also shows a search limitation; 407 never visits a good complete solution. The local metric diagnostic cannot explain every acquisition failure or assign a fraction of total failure to one cause.

## Information and controls

The actor receives scalar cost, not target coordinates/order/stretch or gold error. Critics obtain the sensory waveform or neural response; target parameters used in the review grid are evaluator-only diagnostic labels. Saved logs and the independent replay support this separation.

Zero HVC does not remove recurrent temporal dependence. Existing E/I dynamics, quiet initial state, episode boundaries and event history can carry timing information before first/second moments pool responses in time. The tutor-specific mean/variance readout adds sensory target memory. In particular, the “unplasticized” control freezes circuit synapses while still learning that target-specific readout; it is not a no-memory control.

The full template stores the clean final 2200 ms sensory exemplar and registers its first detectable onset to the candidate onset. Ordered memory stores observed runs and their relative schedule. Both therefore use an explicit correspondence prior unavailable to a global-rate critic. The oracle alone is privileged by environment truth, but on these clean, reachable piecewise-constant tutors its objective equals the exemplar template. Independent scalar histories for ordered memory/template/oracle coincide. Their 8/8 performance is a sound positive control and no demonstrated advantage beyond template matching.

The favorable assay has a shared 4D content plan, six fixed production events, normalized gain, target order inside the original six-policy subset, a 64-policy expansion, clean tutoring, long quiet tails and detectable gaps. 35 continuous sensory renditions tutor source synapses; one final clean exemplar supplies the prototypes/templates. Critics share scalar query budgets, not equal information use, memory or compute. The review does not validate full acquisition under continuous/noisy natural song or neural feedback noise.

## Original 400 witness and its precision limit

At identical content/order and common onset 0, the independently rendered stored .8400000000000001 program has source cost 6.603257842954865e-5 and waveform MSE 0.0001001154352. Stored .8350000000000001 has lower source cost 6.498407159505790e-5 but higher MSE 0.0400977885334. The source therefore favors the worse program by 1.04850683449e-6. Independent/source trace disagreement is at most 6.40e-14. This is a finite local misranking; it does not show a global wrong minimum or loss of all timing information.

The frozen crossed grid did not reproduce 400's reversal because its literal target-minus .005 is .835, one binary ULP below the saved actor value. A separately declared two-encoding audit, preserved in `PRECISION_AMENDMENT.md`, shows that the change moves the third event by one 1 ms frame. Only waveform samples 400 and 484 differ. Literal .835 has cost 6.645813345798165e-5 and MSE 0.0437339783652: the cost now increases against the same .840 reference. The stored witness is valid for its rendered program but is sensitive to the rendering grid. It cannot support a smooth duration-gradient claim. No original float, actor log or grid was repaired or replaced.

## Frozen contrary test: content error can compensate timing error

`DIAGNOSTIC_PROTOCOL.md`, `review_core.py` and `crossed_diagnostic.py` were hash-frozen at 14:02:53 UTC, before the crossed responses. Each consumed case keeps its stored circuit, prototype, quiet reset, correct observable order and onset 0. Content interpolates from the true target to the population actor's acquired content at alpha 0, 0.5, 1. For each content, duration offsets are −.02, −.005, 0, +.005, +.02; two further candidates shift the second event by ±20 ms at target duration, preserving exposure. This gives 21 responses/case. The same 21 responses are tested on fixed circuit 400 only: **189 responses total**. Six predetermined response/feature comparisons agree with the pinned source within 8.33e-17 in feature coordinates.

All nonbaseline comparisons use independently rendered, onset-registered samplewise waveform error. There is no parameter fit or winner-dependent extension of the frozen grid.

| Circuit/readout | Content alpha | Worse-gold/lower-cost changes | Cases with a wrong preference | Robust changes at eps1e-8 | Robust changes at eps1e-6 |
|---|---:|---:|---|---:|---:|
| Tutored population |0|0/48|none|0|0|
| Tutored population |0.5|3/48|403,405,407|2|0|
| Tutored population |1|8/48|401,402,403,404,405,407|8|3|
| Fixed circuit400 |0,0.5,1|0/6at each alpha|none|0|0|

Here eps is an absolute per-query cost uncertainty bound; a gap must exceed 2 eps. These fixed sensitivity levels are not measurements of biological precision. The one fixed-circuit case cannot estimate an eight-case difference in local reversal rates. Exact-content zero cost is built into the prototype and supplies a weak positive control, not evidence of general corrective fidelity.

Let whitened content residual be `u=(m_base−m_tutor)/sqrt(V)` and the temporal feature change be `v=(m_changed−m_base)/sqrt(V)`. The unchanged squared feature cost obeys exactly

`Delta L = 2 mean(u*v) + mean(v*v)`.

For all 11 wrong preferences, `mean(v*v)>0`: the readout features distinguish the temporal change. The negative cross term outweighs this positive term. The finite residual/timing Gram determinants are also strictly positive; their normalized values are at least 0.96757. Thus these observed contrasts are not even collinear in the measured feature space. This supports metric compensation rather than an explanation requiring zero timing sensitivity along the tested contrast. It does not establish injectivity of the entire feature map, full-response sufficiency, a local Jacobian rank theorem or absence of information loss elsewhere.

The three acquired-content changes robust at eps 1e-6 are 402 duration −.02 (delta cost −1.06812e-5, delta MSE +0.185389), 407 duration −.02 (−2.22752e-6, +0.185345), and 407 gap −20 ms (−2.40482e-6, +0.072687). The last gives an exposure-preserving example. These additional cases preserve the metric finding despite 400's numerical-grid sensitivity. They are postvalidation checks of consumed cases, not a new holdout rate estimate.

A frozen elementary control makes the logical point without a neural model: `f(c,t)=(c+t,t)` is invertible. With true target (0,0) and content error c=.1, moving t from 0 to −.05 reduces squared feature cost from .01 to .005 while true squared error rises from .01 to .0125. All information is retained by this map. A bad correction therefore does not logically require absent timing information. This ordinary metric geometry is not a new theorem or model class. The actual neural-feature decomposition supplies its finite relevance here.

## Prior scope, reliability and scientific payoff

The cached primary [Gong et al. reviewed preprint111771](https://elifesciences.org/reviewed-preprints/111771), SHA256222eefc904fe92a4a05b6312986a29e41c265cf47637ac52027e797bb1ddfc63, already presents locally acquired error codes, error landscapes and an actor-critic song-copying demonstration with supplied syllable state/premotor timing. Removing HVC extends that information setup; it does not refute the published supplied-timing result. `PRIOR_CHECK.json` records selective primary-text inspection; this is not an exhaustive priority review. The main author's source notes identify Gretton mean-feature distances, Elman recurrence and duration/segment models; the reviewer did not independently reread those full works. No universal feature-identification, new temporal model or biological implementation claim is earned. Upstream code redistribution permission remains unverified because no LICENSE was established.

**Numerical reliability:** high for the reported finite aggregates, recorded scalar actor behavior, gold comparisons and local source-confirmed responses. Limits include retrospective generation provenance, unrecomputed full neural query costs, no independent retutoring, synthetic sample size, rendering discontinuities and uncalibrated feedback precision.

**Scientific payoff:** useful clarification and a reproducible restricted learning result. Recognition, corrective ranking and acquisition are different. Existing recurrent/prototype memory can teach much of this task; a clean registered template already solves it. The strongest new contrary evidence explains tested wrong corrections through metric coupling without requiring missing timing information. It narrows the mechanism interpretation but establishes neither a new biological fact nor a constructive general temporal teacher.

**Investment recommendation:** stop the present claim that these results require added temporal state and bank the finite result. No architecture successor is commissioned. A future investment would need a separately justified task where correspondence/noise demands defeat the matched template baseline and distinguish representation insufficiency from metric choice; that missing evidential reason is not supplied by another repair of this clean assay.

## Exposure and reproduction

The block began 13:52:07 UTC and ended before 15:22:07 UTC; one scientific process at a time, 2 BLAS threads. Largest recorded peak RSS is 475,856,896 bytes; precision-check RSS was not separately recorded. Review charge is 177,239,070 bytes, including a conservative 2 MB context allowance and encoded/decoded double charges. Inherited actual lineage 807,663,431 gives charged upper lineage 984,902,501 bytes, below 1 GB. There were zero network requests and no protected observations. `READS.json`, `INPUT_HASHES.json`, `EXPOSURE.json`, `CHECKPOINT_SUMMARY.json` and `MANIFEST.json` preserve accounting and hashes. `README.md` gives historical commands and explains why completed-input scripts must not be blindly rerun under the remaining 2,760,930-byte cap.
