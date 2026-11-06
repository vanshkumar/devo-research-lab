# One postvalidation contrary test

Written2026-11-01after main EVALUATION and AUTHOR_AUDIT_POST, before static-baseline fitting/scoring. This is consumed-data diagnostic evidence; it does not replace or repair the frozen primary comparison. No further hypothesis/model repair is planned in this assignment.

Trigger: both physiology common models select the largest allowed global ratek2, and the main cue gain changes from-3.56%to-0.31%under person scaling. A rapidly saturating common response curve may mainly shrink noisy initial observations toward a common level. The strong contrary hypothesis is that temporal change adds no forecast value beyond a time-independent noisy-prefix estimator.

Fit a static baseline S_i,c=max(0,s mean(A_i)+z(A_i,c-mean(A_i))), clipping expectancy to1. It retains the option of fixed individual cue discrimination(z1)and of cross-cue pooling(z0); no time or cue-omission count enters. Fit s{0,.25,.5,.75,1,1.25,1.5}andz{0,.25,.5,.75,1,1.5}on the same development units by equal-participant MSE, with listed-order ties. Freeze its parameters and script before reading held outcomes for this comparison. Report primary physiology, past-acquisition-scaled physiology and separate expectancy.

Compare S with the saved main C/U and simple baselines using the same15future observations per person. Paired participant bootstrap10,000replicates(seed202611010233)for C-minus-S gain and fractional reduction. A static win narrows any temporal-habituation interpretation to initial-state denoising; a C win remains conditional predictive evidence and does not identify an underlying process. Keep the original main results and every failure unchanged.
