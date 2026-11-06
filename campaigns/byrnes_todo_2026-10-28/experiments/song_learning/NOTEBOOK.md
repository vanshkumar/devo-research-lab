# Song learning: separate tutor acquisition from later performance evaluation

Completed 2026-10-28. One pilot plus promoted bounded follow-up. **Decision: retain as an empirically constrained research direction, with target acquisition and evaluation treated as distinct circuit problems.** No new biological mechanism or independent replication is claimed.

## Question and evidence actually obtained

Byrnes §2.1 asks how a culture-derived song target becomes associated with an innate learning drive. The initial pilot sought performance-error evidence, then moved from adult distorted-auditory-feedback experiments to a juvenile developmental study with public source data. PLAN.md was saved before source tables were opened; the literature-level results were already known, so this is exploratory reproduction/robustness. FOLLOWUP_PLAN.md was frozen before unused Fig1/Fig2 source outcomes were opened.

The 2025 experiment records song and dopamine during juvenile development; subjects had normal parental exposure before recording. It does not experimentally assign tutor templates. Its adult-song endpoint is a measured proxy for the internal goal, not a direct observation of a remembered tutor. It contains no phasic developmental dopamine intervention. Crucially, other experiments already provide causal evidence: Hisey2018 manipulates VTA→AreaX/D1 signaling in juvenile copying, while Tanaka2018 identifies a separate PAG→HVC dopamine pathway necessary during tutoring and sufficient, with song playback, to support copying. Our counterexample cannot refute that intervention evidence. These distinct acquisition and evaluation pathways are the main useful mechanistic distinction.

## Source provenance and correction

Primary source: Kasdin, Duffy et al., Nature641,699–706(2025), DOI10.1038/s41586-025-08729-1. A Feb2026 correction reports audio clipping affecting15.9% of audio and updated analysis/figures/source data. The correction states its conclusions are unchanged. We did not discover that error or reproduce the corrected raw pipeline.

Downloaded current public Fig3,Fig4 and Extended8 XLSX; SHA256 and URLs are in data/song_learning/manifest.json. Fig3/4 internal creation dates are2026, consistent with the correction. Fig1 was acquired for follow-up; it contains example acoustic matrices and no bird-to-syllable mapping. Fig2 whole-file size was72,690,975bytes. A capped attempt stopped after7,000,001bytes with no workbook retained. The server advertises byte ranges and returned206; selected ZIP members were then streamed legitimately. ZIP CRC/uncompressed size and per-range SHA256/ETag/last-modified metadata are retained under data/song_learning/fig2_members. We do not claim a whole-Fig2-workbook SHA256.

Source metadata, existing raw originals and partial members are untouched. The read-only extractor uses bundled Python XML/ZIP, not workbook authoring. Spreadsheet skill applied; no new workbook was created. The full open author PDF was read/extracted, including Methods and Discussion, and page3 was rendered/visually inspected. That PDF predates the correction; current numerical results use current publisher data. Exact source locations and access limitations are in SOURCES.md.

## Initial empirical pilot: future-alignment source reproduction

Fig3 sheet e.syllable_traces contains25 rows×600 saved future-trajectory positions. Recomputing its mean reproduces f.population_mean to1.11e−16. At the600th saved source column, all25 rows are positive, mean0.1761313, median0.1609797, range0.01076–0.44841 in the source's projection units. The provided shuffled mean is0.0044178 and supplied envelope[−0.0272539,0.0360895]. Leaving out each syllable yields endpoint means0.16479–0.18302. We do not interpret600 correlated positions as independent tests or use25 syllables as25 birds. The source tables do not contain identities needed for a proper six-bird uncertainty estimate or the raw data needed to reconstruct CCA/shuffle preprocessing.

Fig4's supplied pooled history coefficients have current-rendition coefficient0.333653 and11/11 negative past coefficients. This is descriptive reproduction of reported performance-history structure, not a fresh model selection or a proof of how the target is acquired. Source rows, known population-mean invariant, outputs and logs are preserved.

## Promoted empirical follow-up: unused quality-response panels

Definitive preselected target: source Fig2g per-syllable dopamine averages in the published200–300ms post-onset window, closer versus farther relative quality.

- Closer mean0.178624 ΔF/F%; farther mean−0.212806%; paired difference mean0.391430 percentage points, median0.353304, range0.05106–0.96657.
- All25 paired differences are positive. Leave-one-syllable means span0.36747–0.40561. Every nonempty grouping of strictly positive paired differences also has a positive group mean, but missing bird membership prevents estimating bird-level variance or a new population CI.
- The reference syllable-level paired t-test gives t=9.14276,p=2.74606e−9, matching the published rounded value. This is a reproduction check, not independent-animal inference.
- Preselected Fig2f decile curves show a strictly decreasing200–300ms mean profile in the source's unlabeled A..J column order (Spearman rank−1). The source worksheet does not independently identify that column order as high-to-low quality. Numerical agreement of first/last curves with closer/farther g scalars is a post-inspection consistency check, not an independently specified quality orientation. No raw time vector accompanies the displayed24000-point curves; we compare half-open and inclusive−1..+1sec display grids. They differ by at most1.12e−5ΔF/F% in the selected means. End-decile means reconcile with the definitive g scalar panel within0.000914; the small discrepancy may reflect sampling/averaging conventions, not raw-data accuracy.

These source panels were unused in the initial pilot but reuse the same selected animals/recording study. The definitive g panel supports a relative-quality evaluative contrast under the chosen adult-endpoint/history proxy. The decile panel supplies an ordered source-column response with uncertain independent quality labeling. They cannot distinguish tutor-derived evaluation from another target correlated with the eventual adult song, prove dopamine causes each natural learning step, or establish the origins of target selection.

## Controlled adversarial check and known answer

Consider exploration x=mu+epsilon with epsilon iid N(0,sigma²I), latent target theta, and evaluative signal d=−||x−theta||²+noise. Then

`Cov(epsilon,d)=2sigma²(theta−mu)`.

Expand the squared error; centered Gaussian cubic moments vanish. Therefore the direction most correlated with this signal points toward the latent target even when the structural song update is simply `mu_next=mu+eta(theta−mu)` and has **no dopamine input**. A common latent target can generate positive movement along a fitted local dopamine-correlated vector.

Executed50 seeds,23 acoustic dimensions,150 renditions/block,35 blocks, sigma.25,eta.1. In this no-dopamine-input model, median average future alignment is0.01938 versus local shuffled0.000≈(−5.94e−5). An independent-signal control has alignment−8.27e−5. For a dopamine-weighted covariance updater, alignment is also positive. A perfect dopamine clamp leaves target-driven song paths exactly unchanged; it stops the dopamine-dependent updater (final squared target error1 vs unclamped median0.00792). For the direct-target updater, clamped/unclamped final error is0.000627. Observed clamped signals are zero in both models and do not retain an artificial correlation metric.

The models are not fitted to the paper and are not claimed to have identical full observational distributions. This is a checked counterexample to interpreting the **alignment signature alone** as mechanistic proof, not a rebuttal of interventions or other data. A200000-sample independent Gaussian moment control matches the exact covariance within0.000203. FOLLOWUP adds an independent scalar arithmetic check of the empirical mean and the same closed-form covariance derivation.

Both models assume a target is already available. Neither solves how a tutor is chosen or encoded. That is precisely why measuring an error correlate cannot by itself close the cultural-target grounding problem.

## Strongest objection and what to inspect next

Existing pathway perturbations defeat a blanket “dopamine is not causal” story. The current developmental data add natural graded evaluation, while PAG→HVC tutoring evidence addresses acquisition. A useful next question is how social cues select which auditory memories become the reference for the later critic, and whether perturbing a learned tutor representation changes target-specific evaluation rather than generic singing/arousal. This requires tutor identity/exposure and memory/circuit manipulations, not simply more unlabeled song recordings. No new animal experiment, author contact or inaccessible raw-data request was undertaken.

The strongest surviving limitation of this campaign result is missing independent-bird/source-raw structure combined with the adult-endpoint proxy. Strong association is reproducible in the published summaries; the causal architecture and template acquisition remain separate questions. Claims of comprehensive novelty or a falsification of Byrnes's overall framework are unwarranted.

## Commands and failures preserved

From repo root:

```sh
.venv/bin/python campaigns/byrnes_todo_2026-10-28/experiments/song_learning/acquire.py
/Users/vanshkumar/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3 campaigns/byrnes_todo_2026-10-28/experiments/song_learning/extract.py
.venv/bin/python campaigns/byrnes_todo_2026-10-28/experiments/song_learning/run.py
.venv/bin/python campaigns/byrnes_todo_2026-10-28/experiments/song_learning/followup.py
```

Online selected-member acquisition only if caches are absent: range_source.py (public206, bounded4MB per invocation); acquire_followup.py now fetches only the small Fig1 file. Offline run/followup use existing verified originals/members. Initial failed whole-Fig2 acquisition was deliberately not retried at a higher whole-file cap. Acquisition totals are in download_accounting.json. Public raw-spike data for Duffy2022 remain request-only; Figshare code example is synthetic. PMC browser-check, EuropePMC500 and BioC no-result responses were preserved as access limits, not bypassed. No money, accounts, publication, private upload or messages.

Implementation correction: the first simulated clamp diagnostics computed alignment from the latent unclamped evaluator although the path intervention was correct. initial_control_summary.json preserves that run. The final code uses observed clamped d=0, gives zero clamped alignment and retains the same path/intervention conclusion; decisive analyses were rerun. Source analysis did not change. Main/follow-up stderr files are empty.

Final audit correction: root identified that the first follow-up code oriented decile columns using the dopamine endpoints themselves. The final code preserves original A..J ordering and reports monotonic decrease in that order only; it labels endpoint reconciliation to g as post-inspection. No g contrast, source value, source time convention or simulation result changed.
