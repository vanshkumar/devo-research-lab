# Proposed learning for PI integration

**2026-10-29 — Flesch person-mixture integration and acquisition checks**
- Observation: The saved source-only value prescription has exact selected B200 curve error 10.1967 pp at three Gauss-Hermite points and 10.1985 pp at nine, while its fixed-parameter 71-person selected NLL changes 18230.32→18155.08→18134.09 at 3/5/9 points. Population means can look numerically stable while the person-mixture trajectory likelihood remains underresolved. All 48 B200 source people start near chance (47.9% first nonboundary trial, balanced truth) and reach 86.3% averaged over their first forty; a high first fifty-opportunity bin does not certify pretraining knowledge.
- Action: Keep likelihood-integration convergence separate from mean-forecast stability, and inspect first-exposure learning before attributing this source gap to initial skill or practice. Preserve the failed ≤10 pp source gate and unfinished full calibration; do not consume B2/B20 responses or refit automatically from this diagnostic.
- Confidence: high

Shared root files remain PI-owned. This proposal avoids duplicating the existing full-prescription and selected-cohort observations.
