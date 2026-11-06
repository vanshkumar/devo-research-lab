# Reproduction and preserved execution record

Run from `/Users/vanshkumar/Documents/repos/devo-research-lab`. The primary result
is already complete; reruns are audits of consumed source rows, never a new
prospective test or permission to open external data.

## Fast integrity and access check

```sh
campaigns/learning_rule_transport_2026-10-28/.modelenv/bin/python campaigns/population_learning_transport_2026-10-28/code/verify.py
```

This verifies all 44 frozen files, 4,407 original byte hashes, all 150 source
and source-state counterfactual forecast files, prefix/metadata hashes, source
result hashes and ledger ordering. It checks that all forecasts precede scored
outcomes, access caps hold, and no external or SWC_007 value access occurred.
It reads no trial values and uses no network. It refreshes only its audit JSON.

## Independent original-byte reconstruction

```sh
campaigns/learning_rule_transport_2026-10-28/.modelenv/bin/python campaigns/population_learning_transport_2026-10-28/artifacts/coverage/reconstruction/reconstruct_scores_limited.py --released
campaigns/learning_rule_transport_2026-10-28/.modelenv/bin/python campaigns/population_learning_transport_2026-10-28/artifacts/coverage/SEMANTIC_AUDIT.py
```

These independently read only the already exposed first 4,000 rows of 24 source
animals and first 3,000 rows of NYU-21, with before-read exposure logging. They
reconstruct native signs, endpoints, counts, proper scores, intervals and
bootstrap comparisons. They never open SWC_007 or the protected external cohort.
The numerical reconstruction uses explicit pair distances for CRPS, rather
than the production sorting identity. Its result agrees within 7.79e-15.

The audit copy records two narrow repairs, with exact diffs/hashes: cap NYU-21
at four complete future bins; align its final dictionary with the pre-scoring
finite-subgroup guard. The first stopped audit attempt passed the numerical
comparisons and is preserved. The original frozen reconstructor is unchanged.

## Independent simulation replay

```sh
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 campaigns/learning_rule_transport_2026-10-28/.modelenv/bin/python campaigns/population_learning_transport_2026-10-28/code/production_replay.py --cohort source --limit 6
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 campaigns/learning_rule_transport_2026-10-28/.modelenv/bin/python campaigns/population_learning_transport_2026-10-28/artifacts/policy_audit/production_replay/FIXED_SWAP_REPLAY.py
```

The first six source animals are chosen by SHA256 ID. Each replay reconstructs
prefix GRU recurrences/Jacobians/Fisher covariance independently, then generates
512 particles for each of three actors. The fixed-policy replay has its own
sampler. All 36 sampled curves, counts and pool summaries agree exactly;
coefficient/memory differences are below 3.4e-12. These commands read only saved
permitted prefixes, metadata and generated forecasts, never real future choices.
They refresh their own audit outputs and local audit exposure log.

## Pre-exposure controls and original policy diagnostic

```sh
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 campaigns/learning_rule_transport_2026-10-28/.modelenv/bin/python campaigns/population_learning_transport_2026-10-28/code/policy_audit.py
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 campaigns/learning_rule_transport_2026-10-28/.modelenv/bin/python campaigns/population_learning_transport_2026-10-28/code/gate_audit.py --precision --controls --particles 128 --repetitions 20000 --counts 5,2,1,10,6
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 campaigns/learning_rule_transport_2026-10-28/.modelenv/bin/python campaigns/population_learning_transport_2026-10-28/code/learner_controls.py
```

These use consumed old-source data only. They regenerate timestamped exploratory
audit/control artifacts; their original versions are pinned in FREEZE.json, so
do not overwrite them if preserving the exact freeze check. For a fresh rerun,
use a copy of this campaign folder at the same repository depth, changing only
audit output constants or retaining the existing pinned artifacts separately.
No learner is fitted. The known-learner control defines a frozen conditional
generative law in consumed prefix contexts, independently generates future
streams, and distinguishes expected-law recovery from noisy single-cohort power.

## Historical primary execution, not a fresh test

Before any new prefix, FREEZE.json was written and the following source run
executed once:

```sh
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 campaigns/learning_rule_transport_2026-10-28/.modelenv/bin/python campaigns/population_learning_transport_2026-10-28/code/campaign.py --forecasts --particles 512
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 campaigns/learning_rule_transport_2026-10-28/.modelenv/bin/python campaigns/population_learning_transport_2026-10-28/code/score_entrypoint.py
```

Do not rerun these into the original primary folders: they would refresh
forecast metadata/manifests after exposure and obscure the historical ordering.
The independent replay commands above verify the actual saved result without
altering primary files. The source-only reader has no external-cohort route.

The scoring entrypoint adds the explicitly recorded pre-scoring finite-subgroup
guard while importing the unchanged frozen scorer. The source result has no
missing endpoint/subgroup, so all complete-data statistics are identical.
RELEASE_REQUIREMENTS.json makes clear that a provisional performance flag alone
cannot release external data; independent checks and a separately frozen
external protocol would also have been needed. Here the performance flag is false.

## Secondary source challenges

```sh
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 campaigns/learning_rule_transport_2026-10-28/.modelenv/bin/python campaigns/population_learning_transport_2026-10-28/code/diagnostics.py
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 campaigns/learning_rule_transport_2026-10-28/.modelenv/bin/python campaigns/population_learning_transport_2026-10-28/code/retention_fixed_challenge.py
MPLCONFIGDIR=/private/tmp/population_transport_mpl .venv/bin/python campaigns/population_learning_transport_2026-10-28/code/plot_result.py
```

These use saved source prefixes/forecasts and already scored source endpoints.
They never change the primary result or source gate. The two future-only
perturbations use 128 particles; they are postvalidation diagnostics, with the
primary prefix calibration retained. The source-state policy swaps were saved
before future outcomes, but have no real changed-policy counterpart in these
animals. The plot was rendered and visually inspected.

## Software, seeds and failures retained

Numerical runtime: CPython 3.12.14, NumPy 2.3.5, SciPy 1.18.1, Numba 0.68.1,
DuckDB 1.4.1 (the pinned local reader extension). SOFTWARE.json records versions.
Forecast seed is the first eight SHA256(subject) hex digits modulo 2^31−1;
stream offsets 101/211/313/419 separate choices, donor engagement, prefix-state
uncertainty and trainer sampling. Bootstrap seed is 202610282. Known-answer
control seeds and historical exploratory particle counts are saved with outputs.

Primary and sensitivity runs completed with empty stderr. The main numerical
environment lacks Matplotlib; the figure uses the existing root .venv, with no
numerical refitting. Its initial missing-package error and font-cache notice
are recorded in the execution record. The metadata audit first met sandbox DNS
restrictions; normal authorized public-data network escalation succeeded. A
NumPy private-header API mismatch was corrected to versioned public header
readers before any trial values were accessed. The static missing-subgroup
fixture intentionally emits an empty-mean warning before rejecting that case;
the real source data have no such missingness. No scientific threshold, cohort,
model, or future outcome access scope was selected from these failures.

Detailed commands, saved stdout/stderr and audit-only amendments remain in
artifacts/. Historical campaign files were never overwritten. There is no paid
compute, separately billed API, private upload, publication or external contact.
