# A learned evaluator can reward attenuation that worsens its target match

Completed 2026-10-28. One already-consumed synthetic plant and its frozen trained source circuit; no fitting, new empirical outcomes or actor training.

**The circuit prefers the correct amplitude at the exact target, but attenuation becomes misleading away from that target.** At motor offset1, reducing signed auditory-drive gain from1 to.5 lowers circuit cost from2.0004 to1.8730Hz while increasing true target loss from1.2740 to1.6370 (+28.5%). The true-loss-optimal grid gain is.75, with loss1.2055. Thus the result is not simply that all amplitude reduction is harmful: the learned evaluator prefers too much reduction in this example.

| Motor offset | Circuit-preferred gain | True-loss-preferred grid gain | Circuit cost at gain1 → preferred gain | True loss at gain1 → circuit-preferred gain |
|---:|---:|---:|---:|---:|
| 0, exact target | 1 | 1 | 1.4431 → 1.4431 | 0 → 0 |
| .25 | 1 | 1 | 1.4877 → 1.4877 | .1065 → .1065 |
| 1 | .5 | .75 | 2.0004 → 1.8730 | 1.2740 → 1.6370 |
| 2 | .25 | .75 | 2.6699 → 2.0030 | 2.9205 → 2.9801 |

All minima are over the declared finite grid, not optimized global minima. A common gain was applied across all six contexts. At the exact target, individual context-window grid minima occur at gains1,1.25,1,1,1.25,1; the aggregate minimum is1. These window scores include history under the common gain and do not identify separate optimal gains for independently manipulated contexts.

## Precisely what gain means

`PREDECLARATION.json` specified gains0,.25,.5,.75,1,1.25,1.5,2 and motor offsets0,.25,1,2 before the32 probe cells ran. The original feature plant produces centered, signed vectors with standard deviation2. We multiply its output **after** normalization and projection to the600 E neurons, without renormalizing. The source model adds this signed `aud` term directly to membrane drive. Gain therefore scales both positive and negative auditory drive around zero; it does not multiply total neural firing or a positive baseline.

HVC timing, recurrent weights, initial state, zero dynamical noise and the six120-ms scoring windows remain fixed. Gain0 means **absent auditory drive during the ongoing premotor sequence**, analogous to failed output/deafened-like feedback. It is not literal nonsinging, which would also remove the premotor signal. At exact-target shape, gain0 costs2.0592Hz versus1.4431Hz at gain1: zero auditory drive does not beat the target here.

The gain range corresponds to active-pattern drive standard deviations0–4 in model units, with nominal target standard deviation2. For the target, gain1 spans approximately−1.15 to+11.53 input units, and gain2 doubles that range. These are not calibrated sound-pressure levels, microphone amplitudes, or validated physiological variation. The intervention is valid for the specified model input, but a physical amplitude manipulation through the original normalizing auditory encoder could behave differently.

True loss is mean squared difference between the100-channel gain-scaled feature vector and the original gain1 target. It is computed independently of neural reward. For a wrong shape, reducing gain can honestly improve squared error. The independent quadratic calculation uses `L(g)=g² E[y²]−2g E[y target]+E[target²]`; continuous optimal gains are1,.9867,.8408,.6349 for the four offsets. The evaluator's preferred.5 and.25 gains lie below both the corresponding continuous and grid optima. Its excess losses above the best grid alternatives are.4315 and.5398.

## Decision

This supplies a concrete reason to run a full joint shape-and-gain learning study: **does the actor escape this misleading reward direction and reach the target, or does it learn persistent attenuation?** The positive normalized-plant pilot and the present reward conflict can both be true. Neither this grid nor the existence of a lower-cost attenuated wrong output proves a learning trap, failure of all sensory evaluators, or a defect in the paper's explicitly simplified demonstration.

A consequential next study would measure complete fixed-budget trajectories on held-out entire plants and targets, comparing learned and oracle evaluators with matched exploration and initial conditions. It should separate generic amplitude constraints from supplied timing support. This bounded preflight ends at the declared grid; no repair, finer search, new circuit fit or full actor campaign was performed.

## Verification and replay

All32 probes repeated exactly. Separately written feature-map algebra agrees within3.56e−15, quadratic true losses within1.78e−15, and a separate implementation of the frozen circuit equations reproduces two target-amplitude probes within4.45e−16. Gain1 and gain0 reproduce the original pilot's target and absent-auditory-drive results exactly. Hashes verify that read source files and the previously generated state remained unchanged. The entire grid and checks took8.17seconds.

`RESULT.json` contains all32 cells, all six context scores/losses, source hashes, timing and verification. Run from the repository root:

```sh
campaigns/learning_rule_transport_2026-10-28/.modelenv/bin/python experiments/sensory_evaluator_amplitude_preflight_2026-10-28/run.py
```

The source remains gongziyida/vocal-error-network commit `8309db5b1e2abb0d937fec7a1f9d434b06a9bd7c`, using the existing locally generated state in `experiments/sensory_evaluator_preflight_2026-10-28/`. This is computational verification on development material, not independent scientific replication.
