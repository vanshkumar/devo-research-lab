# Concrete additional-observation design challenge

2026-10-28. Specified before inspecting these simulations or any empirical validation responses. This follows the calibration challenge's finding that cleaner sensory measurements alone do not fix five-point recovery.

Simulate independent cohorts of160 and320 people. Replicate the original stimulus schedules, condition allocations and development/validation proportions2× and4×, but assign fresh unique IDs and regenerate every participant's latent effects, choices, omissions and feedback. No behavioral trajectory is copied. This gives82/78 development/validation people at160 and164/156 at320. The same ten actual schedules and three entirely held-out schedules remain.

For each size, run30 replicates of the shared common-law null, +5-point slow-history difference and −5-point difference. Use the frozen main-generator injection scales and save each replicate's actual standardized truth, which fluctuates slightly under the newly drawn people. Seeds are `402610280 + 1000000*size_factor + 10000*scenario_index + replicate`.

Compare two specified procedures on identical simulated task datasets:

- Original first200 association calibration and original condition-history priorSD1.
- An additional800 independent fully learned sensory choices per person, plus condition-history priorSD3. The extra observation assumes known lapse, no history effects and balanced signed contrasts, with jointly estimated bias/sensitivity. It is the optimistic measurement probe from the prior challenge, not ordinary extra task trials.

Report mean effect bias, score gain and participant-score-bootstrap detection, separately overall and on the unseen schedules. Count how often both overall and unseen-schedule score intervals favor the condition model. Report null false-detection rates and Wilson intervals for all30-replicate detection estimates. The target is an observed detection rate of at least80% for both signs, interpreted jointly with null behavior. With30 replicates, a point estimate meeting80% is not a lower-confidence-bound guarantee of80% power.

This is a generator-conditional study of a future independent cohort, not an analysis of appending new observations to the actual fixed80-person dataset. The two combined designs require224,000 or448,000 total decisions (600 original-task plus800 sensory-only decisions per person). Increasing people on the existing schedules does not create new schedule coverage, remove nonrandom allocation or establish causal interpretation.

If neither tested design meets the criterion, report that the tested320-person design remains insufficient under the specified procedure/generators. Do not extrapolate an untested sufficient sample size. Final artifacts: `sample_size_challenge/manifest.json`, `replicates.csv`, `summary.csv`, and `SAMPLE_SIZE_CHALLENGE_REPORT.md`. A separate one-replicate smoke check is preserved in `sample_size_smoke/`.
