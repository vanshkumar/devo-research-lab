# Frozen attribution comparison

Freeze before any new ablation execution. This is a postvalidation diagnostic on consumed synthetic controls, not a new validation set or human calibration.

The sole changed component is the learned role's applied reliability: override `Learner.weight` to return exactly 1 on every edge from the first observation. Retain its constant-context-per-story posterior, posterior averaging before the temperature-4 response softmax, published Simulation2 parameters, initial counts/priors, hard end-story assignment and unit count updates. Rerun every prediction, assignment and count online from zero; never reuse learned states for the ablation. Diagnostic reliability may be computed from each role's own past counts without applying it in the ablation.

Use seeds27001–27020, families original/relocated/deterministic, curricula blocked/interleaved/early/late, 200stories each. Early-minus-late is the single mixed-curriculum contrast. Generate the exact saved inputs and their seed+908172 state permutations; compare full-role probabilities, weights and assignments byte-for-byte with frozen saved outputs before interpreting the ablation. No middle curriculum, additional family, seed, fitting, readout repair or new primary model.

Primary paired effect: full minus reliability-one mean correct-choice probability on deterministic non-cue edges in stories161–200, in percentage points. Independently reconstruct labels/masks and probability/log-loss scores. Report each family/curriculum, not a pooled cross-family outcome. Use seed-paired bootstrap95% intervals, 10000resamples with RNG77201, across the20already-consumed seeds. These quantify generator Monte Carlo variability only; do not infer human uncertainty, equivalence or causal necessity.

Secondary: first five return stories81–85 and full return block81–120 in blocked training; label these indices without return interpretation for other curricula. Report stepwise probabilities, applied and estimated reliability, schema count/purity and changed story partitions. Test exact state-permutation behavior and original/oracle semantics. The source-faithful oracle is an advantaged local-MAP model, not a perfect-performance bound.

Audit pre-observation ordering, completed-story-only reliability/counts, evaluator-label independence, no-update predictions, future-suffix invariance and original-byte/source pins. Use visibly bounded stories and two-candidate options as declared ordinary observations, not privileged context/noise labels. Preserve failures. Source availability assessment is limited to the existing SOURCE_REPORT; no human header, response, archive or new lookup.

Resource limit: one process, 2GB, at most300s total simulation/audit execution; finish by21:17:50UTC. Save separate audit/ablation outputs and original hashes. Do not execute source utils.py, which contains a network request at import.
