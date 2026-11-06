# Known-schedule human forward forecasts retain the history gain

Completed November 2, 2026. Same paused/resumed allocation and original consumed participants. Jobs0. The broader scientific goal remains unfinished; no distinct independent review has occurred yet.

## Earned finding

With the **exact future deterministic source schedule known**, the frozen shared-history predictor retains a useful marginal later-choice advantage after generating every post-calibration choice, feedback event and omission. On the original39evaluation people/2,867responding primary choices, its equal-person log-score gain over the frozen response-persistence comparator is **.033894nat/choice**, with stratified-person95% interval **[.025548,.042306]**. Score Monte Carlo SE is **.00001564nat**. This passes the frozen .01nat/choice/positive-interval/MCSE<.001 criterion.

| Observation assumption | Shared minus persistence, nat/response | Person95% interval |
|---|---:|---:|
| Main source-only omission completion | .033894 | [.025548,.042306] |
| Exact no-omission limit | .033974 | [.025567,.042447] |
| Twice source omission probability | .033771 | [.025526,.042144] |

The main Brier improvement is .015433[.011690,.019395]. All-later log-score gain is .014830[.008113,.022214]; zero-contrast primary gain is .018642[.003497,.033695]. Familiar/unseen original schedule strata have point gains .026884/.037820 across14/25people. Every original schedule has positive point gain, but some are below .01 and contain only two people. The two-stage schedule/person interval is [.019504,.045060]; every leave-one-schedule-out mean remains positive. These are conditional finite-schedule summaries, not a guarantee for a new teacher population.

See [SCORES.json](SCORES.json), [individual scores](PERSON_SCORES.csv), [frozen forecasts](FORECASTS.npz) and [forecast saving record](FORECAST_META.json). Main forecasts were saved20:34:48.940Z; the separate scoring output was saved20:35:04.209Z. Protocol/code/inputs froze20:33:46.133Z, before either operation. No learning-rule/population/person/hyperparameter fit was performed.

## Why the positive result is narrow

The source task reads a fixed pre-generated XLSX schedule sequentially, once. Each evaluation person's first200 visible signed contrasts plus sides actually revealed by prefix responses uniquely identifies one of the ten source files. That exact lookup legitimately specifies this particular environment, but it also exposes its **realized future target order**. We do not replace this order with independent draws from probabilityLeft, call the targets generated, or claim a forecast under an uncertain stochastic teacher law. Hidden bias and switch labels define scoring only.

On a response, own choice times signed correctness equals scheduled target side. Thus a generated left/right choice changes the lagged-choice nuisance but **does not change target-history evidence**. Only a generated omission prevents that revelation. The exact no-omission gain exceeds main by just .0000801nat/response. The saved conditional gain was approximately .03396nat/choice; near-equality is descriptive, not a matched causal decomposition. This task is therefore an easy case for target-history generation compared with a genuinely history-dependent teacher. The strongest teacher-information explanation survives.

This is also a forecast of **choice conditional on current responding**, scored as marginal binary forecasts. It is not a proper joint-trajectory likelihood or demonstrated engagement forecast. The source's integrated one-step predictive kernel is extended sequentially without changing any coefficient or quadrature rule. It does not test a persistent latent-person-coefficient generative model, which would require an additional explicit prescription. Random-node sampling implements the existing conditional kernel and is not a biological claim of redrawn traits.

## Observation completion and uncertainty

The sole PI-authorized pre-main revision adds a simple shared observation law: condition-specific constant omission probability, independent of target, choice and history. Original development trials201–600 contain113/8800discovery omissions and0/7600taught omissions. Jeffreys Beta(.5,.5) gives predictive means .0128963/.00006578. Each trajectory draws the source posterior q once and uses the same q and omission events for both models. Conditional-on-current-response predictions weight trajectories by1-q. Actual evaluation future omissions never calibrate this law.

This integrates source omission-parameter uncertainty only within the declared iid model. The zero/doubled-rate sensitivities do not validate independence, rule out temporal clustering/target-dependent engagement or bound arbitrary observation laws. Learning-fit uncertainty remains frozen/conditional. Participant and schedule/person resampling describe the original selected source schedules; only three schedules were originally held out from learning-fit development. All80people were already consumed before this study, so the new test is explicitly postvalidation.

## Actual checks and their limits

The original November1first calculation matched the source predictor within1.11e-16 and was not rerun for status cleanup. New constructed future paths, including an omission, match all312source predictions across both competitors within3.33e-16. Exact four-step16-choice-path enumeration agrees with no-omission recursion within1.11e-16. All-omission trace decay/previous-choice-zero checks pass. An exact81-path Beta(.5,.5) response/omission reference agrees with the particle implementation within measured simulation uncertainty, challenging the1-q current-response weighting under a deliberately uncertain constructed law.

Independent scalar log-ratio calculations and the original source's mask constructor reproduce every saved person score within1.05e-16 and all39-person means within6.94e-18. Actual primary masks agree from the original cached labels and source-XLSX input reconstruction. Proper-score expected-gain signs under each model's marginal Bernoulli law pass. These are reference/implementation controls, not validated full-pipeline power, coverage or proof of biological validity. See [CHECKS.json](CHECKS.json) and [FINAL_AUDIT.json](FINAL_AUDIT.json).

The earlier campaign's recovery simulations generate different synthetic populations to assess estimator discrimination; they did not answer this exact fixed-fit empirical forward-score question. Existing history effects, generated behavioral forecasts and heterogeneous learning have substantial prior work. This task performed ZERO new public operations, and the original full human manuscript remained incompletely inspected. No priority or general-method novelty claim is earned.

## Investment decision

Bank the narrow positive forecast and its teacher-information ceiling together. The conditional gain does survive generation of later behavior in this fully known environment; that observation does not establish a useful human learning mechanism or explain the mouse forecast gap. Further fitting, larger particle sweeps or condition-effect/equivalence repair on these people would not remove the information limitation. Close this bounded author allocation without tuning.

If the PI uses this result in a consequential synthesis, the next useful allocation is a fresh independent challenge to the exact teacher-information and kernel interpretation, with its own reproduction and strongest contrary. A genuinely new test of generated-teacher acquisition needs a separately justified teacher law whose future realizations are unavailable to the forecaster. Do not silently manufacture that law from the existing bias labels or open a protected/new source automatically. The present benchmark alone cannot complete the native scientific goal.

## Preservation and resources

The same reservation resumed at20:26:12Z on November2, retaining603active seconds before the human pause. Effective feasibility/freeze/hard limits were20:41:09/20:51:09/21:46:09Z. Last scientific audit finished20:37:40Z. Every completed scientific command exited0; the human-pause-denied feasibility write and earlier read-guard denials remain recorded. Feasibility stdout was too verbose and tool-truncated; full output artifact survives. No numerical failures or main-score rescue occurred.

The original134,562,545-byte CSV was not reopened. Both cached numeric partitions were fully decoded (80people/48,000rows, all already consumed). Source builder and ten source workbooks were inspected; no new participants, protected outcomes, public operations or ingress. Observed scientific peakRSS167,854,080bytes against800MB; one scientific process/numerical thread. Conservative cumulative read/hash/decode booking is450MB against500MB, containing128,339,569explicit recorded bytes through record-only closeout and allowances for earlier context/import/runtime/output overhead. This is **not measured physical I/O or a proved complete-I/O upper bound**; exact runtime reads, physical I/O and tool/host peaks remain unknown. Preserve that accounting limitation. [RESOURCES.json](RESOURCES.json), [SOURCE_PINS.json](SOURCE_PINS.json), [environment](ENVIRONMENT.json).
