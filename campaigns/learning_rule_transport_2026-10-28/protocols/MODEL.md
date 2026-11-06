# Published learning-rule reconstruction

This document records development work before source validation. All model
fitting and model selection use `dev` animals only. The 62 nested training and
12 nested development-validation animals are frozen in
`artifacts/models/DEVELOPMENT_MODEL_SPLIT.json`. Development-validation animals
are not source holdout animals. Source/lab and external outcome files remain
sealed from this model worker.

## Exact source

Liu, Geadah and Pillow, *Flexible inference for animal learning rules using
neural networks*, arXiv2509.04661v2, 5February2026. The source repository is
`Helena-Yuhan-Liu/InferLearningANNGLM` at commit
`0ae19f7eec2836ab05487cc0342c7d1ac51a2727`. Exact original `models.py`, `main.py`
and `run_reinforce.py` are preserved under `artifacts/models/source/`.

* `models.py`, class `DeltaDNNGLM`, supports separate right-contrast,
  left-contrast and bias coefficients (`num_weights_mode=1`). Two ReLU hidden
  layers with 16 units approximate the additive per-trial coefficient update.
  The original source default is 32 units; 16 is this study's smaller fixed
  architecture. One source-default 32-unit capacity challenge is also run before source validation, without introducing another architecture.
* `main.py` lines 94–96 transform contrast as `tanh(5contrast)/tanh(5)`;
  lines 189–217 construct binary choices, reward, side sign and **previous**
  trial inputs. Prediction for trial t uses only updates through trial t−1.
* The DNN input is current three-dimensional coefficient state plus previous
  transformed signed contrast, constant 1, session-start flag, binary choice,
  reward and positive-stimulus sign. The source's side input is the redundant
  sign of the stimulus, including 0 at zero contrast, not an oracle hidden side.
* Binary reward is 1 when feedbackType>0 and 0 otherwise. Reward volume is not the
  reward covariate in this model, matching the published binary model. The
  trainer still generates its own reward schedule. Reward volume and wheel
  gain are untested omitted actor inputs: these policies cannot change their
  update because reward amount or wheel gain changes. Reconstructing those
  generator branches does not establish behavioral robustness to them.
* Source fitting uses a cross-entropy objective and truncated backpropagation.
  Our scientific fit uses 500-trial gradient truncation, source learning rate .001,
  two reproducible random seeds 221/337 and up to 1000 epochs. Checkpoints every 25
  epochs are selected using the fixed nested development animals' postprefix
  conditional log loss. A 150-epoch/truncation-100 preliminary fit is retained
  as a development pilot. Equal animal weights replace equal trial weights.
  Gradients accumulate over 500-trial chunks with recurrent coefficients
  detached at chunk boundaries, then one Adam step is taken per epoch. A
  fixed 1e−5 weight decay and unit gradient-norm clipping stabilize ordinary CPU
  fitting; these are declared fitting choices, not original-paper defaults.

The independent original-class/numpy recurrence audit in
`SOURCE_RECURRENCE_AUDIT.json` covers 233 synthetic binary trials with multiple
session boundaries. Maximum probability and coefficient differences are
1.014e−7 and1.924e−7, respectively; vectorized and scalar numpy recurrences
agree exactly. Original classes are extracted using Python AST to avoid
importing unrelated source dependencies. This verifies the recurrence and
causal trial shift; it does not reproduce the original paper's numerical
results or its different 12-mouse cohort.

## Omissions, initialization and cohort scope

Raw ALF choices are preserved: +1 means left, −1 means right, and 0 means omission. The
model returns P(right|response). The common three-category observation wrapper
used by the lead supplies omission probability equally for all models.
Omissions are scored and counted as training opportunities, but no binary
choice update is fabricated; the binary coefficient update is skipped.
This is an explicit observation extension of the source binary model.
The original pinned `DownloadingData.ipynb`, cell 8, drops rows whose choice is 0
and maps raw ALF +1 to left 0 and −1 to right 1. It also drops feedbackType 0. Our omission
handling preserves exposure time and restores that outcome category, rather
than copying this source omission exclusion into the acquisition endpoint.

Development fitting initializes each animal from a penalized static GLM fit
to its first 200 available trials. It includes all indexed trials up to 6000,
retaining shorter histories and omissions. This differs from original zero
initialization to accommodate the cache's uncertain true first
biological exposure. No outcome-dependent inclusion or learning inflection
selects the prefix or horizon.

At forecast time, only the fixed first 1000 task trials may calibrate the three
initial coefficients. `initial_state(prefix)` maximizes their prefix-only
causal conditional likelihood, with Gaussian N(0,2I) penalty and fixed bounds
right/left [−8,12] and bias [−6,6], then replays the observed prefix once to the
forecast state. The learned update law is frozen. It does not use any future
choice, reward, criterion-attainment label, smoothed weight or rate path.
`method='zero'` and `method='static'` provide declared initialization challenges.

## Canonical reinforcement-learning family

The REINFORCE model updates a three-coefficient logistic policy as
`Δw = α * (reward + adder) * (y−P(right)) * x`.
Each coefficient has its own α and adder, matching source dimensions.
The source `run_reinforce.py` estimates α and adder across training animals.
The source function `reinforce_base` in `simulate_learning.py` calls its
parameter `base` and computes `reward-base`; therefore its `base` is the
negative of the additive offset stored under our legacy NPZ key `baseline`.
The families are identical under that sign mapping. Numerical agreement of
the exact source REINFORCE recurrence is 1.11e−16 in coefficient space.

The first development fit with adder bounds ±1.5 reached its positive limit;
a justified bound sensitivity at ±10 also reached the positive stimulus limit.
Both fits and logs are preserved. To avoid dependence on this arbitrary bound,
the final source-baseline parameterization optimizes its algebraically
equivalent gains `a+b*reward`, with b=α in [1e−6,.5] and a=α*adder in [−.5,.5]. The
export retainsαand adder. A positive additive offset may make the rule largely a
choice-history tracker; its conditional fit alone does not establish autonomous
learning. A pure reward-driven REINFORCE control fixes adder=0 and estimates
only three α values with the same prefix access.

For this family there is an exact conditional/autonomous distinction.
If a virtual learner samples its own choice `y~Bernoulli(p)`,
`E[a*(y-p)*x | state,x]=0`. With a deterministic correct side `z` and
`reward=1[y=z]`, the mean update is
`b*p*(1-p)*(2*z-1)*x`. Thus the reward-independent gain can track actual
animal innovations when conditioned on their choices while adding no
autonomous mean acquisition drift. It still adds process variance. This is
an algebraic property of the fitted family, not a claim that all neural
learning rules must fail. The fitted source-baseline right/left coefficient
ratios `a/b` are 35.529 and 17.388; the bias ratio is 2.466. Main forecast evidence
is needed to determine whether this distinction is consequential here.

## Public API and reproduction

`learning_models.py` requires NumPy/SciPy. Numba is optional and accelerates
scalar likelihood/calibration. No torch is required for loading NPZ models,
forecasting or scoring. The isolated Python 3.12 environment `.modelenv` contains
torch 2.15.0, NumPy 2.3.5, SciPy 1.18.1 and Numba 0.68.1; exact dependency evidence is in
`artifacts/models/requirements-model-lock.txt` and `logs/model_dependencies.log`.

```
model=load_model(path)
state=model.initial_state(prefix)
p_right=model.probs(state,signed_contrast)
model.update(state,signed_contrast,raw_ALF_choice,feedbackType,session_start)
```

The trainer's internal physical side is −1 left/+1 right. Model updates accept
raw ALF choice +1 left/−1 right. The final `VectorTrainer.correct_choice` and
`rollout.choice` already expose **raw ALF** choices, so they enter model updates
directly with **no additional sign flip**. Only an independently generated
physical-direction choice would need conversion. `probs` and `update` support
batch arrays for Monte Carlo forecasts. Each autonomous call uses the generated
choice and generated reward. `sequence` is reserved for explicitly
conditional predictions that assimilate actual intervening observations.

```
.modelenv/bin/python code/fit_learning.py --audit
.modelenv/bin/python code/fit_learning.py --rl --end 6000 --stable-gain
.modelenv/bin/python code/fit_learning.py --rl --end 6000 --pure-reward
.modelenv/bin/python code/fit_learning.py --dnn --end 6000 --epochs 1000 --check-every 25 --seed 221 --truncation 500
.modelenv/bin/python code/fit_learning.py --dnn --end 6000 --epochs 1000 --check-every 25 --seed 337 --truncation 500
.modelenv/bin/python code/fit_learning.py --dnn --end 6000 --epochs 1000 --check-every 25 --seed 443 --truncation 500 --hidden 32
```

Commands are run with the campaign directory as CWD. The lead's offline runner
provides full exact commands. Forecast scores, uncertainty, source gate and external exposure are
owned by the campaign lead, not selected by this fitting script.

`MODEL_RESULTS.csv` and `MODEL_FIT_DIAGNOSTICS.png` summarize binary conditional
log loss after the first 1000 trials through at most 6000 total trials,
averaging animals equally when any postprefix response is available. This
model-selection diagnostic includes 11 animals (one other nested development
animal has no postprefix observations). Its horizon and binary observation
denominator differ from the main forecast protocol's 3000-trial,
three-category scores and complete 500-trial curve bins; these development
numbers must not substitute for the independently reserved source results.

## Completed prevalidation fits

All fits below completed before the lead's source validation freeze. No
all-development refit was performed; the nested training set remains 62 animals.

| Model | Selected checkpoint | Development conditional NLL | Final export |
|---|---:|---:|---|
| DNNGLM16, seed 221 | 1000 | .45095067 | `dnnglm_nested_best.npz` |
| DNNGLM16, seed 337 | 950 | .45157529 | `dnn_seed337_best.npz` |
| DNNGLM32, seed 443 | 950 | .44887320 | `dnnglm32_nested_best.npz` |
| Source-baseline REINFORCE | likelihood optimum | .44538036 | `reinforce_nested_stable.npz` |
| Pure-reward REINFORCE | likelihood optimum | .51001025 | `reinforce_pure_nested.npz` |
| Prefix static GLM reference | prefix only | .65913875 | computed in each model's CV records |

The source-default width32 challenge modestly improves on width16 in this
conditional selection diagnostic. Both remain behind the strong freely fitted
source-baseline REINFORCE family in this different cohort. They improve on the
pure reward-driven canonical model. This is an empirical reproduction of the
architecture and causal conditional-prediction capacity; it does not reproduce
the paper's full model-ranking result on its original 12 animals.

Exact final export hashes and the full small search/amendment history are in
`MODEL_SELECTION.json`; original source blobs are independently verified against
the pinned Git tree in `source/MANIFEST.json`. The model worker never opened
the source animal/laboratory holdout or external outcomes during this work.
