# Preregistered causal-consequence test

Frozen before generating ANY new teacher/stream, after REFERENCE.json PASS at 2026-11-03T02:21:52Z. This is the single substantive design; zero substantive revisions used. It is not a setting/frontier search or a published-curve reproduction.

## Claim and alternatives

Question: does postponing the mean reset in the pinned source's otherwise literal renewal update produce a material practical retention improvement, without sacrificing acquisition, on the original repository's small regression task? Author intent/historical deployment remain uncertified. The hypothesis is a conditional mechanistic consequence. Strong alternatives: compensation is negligible for low-utility units; it merely exchanges acquisition for retention; it only preserves a local mean and not old functions; random renewal plus the same compensation/replay does as well; ordinary replay or a bounded observed-input cache dominates.

The intervention uses already held, updated exponential mean and POST-gradient output weight, compensates the output bias, then zeros that mean. Baseline resets the mean first. All other source operations/defaults remain: step .01, decay .99, strict maturity >10 (JSON100 versus direct-expr effective10 remains disclosed), replacement1e-4, adaptable_contribution, Bernoulli replacement/accumulate=False, PRE-gradient features, POST-gradient weight magnitudes, fresh Kaiming incoming weights, zero incoming bias/outgoing weight/age. No true old labels, support enumeration, future inputs, task boundary signal or scorer state enters a learner.

## Fixed finite design

EIGHT independent whole teacher/stream realizations, seeds 240001 through 240008 inclusive, generated only after this freeze. Seed1729 remains consumed development and is not evaluated. Per teacher: original 20 binary inputs/15 JOINTLY resampled slow bits every10,000 examples/5 fresh bits; fixed100-LTU target with exact source threshold and bias; 5-ReLU111-parameter neural learner. 100 contexts/1,000,000 current examples. Preserve original extra generated101st block/1,010,000 fast draws and charge it as consumed. Generate initial neural weights after the data draws, with the same source distributions. Python float64/RNG is conditional source-equation execution, not Torch float32/author RNG or the paper's distinct one-bit-flip prose.

Within each teacher all neural arms share initial weights, current data and reservoir random draws. Method randomness uses seed seed+1000; event RNG seed+1011. Replay sampling seed+2000 and AlgorithmR insertion seed+3000. New teachers have distinct parameter/data/method realizations. No selection or adaptation across teachers.

EIGHT arms, all reported:

1. CBP literal, current-only (1M gradients).
2. CBP retained-mean, current-only (1M gradients).
3. CBP literal plus one replay per example (1,999,999 gradients).
4. CBP retained-mean plus same replay (1,999,999 gradients).
5. Uniform-score random renewal literal plus same replay (1,999,999 gradients).
6. Uniform-score random renewal retained-mean plus same replay (1,999,999 gradients).
7. SGD plus same replay, no renewal (1,999,999 gradients).
8. Bounded observed-input LRU cache677, observed-label mean on misses, no replay.

Replay reservoir capacity506; sample BEFORE insertion, current gradient then replay gradient, GnT after each applicable gradient. Equal random inputs pair event opportunities; eligibility/selected identities may diverge causally. Random-score arms retain the source-style five uniform random scores per update, so their extra random generation is priced. No claim of exactly identical replacement counts or unit identities after trajectories diverge. No shrink/perturb setting is tuned or tested.

The cache is a serious practical competitor but the677/506 choice comes from the consumed calibration's4KiB ALGORITHM-CORE convention. It is NOT equal total storage. Record actual serialized state including each method RNG, reservoir and sampling/insertion RNG, and actual object sizes; teacher, scoring tables, output logs and debugging snapshots are separate experimental storage and unavailable to learners. The code shares a reservoir only to pair data; deployed neural storage charges a full copy per learner. All neural step sizes are identical. Intervention changes one rare bias operation, not gradient scaling; report gradient and replacement counts and bias-change magnitudes.

## Fixed outcomes and interpretation

Primary acquisition: mean pre-update MSE on first1,000 current examples of EACH of100tasks. Also report tasks10–99, all1M pre-update MSE and post-task competence. Retention: exact original32-point support MSE, all earlier contexts at each boundary. Primary average weights earlier contexts equally within boundary then99boundaries equally. Co-primary terminal risk weights99earlier contexts equally after task99. Report initial risk before task0, each task's finish competence, changes from that competence, and fixed ages1–9/10–49/50–99. No horizon selection after results.

For each teacher and baseline/alternative pair, retention gain=(baseline−alternative)/baseline for average AND terminal risk; acquisition cost=(alternative−baseline)/baseline. The primary current-only mechanism earns a **material joint benefit** only if BOTH retention gains exceed10% with lower two-sided95% teacher-paired t intervals >.10 and acquisition-cost upper95% <.02. The replay pair is a separately reported preplanned practical robustness test using the same rule. Broad practical superiority additionally needs these same fixed inequalities versus SGD+replay, both random-renewal arms and the cache; no such superiority follows from the primary pair alone. Report all pairwise point changes, never select a favorable comparator or horizon. Risk ratios require positive denominator; a zero risk makes the relative criterion unearned rather than adding a chosen epsilon.

Eight teachers, not tasks/points/updates, are independent units. Use paired teacher mean, sample SD/sqrt8, t7=2.364624251 for two-sided95% intervals. Intervals are model-based small-sample summaries without proven normality/coverage; failing a gate is not equality. Report all eight effects and counts. Also predeclare a per-teacher joint success: both risk gains≥.10/acquisition cost≤.02. If0/8 succeed, exact one-sided95% binomial upper prevalence=1−.05**(1/8); this describes the specified generator only and no universal absence. No postvalidation rescue/revised margin/new settings/new seed batch.

## Discrimination and correctness

The independently expressed exact rational reference includes constant-feature positive control: removal changes prediction−.3/MSE.09 for literal, zero for retained-mean; a dead-feature negative control is identical. These earn numerical sensitivity only. Recheck literal branch against prior checked engine. Independently reconstruct all boundary neural predictions/risks from saved snapshots and teacher integer equations; validate initial competence/age/average and terminal summaries. Audit cache final predictions without touching its LRU/hit counters. Save sampled actual renewal pre/post states for direct observed function-change checks. A positive identity or code discrepancy is not the material result; the eight untouched teachers provide its consequence test. A surviving consequential claim requires a new distinct independent reviewer commissioned by PI.

## Resources and stops

One process/thread, no dependencies or public payloads. Maximum1,800s cumulative scientific-process runtime, with main driver capped1,680s to leave audit/closeout. At any nonfinite state/resource/deadline failure stop and report PARTIAL, preserve all teacher exposure, no replacement teachers. Primary test deadline03:33:20Z/hard03:58:20Z includes orientation. At reserve/human stop save incomplete. No broad campaign reopening, old protected data, shared edits or native goal. Exact reproduction and failures/resources/exposure saved in task path.
