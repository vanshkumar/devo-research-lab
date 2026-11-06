# Why the first oracle failure cannot diagnose a bad evaluator

This is an assay-control calculation, not a new general theorem.

Let y(a) and t be the centered, SD2 sensory patterns concatenated across the six contexts. In the nondegenerate generated patterns, E[y²]=E[t²]=4. Define rho(a)=E[y(a)t]/4. The gain-dependent true MSE is exactly

`L(a,g) = 4g² - 8g rho(a) + 4`.

The optimal nonnegative gain at fixed shape is `max(0,rho(a))` (bounded above2 here). At g0, `L(a,0)=4` for every shape. Every pure shape coordinate proposal is therefore equal-cost. If the current shape has negative correlation and positive gain-only increments also worsen loss, strict coordinate search cannot leave that state. A globally reachable exact target does not prevent this coordinate-local trap. The same absent-drive equality holds for any deterministic frozen circuit with the clock retained.

Development plant1 supplies the exact witness: the oracle starts at trueMSE9.196659, reaches gain0/trueMSE4, and retains exactly its initial four shape coordinates. The learned35 joint actor reaches the same program. The learned35 fixed-gain actor reaches about.00270 MSE. These observations do not establish a circuit-specific attenuation trap; the known-answer oracle has the same exploration problem.

The single revised common broad-poll rule fixes the known-answer development problem: all three revised oracles recover more than99.99% of initial true loss at64 rounds, including plant1. It does so using target-blind programs and the same641 feedback-slot budget. All original evidence is preserved in `results/`, `COORDINATE_PILOT.json` and `COORDINATE_DEVELOPMENT_VERIFICATION.json`. Further optimizer selection is forbidden before the held-out comparison.

This does not prove the revised search finds global optima on every future draw. Whole-plant validation must keep every draw, show individual oracle outcomes and distinguish incomplete search from reward conflict. In particular a large fractional improvement can include mere attenuation when initial MSE exceeds4; absolute loss, final gain, wrong-tutor controls and the frozen secondaryMSE<=.4 endpoint address that interpretation.
