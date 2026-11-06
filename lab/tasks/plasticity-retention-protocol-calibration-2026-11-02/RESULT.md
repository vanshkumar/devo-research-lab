# Calibration complete; recommend CLOSE for this main-campaign proposal

**Original-scale renewal/replay and full old-function scoring are cheap and numerically checked. No matched-retention benefit is earned. Recommend closing this proposed main campaign rather than funding a setting/frontier search.** The broader scientific question and the PI's native goal remain unfinished. [Contribution decision](CLOSE.md).

## Actual calculation

ONE already consumed seed1729 teacher/stream, original20inputs/100-LTUteacher/5-ReLUlearner,100tasks×10,000examples. Source-CBP step.01/decay.99/effective direct-expr maturity10/replacement1e-4/adaptable_contribution. SGD receives the same step size. Each neural arm receives the same current observation, same pre-insertion reservoir example and exactly1,999,999gradient steps, with GnT after each CBP gradient. The506-record reservoir is replacement-independent. A separate677-record packed-array LRU sees only actually observed pairs, with the observed-label mean on misses. No scorer labels enter a learner.

| Feasibility arm | First1,000/task acquisition MSE, all100tasks | Mean all-old risk over99boundaries | Final old risk,99contexts | Mean risk immediately after each task |
|---|---:|---:|---:|---:|
| SGD+replay | 1.219456 | 1.780012 | 2.681099 | .848818 |
| CBP+same replay | 1.157860 | 1.911251 | 2.060966 | .702990 |
| Bounded exact observed-input cache | .097554 | 1.465596 | 2.306908 | 0 |

The cache has996,800hits/3,200misses in1Mexamples. CBP performs1,017unit replacements. Average old risk weights earlier contexts equally at each boundary, then boundaries equally; final risk is a different horizon. Age1–9/10–49/50–99and changes from initial competence are saved. Cache is stronger on the two fixed averages but worse than CBP on terminal and old-age retention; these are development observations, not independent superiority/equivalence results. Do not select a favorable retention horizon after seeing the reversal. Target support variance is2.9700303711; normalized scores are saved, not used to redefine a material margin.

The full pair+cache+all-old scorer takes50.3423s, maximum34,816,000bytesRSS. Timed neural learning costs: SGD10.3073s; CBP25.4690s. All32-point full supports at every boundary cost2.0016s across all three models. Cache learning/lookup costs11.0986s. [Measured summary](FULL_SUMMARY.json), [complete matrices/snapshots](FULL_STREAM.json).

## Numerical evidence and limits

[REFERENCES.json](REFERENCES.json) passes four exact-rational utility/renewal cases, four111-parameter scalar/finite-difference gradient checks, three full-support/constant-prediction scorer checks, exhaustive AlgorithmR subset inclusion and eight cache events. Every proposed neural control path actually executes on200consumed source observations. Source reset order, strict maturity, zero-replacement early return and pre-gradient features/post-gradient weights are tested.

[AUDIT.json](AUDIT.json) separately reconstructs all323,200saved neural predictions, maximum risk gap1.07e-14; final-cache reconstruction is exact. This is within-investigator independent implementation, not distinct scientific review. A20,000-gradient SNP timing prefix executes in.692984s; its69.30s/2Mgradient price is linear EXTRAPOLATION only. No fullSNP/random frontier or main evaluation was run.

The4KiB calculation is a conditional algorithm-core budget: CBP numeric state+506pairs=4,092bytes; cache pairs+four64-bit scalars=4,094bytes. Actual packed-cache arrays occupy4,202objectbytes, and actual serialized neural RNG states exceed7.5KB. Python/process state and common random tapes are not free total-storage certification. A fair main storage result is UNRUN. This extra neural RNG state cannot be hidden in a memory-efficiency claim.

## Source/contribution gate

The [CVPR2024paper's arXivv2 primary text](https://arxiv.org/html/2312.00600v2) now verifies joint acquisition/forgetting analysis with replay and two peer learners, closing the generic joint-benefit story. The source-specific selective-versus-random renewal residual is narrower and not exhaustively resolved. [PRIOR_GATE.md](PRIOR_GATE.md) preserves scope/access failures. Pinned original GnT/CBP equations remain exact previous-source artifacts. New requirements matches its Git blob; provider-normalized CBP config/AdamGnT/grid-driver files FAIL byte identity, and their actual/expected hashes are retained. Original-Torch/published-curve reproduction remains UNRUN. JSON's maturity_threshold100 versus runner's mt/default10 and mean-reset-before-compensation are explicit repository facts, not alleged published-result errors.

## Disposition and accounting

Recommend CLOSE because this bounded calibration supplies no positive investment evidence beyond known generic tradeoff work and a strong finite-support cache, with horizon and storage qualifications still preventing the proposed claim. Compute is affordable; a main design is not funded or launched. This is not proof of no effect or a closed broader lab question. Main contribution, common attained-retention region, balanced selection, independent teacher uncertainty/material-effect discrimination and distinct scientific review remain UNRUN; no another-calibration recommendation is left as the only output.

TwelveNEWpublic operations in TWO named programs are exhausted.100MBNEWingress is conservatively charged as the full allowance, actual provider/failure ingress compliance UNCERTIFIED. Separate additional read/hash/decode accounting and all failures are in [RESOURCES.json](RESOURCES.json). Earlier30ops/58MBingressUNCERTIFIED/100MBseparate read/consumedteacher/ONErevision remain additive. This task used ONE pre-main revision before outcomes. No new teacher/data examples, empirical/protected-oldraw access, dependency installation, paid compute, shared edits or native goal. All actual commands have finished; jobs0. [README](README.md) gives reproduction; [proposed learning](PROPOSED_LEARNING.md) is for PI integration.

The single terminal report was DELIVERED to current registry PI01a19efc-5590-73d2-910e-6920a3a81eaf without overrides; actual response returned the same threadId/isError=false. STATE/TERMINAL_REPORT record delivery. Jobs0; no acknowledgement wait or science restart.
