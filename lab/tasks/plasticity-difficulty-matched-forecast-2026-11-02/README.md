# Paired-state same-task forecast development pilot

Read [RESULT.md](RESULT.md), [CLOSE.md](CLOSE.md), [PILOT_PLAN.md](PILOT_PLAN.md), [PRIOR_INFORMATION_GATE.md](PRIOR_INFORMATION_GATE.md), [AUDIT.json](AUDIT.json) and [RESOURCES.json](RESOURCES.json). Decision: CLOSE/no main/no retuning. Four teacher/history independent units, eight original1M-update learners, then paired10k same-task acquisitions.

The saved artifacts are the evidence. Reproduction is listed for an independently authorized reader; this CLOSE authorizes no new run. From repository root, standard-library Python only, phases in this exact order:

```sh
python3 lab/tasks/plasticity-difficulty-matched-forecast-2026-11-02/paired.py prepare
python3 lab/tasks/plasticity-difficulty-matched-forecast-2026-11-02/inspect_blind.py
python3 lab/tasks/plasticity-difficulty-matched-forecast-2026-11-02/paired.py direct
python3 lab/tasks/plasticity-difficulty-matched-forecast-2026-11-02/paired.py acquire
python3 lab/tasks/plasticity-difficulty-matched-forecast-2026-11-02/audit.py
```

`paired.py` imports ONLY equation/helper definitions from the preceding task's `pilot.py`; it loads no old numerical state/data/calibration. The helper pin and all original source blob/SHA256 pins are in BLIND_FORECASTS. Original shibhansh/loss-of-plasticity commit3138c5556859e0e2918d40f113b40699b6575cfa/root803541478812c901d267bd5acd069be20fb824f9 uses MIT; original license and cached source are at `lab/tasks/plasticity-retention-source-benchmark-2026-11-02/vendor/`. Source-equation float64/Python RNG differs from author Torch. No dependencies installed or downloads needed for numerical reproduction.

BLIND_FORECASTS contains fitted past-only predictors, all ten assay measurements and future target-blind forecasts. CALIBRATION contains36 preceding paired calibration cases. SCORER_CONTINUATION contains new synthetic teachers/context recipes, initial/mature learner states/full100-task summaries, input-sequence hashes and future/unused-extra input draws. It is scorer-only with respect to the forecasting interface, and development-exposed scientific evidence, not a protected empirical archive. DIRECT_FORECASTS contains privileged labelled-copy predictions; ACQUISITION_OUTPUT contains actual future outcomes/all80k scalar references. BLIND_NONDEGENERACY records the15-minute gate. AUDIT reconstructs frozen fits/scores/costs. REPRODUCTION_MANIFEST pins saved scientific artifacts; its hashes provide consistency, not independent chronology certification.

All four public operations/one followed program and provider-byte/license limitations are recorded in PUBLIC_OPERATIONS/RESOURCES and the prior gate. No distinct independent review, population uncertainty, main claim or biological inference is earned. Proposed memory is scoped in PROPOSED_LEARNING for PI integration; workers do not edit shared LEARNINGS.
