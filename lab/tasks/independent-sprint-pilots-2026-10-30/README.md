# Independent research pilots,2026-10-30

Read `RESULT.md` for the earned result and `STATE.md` for completion/jobs. The initial protocol is `PLAN.md`; failed-control and reference amendments are preserved separately. This folder is an exploratory evidence block using consumed biological/synthetic inputs. It is not independent validation or a new biological experiment.

## Runtime

Run from `/Users/vanshkumar/Documents/repos/devo-research-lab`. The existing numerical environment is `campaigns/learning_rule_transport_2026-10-28/.modelenv/bin/python`: Python3.12.14, NumPy2.3.5, SciPy1.18.1, Numba0.68.1. No installation is required. Scripts set BLAS/OpenMP thread limits to2, direct Numba caches to this task and suppress bytecode outside it. Run one command/process at a time. Literal35-rendition source tutoring is retained; the long140-rendition experiment is not repeated.

The separate existing `.venv/bin/python` can render the final plot from saved outputs; it is not used for scientific fitting. The numerical scripts charge scientific reads in `READS.json` before access. Replaying the entire block again counts additional reads; do not reset that ledger to evade its1GB budget. Cached generated states are reused. Exact older source/data assets and license qualifications are in `SOURCES.md`.

## Reproduction

These are separate sequential commands, all from the repository root:

```sh
campaigns/learning_rule_transport_2026-10-28/.modelenv/bin/python lab/tasks/independent-sprint-pilots-2026-10-30/inspect_sources.py
campaigns/learning_rule_transport_2026-10-28/.modelenv/bin/python lab/tasks/independent-sprint-pilots-2026-10-30/worm_pilot.py --stage controls
campaigns/learning_rule_transport_2026-10-28/.modelenv/bin/python lab/tasks/independent-sprint-pilots-2026-10-30/worm_pilot.py --stage main
campaigns/learning_rule_transport_2026-10-28/.modelenv/bin/python lab/tasks/independent-sprint-pilots-2026-10-30/worm_pilot.py --stage shifts
campaigns/learning_rule_transport_2026-10-28/.modelenv/bin/python lab/tasks/independent-sprint-pilots-2026-10-30/worm_followup.py
campaigns/learning_rule_transport_2026-10-28/.modelenv/bin/python lab/tasks/independent-sprint-pilots-2026-10-30/run_teaching_batch.py
campaigns/learning_rule_transport_2026-10-28/.modelenv/bin/python lab/tasks/independent-sprint-pilots-2026-10-30/teaching_followup.py --plant 100 --noise-repeats 20
campaigns/learning_rule_transport_2026-10-28/.modelenv/bin/python lab/tasks/independent-sprint-pilots-2026-10-30/teaching_followup.py --plant 101 --noise-repeats 20
campaigns/learning_rule_transport_2026-10-28/.modelenv/bin/python lab/tasks/independent-sprint-pilots-2026-10-30/teaching_followup.py --plant 102 --noise-repeats 20
campaigns/learning_rule_transport_2026-10-28/.modelenv/bin/python lab/tasks/independent-sprint-pilots-2026-10-30/untutored_control.py --plant 100
campaigns/learning_rule_transport_2026-10-28/.modelenv/bin/python lab/tasks/independent-sprint-pilots-2026-10-30/untutored_control.py --plant 102
campaigns/learning_rule_transport_2026-10-28/.modelenv/bin/python lab/tasks/independent-sprint-pilots-2026-10-30/duration_tail_check.py
campaigns/learning_rule_transport_2026-10-28/.modelenv/bin/python lab/tasks/independent-sprint-pilots-2026-10-30/verify_results.py
.venv/bin/python lab/tasks/independent-sprint-pilots-2026-10-30/plot_results.py
campaigns/learning_rule_transport_2026-10-28/.modelenv/bin/python lab/tasks/independent-sprint-pilots-2026-10-30/make_manifest.py
```

`run_teaching_batch.py` first checks all3 privileged true-loss oracles, then executes source-reference diagnostics and the matched1206-query per-order actor for each plant. Its four critic arms are clocked, fixed-clock/unregistered onset, onset-reset retaining a known relative template, and re-trained zero-HVC. Each uncached scalar query uses two deterministic source probes. Exact duplicate probes are memoized, while every logical feedback slot is counted. The original321-query coupled actor/control failure is preserved in `teaching_failed_v1.py` and `outputs/teaching_learning_100_20.json`; do not mix that actor's results with the revised main comparison.

`teaching_followup.py` retrains reversed-tutor and tonic-drive controls, scores64 predeclared distinct permutations, completes a duration-only learning task, and measures explicit hypothetical readout/source-noise sensitivities. It does not train a noisy actor or learn a new general alignment mechanism. Source-noise trials use a separate seeded frozen Euler integrator that must match the unchanged source at zero noise. Failure aborts that run before noise interpretation.

`untutored_control.py` challenges attribution on the two successful no-clock main cases. These controls are selected after the main outcomes and are explicitly falsification checks, not a population tutoring-effect estimate. `duration_tail_check.py` adds a common700ms quiet suffix to initial/final/target duration probes and reproduces the saved original prefixes; it tests a finite readout-window alternative. Neither is a new validation cohort.

## Inspectable artifacts

- `outputs/worm_main.csv`: neuron-local and population methods at four horizons in six discovery animals. `worm_reference.json` retains the exact older current-only comparison.
- `outputs/worm_controls.csv`: five shared-rotation, five independentAR and five independentAR2 generated controls. `worm_shifts.csv` contains3 channel-shift controls per animal; these are dependent diagnostics, not18 additional animals.
- `outputs/worm_followup.json`: middle-window-selected local/population families, common-origin finite history ladder, independent direct linear-solve check.
- `outputs/teaching_learning_{plant}_per_order_20.json`: learning endpoints and actual source-query counts. The corresponding NPZ files contain every query action/cost and full accepted trajectory, plus true losses scored offline.
- `outputs/teaching_followup_{plant}.json`: tutor specificity, broader order choices, duration trajectories, readout-noise choices and seeded current-noise summaries. `teaching_source_noise_{plant}.npz` retains trialwise costs.
- `outputs/VERIFICATION.json`: separate loss reconstruction, scalar-feedback replay, corrected reference and admitted-input checks. These are author checks; they do not replace the PI's independent scientific review.
- `outputs/untutored_control_{plant}.json`: full matched zero-HVC searches without tutor exposure. `outputs/duration_tail_check.json`: original-prefix and extended-window duration comparisons.
- `MANIFEST.json`: exact admitted synthetic/input and owned-output hashes, original worm Git-blob pins and cumulative input-read accounting. `STATE.md` and `READS.json` remain mutable coordination/accounting records and are excluded from their own hash collection.
- `DECISIONS.md`: belief/allocation changes and preserved failed controls. `SOURCES.md`: exact prior/access qualifications. `PROPOSED_LEARNING.md`: a proposal for PI integration, without concurrent root memory edits.

The preferred scientific question remains explicit in `RESULT.md`; source reproducibility and scientific payoff are assessed separately. Protected memory/Pan/Flesch/HABITS and reserved worm observations stay closed.

Plant100's first follow-up calculation failed only at export because order lists contained NumPy integers. Preserve `FOLLOWUP_EXPORT_FAILURE.md`, its original code and failed-at-export noise NPZ. The serialization-only rerun uses unchanged seeds/cached circuits; the verifier compares those actual noise arrays. This failure is not erased or used as result selection.
