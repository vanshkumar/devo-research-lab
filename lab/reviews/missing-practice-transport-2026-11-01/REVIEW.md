# Independent mathematical review

**Verdict: bank the result as a conditional measurement-design example.** The primary K=4 case fails the frozen 0.10 target-diameter criterion. I found no material mathematical error in the stated deterministic shared-retention class. The favorable K=1 and success-complete-logging cases require their additional observations and guarantees. My independent contrary test shows that the K=1 recommendation also depends on the return score's resolution: rounding it to the nearest 0.05 permits an attained target gap **0.114335787**, despite exact source endpoints.

Author: `01a1957a-b2a8-7cf2-a3cb-cf8329a97d0e`. Independent reviewer: `01a1958e-e467-7fe1-9393-4b992feda870`, fresh Sol/max. Source bundle: `lab/tasks/missing-practice-transport-2026-11-01/`. No author code was imported or executed; no empirical records or public sources were queried.

## Independent reconstruction and main decision

I first constructed the teaching event update and pre-update observations directly from PROTOCOL.md. FIRST_CALCULATION.json completed at **05:23:30.842570 UTC**, before the 05:34:12.427 checkpoint. It executes same-observation K=2 worlds independently; it is an attained witness, not the practical worst gap. INDEPENDENT_BOUNDS.json then reconstructs the consequential extrema and their actual source and target event traces.

The main information set buys two compulsory calibrated, nonlearning source scores, both 0.75. It is stronger than the original binary certificates. For true block count n, these scores fix a=1-4^(-1/n). The last event's pre-update score has certificate 1 exactly when 2(n-1)>=n. A shared deterministic recorder that retains first-in-block failure and last-in-block success constructs the retained (0,1) observations for every allowed n>=2. The count restriction is **total** omissions: n_A+n_B<=4+K, with n_A,n_B>=2. It is not K omissions per task.

In a fresh alternating target, a task's pre-update sequence satisfies z_0=0 and z_(j+1)=rho[a+(1-a)z_j]. Both coordinates and the gains are monotone on the declared domain because the update stays in [0,1] and its derivative in a is rho(1-z)>=0. Summing appearances independently gives

T = sum over k=1..5 of [(6-k)/12][a_A(1-a_A)^(k-1)+a_B(1-a_B)^(k-1)]rho^k.

The event simulator and this polynomial differ by at most **1.11e-16** in the executed checks. Conditional on counts, continuity fills the closed interval as rho varies; the unknown-count set is a finite union. At an exact return score it is instead a finite set of points, since r=0.75*rho^n_B fixes rho for each feasible count pair.

| Information/design | Independently reconstructed result | Interpretation |
|---|---:|---|
| Original certificates, K4 | [0.123946, 0.833333] | Sharp extrema; no calibrated endpoints supplied for free |
| Two endpoints plus count/full own-task source audit | worst diameter 0.41259765625 | Audit outcome matters; this is the worst remaining outcome |
| Exact return, K1 | attained worst candidate 0.082217549820 | Author enclosure [0.082217549820, 0.082227...] supports the favorable 0.10 decision |
| Exact return, K2 | attained 0.128480699845 | Same-observation finite counterexample already fails 0.10 |
| Exact return, primary K4 | attained 0.174643194276 | Author upper enclosure 0.174652...; primary failure preserved |
| Every successful event retained, K4 plus exact return | attained 0.094127247487 | Author upper enclosure 0.094135...; additional logging guarantee |
| Fixed r=81/256, K4 | diameter 0.147022... | Conditional outcome, not the worst-outcome guarantee |

The independently computed K1/K2/K4 maxima occur at r=0.1875, where count branches enter. I checked membership immediately below, exactly at, and immediately above every K4 feasibility threshold 0.75*2^(-n_B). Threshold equality is included. Source extrema are sharp by monotonicity and constructed histories. The worst-return numbers above are verified attained values plus numerical global analyses; I retain the author's conservative enclosures rather than promote floating root calculations into a formal sharpness certificate.

For an independent global numerical challenge, each pair of count-specific targets becomes a sparse polynomial in (r/0.75)^(1/lcm(n_B1,n_B2)). I evaluated endpoints and derivative-root candidates using a recursive Rolle/monotone-interval construction, then separately checked an observation grid including all feasibility thresholds. All six K cases and the success-complete case agree with the author's saved enclosures. This method is complete in exact arithmetic; the implementation uses ordinary floats, not certified root isolation. The author's monotone envelope is conservative in real arithmetic: its active set stays fixed on each threshold cell; the upper endpoint limits existing branches, and entering branches are evaluated at the threshold with their complete observation partition. I found no threshold extrapolation error.

Re-reading a retained row creates no new hidden-event observation. A complete blocked source's **own-task** scores do not measure retention of the other task: B is zero during the A block, and B's own subsequent scores do not read A's loss. Counts plus the return identify the shared-retention parameters only after the calibrated endpoint information is bought. Success-complete logging forces n in {2,3}, since a 0.75 endpoint entails floor(n/2) successful pre-update events. It cannot be inferred from the retained successes alone.

Binary-return Y=0 has an excluded upper score boundary; its reported upper value is a supremum. I independently reconstruct the primary binary diameter suprema 0.335483... and 0.289258.... The exact-score finite sets and the source intervals do not have that open-boundary qualification.

## Calibration coupling and the author's directional sensitivity

At known counts (3,3), the same unknown source score s_A affects both a_A and rho=(r/s_A)^(1/3). Independently maximizing over feasible coupled scores, rather than combining unattainable marginal corners, reproduces the attained epsilon=0.04 width **0.072537482498**. My separate 2,048-cell monotone enclosure gives **0.072556466366**; the author's finer enclosure is 0.072539855501. All six nonzero predeclared error levels remain below 0.10. Neither enclosure is claimed sharp, probabilistic coverage, or a maximal tolerable error. Source certificate constraints remain satisfied over these error ranges.

I independently executed both directional-retention source histories and fresh targets. Complete own-task source scores, counts, endpoints and A return match exactly while the target scores are 0.283086428... and 0.469738412..., gap **0.186651984112**. After the source I executed the additional A teaching event from its nonzero state, then read B without updating it. The B readings 0.375 and 0.75, divided by the pre-event 0.75 B score, recover the two missing-direction retentions. The A update itself changes A and does not contaminate this B ratio under the stipulated dynamics. This earns the claimed identification only for fixed directional retentions and calibrated nonlearning observations; it earns no state-independent or biological calibration evidence.

## Independent contrary test: finite score resolution

CONTRARY_PLAN.md fixes one change before the test: Q(r)=0.05*floor(r/0.05+1/2). The source endpoints remain exactly 0.75, K=1, and the learning law is unchanged. I intersected every displayed score's left-closed/right-open preimage with every feasible count branch, then used count-specific monotonicity to compute bin extrema and suprema.

The worst displayed score is **0.25**, whose true-return bin is [0.225,0.275). Its target-diameter supremum is **0.114337189060**. Two strictly interior, event-executed witnesses are:

| Counts (A,B) | True return | Displayed return | Target |
|---|---:|---:|---:|
| (3,2) | 0.225001 | 0.25 | 0.260730526491 |
| (2,3) | 0.274999 | 0.25 | 0.375066313907 |

Both have exactly one omitted event, the same retained certificates and two source endpoints, and retentions inside [0.5,1]. Their attained gap **0.114335787416** exceeds 0.10. The upper-bin boundary is excluded, so the reported bin maximum is explicitly a supremum; the finite witnesses independently establish failure. This is a coarser measurement boundary, **not an error in the exact-score main class**, and differs from the known-count calibration calculation. No empirical device-resolution claim or precision grid was attempted.

The initial contrary output used a lower-bin-edge witness and a rounding guard; it is preserved as CONTRARY_INITIAL.json. I moved both finite witnesses 1e-6 into their bin and removed the rounding guard, without changing the frozen test or its result. CONTRARY_PLAN.md's 05:27 prose minute was rounded ahead of the actual first test time; actual output UTC timestamps and tool ordering establish that the plan was saved before either execution. No frozen plan bytes were edited.

## Reliability and limits

AUDIT.json verifies four core freeze pins plus all 22 saved artifact pins and byte sizes, with maximum independent source-bound difference **5.55e-17**. Eighty-digit gains/returns independently reproduce the maximizing target witnesses. The pins establish present-byte consistency; historical author timing remains reported metadata, not an independently attested event log. The original K0 generic envelope's **50,000-box failure** is preserved. Its exact zero under endpoints plus exact return follows separately because only (2,2) is possible. The numerical 1e-11 guards and high-precision checks are not directed rounding.

All outputs are deterministic synthetic/development evidence. No population confidence, stochastic recording-law calibration, empirical identification, novelty audit, protected target release, or validation of calibrated/nonlearning biological probes is earned. State-dependent or history-dependent learning remains untested. Resource, exposure, failed-command and unrun records are in RESOURCES.json. No author repair or restart is needed. The PI can bank this example and reallocate; a wider measurement recommendation must specify logging guarantees, both interference directions, and actual score precision.
