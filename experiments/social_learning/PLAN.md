# Social information order — frozen pilot protocol

2026-10-28, saved after reading the paper and code definitions, before inspecting CSV outcomes. This is a newly selected empirical direction after the user requested broader initiative. Motivation: how learned social information changes an action preference, and whether apparent primacy identifies a learning mechanism.

## Material and hypotheses
Primary experiment: Santiago Araújo et al. 2024, DOI 10.1098/rsos.240408. Public 462-trial CSV, Dryad version 296766; the publisher's Figshare file 46746183 has the identical Dryad-declared SHA256. Paper-level outcome is already known from literature (main 64 eligible trials, weak first-demo tendency); therefore this is exploratory reanalysis, not an independent replication of subjects or a blind discovery.

Alternatives: true first-information weighting; weak/no learning and finite-sample fluctuation; color preference correlated with assignment; selection of trials with mating after two courtships; date/device heterogeneity. Even a robust preference is behavioral evidence, not identification of imprinting or a neural circuit.

## Pilot S2: replication and observation/selection audit
1. Recompute all flags from original color fields, not copy_dc_bin. Count every missingness pattern. Eligible = both courtship colors and chosen color observed. Verify courtship colors are distinct when both present. Primary paper score = chosen equals second demonstration in T, unique demonstration in C1/C2. Separately report chosen equals first/unique demonstration. Match n and exact two-sided binomial tests from paper. If mismatch, investigate before inference.
2. Check supplied copy_dc_bin against independently reconstructed scores on eligible and excluded trials. Original Rmd initially defines first-demo copying for T, whereas codebook describes second-demo copying: follow computation/values and report discrepancies without assuming error in the published statistics.
3. Color-stratify main/controls. Estimate first/unique copying with equal weighting of pink/green demonstration strata. Different denominators must be shown.
4. Sensitivity: all matings (including one-courtship trials) and all randomized-assigned trials as three outcomes {first/single choice, opposite choice, no mating}. These are different estimands; no missing choice imputation. Report treatment-specific eligibility, mating, and double-courtship rates. Worst-case missing-choice bounds make assumptions explicit; they are not corrections for the published estimand.
5. Date-cluster bootstrap (seed 20261028; 5000 resamples) for main first-demo preference and main-minus-C1 difference. The CSV may lack true simultaneous experimental blocks; date is a conservative available unit, not proof of independent clusters. Include leave-one-date-out estimates. If clusters few, say so. Avoid treating fly frames as replicates.

## Validation and decisions
Positive control: known binomial probabilities/intervals checked against direct standard-library enumeration on toy values. Independently verify eligible counts/score with csv module, not pandas. If main binomial reproduction fails, no target inference until resolved.
Expected interpretation: identical early-only and conflicting-sequence choice rates would support little incremental behavioral effect of the second demonstration within precision, not proof it was ignored. Robust main >.5 would support a preference under this protocol, not human-like primacy, general social cognition or imprinting. A broad sensitivity range or color/date dependence warrants revision and a more discriminating design. Do not hunt a subgroup with p<.05.
Keep/revise/retire decision based on informativeness, controls and effect precision. If promoted, execute a stronger analysis/model-identifiability check and an independent audit before final recommendation. Preserve every condition, source discrepancy, failure and exploratory addition.
