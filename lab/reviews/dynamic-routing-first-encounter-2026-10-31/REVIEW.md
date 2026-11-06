# Independent review: bank a narrow channel result; transfer remains unscored

**Decision:** bank the independently reproduced disagreement between exported lick timestamps and task-controller responses, preserve the frozen scoring stop, and close this source/fitting allocation. Narrow any implication that the first-encounter outcomes themselves are inconsistent. None of the three discrepant rows is a selected first encounter, and the available evidence does not identify a hardware fault or invalidate the archive. Cross-stimulus forecast utility remains unresolved.

Reviewer `01a19536-325a-7410-a689-b87e130531cc` is a fresh Sol/max context, distinct from both investigators. All work was offline in this review path after registered START. No author helper was imported or executed. No real evaluation loss, replacement cohort, revised gate or refitted model was produced.

## What was independently reconstructed

[FIRST_CALCULATION.json](FIRST_CALCULATION.json) decodes actual cached compressed columns with the pinned Numcodecs 0.12.1 C-Blosc implementation: development 538 rows/21 columns and three evaluation sessions totaling 1,594 rows, with both additional evaluation controller-response vectors. All finite exported lick timestamps occupy their own half-open windows; stimuli are strictly ordered, windows end before the next stimulus, delivered-reward flags match finite water times, and prior rewards precede the next stimulus.

| Source row, zero based | Independently decoded result |
| --- | --- |
| 713655, 402 | `vis-`, false response flag, missing controller response, exported lick at 5435.55572 s; window 5434.66394–5435.58140 s. |
| 759434, 367 | `vis-`, false response flag, missing controller response, exported lick at 4640.38652 s; window 4639.48181–4640.41595 s. |
| 713655, 54 | Controller response 2850.76569 s, contingent reward 2850.78235 s, exported lick 2850.97689 s. Water follows registration by 0.01666 s and precedes the exported lick by 0.19454 s. |

Full evaluation controller vectors have 172/183 finite entries and exactly agree with every binary response flag. The development controller vector also agrees with its 162 flags. All contingent deliveries follow the available controller timestamps. These are checks of exported channels; original sensor events were not inspected and exported lick times are not independently established physical ground truth.

[SOURCE_SUPPORT.json](SOURCE_SUPPORT.json) verifies the cached PyPI wheel digest, 4,304 trusted-decoded reward bytes against the frozen decoded reference, three predecessor artifact pins, four distinct subject/session scalars, each asset's CC-BY-4.0 declaration, the capsule's different-mice statement and two Git blob identities. All four session dates follow the historical caveat. Time is interpreted in the NWB interval convention of seconds on the session reference; the actual per-column descriptions are reproduced. No separate sensor-clock calibration or instrument deployment is certified.

## The frozen contrary diagnostic

[CONTRARY_PLAN.md](CONTRARY_PLAN.md) was saved before independent raw reconstruction. [CONTRARY.json](CONTRARY.json) tests row/window/controller interpretation and endpoint-history relevance as one coherent postvalidation diagnostic.

Each discrepant exported timestamp belongs uniquely to its own response window, rather than a neighboring row. Changing a half-open interval to a closed interval does not remove either false-flag case. Those timestamps precede the exported window stops by 25.68/29.43 ms. Even moving the stop earlier by one **hypothetical nominal 60 Hz frame** leaves them inside. This arithmetic does not certify the actual frame clock, conversion offset, detection latency or sampling rule.

The cached development task script admits a controller response on a half-open frame interval and records a session frame, with contingent reward issued through that branch. Its input-sampling superclass, raw sensor-to-NWB conversion and the three evaluation commit bodies are not available in this cache. The schemas describe an older early-registration bug and true-flag/missing-time caveat; these later false-flag/finite-time observations have the opposite direction. The code and dates therefore do not identify recurrence of that bug or any unique cause. Differing acquisition/detection/window conventions remain possible but unverified.

Independent selection exactly reproduces five first encounters per evaluation mouse. **No discrepant row is an endpoint, and substituting a finite-lick indicator would leave all 15 selected outcome labels unchanged.** The reward-order case uses the same recorded binary response and delivered-water input under either timestamp interpretation; neither lick timestamp enters the predictor.

The two `vis-` disagreements precede the last selected encounters, rows 431/461. A descriptive hypothetical input comparison changes only `global_response_0.1` and `global_response_0.3` there, with largest absolute feature differences 0.0052334763 and 0.0000055533. All other evaluation endpoint features and both shared-context features are unchanged. No hypothetical-channel probabilities or losses were scored. This narrows the scientific relevance of the discrepancies while retaining the predeclared gate failure.

## Forecast, freeze and control checks

[PINS_AND_FREEZE.json](PINS_AND_FREEZE.json) verifies all 12 frozen artifacts, 95 acquired-response pins, 160 stable author artifact pins and all three forecast files. The 03:32:36Z freeze precedes initial evaluation trial acquisitions at 03:32:38.950437–03:32:55.837536Z; forecast pins were saved at 03:33:27Z. In frozen `score()`, the invalid-gate assertion is at line 52 and the first loss call at line 56. Independent checks reproduce the invalid gate; primary/trial score files are absent. This is static guard inspection plus independent data reconstruction, not execution of the author's score command or a claim to prove every historical action.

[FORECAST_RECONSTRUCTION.json](FORECAST_RECONSTRUCTION.json) independently implements all 30 features, main/instruction-ablation paths and frozen-parameter predictions. All 12,752 probabilities match within 3.33e-16. Current/future response/reward perturbations at four positions per session leave current/past features identical; removing privileged selection labels also leaves main features identical. Raw chronology makes all earlier recorded outcomes available before the next stimulus. Development/CV/control model refits were not independently repeated.

[CONTROL_RECONSTRUCTION.json](CONTROL_RECONSTRUCTION.json) reconstructs every saved synthetic loss/expected loss and practical decision from 960 rows. Both generators pass 0/32. R-generator mean expected **fitted** R-over-C gain is 0.0109671718 nat, with replicate means −0.0069526 to 0.0322033; C-generator mean is −0.0044455680. [GENERATOR_SUPPORT.json](GENERATOR_SUPPORT.json) independently regenerates 256 complete sequences/137,728 synthetic rows and matches all 960 saved endpoint truths/outcomes, with truth-probability error at most 1.11e-16.

That expectation compares two fitted forecasts against known generator probabilities conditional on simulated history. It is not an optimal-C oracle gap. A coefficient of four is not a certified 0.05-nat increment; 0/32 is not a calibrated miss rate for such an effect. Full hyperparameter-selection calibration, independent schedule variation and population coverage remain unrun.

## Interpretation and allocation

The verified contribution is a finite export/channel distinction and a faithfully preserved protocol stop. The contrary result rules out three selected-label errors and finds small, specific history differences under a hypothetical channel substitution. It does not earn the original predictive comparison, show absent/equal biological updating, or establish global data invalidity. Source BasicRL/ContextRL comparisons are already cached; full publication priority remains uncertified and no novelty is claimed.

Close further fitting/source repair on this consumed allocation and let the PI reallocate. Do not score the passing mouse alone, change the response law after evaluation, or open a third acquisition grant. All 2,132 real rows, controller vectors and earlier notebook/schema/five-session summaries remain consumed. Protected lab data were not accessed. [RESOURCES.json](RESOURCES.json), [EXPOSURE.json](EXPOSURE.json) and [UNRUN_CHECKS.md](UNRUN_CHECKS.md) preserve accounting and limits. This review endpoint does not stop the continuing lab or its heartbeat.
