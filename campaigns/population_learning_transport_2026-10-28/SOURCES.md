# Sources and provenance

All material is public. Empirical validation used only the original release's
26 format-excluded source candidates. The protected Pan-Vazquez cohort was not
opened; the separate Noel release was not substituted.

The original caches are under sources/longitudinal_learning_feasibility_2026-10-28/standard_cache/.
The prospective candidate inventory is sources/prospective_acquisition_feasibility_2026-10-28/excluded26_inventory.json,
SHA256 `1d1f726d7dc7a59b6fd6800fccd3db322da7508f507b66c4eded4fb7abcf78d6`.
New artifacts/coverage/INDEX.json maps dataset IDs/public S3 URLs;
BYTE_MANIFEST.json pins size/cache MD5/SHA256; FILE_METADATA.json and SESSIONS.json
preserve headers, footers, schemas and chronology. All 4,407 files verified.

RNN, growth bank, trainer source and historical manifests remain in
campaigns/learning_rule_transport_2026-10-28/, reused by reference without edits.
FREEZE.json hashes imported code and model/bank files. The old
sources/trainer/MANIFEST.json records exact Git URLs and six historical task
versions. Independent AST tests execute original correction and pool methods.

Primary papers/code checked in the bounded review:

- [Liu, Geadah & Pillow](https://arxiv.org/html/2509.04661v2), §4/Fig4 and Appendix C; [author code](https://github.com/Helena-Yuhan-Liu/InferLearningANNGLM), pin `0ae19f7eec2836ab05487cc0342c7d1ac51a2727`. Held-out conditional prediction and the RNN architecture are prior contributions.
- [Geadah & Pillow](https://pmc.ncbi.nlm.nih.gov/articles/PMC12621722/), §2.1.1–2.4; [author code](https://github.com/victorgeadah/LearningRules/blob/main/fit.py), pin `0aa2edb7d05bef69ba544b143e885f956c8b9026`. Acquisition fits under both curricula and fitted dynamic learning rates are prior work.
- [Pan-Vazquez et al.](https://pmc.ncbi.nlm.nih.gov/articles/PMC11579926/), Results/Methods: random mixed contrasts, no shaping/debiasing, fixed reward. Four contrasts in Results conflict with a fifth 50% value in Methods; prior permitted first-session inputs support four. Exact custom acquisition code remains unresolved.

artifacts/method_audit/PRIOR_WORK.md records precise locations, access failures
and scope. Direct PMC occasionally returned a challenge page; indexed primary
text, live author code and existing Git-blob-verified bytes supplied evidence.
No access bypass or exhaustive novelty claim was made. All seven previous
campaigns and the separate sensory-evaluator preflight are preserved.
