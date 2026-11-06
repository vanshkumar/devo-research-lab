# Exact driven-state stability test

This task tests whether the exact review-generated finite-pulse2019circuit candidate is a switch between locally attracting regimes or only a difference in relaxation times. See [PROTOCOL.md](PROTOCOL.md), its actual [FREEZE.json](FREEZE.json), [REFERENCE.json](REFERENCE.json), and final RESULT.md/STABILITY_RESULT.json when saved. Original20–22spulse, commonPLM.2+ASK.24background, two fixed source seeds and all279neurons/558states are unchanged. The only new horizon is the predeclared300scontinuation, followed by the same2schallenge. No empirical/protected observations are used.

The investigator is the author of this follow-up. It reuses and attributes the prior review's `lab/reviews/interactome-transient-reachability-2026-11-03/independent_model.py` (actual resolved path/pin in REFERENCE/FREEZE), while independently assembling sparse Jacobians, source/scalar comparisons and complete558x558periodic variational calculations. Numerical cross-checks inside this study do not replace a fresh distinct independent reviewer of its claim.

## Reproduce

Use the repository's EXISTING `.venv/bin/python` (Python3.9.6/NumPy2.0.2/SciPy as recorded in final manifest), no install. Run the stability replay in a separate copy/checkout, retaining the ORIGINALsix frozen files, to preserve original saved observations:

```sh
.venv/bin/python lab/tasks/interactome-retained-state-stability-2026-11-03/stability.py
```

For a separate original-source verification run `.venv/bin/python lab/tasks/interactome-retained-state-stability-2026-11-03/reference.py` in another verification copy. Its original timestamp/ZIPheaders are pinned, so rerunning reference.py in the stability replay copy intentionally changes the frozen bytes and the guard then rejects. `freeze.py` is the actual historical receipt creator, not a command to run again or a way to claim a new pre-evaluation freeze. The stability job itself verifies those pins, fixes numericalthread environment to1 and stops after1080s rather than extending the original20minscienceprocess allocation.

`reference.py` compares the full pinned2019source equations with explicit scalar and inherited sparse expressions at the exact admitted42sstates; it also executes the original54step FWD sourceVODE/sparseRadau reference. `stability.py` saves complete long/challenge trajectories, section crossings, one root per finite history, one bounded same-start periodic shooting attempt, fullmonodromy matrices/multipliers at512/1024/2048steps, independentBDFtangent checks and two central-difference sourceflow trajectories. All outputs are consumed development, not replacement validation.

Exact original source/assets, names, presets and BSD3license remain in the two predecessor task paths, with pins/license qualifications in their SOURCE_MANIFEST and this task's final manifest. Do not execute the release's Flask/eventlet/UI imports; only the six already pinned mathematical source functions are AST-extracted as comparators. Source `.npy` Python2header warnings are preserved. Backend/source-voltage conventions are literal and not a calibrated physical locomotion/fluorescence mapping. This2019beta is not exact2017.

Known2017drivenmultistability and longtransients are closest prior. A positive can establish a conditional source-specific finite-accessibility prediction with numerical local stability, not priority for bistability, rigorous global permanence, biological memory or completion of the native lab mission. A negative closes only this exact consumed candidate. Full prior raw/summary exposure, failures and resource uncertainty survive; same operator goal/heartbeat remain unchanged.
