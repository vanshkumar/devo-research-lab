# Prospective learning forecasts: scientific draft

29 October2026. Unpublished local manuscript and reproducible benchmark account. No authorship, submission, priority or publication readiness is asserted.

Start with [the manuscript](manuscript.md), then [the methods appendix](METHODS_APPENDIX.md), [evidence and objections ledger](CLAIMS.md) and [internal scientific review](REVIEW.md). [The owner decision](../../RESEARCH_AGENDA_2026-10-29.md) explains why this milestone takes priority over another short campaign. The review supports a scoped benchmark draft; its contribution relative to prior work still needs independent scientific assessment before any submission decision. The owner addressed its terminology and self-contained-methods recommendations in the draft and appendix.

The primary empirical result is the frozen prospective RNN-versus-growth comparison on24 previously unused animals. The same-cohort actual-history analysis added here is explicitly postvalidation and reuses only already-consumed observations. It cannot replace a forecast, identify a unique cause of failure or release protected data. The prior-work clarification recognizes that generated-choice evaluation itself already exists.

## Entry points

- [Primary prospective population report](../../campaigns/population_learning_transport_2026-10-28/REPORT.md).
- [Preceding individual forecast report](../../campaigns/learning_rule_transport_2026-10-28/REPORT.md).
- [Matched-cohort diagnostic and exact rerun command](../../experiments/matched_history_diagnostic_2026-10-29/REPORT.md).
- [Prior clarification](PRIOR_UPDATE.md).
- [Matched-cohort figure](figures/matched_history.png), with [source pin](figures/MATCHED_HISTORY_SOURCE.json).
- `LINK_CHECK.json` verifies local evidence links; it is a documentation check, not scientific validation.

Regenerate the descriptive figure from the saved diagnostic JSON, without reading raw behavior or fitting a model:

```sh
.venv/bin/python papers/learning_forecasts/plot_matched.py
```

The figure reports different information/averaging regimes explicitly. Its plotted curves and errors are descriptive; it does not show a controlled causal ablation. Original campaign freezes, primary results, failures and exposure ledgers remain authoritative. All20 protected external animal prefixes and outcomes remain sealed.
