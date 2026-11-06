# Independent empirical partial-identification audit

2026-10-28. Inspected `experiments/empirical_summary.py`, its JSON output, the figure digitization values, and the table transcription. This audit does not redigitize pixels. It independently checks arithmetic, assignment enumeration, source restrictions, and interpretation. No root functions are imported.

I also visually inspected the original `inputs/zhao/figure5.jpg`: the opto-only group has seven diamonds, four below approximately260ms, while the conflict group has four diamonds with middle points near320–350ms. This independently supports the group orientation and approximate digitized medians; it is a visual sanity check, not a second pixel calibration.

## Material correction found and reported

The first root calculation permitted any nonempty assignment of the seven opto-only elements to four birds. Its extrema used four elements in one bird. Zhao main text P10 explicitly reports **one to three song elements** for the300ms opto-tutored birds. The source agent identified this restriction, and I confirmed it in cached `inputs/zhao/pmc.html`, line1437/P10. Therefore a source-consistent primary calculation must cap opto-only bird repertoires at three. The unrestricted result remains a valid broader sensitivity case, but cannot be presented as the sharp source-constrained bound.

The independent code exhausts labelled assignments using `itertools.product`, rejects empty/over-capacity groups, computes each equal-bird mean using Python standard-library arithmetic, and divides the labelled count by k!. This is independent of root's restricted-growth recursion and NumPy means.

| Maximum opto elements/bird | Anonymous partitions | Conflict−opto equal-bird mean bounds, ms |
|---|---:|---:|
|2 (stricter sensitivity)|105|[−175.2755,+31.2672]|
|3 (source-consistent)|315|**[−222.1074,+96.9008]**|
|4 (unrestricted original)|350|[−248.2094,+130.8540]|

The four conflict elements across three nonempty birds have six partitions; their largest group is automatically two. Their equal-bird means range341.0468–425.0689ms. With the source cap3 the opto-only means range328.1680–563.1543ms. All displayed bounds concern a finite set of digitized element summaries, not a population parameter.

A conservative ±4pixel uncertainty for every point gives at most ±13.2231ms for any convex group aggregate. Adding both groups' worst-case errors extends the source-consistent difference bound to **[−248.5537,+123.3471]ms**. This is an extraction sensitivity envelope; it is not a confidence interval. Shared axis uncertainty may correlate the errors, so adding group bounds separately is conservative.

The sign remains unidentified even under the stricter cap2. Thus the substantive missing-membership conclusion survives the correction. Exact membership data would determine the observed cohort means; none of these bounds substitutes for independent-bird or family-level sampling uncertainty.

## Independent arithmetic checks

- Exhausting bit masks selecting4of11 long-table values reproduces all330 possible4/7 splits. Opto-only median range213.4–434.3ms; conflict median range194.3–621.15ms; difference range−240–407.75ms.
- The table support gap is24.1ms. Every convex aggregation of any relevant long subset stays at least24.1ms above every convex aggregation of any short subset, **conditional on the relevant observed groups being contained in the supplied11 and26 values**. This includes equal-bird means formed from retained elements. Table/main-count mismatches must remain explicit; the support statement does not cover omitted or unmeasured renditions or a bird population.
- For the unrestricted grouping, a separate analytical formula matches enumeration: sorted n values assigned to k nonempty groups minimize their equal-group mean by isolating the smallest k−1 values and pooling the rest; maximum isolates the largest k−1. This follows by rearrangement/majorization of per-observation weights. The root's unrestricted witnesses match those extrema. The source capacity restriction requires the constrained enumeration above.

## Calibration and claim boundary

The frozen root protocol used the main-text300ms median323ms. Against the newly digitized conflict median332.2314ms, that yields an arithmetic residual **+9.2314ms**. The later switch to the plot's opto-only median249.5868ms produces residual **+82.6446ms**. Because that switch followed source inconsistency discovery and access to the plotted outcomes, preserve the frozen calculation and rejection reason in provenance, and label the plot-based version exploratory. If the source audit establishes323ms is a pooled or unsuitable subgroup value, it must **not** remain a valid primary biological prediction merely because it was frozen earlier. Both reference, motor-scaffold, and shared implementations have the same prediction under the stipulated common overwrite map; neither residual ranks them.

Do not call a nonzero extraction-only residual a statistical rejection of overwrite. Do not call a small residual statistical equivalence. Neither comparison is untouched independent-bird validation.

The partial-identification finding concerns the accessible summaries, not a demonstrated error in the original analysis. The paper explicitly reports by-bird statistics for the short-versus-long manipulation. Unknown public memberships prevent reproducing that calculation; they do not show it was incorrectly performed. The source-cap correction and omitted-metadata problem narrow the reanalysis without invalidating the qualitative intervention evidence.

## Reproduction

```sh
.venv/bin/python campaigns/song_target_memory_2026-10-28/audits/model_audit/check_empirical_bounds.py
```

`empirical_independent_check.json` contains source hash, exact counts, witnesses, extrema, and original-calibration sensitivity. Saved stdout/stderr are `empirical_check_stdout.log` and `empirical_check_stderr.log`; stderr is empty. This computation runs offline and requires no long job or external contact.
