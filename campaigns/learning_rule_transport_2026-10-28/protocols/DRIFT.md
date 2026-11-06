# Localizing conditional versus autonomous update dynamics

2026-10-28. Development-only analytical diagnostic, specified before source
validation. This analysis uses exact model artifacts, synthetic states/actions,
and the first1,000tasktrials of eight input-selected **development** animals.
No source holdout or external outcomes are read. It must be interpreted after
the empirical forecast test, not used as a substitute for it or as a proof that
all learning rules fail.

## Exact distinction for the fitted REINFORCE family

Let `y=1` denote a right decision, `p=P(right|response)` from the current model,
`z=1` the task's assigned correct side right, and `r=1[y=z]` on response trials.
Let `φ` be the three GLM features (right contrast, signed left contrast,1).
The implemented/source-family update is componentwise

```
Δw = (a + b*r) * (y-p) * φ
a = alpha * adder
b = alpha
```

The stored NPZ key`baseline` is this **adder**, not a subtractive reward
baseline. For a self-generated response`y~Bernoulli(p)`, at a fixed current
state and nonzero stimulus,

```
E[Δw | response,state,stimulus] = b*p*(1-p)*(2*z-1)*φ.
```

The reward-independent history term cancels exactly in the mean. With omission
probability`o` and update skipped on omissions, multiply this expectation by
`1-o`. It still contributes process diffusion. For a different teacher's
choice probability`q` supplied as actual intervening behavior,

```
E[Δw | teacher] = (1-o) * [a*(q-p)
                           + b*(z*q*(1-p) - (1-z)*(1-q)*p)] * φ.
```

Thus a large`a` can rapidly track another learner's choice innovations without
providing corresponding autonomous mean acquisition drift. This is an exact
property of the fitted family, not a critique of conditional log scores. It
does not imply that autonomous observable performance is constant: nonlinear
readout, diffusion, state dependence and trainer feedback all still matter.

The exact one-step covariance is also enumerated. On a response trial, the two
possible coefficient increments are

```
d1 = (a+b*z) * (1-p) * φ        with probability p
d0 = -(a+b*(1-z)) * p * φ       with probability 1-p.
```

Include the zero increment with probability`o`; covariance is the resulting
second moment minus outer(mean,mean). At zero contrast, the trainer independently
assigns hidden side50:50. We enumerate all four response/hidden-side
combinations. The autonomous mean is zero there for this RL family; a
hypothetical teacher with`q!=p` can still induce bias tracking.

## Executed diagnostic and provenance

`code/drift_analysis.py` snapshots each model's exact bytes before loading,
records its SHA256/metadata in`artifacts/drift/MODEL_MANIFEST.json`, and enumerates
local drift/diffusion on:

- symmetric sensory coefficients0,.5,1,2,4 with bias−2,−1,0,1,2;
- asymmetric sensory pairs(0,2),(2,0),(1,3),(3,1) with bias−1,0,1;
- a symmetric99%correct state with coefficients`logit(.99)` and bias0;
- eight metadata/hash-selected development prefix endpoints;
- eleven signed contrasts including zero and both session-start flag values.

Each row assumes omission probability.05; prefix-only comparisons instead use
that prefix's observed omission fraction. The state grid is diagnostic, not a
statistical sample of biological animals. Hypothetical teachers have correct
response probabilities.5,.7,.9,.99; none comes from animal future choices.

Current snapshot run uses DNN16(`dnnglm_nested_best`), fitted reward-offset
REINFORCE(`reinforce_nested_stable`) and pure-reward REINFORCE
(`reinforce_pure_nested`). It produces3,036local-state rows,912hypothetical
teacher rows and24prefix comparisons. A later capacity-model snapshot can be
added by explicit command; do not silently equate a different fitted artifact
with these saved numbers.

Eight prefix animals are selected by
`SHA256('drift_prefix:'+subject)` among development animals with at least1,000
indexed trials. They are SWC_036,ZM_1745,KS024,ZM_3002,DY_006,ZM_1371,DY_011,
CSHL_011. Original Parquet queries return only remaining prefix rows with
SQL`LIMIT`; fields are contrastLeft,contrastRight,choice,feedbackType,rewardVolume.
Exact source files, hashes and returned row counts are in`PREFIX_EXPOSURE.json`.
These records are an additional development-prefix exposure, not untouched
validation. The conditional prefix comparison is in-sample initialization
diagnostics and cannot establish prospective accuracy.

## What the current artifacts show

The fitted reward-independent and reward-dependent coefficient gains are:

| Model/coefficient | a(history) | b(reward) | a/b |
|---|---:|---:|---:|
| Fitted RL/right | .088462 | .002490 |35.529 |
| Fitted RL/left | .086635 | .004982 |17.388 |
| Fitted RL/bias | .205035 | .083158 |2.466 |
| Pure RL/right |0 | .002242 |0 |
| Pure RL/left |0 | .001036 |0 |
| Pure RL/bias |0 | .379962 |0 |

At a symmetric state`w=(1,1,0)`, both100%contrast sides have current conditional
correct probability.73106. For a right stimulus, fitted RL's own-action mean
right-weight increment is.0004651. If a hypothetical90%-correct teacher's
choices are supplied, it is.0147701: the history-innovation component is.0141976
and the reward component.0005725. This illustrates the information consumed
by conditional tracking; it is not a finding about an actual withheld animal.

Direct enumeration also computes the exact change in mean of the two100%
contrast correct probabilities **after one random update**, evaluated on both
probe sides. Averaging the learning stimulus equally over left/right, at the
same`w=(1,1,0)`:

| Current artifact | Mean correct-probability change after one update |
|---|---:|
| DNN16 |−.12399percentage points |
| Fitted RL |−.05808percentage points |
| Pure RL |−.03004percentage points |

This includes nonlinear consequences of update variability. Positive mean
sensory-coefficient drift does not guarantee positive one-step observable
acquisition when bias updates are large. For example, pure RL's bias learning
gain is much larger than its sensory gains. These are **local** evaluations at
a stated synthetic state, not integrated1,000trial changes, average biological
learning rates, or proof that the eventual long rollout decreases performance.
The DNN16's cross-coefficient updates can also help one side while hurting the
other. The actual empirical source gate determines whether these properties
are consequential for the data.

In the eight observed prefixes, fitted RL's mean actual conditional sensory
updates are.000557/.000863, versus own-action expectations.000166/.000323
at the same prefix states/inputs. DNN16 gives actual.000731/.000779 versus
own−.000223/.000595. These in-sample prefix summaries localize dependence on
real choice innovations and are not independent empirical validation.

## Known-answer numerical checks

For each model, seven seeded cases draw50,000independent actions at a fixed
state, compute feedback from the action's actual task correctness, skip no-go
updates and call the actual vectorized model recurrence. Cases include zero
contrast, both sides, asymmetric initial state, session start and99%-correct
states. There are21cases/1,050,000action samples in this run. Largest
standardized MonteCarlo mean discrepancy is2.806standarderrors. The exact
enumerated RL mean agrees with its analytical formula to4.18e−16.
The largest second-moment discrepancy is2.600standarderrors; full empirical
and exact covariance matrices are also saved for each case.
`MONTE_CARLO_CHECKS.json` saves each case's exact mean, MC mean, standard error,
state, probability and seed family. This checks correct action/reward semantics
and enumeration; it does not validate the biological update law.

## Reproduction

From repository root:

```sh
campaigns/learning_rule_transport_2026-10-28/.modelenv/bin/python \
  campaigns/learning_rule_transport_2026-10-28/code/drift_analysis.py \
  --dev-prefixes 8 --mc-actions 50000 \
  --models \
  campaigns/learning_rule_transport_2026-10-28/artifacts/drift/model_snapshots/dnnglm_nested_best.npz \
  campaigns/learning_rule_transport_2026-10-28/artifacts/drift/model_snapshots/reinforce_nested_stable.npz \
  campaigns/learning_rule_transport_2026-10-28/artifacts/drift/model_snapshots/reinforce_pure_nested.npz
```

The run is offline. Default models are explicitly named in the script and exact
copies are preserved under`artifacts/drift/model_snapshots/`. Future
reconstruction must use those copies if the mutable development filenames have
changed. Original-byte reconstruction of decisive source forecasts is a
separate task after the lead's freeze/evaluation.
