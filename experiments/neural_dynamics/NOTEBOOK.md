# Neural dynamics notebook

## Before outcomes
- Initial protocol: PLAN.md, selection.json. Six discovery files pinned to commit 513782b42ad77e75f35adfbc70064b7418ff674a; four validation animals untouched. Acquired using acquire.py; git-blob SHA1 verified before saving, SHA256 and bytes in data/public/manifest.json.
- Acquisition-raw movies are not used. JSON traces are a public processed mirror; their upstream metadata/derived encoding labels are not used as scientific ground truth.
- Environment: isolated .venv; dependencies locked at experiments/requirements.lock.txt. Sandboxed pip DNS failed; authorized network escalation succeeded. Agents noticed NumPy @ warnings on finite inputs; root uses explicit einsum products and SciPy linear algebra, and run logs contain no such warnings.

## Commands actually executed
```
.venv/bin/python experiments/neural_dynamics/acquire.py --part discovery
OPENBLAS_NUM_THREADS=1 MPLCONFIGDIR=$PWD/.mplconfig .venv/bin/python experiments/neural_dynamics/run.py --part controls > experiments/neural_dynamics/control.log 2>&1
OPENBLAS_NUM_THREADS=1 MPLCONFIGDIR=$PWD/.mplconfig .venv/bin/python experiments/neural_dynamics/run.py --part discovery > experiments/neural_dynamics/discovery.log 2>&1
```

## Controls and revision
Forecast control (10 seeds): population ridge beats diagonal direct AR on noisy rotations at 0.6/3/12 sec (median improvements .350/.492/.157); it does not at 30 sec (-.014). Independent AR does not show systematic population advantage, except a small .010 at 30 sec where correlations are weak. This supports capability at recoverable horizons, not unlimited forecasting.

Spectrum/marginal invariants pass. The general expectation that a shared oscillation must have lower dimension than independent-phase nulls is **false for a pure single-frequency sinusoid**: all phase-randomized channels remain in span{sin,cos}. Raw top-3 variance stays 1.0 and no rejection follows. This failed universal positive-control assumption is preserved in control_nulls.csv. Stochastic noisy rotations and shared broadband AR do reject, while independent AR does not. Treat tests as channel-independence tests conditional on spectra, never tests for loops or nonlinear dynamics. Differencing the exact sine introduces endpoint spectral leakage; its tiny rank differences and low Monte Carlo p must not be biologically interpreted.

## Discovery outcomes (before validation)
All six raw and differenced recordings have participation ratio below every 39 independent-phase and shift nulls. Raw top-3 fractions .353–.478 versus phase-null medians .153–.240. This is evidence for coordinated second-order structure beyond individual channel spectra, not recurrent mechanism or loop topology.

Initial population ridge loses to diagonal AR in every discovery animal/horizon. At .6 sec, persistence is best of the tested models in all six. Train-normalized mean-predictor errors 1.84–3.97 at .6 sec indicate substantial distribution/mean shift, so declaring an absence of predictive population information would be premature. Next check: identity/persistence-anchored ridge, own-history AR and finite sample/temporal split effects before selecting validation claims.

## Access limitations
- Initial PMC browser access returned a browser check; publisher full text returned 403. Public author-deposited PDF attempted as legitimate alternative. No challenge or access control bypassed.
- Kato .mat is absent from the pinned public mirror tree, despite README references. No Kato result is computed here; do not infer moving-versus-immobilized differences.
