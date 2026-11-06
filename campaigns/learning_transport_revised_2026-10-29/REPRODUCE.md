# Reproduce the finite comparison

Work from `/Users/vanshkumar/Documents/repos/devo-research-lab`. No network, new external observations, paid resources or historical writes are needed. The existing `campaigns/learning_rule_transport_2026-10-28/.modelenv/bin/python` provides NumPy/SciPy/Numba and the pinned DuckDB reader. All new logs and outputs stay in this campaign. All Pan prefixes/outcomes remain sealed.

The scientific prescription is [DESIGN.md](protocols/DESIGN.md), with the pre-computation aggregation clarification in [COMPARISON_DEFINITIONS.md](protocols/COMPARISON_DEFINITIONS.md). [FIT_FREEZE.json](protocols/FIT_FREEZE.json) and [COMPARISON_FREEZE.json](protocols/COMPARISON_FREEZE.json) pin the exact code/protocol. Do not modify those bytes or rerun historical campaign entrypoints into their original directories.

Use these environment settings with numerical commands:

```sh
export OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONDONTWRITEBYTECODE=1
export NUMBA_CACHE_DIR=/Users/vanshkumar/Documents/repos/devo-research-lab/campaigns/learning_transport_revised_2026-10-29/artifacts/numba_cache
```

Independent checks reconstruct the saved result without fitting a new model:

```sh
campaigns/learning_rule_transport_2026-10-28/.modelenv/bin/python campaigns/learning_transport_revised_2026-10-29/code/verify_campaign.py
campaigns/learning_rule_transport_2026-10-28/.modelenv/bin/python campaigns/learning_transport_revised_2026-10-29/audits/independent_transition_check.py
campaigns/learning_rule_transport_2026-10-28/.modelenv/bin/python campaigns/learning_transport_revised_2026-10-29/audits/independent_result_check.py
```

The first reads hashes/JSON only and verifies historical and new freezes, saved forecasts, the explicit control-log finalization record and the stopping/access status. The transition check uses one previously consumed development prefix and synthetic futures; the result check reconstructs consumed-derived targets, fit selection, numerical comparisons and saved control replicates. They preserve historical ledgers and freezes. Their result JSONs and reviews specify actual checked tolerances and scope.

Historical execution of this new campaign:

```sh
campaigns/learning_rule_transport_2026-10-28/.modelenv/bin/python campaigns/learning_transport_revised_2026-10-29/code/fit_transition.py --fit --freeze campaigns/learning_transport_revised_2026-10-29/protocols/FIT_FREEZE.json
campaigns/learning_rule_transport_2026-10-28/.modelenv/bin/python campaigns/learning_transport_revised_2026-10-29/code/compare_source.py --phase baselines
campaigns/learning_rule_transport_2026-10-28/.modelenv/bin/python campaigns/learning_transport_revised_2026-10-29/code/compare_source.py --phase alternative
campaigns/learning_rule_transport_2026-10-28/.modelenv/bin/python campaigns/learning_transport_revised_2026-10-29/code/compare_source.py --phase summarize
campaigns/learning_rule_transport_2026-10-28/.modelenv/bin/python campaigns/learning_transport_revised_2026-10-29/code/calibrate_decision.py
```

The fitting/comparison runners reuse existing cells only after hash/metadata checks. For a full new regeneration preserve the archived files and use a same-depth copy with its own new output paths, retaining the original freezes; never overwrite a primary forecast. Do not rerun the control generator into the archived directory: it rewrites timestamped result/manifest files. The independent replay is the preferred check of the recorded computation. Controls have their own pre-run [CALIBRATION_FREEZE.json](artifacts/decision_controls/CALIBRATION_FREEZE.json) and frozen finite-pool residual/draw inputs. They must not be tuned after their failed result. The original stdout-manifest mismatch and dated finalization record remain part of the audit.

The known-learner conditional-prefix recovery and fixed-policy check has its separate plan/freeze under `artifacts/known_learner/`, with `code/known_learner_control.py`. It generates synthetic futures only; it does not analyze Pan. Its result and scope are supplementary to the failed primary readiness controls.

Scientific figure, from saved summaries only:

```sh
MPLCONFIGDIR=/private/tmp/revised_transport_mpl .venv/bin/python campaigns/learning_transport_revised_2026-10-29/code/plot_result.py
```

The source reader whitelists original74 development animals, original40 full-horizon source animals and later24 primary source animals, returning at most4000rows. It excludes the six old prefix-only cases, NYU21, SWC007, every Pan identity and all unused cohort values. Original prepared archives are already fully consumed; their decompression does not create fresh confirmation. The mixed-format path returns only its capped first-n rows. Future metadata conditioning predicts neither attendance nor calendar time, and cannot establish biological first exposure.
