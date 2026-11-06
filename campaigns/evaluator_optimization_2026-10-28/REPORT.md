# A locally learned sensory reward teaches independent reachable motor plants

Completed 2026-10-28. All held-out learning, declared challenges, independent reconstructions and fresh-source replay are complete. No successor campaign is launched.

A sensory cancellation circuit trained with local plasticity supplied useful, target-specific feedback for complete motor optimization through independently constructed plants. On 12 new whole plant/circuit/target/start tuples,35 tutor renditions followed by 641 scalar-feedback slots removed **97.17% of initial true feature error** [95% paired plant bootstrap94.38–98.96%]. The matched true-error oracle removed99.9977%. All 12 learned-reward actors reached the declared secondary fidelity threshold; neither untutored nor context-shuffled tutoring did so on any plant.

This is a computational sufficiency result for a specified favorable assay: four shared motor coordinates, a controllable signed auditory-drive gain, six supplied clocked contexts, normalized synthetic features, deterministic resets and zero circuit noise. Every new plant receives its own newly tutored evaluator. The result concerns the portability of the tutoring-and-search recipe across sampled plants; it does not establish transfer of one trained network, natural vocal learning or a unique biological mechanism.

## Question and owner decision

The primary hypothesis was positive: a locally acquired sensory reward can achieve at least half the matched oracle's mean target improvement and beat both untutored and incorrectly associated tutoring. A one-plant misleading gain preference was development evidence, not proof that complete learning would fail. We tested full trajectories, exact reachability, a successful oracle and entirely new plants before deciding how useful the evaluator was.

The portfolio reassessment retained the prospective mouse forecast study as the lab's strongest empirical account. Its growth advantage4.69pp[2.85,5.67] on 24 unused animals survives as a specific benchmark finding, with session-model/selection objections and unearned external gates intact. The other completed atlas, song, human and motor programs lacked defining measurements for a stronger immediate biological test. Three bounded independent reviews are saved in [the agenda review directory](../research_agenda_2026-10-28/reviews/). This allocation selected one complete computational teaching experiment, not another empirical parameter repair or a broad literature search.

## Frozen test and target information

The plant is fixed before target draw: six separately sampled100-channel rectified affine maps from a shared four-dimensional program, each centered and standardized to SD2. A common nonnegative gain acts after normalization. Target and starting programs are independent draws; the exact target is reachable at gain 1. Unit target gain is a known property of this normalized task family, and all primary actors start at unit gain. Individual target shape is supplied only through evaluator tutoring; the motor actor sees scalar feedback and no target action, target features, offline MSE or derivatives through the plant. The oracle is explicitly privileged.

We execute the unchanged pinned600E/150I Gong circuit/plasticity with a supplied15-HVC clock. Six100-ms patterns have120-ms score windows; mean excitatory rate is the cost.Correct35 and140 tutoring share the original initialization and exactly the same first35-rendition sensory/clock prefix. Shuffled35 shares the initialization, clock and marginal sensory exposures while deliberately changing context assignment. Each frozen evaluator has its own500-ms burn from the same original membrane states. Published example training uses noise.1; this assay uses zero noise.140 is continued exposure under fixed settings, not an established converged teacher.

All six arms use the same641 feedback slots and common target-blind broad proposals, with local coordinate polls in other rounds. Search is deterministic derivative-free optimization, chosen favorably to assess reward utility, rather than a biological actor-critic implementation. Fixed gain removes an action axis and supplies the task's known nominal amplitude; it is an ablation, not a task-preserving repair. See [METHODS.md](METHODS.md), [the held-out plan](protocols/HELDOUT_PLAN.md) and [the timestamped code/protocol freeze](protocols/FREEZE.json).

## Held-out primary result

Each row includes all 12 frozen tuples. Intervals resample whole tuples, paired across arms; they concern this synthetic generator. Fidelity means terminalMSE<=.4, one tenth of target feature energy4. The mean initialMSE is6.197, range1.285–9.422.

| Feedback / control | Mean initial error removed [95% interval] | Mean terminal featureMSE | Fidelity count |
|---|---:|---:|---:|
| True-error oracle, joint |99.9977%[99.9961,99.9989]|.000108|12/12|
| Learned35, joint |97.17%[94.38,98.96]|.10434|12/12|
| Learned35, fixed gain |99.30%[98.91,99.63]|.03074|12/12|
| Learned140, joint |51.27%[2.18,84.24]|2.14412|4/12|
| Untutored, joint |.59%[−50.35,37.16]|4.41862|0/12|
| Shuffled35, joint |17.31%[−25.37,48.04]|3.66902|0/12|

Learned35 captures97.17%[94.38,98.96] of the oracle's mean normalized improvement. Its improvement advantage over shuffled35 is79.86 percentage points of initial error[50.58,120.01], and over untutored96.58[61.34,144.87]. Contrasts can exceed100points because controls sometimes worsen an initially good program; absoluteMSE and fidelity counts show that the advantage is not merely attenuation or denominator scaling. All declared primary utility criteria pass. [PRIMARY_RESULT.json](PRIMARY_RESULT.json) contains every plant and frozen contrast; [primary_snapshots/](primary_snapshots/) preserves the 64-round evidence before extension.

The result also has a finite-budget residual accuracy gap. Learned35 retains mean normalized residual.02830 versus the oracle's.0000227; their paired residual gap is.02828[.01036,.05616]. All 12 learned35 trajectories contain at least one accepted step that improves circuit cost while worsening true loss. Those local conflicts coexist with substantial complete acquisition. Learned final gains range.846–1.281; there is no universal attenuation endpoint.

## Prespecified challenges

Longer tutoring provides a prespecified exposure sensitivity test of a simple monotonic account. Increasing35 to 140 renditions at unchanged learning settings reduces normalized improvement by 45.90points[12.20,95.60] and changes fidelity 12/12→4/12. Fixed gain improves learned35 by 2.13points[.40,4.70]. These are secondary comparisons without a familywise guarantee. Learned35 beats140 on 10/12 plants. The 140 mean is variable and includes a large failure; plant-level losses remain visible. This cannot establish structural failure of cancellation, asymptotic convergence, a biological exposure effect or numerical/ODE instability. [The primary source duration note](SOURCES_LONG_TUTORING_NOTE.md) states the source's actual training regime.

Doubling the primary search budget to 128 rounds/1281 slots leaves the oracle unchanged on all 12 plants and learned35 unchanged on 11. Plant103 makes seven further accepted reward improvements but its MSE rises.006359; ensemble mean MSE rises.000530, while normalized improvement changes97.1698%→97.1633%. This does not repair the residual gap under the declared search. It is not a global-convergence certificate. The64-round primary results and all paired contrasts remain numerically unchanged; [FINAL_RESULT.json](FINAL_RESULT.json) retains the extension separately.

The separate target-informed finite-scale diagnostic lowers circuit cost while moving away from the exact target in 12/12 learned35 cases (mean new MSE.01711 after a.05 program step), and 11/12 learned140 cases. These are actual evaluated wrong programs, not merely inferred gradient signs. All 12 primary learned35 endpoints also score below the exact target despite nonzero goal error. Useful teaching therefore coexists with a biased score. The 140 deficit mixes possible reward bias and search difficulty: two poor140 endpoints still score worse than the exact target, and the extra motor-budget test covers35, not140. A unique cause of the 140 loss is unresolved. See [DIAGNOSTIC_SUMMARY.json](DIAGNOSTIC_SUMMARY.json).

## Scientific control, provenance and verification

The first coordinate-only pilot failed a known-answer control: plant1's oracle and learned actor both reached gain 0, where every pure-shape proposal has identical output/cost. Strict descent cannot traverse that neutral plateau. We preserved that failed pilot and made one prevalidation target-blind global/local search revision. All three revised development oracles then recovered>99.99% of initial loss; no further actor or plant selection followed validation. [The deviation](protocols/DEVELOPMENT_REVISION.md), [exact gain-zero calculation](GAIN_ZERO_CONTROL.md) and [original pilot audit](COORDINATE_DEVELOPMENT_VERIFICATION.json) prevent mislabeling an optimizer trap as a teacher failure.

Independent reconstruction of all 12 primary tuples,72 arms,46,152 feedback slots, feature losses, seeded draw order and full search choices passed. Separately written dense equations also reproduce selected frozen circuit/burn/target scores. Source/protocol hashes remain unchanged. [PRIMARY_VERIFICATION.json](PRIMARY_VERIFICATION.json) records the checks and their limits. Final verification additionally reconstructs all extended choices, all 288 diagnostic losses/finite differences and 62 frozen dynamics probes, including the adaptively selected worst140 endpoint (plant 104). [VERIFICATION.json](VERIFICATION.json) records this postvalidation adversarial selection explicitly through its plant list. Fresh source training reproduces all four circuit states and both selected primary actor trajectories byte-exactly on plant 100; [the replay record](reproduction_plant100/REPRODUCTION.json) is software verification, not new validation. Training plasticity is the pinned source implementation, not an independent reimplementation. Held-out learning, reachable known answers and wrong-tutor/untutored controls provide the scientific evidence.

A fresh reviewer independently reconstructs all primary losses and paired bootstrap numbers without importing production analysis or the verifier. As an exploratory normalization challenge, the learned35 absolute-MSE advantages remain4.314[4.022,4.553] versus untutored and3.565[3.301,3.781] versus shuffled; it wins each paired comparison12/12. Excluding the worst140 plant 104 raises that arm's mean normalized improvement to72.52%, but leaves7 other fidelity failures; every leave-one-out35-minus140 mean advantage remains at least24.46points. This supports a heterogeneous exposure sensitivity, not a uniform collapse. [Adversarial review](audits/ADVERSARIAL_REVIEW.md), [independent primary numbers](audits/INDEPENDENT_PRIMARY_NUMBERS.json) and [independent final numbers](audits/INDEPENDENT_FINAL_NUMBERS.json) preserve these clearly exploratory stress checks.

## Relation to prior work and strongest objection

[Gong et al.](https://elifesciences.org/reviewed-preprints/111771) already demonstrates predictive cancellation, gain/error landscapes, memory/landscape interventions and simple reinforcement learning. Its inspected notebook derives a motor dictionary from adult target spectrograms and supplies timing. Our added result is the frozen quantitative teaching comparison across independently fixed, reachable whole plants with matched oracle/control budgets. Priority beyond the inspected sources remains unestablished. Generic proxy overoptimization also has established [prior work](https://proceedings.mlr.press/v202/gao23h.html).

The strongest surviving objection is the favorable assay itself: a known normalized target family, low-dimensional reachable motor programs, perfect context timing, deterministic resets and noiseless feedback. Those supports sharply limit the biological contribution.140's failure demonstrates a boundary of the fixed recipe; no tested count is an asymptotic-learning guarantee. The independent-plant result answers one computational question while leaving the natural encoder, motor plant and timing-learning problems open.

## Reproduction and investment

The owner decision is to **bank this positive, bounded computational result and stop this campaign**. A local cancellation rule can supply useful target-specific teaching without a tutor-derived motor basis in this independently drawn plant family. Its residual score bias and exposure sensitivity remain material. Another gain/optimizer/hyperparameter sweep would add less than a grounded encoder/motor/timing test; suitable biological measurements have not been established in this lab. Keep the prospective mouse result as the empirical anchor, and do not reopen protected data to improve a model. This is a stopping decision, not a successor queue or an audit assigned to the user.

No protected empirical observations were opened. All 20 strict external Pan-Vazquez prefixes/outcomes remain sealed; neither previous source gate passed and this synthetic study is not an external release condition. [Validation status](protocols/VALIDATION_STATUS.json) preserves exact exposure distinctions.

From the workspace root, reproduce the primary analysis and independent check:

```sh
campaigns/learning_rule_transport_2026-10-28/.modelenv/bin/python campaigns/evaluator_optimization_2026-10-28/analyze.py --plants 100 101 102 103 104 105 106 107 108 109 110 111 --rounds 64 --base-dir campaigns/evaluator_optimization_2026-10-28/primary_snapshots --output /tmp/evaluator-primary-reanalysis.json
campaigns/learning_rule_transport_2026-10-28/.modelenv/bin/python campaigns/evaluator_optimization_2026-10-28/verify.py --plants 100 101 102 103 104 105 106 107 108 109 110 111 --base-dir campaigns/evaluator_optimization_2026-10-28/mixed_results --search mixed --require-all-arms --required-rounds 64 --dynamics-plants 100 104 --diagnostics --output /tmp/evaluator-independent-check.json
```

Fresh-source replay into a **new, nonexistent** directory (change the output path if used before):

```sh
campaigns/learning_rule_transport_2026-10-28/.modelenv/bin/python campaigns/evaluator_optimization_2026-10-28/reproduce.py --output-dir /tmp/evaluator-fresh-replay --plants 100 --rounds 64 --arms oracle_joint learned35_joint --memoize --compare-authoritative
```

Use explicit100–111 IDs; development0–2 remains consumed. [Environment](ENVIRONMENT.json) pins the installed Python/NumPy/SciPy/Numba versions. Rendering uses root`.venv/bin/python plot.py`; the model environment has no Matplotlib. [PNG](figures/result.png) and [PDF](figures/result.pdf) were rendered and visually inspected. PanelA/C intervals are paired plant bootstraps; panelB/D bands are SEM. No new dependencies were installed; no accounts, paid compute, publication or external contact were used.
