# Motor-assay measurement decision

Read [RESULT.md](RESULT.md), then [RIVALS_AND_ASSUMPTIONS.md](RIVALS_AND_ASSUMPTIONS.md) and [SOURCES.md](SOURCES.md). Author closes the proposed collection recommendation: accurate external offset calibration and randomized forced-choice probes can coexist with a small event-by-precursor reporting criterion that hides either signed .2-degree transition contribution. Storage additionally lacks an independently calibrated observation loading. This does not assert an empirical bias or universal impossibility.

Reproduce from `/Users/vanshkumar/Documents/repos/devo-research-lab`:

```sh
python3 lab/tasks/motor-assay-identification-2026-11-02/first_calculation.py
python3 lab/tasks/motor-assay-identification-2026-11-02/calibration_frontier.py
python3 lab/tasks/motor-assay-identification-2026-11-02/final_audit.py
```

Python standard library only, tested Python 3.9.6 on macOS arm64. No dependency installation, empirical input or network is used by these commands. They overwrite this task's generated JSON; timestamps and hashes of timestamped output will change. Expected scientific values: exact residual zero, original scalar .2, centered signed targets [-.2,.2], report-as-true estimates [-.1,.1], critical per-cell bias .26545670453072434 and zero 2AFC/quantizer mismatches. Seed 483291; exact proof uses Fraction, with a separate normal-equation/scalar check and a coupled float observation-law diagnostic. Do not describe the latter as empirical power or heterogeneous-parameter recovery.

`FINAL_AUDIT.json` pins the saved calculation code/outputs, calibration gate, mathematics and source manifest. `RESOURCES.json` preserves limits, failures, exposure and unknown accounting; `PROPOSED_LEARNING.md` is for PI integration. Shared lab files and native goals were not edited. A fresh distinct reviewer remains required for a consequential lab claim.
