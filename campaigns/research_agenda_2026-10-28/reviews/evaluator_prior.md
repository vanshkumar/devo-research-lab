# Independent assessment: sensory evaluator as teacher

2026-10-28. Bounded review by `evaluator_prior`. Read the full lab learnings and charter, both completed sensory preflight reports, the pinned source audit, upstream `src/RL.py` and the dictionary-generation notebook. Browsed primary papers below. No numerical experiment, old-file modification or protected-data access was performed.

## Judgment

The direction merits **one bounded discriminating learning experiment**, conditional on the other portfolio reviews revealing no stronger executable opportunity. Its strongest potential contribution is a quantitative condition for successful learning from a locally acquired internal evaluator through an independently specified motor plant. A failure witness, gain grid, or generic observation that reward optimization can become misdirected is insufficient.

The completed preflights support execution feasibility and include both beneficial local updates and a misleading gain preference. They do not establish full-learning success or failure. The decisive scientific upgrade is therefore complete learning with a known reachable target and a successful matched oracle, followed by an intervention discriminating persistent evaluator bias from insufficient motor optimization or insufficient tutoring. The conclusion should concern this specified circuit and plant ensemble, without translating signed input gain into acoustic amplitude or a natural-vocal claim.

## What nearest prior work already establishes

| Primary evidence inspected | Implication for this campaign |
|---|---|
| [Gong et al., reviewed preprint v1, 2026](https://elifesciences.org/reviewed-preprints/111771), Fig. 5 and Results “Population error codes exhibit two-stage learning”; Fig. 6 and Fig. S12 | Already studies gain along correct-song/no-feedback interpolation, off-manifold perturbations, response minima, connectivity-mode interventions, and downstream scalar-reward learning. Perturbing modes already impairs learning. The authors explicitly raise incomplete convergence at their fixed learning step as one explanation for residual landscape imperfections. |
| [Pinned Gong code](https://github.com/gongziyida/vocal-error-network/tree/8309db5b1e2abb0d937fec7a1f9d434b06a9bd7c), `src/RL.py`, `further_analysis/RL_syl_generation.ipynb` | The inspected notebook fits the motor dictionary to adult target spectrogram data. The environment normalizes sparse embeddings and supplies syllable timing; its policy receives only scalar mean-rate feedback. These are explicit simplifications, rather than evidence that the paper's sufficiency result is invalid. |
| [Fiete, Fee & Seung, 2007](https://journals.physiology.org/doi/full/10.1152/jn.01311.2006), abstract and actor/critic discussion | Biologically motivated perturbation-based motor learning driven by an internal tutor-comparison critic predates this study. The special question is how that critic becomes useful through learning, not whether internal reward can guide trial-and-error behavior. |
| [Gao, Schulman & Hilton, ICML 2023](https://proceedings.mlr.press/v202/gao23h.html), abstract/introduction | Systematically measures true-objective degradation under optimization of a learned proxy, using a synthetic gold reward and matched optimization. Merely reproducing this phenomenon in another network is a weak novelty claim. |
| [Skalse et al., 2022, revised 2025](https://arxiv.org/abs/2209.13085v2), abstract/formal scope | Formalizes conflicts between improving proxy reward and improving true reward. Its broad policy-space result does not imply that this particular constrained motor plant must fail, so an actual learning experiment remains necessary. |

These inspected sources do not establish absence of the proposed plant benchmark elsewhere. Priority remains unestablished. The source-specific contribution would be a held-out quantitative answer about useful teaching and its limits, rather than a general new reward-hacking theorem.

## Sharpest discrimination

**Primary hypothesis:** with a motor plant fixed before drawing reachable targets, the frozen learned cancellation reward yields substantially less true target improvement under joint shape/gain control than the matched oracle; the deficit persists when motor optimization has adequate budget.

**Endpoint:** terminal true feature loss divided by initial loss, paired across whole independent plants, with identical initialization, exploration draws and feedback-query budgets. Report the complete trajectories as well. The oracle is privileged by design; untutored and target-shuffled evaluators establish whether tutor-specific learning supplies the benefit. A fixed-gain arm diagnoses the extra control axis but removes part of the joint task, so it is not itself a task-preserving repair.

**Strongest competing explanation:** the actor is underoptimized, or 35 tutor exposures leave a transiently inaccurate reward. A useful limited sequence is:

1. On development plants, ensure the oracle learns with the selected search/update rule and budget; freeze the actor settings, target/action distributions, plant family and endpoints before held-out plants.
2. Compare learned, oracle, untutored and shuffled-teaching conditions on entire held-out plants. Keep the same scalar-feedback access and common random exploration draws. Count feedback queries, including rejected steps or line searches. Do not reuse target gradient or target-selected initialization for the actual learned-reward actor.
3. If learned-reward actors plateau while the oracle succeeds, examine one **declared longer motor budget**. Stalling with remaining downhill circuit directions is an optimizer limit. Continued lower circuit cost with higher true error is evidence of a reward conflict along actual learning trajectories. Neither endpoint alone establishes convergence.
4. Test **longer tutoring**, preferably 35 versus a declared several-fold increase at unchanged learning rules, on a fresh development sample or as an explicitly secondary held-out intervention. If the teaching deficit disappears, report a tutoring/optimization interaction rather than a structural impossibility. Do not tune a tutoring count on held-out target losses and relabel the replacement frozen.
5. Use exact-target starts only as a separate diagnostic: finite-difference circuit descent at the exact reachable target should be stationary under a perfectly aligned teacher. If it drifts reproducibly, compare its direction to the bias reached from ordinary starts. This identifies a target-local reward defect but is not an independent novel theorem or proof of a basin-wide trap. The exact target must not initialize the primary learner.

A stronger mechanistic result would predict which plants fail from an independently measured property of the learned evaluator, such as the target-local reward gradient projected into the plant's reachable tangent directions. That prediction must be frozen on development plants and tested on held-out plants. A merely retrospective correlation is exploratory.

## Target information and validity constraints

- Motor plant, encoder, timing, action bounds and initial action distribution are fixed before target draw. Targets are generated from the reachable set after fixing the plant, then shown only to evaluator tutoring. Keep any shared timing scaffold explicit.
- Oracle computation and true loss evaluation remain outside the learned actor. An amplitude penalty calibrated from the true tutor norm or distance would add target information; it cannot silently count as an intrinsic generic repair.
- Whole plant/circuit/target draws are the replication units. Repeated queries, contexts within a song and actor restarts do not create additional independent plants.
- Retain gain as a signed auditory-drive manipulation. A physical acoustic claim would require a validated encoder and plant mapping, beyond this bounded study.
- Normalization, zero circuit noise and supplied timing make a favorable mechanism assay. Failure can establish a limit in that assay; success remains conditional on those supports.

## Investment and stop decision

Invest in the bounded matched-learning test because it can turn a speculative reward conflict into an inspectable computational result. Do not start a broad architecture/penalty sweep. Stop if the oracle cannot learn, the apparent deficit disappears when query access is matched, or the finding remains only a restatement of a known bad proxy direction. If full held-out trajectories reveal a material deficit, spend the next bounded increment on **longer tutoring versus longer motor optimization**, since these interventions separate the strongest alternatives without secretly giving the actor the tutor. A reproducible, quantified boundary on useful teaching is sufficient for a completed result; a universal failure or biological mechanism is not warranted.

Suggested project-specific learning for the lead to add if adopted: Gong's own discussion makes finite tutoring a concrete alternative to structural evaluator bias; a failure at 35 tutor exposures should be challenged with longer tutoring before a mechanistic conclusion. This is more specific than the existing gain-conflict entry.
