# Predevelopment clarification

2026-10-28, before new simulation outcomes. Independent prereview identified two material points.

1. Add a **shuffled35 joint-control arm**: same initial circuit,35 tutoring renditions, same fixed clock and exact marginal target features, but cyclically permute the six tutor patterns across their context windows. It receives the same641/321 actor-query budget. Beating untutored alone would not establish target-specific learning because generic tutoring changes error sensitivity. Main target-specific contrast is learned35 versus shuffled35; learned35 versus untutored is retained.
2. Use literal continuous140 tutoring from the same initial circuit/states as35, rather than restarting105 renditions from35. Source asynchronous plasticity consults a10-ms history; a new sim call would reset this history. The two exposure arms share all initial randomness and the exact first35-rendition input sequence, while140 retains the unchanged continuous source equations. This costs35 additional training renditions but avoids an approximation.

All six arms share the original circuit initialization. Each frozen network receives its own500-ms pre-probe burn from the same original hE/hI under its own weights. Zero sensory SD uses the declared1e-12 floor with no redraw. Any zero initial true loss remains in the ensemble, with ratio endpoints undefined and absolute loss reported; no performance-based exclusions or replacements.

Resource refinement: literal140 training materializes source time-by-neuron arrays and can peak around2.7GB per process, much larger than a single probe. Use at most four processes and reduce if ordinary memory telemetry warrants it. No paid compute or new dependencies.

Clock-prefix refinement, still before outcomes: Gaussian HVC bursts have anticipatory tails. Generating exactly35 periods omits the upcoming36th burst near the end of35's final post interval, whereas140 includes it. Generate one additional future clock period and truncate to the auditory length in every training arm. This gives exactly identical35-rendition input prefixes across exposure conditions without changing the source clock equation. It is a continuously scheduled clock convention, and differs from the earlier one-plant preflight only at the terminal clock boundary. Exact array equality must be checked before execution.

Acceptance uses strict cost decrease; equal proposals retain the incumbent. `argmin` chooses the first coordinate/sign in deterministic order for equal improving candidates. Intervals are ordinary paired whole-plant percentile bootstraps, descriptive for this fixed ensemble/generator and without a familywise guarantee across secondary tests. Root will freeze analysis code before held-out outcomes.
