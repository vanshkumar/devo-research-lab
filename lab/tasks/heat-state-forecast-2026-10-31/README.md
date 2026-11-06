# Heat-response forecasts

The seven-animal frozen test does not earn joint added-state utility: neural gain12.7%with an interval spanning zero, behavior−24.9%versus a strong simple forecast. Fractional fluorescence gives2.5%neural gain. The simple behavior forecast improves29.2%over the shared response. See [RESULT.md](RESULT.md) for interpretation and the [figure](HEAT_FORECAST_RESULT.png).

## Inspect and replay

Workspace root: `/Users/vanshkumar/Documents/repos/devo-research-lab`. Required libraries already exist in `.venv`: Python3.9.6, NumPy and Matplotlib; exact runtime versions are in [ENVIRONMENT.json](ENVIRONMENT.json). No installation or network is needed for cached replay.

```sh
cd /Users/vanshkumar/Documents/repos/devo-research-lab
.venv/bin/python lab/tasks/heat-state-forecast-2026-10-31/reproduce.py
```

This replays all31forecast arrays from source and prefix caches, checks every frozen hash, independently recomputes primary MSE with scalar loops, and writes `REPRODUCTION.json`. The original run reports zero forecast discrepancy and <=4.45e−16error discrepancy. A future reviewer with a separately scoped budget can redirect its output:

```sh
.venv/bin/python lab/tasks/heat-state-forecast-2026-10-31/reproduce.py --output /absolute/owned/review/path/REPRODUCTION.json
```

Do not rerun acquisition or rewrite the frozen split/protocol. All19heat outcomes are consumed; a new context does not recreate a holdout or reset read budgets. Future numerical execution requires its own registered finite assignment.

## Exact original sequence

The recorded commands below explain artifact creation. They are historical reproduction steps, not a request to reacquire or overwrite the completed experiment. Acquisition used the same commands with platform network escalation after sandbox DNS failed. The prefix acquisition/prediction guards intentionally reject duplicate access or overwriting saved forecasts.

```sh
.venv/bin/python lab/tasks/heat-state-forecast-2026-10-31/metadata_check.py
.venv/bin/python lab/tasks/heat-state-forecast-2026-10-31/data_check.py
.venv/bin/python lab/tasks/heat-state-forecast-2026-10-31/prepare.py --part development
.venv/bin/python lab/tasks/heat-state-forecast-2026-10-31/forecast.py --development
.venv/bin/python lab/tasks/heat-state-forecast-2026-10-31/checks.py
.venv/bin/python lab/tasks/heat-state-forecast-2026-10-31/controls.py
.venv/bin/python lab/tasks/heat-state-forecast-2026-10-31/revision.py
.venv/bin/python lab/tasks/heat-state-forecast-2026-10-31/prefix_reader.py --control
.venv/bin/python lab/tasks/heat-state-forecast-2026-10-31/freeze.py
.venv/bin/python lab/tasks/heat-state-forecast-2026-10-31/prefix_reader.py --acquire
.venv/bin/python lab/tasks/heat-state-forecast-2026-10-31/evaluation.py --predict
.venv/bin/python lab/tasks/heat-state-forecast-2026-10-31/evaluation.py --score
.venv/bin/python lab/tasks/heat-state-forecast-2026-10-31/verify.py
.venv/bin/python lab/tasks/heat-state-forecast-2026-10-31/attribution.py
.venv/bin/python lab/tasks/heat-state-forecast-2026-10-31/artifacts.py
.venv/bin/python lab/tasks/heat-state-forecast-2026-10-31/reproduce.py
```

The first attribution execution saved `POSTVALIDATION_ATTRIBUTION.json`. A necessary matched-alpha control was then added, preserving that artifact; current `attribution.py` writes `POSTVALIDATION_ATTRIBUTION_MATCHED.json` and a separate prediction file. Frozen primary code was unchanged. The initial prefix-control assertion used `equal_nan=True` on string arrays and failed; it was corrected before freeze/real evaluation. Two sandbox DNS attempts returned no body; both reservations remain charged. No numerical warnings or hidden outcome-driven repairs were observed in the completed fits.

## Main evidence map

- Design and exposure: `PROTOCOL.md`, `ANALYSIS_PLAN.md`, `SPLIT.json`, `EVALUATION_FREEZE.json`, `ACCOUNTING.json`.
- Startup: `METADATA_CHECK.json`, `FIRST_DATA_CHECK.json`, `DEVELOPMENT_DATA.json`.
- Development and contrary revision: `DEVELOPMENT_RESULT.json`, `DEVELOPMENT_CV.npz`, `ADVERSARIAL_DEVELOPMENT.json`, `DEVELOPMENT_REVISION.json`.
- Evaluation sequence: `EVALUATION_PREFIX_ACCESS.json`, `FORECAST_SAVED.json`, `EVALUATION_OUTCOME_ACCESS.json`.
- Actual forecasts/outcomes: `EVALUATION_FORECASTS.npz`, `EVALUATION_TRUTH.npz`, `EVALUATION_RESULT.json`.
- Checks: `PREFIX_READER_CONTROL.json`, `KNOWN_ANSWER_CONTROLS.json`, `VERIFICATION.json`, `REPRODUCTION.json`; these are author checks, not independent scientific review.
- Sources: `SOURCES.md` and `sources/heat_state_forecast_2026-10-31/SOURCE_MANIFEST.json`. Raw JSONs, prefix projections and derived arrays remain in that source directory.
- Final state/recommendation: `STATE.md`, `RESULT.md`, `PROPOSED_LEARNING.md`.

Seeds are20261031for bootstrap/synthetic controls and11031for reader control. Independent unit is the worm; source standardization, PCA, regression fits and regularization selection stay inside source folds. Bootstrap repeats20000in the main result; synthetic decision controls use2000per draw. Full source preprocessing is not prospective. No background jobs, reviewer or successor is launched here.
