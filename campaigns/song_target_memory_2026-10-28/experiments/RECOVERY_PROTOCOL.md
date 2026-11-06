# Temporal recovery intervention protocol

2026-10-28. Added after independent prior-work audit located Roberts2017 HVC→Av ablation experiment. Known qualitative outcome: five birds reportedly lose temporal recovery after reinforcement ends, while pitch recovery and reinforcement learning remain. Source-reported pairedt4=4.8,p=.008 was exposed. Numerical paired recovery values and exact windows have not been inspected by root. This is an exploratory cross-intervention test; not preregistration or untouched literature validation.

## Mechanisms to compare before extracting numbers

Write adult timing displacement from established song as x. During recovery after white-noise reinforcement ceases:

`dx/dt = −(k_local + g k_route) x`.

The intact total rate k_total=k_local+k_route is calibrated only from each bird's pre-lesion recovery and actual elapsed observation time. HVC→Av lesion is g=0 only insofar as targeting/methods support that mapping. Define β=k_local/k_total. Fixed pre-lesion calibration predicts post-lesion recovered fraction `1−(1−R_pre)^(β T_post/T_pre)`.

- Pure autonomous local motor restoration: β=1, recovery remains after removal of a downstream readout route. This is a restricted but meaningful architecture; it is not all motor memory.
- Routed evaluative reference: β=0, no recovery from the targeted displacement when the route is removed, provided this is the required timing-evaluation route.
- Shared/motor-stored timing code read out through that route: also β=0; identical behavioral prediction to the reference model.
- Mixed restoration: β∈[0,1], exploratory profile across a frozen grid0:.01:1. This estimates a functional dependence only under fixed gain/state and successful ablation. Do not call β a proportion of stored memory.
- Global plasticity suppression is a control alternative. Continued WN-driven timing/pitch learning and pitch recovery can reject it if verified, but cannot exclude timing-specific permissive feedback or state estimation.

Compare absolute/squared prediction errors at independent bird level and extraction-error envelopes; do not select a new learning rate per post-lesion condition. If windows differ or pre recoveries exceed1, do not silently log/truncate data: use matched elapsed times from curves or report a directly paired descriptive endpoint comparison and explicit model limits. If ablation incomplete, timing readout changed, intervention harms performance, or chronology permits consolidation/aging confounds, report them. Any population uncertainty uses birds as units and is conditional on figure reconstruction; no rendition bootstrap.

Primary metric must match source (syllable onset to next onset if so defined), not voiced-element length. These adult recovery experiments constrain use of a persistent timing setpoint, not the acquisition mechanism of Zhao juveniles or tutor specificity by themselves. Combining the studies constrains a plausible architecture across contexts but does not turn them into one longitudinal experiment.

## Source-driven correction before numeric modeling

Full methods source audit reports temporal reinforcement learning also impaired (4/5 birds slower), although pitch learning/recovery is preserved. Thus a timing-specific permissive/plasticity-gain explanation is a serious competitor; the lesion cannot simply be assumed to remove a selective timing evaluator. Source post-lesion recovery window is pre-lesion duration+5–10days, and baseline motif duration/self-similarity change slightly. Figure6f is a boxplot, so individual paired recovery fractions may not be recoverable. Retain the planned conditional equation, but do not calculate bird-level rate fits from invented pairs or boxplot medians. Evaluate which functional constraints are actually identified by the available source summaries.
