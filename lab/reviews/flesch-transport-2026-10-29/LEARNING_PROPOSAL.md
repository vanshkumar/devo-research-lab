**2026-10-29 — Flesch model transport requires the full published prescription**
- Observation: The publication-linked 2023 repository at b23abb9fb8aacb03cc7b51ad96d7fb97c18301b2 is available. Its human-comparison blob runner uses different blocked/interleaved context scaling as well as learning rates; the generators smooth training cues only, and Pandas EMA alpha weights the current cue, not carryover. The all-input and context-only Oja paths are distinct implementations.
- Action: Before this lab tests shared-parameter B200/Interleaved-to-B2/B20 transport, freeze context scaling, Oja path, phase-specific cue handling, centering/initial-context encoding and noise together with the learning rates. Reuse the pinned review code and source-only calibration; sharing rates alone does not test a shared learning prescription.
- Confidence: high

Proposed for PI integration after rereading the current relevant LEARNINGS section. The reviewer owns only this review directory; shared root files were not edited.
