# Independent missing-practice review

Read [REVIEW.md](REVIEW.md). The main conditional result survives independent reconstruction; primary K4 fails the frozen 0.10 criterion. The new prespecified contrary test finds that nearest-0.05 return scores fail even the favorable K1 design (attained gap 0.114335787).

The reviewer is distinct from the author. This is a Python standard-library calculation; no external packages, randomness, network, empirical data, author-code execution, subprocesses, or numerical worker threads. The author bundle is read-only. Python/platform details are recorded in AUDIT.json.

Artifacts:

- `independent_review.py`: independent event simulator, count sets, polynomial/root extrema, score-coarsening calculation, directional intervention and coupled calibration audit.
- `FIRST_CALCULATION.json`: early independent same-observation event execution.
- `INDEPENDENT_BOUNDS.json`: all count/target bounds, maximizing source/target witnesses, 80-digit values and observation-grid checks.
- `CONTRARY_PLAN.md`, `CONTRARY.json`: frozen nearest-0.05 observation test and actual output; `CONTRARY_INITIAL.json` preserves its initial boundary-witness implementation.
- `AUDIT.json`: freeze/artifact checks, independent comparisons, calibration/directional/threshold controls, measured process peak and input bytes.
- `RESOURCES.json`, `STATE.md`, `LEARNING_PROPOSAL.md`: accounting, completion status and scoped shared-memory proposal. No shared files were edited.

To reproduce into a fresh owned directory without replacing the saved evidence, run these commands separately from the repository root. The final positional argument selects the output directory; omit it only if deliberately replacing generated review outputs. The original code reads its original frozen plan, and audit reads only the named author bundle and newly generated outputs.

```sh
mkdir /Users/vanshkumar/Documents/repos/devo-research-lab/lab/reviews/missing-practice-transport-2026-11-01/reproduction-01
python3 /Users/vanshkumar/Documents/repos/devo-research-lab/lab/reviews/missing-practice-transport-2026-11-01/independent_review.py first /Users/vanshkumar/Documents/repos/devo-research-lab/lab/reviews/missing-practice-transport-2026-11-01/reproduction-01
python3 /Users/vanshkumar/Documents/repos/devo-research-lab/lab/reviews/missing-practice-transport-2026-11-01/independent_review.py main /Users/vanshkumar/Documents/repos/devo-research-lab/lab/reviews/missing-practice-transport-2026-11-01/reproduction-01
python3 /Users/vanshkumar/Documents/repos/devo-research-lab/lab/reviews/missing-practice-transport-2026-11-01/independent_review.py contrary /Users/vanshkumar/Documents/repos/devo-research-lab/lab/reviews/missing-practice-transport-2026-11-01/reproduction-01
python3 /Users/vanshkumar/Documents/repos/devo-research-lab/lab/reviews/missing-practice-transport-2026-11-01/independent_review.py audit /Users/vanshkumar/Documents/repos/devo-research-lab/lab/reviews/missing-practice-transport-2026-11-01/reproduction-01
```

Compare numerical values with ordinary floating tolerance (1e-12 is ample); timestamps, input-read sizes for the regenerated audit and native RSS can differ. The initial contrary snapshot is historical evidence of the original review's correction, not an expected fresh-run output. No formal interval or certified-root claim is made. Source identifiers/exposure are inherited only from the pinned author's SOURCES.json; the review makes no new source/licensing/novelty claim.
