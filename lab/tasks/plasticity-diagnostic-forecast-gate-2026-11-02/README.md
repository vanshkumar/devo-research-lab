# Diagnostic acquisition-forecast gate

**Result: executable original-scale development forecasting, CLOSE this recipe without main.** Read [RESULT.md](RESULT.md), [CLOSE.md](CLOSE.md), [prior/information gate](PRIOR_INFORMATION_GATE.md), [plan](PILOT_PLAN.md) and [resources](RESOURCES.json).

The original SCR learner trains 1M updates before six next-task branches. Blind forecasts precede every future true-label copy and continuing acquisition. Only one teacher/learner is used; six branches are not six independent learners. A small score-specific point gain does not earn a useful capacity marker. All generated observations are consumed development.

Dependencies: system Python 3.9.6 standard library only, no installs or Torch. Original source is reused read-only from sibling `plasticity-retention-source-benchmark-2026-11-02/vendor/` and its SOURCE_MANIFEST.json, commit `3138c5556859e0e2918d40f113b40699b6575cfa`, MIT. `BLIND_FORECASTS.json.source` independently re-pins all 12 original blobs and SHA256. The source-equation implementation is independent Python float64/RNG; it does not execute author Torch code or claim its exact seeded trajectory. Primary source license/access notes and exact URLs are in PRIOR_INFORMATION_GATE.md and PUBLIC_OPERATIONS.json; the complete saved tool-rendered response bundle is PUBLIC_SOURCE_RESPONSES.json (not original PDF byte certification).

Exact commands from repo root, **only in a separately authorized reproduction with preserved old outputs**:

```sh
python3 -B lab/tasks/plasticity-diagnostic-forecast-gate-2026-11-02/pilot.py prepare
python3 -B lab/tasks/plasticity-diagnostic-forecast-gate-2026-11-02/pilot.py direct
python3 -B lab/tasks/plasticity-diagnostic-forecast-gate-2026-11-02/pilot.py acquire
python3 -B lab/tasks/plasticity-diagnostic-forecast-gate-2026-11-02/audit.py
```

The saved phases are already complete; this close does not authorize another run. `prepare` fixes and writes blind forecasts before persisting scorer continuation. `direct` reads them and buys exactly 2,000 task-labelled copy updates plus the 32-point support score; it never changes the continuing state. `acquire` verifies forecast hashes and only then trains all six continuing branches. `audit` replays diagnostic features/forecasts and independent arithmetic checks without refitting or obtaining new evaluation states. `SCORER_CONTINUATION.json` stores all generated teacher/context/draw/target information and is consumed scorer material, not predictor input.

Scientific process was sequential, native Python thread only. Resource estimates do not certify provider/runtime/physical I/O. [Manifest](REPRODUCTION_MANIFEST.json) pins the saved files; [proposed learning](PROPOSED_LEARNING.md) awaits PI integration. This endpoint does not stop the lab or complete its scientific native goal.
