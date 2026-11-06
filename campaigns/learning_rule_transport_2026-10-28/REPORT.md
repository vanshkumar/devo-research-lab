# Learning-rule transport: average acquisition survives, individual forecast value is limited

Completed 2026-10-28, America/New_York. This is the bounded first study selected in the research strategy reset, not a reopening of the six completed campaigns.

**The tested models are useful observers of ongoing learning, and they can generate average acquisition. They have not established useful individual virtual learners for changing the curriculum.** After 1,000 calibration trials, the original published-architecture DNN had 16.38 percentage-point error in future side-specific high-contrast accuracy, versus 16.28 pp for a strong exposure/growth forecast. With actual intervening histories and stimuli, its diagnostic error was 2.47 pp. A stronger recurrent architecture improved autonomous distributional prediction, but did not earn the frozen source/laboratory gate. The independent real fixed-curriculum cohort remains sealed.

This is a result about the **tested forecast recipes and information regimes**, not proof that learning rules cannot transfer. The confidence intervals still allow useful improvements. The actionable decision is to retain the RNN as the strongest benchmark, separate observing competence from generating its changes, and preserve external validation while that distinction is addressed.

![Recurrent architecture challenge](/Users/vanshkumar/Documents/repos/devo-research-lab/campaigns/learning_rule_transport_2026-10-28/figures/RNN_CHALLENGE_RESULT.png)

## What was tested

The original allocation used metadata only: 74 development animals, 27 unfamiliar animals in development laboratories, and 27 animals from two completely reserved laboratories, Hofer and Witten. Development was nested into 62 fitting and 12 checkpoint/calibration animals. No eventual learning criterion selected animals. Of the 54 reserved animals, 48 supplied the 1,000-trial prefix plus a scored future bin; 40 supplied the full primary 3,000-trial future (21 unfamiliar-animal and 19 unfamiliar-lab animals: Hofer 9, Witten 10). All 54 remain in the disposition. Shorter futures are reported separately.

Each autonomous forecast received only the first 1,000 trial outcomes and the realized future opportunity/session-boundary vector. It then generated its own stimuli, choices, feedback, coefficient updates and adaptive trainer decisions. It did not replay the real future adaptive curriculum. Forecast files were saved before scoring reads. The target is indexed task exposure, not calendar-time acquisition, stopping or a causal curriculum effect.

The primary endpoint is an observable six-bin acquisition curve, with 500 trials per bin. It equally weights left and right high-contrast correct shares (absolute contrast at least .5, omissions counted as failures), right-choice share among all trials, and omission share. Right-choice share is a bias-related observable, not a stimulus-standardized psychometric bias. The proper score is marginal CRPS, averaged equally over metrics, bins and animals; lower is better. Interval calibration is marginal, not a claim about the joint law of whole trajectories.

The small model set comprised the published additive DNNGLM architecture, source-style REINFORCE with a reward baseline, pure reward REINFORCE, full-prefix skill persistence and an empirical exposure/growth forecast. All shared the same development-derived engagement/omission component. Growth borrows changes from 15 development neighbors matched on prefix behavior; it never borrows the test animal's future. Omissions remain observations and exposure opportunities; no no-go is converted to a right choice.

The original DNN/RL models, baseline bank, uncertainty mapping, score, horizons, gate, seeds and code were frozen before source validation. After seeing that result, a fresh adversarial review requested the paper's stronger recurrent architecture. Its GRU32 plus two ReLU layers was fitted only on the same development animals, with a fixed seed and 1,000-epoch ceiling. Its checkpoint and variance mapping used development data only and were separately frozen before RNN source scoring. This is an explicitly **postvalidation architecture challenge**, not restored untouched source confirmation.

## Source results

These are the 40 full primary animals. Coverage and interval width below refer specifically to the two high-contrast metrics, at nominal 80%.

| Autonomous forecast | Marginal CRPS | High-contrast MAE | Coverage | Mean interval width |
|---|---:|---:|---:|---:|
| Skill persistence + matched engagement | .10441 | 20.59 pp | 67.1% | 47.7 pp |
| Exposure / growth | .08097 | 16.28 pp | 81.3% | 53.4 pp |
| Pure reward REINFORCE | .10300 | 20.48 pp | 61.0% | 47.0 pp |
| REINFORCE + fitted baseline | .08289 | 17.19 pp | 87.7% | 72.2 pp |
| DNN16 | .07996 | 17.24 pp | 78.8% | 60.0 pp |
| DNN32, original primary architecture | .08052 | 16.38 pp | 79.6% | 52.7 pp |
| RNN32, postvalidation challenge | **.07534** | **15.75 pp** | 84.8% | 60.6 pp |

DNN32's gain over growth was .000458, or 0.57%, with a paired animal-bootstrap 95% interval [−.009719, +.010584]. RNN32 improved the point estimate to .005636, or 6.96%, with interval [−.001407, +.013065]. Its accuracy improvement was only 0.53 pp, or 3.24%. These intervals **do not establish equivalence or exclude a meaningful advantage**. They also do not establish the predeclared benefit.

The gate required at least 10% and .002 absolute CRPS benefit over both strong baselines, at least 10% high-contrast MAE improvement with MAE at most 15 pp, useful calibration, and benefit across both reserved labs. It used a bootstrap family screen; the RNN expansion increased the comparison count from four to five candidates before RNN source scoring. No candidate earned the gate. The RNN was slightly worse than growth in Hofer (.078000 versus .077860) and better in Witten (.077608 versus .088897). Two held laboratories are two environments, not 19 independent replications of arbitrary new laboratories.

The recurrent model deserves a qualified positive interpretation. At the secondary 1,000-trial future horizon (47 animals), its CRPS was .059905 versus .066876 for growth, a 10.4% point improvement. At 5,000 future trials (35 animals), it was .074735 versus .082269, a 9.16% point improvement. These descriptive horizons do not replace the fixed primary or its other requirements. Full individual, horizon, laboratory, partial-observation, metric and calibration tables are in [tables/](tables/).

### Actual-history prediction and generated learning are different successes

On the same actual future contrasts and responding trials, DNN32 sequential conditional log loss was .527342 versus .682517 for a frozen prefix GLM, a gain of .155176 nats per choice [95% .119092, .193879]. RNN32 was .528045. Current choices/rewards cannot change the current prediction; they enter only later updates. This reproduces the architectural recurrence and a substantial held-animal conditional gain on this new cohort, not the original paper's exact numerical experiment or its model ranking.

When actual histories were supplied, diagnostic high-contrast errors were 2.47 pp for DNN32 and 2.30 pp for RNN32. Autonomous errors were 16.38 and 15.75 pp. The conditional curve samples hold actual histories and stimuli fixed; their scores are not autonomous joint forecast scores. The valid likelihood comparison uses the same realized inputs. The large diagnostic gap measures dependence on ongoing behavioral information, not a causal effect of showing feedback to the model.

Correct full-history conditional probabilities, combined with a correct environment, also define a correct generative process by the probability chain rule. This gap is therefore an empirical limit of these fitted forecasts and their information/assumption regime, not a mathematical incompatibility between conditional inference and generation.

**The models do generate acquisition.** Across the first and last *future* 500-trial bins, observed cohort-average high-contrast accuracy rose 52.69%→68.61%. DNN32 generated 54.31%→73.52%; RNN32 generated 54.61%→67.28%; growth generated 52.59%→62.39%. The RNN tracks this population mean well. The limitation is individual curve value beyond exposure forecasting, with broad distributions, not absence of mean learning. This descriptive population comparison was not substituted for the individual gate.

[Original frozen-stage figure](figures/SOURCE_FORECAST_RESULT.png), [hash-selected individual examples](figures/INDIVIDUAL_SOURCE_TRAJECTORIES.png), and [all 40 primary animals](figures/ALL_PRIMARY_SOURCE_ANIMALS.png) show the information gap and heterogeneous paths without choosing only successful examples.

## What survived the strongest challenges

The pipeline successfully detected a known transferable learner. A rule fitted with the exact empirical optimizer and first-200-trial training initialization, followed by prefix-only test calibration, beat growth by 22.6% in 24 new synthetic source animals: CRPS .013941 versus .018002, high-contrast error 2.45 pp. Frozen transport to 24 synthetic fixed-protocol animals improved CRPS by 10.3% (.024301 versus .027085), with 5.08 pp error and 83.7% coverage for nominal 80% intervals. These are simulated controls, **not the protected real external cohort**.

Fixed competence, ordinary exposure growth and changing engagement did not earn material update-rule gains over their strongest baselines. They showed why comparison to persistence alone is inadequate. A precision difference in fixed-competence calibration led us to strengthen the real-data persistence baseline to all 1,000 prefix trials before freezing. The earlier synthetic baseline variant and its code snapshot are preserved; exact historical control replay uses those artifacts. The positive comparisons against growth are unaffected by that strengthening.

A known .8 session-boundary retention mismatch caused a correct rule to fail (CRPS .038725, coverage 53.5%). Supplying the known boundary assumption to both prefix calibration and simulation rescued it (.013771, coverage 84.5%). In real source animals, coherent .8 prefix-and-future retention did not rescue DNN32 (.082394, 17.43 pp error) or RL (.088755, 19.05 pp). Alternative prefix initialization, reset-to-anchor, correction removal, faster/slower promotion and fixed-prefix engagement also did not supply a material autonomous rescue. These are bounded perturbations, not an exhaustive exclusion of biological session effects.

An explicitly conditional actual-contrast replay also remained worse. An alternative balanced-zero diagnostic, using independent .5 assignments, yielded CRPS .112658 for DNN32 and .159941 for RL, virtually unchanged. Those assignments are not certified actual conditional hidden sides: adaptive probabilityLeft can retain correction-related bias. Both replay variants leak the animal's real adaptive schedule and cannot become autonomous results. They show that these particular input-replay recipes do not rescue the frozen actors; they do not validate every trainer assumption.

The declared Monte Carlo trigger was honored. DNN16's .001019 original score gain was within .001 of the .002 boundary, so all 40 primary animals were rerun at 1,024 particles against growth. Gain remained only .001329 [−.004679, .007394], or 1.63%, and accuracy remained worse. First-six hash-selected higher-particle checks were also retained. See [SOURCE_CHALLENGES.md](protocols/SOURCE_CHALLENGES.md).

A further postvalidation synthetic termination control used a new independent seed and outcome-dependent stopping. All 24 partial-bin forecasts retained about 2.47 pp error and 85.3% coverage, but only one animal retained the complete 3,000-trial future. No useful full-horizon interval can be inferred from that one animal. This demonstrates attrition and preserves the operational scope; it does not validate real response-time/fatigue-dependent session stopping. Details and the ineffective earlier threshold pilot are in [STOPPING_CONTROL.md](protocols/STOPPING_CONTROL.md).

### A concrete reason conditional tracking can overpromise

For the fitted source-style RL rule,

`Δw = (a + b r) (y − p) x`.

Under self-generated `y ~ Bernoulli(p)`, the reward-independent term has zero mean coefficient update. With a deterministic correct side `z`, the reward term gives `E[Δw] = b p(1−p)(2z−1)x` on responding trials. The fitted sensory history/reward gain ratios were 35.5 and 17.4. Thus a large part of its conditional tracking term becomes diffusion during self-generated forecasts. Exact enumeration and million-scale generated-action checks verify this statement. Nonlinear choice probabilities can change despite zero coefficient drift; the formula is not a proof about DNN/RNN failure. It identifies one concrete way a behavioral observer differs from a prospective learner. See [DRIFT.md](protocols/DRIFT.md).

## What remains unresolved

A plausible unresolved explanation is misspecification of the *generative behavioral process*: a conditional updater can infer ongoing competence from choices without modeling what produces individual future changes, latent engagement/strategy transitions or session effects. Finite-sample uncertainty, fitting choices and genuinely unpredictable future variation are not distinguished from that explanation. No competing latent-process model was tested. The RNN's improved score and good mean curve suggest useful structure remains. This study does not identify a unique missing mechanism or establish that individual learning is intrinsically unpredictable.

Several limits matter:

- Recorded source prefixes are not certified complete biological first exposure. All 40 primary prefixes happened to have high-contrast accuracy below 80%; removing the one cache-left-edge primary animal did not rescue the original models. This reduces one simple explanation without certifying prehistory.
- In most DNN32 prefixes, propagated initialization covariance contracts nearly to its numerical floor. That is a property of the recurrence/Jacobian, not proof of identified biological skill. Early .5 and 1 contrasts are nearly identical after the source transform, weakening separation of sensory/bias coefficients. Predictive process spread is substantial; parameter identification is not claimed.
- Reward volume and wheel gain are **untested omitted actor inputs**. The source models use binary correctness. Generating reward/gain metadata faithfully does not show robustness to volume-dependent or movement-dependent learning.
- Realized future opportunity boundaries may themselves depend on behavior. Supplying them while generating histories is an operational forecast recipe; without a stopping model it is not a complete causal conditional simulator. Full-horizon selection can depend on success, failure or attendance. Partial futures are visible, not silently removed.
- The empirical growth donor can change when a donor is censored at a later bin. Marginal CRPS is appropriate for the stated marginal targets; neither it nor the diagnostic energy score establishes a coherent biological trajectory law.
- The real external cohort differs in laboratory, genotype, implants, year, handling and curriculum. Even a later external failure could not uniquely identify curriculum as its cause.

## Validation, provenance and reproduction

The original [FREEZE.json](protocols/FREEZE.json) was created before source outcomes, with a recorded pre-execution serialization repair that changed no scientific choice. Its final SHA256 is `c0141244ac43d240f858956917e3b2b661c72a01a4bddbccdb3974a818b5741f`. The later [RNN_FREEZE.json](protocols/RNN_FREEZE.json), SHA256 `a4bcaac21b1302d0527daa31df119bd64b38c7389fcdd8d9323f7eecad5cd652`, preserves the postvalidation timing and stricter comparison count.

Original data acquisition reused the pinned release caches. The primary index has 5,120 objects/150.05 MB: 128 source animals (2,447 tables, 1,418,786 rows) and 20 sealed external animals (453 ordinary sessions). One development KS016 object differed from the historical cache and was independently pinned using current public object metadata before its outcomes were opened. Published cohort exclusions, multiple-session chronology, author day mapping and all hashes are preserved. [SOURCES.md](SOURCES.md) records primary papers/code and the bounded novelty review.

Source scoring conversion decoded the complete indexed histories of the 48 forecastable source animals **after forecast saving**; only their first 6,000 rows entered this analysis. Do not call the later decoded rows untouched. Six shorter reserved animals had prefix-only exposure. The real external cohort has had no new choice/reward summaries, prefixes, learning curves, fitted rules or validation scores opened; downloading/hashing bytes and input-only feasibility checks are recorded separately. Its outcomes remain protected. The [exposure log](protocols/EXPOSURE.jsonl) and [validation-status record](protocols/VALIDATION_STATUS.json) are authoritative. All earlier campaigns and their consumed holdouts remain unchanged.

Independent original-Parquet reconstruction reproduced every original source target/count and 1,728 forecast-score rows within 4.45×10⁻¹⁶. Independent RNN reconstruction reproduced both coefficient and hidden-state conditional recurrences within 5.2×10⁻¹⁵ and 432 score rows within 1.6×10⁻¹⁶. Canonical bootstrap animal ordering is saved; alternative order produced only finite-resampling quantile differences and is explicitly audited. [RECONSTRUCTION.md](protocols/RECONSTRUCTION.md), [RNN_RECONSTRUCTION.md](protocols/RNN_RECONSTRUCTION.md) and the fresh [SCIENTIFIC_REVIEW.md](protocols/SCIENTIFIC_REVIEW.md) document the checks and surviving objections.

All **336** main source forecasts regenerate offline exactly: 288 original-model forecasts plus 48 RNN forecasts, including RNN memory endpoints. Raw object/freeze hashes are verified, Python network entrypoints are disabled, and the replay receives only original permitted prefixes and footer opportunities. No external outcomes are needed.

From the repository root:

```sh
campaigns/learning_rule_transport_2026-10-28/.modelenv/bin/python campaigns/learning_rule_transport_2026-10-28/reproduce.py --replay all
campaigns/learning_rule_transport_2026-10-28/.modelenv/bin/python campaigns/learning_rule_transport_2026-10-28/rnn_reproduce.py
```

The faster original-byte score-only command is `reproduce.py --replay none` using the same interpreter. The complete rebuild/fit commands, software versions and historical control replay are in [REPRODUCE.md](REPRODUCE.md). Scientific figures have PNG and PDF versions and were visually inspected.

## Decision and recommended next scientific action

**Complete this study at the source gate and preserve the real external outcomes.** The recurrent model is a promising distributional benchmark and a good population-mean generator, but this study has not established the individual forecast value required for curriculum transport. A claim of universal failure, equivalence to growth or absence of generated learning would exceed the evidence.

The next investment should separate a stochastic process that changes competence from the observation filter that estimates it. Retain the RNN and growth forecasts as benchmarks; model session/strategy variation and relevant reward or movement inputs explicitly, rather than buying more conditional likelihood with another network width. Earn a new prospective source test before spending the independent fixed-curriculum cohort. No successor campaign or automation has been launched.
