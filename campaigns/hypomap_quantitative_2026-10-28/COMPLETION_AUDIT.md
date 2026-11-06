# Completion audit

2026-10-28. The bounded campaign is complete. The persistent objective was actual quantitative discrimination of trace versus substantial joint peptide abundance in C4-313, with technical alternatives and a conditional non-peptide signature. It was not a request to find a positive biological result.

| Required evidence | Executed result |
|---|---|
| Actual quantitative observations and provenance |23,512-cell full-gene sparse subset; version/range/header/checksum records; all target309 observed; source/count/QC reconciliation|
| Frozen estimands and donor evaluation |PROTOCOL.md and SHA256 before joint outcomes; complete grid; five useful donors plus singleton; both studies preserved|
| Donor-resolved joint abundance |204 joint;195 with minor<10; median minor1;2 substantial in one donor/sample; no Siletti substantial cases|
| Depth/quality and empirical backgrounds |Actual-count and metadata sensitivities; mixed mitochondrial units corrected for analysis; matched control pools/multiplier grid and sample-local favorable artifact cases|
| Competing models |Regularized donor-held-out conditional trace/mixed models; donor/source/pool dependence; failed severe-noise recovery explicitly prevents biological inference|
| Scientific positive and null controls |Direct observed-count injections; exact independent recovery; low-count nulls; full-profile same-donor synthetic doublets; moderate-noise model checks|
| Conditional non-peptide signature |Not warranted:2 positives in one donor; every held-out fold lacks positive training or test cases. Eligibility table executed; no misleading classifier fitted|
| Independent verification and adversarial challenge |Own-reader original HDF5 reconstruction of309 cells/1512 grid entries;311 hashed source ranges; model correction; latent-sensitivity/CI cautions retained|
| Prior work and decision |Closest primary quantitative/human/same-source evidence inspected; quantitative negative candidate characterization, no novelty/biological-absence claim|
| Reproduction |Full offline reproduce.sh completed successfully; all analysis stderr empty; input/source checks preserved|

No indispensable data obstacle prevents the observed-count decision. Remaining limitations are substantive: incomplete acquisition-raw/curation chain, no empty droplets or exported per-cell contamination/doublet scores, poor sensitivity to weak latent mixing in znZv1, same-source selection, and no orthogonal biological validation. These do not silently redefine the result; they bound it.

Disposition: deprioritize C4-313 as a reproducible substantial mixed state. Genuine low-level transcription versus ambient signal, and identity of two rare cases, remain unresolved. The report specifies a discriminating same-cell exonic/intronic imaging measurement if that different low-level question becomes valuable. No further campaign or automation was launched.

All work resides under this campaign. Previous evidence/reports and the launching HYPOMAP_QUANTITATIVE_HANDOFF.md were preserved. Public reads and ordinary local computation only; no money, rented compute, paid model APIs, accounts, private uploads, controlled data, publication or outside messages.
