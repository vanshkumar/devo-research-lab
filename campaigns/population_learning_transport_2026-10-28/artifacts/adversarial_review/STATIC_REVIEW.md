# Independent static adversarial review

2026-10-28, America/New_York. Reviewed after the prospective freeze and during prefix-only forecasting. **No new-source prefix file/value, future outcome, or external prefix/outcome was opened for this review.** The review used frozen code/protocol text, pinned metadata, existing consumed-source controls and synthetic arrays.

Freeze SHA256: `625535ac5c20fe7301b7dcdec22549fd0a708271cc51dd79df8dee6f5c37a64c`. All44 listed files matched their hashes at review time. `STATIC_CHECKS.json` records the verification.

## Verdict

The primary endpoint, autonomous chronology, complete-data gate and prospective source allocation are consistent with the frozen design. Complete-data gate results independently match the pre-exposure audit implementation in200 synthetic constructions; maximum animal/cluster interval discrepancy was5.6e−17. There is one demonstrated missing-subgroup edge case to check against actual score availability, and the source scorer's release flag requires the explicit independent-audit guard described below. Neither issue caused a protected external read during this review.

## Confirmed scientific safeguards

- `campaign.py:summarize` uses only signed contrast exactly±1 (1e−9 tolerance), equally averages the two side shares, and includes omissions in each side denominator as failures. A .5contrast never enters this endpoint. The probe is stored separately and is never substituted for observed accuracy.
- Each simulated choice is sampled from the pre-update state; then omission is applied, feedback and adaptive trainer state are generated, and only then does the frozen learner update. Real future contrasts/choices/rewards are absent from the simulation arguments. Realized session-start opportunities are the only future input.
- Prefix calibration retains the frozen RNN three-parameter initial-state MAP and joint Fisher propagation. Growth uses the frozen donor bank/recent500recipe; persistence uses all1000and the .5ridge prior. No new actor fit, per-animal future path or external learning-rate fit appears.
- Metadata determines24primary/one partial animal, with no achieved-learning screen. The incomplete517-opportunity animal is absent from the prefix iteration. The partial animal's future is truncated to four full500bins; the last473opportunities are not scored by this code.
- `score_campaign.py:intervals` agrees with ordinary animal-t and CR1cluster-t formulas when all endpoint cells exist. It averages six population-bin means equally, preserves the common observed-defined mask, and uses influence weights for unequal endpoint availability. The frozen complete-case controls do not separately establish coverage for every missingness mechanism.
- Source gate checks include both90%intervals wholly inside±5pp, curveMAE≤5pp/maxbin≤7.5pp, lab±10pp/leave-lab±5pp, ≥80%endpoint availability per bin, N≥15, baseline noninferiority within1pp, and valid known-answer controls. The code's strict interval boundary comparisons differ only at exact equality from the audit's inclusive comparisons; none of the200checks disagreed.
- The RNN-generator control uses independent future action/trainer streams under both trainers. It is a known-law generative/score control, not a new fitted-rule recovery experiment or independent biological validation. The low observed one-cohort source-generator acceptance and empirical-residual acceptance are correctly disclosed.

## Findings requiring explicit handling

**1. Source `external_release` is provisional performance, not full authorization.** `score_source` writes `SOURCE_GATE.json.external_release = result['gate_earned']` before it checks independently reconstructed scores or replay results. Frozen PROTOCOL requires both before release. The lead accepted this finding before any scored future access and saved `protocols/RELEASE_REQUIREMENTS.json`: the flag alone grants nothing; successful hashed reconstruction, replay, adversarial resolution and a separately frozen external protocol are required. The present mixed reader supports only the excluded26source inventory; an external forecast cannot silently pass through that reader. Review the future external opener against this guard if a source performance pass is obtained.

**2. Undefined subgroup error can be silently ignored.** In `score_campaign.py:35–45`, a laboratory with no valid endpoint for one or more bins receives a NaN scalar after `nanmean(...).mean()`. Python `max` may ignore a non-first NaN. A concrete synthetic construction with zero errors in23animals and every endpoint missing for the singleton third lab passes the entire gate, despite the third lab having no scalar estimate. Its per-bin availability is23/24, so the global80%check does not prevent the failure. The synthetic run emits a “mean of empty slice” warning and is recorded in `STATIC_CHECKS.json`.

This is not permission to alter a scientific tolerance or select subjects after exposure. Before any external release, require all lab and leave-lab scalar summaries to be finite; if the real primary endpoints are complete and all lab summaries finite, this edge case has no effect on the result. If an actual lab/bin is undefined, the corresponding safeguard is unevaluable and release must remain unearned/inconclusive. Do not let the literal frozen Python NaN behavior convert missing evidence into a pass. This finding was sent immediately to the lead while scored outcomes remained sealed.

## Remaining interpretation limits

The source gate has intentionally low power for establishing±5ppaccuracy at empirical heterogeneity. A failure is a lack of release evidence unless the actual error/interval independently demonstrates a practical discrepancy. A source mean can be accurate despite large individual errors, and source calibration does not identify a causal policy effect. The external shift bundles animals/lab/year/genotype/handling with curriculum. Reward amount and wheel gain remain omitted actor inputs, even when trainer metadata is generated accurately.

This review does not certify future results, raw-byte score reconstruction, replay completion or external authorization. Those require the actual independent artifacts and outcome review after the lead's access boundary is satisfied.

## Post-scoring disposition of static findings

The subsequently authorized aggregate review found every primary endpoint and lab/leave-lab estimate finite, so finding2had no effect. `SOURCE_GATE.json` records a failed source performance gate and `external_release:false`, so no external release is warranted. The separate `RESULTS_REVIEW.md` provides the numerical interpretation and independent aggregate checks; it does not substitute for the original-byte and simulator reviewers' work.
