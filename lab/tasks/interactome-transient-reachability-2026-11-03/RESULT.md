# Original full2019 reference banked; one-cycle pulse recipe CLOSED

**A new, frozen finite stimulation test ran on the complete published-model release. It produced no material retained motor-circuit state or altered later response after input restoration. BANK the original-model reference and CLOSE this specific pulse-to-rest recipe.** This is a finite model result, not absence of biological memory or a global impossibility claim. The native scientific mission remains unfinished.

## What actually ran

The source is Kim–Leahy–Shlizerman2019 Neural Interactome's linked beta release, pinned tree `bdb94ca174980e46777f7b1936f539903c688719`, treated as its own version. All279neurons/558states, exact connectivity, source initialization law, constants, input-dependent thresholds and smoothing were retained. Source-equation extraction avoids unrelated server/UI code. It is not exact2017reproduction. [MODEL_REFERENCE.json](MODEL_REFERENCE.json) records actual06:14:46Zexecution, ahead of06:34:58Zgate: exact extracted sourceRHS/VODE and independently expressed sparseRHS/Radau agree on complete54-step defaultzero/FWD trajectories, maxerrors9.48e-7/2.382e-4. A20s full-model FWDreference gives VB01medianperiod1.935s versus paper~2s. Independently assembled threshold solves agree within9.10e-13. Physical unit/behavior calibration remains unearned; reported amplitudes are source-voltage units.

The NEW [protocol](PROTOCOL.md)/[configuration](CONFIG.json) were actually timestamp-hashed at06:18:17.907Z, before evaluation; [FREEZE.json](FREEZE.json) remains unchanged. Two prespecified source-law initializations each settle20s; a2s exact publishedFWDpreset (PLML/R.14,AVBL/R.23) is applied, then zero input is restored for20s before an identical2s challenge. Sham and continuouslydriven controls share the same histories/inputs as declared. Finite/sham have exactly identical zero current and source thresholds after22.3s. All37DB/VB/DD/VD motor neurons are scored, with no selected projection/readout. Two seeds are initialization controls on ONEconnectome, not two biological units.

## Frozen outcomes and numerical resolution

The predetermined material threshold is0.563825964source-voltageRMS,10%of the independently executed sustainedFWDmotor temporalRMS5.63825964.

| Prespecified comparison | Seed0 | Seed1 |
|---|---:|---:|
| Retained finite-minus-sham motorRMS,40–42s | 7.981e-11 | 7.981e-11 |
| Later challenge motorRMS difference,42.3–44s | 1.602e-9 | 1.605e-9 |
| Continuing-drive minus sham motorRMS,40–42s | 329.994 | 329.994 |

**The tiny finite/sham differences are below numerical resolution and must not be interpreted as precise nonzero memory.** The tighter literal-source replay gives retainedRMS2.30e-16 and challengeRMS3.65e-10. Its maximum full-trajectory motor discrepancy from primary integration is6.76e-5, over8,000times below the material cutoff. Thus both declared material gates fail decisively at the chosen resolution, while the responsive continuing-drive control passes. The last/preceding-second ratio1.416 is a numerical-floor ratio, not persistence evidence.

[PILOT_RESULT.json](PILOT_RESULT.json), [PILOT_SUMMARY.csv](PILOT_SUMMARY.csv) and complete rawmodelNPZs preserve all outcomes. FullV/S terminal differences are also negligible. The zero-input localJacobian's largest real eigenvalue is about−3.03283/s; its prespecified linearized tail decays below numerical resolution. That control is consistent with relaxation here, not a proof of global uniqueness. ConditionalNewton/attractor checks were NOT run because their predeclared material prerequisites failed. The renderer is instantaneous; its raw/filtered comparisons agree on the absence of a material effect.

## Failures and actual adversarial checks

The initial text-only connectivity fetch failed; explicitbase64 acquisition succeeded with exactGitblob pins. Our first reference assumed the wrong emask shape, corrected to the actual279x1source asset. The first frozen pilot stopped on a binary output-grid endpoint; the continuation saved all six primary branches before tightVODEfailed at the source's.3s clipping discontinuity. Primary trajectories were preserved, then the SAMEtightreference completed using one-sided segment limits/maxstep10ms. Model/input/seed/horizon/readout/tolerance/materiality choices did not change. All failed code/start receipts and nativeexits survive in [FAILURES.md](FAILURES.md)/history; no outcome tuning or scientific protocol revision occurred.

SciPy's matrix-exponential matmul warnings recurred. [OUTPUT_AUDIT.json](OUTPUT_AUDIT.json) checks finite results and an independent24-term Taylor/scaling-squaring computation using explicit contractions: relativematrixdifference2.884e-10/actiondifference2.934e-36. The warning cause remains unidentified. Direct scalar accumulation reproduces both primary scores; source/scalar/sparse dynamics checks on noninitialstates agree within4.86e-10. These are within-author numerical checks, not a distinct independent review.

## Research decision and limits

**BANK verified full2019execution and this fixed negative; CLOSE the consumed one-cycle forward-pulse-to-zero-input recipe without a main or duration/seed/parameter search.** The inspected prior already predicts input-dependent oscillations; this test adds a directly executed finite-input/restoration/rechallenge comparison rather than a novel general memory principle. The paper's known driven attractors and other legitimate perturbations remain outside this result. Other basins, inputs, time scales, different model versions and biological recordings are untested. No calibrated animal-behavior prediction, priority claim, global absence, unique-attractor proof, model defect or completed native mission is earned.

The PI's next investment should require an independent reason that a different legitimate intervention reaches distinguishable retained states, beyond known continuing-drive dynamics, ordinary relaxation or phase. This allocation supplies no evidence for funding a broader main on the present recipe. A future consequential claim still requires a NEWdistinct independent challenge. Both predecessor source allocations remain CLOSED with their original histories; no empirical/protected observations were opened.

New charges:9publicoperations/full20MBingressUNCERTIFIED/full800MBseparate read/import/context booking/900sconservative localprocessbooking/largest measuredsuccessfulRSS204537856; interrupted peaks and completeprovider/runtime/physicalIOunknown. Additive totals145ops654594722ingressUNCERTIFIED4.901GBseparate reads. Final actual06:27:16Z13%remaining/secondaryunavailable/ordinaryallowed/floor10; no credits/reset. See [RESOURCES.json](RESOURCES.json), [SOURCE_MANIFEST.json](SOURCE_MANIFEST.json), [NATIVE_EXECUTION.json](NATIVE_EXECUTION.json) and [README.md](README.md). Jobs0 at handoff; same operator goal/heartbeat unchanged.
