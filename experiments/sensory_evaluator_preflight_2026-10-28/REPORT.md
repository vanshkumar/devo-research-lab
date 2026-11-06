# A source sensory evaluator can improve an independently specified motor target

Completed 2026-10-28. This is a bounded computational feasibility test, not a new empirical campaign or a completed generalization study.

The published Gong et al. E↔I cancellation circuit ran locally at its full 600 excitatory/150 inhibitory neuron size. After 35 tutor renditions, its mean response to six synthetic target patterns fell from 9.8748 to 1.4431 Hz (85.39% suppression). The motor plant was drawn before the targets and was never fitted to them. Every target was exactly reachable.

The learned rate cost also supplied useful motor-update directions. From three preselected starting offsets, a fixed finite-perturbation update improved the true sensory target objective by 64.7–81.4% of the improvement from an oracle reward using the same queries and action-step norm. Thus a tutor-fitted motor dictionary is not necessary for this particular source circuit to supply useful teaching information. This does not show its supplied timing/context scaffold is unnecessary, identify the weakest sufficient scaffold, or establish natural vocal learning.

| Starting offset scale | Initial true loss | Loss after circuit-reward step | Loss after oracle step | Circuit improvement / oracle improvement |
|---:|---:|---:|---:|---:|
| .25 | .106499 | .079537 | .068780 | 71.48% |
| 1 | 1.273966 | 1.184337 | 1.163878 | 81.42% |
| 2 | 2.920452 | 2.858893 | 2.825273 | 64.68% |

Loss is mean squared difference in the synthetic normalized sensory-feature coordinates. It is not an acoustic similarity score or biological unit.

## What actually ran

The unchanged `EINet.sim`, `bilin_hebb_EI`, and `bilin_hebb_IE` functions come from gongziyida/vocal-error-network commit `8309db5b1e2abb0d937fec7a1f9d434b06a9bd7c`. Seven downloaded source files match that commit's Git blob hashes. Source code, primary article HTML, public reviews and manifest are saved in `sources/sensory_evaluator_feasibility_2026-10-28/`.

The circuit uses the source's 600E/150I/15HVC architecture, connection densities, weight distributions, transfer functions, time constants, E↔I plasticity parameters and 35 tutoring renditions. Target-independent Gaussian premotor bursts provide a fixed clock at the source's 150-Hz peak and 20-ms width. Each of six contexts contains a 100-ms sensory pattern; scored windows extend 20 ms beyond each pattern. The synthetic song lasts 900 ms plus 200 ms silence, with 500 ms burn-in. The source's progress display is replaced with an identity iterator because tqdm is absent. No numerical source code is patched.

The plant is an independently drawn eight-action-to-100-channel rectified affine map, followed by per-pattern centering and standardization to sensory standard deviation 2. Each channel projects to six adjacent E neurons. Plant parameters are drawn first; six target action vectors and motor perturbation directions are drawn afterward. Inputs and their order are preserved in `inputs.npz` and `preflight.py`. This is a deliberately transparent feature-space plant, not a vocal-organ model. Normalization and a shared context clock remain strong simplifying assumptions. Circuit dynamical noise is zero; this differs from the source's noisy training example and makes this a favorable mechanism check.

The circuit trained in 11.43 seconds and a frozen whole-song evaluation took 0.123 seconds on the first run. Full initial training plus five offset probes took 12.62 seconds. The existing learning-rule campaign environment supplies Python 3.12.14, NumPy 2.3.5, SciPy 1.18.1 and Numba 0.68.1. No dependencies were installed and no original empirical outcome files were opened.

## Suppression is not enough; the motor check

For the fixed direction sampled before results, increasing motor offset scales 0, .25, .5, 1 and 2 yielded mean circuit costs 1.4431, 1.4877, 1.6097, 2.0004 and 2.6699 Hz. Corresponding true losses were 0, .1065, .3871, 1.2740 and 2.9205. Silence cost 2.0592 Hz. These average orderings passed a basic source-mechanism check.

For each of three starting points, both diagnostic actors received the same 96 coordinate perturbations (48 action coordinates, plus/minus .05). The circuit actor used only scalar rate cost; the oracle used the true target loss evaluated on the same outputs. Neither actor was given a gradient through the plant. Central differences estimated cost gradients; each actor then took a fixed .1 Euclidean-norm step downhill. The step size was specified before those motor-update outcomes. Circuit/true gradient cosines were .7031, .8247 and .6471. Actual updated actions, rather than gradient alignment alone, produced the improvements in the table.

This is a deterministic, favorable local test with 96 queries per update, not a biologically realistic exploration rule, a stochastic actor-critic learning curve or evidence of efficient acquisition from silence. It also does not establish global reward correctness. One context's cost decreases from 1.2661 Hz at the exact target to 1.2350 Hz at the small wrong offset. The useful aggregate teaching direction therefore coexists with a local reward bias.

## Scientific decision

**Computational feasibility passes.** A source circuit, a separately specified reachable motor plant and an oracle positive control can be executed in well under a minute for this bounded test. The simple claim that successful learning requires a tutor-fitted motor dictionary is already too strong for this instance.

**The publishable question remains open.** The next substantive study should ask when the learned evaluator remains a useful teacher across independently sampled targets, nonlinear motor geometries and explicitly controlled context/timing support. Match reachability, motor dimension, exploration, sensory exposure and trial budgets. Hold out entire plants and targets. Report true target improvement and residual error relative to a matched oracle, including circuits that lower their own cost while worsening the target. Keep motor representation and timing/context interventions separate initially. Crucially, the present plant standardizes each output: silence was only an explicit probe, and amplitude is not a controllable motor axis. Add that axis with matched oracle and fixed clock before claiming robustness to reward exploitation.

Do not promote this six-context, one-plant demonstration to a general result. Stop or change direction if any apparent benefit of a target-conditioned repertoire is explained solely by target reachability/reconstruction or exploration covariance, or if wider tests merely reproduce already-established local error-landscape behavior without identifying a meaningful constraint. A full actor project was not launched.

## Verification and rerun

An independent seeded rerun reproduced the input arrays, trained sparse weights, suppression and all ordering values exactly. The motor gradients were reconstructed from saved queries, and separately written feature-map algebra reconstructed true losses within 4.45e-16. This is computational verification, not independent scientific replication. See `VERIFICATION.json`.

From the repository root:

```sh
campaigns/learning_rule_transport_2026-10-28/.modelenv/bin/python experiments/sensory_evaluator_preflight_2026-10-28/preflight.py --stage prepare
campaigns/learning_rule_transport_2026-10-28/.modelenv/bin/python experiments/sensory_evaluator_preflight_2026-10-28/preflight.py --stage motor
campaigns/learning_rule_transport_2026-10-28/.modelenv/bin/python experiments/sensory_evaluator_preflight_2026-10-28/verify.py
```

`suppression_result.json`, `motor_update_result.json` and saved per-start query arrays contain all results. `FIRST_SUPPRESSION_RESULT.json` preserves the initial timing/result record. `state.pkl` is our generated circuit state, not an untrusted external pickle.
