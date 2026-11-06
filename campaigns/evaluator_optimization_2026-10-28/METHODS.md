# Methods and inferential scope

This document describes the frozen computation. Final numerical conclusions belong in REPORT.md and FINAL_RESULT.json after completion.

## Independent reachable motor plants

The independent unit is an entire tuple of motor plant, circuit initialization, tutor target and starting program. Development IDs0–2 are consumed for protocol decisions. Twelve held-out tuples, IDs100–111, are generated only after protocols/FREEZE.json. They are draws from one declared family, not twelve biological subjects or twelve different families. Every held-out evaluator is newly tutored on its own target; this is generalization of the **teaching recipe**, not transfer of one trained network to a new target.

Each plant has four shared program coordinates a controlling six separately sampled100-channel rectified affine maps. Matrices are Gaussian divided by2; intercepts are Gaussian mean−.4, SD.2. Each context's output is centered and standardized to SD2, with a1e−12 floor. Target and initial programs are independent uniform[-1,1]^4 draws made after the plant. The target is exactly its generated output at gain1. Search bounds are[-2,2]^4 and gain[0,2]. Every draw is retained.

The fifth motor coordinate multiplies all six signed sensory patterns by a common nonnegative gain, after normalization. It is model auditory-current gain, not sound pressure, physical loudness or nonsinging. Gain0 removes auditory drive while premotor timing remains. At nondegenerate target patterns, zero-drive MSE is4. Shared program coordinates make a deliberately restricted low-dimensional manifold across the six contexts; the plant is not a vocal-organ model or six independent syllable policies.

## Learned scalar feedback

The unchanged pinned Gong E↔I source network has600 excitatory,150 inhibitory and15 HVC units. Recurrent connectivity, transfer functions, time constants and two local plasticity rules use the existing source helper. Tutoring has35 or140 repeated renditions. All conditions share an identical initial circuit and original membrane states. Long training is a literal continuous140-rendition simulation from that initialization, preserving the same35-rendition input prefix. A source-call restart would reset the10-ms asynchronous plasticity history; it is not used. One upcoming HVC period is included before truncating training arrays to preserve Gaussian clock tails and exact prefix equality.

Each modeled rendition lasts1100ms: six100-ms patterns at50,200,...,800ms, supplied source-like Gaussian HVC timing across900ms, and terminal silence. Each scalar cost averages excitatory rate across the six120-ms response windows. Probe episodes reset to a500-ms burn state computed under the corresponding frozen weights from the same original membrane initialization. Circuit dynamical noise is zero throughout this assay. Published example training uses noise.1, so this is a favorable, modified mechanism assay despite executing the unchanged numerical functions.

Six arms use true-error oracle feedback; learned35 feedback with joint shape/gain; learned35 with gain fixed1; learned140 joint; untutored joint; and shuffled35 joint. The shuffled circuit sees the exact same six tutor patterns shifted cyclically by one context during35 tutoring renditions. It preserves marginal exposure and the supplied clock, while disrupting the correct sensory/context association. Beating this arm supports target-specific contextual teaching rather than merely generic sharpening. It does not identify a unique plasticity mechanism.

## Search, information and budget

The actor receives only a scalar callback. Circuit actors never use target action, target features, offline true loss, derivatives through the plant or a tutor-fitted action basis. The oracle is explicitly privileged. Fixed gain supplies a simplifying task constraint common to all normalized targets and is an axis ablation, not a generic repair with the same task.

The original coordinate-only pilot exposed a zero-gain flat plateau even for the true-loss oracle. It is preserved as a failed control. One documented prevalidation revision adds target-blind broad proposals every fourth round, matched across reward arms, while retaining coordinate polls in the other rounds. Greedy acceptance uses strictly lower scalar cost, with deterministic first-argmin tie breaking. Broad success resets local step.4; broad failure leaves it unchanged. Local failure halves step to.00625. See the complete seed/schedule in DEVELOPMENT_REVISION.md and run_mixed.py. No actor, plant, encoder or reward tuning follows validation.

The primary budget is one initial query plus64 rounds of10 proposals,641 feedback slots per arm. Fixed-gain omitted-axis slots are actual repeated center feedback. Exact deterministic memoization avoids some repeated source integrations, while recording every feedback slot; cache hits are not free additional exploration. Oracle and learned35 are subsequently continued to128 rounds/1281 slots as a declared challenge, with their64-round primary result preserved. The extra broad programs were drawn in advance from the same fixed seed. Failure to improve with this search is not a global-convergence certificate.

## Outcomes and uncertainty

True loss is100-channel feature MSE averaged across contexts, measured separately from reward. The primary plant endpoint is terminal/initial true loss. Normalized improvement is one minus this ratio. Each independent tuple is weighted equally. No zero-initial-loss draw is replaced; if one occurs, normalized ensemble metrics are undefined rather than silently dropping it. Absolute losses remain available.

The declared utility rule requires learned35's **point estimate** of mean improvement to reach half the oracle's, and paired95% intervals for its advantage over both untutored and shuffled35 to lie above zero. The half-oracle gap and ratio uncertainty are also reported. A point-rule pass is not a confidence-bound claim of half-oracle performance. The known-answer development gate requires>=95% recovery on each of three plants; all exceed99.99%. Held-out oracle outcomes are included for every plant, and its mean must exceed75% reduction for the aggregate utility comparison to be interpretable.

Intervals resample whole tuples, paired across arms, with20,000 ordinary percentile bootstrap draws and seed20261028. They describe uncertainty under this synthetic generator; they are not biological population intervals, and secondary comparisons carry no familywise guarantee. Secondary outcomes include terminal absolute loss, gain, MSE<=.4 (10% of target energy4), accepted reward-improving/true-worsening steps, fixed-gain and140-rendition contrasts, and64→128 changes. These distinguish true acquisition from attenuation and initial-error normalization.

The separate exact-target diagnostic makes10 centered finite differences ath.025 plus one.05-norm proposed descent from the target. It uses12 uncached circuit evaluations per exposure condition. This deliberately target-informed diagnostic never initializes the primary actor. With sharp nonlinear changes it is a finite-scale direction, not proof of a smooth infinitesimal gradient or dynamical instability.

## Evidence checks and boundaries

verify.py independently reconstructs seeded plant/target/start draws, feature algebra, every stored true loss, full proposal/acceptance/step histories and query counts. It independently integrates selected frozen circuits using dense explicit contractions and separately written Euler/transfer equations, including burn states and exact-target responses. Diagnostics receive independent loss/finite-difference checks. Source and freeze hashes are checked, and original failed pilots remain preserved. These are computational verification; held-out learning and successful true-loss controls supply the scientific test. Training plasticity is not independently reimplemented, and no independent empirical replication is claimed.

All empirical campaign reports and exposure ledgers remain unchanged. No protected mouse, human, worm or other observation is opened. In particular, all20 strict external Pan-Vazquez prefixes/outcomes stay sealed: the earlier individual and prospective population gates remain unearned. The prior prospective growth advantage4.69pp[2.85,5.67] remains the lab's strongest empirical benchmark finding, with its session-model and selection objections retained.
