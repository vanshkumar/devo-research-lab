# Frozen joint opportunity–correctness audit

2026-11-01. Investigator `01a19734-d25e-7bb3-8e81-85110583eb56`, start21/samecycle13. This is postvalidation analysis of the same consumed24 animals. Original START12:56:15Z, firstnumeric13:08:15Z, design13:16:15Z, hardstop13:56:15Z apply unchanged. No manuscript writes.

## Question and alternatives

Does the saved autonomous RNN predict the observed joint distribution of exact100 opportunity counts and successes better than saved growth, or is its count-pooled cohort accuracy agreement a favorable aggregate that need not imply better joint forecasts? First calculation independently reconstructs the prior RNN/growth and count-pooled RNN summaries and verifies all48 original paired ensembles against their original manifest pins. Neither model is regenerated or fitted.

## ONE main comparison, fixed before new scores

For animal i, future500-opportunity bin b, side s, particle j, retain the actual paired integers N=number of exact100 opportunities and K=number correct, including omissions as incorrect. Define the three exhaustive category proportions

`q = (K, N-K, 500-N)/500`.

The observed q uses the independently reconstructed target integers. The first two categories are correct/incorrect exact100 opportunities on this side; the third is every other stimulus opportunity. N>0 throughout. This vector is one-to-one with (N,K), hence with (N,K/N). It does not replace counts by their means or construct paths from unpaired marginals. Correct and incorrect categories have the same units; sides are treated symmetrically. No estimated scale, outcome-based standardization, smoothing or likelihood bandwidth is used.

Distance is Euclidean distance between q vectors divided by sqrt(2), the distance between distinct one-hot categories. For each animal/bin/side the main score is the exact energy score of the saved equal-weight512-point empirical forecast:

`ES_V = mean_j d(q_j,y) - sum_jk d(q_j,q_k)/(2*M*M)`.

Lower is better. Each animal's score is the simple average over its six bins and two sides; the cohort score gives each of24animals equal weight. The sole main contrast is `mean(ES_growth - ES_rnn)`: positive favors RNN. This is a proper score of the joint count–success distribution **within each bin/side**, averaged with equal side/bin/animal weights. It does not assess the full cross-bin or cross-side joint trajectory law. Counts are necessarily part of this new estimand; original ratio endpoints remain separately visible. This is neither an alternate primary gate nor prospective success.

Report the two energy-score terms separately. A positive contrast supports only relative predictive advantage for this fixed consumed cohort and functional; a negative one favors growth. An interval crossing zero leaves even that contrast imprecise. No new practical threshold/pass rule will be selected.

## ONE accuracy-blind reference

Use the SAME saved draws and observed counts, collapse correct/incorrect into N, and calculate scalar CRPS for N/500 with the same finite-ensemble formula. This is the one additional reference, not a new fitted model. Its paired growth-minus-RNN contrast checks whether a joint-score ordering also occurs with all correctness information removed. Do not subtract the two different scores to claim an isolated accuracy contribution, and do not select between them after seeing results. A joint advantage without a count-only advantage would be consistent with added correctness information under this score, not a causal attribution. Identical count and joint ordering can still include correctness differences.

## Required companion summaries

For BOTH models retain original mean-of-particle accuracy ratios and the changed `sum(K)/sum(N)` within animal/bin/side, then equal-side/equal-animal/equal-bin aggregation. Report population-curve, individual equal-side and individual side MAE in percentage points; covariance identity and integer checks; observed/generated opportunity ranges; mean count and success errors. These are predeclared descriptive companions, not additional candidate scoring rules or replacement gates. No conditional rollout or new trajectory is generated.

## Uncertainty and numerical checks

- Primary unit is animal, not288cells or512particles. Report20000 paired-animal bootstrap percentile intervals (seed2026110101) and paired Student-t intervals. These condition on the consumed selected cohort/fixed recipe and lack postselection/coverage guarantees.
- There are5 represented laboratories with unequal counts10/6/5/2/1. Report CR1 laboratory-cluster t(G-1) sensitivity, all per-lab means and all leave-one-lab-out contrasts. Five clusters do not certify arbitrary-laboratory transport or calibrated coverage.
- Report the U-statistic version replacing M*M by M*(M-1) in the pair term; this is the fixed diagonal/finite-ensemble correction for the SAME energy functional, not a searched alternative. Primary is exact ES_V of saved empirical forecasts.
- Quantify finite-particle variation separately using exact delete-one U-score pseudovalues. RNN/growth use the original shared particle streams: the frozen simulator uses the same subject seed/initial draws and resets the same random streams for both. Pair the particle index within each animal, keep animal streams separate, and report the cohort jackknife MC standard error. Also report8fixed disjoint64-particle paired U-score contrasts as a finite-resolution diagnostic. These are approximate numerical integration diagnostics, not biological intervals or posterior calibration.
- Independent scalar checks of two preselected cells for BOTH methods: subject indices0/23, bin-side(0,0)/(5,1). Compute distance sums with scalar arithmetic rather than the vector implementation. Check permutation invariance, point-mass/identical-forecast limits and separate count/correctness changes. A fixed-N correctness change must change joint score while count-only score remains zero. These are implementation invariants, not new empirical models/controls.
- No model refits, uncertainty refits, source parameter uncertainty, interval-coverage experiment, novel literature claim or likelihood-based calibration will be earned.

## Freeze, resources and stopping

Save complete observed/generated comparison vectors with subject/particle/bin/side pairing and source pins before new scores. Freeze this design, resource plan and executed comparison source. No access outside the same24consumed first4000rows is necessary. New raw rows/public operations/downloads/ingress are zero. Historical observations/failures remain unchanged.

200000000bytes total additional read/hash/decode, including preserved5000000byte failed-start allowance;800000000byte peakRSS; one scientific process/thread. First calculation charged52533701bytes and peaked53870592bytes. Charge whole NPZ containing assets and all decoded members, repeated hashes and failed passes. Physical I/O remains unknown. Stop and save partial work if a cap/deadline binds. Save resources/outputs/RESULT/README/STATE/proposed learning task-local, then one<=400word terminal report to current registry PI and finish/jobs0.
