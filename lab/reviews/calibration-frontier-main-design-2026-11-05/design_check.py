"""Independent summary-only design check. No author imports or empirical rows.

Run from repository root with .venv/bin/python and one numerical thread.
The calculations assess development precision, not a newly run main study.
"""
import hashlib
import json
import math
import pathlib
import resource
import time
from datetime import datetime, timezone

import numpy as np
from scipy.stats import t

START = time.monotonic()
CPU_START = time.process_time()
ROOT = pathlib.Path(__file__).resolve().parents[3]
SOURCE = ROOT / "lab/tasks/acquisition-rule-vs-tracker-2026-11-05"
OUT = pathlib.Path(__file__).resolve().parent
PINS = {}
READ_BYTES = 0


def read(name):
    global READ_BYTES
    path = SOURCE / name
    raw = path.read_bytes()
    READ_BYTES += len(raw)
    PINS[str(path.relative_to(ROOT))] = {
        "bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest()
    }
    return json.loads(raw)


def mean_columns(x):
    # Explicit contractions avoid depending on this workspace's BLAS behavior.
    return np.sum(x, axis=0) / len(x)


def inference(x, margins, boot_count=20000, seed=20261105):
    n, m = x.shape
    estimate = mean_columns(x)
    se = np.std(x, axis=0, ddof=1) / math.sqrt(n)
    rng = np.random.default_rng(seed)
    upper_max = []
    absolute_max = []
    for begin in range(0, boot_count, 500):
        size = min(500, boot_count - begin)
        indices = rng.integers(0, n, size=(size, n))
        boot = np.mean(x[indices], axis=1)
        pivot = (estimate - boot) / se
        upper_max.extend(np.max(pivot, axis=1).tolist())
        absolute_max.extend(np.max(np.abs(pivot), axis=1).tolist())
    q_upper = float(np.quantile(upper_max, .95))
    q_two = float(np.quantile(absolute_max, .95))
    bonf = float(t.ppf(1 - .05 / m, n - 1))
    return {
        "n": n, "family_size": m,
        "estimate": estimate.tolist(), "sd": np.std(x, axis=0, ddof=1).tolist(),
        "se": se.tolist(), "margin": margins.tolist(),
        "pointwise_two_sided_t95": np.stack([
            estimate - t.ppf(.975, n - 1) * se,
            estimate + t.ppf(.975, n - 1) * se], axis=1).tolist(),
        "bonferroni_one_sided95_critical": bonf,
        "bonferroni_one_sided95_upper": (estimate + bonf * se).tolist(),
        "bonferroni_margin_headroom": (margins - estimate - bonf * se).tolist(),
        "bootstrap_count": boot_count,
        "centered_bootstrap_maxT_one_sided95_critical": q_upper,
        "centered_bootstrap_maxT_one_sided95_upper": (estimate + q_upper * se).tolist(),
        "centered_bootstrap_maxabsT95_critical": q_two,
        "centered_bootstrap_maxabsT95_lower": (estimate - q_two * se).tolist(),
        "centered_bootstrap_maxabsT95_upper": (estimate + q_two * se).tolist(),
    }


scores = read("EARLY_SCORES.json")
reduction = read("EARLY_REDUCTION.json")
selection = read("EARLY_SOURCE_SELECTION.json")
preparation = read("PREPARATION.json")
subjects = list(scores["per_animal"])
manifest = preparation["eval_source_manifest"]
lab_map = dict(zip(manifest["subjects"], manifest["labs"]))
labs = np.array([lab_map[s] for s in subjects])
site_names = sorted(set(labs))
assert len(subjects) == 64 and len(site_names) == 9
assert subjects == manifest["subjects"]


def risks(cutoff, horizon, model, metric):
    return np.array([scores["per_animal"][s][str(cutoff)][model][str(horizon)][metric]
                     for s in subjects], dtype=float)


def primary_vectors(horizon):
    columns = []
    for cutoff in [200, 1000]:
        ordinary_mae = risks(cutoff, horizon, "recent_growth", "equal_side_mae")
        neural_mae = risks(cutoff, horizon, "gru", "equal_side_mae")
        ordinary_score = risks(cutoff, horizon, "recent_growth", "mixed_ratio_score")
        neural_score = risks(cutoff, horizon, "gru", "mixed_ratio_score")
        columns += [ordinary_mae - neural_mae, .9 * ordinary_score - neural_score]
    return np.stack(columns, axis=1)


labels = ["200_MAE_gain", "200_score_10percent_margin_contrast",
          "1000_MAE_gain", "1000_score_10percent_margin_contrast"]
margins = np.array([.02, 0, .02, 0])
primary = primary_vectors(2000)
primary_result = inference(primary, margins)
primary_result["labels"] = labels
primary_result["MAE_units"] = "fractions; multiply by100 for percentage points"
primary_result["score_margin_definition"] = ".9*ordinary_score-neural_score; upper<0 excludes >=10percent relative neural score improvement"

# Independently reproduce the saved means, not author analysis code.
checks = []
for cutoff in [200, 1000]:
    for metric in ["equal_side_mae", "mixed_ratio_score"]:
        gain = risks(cutoff, 2000, "recent_growth", metric) - risks(cutoff, 2000, "gru", metric)
        checks.append(abs(float(np.mean(gain)) - reduction["gru_advantage"]["recent_growth"][str(cutoff)]["2000"][metric]["equal_animal"]))

site_vectors = np.stack([np.mean(primary[labs == site], axis=0) for site in site_names])
site_result = inference(site_vectors, margins, seed=20261106)
site_result["site_names"] = site_names
site_result["labels"] = labels

strata = {}
for name, indices in [("old40", np.arange(40)), ("later24", np.arange(40, 64))]:
    strata[name] = {"n": len(indices), "primary_estimate": mean_columns(primary[indices]).tolist()}

# Cluster sensitivity targets an equal-animal mean. It does not manufacture
# generalization to a population of new sites from these nine existing sites.
estimate = mean_columns(primary)
cluster_influence = np.stack([np.sum(primary[labs == site] - estimate, axis=0) / len(subjects)
                              for site in site_names])
cluster_se = np.sqrt(len(site_names) / (len(site_names) - 1) * np.sum(cluster_influence**2, axis=0))
cluster_critical = float(t.ppf(1 - .05 / 4, len(site_names) - 1))
cluster = {"working_cluster_se": cluster_se.tolist(), "df": 8,
           "bonferroni_upper": (estimate + cluster_critical * cluster_se).tolist(),
           "warning": "Working small-site sensitivity, not calibrated arbitrary-site coverage."}

# Direct paired calibration and horizon interaction: never compare marginal CIs.
interaction = {}
for horizon in [500, 2000]:
    z = []
    for cutoff in [200, 1000]:
        z.append(np.stack([risks(cutoff, horizon, "recent_growth", metric) -
                           risks(cutoff, horizon, "gru", metric)
                           for metric in ["equal_side_mae", "mixed_ratio_score"]], axis=1))
    direct = z[0] - z[1]
    se = np.std(direct, axis=0, ddof=1) / 8
    mean = mean_columns(direct)
    interaction[str(horizon)] = {"estimate": mean.tolist(), "animal_t95":
        np.stack([mean-t.ppf(.975,63)*se,mean+t.ppf(.975,63)*se],axis=1).tolist()}

full_panel = inference(np.column_stack([primary_vectors(500), primary]), np.tile(margins,2),
                       seed=20261107)
full_panel["labels"] = [f"{h}_{label}" for h in [500,2000] for label in labels]

# Source-selection uncertainty from permitted per-animal source aggregate scores.
# Resample the SAME source animal jointly across cutoffs and candidates.
candidates = list(selection["ranking"])
source_subjects = selection["validation_eligible"]
source_labs = {r["subject"]: r["lab"] for r in selection["cv"][candidates[0]]["200"]["per_animal"]}
source_site_names = sorted(set(source_labs.values()))
source_cube = []
for candidate in candidates:
    by_cutoff = []
    for cutoff in [200,1000]:
        rows = {r["subject"]:r["score"] for r in selection["cv"][candidate][str(cutoff)]["per_animal"]}
        by_cutoff.append([rows[s] for s in source_subjects])
    source_cube.append(np.mean(by_cutoff,axis=0))
source_cube = np.array(source_cube).T
source_site_indices = [np.array([i for i,s in enumerate(source_subjects) if source_labs[s] == lab])
                       for lab in source_site_names]
source_point = np.mean([np.mean(source_cube[idx],axis=0) for idx in source_site_indices],axis=0)
source_rng = np.random.default_rng(20261108)
source_boot_means = np.zeros((20000,len(candidates)))
for indices in source_site_indices:
    resampled = source_rng.choice(indices,size=(20000,len(indices)),replace=True)
    source_boot_means += np.mean(source_cube[resampled],axis=1) / len(source_site_indices)
winners = np.argmin(source_boot_means,axis=1)
source_selection = {
    "candidate_order": candidates, "equal_site_mean":source_point.tolist(),
    "saved_ranking_max_error":max(abs(float(source_point[j])-selection["ranking"][c]) for j,c in enumerate(candidates)),
    "fixed_source_site_stratified_animal_bootstrap_winner_fraction":{
        candidate:float(np.mean(winners == j)) for j,candidate in enumerate(candidates)},
    "site_sizes": {lab:len(idx) for lab,idx in zip(source_site_names,source_site_indices)},
    "candidate_minus_selected_paired_bootstrap95":{
        candidate:np.quantile(source_boot_means[:,j]-source_boot_means[:,0],[.025,.975]).tolist()
        for j,candidate in enumerate(candidates) if j},
    "leave_one_source_site_out_winner":{},
    "warning":"Selection stability only. These saved source summaries cannot propagate donor-bank or candidate-specific evaluation uncertainty. Singleton source sites have zero within-site bootstrap variance. Neural source parameters remain fixed."
}
for omitted in source_site_names:
    keep = [idx for lab,idx in zip(source_site_names,source_site_indices) if lab != omitted]
    means = np.mean([np.mean(source_cube[idx],axis=0) for idx in keep],axis=0)
    source_selection["leave_one_source_site_out_winner"][omitted] = candidates[int(np.argmin(means))]

# Check the mixed observable energy score on a small, fully enumerated law.
support = np.array([[1.,0.,0.],[0.,0.,1.],[0.,.5,.5],[0.,1.,0.]])
distances = np.sqrt(np.sum((support[:,None,:]-support[None,:,:])**2,axis=2)/2)
truth = np.array([.2,.2,.4,.2])
forecast_laws = {"truth":truth,"all_missing":np.array([1.,0.,0.,0.]),
                 "positive_only":np.array([0.,.25,.5,.25]),
                 "wrong_positive_accuracy":np.array([.2,.4,.2,.2])}
expected_scores = {}
for name,forecast in forecast_laws.items():
    first = np.sum(truth[:,None]*forecast[None,:]*distances)
    second = np.sum(forecast[:,None]*forecast[None,:]*distances)/2
    expected_scores[name] = float(first-second)
assert all(value >= expected_scores["truth"] - 1e-14 for value in expected_scores.values())
positive = support[1:,1]
crps_identity_error = float(np.max(np.abs(distances[1:,1:]-np.abs(positive[:,None]-positive[None,:]))))

# A mean forecast assessed by absolute loss is not a proper score of its mean.
# Preserve the historical MAE readout, but do not infer distributional absence
# from it alone. This skewed known law reverses MAE and CRPS orderings.
binary_truth = np.array([.8,.2])
binary_values = np.array([0.,1.])
truthful_mean = float(np.sum(binary_truth * binary_values))
point_mean_MAE = float(np.sum(binary_truth * np.abs(binary_values-truthful_mean)))
point_median_MAE = float(np.sum(binary_truth * np.abs(binary_values)))
binary_dist = np.abs(binary_values[:,None]-binary_values[None,:])
truthful_expected_CRPS = float(np.sum(binary_truth[:,None]*binary_truth[None,:]*binary_dist)/2)
median_expected_CRPS = float(binary_truth[1])

result = {
    "utc":datetime.now(timezone.utc).isoformat(),
    "scope":"Independent design calculation from permitted consumed aggregate summaries and a simulated finite law; no new forecasts or empirical trial access.",
    "input_pins":PINS,
    "saved_mean_reproduction_max_error":max(checks),
    "primary_long_window_four_endpoint_family":primary_result,
    "equal_observed_site_sensitivity":site_result,
    "equal_animal_cluster_sensitivity":cluster,
    "strata":strata,
    "paired_information_contrast":interaction,
    "all_eight_readout_sensitivity":full_panel,
    "source_selection":source_selection,
    "mixed_observable_score_check":{
        "expected_scores":expected_scores,"positive_CRPS_identity_max_error":crps_identity_error,
        "missing_vs_positive_distance_formula":"sqrt(a*a-a+1)",
        "interpretation":"Proper mixed-observable score; not a score of the full count/success or acquisition-path law."},
    "mean_MAE_counterexample":{
        "truth_P_accuracy0":.8,"truth_P_accuracy1":.2,
        "truthful_mean_forecast":truthful_mean,
        "truthful_mean_expected_MAE":point_mean_MAE,
        "median_point_forecast_expected_MAE":point_median_MAE,
        "truthful_distribution_expected_CRPS":truthful_expected_CRPS,
        "median_point_distribution_expected_CRPS":median_expected_CRPS,
        "interpretation":"Point MAE of particle means is an operational readout, not a proper score of expected accuracy or a full law. Require the proper-score endpoint for a broad forecast-law absence claim; predeclare median-MAE sensitivity without replacing the consumed primary."},
    "resources":{
        "explicit_summary_read_bytes":READ_BYTES,
        "numeric_working_array_bytes":primary.nbytes+site_vectors.nbytes+source_cube.nbytes+source_boot_means.nbytes,
        "computation_phase_cpu_seconds_excluding_imports":time.process_time()-CPU_START,
        "computation_phase_wall_seconds_excluding_imports":time.monotonic()-START,
        "peak_RSS_bytes_macOS":resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
        "external_ingress_bytes":0,
        "unknown":"Physical I/O, interpreter/import reads and provider overhead not measured; text context reads are separate."},
    "uncertainty":"All resampling is developmental and assumes the specified source-site/animal sampling. No coverage certificate for outcome-driven study selection, future model families, unseen sites, or misspecified teachers. Simultaneous bounds omit source refits and integration uncertainty."
}
(OUT/"DESIGN_CHECK.json").write_text(json.dumps(result,indent=2)+"\n")
print(json.dumps({"summary_reproduction_error":result["saved_mean_reproduction_max_error"],
    "long_window_means":primary_result["estimate"],
    "bonferroni_upper":primary_result["bonferroni_one_sided95_upper"],
    "bootstrap_maxT_upper":primary_result["centered_bootstrap_maxT_one_sided95_upper"],
    "site_bonferroni_upper":site_result["bonferroni_one_sided95_upper"],
    "source_selection":source_selection,
    "mixed_score_check":result["mixed_observable_score_check"],
    "resources":result["resources"]},indent=2))
