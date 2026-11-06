# Zhao2019 source audit

2026-10-28. Primary: Zhao, Garcia-Oscos, Dinh & Roberts, Science366:83–89, DOI10.1126/science.aaw4226; official author manuscript PMC7688245. Full primary HTML and all supplementary methods/captions inspected. Official figures3–6 inspected visually. Supplement TableS1 inspected as embedded raster and rendered page15; independent transcription by contrary_sources agent confirms arithmetic. Paths below relative to campaign root.

## Consequential result for this campaign

The two artificial-tutoring conditions do not isolate light-pulse width. Fig3A/E contrasts four50-ms pulses at100-ms onset spacing against a single300-ms pulse; total illumination per trial also changes200→300ms. There is no width×spacing arm in the main paper or supplement. Subsequent sequence-network predictions must distinguish voiced-element duration from neural sequence or onset-to-onset period. The published element segmentation can partition a continuous vocalization using amplitude fluctuations; silent gaps are not required. No gap-duration table or matched sequence-period measurement is supplied.

Published TableS1 cannot support a clean individual-bird quantitative holdout: it supplies element means and within-element SDs but no bird identities. Its long row combines11 elements from the opto-only and conflict cohorts. Its short row contains26 means, averaging70.073ms (printed70.1), median60.75ms; main Fig3 captions instead report25 elements and main text median62.3ms. Two red table values59.2 and62.3 are its middle entries. No arbitrary point is removed. This is an unresolved source-summary discrepancy, not proof that the causal duration effect is false.

## Intervention/evidence matrix

| Condition | Intervention and timing | Observation and unit | Controls/uncertainty/source |
|---|---|---|---|
| Untutored baseline | Foster mother; no male tutor after<12dph | Adult song elements;10birds/61elements | MainP9/Fig3; these are not hand-reared socially isolated birds |
| Normal tutor | Natural social tutoring |15birds/73elements; pooled median106ms | MainP9/Fig3; no bird IDs in available table |
| Short opto | ChR2 in NIf35–45dph; at least2wk expression;4×50ms pulses per motif event at100ms onset spacing;5 sessions within10days | Main7birds/25elements; one adult day90–120dph;40motifs/bird | Fig3A; supplement PDFpp4–6. Table26-element mismatch. Pooled main median62.3ms; table median60.75ms |
| Long opto only | Same acquisition/preselection; one300ms pulse per motif event;5sessions |4birds/7elements; adult endpoint | MainFig3G/Fig5C; no individual IDs. Figure-derived pooled median≈250ms, conservative extraction interval236–263ms, not biological CI. Caption's323ms does not agree with this group's plotted median; pooled long11 table median323.5ms |
| Natural+long opto | Each detected live-tutor motif triggers300ms pulse;5days,≈90min/day |3birds/4elements;3bird-level tutor-similarity marks | Fig5. Figure-derived pooled element median≈332ms, extraction interval319–345ms; low tutor similarity. No within-bird pairing of durations/tutor exposures in public material. P=.9 is a distributional non-detection, not equivalence |
| Lesion before tutoring | Intersectional retrogradeCre inHVC plus Cre-dependent caspase3 inNIf at35–40dph; isolate then tutor55–60dph | Adult SAP similarity;4plotted bird marks | MainP17/Fig6; four marks is observed figure count, not separately stated sample size. Low copying. Compare normal tutors and isolates |
| Tutoring before lesion | Raised with tutor; same lesion35–40dph; separation from tutor at60dph | Adult similarity;5plotted bird marks | MainP17, supplement PDFp6, Fig6. High copying. Crucial qualification: post-lesion group continues social exposure until60dph; this is not a clean identical-duration tutoring-order crossover |

The Fig5B and Fig6B normal-control plotted values appear reused; no IDs establish independent cohorts. Do not count those panels as independent replication. Main pre/post-lesion comparison supports an acquisition-stage bottleneck but cannot prove exact storage site or an explicit comparison algorithm.

## Methods and mechanistic controls

- **Targeting**: axon-targeted ChR2 delivery; Fig2/mainP7–8 reports AMPA/NMDA-mediated input, complex polysynaptic HVC responses. Most recorded sites increase firing; some decrease. No single HVC target cell class is isolated.
- **Off-target tests**: retrograde tracing shows largely separate NIf→HVC and NIf→Av populations (<5%double projections); no observed antidromic responses at9NIf recording sites in3hemispheres/2birds; optically evoked HVC responses only within first500µm vsAv≈1.5mm away. These favor local terminal action, but do not identify which downstream plasticity is written or eliminate every network-mediated effect.
- **Preselection**: birds entered behavioral tutoring only after strong light-evoked responses at≥3sites per hemisphere, spaced≥100µm. Pre-stimulation vocalizations had to be subsong. Results concern this selected successfully stimulated sample, not arbitrary injected juveniles (supplement PDFpp4–5).
- **Dose scheduling**: opto-only sessions replay the event times from one of two real90min tutoring sessions, containing300 or370motifs; assignment to event pattern randomized. All stimuli within one session thus have naturalistic motif timing, but the within-event short/long pattern differs. No reported randomization of pulse-duration condition or blinding of song analysis (supplement PDFpp5–6,S3).
- **Measurement**: one adult day; dominant motif identified by visual inspection and female-directed song;40renditions per bird. SAP2011 adaptive amplitude threshold used with a manually chosen common constant across all birds. Developmental tracing and visual inspection check segmentation; analysis explicitly unblinded. TableS1SD is within-element rendition variation, not between-bird uncertainty.
- **Gradual learning**: Fig4/S7 provide selected examples, not raw longitudinal population trajectories.50ms example splits an initially long element into shorter amplitude-modulated units;300ms example refines harmonic elements after stimulation ends. MainP13 says initial changes2–3days, continued refinement over≈month, crystallization≈85–90dph. This rejects a strict instantaneous-and-fixed output imposition; it does not exclude latent motor-network restructuring whose output is learned/developed later.
- **Innate-output-selection check**:12/14opto birds retain recognizable introductory elements in addition to motifs; one sibling pair uses continuous introductory sounds. Long opto elements exceed isolate distribution. This challenges simple selection of only introductory notes or unmodified isolate syllables, but does not eliminate motor plasticity in a growing network.
- **Feedback**: no deafening, feedback delay, auditory-error clamp or auditory-feedback removal experiment is reported in the full main text or this supplement. Do not attribute demonstrated feedback dependence of this opto effect to this paper. Broader song-feedback literature can constrain models separately.
- **Lesion efficacy**: supplement PDFp3 states retrograde tracer verification after genetic lesions; no quantitative lesion-completeness table or residual-neuron count is provided here. Caspase3 kills projection-defined NIf neurons, including any collateral outputs of those cells, rather than severing only theirHVC terminals.

## Numerical extraction and validation boundary

`audits/zhao_source/EXTRACTION_PLAN.md` predates source numeric inspection. Qualitative short/long/conflict/lesion results were already known; this is never untouched literature validation. Main captions exposed some numeric outcomes before root model fitting. TableS1's pooled long row also exposes conflict-group values without labels. A bird-level heldout likelihood cannot honestly be calculated from it.

`table_s1_transcription.csv` preserves exact one-decimal printed element means andSDs, missing IDs,40renditions, and source page. `table_s1_summary.json` checks arithmetic. `audits/prior_work/zhao_table_independent.json` independently transcribes26+11means and agrees. The one-omitted-point median range is only a diagnostic of the25/26discrepancy, not a repaired dataset.

`figure5_duration_digitization_corrected.json` reconstructs group-specific plot marks from panelC without assigning table rows to groups. Axis ticks0,400,800,1200ms were read at source y430,309,188,67. Colored connected components identify separated marks; two merged components at the low end of the opto-only cohort are resolved by visible diamond centers in a preserved crop. Their uncertainty is widened to±3pixels; the conservative median envelope additionally allows±1pixel axis calibration. Original uncorrected components are preserved. These are endpoint summaries from plotted elements;4+3birds are the independent experimental units. No element bootstrap, animalCI or claim of equal group means is warranted.

## Access and reproduction

- Main source URL: https://pmc.ncbi.nlm.nih.gov/articles/PMC7688245/ ; shell download succeeded while web renderer initially saw a browser check.
- Supplement URL as linked by PMC: https://pmc.ncbi.nlm.nih.gov/articles/instance/7688245/bin/NIHMS1646797-supplement-Supp_Material_and_Figures.pdf . Direct curl returned a normal download-preparation HTML page, not a PDF. A normal in-app-browser visit and click of the public supplement link produced an ordinary download at `/Users/vanshkumar/Downloads/NIHMS1646797-supplement-Supp_Material_and_Figures.pdf`; that exact file was copied to `inputs/zhao/supplement_verified.pdf`. No captcha was solved and no challenge/cookie internals were manipulated.
- Publisher supplementary link returned blockedHTML; EuropePMC fulltext/supplement APIs did not supply the file. These response bodies are retained with honest extensions.
- Official figureCDN URLs and all SHA256/file sizes are in `inputs/zhao/MANIFEST.json`.
- `pypdf` from bundled runtime extracted full text and embedded table raster. Poppler produced page15/16PNGs but emitted fontconfig cache errors; source raster and rendered table were inspected and agreed. No font settings/permissions changed.

Offline reproduction:

```sh
.venv/bin/python campaigns/song_target_memory_2026-10-28/audits/zhao_source/transcribe_table.py
.venv/bin/python campaigns/song_target_memory_2026-10-28/audits/zhao_source/digitize.py
```

No new animal data, source author contact, external messages, private uploads, payments or publication.

## Independent bound check and kernel audit

`audit_support_bound.py` independently confirms from the transcribed table that every observed long element mean exceeds every short element mean:176.1−152.0=24.1ms (24.0ms allowing ordinary±0.05ms rounding on each endpoint). Every nonempty long subset retains this lower bound. Convex averaging of observed element means within any nonempty assignment to birds preserves it, as does any arbitrary single deletion from the26short entries. This is a robust finite-sample support constraint despite missing IDs; it is not per-rendition nonoverlap or a population effect/p-value. Table colors encode treatment and red median marks, not bird identities. S7 identifies one sibling pair, so independence of family histories is not established.

`audit_hvc_kernel.py` independently translated originalHVCIter.m into scalar Python without importing the root reference and compared the compiledC++subject under test:5cases, exact binary activity, maximum weight error1.11e−15. This duplicated an audit concurrently completed elsewhere before coordination caught it; it is a numerical check, not an additional empirical result. The model cannot be given acoustic predictive credit without a decoder between sequence duration and voiced elements. Original `hvc_RhythmicStim.m` explicitly changes parameters acrossISI; the root's fixed-parameter multi-ISI test is a new stress test, not an exact replay of that tuned script.
