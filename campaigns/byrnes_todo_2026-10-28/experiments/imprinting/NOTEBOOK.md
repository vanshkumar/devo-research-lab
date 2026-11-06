# Filial imprinting: sensory bias and learned generalization

Completed 2026-10-28. Two empirical pilots, with distinct questions. Root selected atlas/song for major follow-up, so these remain bounded supporting results. No neural circuit or innate teaching signal was identified.

## I1. What does a naive approach preference actually establish?

PLAN.md was saved before source-table outcomes were computed. Published article outcomes were already known. Raw material is four unchanged publisher tables from Freeland et al. (online2024, issue2025), DOI10.3758/s13420-024-00638-z. Chicks were dark-hatched and tested at their first visual experience; this is a test of predisposition before trained imprinting.

Analysis uses the independent chick, not its20 minute bins. Each chick's mean supplied preference index is averaged; bootstrap resamples whole chicks5000 times, seed20261028. Choice-interval scores of50 when neither stimulus area is occupied are preserved rather than silently imputed as a genuine choice. Separate sensitivity weights by actual occupied frames. Target side is reconstructed from left/right counts and agreement with the supplied fraction, keeping original tables intact.

| Condition (large vs five small) | Chicks in table | Mean minute preference for large, % | Subject bootstrap95% CI | Occupancy-weighted mean, % |
|---|---:|---:|---|---:|
| Both red |46|66.621|57.57–75.01|71.160|
| Both yellow |40|48.076|41.27–55.10|43.853|
| Red large / yellow small |58|84.988|78.66–90.53|89.429|
| Yellow large / red small |53|28.527|20.44–37.37|24.306|

Positive control: red/yellow source point estimates reproduce to reported rounding. Red-minus-yellow large preference18.545percentage points, bootstrap95%[7.43,29.79], subject Mann–Whitney p=.00250. The paper's displayed SEM is not exactly reproduced by the subject-mean SEM here; we report our own defined bootstrap interval rather than substitute its uncertainty. Exact finite sign enumeration checks a known probability1/16.

Supplied ratios reconstruct from source occupancy counts to floating precision except two bins in crossed-condition chicks46 and49: their supplied index50 does not equal the available occupancy ratio. Those rows are preserved and identified in ratio_reconstruction.csv. They do not drive the red-versus-yellow-only comparison. The tables already omit nonapproachers, so full-population approach rates cannot be independently reconstructed from these files. Published descriptions differ between50 and51 for the red-group total; no attraction-denominator claim is based on choosing one of these versions.

The geometric control is consequential:111.8mm squared versus5×50mm squares gives nearly equal area12499.24vs12500mm², but total contour447.2vs1000mm and numerosity1vs5. Thus “large” does not isolate size from contour/numerosity. A standard-sRGB illustration gives red/yellow relative luminance.2126/.9278 and white-background Michelson contrasts.6493/.03745. This does not estimate the chicks' perceived brightness: actual display spectra, avian cone sensitivities and adaptation were not measured here. The source itself treats hue, brightness and contrast as unresolved. An innate adult-recognition interpretation is stronger than this design identifies.

Decision: **retain sensory gating candidate, revise semantic/teaching interpretation**. Approach to a salient visual feature is an empirical starting point for a grounding circuit. These naive birds provide no intervention on how that bias teaches a subsequently learned representation. Dark rearing does not distinguish genetically specified social semantics from a visual salience mechanism.

## I2. Does a published prior-driven model predict held-out learned generalization?

LEARNING_PLAN.md was saved before main Exp4 outcome computation. This is a distinct trained-exposure/generalization question using Wang et al.2024, DOI10.1016/j.isci.2024.110195, Zenodo10869154. Original source notebooks were read as JSON/text and never executed. Exp4 contains long-five-day Red1 and Yellow1 imprinting data:28/35 chicks. Dual-choice trials require both nonzero stimulus codes;0 indicates blank/no-object. Source approximate wavelengths645/580 mark familiar endpoints. Eight ordered color-distance ranks are verified against code; data are averaged within chick×test color before comparisons.

Model parameters are fixed from the source: multiplicative preference update alpha=.01,Gaussian sigma=.2,t=300, with its quadratic red-orange-yellow prior versus a uniform prior. Model coordinate uses ordinal k/8 sampling, matching the source1000-point discretization, rather than claiming physical wavelength is a perceptually uniform scale. A single multiplicative response scale is fitted only to odd-ID discovery chicks in each cohort. Even-ID chicks were reserved before computation:14 red and17 yellow validation subjects. No parameter tuning on them. Constant discovery-mean preference is an additional baseline.

| Long-exposure cohort | Discovery/validation n | Biased-prior validation MSE | Uniform-prior MSE | Constant baseline MSE | Biased−uniform95% paired subject-bootstrap interval |
|---|---|---:|---:|---:|---|
| Red1 |14/14|.035897|.035734|.038373|[−.000099,.000461]|
| Yellow1 |18/17|.040037|.038973|.040285|[.000457,.001738]|

Preference units are proportions; MSE averages the eight color errors per validation chick. Uniform prior predicts this long-exposure holdout at least as well, especially in Yellow1. This does **not** refute a biological predisposition or the article's distinctive fast-learning claim: the available test is after five days, when both models have largely converged. The source's maximum-preference scaling is replaced here by honest discovery-only amplitude calibration; published R² values are not directly reproduced by this new validation estimand. Initial-prior uncertainty and model-class alternatives are not propagated.

Critical availability limit: Zenodo metadata assigns identical MD5 to Experiment1.zip and Experiment2.zip. Downloaded Experiment1.zip verifies that MD5 but contains Exp2a/b/c spreadsheets with blue-green test wavelengths450–514, not the short red-yellow condition. Exp4 has red-yellow580–645. Therefore the short red-yellow1-day raw condition needed to test different learning speed is absent from this pinned deposit as retrieved. This is a specific archive limitation, not evidence that no legitimate other copy exists. No short-vs-long empirical comparison is claimed. archive_audit.json records names, schema and color codes.

Computational controls: iterative normalized updates agree with fixed-exposure closed form within4.4e−14. Independent scalar Lagrange-polynomial/log-update arithmetic agrees with saved model curves within5.2e−15, without importing the original notebook or analysis model function. Post-pilot synthetic recovery diagnostic freezes two sample sizes, two noise levels and100 seeds: when the biased model truly generates observations, the long-red comparison recovers it91/100 times at low noise(.03), but only63/100 at noise.15 with14 discovery/14validation subjects. Long-yellow rates99/100 and68/100. With128 low-noise subjects per part both recover100/100. Thus a negative observed comparison cannot establish that priors are absent; detectability depends on regime. Full fixed grid includes t100 and t300, with no selection of a favorable result. This is a control, not an additional pilot.

Decision: **revise; no promotion or absence-of-prior claim**. Existing long data support exposure-dependent generalization but weakly distinguish the prior component. Resolve the missing short condition and check actual sensory coordinates before a mechanistic comparison. Neural recordings/interventions or an exposure manipulation isolating the bias as a teaching signal would be necessary for a nuts-and-bolts circuit claim.

## Reproduce and failures

From repo root:

```sh
.venv/bin/python campaigns/byrnes_todo_2026-10-28/experiments/imprinting/acquire.py
.venv/bin/python campaigns/byrnes_todo_2026-10-28/experiments/imprinting/analyze_predispositions.py
.venv/bin/python campaigns/byrnes_todo_2026-10-28/experiments/imprinting/analyze_learning.py
.venv/bin/python campaigns/byrnes_todo_2026-10-28/experiments/imprinting/audit_learning.py
.venv/bin/python campaigns/byrnes_todo_2026-10-28/experiments/imprinting/audit_archive.py
```

Python3.9.6,numpy2.0.2,scipy1.13.1,pandas2.3.3,openpyxl3.1.5. openpyxl and et_xmlfile were installed into the existing isolated environment for read-only source extraction. No spreadsheet source was modified or exported. Raw source archives about5MB; no movies downloaded. Acquisition checks hashes on cache reuse; all substantive outputs CSV/JSON and exact logs are alongside the scripts.

Access record: new multipoint-pattern DOI returned403 and was not pursued; PMC Wang browser page presented a challenge, so the legitimate public EuropePMC full-text API supplied the open article. Publisher supplementary tables and Zenodo public versioned APIs worked. One initial learning-script run had a syntax error from missing spaces in a conditional expression; corrected before any numerical output, no parameters or conditions changed. Final pilot/control stderr files are empty. No contacts, accounts, paid services, uploads, publication or external experiments were undertaken.
