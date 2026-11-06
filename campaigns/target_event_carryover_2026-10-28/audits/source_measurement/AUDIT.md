# Independent measurement and source audit

2026-10-28. Scope: pinned public code, primary frozen-development transformations, input-only geometry, and bounded prior-work review. This audit estimates no empirical learning or target-carryover effect. The validation rows' outcomes were discarded at ingestion; no external outcomes were parsed. Published aggregates and analysis scripts were known background. All writes are confined to this audit directory.

## Decision for the primary endpoint

Use **the exported unmasked endpoint-angle column `Hand_raw`**, with explicitly chosen baseline-only offset calibration if desired. Preserve person and complete trial chronology. Do not describe it as acquisition-raw: the acquisition/export preprocessing code is absent from the pinned repository. Use the original `Hand` missingness mask as a prespecified sensitivity, and treat `Hand_dt`/`Hand_Diff` only as source-pipeline controls. This recommendation is based on transparent algebraic evidence below, not an observed target effect.

A defensible primary mask is finite endpoint values and a fixed physical-angle bound such as absolute angle <=90 degrees, while keeping all input trials in chronology. Main-trial local smoothing should not define the primary endpoint. The lead should freeze its exact mask and robust/noise model. A baseline offset is constant within person and cancels from genuine differences, but it matters for person-held-out level prediction. Baseline-only mean or median calibration must be fixed in advance.

## Development-only algebra: what the columns actually support

Reproduce with:

```
.venv/bin/python campaigns/target_event_carryover_2026-10-28/audits/source_measurement/audit.py
```

The script reads `protocol/split.json` and copies numeric primary outcomes only after checking membership in the frozen development IDs. It never parses external outcomes. `audit_results.json` holds per-person numerical results, code/source hashes, input cells and seven cross-person checks.

Across all 20 development people (16,480 rows):

| Check | Result | Consequence |
|---|---|---|
| `Hand_raw` finite | Every row | It retains values removed from other columns. |
| `Hand-Hand_raw` where both finite | Exactly zero for every row | `Hand` is a masked version of the same exported angle values. |
| Missing `Hand` / `Hand_dt` | 35 / 33 rows | Masks are not identical. |
| Within-person `Hand_Diff[t] - (Hand_dt[t+1]-Hand_dt[t])` | Max absolute residual 0.000005 degrees; generally floating precision | Source difference uses `Hand_dt`, with CSV precision rounding. |
| Same comparison using `Hand_raw` | Person maxima 2.219–6.284 degrees | `Hand_Diff` is unsuitable as a raw endpoint transition. |
| Within-person difference missingness | Exactly matches missingness of either adjacent `Hand_dt` | It is safe to reconstruct only with true adjacency. |
| `Hand_raw-Hand_dt` after best person-specific linear trend removed | Max absolute residual 6.329–19.334 degrees | `Hand_dt` is neither raw angle minus a constant nor ordinary linear detrending. |
| Candidate centered boxcar transformations | No tested 3/5/7/9/11/21/51/101-trial window reproduces it | The precise transformation remains unresolved; do not assign it an invented smoothing algorithm. |
| Baseline `Hand_raw` mean across people | -0.666 to 3.064 degrees | It is not already person-centered by the first-100-trial mean. |
| Baseline `Hand_raw` median across people | -0.610 to 1.678 degrees | Nor is it centered by that median. |

The two differing angle masks are TE_SPE SN6 TN43 and SN8 TN245: `Hand` is missing but `Hand_dt` is finite. The upstream operation causing this cannot be verified from public code.

### Confirmed cross-participant difference contamination

For TE_SPE SN3→4, SN8→9, SN13→14, and ControlJump SN5→6, SN11→12, SN12→13, SN15→16, the supplied `Hand_Diff` at the first person's TN824 equals the next person's TN1 `Hand_dt` minus the first person's TN824 `Hand_dt`, with residual exactly zero. These seven checks use adjacent people who are **both in development**. No validation outcome was needed. All examined people except final-file SN20 have a finite terminal difference. This establishes that the exported difference traverses participant boundaries. The campaign's boundary-safe event design avoids these rows, but should still rebuild every transition explicitly.

### Pinned-code provenance limit

The complete pinned Tsay root contains `Analysis`, `TJ_Figs`, `TJ_GitHubData`, README and metadata files. All three subdirectories were inventoried. `Analysis` contains plotting/model-fitting/simulation R sources and an HTML notebook. No acquisition, trial-randomization or export-preprocessing source is present. Neither `Hand_raw` nor `Hand_dt` is referenced by those analysis files or embedded notebook. `Hand_Diff` is consumed, never constructed. Seven downloaded code/notebook files match pinned Git blob SHA1s exactly; SHA256 and byte sizes are in `audit_results.json`. The existing feasibility copies of two code files had newline-related byte differences, so this audit preserves fresh byte-exact copies in `code/` without altering prior source files.

The missing upstream code is a provenance limitation, not proof that the published transformation or acquisition was wrong. An inference about exported endpoint behavior is feasible; an assertion of unsmoothed acquisition trajectories is not.

## Chronology, intervention and primary inputs

The paper defines the primary hand measurement at target-distance crossing and the target jump at movement initiation. Fast shooting instructions discourage online adjustment but do not mathematically remove it. Thus an endpoint is a mixture potentially containing online correction; future no-jump readouts are essential. The source's signed convention is operationally clear in `TargetJump_5Feb2022.Rmd`: positive clamps have their response sign reversed for adaptation-magnitude plots. Preserve signed raw angles for this campaign instead of flipping all observations by current clamp.

The paper says Experiment2 has zero-mean 24-trial scheduling. The actual exported sequences support four 180-trial balanced portions plus one deterministic terminal trial per portion, as established in the preflight. No assignment code is available to establish an exact randomization distribution. Use the actual schedules for recovery and participant-level uncertainty; do not manufacture independent Bernoulli assignment or 24-trial permutations.

The nine observed primary cells are **not** a Cartesian clamp-by-jump grid in set A:

| Source set | Current clamp | Permitted target jumps |
|---|---:|---|
| A / TE_SPE | -4 | -8, -4, 0 |
| A / TE_SPE | 0 | -4, 0, +4 |
| A / TE_SPE | +4 | 0, +4, +8 |
| B / ControlJump | -4, 0, +4 | -8, 0, +8 for each clamp |

Both files encode all baseline TN1–100 rows as clamp=0 and target jump=0. The published plotting script groups `TE_SPE_data` and `ControlJump` after `drop_na()` without a `TN>100` filter (lines66–68 and111–113 in the saved byte-exact file). Consequently a reproduction of that source's zero/no-jump cell may contain baseline observations. It is not the randomized index-trial estimand. Its nonzero-input condition summaries are more straightforward extraction controls.

The study's person key must include source file because SN1–20 restarts. Keep the 100 baseline trials and four deterministic probes as chronology/calibration data, but exclude probes and crossing windows from randomized-event contrasts.

## Independent-laboratory transfer: eligible scope and traps

The public repository contains analysis scripts and already-exported CSVs; its MATLAB acquisition/preprocessing sources are not present. In both external analyses `reachAngle=HandError` (fig3 line72; fig4 line58). The paper's Statistical Analysis section (journal p335, PDF page4) states that experiments3/4 use the endpoint at target distance, whereas experiments1/2 use maximum velocity. Do not substitute the latter timing into this transfer.

Experiment3 is the closest transfer source: 18 people, ±4-degree current clamps, with no jump, jump-to, jump-away and flicker. Input-only mapping in `analysis_fig3_tsayrep.Rmd` lines56–69 is:

- `TargetJump==0.01`: jump-in-place/flicker, not a 0.01-degree spatial displacement.
- `TargetJump==ClampAngle`: jump-to.
- `TargetJump==-ClampAngle`: jump-away.
- `TargetJump==0`: stationary target.

The 14,400 randomized exposures contain 1,798–1,802 observations per signed cell, consistent with slight exported imbalance. Trials104–903 are exposures;904 is a final response. Experiment4 has 42 people and 36 cells (12 signed clamps × Miss/Hit/Jump To), each repeated24 times per person over104–967;968 is the final response. Neither has a randomized zero-clamp condition.

**A sign-convention trap in Figure4:** all `TrialLabel=='Jump To'` rows have `TargetJump==-ClampAngle`, unlike Figure3. This is established exclusively from input columns. Use `TrialLabel` to identify geometry; a harmonized physical jump direction requires `jump=ClampAngle` for jump-to, rather than blindly transporting the raw `TargetJump` sign. No acquisition code establishes why the exported signs differ. Fig4's `Hit` uses a larger stationary target, so it is not interchangeable with stationary-small `Miss`. Exported target-size values are in task units and should not be interpreted directly as physical millimeters.

For a narrow prespecified transport, prioritize Figure3's spatial jumps and stationary trials, account separately for flicker in intervening/current-input terms, and freeze whether jump-to only or both spatial directions are eligible. A primary set-A zero-clamp jump shares the spatial magnitude but not the current-error condition with Figure3. Testing the same old-input propagation coefficient when current clamp is nonzero therefore adds an invariance assumption. Include flexible current clamp-by-condition effects and report this as **transport**, never exact replication. Figure4 adds both magnitude interpolation/extrapolation and target-size heterogeneity and is optional secondary evidence, not 42 extra exact replicates.

### External outlier implementation discrepancy

Both external R scripts claim a centered five-trial smooth but implement `mean(y[i-2:i+2], na.rm=T)` (line32). In R, `:` has higher precedence than binary `+` and `-`; the index is `i-(2:i)+2`, namely `i,i-1,...,2`, not `(i-2):(i+2)`. For example i=5 selects5,4,3,2 rather than3,4,5,6,7. This follows the [official R operator-precedence documentation](https://stat.ethz.ch/R-manual/R-devel/library/base/html/Syntax.html). This cumulative-looking smooth only defines the exclusion residual; it is not subtracted from the retained response itself.

The scripts then mask reachAngle when that residual exceeds three person-level SDs, absolute angle exceeds90, or FalseStart==1 (fig3 lines79–104;fig4 lines65–90). They replace values with NA and compute adjacent differences without dropping chronological rows (fig3 lines110–116;fig4 lines96–102). Prespecify a transparent campaign mask and, if source-summary replication is required, separately implement the literal author code and intended centered-window sensitivity. Do not silently correct a source reproduction and call it identical.

There is also a manuscript timing inconsistency: the methods specify target manipulation at one-sixth of the reach, while the Figure3 results prose says halfway through the reach. The methods definition is the most specific available source, but absent acquisition code it is not independently verified.

## Bounded prior-work assessment

1. **[Kim, Parvin & Ivry2019](https://elifesciences.org/articles/39882)** already compared a correction/retention state-space account, task-outcome modulation and parallel errors. Their blocked-transfer fits attributed the clearer difference to updating; retention intervals overlapped and parameter correlations limited interpretation. The present question is not a new gain-versus-retention hypothesis. The candidate extension is old-randomized-input × later-event propagation with withheld quantitative validation, rather than a fit to blocked average learning curves.
2. **[Tsay et al.2022](https://doi.org/10.1371/journal.pcbi.1010005)** already used random-sequence next-trial changes to test clamp, task-error and distraction accounts. The public script aggregates participant-condition medians; its models fit group response-versus-jump curves. It does not implement the proposed earlier-input × zero-clamp event lag curve or reserved-person propagation prediction in inspected code. This is a bounded code comparison, not an exhaustive novelty finding.
3. **[Al-Fawakhiri et al.2023](https://doi.org/10.1152/jn.00061.2023)** already contrasts target-size and target-motion manipulations. Repeating its mean next-trial suppression is a control, not the campaign's contribution.
4. **[Tsay et al.2022 PReMo](https://pmc.ncbi.nlm.nih.gov/articles/PMC9377801/)** formalizes adaptation as goal-minus-perceived-hand correction (equations12–13). It supplies a primary-source rationale for fresh state-dependent error even under zero programmed clamp. As an explicit discrimination witness, `x[t+1]=a*x[t]+b*(c[t]-lambda[Jt]*x[t])+d[Jt]` is algebraically identical to `(a-b*lambda[Jt])*x[t]+b*c[t]+d[Jt]`. With common observations/noise, event-dependent perceived-error correction and event-dependent effective retention can have exactly the same observable law. No amount of endpoint-only fitting distinguishes those paired generators; this does not invalidate an observable propagation result.
5. The bounded search also surfaced [Leow et al.2020, Task Errors Drive Memories That Improve Sensorimotor Adaptation](https://pubmed.ncbi.nlm.nih.gov/32029533/) and [Interaction between model-based and model-free mechanisms in motor learning,2025](https://journals.physiology.org/doi/10.1152/jn.00219.2025). Their retrieved abstracts address prior task-error experience/savings and between-task target-jump carryover. These warn against broad claims that target events or task-error history have never been linked to memory. Neither abstract describes this zero-clamp signed old-input interaction design; abstracts alone cannot prove absence of overlap.

## What this audit changes

The data support a stimulus-anchored endpoint propagation analysis if the lead bypasses unverified detrending, respects actual trial boundaries, controls current/intervening cell geometry, and treats participants as replication units. They cannot independently establish storage, reward specificity, a complete randomization distribution, acquisition-raw trajectories, or exact zero-clamp replication in the second laboratory. The most consequential preventable errors are now concrete: source difference crossing people, transformed-angle differences, external flicker coding, Figure4 reversed jump sign, and cumulative-index outlier smoothing.

The independent extraction/statistic audit later in the campaign should start from the original byte-verified CSVs and frozen endpoint rules, not from `Hand_Diff`, `Hand_dt` or the lead's intermediate tables.
