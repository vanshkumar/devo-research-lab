# Independent HVC port and stimulus-design audit

2026-10-28. Read root `experiments/hvc_kernel.cpp`, `hvc_model.py`, `intervention_design.py`; compared with acquired `Sporadic HVC Simulations/{HVCIter.m,HVCModel_sporadicSims.m,findChainLength_v3.m}` and inspected the separate rhythmic script. No root implementation files were edited.

## Numerical verdict

The source HVC recurrence is correctly translated in the inspected version. Independent Python scalar loops, written without importing either root implementation, agree with C++ on all spike decisions across 18 small cases; maximum synaptic-weight discrepancy is **4.44×10⁻¹⁶**. Cases include learning off/on, source-like versus weak adaptation, and complete silence with nonzero heterosynaptic penalties. This validates translation, not biological fidelity.

Verified details:

- Adaptation uses previous activity and previous adaptation; recurrent inhibition uses the sum after feedforward rectification.
- STDP sign and both pre/post heterosynaptic penalties match. The extra η multiplying the penalty is present in the public source and is correctly retained.
- Hard weight clipping, diagonal zeroing only when plasticity is active, and Wmax=5 are correct.
- Sporadic-model N=100, initial uniform[0,.1] weights, pin=.001, beta=.115, alpha=30, eta=.025, epsilon=.2, tau=12, gamma=.01, wmax=1, seed neurons=10 match.
- The omitted source subsong run has η=0 and leaves weights unchanged. The source resets neural state before training, so skipping it changes neither the training state nor weights. PRNG state after reseeding for weights is separately acknowledged; the root does not claim identical MATLAB randomness.
- Public trialTimes has 7,200 1-based indices, first51,last359740. Root subtracts one correctly; the end-window filter removes none at the full360000-step duration.
- Root's length count matches `find(actSums(2:end)==0,1)` and the source final-ten-trial selection. Starting after the fourth onset at +30steps matches MATLAB column31. Output milliseconds use the source10ms step convention.

## Interpretation limits that matter

The source's labels “300” and “4x50” do **not** mean a300ms versus50ms neural clamp. The model delivers one10ms seed event for the former and four10ms seed events at100ms onset spacing for the latter. Pulse duration is absent from the implemented input. The source model therefore supports an onset-pattern/scaffold alternative; it is not a quantitative encoding model for optogenetic width itself.

The source length extractor runs on the final training trials, while forced inputs and synaptic plasticity remain active. Root's extra frozen-weight, reset-state, single-seed probes are valuable because they test what the weights store without continued rhythmic driving. They must remain labeled an additional analysis, even if motivated by the paper's Methods. Training and frozen-probe lengths should not be pooled. Neither is measured song duration.

TrialTimes has minimum gap27steps and seven gaps≤30steps. Consequently some four-event trains overlap the next train. This is faithfully inherited from source timing. The root's matched-train schedule changes exposure spacing to remove that issue for specified periods; it is a controlled sensitivity analysis, not the original schedule. For any new period, verify that its final offset fits before the next train—minimum nominal spacing120steps does not guarantee this for arbitrary offsets greater than120.

The separate `Rhythmic HVC Stimulation/hvc_RhythmicStim.m` changes parameters with desired period, including N, adaptation tau, Wmax, and sometimes gamma. Its demonstrations cannot serve as fixed-parameter out-of-condition prediction. The sporadic source port uses one common parameter set, which is the appropriate stricter check. This is a limit of the demonstration, not proof that the model cannot generalize.

## Stimulus-design audit

Root's two-condition affine interpolation and rank2/nullity2 calculation are correct. Zero residual is inevitable for two affine parameters. The source's pooled element medians cannot supply independent-bird uncertainty.

The proposed fixed-count width×period crossing identifies width and onset-period main effects, but **total-light dose remains proportional to width**. It cannot distinguish width from total exposure nonparametrically. The affine dose extrapolation at150ms width uses600ms total light, beyond calibration200–300ms; a divergent prediction there depends on the affine extrapolation assumption. If claiming resolution of the whole original width/count/dose ambiguity, vary count too, or include a matched-total-dose contrast. If the claim is specifically width versus onset rhythm, the four-condition crossing is appropriate and should be stated narrowly.

## Reproduction

Build the root library with its verifier, then run:

```sh
.venv/bin/python campaigns/song_target_memory_2026-10-28/experiments/hvc_model.py --verify
.venv/bin/python campaigns/song_target_memory_2026-10-28/audits/model_audit/check_hvc_kernel.py
```

`hvc_independent_check.json` pins the inspected C++ and source MATLAB hashes, and records every numerical case. The independent checker does not import the root's NumPy recurrence. Its saved stderr is empty. This audit required no downloads or long simulations. A practical resource issue was reported to root: source uint8 noise+activity arrays are below80MB, but allocating full float RNG arrays temporarily takes288MB, and long matched schedules can approach1GB; chunking avoids that peak if needed.
