# Independent transition and bounded-reader review

2026-10-29. **PASS for the reviewed implementation.** This verifies the new session-transition prescription and its bounded source reuse, not scientific readiness or transport. The persistent question is whether dynamics inferred under source training can forecast acquisition after1000 opportunities for the next3000 under a different trainer, generating actions/omissions/feedback and materially beating growth. All source observations here are consumed development evidence; historical failed gates remain failed; Pan20 prefixes/outcomes remain sealed.

The executable record is [independent_transition_check.py](independent_transition_check.py); numerical results, reviewed code/design hashes and old-ledger hashes are in [INDEPENDENT_TRANSITION_CHECK.json](INDEPENDENT_TRANSITION_CHECK.json). Run from the repository root:

```sh
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 campaigns/learning_rule_transport_2026-10-28/.modelenv/bin/python campaigns/learning_transport_revised_2026-10-29/audits/independent_transition_check.py
```

## Evidence

- An independent scalar NumPy implementation reconstructs the GRU and coefficient recurrence without calling production `sequence` or `update`. Across1081 synthetic opportunities and rho=.5,.7,.9,1, probabilities/coefficient/memory states agree within8.89e-16.
- Continuous histories and split continuations agree exactly at five boundary/nonboundary cuts for every rho. A new history's initial start flag does not attenuate its initialization; a continuation at a genuine boundary does. An omitted first opportunity receives the pretrial transition, while its post-response update leaves both states unchanged.
- Deliberately applying the transition twice changes predicted probabilities by6.05–10.58pp. Delaying it until after prediction changes the omitted boundary's probability by1.48–7.66pp. The checks detect both mistakes. Current action/feedback perturbations leave every probability through the changed opportunity exactly unchanged.
- Rho1 reproduces the old sequence exactly. Its prefix MAP/Fisher calibration metadata and256 coefficient/memory particles also agree exactly. An independent scalar finite-difference/Fisher reconstruction for rho.7 and1 agrees within2.10e-12.
- For one already-consumed original-development prefix, rho1 regenerates256-particle3000-opportunity futures under both trainers with exactly matching curves, counts, coefficient bins, final memory, probe probabilities and trainer pools. A separate vector recurrence and independent endpoint reduction also reproduce rho.7's complete streams under both trainers. This uses the frozen trainer already independently verified historically; it does not claim a second independent native-trainer implementation.
- The only empirical read is original development animalCSHL034's first1000 rows via `common.load_consumed(cap=1000)`, logged before loading in this campaign. Future session starts in these audit simulations are synthetic. No actual future choices, outcomes or opportunity metadata were opened by this check.
- Pan/fip_13, SWC_007, NYU-21, an unknown identity and zero/4001-row caps are rejected before logging or decoding. Historical exposure loggers are patched to raise if invoked; old exposure-ledger hashes remain unchanged. Every pin in the old population freeze passes before and after execution.

## Code and scope assessment

`session_model.sequence` implements pretrial attenuation and carries the continuation distinction explicitly through the initial-state type. Inherited prefix MAP fitting dynamically calls that recurrence, and the old joint Fisher propagation therefore uses the candidate's own prefix dynamics. `common.simulate` supplies the same rho to both coefficient/memory future transitions, applied before prediction; inherited `update` retains the old post-response session covariate and does not apply a second transition.

`common.load_consumed` permits only original74 development, original40 full-horizon source and later24 primary source identities. Its mixed-original-byte path reads only requested first-n rows, capped at4000. The original prepared NPZ path decompresses arrays from already fully consumed histories and returns only the cap; this does not restore or expand their scientific exposure. New writes go to the new campaign ledger. Imported historical functions used in these routes have no implicit exposure writes; the test verifies that assumption dynamically.

The fixed equal-lab population-curve MAE objective is coherent with the population question. It does not fit a new within-session learning law or identify biological retention. The finite six-value grid and conservative tie rule avoid an architecture tournament. Comparisons on historical40/later24 remain development checks despite their past holdout roles.

No blocker was found in the reviewed transition or reader. Preserve three statistical limits in interpretation: the few-lab bootstrap is a development robustness screen; signed error cancellation inside each lab can differ from individual predictive utility;256-particle fitting versus512-particle comparison leaves MonteCarlo variation that should be reported without refining the frozen grid. The separate known-answer control and source-readiness criteria must still pass before any protected-prefix access can be considered.
