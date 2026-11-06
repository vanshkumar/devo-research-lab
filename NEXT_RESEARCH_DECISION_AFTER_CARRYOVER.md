# Next research decision: determine what measurement would make the motor-memory question answerable

2026-10-28. Research-decision review after the completed target-event carryover campaign. This is the selected next objective; no successor execution thread, human experiment or automation has been launched.

Strategic update: after the user's request to step back and own the broader initiative, this proposal was **deprioritized as the main next project**. The [research strategy reset](RESEARCH_STRATEGY_RESET_2026-10-28.md) selects autonomous learning-rule transport across training policies. The assay plan below remains a conditional future branch and its technical conclusions are preserved.

## Decision

Run one focused **computational assay-identification study** before commissioning people or fitting the remaining endpoint datasets. Establish which independently checkable measurement constraints and randomized perturbations would separate an event-dependent transition from fresh perceived-error correction, and quantify the precision and sample cost required at the existing 0.2° behavioral scale. Test storage versus expression separately; an assay that resolves one ambiguity need not resolve the other.

The concrete deliverable is an auditable **measurement-and-design frontier**: for a small declared set of candidate assays, identify the closest competing mechanism, any exact observational equivalence, the calibration assumptions that remove it, and the attainable full-procedure discrimination/interval calibration as measurement bias and noise vary. Recommend collection only if at least one version has a defensible measurement contract and useful sensitivity. If every feasible version still admits an exact rival, return that explicit counterexample and the specific additional observation required.

This must produce analytical results, executed simulations and a decision about an actual assay. A list of desirable measurements or a conventional power calculation is insufficient. The intended scientific contribution is a quantitative answer to what can distinguish these accounts, not a claim to have invented observability, rank conditions or motor-learning state models.

## What the completed campaign changes

The [completed report](campaigns/target_event_carryover_2026-10-28/REPORT.md) and [completion audit](campaigns/target_event_carryover_2026-10-28/COMPLETION_AUDIT.md) support closure of that investigation:

- An earlier-error response is present: +0.677° [0.360, 0.995] in reserved people. The event modulation is +0.083° [−0.309, +0.474]; the original ±0.2° margin remains unresolved.
- Added propagation terms worsen the frozen distributed-lag forecast. The independent-laboratory contrast does not establish transport. The later stationary-readout sensitivity has sizeable uncertain negative estimates and must not be described as uniformly near zero.
- Narrow state-model bounds fail known-effect calibration. A covariance-aware repair helps without earning a general bound. High information for stipulated known-generator oracles means this is not a universal data-information limit.
- Exact paired accounts can generate identical endpoints with changed storage retention or fixed retention plus fresh state-dependent perceived error. A dynamic expression process supplies another equivalence.

All 40 primary and 18 external Figure3 people are consumed. External Figure4's 42 people and the optional 210-person geometry outcomes remain unexamined. Their availability alone is not a reason to reopen the same storage claim. Preserve them while establishing what different observation would be informative.

## The proposed new assay needs a stronger test than the completion report suggested

Common no-feedback probes would improve the earlier-input contrast. Initial heading plus endpoint would help distinguish some online corrections from changes already present at movement onset. Perceived-hand and remembered-goal reports could constrain certain error accounts. None is automatically a calibrated storage measurement.

In the restricted one-state model

    x_next = a_J*x + b_J*e,

known, event-invariant observations of x and e identify the two coefficients only when their within-event design has rank two, or one coefficient is independently fixed. The existing zero-clamp witness has e = −lambda_J*x: even perfect error reports leave gain and retention confounded if both are free. Independently randomized event offsets, crossed with precursor states, can supply a missing direction under this restricted measurement model.

Expression is a separate problem. For example,

    S_next = a*S + U
    Z_next = (a + delta*J)*Z + delta*J*S
    y = S + Z

produces the same endpoint recurrence as event-dependent retention of y. Adding heading and endpoint channels that both measure S+Z leaves that identity intact. A second calibrated channel r=S+kappa*Z with known kappa different from one would separate the components algebraically; its error amplification grows as kappa approaches one. There is currently no established reason to treat an aim or hand-location report as that channel. The next study must not assume this anchor into existence.

Active/passive robot-matched localization can constrain contributions under particular assumptions; it is not an established direct readout of stored state. [‘t Hart & Henriques (2016)](https://journals.plos.org/plosone/article?id=10.1371/journal.pone.0163556). Perceptual-report precision and context dependence also require explicit treatment. The design review found categorical report resolution, added reporting time and localization uncertainty large enough that unbiased instantaneous subdegree reports cannot be the default. See [Tsay et al.](https://pmc.ncbi.nlm.nih.gov/articles/PMC7717163/) and [Will & Stenner](https://doi.org/10.1152/jn.00447.2023). Source-specific values must be verified and translated into the proposed assay's error model; they are not universal noise constants.

## A precise execution target

Compare these candidate assay versions, with full generative models and matched assumptions:

1. Existing randomized endpoints: reproduce the exact storage/perceived-error and expression witnesses as negative identification controls.
2. Stationary precursor, randomized target event, five common no-feedback probes, heading and endpoint: test which online/readout alternatives are removed and explicitly retain surviving equivalences.
3. Add hand/goal reports without independently varied event error: demonstrate whether collinearity and unknown report loading/bias still prevent separation.
4. Cross signed precursor amplitudes with independently randomized small event cursor offsets; add independently calibrated perceptual channels, matched report/no-report branches and matched elapsed time. Test whether this separates the declared transition-versus-error accounts, then independently test the expression alternative.

The first substantive computation should extend the campaign's exact paired witnesses through all proposed observation channels. If an exact rival survives, do not calculate a meaningless sample size for distinguishing it. State the calibration restriction or intervention that would have to exclude that rival.

For versions with nonzero separation:

- Freeze a small named mechanism set, plausible parameter/calibration ranges, candidate schedules and a cost measure before optimizing. Include heterogeneous gains, correlated movement/report noise, quantized reports, event-dependent report bias, altered elapsed time and report-induced changes in behavior. Separate justified constraints from speculative ones.
- Compare rivals after fitting or optimizing their permitted nuisance parameters. A favorable known-parameter oracle is an upper reference, not proof that a feasible experiment identifies the mechanism. Establish the minimum separation over the declared uncertainty set and show which nuisance direction makes it collapse.
- Express target differences on the original five-probe behavioral scale, retaining ±0.2° as the reference. Do not substitute a convenient latent-parameter difference or enlarge the margin after failure. Display the full response curve as well; a rebound can cancel in its mean.
- Evaluate existing estimators, including an appropriate stochastic-likelihood or input-moment method when its assumptions apply. The task is to find an honestly calibrated procedure, not to require a new estimator. Test the complete fitting/calibration/selection procedure on independently generated cases, including generators outside the fitted family.
- Assess 95% coverage, false-equivalence behavior at both signed boundaries, false positives and useful power. Use approximately 80% detection as an initial design target with controlled false positives, with enough simulations to quantify uncertainty. Specify the testing convention: a 95% interval wholly inside a margin and a conventional 5% TOST are not interchangeable criteria.
- Report people, episodes, movements, reports and expected session time. Noise can average down; unknown systematic bias or an unanchored expression loading cannot. Show these limits separately rather than quoting one sufficient N.
- Reserve synthetic generator families/parameter regions for an independent final challenge. Have an independent implementation verify the exact witnesses and decisive recovery result. Preserve all failed designs and optimization attempts.

The final result must say one of the following, with explicit scope: a named, implementable assay separates specified accounts under checkable calibration tolerances; an operational transition/error distinction is feasible but storage attribution still requires an unavailable anchor; or all tested feasible assays admit an explicit indistinguishable rival. Do not claim a global minimum over every possible experiment or an impossibility for every neuroscience measurement.

## Why this over the alternatives reviewed

| Alternative | Review judgment |
|---|---|
| More fits or the remaining endpoint cohorts | Do not select merely because outcomes remain unused. They do not themselves remove the exact attribution ambiguity. |
| Promote the colored-noise result into a new statistical theorem | Preserve it as a useful methods result, but the core short-panel nuisance mechanism already has close mathematical prior. A domain benchmark belongs inside assay validation, rather than being sold as an entirely new theory. |
| Commission the report's proposed human assay immediately | Premature: heading and reports do not automatically supply independent calibrated state/error channels. |
| New cerebellar optogenetic reanalysis | Attractive in principle, but this bounded review did not verify the needed released intervention records or later-learning contrast. Do not launch from a code schema alone. |

The exact covariance-dependent concentrated-loss mechanism is already explicit in [Fortin, Gagliardini & Scaillet, §1.3.3](https://academic.oup.com/jfec/article/23/1/nbad024/7271793). Motor-learning estimation/noise precedents include [Albert & Shadmehr (2018)](https://pmc.ncbi.nlm.nih.gov/articles/PMC5966728/) and [Ahn et al.](https://doi.org/10.1371/journal.pone.0158466). Our campaign's witness remains valuable, but a new finding about a wrong candidate's expected loss does not yet prove a global asymptotic false-equivalence result or a new estimator.

The new neural-data lead was Koppen et al.'s temporal-prior study. The verified author archive supplies code expecting optogenetic session files; actual experimental archive access failed, and optogenetic trial availability remains unverified. A different cerebellar-learning source offers data on request. [Bounded source audit](sources/intervention_successor_feasibility_2026-10-28/AUDIT.md). These access limits do not challenge the published science and do not justify bypassing controls.

## Scope and completion

This is a computational/theoretical follow-up, not authorization to recruit participants, contact laboratories, buy equipment, spend money or publish. It can finish with public source constraints, exact algebra, local simulations and independent scientific review. Complete prior studies remain complete; no consumed data can become a new holdout.

The ambition is to obtain a real result about what observation would change the mechanistic judgment—and what precision that observation must achieve. The study should earn or reject a collection recommendation with evidence. It should not end with another loosely specified better-experiment proposal.
