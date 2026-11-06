# Final source-claims review

2026-10-28. Scope: final REPORT.md, recovery_summary.json and the preserved Zhao/Roberts primary evidence. No new acquisition, model rerun, independent replication, or root edits. Prior mathematical/code auditors own those checks. LEARNINGS.md reread.

Reviewed snapshots:

- REPORT.md SHA256 `409602e4a6198c8c4adc8865d2613b24a28e9221422517e31a117f289ee56569`
- outputs/recovery_summary.json SHA256 `02865954c701f0eb8668766e2a974c289333948223c0a50a5371dfd078548ac5`
- audits/roberts/EVIDENCE.md SHA256 `5f8d5202d7991ddd4956f680bb8856ae5d38d6eaff2a7e0520c81b52bbab1112`
- audits/zhao_source/EVIDENCE.md SHA256 `4c19a4bd822220f719394a051c6dc047258b5118e5d8ccc8b419447c0cc64a82`

## Verdict

**Major numerical source claims match. Two small causal/measurement wording corrections are recommended before finalization.** The report correctly rejects a selective-recovery-only reading of Roberts and does not turn plotted element means or boxplot summaries into independent birds. It appropriately narrows the novelty and validation claims. No result-changing source discrepancy found beyond the already disclosed Zhao table inconsistencies.

## Recommended corrections

1. **REPORT.md line66: qualify the local-restoration inference and surface the order confound.** The sentence calling a pathway-independent local restorer inconsistent with the result is conditional on the correct intervention mapping, but should make explicit that the observed pre/post difference must be attributable to the lesion rather than elapsed time/retest and changed local state. Every Figure6 bird was intact first; at least3 weeks elapsed after caspase; no Figure6 sham/retest cohort is described; baseline motif duration changes slightly. The same concerns appear in the linked source audit, but this is central enough for one report sentence. Suggested wording: “This challenges a local restorer assumed unchanged by the lesion, but intact-first order, no described sham/retest cohort, partial ablation and small baseline timing changes limit that exclusion.” This does not deny the published causal evidence; it stops the campaign's restricted model comparison being stated as an unconditional architectural result.

2. **outputs/recovery_summary.json restrictions[1]: replace signed-drift wording.** “Timing baseline drift rose” is stronger than the accessible rate definition supports. Use “the displayed baseline rate magnitude increased.” The source plots baseline and return rates positive without fully specifying slope/sign handling. The separate claim of a slight change in motif duration is supported by PMC Supplementary Figure6, but is not the same measurement as Figure6's baseline slope.

Optional clarity: the report could explicitly say that Zhao contains no auditory-feedback-removal test. It currently attributes feedback-pathway constraints to Roberts and does not falsely claim such a Zhao control, so omission is not an error. Similarly, including Roberts n=5 in the main prose would improve clarity even though t(4), the cited audit, and JSON already establish it.

## Verified major claims

| Claim | Source check / scope |
|---|---|
| Zhao four50ms pulses at100ms onset spacing versus one300ms pulse | Verified main Figure3 and supplement;200 versus300ms total illumination; no factorial width/spacing isolation. Rhythm alternative is prior Mackevicius work, correctly not claimed as new. |
| Short TableS1 has26 means, mean70.073ms, median60.75ms; main25 elements and62.3ms | Verified independent transcription and primary source;59.2/62.3 single-deletion median range preserved as sensitivity rather than repair. |
| Long11 TableS1 values combine two conditions, median323.5ms, unlabeled membership | Verified. Report correctly rejects323ms as verified opto-only calibration and does not identify membership by value size. |
| max(short)=152.0,min(long)=176.1, support gap24.1 or24.0 with rounding | Verified means-of-elements claim; report explicitly excludes rendition/population inference and conditions on observed table coverage. |
| Figure5 opto-only7elements/4birds versus conflict4/3; plotted medians249.6/332.2ms | Matches preserved digitization;236.4–262.8 and319.0–345.5 are extraction envelopes only. |
| Maximum3 elements per opto-only bird | Rechecked exact primary Results sentence:300ms birds produced one to three song elements. Short-group statement only says a majority, so no analogous strict short cap is supported. Root applies cap only to opto-only. Assignment enumeration itself belongs to model audit. |
| Zhao gradual maturation and lesion chronology | Verified; report allows latent motor restructuring and discloses continuing exposure of pre-exposed birds until60dph after lesion injection. Projection cell kill is not terminal-only. |
| Roberts temporal WN learning also slows | Verified Results:4/5 slower. Paired t(4)=4.8,p=.008 belongs to recovery. No WN-learning or pitch t/p is supplied for Figure6. Report does not invent one. |
| Roberts temporal endpoint includes syllable+gap | Verified explicit Methods onset-to-next-onset definition despite abbreviated gap plot label. Report does not substitute Zhao's voiced duration. |
| Temporal means2.042→1.028 learning,1.236→0.389 return | Matches caption-defined vector mean markers and ±~.031ms/day extraction envelopes. Group ratios0.503/0.315 and gain prediction0.622 are descriptive calculations from those means. |
| Five birds per task, three shared between tasks | Verified Methods:7 unique birds; JSON gives correct task overlap. No independent10-bird assumption. |

## Recovery summary inference check

The JSON explicitly labels exploratory published-summary reconstruction, not paired reanalysis, biological replication or untouched validation. Each ratio is correctly described as a ratio of group means, not a mean of paired ratios. Extraction intervals are consistently distinguished from confidence intervals. The gain diagnostic does not report a likelihood, p-value, paired variance estimate or model rejection. Its nonoverlapping extraction envelopes only show the plotted summaries differ from the restricted one-gain prediction beyond the chosen reading allowance; they cannot statistically reject a population common-gain model, rule out bird-specific gains, or infer a population gain difference.

The frozen exponential-fraction model is explicitly left unfitted because rate magnitudes cannot replace displacement-normalized recovery fractions with measured windows. This is the correct response to source feasibility. The published pre/post temporal recovery test is carried forward as a source result, not recalculated from invented points. The report also correctly states that complete selective evaluator erasure is not established: residual rate, partial ablation, temporal-learning loss and uncertain dynamics all matter.

## Novelty and cross-study boundary

The report does not claim a new rhythm explanation, de novo motor scaffold mechanism, unique storage site, untouched prediction, or new neural discovery. Its formal equivalence is explicitly restricted to scalar effective models and specified mappings, avoiding a universal impossibility claim. Roberts adult setpoint recovery and Zhao juvenile tutoring are not the same cohort or endpoint; the final report expressly denies establishing their causal identity. A positive future evaluative-mediation interaction would identify a functional route under exclusion assumptions, not necessarily an anatomically distinct target store; the report preserves that distinction.

No new project-learning entry is necessary beyond the source distinctions already sent for root integration; this review reconfirms rather than adds a new observation.
