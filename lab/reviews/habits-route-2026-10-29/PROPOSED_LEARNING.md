# Proposed shared learning — for PI integration

The reviewer owns only this review directory. The PI should reread the current relevant LEARNINGS section and integrate this specific entry once, preserving concurrent additions.

**2026-10-29 — HABITS live and cached teacher state**
- Observation: The publication-pinned MT firmware copies live model state to actionmodel only every second accepted response; startup resets the cache and its compiled S0[1]=+.5 differs from the paper/configuration's -.5. With a synthetic admissible t=100 state, extracted source functions select (3,1) with preserved cache versus (2,0) with boot-default cache; an independent score reduction agrees. This does not show a reset occurred or affect a biological forecast. Later code phases also randomize delay and retain adaptive direction selection, beyond the simple testing policy described in Methods.
- Action: For this HABITS route, replay live/cache state, reload precision and protocol timing explicitly; carry bounded Methods/code deployment alternatives before any future forecast. Do not treat a teacher replay or one changed synthetic selection as evidence for a transferable animal learning rule.
- Confidence: high
