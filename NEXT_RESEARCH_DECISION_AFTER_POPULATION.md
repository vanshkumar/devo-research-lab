# Test whether a learned evaluator remains a useful teacher under optimization

2026-10-28. Research-decision review following the completed prospective population campaign. This file selects the next scientific direction; no successor app thread or full campaign has been launched by this review.

## Decision and the result we keep

Close the current empirical RNN-repair program and preserve the external cohort. Promote a distinct controlled question: **Can a sensory evaluator learned from examples teach a target through an independently specified motor plant when the learner can change both output shape and gain?**

The latest empirical result is substantive. On 24 genuinely new source animals, frozen growth reduces mean-curve error from the RNN's 6.97 to 2.28 percentage points, an advantage of 4.69 points [95% paired animal interval 2.85, 5.67]. Individual CRPS also favors growth. The frozen prospective recipe did not establish useful population forecasting. The [completed report](campaigns/population_learning_transport_2026-10-28/REPORT.md) and its exposure record are authoritative.

Keep two qualifications. First, correctly centered source-like forecasts passed the conservative release gate only16.34% of the time. Gate failure alone is weak evidence of invalidity; the separate observed baseline loss is the stronger finding. Second, neither bias interval establishes an underlying error exceeding5 pp. The future-only0.8 session perturbation improves mean error to2.12 pp, but jointly shrinks behavioral coefficients and recurrent memory after a prefix calibrated under the original model. This postvalidation diagnostic demonstrates consequential session assumptions, not a biological retention estimate, coherent replacement rule or permission to open the external cohort.

I am not choosing another parameter repair as the next project. That would require independent evidence fixing a coherent transition/observation prescription before another empirical test. The retained benchmark already distinguishes conditional prediction, old-cohort average fit, prospective autonomous prediction and simulated policy effects. The eight completed campaigns should remain an accumulating record, rather than eight claims of success or eight reasons to continue their last failure mode.

## The alternative now has an actual failure witness

Our [first sensory-evaluator pilot](experiments/sensory_evaluator_preflight_2026-10-28/REPORT.md) runs the unchanged published600E/150I predictive-cancellation circuit on targets drawn after fixing the motor plant. Three local motor steps achieve64.7–81.4% of matched oracle improvement. That establishes execution feasibility, not full learning, robustness or a biological mechanism.

The prior pilot normalized every output, removing gain as a controllable axis. This review executed a [predeclared amplitude-axis test](experiments/sensory_evaluator_amplitude_preflight_2026-10-28/REPORT.md) on the same consumed synthetic plant and frozen circuit: four shape offsets by eight gains, with the same premotor clock. Gain multiplies signed auditory drive after normalization. It is a dimensionless model-input manipulation, not calibrated sound pressure. Gain zero means missing auditory feedback during an ongoing clock, not literal silence with all premotor activity off.

At the exact target, gain1 has the best mean circuit cost on the tested grid; simply asserting that silence wins would be false. Away from the target, however, optimizing circuit reward can worsen the target objective:

| Shape offset | Gain preferred by circuit | Circuit cost, gain1 → preferred | True feature error, gain1 → preferred | Best true-error gain on grid |
|---:|---:|---:|---:|---:|
|1|.5|2.0004 →1.8730 Hz|1.2740 →1.6370|.75|
|2|.25|2.6699 →2.0030 Hz|2.9205 →2.9801|.75|

For offset1, true error increases about28.5% even as circuit reward improves. We also computed the continuous true-error-optimal gain (.84075), so attenuation is not being called pathological merely because it changes amplitude: appropriate attenuation genuinely helps this wrong shape, but the circuit prefers too much. Exact repeated probes agree, independent feature/quadratic-loss reconstruction agrees within3.6e-15, and an independent dynamics reconstruction agrees within4.5e-16. No new empirical outcomes or circuit fitting were used. This is a one-plant local conflict, not evidence that a full actor must fail or that the circuit lacks a correct global optimum.

## The substantive experiment

**Hypothesis:** a sensory reward can respond correctly to passive deviations yet guide an optimizing learner into biased states; useful teaching depends on the interaction between evaluator geometry and the motor plant. Test whether this happens systematically and identify a specific constraint that predicts or prevents it, rather than collecting another favorable gradient demonstration.

1. Fix sensory encoders and motor plants independently of tutor targets; draw targets afterward from the known reachable set. Hold out whole plants and their target draws, not just more trials or contexts on the original eight-action map. Keep target-specific information in evaluator tutoring, with no tutor-fitted action dictionary or target-dependent actor initialization. The true-error oracle is an explicitly privileged positive control.
2. Run full fixed-budget learning with the learned scalar reward, a true-error oracle, and untutored/shuffled-reward controls. Match initial states, plant, exploration covariance, update rule and number of feedback queries. Set budgets and hyperparameters on development plants before held-out evaluation. Oracle failure means the assay cannot judge the teacher.
3. Give the actor joint control of shape and nonnegative bounded gain; compare with a fixed-gain arm under otherwise identical conditions. Initially keep context timing fixed so the gain test is interpretable. Then test noise and altered geometries as separate, prespecified generalization challenges. Physical vocal amplitude or natural song claims require a validated sensory/motor mapping, not relabeling signed neural-current gain.
4. Primary endpoint: true target loss after the frozen feedback budget, normalized to each plant's initial loss. Estimate paired differences and uncertainty over independent plants. Report oracle-relative improvement secondarily, with a declared handling rule when oracle gain is near zero. Count reward improvements that accompany target deterioration, residual target error, and learning trajectories; lowering the circuit's own rate is insufficient.
5. If failures appear, distinguish a biased reward from reachability, exploration and actor optimization. Test at most one mechanistically motivated generic constraint, selected on development plants and then frozen, against the same oracle and controls. Do not add target information to the actor, repair each held-out plant, or erase failure by normalizing the controllable axis away. A clean quantified limit can be the result; a successful teacher must generalize.

The nearest prior [Gong et al. study](https://elifesciences.org/reviewed-preprints/111771) already demonstrates local predictive cancellation, error landscapes and simple reinforcement learning. Its Figure5 already varies auditory-input gain and studies how the response minimum moves toward the tutor; our gain sweep is a feasibility/stress test, not a new scientific contribution by itself. The contribution cannot be "a learned critic can guide learning." Our inspected source also supplies a tutor-derived motor basis and timing scaffold. The sharper additional test concerns optimization through independently constructed reachable plants, controllable gain and the conditions for successful teaching. This is a bounded novelty assessment, not a claim of priority. Generic reward hacking by itself is also insufficient novelty.

The strongest failure hypothesis to test is that joint shape/gain optimization systematically produces poor tutor matching on untouched reachable plants even when the same learner succeeds with oracle reward. Distinguish optimizer stalling from convergence toward lower circuit cost with worse target fidelity. A correction must respect a declared information budget; giving the actor true tutor distance or target-amplitude information would conceal the bootstrapping question. Independent prior review supports this bounded whole-plant test conditionally, while judging a single bad gradient or a penalty that fixes one constructed example insufficient.

## Investment and stopping

The controlled direction warrants the next main campaign because it gives us known target geometry, direct interventions and repeatable failure/success controls, while addressing the broader question of how an internally learned evaluator becomes useful for action. The initial local results include both positive teaching and a verified misleading direction, making the next full-learning test informative in either direction.

Stop if the matched oracle cannot learn, an apparent effect reduces to reachability/exploration differences, or the result merely repeats existing cancellation/error-landscape demonstrations. Continue toward a scientific result only if the fixed protocol establishes substantial held-out learning or a reproducible failure mechanism with predictive consequences across plants. Do not claim a biological discovery from synthetic feature-space results. No additional empirical holdout is needed for this next controlled test; the20 protected mouse animals remain sealed.
