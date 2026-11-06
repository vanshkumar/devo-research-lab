# Fixed HVC suite

2026-10-28, saved after kernel verification, a 10,000-step pilot, and seed1 source-protocol runs. Pilot was insufficient training (30ms); full source7200 trials produced rhythmic100ms and single170ms frozen neural activity. This is an exploratory reproduction, not validation against untouched biological observations.

Use source parameters and7200 trials for six seeds1–6 in each source protocol (four100ms-spaced seed impulses / one impulse). Do not retune to empirical duration or to a seed. Examine both source-script during-training readout and single-pulse frozen-weight readout. Record network means and censoring; ten probes are nested within each network.

Cross-protocol generalization: six matched-seed networks at100,200,400ms onset periods, four impulses/train and the same7200 train-onset schedule. Separate trains by120+Poisson(50) steps to prevent overlap even at400ms period; source parameters held fixed. This manipulates the onset hypothesis; width is absent from this source model and hence has exactly zero sensitivity under its onset-extraction mapping. It is not evidence that biological NIf discards width. No pulse-width-to-acoustic fit is imposed on neural activity lengths.

Known-effect controls: no plasticity at source seed1 for both protocols; kernel agreement with independent arithmetic and a known50ms chain. Sensitivity: source seed1 with tau×.75/1.25 and eta×.5/2, both protocols. This asks robustness of the computational phenomenon, not a population confidence interval for birds.

Resource: two concurrent local jobs maximum; chunked noise generation, roughly<300MB working arrays/job for longest matched runs. Expected several CPU minutes, no external compute. Cache output by exact protocol/seed/parameter string; offline runner reexecutes when requested.
