# Frozen comparative-decision controls

2026-10-29. Saved source summaries only; no new trial values or protected data opened.

The exact external decision requires a5pp population-curve MAE gain over both baselines and paired95%lower gain>0. Each construction uses2,000independent simulated20-animal cohorts and20,000shared count resamples per cohort. All six bins stay together. Neither thresholds nor methods were tuned from these controls.

| Construction/case | Decision rate | Exact MonteCarlo95%interval |
|---|---:|---:|
|primary_pooled64: signal_baselines_plus10pp|62.75%|[60.59,64.87]%|
|primary_pooled64: signal_baselines_minus10pp|72.00%|[69.98,73.96]%|
|primary_pooled64: null_baselines_correct_candidate_plus10pp|0.00%|[0.00,0.18]%|
|primary_pooled64: null_baselines_correct_candidate_minus10pp|0.00%|[0.00,0.18]%|
|primary_pooled64: null_equal_error_candidate_plus5_baselines_minus5|2.15%|[1.56,2.89]%|
|primary_pooled64: null_equal_error_candidate_minus5_baselines_plus5|5.10%|[4.18,6.16]%|
|primary_pooled64: null_identical_correct_forecasts|0.00%|[0.00,0.18]%|
|double_variability_bounded: signal_baselines_plus10pp|26.65%|[24.72,28.65]%|
|double_variability_bounded: signal_baselines_minus10pp|23.25%|[21.41,25.16]%|
|double_variability_bounded: null_baselines_correct_candidate_plus10pp|0.00%|[0.00,0.18]%|
|double_variability_bounded: null_baselines_correct_candidate_minus10pp|0.45%|[0.21,0.85]%|
|double_variability_bounded: null_equal_error_candidate_plus5_baselines_minus5|2.40%|[1.77,3.17]%|
|double_variability_bounded: null_equal_error_candidate_minus5_baselines_plus5|4.80%|[3.91,5.83]%|
|double_variability_bounded: null_identical_correct_forecasts|0.00%|[0.00,0.18]%|
|shared_empirical_lab_offset: signal_baselines_plus10pp|55.70%|[53.49,57.89]%|
|shared_empirical_lab_offset: signal_baselines_minus10pp|53.30%|[51.08,55.51]%|
|shared_empirical_lab_offset: null_baselines_correct_candidate_plus10pp|10.70%|[9.38,12.14]%|
|shared_empirical_lab_offset: null_baselines_correct_candidate_minus10pp|6.90%|[5.83,8.10]%|
|shared_empirical_lab_offset: null_equal_error_candidate_plus5_baselines_minus5|28.65%|[26.68,30.69]%|
|shared_empirical_lab_offset: null_equal_error_candidate_minus5_baselines_plus5|30.60%|[28.59,32.67]%|
|shared_empirical_lab_offset: null_identical_correct_forecasts|0.00%|[0.00,0.18]%|

Primary controls: **failed_primary_control_requirement**. Both±10pp signals must have at least80%decision success; every primary null must have at most5%false superiority. Gate thresholds use the prespecified point MonteCarlo rates; exact intervals display finite precision.

Primary errors are all64consumed source RNN six-bin residual vectors centered by finite-pool bin means. Each simulated cohort is sampled independently from that pool and is not recentered. Outcomes remain bounded around.5. The doubled construction clips/recenters explicitly; its realized scalarSD multiplier is1.866, so it is a bounded variability challenge rather than an exact doubling after clipping.

The shared-lab construction adds one empirical lab offset to the whole cohort. Forecasts remain centered on the unconditional mixture, while known conditional environment means and true losses are recomputed from the full bounded pool. Thus nominal signal/null labels need not remain true conditional on each lab offset; the saved result separately counts true material effects and false material decisions.

| Construction | Scalar bias90%coverage | Scalar bias95%coverage | Descriptive MAE95%coverage |
|---|---:|---:|---:|
|primary_pooled64|87.70%|92.70%|0.00%|
|double_variability_bounded|88.10%|92.70%|0.00%|
|shared_empirical_lab_offset|87.70%|92.70%|90.05%|

Scalar bias coverage uses the known finite-population mean, conditional on the sampled environment. The saved unconditional coverage additionally shows the failure of animal-only intervals to capture an unmodeled shared environmental shift. Absolute-MAE and gain intervals are nonregular when a forecast has exactly zero population loss; percentile intervals can undercover there. They are reported as diagnostics and cannot establish absolute-error equivalence. The known-answer decision sensitivity/specificity, rather than nominal absolute-loss coverage, is the frozen readiness question.

No previous failed gate was changed. A failed control criterion stops this implementation branch before Panprefixes; it is not evidence against transferable learning. Even a passing control would require the separately justified access condition, source-readiness check and full prescription freeze before any external prefix.
