# Postvalidation strongest published architecture challenge

Recorded 2026-10-28, after the initial DNN/RL source evaluation. This does not
restore an untouched source holdout. The original source test, its exposure
record and frozen files remain intact. An independent adversarial review
identified omission of Liu/Geadah/Pillow's strongest published RNNGLM as the
most consequential outstanding model challenge. The lead authorized this
bounded extension before the first RNN fit: one fixed seed557, the original
62 training/12 development-validation animals, a1000-epoch ceiling and no
source or external outcome access by the implementation/fitting worker.

The challenge is a diagnostic expansion after validation. It must be reported
as such even if it passes the source forecast gate. The external cohort remains
sealed unless a substantive rule meets the unchanged source performance and
calibration requirements. The lead predeclares the multiplicity adjustment for
five rule candidates and two baselines (lower bootstrap percentile.005) before
the RNN's source scoring.

## Architecture and fitting choices

Use the exact pinned source `DeltaRNNGLM` class in
`artifacts/models/source/liu_models.py`, commit
`0ae19f7eec2836ab05487cc0342c7d1ac51a2727`, configured as in the source main
script: `DNNfirst=False`,32hidden GRU units, two32unit ReLU layers,
`num_weights_mode=1` (right/left contrast and bias). A three-vector of trainable
scales multiplies each additive GLM coefficient update. The source's unused
`fc` layer is retained for exact parameter initialization/state mapping. There
are6438source parameters, of which96in that layer are inactive in RNN-first
mode. The model's32dimensional memory is generated causally; it is not fitted
as an extra individual parameter.

The GRU input is the current GLM state plus the completed trial's transformed
signed contrast, constant1, session-start flag, binary choice, binary reward
and stimulus sign. It predicts the next trial's policy after the completed
trial's feedback. Current/future choice and reward cannot enter the current
prediction. The source contrast transform is `tanh(5contrast)/tanh(5)`.
Reward volume and wheel gain are untested omitted actor inputs in this RNN as
well. Correct trainer branches cannot by themselves test a policy's response
to those quantities when they never enter its decision/update function.

The source optimizer is Adam(lr=.001), with StepLR(step_size=5,gamma=.999),
without weight decay or gradient clipping. Use500trial truncated gradients;
accumulate chunk gradients and take one optimizer step per epoch. Each animal
receives equal total likelihood weight, retaining the first campaign's
observation and initialization protocol. Training initializes its three GLM
coefficients from that animal's first200trials. At prediction, the frozen rule
calibrates only three initial coefficients using the first1000trials' causal
likelihood with the sameN(0,2I) prior/bounds as the first-stage models.

The sole scientific fit uses seed557 and up to6000trials per animal, retaining
short histories. Checkpoints every25epochs are selected by equal-animal
conditional response log loss on the same12development-validation animals.
No extra seed, architecture, learning-rate path or source-based tuning is
authorized by this challenge. Numerical failure would require a separately
recorded repair; a plateau is not a reason to stop the fixed ceiling early.

Omissions remain scored observations/training opportunities. Like the DNN
extension, they skip the published binary update; for this RNN that means
skipping both GRU memory and GLM updates. The common frozen omission/exposure
model supplies their probabilities. This is an explicit observation extension
of the source's omission-dropping binary preprocessing.

## Source and implementation audits

The exact source class is extracted using PythonAST, avoiding unrelated imports.
One-layer `nn.GRUCell` has the same recurrence as its `nn.GRU`; its weights map
directly from source `*_l0` parameters. On511synthetic binary trials with
session boundaries, original-vs-numpy maximum probability/weight differences
are2.53e−7/1.00e−6; final memory differs by1.15e−7. Vectorized numpy vs scalar
Numba probability differences are0 and hidden-state differences5.55e−17.
The500trial scripted training block matches eager loss exactly and gradients
within1.87e−9. See `artifacts/rnn/SOURCE_RECURRENCE_AUDIT.json`.

The small8animal/2000trial smoke and full62animal/6000trial five-epoch benchmark
remain saved under distinct tags. All losses and gradients are finite. Once
the scripted block warms, the full fit takes about.9seconds per epoch on the
ordinary local CPU (about15minutes for the fixed1000epoch ceiling). No paid
compute, GPU service or external model API is used.

`ROLLOUT_CONTINUATION_AUDIT.json` verifies that a full1500trial conditional run
equals a1000trial prefix plus500trial continuation exactly in both probability
and hidden endpoint. Intentionally dropping the hidden state changes later
predictions. This directly guards the failure where a generic state wrapper
keeps `w` but silently discards `h`.

## Autonomous forecasts and uncertainty

New files `rnn_learning.py`, `fit_rnn.py` and `rnn_rollout.py` leave every original
frozen scientific file unchanged. The separate rollout imports the same frozen
trainer, observation/exposure model, trajectory summary and score functions.
After the prefix it samples its own choices, obtains its own generated feedback
and updates its own weights AND memory. Only realized session opportunities
enter as future conditioning; actual future adaptive inputs are permitted only
in an explicitly labeled replay diagnostic.

Prefix calibration starts GRU memory at0 and constructs its endpoint from the
real calibration prefix. Finite differences estimate the likelihood Fisher
matrix for three initial GLM coefficients and endpoint Jacobians for both `w`
and `h`. The same three-dimensional Gaussian perturbation propagates jointly
into both states, preserving their dependence. This is a rank-at-most3 local
approximation, not a fitted32dimensional hidden posterior. A common scale cap
keeps the endpoint GLM covariance's largest eigenvalue at most4; linearized
hidden samples are clipped to the GRU's[−1,1] domain. The cap and clipped
fraction are saved for every animal. No new population update coefficient is
fitted during calibration.

The RNN uses the same512particles,1000trial prefix,500trial bins and
1000/3000/5000future horizons as the first-stage protocol. Its residual variance
scale is selected from the same0/.5/1candidate set using development-only
leave-one-animal-out primary-horizon CRPS. Save this under
`artifacts/rnn/calibration/`, without changing the original frozen calibration.
Both raw and widened forecasts must remain available. All mean, calibration,
per-lab and practical-improvement gate requirements remain unchanged.

## Runnable commands

From the repository root:

```
campaigns/learning_rule_transport_2026-10-28/.modelenv/bin/python campaigns/learning_rule_transport_2026-10-28/code/fit_rnn.py --audit
campaigns/learning_rule_transport_2026-10-28/.modelenv/bin/python campaigns/learning_rule_transport_2026-10-28/code/fit_rnn.py --fit --end 6000 --epochs 1000 --check-every 25 --seed 557 --tag main
campaigns/learning_rule_transport_2026-10-28/.modelenv/bin/python campaigns/learning_rule_transport_2026-10-28/code/rnn_rollout.py --split devcv --tag rnn_dev --particles 512 --horizon 5000
campaigns/learning_rule_transport_2026-10-28/.modelenv/bin/python campaigns/learning_rule_transport_2026-10-28/code/uncertainty.py --models rnnglm32 --forecast-dir "$PWD/campaigns/learning_rule_transport_2026-10-28/artifacts/forecasts/rnn_dev" --out-dir "$PWD/campaigns/learning_rule_transport_2026-10-28/artifacts/rnn/calibration"
```

Protected source CLI execution requires a separate challenge freeze supplied
with`--freeze`; external execution additionally requires its explicit gate.
Forecast bytes are saved before future outcomes are opened for scoring. The
fitting worker runs development commands only. The lead owns source scoring,
gate interpretation and the campaign's final stopping decision.


## Completed development handoff

The fixed1000-epoch run completed in858seconds. Seed557's best development
checkpoint is975, conditional response log loss.44961625 over11eligible
nested development animals. It remains a different cohort/observation protocol
from the paper; the paper's exact model ranking is not claimed reproduced.
The final export is `artifacts/rnn/rnnglm32_nested_best.npz` (identical to
`main_best.npz`), SHA256
`c7f675d18f4143891ed7d2c76d91f74be74da9565fbae5407952768e2c146940`.

All source/fitted/closed-loop audit artifacts were regenerated using this
FINAL hash. Against the exact source on6000development trials, maximum
probability discrepancy is2.90e−7 and future conditional log-loss discrepancy
4.86e−9. In2000self-generated trials, choices and rewards match the source
implementation exactly; maximum probability discrepancy is3.84e−7.

The first3eligible development animals by hashedID were used only to audit
initial-state linearization: mean absolute probability errors versus exact
prefix replays are.0185,.0175and.0453percentagepoints; the largest individual
probe discrepancy is.82percentagepoints. No hidden samples were clipped and
no endpoint covariance cap was active in these checks. This verifies this
local approximation at those development prefixes, not its universality.

The512-particle development forecast on10full3000-trial animals gives marginal
CRPS.054129, high-contrast MAE11.215pp,80%coverage91.67% and mean80%width36.19pp.
Conditional curve diagnostics give high-contrast MAE3.701pp and binary NLL.485749
at that horizon. These are development results, not source validation. The
same development leave-one-animal-out variance procedure selects residual
scale0: CRPS.054129/.054940/.057656 for scales0/.5/1. It supplies no residual
widening or mean rescue to the RNN. Its separate configuration and donor bank
are saved under `artifacts/rnn/calibration/`; original frozen calibration
files are unchanged.

The lead should freeze the three RNN files, final model, allocation/specification,
separate configuration/residual bank, and the original `protocols/FREEZE.json`
before source execution. The RNN CLI recursively verifies that original freeze
when linked. Pass the canonical model path explicitly with`--model` during
protected execution. All source gate/transport decisions remain with the lead.

## Offline forecast replay after source execution

The separate `rnn_reproduce.py` verifies both original and RNN freeze hashes,
blocks Python network connection entrypoints, and regenerates every one of the
48 eligible source forecasts with512particles. It selects only the original
first1000rows per animal; future opportunity boundaries come from the pinned
footer counts. Full-subject outcome loaders are disabled. No actual future
choices/rewards or external outcome files are opened by this replay.

All48forecasts replay exactly: maximum absolute difference0 across raw curves,
primary curves, GLM coefficient traces, GRU hidden endpoints, simulated counts,
trainer pools, seeds and future opportunity boundaries. Original prefix object
MD5/SHA256 pins and every frozen scientific artifact are checked before/after.
The run takes185.76seconds in the campaign's isolated Python3.12environment.
Replayed arrays and per-animal JSON/CSV records are preserved separately under
`artifacts/rnn/offline_reproduction/`; no primary forecast is overwritten.

```
campaigns/learning_rule_transport_2026-10-28/.modelenv/bin/python campaigns/learning_rule_transport_2026-10-28/rnn_reproduce.py
```

The default requires the complete48file set and fails when any forecast or
metadata file is missing. This establishes computational replay from original
prefix bytes, not an independent reconstruction of biological future scores.
See `offline_reproduction/RESULT.json` and `FORECAST_REPLAY.csv` for the exact
model/freeze hashes, environment, coverage and comparison record.
