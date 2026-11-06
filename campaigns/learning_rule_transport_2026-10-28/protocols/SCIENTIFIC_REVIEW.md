# Independent adversarial scientific review

2026-10-28. Status: final scientific review of the completed source experiment
and post-validation RNN challenge, including independent reconstructions.
This is a scientific review, not a
second implementation of the entire model-fitting/trainer pipeline.

## Verdict

The completed frozen experiment supports a **failure to earn the stated
autonomous source-forecast gate**, despite strong conditional prediction.
The twenty external fixed-curriculum animals should remain protected. It does
not establish equivalence to growth, absence of learning, a universal
identifiability barrier, or failure of all published learning-rule models.

The primary DNN32 and the later RNN32 generate substantial population-mean
acquisition. The RNN's observed 6.96% CRPS improvement is promising but uncertain
and misses the conjunction of practical accuracy and lab requirements. Its
post-validation timing must remain visible. The DNN32's
weakness is individual future-curve value beyond the matched empirical growth
baseline, under this initialization, observation wrapper, training procedure
and opportunity-conditioned target. A broader claim that it cannot generate
learning would contradict the retained forecasts.

## Review boundary and evidence

I read `LEARNINGS.md` in full, campaign STATE, FREEZE, MODEL, TRAINER, DATA,
RECOVERY, UNCERTAINTY, DESIGN_REVIEW and DRIFT; inspected the forecast, score,
baseline, data-access and model recurrence code; checked pinned original
Liu source classes and fitting defaults; and directly reviewed the primary
Liu/Geadah texts within the bounded novelty scope below. No external prefix,
choice, feedback, reward or acquisition curve was opened. My numerical work
uses only retained source forecasts and observed summaries for trials
1001--6000. No learning rule or calibration distribution was refitted.

`artifacts/review/review_scores.py` independently expands the proper marginal
CRPS U statistic from retained forecast samples, checks every saved source
score, and computes animal-level paired comparisons and bin/metric coverage.
All CRPS values agree exactly with the lead implementation (maximum absolute
difference zero). There are forty full-primary-horizon animals, twenty-one
unfamiliar animals in development labs and nineteen in the two whole held
labs; forty-eight supply at least one complete future bin. Full results and
input hashes are in `artifacts/review/SOURCE_REVIEW_STATS.json` and
`SOURCE_REVIEW_SCORES.json`.
Bootstrap replay uses the saved canonical subject order (animal holdout then
lab holdout, alphabetically within each), seed 891 and 10,000 resamples. This
matches the frozen screen's finite-resampling convention rather than letting
an equivalent permutation create small Monte Carlo quantile differences.

The separate original-Parquet reconstruction reports 48 reconstructed animals,
1,728 score records, maximum CRPS discrepancy 4.44e-16, and zero differences
in MAE, coverage and interval width. That independent data reconstruction
substantially reduces the chance of a raw-choice/summary coding explanation;
it is distinct from my retained-sample verification.

The completed offline runner disables network entry points, verifies 5,120
pinned original objects (including external hashes only), rebuilds source
targets and regenerates all 288 first-stage model forecasts in 48 animals.
Its maximum forecast-sample difference is exactly zero. The frozen numerical
source result is therefore reproducible from local inputs. This evidence does
not certify biological adequacy of the model or uniqueness of the update law.

## Actual frozen primary result

All rows concern autonomous 3,000-trial forecasts after the same 1,000-trial
prefix, with equal-animal marginal CRPS. Positive gain means lower CRPS than
growth. Percentage-point errors include omissions as failures.

| Frozen model | CRPS | Gain over growth [95% animal bootstrap] | Relative gain | High-contrast MAE | High-contrast 80% coverage |
|---|---:|---|---:|---:|---:|
| DNN32 | .080517 | .000458 [−.009719,.010584] | .56% | 16.38 pp | 79.58% |
| DNN16 | .079955 | .001019 [−.004778,.006898] | 1.26% | 17.24 pp | 78.75% |
| Reward-offset RL | .082889 | −.001914 [−.011753,.008055] | −2.36% | 17.19 pp | 87.71% |
| Pure reward RL | .103005 | −.022030 [−.037889,−.007792] | −27.21% | 20.48 pp | 61.04% |
| Empirical growth | .080975 | reference | — | 16.28 pp | 81.25% |
| Skill persistence + matched engagement | .104411 | reference | — | 20.59 pp | 67.08% |

Beating persistence is insufficient here: exposure growth explains much of
that advantage. The fixed-competence synthetic control already demonstrated
why prefix-estimation precision can also create a spurious apparent learning
advantage. Neither concern is cured by calling persistence a null model.

DNN32 misses the .002 absolute and 10% relative gain requirements against
growth, the family-screen positive lower bound, the 10% high-contrast MAE
improvement, the 15 pp MAE ceiling, and parts of the held-lab criterion. DNN16
does not rescue the main result. Its small aggregate CRPS gain is accompanied
by worse high-contrast MAE, so it should not be called improved acquisition
forecasting.

The uncertainty is wide enough that the DNN32 comparison does **not** rule out
a 10% CRPS advantage: .010584, the upper ordinary 95% gain endpoint, exceeds
10% of growth CRPS (.008097). The frozen screen's lower endpoint is −.012709.
This is absence of demonstrated useful advantage, not a calibrated
equivalence or impossibility result. The percentile animal bootstrap is an
approximate finite-cohort screen, not a theorem of familywise coverage.

## What conditional prediction does establish

On the same actual future contrasts and responding trials, DNN32 conditional
binary NLL is .527342 versus the prefix-only static GLM's .682517. The
equal-animal gain is .155176 nats/response, with paired 95% interval
[.119092,.193879]. DNN16 and reward-offset RL have similarly substantial
positive gains. These are valid sequential conditional log scores.

The much smaller conditional curve CRPS (.012303 for DNN32) holds actual
intervening choices/rewards and actual adaptive stimuli fixed. It is a useful
tracking diagnostic, not another draw from the autonomous trajectory
distribution. Do not compare that number with growth's autonomous CRPS as a
matched-input causal contrast. Adaptive future stimuli additionally disclose
curriculum progress, which is why the actual-input replay must stay labeled.

The exact reward-independent RL update has zero own-action mean coefficient
drift; under a teacher's different choice probabilities it tracks their
innovations. That identity explains one concrete route to strong conditional
accuracy without a corresponding autonomous mean update. It does not prove
that DNN32 fails for this reason, nor that zero mean coefficient drift implies
constant observable performance. DRIFT's current numerical DNN example is
DNN16 and should not silently stand in for DNN32.

Saved mean curves reinforce this distinction. The observed mean high-contrast
accuracy rises from 52.69% in the first forecast bin to 68.61% in the sixth;
DNN32 forecasts 54.31% to 73.52%, reward-offset RL 52.66% to 65.93%, and growth
52.59% to 62.39%. Thus DNN32 generates learning and even captures a population
trend reasonably. Individual errors and distributional score, not a missing
population trend, prevent useful superiority. These curves are retained in
`artifacts/review/SOURCE_MEAN_CURVES.json`.

## Whole-lab, censoring and opportunity interpretation

DNN32 gains 4.40% over growth in the nineteen held-lab animals, below the
frozen 5% lab threshold. It is slightly worse in Hofer (−.000272 CRPS gain,
n=9), better in Witten (+.007238, n=10), and worse in the twenty-one
same-environment held animals (−.002459). DNN16 has small positive mean gains
in both held labs but fails the overall practical and accuracy requirements.
Two held laboratories cannot support population uncertainty over arbitrary
new labs; resampling their animals does not create more environments.

All fifty-four allocated source animals belong in the disposition. Six lack
the required prefix-plus-bin opportunity, and another eight lack a full
3,000-trial future. The primary is conditional on being observed that long;
metadata-based inclusion does not make competence-dependent stopping benign.
The 48-animal partial-bin sensitivity retains different horizons and is not
an estimate of the missing complete futures. Its DNN32/growth CRPS values
.074221/.075412 do not rescue a 10% practical advantage. At the secondary
5,000-trial horizon, 35 complete animals give .082226/.082269.

Realized opportunity counts and session boundaries are supplied to every
actor. This is a trial-indexed acquisition forecast, not calendar-time,
attendance, duration or cessation prediction. Indexed session start is not
certified first biological exposure; absence of a cache-left-edge artifact
does not certify complete prehistory. All forty primary animals have prefix
high-contrast accuracy below .8, so the proposed >=.8 competence stratum is
empty and cannot support a competence-general conclusion.

Moreover, stopping and future session lengths can depend on behavior and
fatigue. Supplying realized opportunity boundaries while generating behavior
does not by itself reproduce the conditional selection distribution induced
by that stopping process. This operational forecast supplies opportunity
covariates; it is not a complete causal model of opportunity-conditioned
behavior. The fixed-length and independently censored synthetic controls do
not validate informative stopping. This limits attribution of failure to the
trialwise law even when an opportunity-conditioned score is legitimate.

## Calibration and model/trainer limits

Near-80% marginal coverage is not enough to establish useful precision.
DNN32's side-specific high-contrast intervals average approximately 52.70 pp
wide; reward-offset RL's are approximately 72.17 pp wide. DNN32's pooled
four-metric coverage is 83.44%, while its high-contrast coverage is 79.58%.
Omission coverage is 97.08% and contributes to the pooled apparent calibration.
Pure RL has only 61.04% high-contrast coverage despite 70.10% pooled coverage.
Coverage by bin and metric must accompany pooled values, and marginal coverage
does not certify joint temporal calibration or a posterior over update laws.

The frozen calibration uses only ten development donor curves, selected
under leave-animal-out CRPS and applied under the same candidate policy to all
models. This protects the holdouts. It remains an approximate predictive
discrepancy model; it cannot identify inter-animal learning-rate variation,
parameter uncertainty or the true law. Clipping also changes means slightly,
as UNCERTAINTY correctly records. Raw and calibrated scores must stay visible.

Saved prefix metadata also shows 39/40 primary animals still have only 100% and
50% contrasts available. Under the published transform these map to 1 and .9867,
weakly separating three sensory/bias coefficients. In 34/40 DNN32 forecasts, all
propagated endpoint covariance eigenvalues are below 1e-6, near the 1e-7 floor.
This reflects the recurrence Jacobian's contraction, not independent evidence
that biological skill or the update law is precisely identified. Prefix-only
static/zero challenges help localize this limitation; they cannot certify
the initial latent state. The exact metadata-derived diagnostic is saved in
`artifacts/review/PREFIX_STATE_DIAGNOSTICS.json`.

Trainer reconstruction is unusually concrete for this public-data task:
versioned original code, adaptive buffers and generated correction/promotion
decisions are audited. Unrecorded settings, body weights, wheel plant, hidden
prehistory and the external custom acquisition source remain genuine limits.
In particular, **reward-volume and wheel-gain biological effects are not
challenged by preserving their metadata**. The actor consumes binary feedback;
rewardVolume and gain do not enter its learning or engagement rule. A fixed
reward-volume policy therefore cannot establish robustness to a
volume-sensitive animal. This is an omitted-input scope limitation, not an
implementation error in the reconstructed binary model.
`artifacts/review/VOLUME_GAIN_INVARIANCE.json` supplies a synthetic witness:
adaptive and fixed policies deliver different next-session amounts (2.9
versus3.0uL), while DNN32/RL sampled curves, learned weights and promotion
pools remain exactly equal under the same random draws.

The positive recovery fits the empirical RL pipeline to a known transferable
RL generator and forecasts unfamiliar adaptive and fixed-policy animals. Its
22.6%/10.3% improvements over growth provide real evidence that this particular
pipeline need not fail automatically. The null generators establish specific
failure checks, not a general type-I error rate from repeated independent
experiments. Known .8 retention misspecification and its rescue show why real
forecast failure cannot uniquely indict the trialwise law. The current
positive control is also not an exact fitted-DNN/RNN recovery demonstration.

## Completed source challenges and finite simulation

The declared diagnostic families have now been run on all forty primary
animals for DNN32 and reward-offset RL, with 256 particles. DNN32 CRPS ranges
from .080601 (slow promotion) to .106439 (no correction), with .089014 for static
current competence, .080962 for zero initialization, .081127 for future .8
boundary retention, .085897 for resetting to the prefix anchor, and .081499
for fixed omissions. None materially outperforms growth's frozen .080975.
The maximum autonomous sensitivity gain over growth is only .000374, so none
triggers the recorded .001 threshold for 512 particle confirmation. Reward-offset
RL also has no material rescue among these variants. This limits the listed
simple explanations; it does not exhaust all trainer/observation models.

The original .8 retention source diagnostic changes future boundaries only;
its prefix calibration still assumes retention 1. This is a perturbation of
future dynamics, not a coherent alternative with .8 retention throughout the
animal's prefix. The known-answer rescue does include retention-aware prefix
calibration. This review requested the matching source wrapper. The lead then
ran the recorded post-validation coherent prefix-plus-future .8 model on all
forty animals: DNN32 CRPS .082394 and high-contrast MAE 17.43 pp, versus
growth .080975 and 16.28 pp; RL CRPS .088755. This repair does not rescue the
forecast. It tests one fixed retention assumption without refitting the
source update law under that alternative, and should not be read as excluding
all models of overnight change.

Forcing actual future adaptive contrasts makes the generated-history
diagnostic worse (DNN32 CRPS .112675, RL .159926). This cannot establish that
trainer uncertainty is irrelevant: those contrasts were chosen in response
to another history of choices and errors. Replay breaks that closed-loop
relation. Its label as a conditional-input diagnostic is essential.

The declared finite-simulation trigger is met because DNN16's .001019 gain
is within .001 of the .002 boundary. It was honored by rerunning DNN16 and growth
at 1024 particles for all forty animals. Gain becomes .001329 (1.63%), with 95%
interval [−.004679,.007394], still below the practical point requirements;
high-contrast MAE is 17.19 pp versus 16.35 pp for growth. The six subject-hash
selected DNN32/RL checks give mean CRPS changes +.000389/+.000750. Individual
changes reach .003600/.004692, so individual forecast precision should not be
described as exact. This evidence supports stability of the failed practical
gate, not numerical convergence of every individual curve.

A new outcome-dependent stopping diagnostic preserves its exploratory timing
and initial pilot. It forecasts a known learner under performance-dependent
terminal censoring. Only one of 24 animals retains the full primary future;
the other results use partial bins. The 24 animal partial-bin fitted/growth
CRPS values .014077/.018381 show that stopping does not inevitably destroy
performance in that generator. The single full-animal bootstrap is
degenerate, and neither comparison validates real RT/fatigue/session-length
stopping or establishes full-horizon operating characteristics.

## Completed strongest-published-architecture challenge

The lead responded to this review's architecture objection by fitting the
exact source RNNGLM32 on the same 62 training and 12 development-validation
animals, using one fixed seed and the source optimizer under the fixed
1,000-epoch ceiling. Checkpoint 975 wins development conditional NLL. Final
model SHA256 is `c7f675d18f4143891ed7d2c76d91f74be74da9565fbae5407952768e2c146940`.
Final fitted original-class and closed-loop audits use that exact artifact;
the latter has zero choice/reward mismatches over 2,000 synthetic trials.
The source-freeze record was written before any RNN source scoring and uses
the expanded five-candidate/two-baseline lower percentile .005. All original
frozen artifacts remain unchanged. This is still a post-validation expansion
of the model set, not restoration of an untouched source confirmation.

My independent retained-sample analysis covers the same 40 complete primary
and 48 partial source animals; CRPS agrees exactly with the RNN scorer.
Development-only uncertainty selection chooses no residual widening, so raw
and calibrated RNN samples are exactly identical. Actual source results are:

| Post-validation RNN result | Value |
|---|---|
| Primary CRPS | .075339 versus growth .080975 |
| Gain over growth | .005636, or 6.96%; 95% animal interval [−.001407,.013065] |
| Expanded family-screen lower bound | −.003630 |
| High-contrast MAE | 15.75 pp versus growth 16.28 pp; 3.24% reduction |
| High-contrast 80% coverage / mean width | 84.79% / 60.63 pp |
| Hofer / Witten CRPS gain over growth | −.000139 / +.011289 |
| Conditional binary NLL | .528045 versus static .682517 |

RNN32 is the strongest observed autonomous candidate and improves the point
estimate substantially over DNN32. Its absolute CRPS gain passes .002, and
its held-lab aggregate gain is about 7.02%. It nevertheless misses the 10%
overall CRPS gain, positive screen, 10% high-contrast MAE gain, 15 pp ceiling
and positive mean gain in both held labs. It therefore does not earn the
expanded source gate. Its interval still allows a useful 10% advantage;
absence of gate passage cannot be reported as absence of an effect.

Its population mean high-contrast accuracy rises 54.61% to 67.28%, close to
the observed 52.69% to 68.61%. At the secondary 5,000-trial horizon, 35 complete
animals give RNN/growth CRPS .074735/.082269 (9.16% observed gain) and RNN
high-contrast MAE 15.46 pp. At 1,000 trials, 47 complete animals give
.059905/.066876 (10.42% observed gain), but high-contrast MAE improves only
about 7.5%. These prespecified secondary horizons deserve display; they do
not replace the primary horizon or all its conjunctive requirements.

The architecture objection is thus addressed by a concrete empirical
challenge. The residual limits are model-set selection after source exposure,
one optimization seed, the adapted observation/initialization process and
unmodeled process/individual variation. The result should be presented as a
promising but insufficiently demonstrated candidate, alongside the original
frozen negative gate. Complete review numbers and hashes are in
`artifacts/review/RNN_REVIEW_STATS.json`.

Independent original-byte/manual-GRU reconstruction also covers all 48 RNN
source animals and 432 score rows. Maximum score discrepancy is 1.53e-16,
conditional NLL discrepancy 2.22e-16, and conditional probability discrepancy
7.22e-16. Current-trial perturbation and omission-hold discrepancies are zero.
This resolves the central RNN coding/causality concern; it does not certify a
unique biological model.
The RNN's separate offline replay regenerates all 48 saved source forecasts,
including GLM weights and hidden state, exactly (maximum difference zero),
with original prefix rows and footer-derived opportunities only.

## Bounded novelty and published-model scope

[Liu, Geadah and Pillow v2](https://arxiv.org/html/2509.04661v2), especially
Fig.4, section4 and AppendixC, already test held animals and future trials;
their actual choices/rewards enter sequential prediction. RNNGLM is their
stronger empirical model. Their default DNN has two32-unit layers, while the
campaign uses a supported three-coefficient mode on another cohort. The
pinned classes verify recurrence, not exact paper-result replication. The
new evaluated target is generated-history, multi-session curve forecasting
under a simulated adaptive trainer and protected whole labs. It is not a new
learning-rule architecture or discovery that held-animal prediction is
possible. The paper's simulations and under-constrained inverse-problem
discussion already concern learning-rule recovery and its limitations.

[Geadah and Pillow](https://pmc.ncbi.nlm.nih.gov/articles/PMC12621722/),
sections2.1--2.4, infer individual PG dynamics with process/daybreak noise and
dynamic rates across adaptive and fixed curricula. Their learning-component
decomposition uses actual decisions; this campaign's source-frozen external
transport would be a different validation target. Do not claim curriculum
dependence, side asymmetry, aversive error updates, latent rates or generative
modeling itself as new. Direct PMC open returned a challenge page; the
search-indexed primary full text supplied the section-specific evidence.

This bounded review supports a specific validation distinction, not an
exhaustive first-in-literature claim. The original frozen DNN/RL set omitted
the strongest recurrent architecture; the completed RNN32 challenge above
addresses that omission while preserving its post-validation timing. It
does not silently join the original four-candidate confirmatory gate, and
the extra candidate's multiplicity adjustment was recorded before its source
scoring. The broader Geadah latent/noisy individual model and all possible
learning rules remain outside the tested set.

## Priority findings and resolution

1. **P1 — Bound the claim to predictive value of the fitted actors.** Preserve
   the distinction between substantial generated population acquisition,
   strong conditional prediction and unearned individual autonomous advantage.
   Display the stronger RNN result, its post-validation timing, both broad
   confidence intervals and the absence of equivalence.
   Even successful transport would not identify a unique biological law;
   failure here is still less informative about mechanistic uniqueness.
   Generative-process misspecification is a plausible hypothesis, not an
   empirically selected strongest explanation over sample uncertainty or
   fitting choices; no such comparative causal diagnosis was performed.

2. **P1 — Keep external data sealed.** The actual original source gate is
   false for all four frozen candidates; the expanded RNN gate is also false.
   The Pan cohort cannot be opened as
   a search for an effect. External success/failure, if eventually tested
   after a legitimately earned gate, would bundle policy, lab, genotype,
   implants, handling and year and could not isolate curriculum causally.

3. **P2 — Report exposure literally.** Forecasts were saved before future
   scoring. However the scoring loader decodes full source histories before
   slicing the analyzed first 6,000 trials. Report full source conversion
   exposure and the bounded analysis separately; do not say later source
   outcomes remain technically unopened. This does not undo the prospective
   forecast save boundary or open external outcomes.

4. **P2 — Avoid overclaiming calibration, recovery or optimization.** Show
   metric-specific precision/calibration and failed controls; retain the
   model-selection epochs, seeds and explicit fitting deviations. DNN16's
   selected epoch is 1000, DNN32's is 950 and RNN32's is 975 of 1000; this bounded fitting budget
   is meaningful, but it does not exhaust alternative initialization,
   regularization, latent noise, individual heterogeneity or recurrent-model
   optimization. Do not present inert volume/gain changes as biological
   robustness checks.

The missing strongest architecture, coherent-retention mismatch, finite
simulation trigger, reward/gain scope and replay-side issue have all received
concrete checks or explicit corrections. No further empirical challenge is
required to complete the bounded source-gate conclusion. Additional model
search would be new work on consumed source validation, not a reason to
relabel this experiment as untouched confirmation. The reporting requirements
above remain necessary for an honest final claim.

I also read the completed `REPORT.md` in full. Its numerical results, source
decisions, stage labels, population-mean qualification, external protection
and stated limits agree with this review. Two final wording refinements were
sent to the lead: present generative misspecification as a hypothesis, and
describe the Bernoulli(.5) zero-side replay as an alternative balanced
diagnostic rather than certified true hidden assignment. Actual adaptive
side probabilities can retain correction-related bias. Neither refinement
changes any score or gate, and neither requires another empirical run.

## Qualified claim supported now

The evidence should be classified as follows:

| Category | Current assessment |
|---|---|
| Material implementation error | None identified in the frozen decisive result; original-byte, causal, recurrence, scoring and offline checks agree. |
| Controlled failure | Wrong session-retention dynamics cause a known learner to fail; the known matched correction rescues it. This localizes a scope limitation. |
| Predictive failure | All four frozen candidates and the later RNN miss the practical source gate; pure RL is clearly inferior to growth in this sample. |
| Insufficient evidence | Useful DNN32/RNN advantage is not established or excluded; external transport, arbitrary new-lab performance, informative stopping and unique mechanisms remain unestablished. |
| Broad impossibility | Unsupported. No experiment here demonstrates that autonomous acquisition forecasting or biological learning-rule identification is universally impossible. |

On forty source animals with a complete forecast horizon, reconstructed
learning-rule models substantially improve sequential prediction when real
intervening behavior is supplied, yet do not demonstrate the prespecified
useful autonomous advantage over exposure growth after a 1,000-trial prefix.
The frozen DNN32 gains only .56% CRPS; a post-validation RNN challenge gives
a more promising 6.96% observed gain, with a 95% interval spanning no benefit
and a meaningful benefit. RNN individual high-contrast errors remain 15.75 pp
and its 80% intervals about 61 pp wide. Both generate population acquisition;
neither earns the required source gate. The twenty fixed-curriculum external
animals remain untested. This result establishes neither a unique law,
equivalence to growth, nor a general impossibility of forecasting learning.
