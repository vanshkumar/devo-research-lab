# Post-freeze presentation record

After validation and successful offline replay, visual inspection found that the fixed-margin legend overlapped the last error bar in primary_effect.png/pdf. A separate finalize_figures.py wrapper moves only that legend to the empty space between rows. It invokes the unchanged frozen renderer with unchanged saved numerical inputs; no source outcomes, statistical estimates, intervals, eligibility or predictors change. The46 originally frozen artifacts remain unchanged. The main offline runner reproduces the frozen renderer; run the optional wrapper afterward to reproduce this cosmetic adjustment.

All primary/external results are consumed at this point. No new inferential analysis or new validation test was performed.
