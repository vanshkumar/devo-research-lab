# Training-policy reconstruction and causal simulation

2026-10-28. Owned by trainer subagent. All checks below use source code, metadata,
synthetic learners, or stimulus/probability inputs. No real choice, feedback,
reward, accuracy or acquisition curve was read for this reconstruction. The two
feasibility first-session files were inspected only for distinct
`contrastLeft,contrastRight,probabilityLeft` triples; this additional input
exposure was reported to the data/lead agents.

## Standard adaptive policy

Pinned original source is in `sources/trainer/`, with byte hashes and exact raw
GitHub URLs in `sources/trainer/MANIFEST.json`. Source repository is
[IBL iblrig](https://github.com/int-brain-lab/iblrig). Six historical versions were
checked: 3.8.1 (`819d45f`), 4.1.3 (`ce49ed7`), 5.3.1 (`c6aeb27`),
6.3.1 (`4d93f67`), 6.4.0 (`9177b85`), 6.4.2 (`0ee17a1`). These span early and
dominant metadata versions. The cached standard3391-session version distribution
includes6.3.1=556,6.4.0=472,6.1.3=420,6.2.5=264,5.3.0=258,4.1.3=227,
5.2.9=179,5.2.7=179; this audit is representative, not verification of every
minor version/operator settings combination.

`AdaptiveContrast._update_buffer/_update_contrast/_update_contrast_set/
_min_trials_at` and `TrialParamHandler._next_contrast/_next_position` are
AST-identical across all six pinned versions. Settings for these operations also
agree. The original docstring mentions resetting the buffer when a contrast is
added, but the actual update code does **not** call `_reset_buffer`; simulation
follows the executable code.

The initial contrast pool is100%,50%. Each side/contrast has a50-slot binary
correctness buffer, initialized to zeros. Only adaptive (noncorrection) trials
update this buffer. The exact binomial criterion gives40; code requires a sum
strictly above40, independently on both sides, at both100% and50% before adding
25%, then independently at25% before adding12.5%. Count subsequent adaptive
trials with12.5% in the pool; add6.25% at200, zero at400, and remove50% at600.
All available nonzero contrasts receive equal sampling probability; zero
receives half that mass. This differs from the full biased task's zero mass.

An incorrect or omission trial at100% or50% invokes a correction trial until a
correct response; other contrasts do not. A correction repeats contrast
magnitude, **not necessarily stimulus side**. The source retains a10-trial
wheel-response buffer, initialized with zeros. It samples a normal random
number with mean the recent wheel-right fraction and SD0.5, shows left if the
sample is below0.5, otherwise right. The returned probabilityLeft is one minus
that wheel-right fraction; the next noncorrection side draw uses this saved
probability before resetting it to0.5. The simulator retains this one-trial
carryover rather than forcing all noncorrection draws to0.5.

Raw ALF choice is wheel direction: +1 means a **left decision**, -1 a right
decision,0 omission. Both model and trainer APIs use this raw convention.
Signed stimulus is contrastRight-minus-contrastLeft, positive on the right.
`sample()` returns physical `side`=-1left/+1right and `correct_choice=-side`.
At zero contrast, hidden assigned side is still sampled and determines reward.
`observe(choice)` computes correctness and feedback itself. An omission has
feedbackType=-1 and rewardVolume=0; it is never recoded as a right response.

Session reset preserves adaptive contrast pool/buffers/counter, clears
correction and response buffers, and resets probabilityLeft to0.5. Source
session-level reward decrements0.1uL if the preceding session had at least200
trials (floor1.5uL for sucrose,2uL for plain water). A shortfall relative to
1mL per25g body weight overrides with a0.1uL increment. Later5.x/6.x branches cap
at3uL; inspected3.8.1/4.1.3 lack this cap. `version=` selects this difference.
Source wheel gain becomes4deg/mm if the preceding session reached200trials,
otherwise8; it is returned as metadata. There is no fitted wheel plant in this
behavioral model, so influence of gain is a residual observation-model limit.

No body-weight series or per-session operator settings are in the saved cache.
Default simulation assumes25g and sucrose-water floor1.5uL, initializing
delivered reward from positive rewards in the permitted prefix. A fixed reward
policy and correction/promotions envelope are exposed as planned sensitivities.
Future actual reward volumes, contrasts, probabilityLeft or repNum must never
enter autonomous calls. `from_prefix` accepts only a prefix dictionary; exact
repNum is used where indexed, otherwise correction status is causally inferred
from prior high-contrast errors. Observed prefix contrast levels inform the
minimum available pool. Hidden biological pretraining can leave older buffers,
counter and pool uncertain; it is not silently filled from future trials.

## External fixed policy

[Pan-Vazquez et al.](https://pmc.ncbi.nlm.nih.gov/articles/PMC11579926/) describes
uniform random nonzero contrasts, fixed3uL correct reward, no shaping/debiasing,
60s response window and1h sessions. The results section lists100%,25%,12%,6.25%;
the methods additionally lists50%. The saved fip_13first-session stimulus inputs
resolve the executed sample as exactly1,.25,.125,.0625 on each side, with
probabilityLeft0.5 throughout. The generator uses those four nonzero values,
uniform contrast and independent equiprobable side, fixed3uL, no correction,
no performance-dependent contrast/reward decisions. Its error/omission
feedback is-1 with no reward. Every cached ordinary Pan session is labeled
FPChoiceWorld6.4.2, which is a custom task not present in the public historical
iblrig main tree or the pinned Pan analysis repository. The index contains no
taskSettings; public S3 raw-behavior directories for the two feasibility
sessions contain no settings (Pan contains only stimulus-position recording;
standard has no indexed raw objects). Searches of the public author analysis
repository and main task trees did not recover the custom acquisition source.
Thus publication plus checked inputs support the external generator; exact
custom acquisition-code reproduction is **unresolved**, not falsely certified.
This remains an external-trainer uncertainty if the source gate earns transfer.

## Exposure and stopping scope

The lead conditions on realized future numbers and boundaries of task
opportunities. These are supplied as opportunity information to every actor.
The simulator neither replays adaptive stimuli nor forecasts calendar time,
training attendance, trial duration, task cessation, or operator decisions.
Original standard stopping code checks45min with<=400trials, latest20median
RT>5times overall median after400trials, and a90min maximum, plus task2000trial
limit/operator stop. Those policies depend on RT/time/handling absent from the
compact actor; conditioning on opportunities is an explicit scope limitation.

## Runnable verification and interface

```
.venv/bin/python campaigns/learning_rule_transport_2026-10-28/code/trainer.py \
  --self-test --output campaigns/learning_rule_transport_2026-10-28/logs/trainer_self_test.json
```

Tests execute the **original pinned**6.4.2AdaptiveContrast class, extracted by
AST from its saved source bytes, alongside the campaign implementation for1800
known synthetic transitions. Pools/counters agree at every step and the maximum
buffer-sum difference is0. A700-trial synthetic prefix reconstruction spanning
three sessions exactly recovers pool, buffer sums,12.5counter, correction,
response buffers, session counts/water, reward, gain and side-probability state.
Same-seed forecasts match exactly; perfect learners progress through the
curriculum; omissions never earn reward or promote; session transitions clear
correction; external samples include exactly the four contrasts and3uL rewards.
These establish computational fidelity of the audited branches, not full
biological trainer fidelity or calibration of forecast uncertainty.

```
trainer = VectorTrainer.from_prefix(prefix, n_particles=256, seed=seed,
                                    protocol='standard', version='6.4.2')
stim = trainer.sample()          # arrays, no future observations accepted
outcome = trainer.observe(raw_choice_array)
trainer.new_session()           # at supplied opportunity boundary only
```

`correction=False`, `promotion='fast'/'slow'` (>35/>45 rather than>40),
`reward_policy='fixed'`, and version-dependent cap provide a bounded mismatch
envelope. They are diagnostics, not automatically selected from validation.
