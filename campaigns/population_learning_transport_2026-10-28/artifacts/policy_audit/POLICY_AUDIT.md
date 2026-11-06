# Independent policy prediction audit

Completed 2026-10-28. No new source 26 prefixes/outcomes and no external raw prefixes/outcomes were opened. This audit reads only the already-consumed source histories, published task methods and pinned code.

**The large prediction is reproducible, but most of its size depends on the adaptive correction/side-sampling loop.** This is a scientifically relevant prediction about the complete generated trainer. It is not evidence that a harder contrast distribution improves biological learning. The frozen source population test remains worthwhile; it must precede any protected external forecast.

## Independent reconstruction

The exported model hash is `c7f675d18f4143891ed7d2c76d91f74be74da9565fbae5407952768e2c146940`. Every file directly pinned in RNN_FREEZE.json agrees. This implementation directly loads matrices and independently computes transformed contrasts, GLM probabilities, GRU gates, hidden-state updates, ReLU layers and additive weight updates. It independently samples the fixed trainer, computes correctness and summarizes exact100% observed trials and read-only probability probes.

The same 64-particle, four-prefix preflight is reproduced to maximum metric error 5.55e-16; prefix probability/weight/hidden reconstruction error is at most 2.22e-15. The actual preflight used 64 particles, not 512. The original source production files used 512. Same simulation seed, state uncertainty and common engagement draws were preserved. No model was fitted.

Native choice +1 is a leftward decision/rightward wheel movement; physical-right stimuli require choice -1. Positive transformed right contrast therefore raises the correct-right probability, while the left coefficient acts on negative contrast. Omissions remain failures in accuracy denominators and leave both actor states unchanged. Current-trial predictions are computed before the current action and feedback update.

The pinned original `TrialParamHandler._next_position` and `_next_contrast` methods were AST-extracted and exercised on 143 controlled position/probability cases and 24 correction-branch cases. All agree. On correction trials, recent choice +1 frequency increases right-stimulus probability, countering that decision tendency. Its saved side probability also controls the following adaptive draw before returning to 0.5. The source's response-buffer sign and one-trial carryover match the frozen simulator. The earlier original-code 1,800-transition adaptive-pool comparison and 700-trial prefix reconstruction were also rerun successfully.

All eight consumed prefixes have indexed finite repNum. Reconstructing their trainer summaries reproduces saved production pool, 12.5%-counter, session, reward and gain metadata (PREFIX_TRAINER_CHECK.json). Prefix initialization uses saved three-coefficient MAP calibration; recurrent memory comes from the entire 1,000-opportunity prefix, with the same rank-three Fisher perturbations. Neither biological prehistory nor a free hidden state is fitted.

## Magnitude and fragility

On the original four prefixes, the independently reconstructed primary contrast is +25.34 pp at observed±100% trials and+23.91 pp for identical probability probes. On eight hash-selected consumed prefixes, these become 23.87 pp and 22.40 pp, with conditional Monte Carlo SE 0.43 pp and 0.39 pp. All eight are positive, but one is only 11.48 pp; between-prefix SD is 5.16 pp. This additional variation warns against treating the four-prefix spread as population certainty.

The table gives fixed-minus-adaptive percentage points. Only the primary row uses eight prefixes; every sensitivity uses the original four. Variants were specified before running them and none was selected as a new primary law.

| Variant | Prefixes | Observed±100% | Identical probability probe |
| --- | ---: | ---: | ---: |
| Original policy contrast (first 8 prefixes) | 8 | +23.87 | +22.40 |
| Adaptive correction disabled | 4 | +6.15 | +6.19 |
| Faster adaptive promotion | 4 | +24.98 | +23.59 |
| Slower adaptive promotion | 4 | +25.21 | +23.82 |
| Fixed mix also includes 50% | 4 | +24.62 | +23.22 |
| Fixed only 100/50% | 4 | +19.26 | +17.84 |
| Zero recurrent memory at forecast onset | 4 | +25.61 | +24.08 |
| Static 1000-prefix current coefficients | 4 | +19.23 | +17.72 |
| Future update output multiplied 0.9 | 4 | +24.69 | +23.46 |
| Future update output multiplied 1.1 | 4 | +25.75 | +24.23 |
| Prefix-static omission probability | 4 | +25.17 | +23.76 |
| Zero omissions | 4 | +25.18 | +23.78 |
| Future boundary retention 0.8 | 4 | +20.41 | +18.82 |
| Future boundary reset to prefix endpoint | 4 | +12.34 | +10.17 |
| Future session-start actor input zero | 4 | +25.10 | +23.72 |

Disabling adaptive correction reduces the original-four contrast from 25.34 pp to 6.15 pp. Keeping only 100/50% contrasts in an independent balanced fixed trainer still produces 19.26 pp over primary adaptive training. In primary standard runs, 44.8–64.6% of generated trials are corrections and 96.5–98.8% are 100/50%; without correction, simulated actors more often reach low-contrast stages. Thus the model's complete closed loop, including correction-related side allocation, is the main diagnosed source of the large extrapolation. This is a conditional simulation intervention, not a unique biological mechanism.

No sign reversal occurred in the bounded checks. Initialization and session assumptions change the magnitude substantially: static current coefficients yield 19.23 pp and resetting every future session to the prefix state yields 12.34 pp. Retention and scale checks change only future dynamics while preserving the permitted prefix; they are deliberately diagnostic perturbations, not coherent alternative fits or parameter-posterior intervals. No architecture or parameter tournament was run. Across every audit simulation, absolute weights remain below 6.21 and hidden coordinates below 0.998. This establishes finite-horizon numerical stability for these runs; it does not prove asymptotic stability or biological validity.

## External trainer and unavoidable limits

The primary [Pan-Vazquez et al. article](https://pmc.ncbi.nlm.nih.gov/articles/PMC11579926/) was checked again. Results describe four uniform contrasts and absence of shaping/debiasing; the methods include 50% as a fifth value. The previous permitted input-only first-session audit found exactly 1,.25,.125,.0625 and side probability 0.5. The independently reconstructed primary fixed sampler uses those four contrasts uniformly, independent balanced sides, no correction and binary correctness. The fifth-contrast sensitivity retains a large 24.62 pp prediction. The exact custom FPChoiceWorld acquisition source was not recovered in the prior bounded search; publication plus one-session inputs do not certify every later session. A source gate followed by a frozen external policy/coverage audit is still required.

Reward-volume and wheel-gain metadata differ between policies but are absent from this actor's inputs. Their numerical changes cannot explain the simulated contrast: the actor sees only binary correctness and contrasts/session-start/action. This also means the actor has no tested invariance to reward-amount or movement-dependent learning. Missing rewardVolume in a later mixed-format source read must remain unavailable rather than being described as measured; it is inactive to this binary actor.

The forecast conditions on realized session starts and opportunity counts. It does not model attendance, calendar time, RT, fatigue or outcome-dependent stopping. Any later external result concerns bundled lab/animal/policy differences. The matched±100% observed endpoint uses generated high-contrast trials; the latent probe is a distinct read-only probability query and is never substituted for observed accuracy.

## Reproduction and decision

From repository root:

```sh
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 campaigns/learning_rule_transport_2026-10-28/.modelenv/bin/python campaigns/population_learning_transport_2026-10-28/code/policy_audit.py
```

The last complete run took 54 seconds with empty stderr. RESULT.json contains all variants, individual prefixes, generated contrast/repeat frequencies, weight checkpoints, exact source-method controls and source pins. PARTICLES.npz preserves the per-particle trajectories; PINS.json records code/model/bank/result hashes. The prefix-trainer crosscheck independently reopens the already-consumed prefix arrays and compares `VectorTrainer.from_prefix(...).state_summary()` with each saved original metadata summary, broadcasting the common state across 64 rather than 512 particles. No new or external access is needed for any check here.

Proceed with the prospective population source gate. The giant extrapolation is not a detected numerical/sign artifact, but its dependence on correction dynamics must remain central to interpretation. Do not replace the full external mixed policy with an all-easy trainer; the latter was only a diagnostic intervention. Do not treat the small conditional Monte Carlo errors as biological calibration or certify a changed-policy forecast before actual external-prefix initial states are available under the frozen release rule.
