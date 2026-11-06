# V1 — finite sandbox tests and proxy magnitude

Decision: **retire as a research lead; retain a runnable evaluation example**. This is one analytical/computational pilot with a small exploratory adversarial check, not a test of a trained AI or brain-like agent.

`run.py` enumerates66 nonnegative integer utility vectors (welfare, pleasure, approval), summing to10, over27 feature vectors in{−1,0,1}³ and all351 unordered action pairs. Ties choose the first action. All66 choose the helpful action on an aligned three-action training menu. Across the full test set,56 sacrifice strictly positive welfare in at least one context. A greedy cover finds a single diagnostic menu catching all56;10 vectors pass. An independently implemented maximum-welfare check verifies those10 on all351 menus. Tied welfare preferences do not count as harm.

This apparently complete test is complete only within its fixed domain. After seeing that result, `followup.py` tests an explicitly exploratory magnitude shift: choose between[1,0,0] and[0,m,m]. Nine of10 passing vectors sacrifice welfare at m=3,5 or10; pure welfare never does. Exact inequality w>2(p+a) independently identifies the original passing set. For every passing proxy mixture, its first strict shifted failure equals floor(w/(p+a))+1. No randomness or numerical tolerance is involved.

The result changes the proposed sandbox specification: coverage must state its policy family, observation access and feature magnitudes. It does not show that values are observable in general, that a deceptive policy passes or fails, or that a finite battery validates AGI safety. Existing reward/specification and goal-misgeneralization work already establishes the broad issue; this simple result is not claimed novel.

Original plan mentioned MDPs/three-action menus, but the executed diagnostic is a static two-action exhaustive utility calculation (with one three-action training menu); there are no dynamics, learned observations, or held-out agents. The finite list is exhaustively evaluated, so no population p-value is warranted.

From repository root:
```sh
.venv/bin/python campaigns/byrnes_todo_2026-10-28/experiments/sandbox/run.py
.venv/bin/python campaigns/byrnes_todo_2026-10-28/experiments/sandbox/followup.py
```
