# Event measurements found; defining source certification incomplete

**Partial source-gate stop. No held-animal forecast, model comparison, uncertainty interval or utility result was computed.** The original question remains unresolved: does pre-stimulation neural state improve measured downstream response forecasts beyond pair means and own activity/history?

## Direct observations

The article-linked public OSF deposit `e2syt` has a `raw_extracted_data/` folder with 678 listed items, consistent with 113 six-file recording exports. The first listing page exposes matched dataset-name, GCaMP, neuron-label, stimulation-neuron, stimulation-volume and time files. These are event-level traces, not fitted atlas kernels. Bulk current exports are 84,924,311 bytes (unc-31), 523,093,816 bytes (WT text) and 1,143,920,663 bytes (full native objects), all over this allocation's 50 MB ingress ceiling. This does not show that the full archive lacks needed metadata.

All six files of recording 0 were acquired and pinned. `FIRST_DATA_CHECK.json` contains actual executed alignment arithmetic at 04:16:11Z, well inside the 04:30:34.816Z source gate. The fluorescence table has **4,454 × 114 values, 384,648 finite**, with 55 nonempty label strings, 70 stimulation events, 2,226.5 seconds of nominal time, and exactly 0.5-second increments. The shortest inter-event interval is 30.5 seconds. Five stimulation target codes are -3 and seven are -2. The first event's target label is empty; it was not certified as an identified-neuron intervention.

At the second event, frame 101 / nominal 50.5 s, target index 19 is labeled AVEL. The diagnostic window [-10,-1) s has 18 frames and [2,12) s has 20 frames, with usable pre/post means in 53 named downstream columns. Their median absolute post-minus-pre difference is 0.907619 fluorescence units. For example, IL2V changes 11.752593 → 12.875333 (+1.122741). The next event is labeled AVAL, with 53 available downstream columns and median absolute change 0.996444. These calculations demonstrate available measurements and variation; they are not estimates of causal effects or forecast utility. Availability here accepts any finite observations and is deliberately not a main-analysis quality rule.

Only metadata were acquired for recordings 1 and 2. Their source paths end in `20210824_114940` and `20210824_144628`, versus `20210824_104000` for recording 0. Their metadata declare 5,395/3,789 frames, 136/132 columns and 85/61 events. Neither fluorescence payload was acquired. All three inspected records also have missing or ambiguous identities; recordings 0 and 2 have duplicate nonempty label strings. See `METADATA_CHECK.json` for complete counts, including the initially permissive named-event counts that still include ambiguous strings.

## Why the gate did not pass

The publication reports 113 WT-background individuals, and the library README describes aggregating recordings from different animals. However, the inspected six-field export supplies recording paths without an explicit animal-to-record linkage or reuse indicator. Matching the total of 113 presumed exports to 113 published animals is suggestive, not a certified per-record independent-animal map. This assignment required that distinction before held-animal evaluation.

The paper describes a default 500-ms WT stimulation and a special AFD series with 100–500-ms durations. The plain export has no per-event duration or protocol/strain field; recording 1 includes an AFDR-targeted event. The native event properties were not retrieved. Thus a protocol default was not promoted into an observed duration for these events.

The source code's `export_to_txt` writes `self.sig[ds].data`, an artificial uniform `arange * Dt` time vector, `i0s + shift_vols`, target indices and label strings. It does not export signal-loading/processing settings, actual acquisition timestamps, target-hit checks, or complementary labels for -3 targets. `Funatlas.from_datasets` accepts variable signal-processing arguments and optionally replaces failed stimulation cross-checks with -2. The provenance of the separately uploaded 2024 `raw_extracted_data` objects was not certified from the inspected materials. Published interpolation/bleach removal/filtering cannot simply be assumed to have or not to have been applied. Consequently a past-only predictive information set was not certified.

The paper contains useful illumination/off-target characterization and unstimulated control descriptions, including a visible stimulus artifact. No matching sham/off-target traces or event-level artifact flags were acquired. The OSF node's explicit license field is null; the article is CC-BY-4.0 and the pinned analysis code is GPL-3.0. Neither was asserted to license the external OSF files.

These are **limits of this bounded certification**, not claims that the archive is invalid, that the observations are absent everywhere, or that state modulation is absent. The instruction was to stop rather than substitute summary endpoints or a recording-level comparison when the defining gate remained unmet. The remaining operations were not spent on an acquisition repair chain or a third source family.

## Prior work and interpretation

Randi, Sharma, Dvali and Leifer, *Nature* 623, 406–414 (2023), DOI 10.1038/s41586-023-06683-4, already reports heterogeneous trial/animal responses and kernels and discusses state/history, neuromodulation, plasticity and animal differences as possible contributors. This run found no novel biological result. A useful event-level opportunity exists, but this allocation did not earn the requested independent-animal forecast comparison.

## Limits, exposure and decision

Recording 0's **entire fluorescence table**, including unlabeled columns, is development-exposed/consumed, not just the examples printed. Recordings 1 and 2 have complete metadata exposure and no acquired fluorescence values. Article summaries, source code, top-level file metadata and the first 100-item raw-folder page are exposed. Protected cohorts and older closed branches were not opened.

Main freeze, fitting, predictions, scoring, animal uncertainty, finite positive/null controls, contrary checks and independent review are all **UNRUN**. There are no active jobs. Resources and source pins are in `RESOURCES.json` / `SOURCE_MANIFEST.json`; unknown failed-transfer/provider quantities remain explicitly unknown with conservative charges. Recommendation: close this allocation and return to the PI for reallocation. Do not restart it automatically or label an input/data check as an empirical forecast result. A future independently justified revisit would need an exact affordable object that supplies the missing record/protocol/processing linkage first.
