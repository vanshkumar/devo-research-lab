"""Finite calibration of the frozen comparative decision using saved source arrays.

No raw trial files, external inputs, new prefixes or new outcomes are opened.
The plan is pinned before simulation; controls never select another rule.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path
import time

import numpy as np
from scipy.stats import beta

from comparison_statistics import (
    BOOTSTRAP_REPLICATES, BOOTSTRAP_SEED, MATERIAL_GAIN,
    bootstrap_counts, curve_mae_from_residual_mean, external_decision,
    gain_from_residual_means, self_test,
)

CAMPAIGN = Path(__file__).resolve().parents[1]
ROOT = CAMPAIGN.parents[1]
OUT = CAMPAIGN / "artifacts/decision_controls"
OLD_ARRAY = ROOT / "campaigns/population_learning_transport_2026-10-28/artifacts/method_audit/CONSUMED_SOURCE_EXACT100.npz"
LATER_ARRAY = ROOT / "campaigns/population_learning_transport_2026-10-28/artifacts/results/SOURCE_ARRAYS.npz"
REPETITIONS = 2000
SIMULATION_SEED = 202610292
COHORT_N = 20
CASES = {
    "signal_baselines_plus10pp": (0.0, .10, .10),
    "signal_baselines_minus10pp": (0.0, -.10, -.10),
    "null_baselines_correct_candidate_plus10pp": (.10, 0.0, 0.0),
    "null_baselines_correct_candidate_minus10pp": (-.10, 0.0, 0.0),
    "null_equal_error_candidate_plus5_baselines_minus5": (.05, -.05, -.05),
    "null_equal_error_candidate_minus5_baselines_plus5": (-.05, .05, .05),
    "null_identical_correct_forecasts": (0.0, 0.0, 0.0),
}


def digest(path):
    return sha256(Path(path).read_bytes()).hexdigest()


def now():
    return datetime.now(timezone.utc).isoformat()


def rate_interval(k, n):
    """Two-sided exact Clopper-Pearson interval for MonteCarlo proportions."""
    lower = 0.0 if k == 0 else float(beta.ppf(.025, k, n-k+1))
    upper = 1.0 if k == n else float(beta.ppf(.975, k+1, n-k))
    return {"count": int(k), "repetitions": int(n), "rate": float(k/n),
            "interval95_ClopperPearson": [lower, upper]}


def source_pool():
    with np.load(OLD_ARRAY, allow_pickle=False) as old, np.load(LATER_ARRAY, allow_pickle=False) as later:
        old_observed = np.asarray(old["observed"], float)
        later_observed = np.asarray(later["observed"][:, :, :2], float).mean(2)
        residual = np.concatenate((old_observed - old["rnn"].mean(1),
                                   later_observed - later["rnn_means"]), 0)
        subjects = np.concatenate((old["subject"], later["subjects"]))
        labs = np.concatenate((old["lab"], later["labs"]))
    assert residual.shape == (64, 6) and np.isfinite(residual).all()
    assert len(set(subjects)) == 64
    center = residual.mean(0)
    error = residual - center
    assert np.abs(error).max() < .49
    labels = sorted(set(labs))
    lab_offsets = np.array([error[labs == lab].mean(0) for lab in labels])
    lab_offsets -= lab_offsets.mean(0)
    return error, subjects, labs, labels, lab_offsets, {
        "animals": 64, "original": 40, "later": 24,
        "raw_bin_residual_mean_removed": center.tolist(),
        "centered_bin_means": error.mean(0).tolist(),
        "centered_scalar_sd": float(error.mean(1).std(ddof=1)),
        "centered_max_absolute_error": float(np.abs(error).max()),
        "lab_labels": labels, "lab_shared_offsets": lab_offsets.tolist(),
    }


def make_bounded_pool(error, scale):
    scaled = scale * error
    bounded = np.clip(scaled, -.49, .49)
    center = bounded.mean(0)
    bounded -= center
    factor = min(1.0, .49 / np.max(np.abs(bounded)))
    bounded *= factor
    assert np.abs(bounded).max() <= .49 + 1e-14
    assert np.abs(bounded.mean(0)).max() < 1e-14
    return bounded, {
        "requested_multiplier": scale,
        "clipped_pool_cells": int(np.count_nonzero(scaled != np.clip(scaled, -.49, .49))),
        "post_clip_center_removed": center.tolist(), "post_center_common_shrink": float(factor),
        "realized_scalar_sd_ratio": float(bounded.mean(1).std(ddof=1) / error.mean(1).std(ddof=1)),
        "finite_population_mean": (.5+bounded).mean(0).tolist(),
        "finite_population_max_recenter_error": float(np.abs(bounded.mean(0)).max()),
    }


def freeze_plan(repetitions, source_description):
    OUT.mkdir(parents=True, exist_ok=True)
    pins = [Path(__file__), CAMPAIGN/"code/comparison_statistics.py", CAMPAIGN/"protocols/DESIGN.md", OLD_ARRAY, LATER_ARRAY]
    plan = {
        "utc": now(), "date": "2026-10-29", "status": "frozen_before_control_execution_no_data_release",
        "cohort_n": COHORT_N, "repetitions_per_construction_and_case": int(repetitions),
        "bootstrap_replicates": BOOTSTRAP_REPLICATES, "bootstrap_seed": BOOTSTRAP_SEED,
        "simulation_seed": SIMULATION_SEED, "material_gain": MATERIAL_GAIN,
        "decision": "Both growth and persistence gains >=.05 and paired percentile95% lower gain >0; no omnibus accuracy gate.",
        "cases_candidate_growth_persistence_shift_from_template_point5": CASES,
        "primary": "Uniform iid animals from the64 pooled centered empirical six-bin residual vectors; outcomes=.5+residual, no sample-cohort recentering.",
        "double_variability": "Multiply residual pool by2, clip to+/- .49, center each finite-pool bin, common shrink only if recentering leaves bounds. Report realized variance ratio; do not call clipping exact variance doubling.",
        "lab_offset": "Draw one empirical equally weighted zero-mean lab offset per entire20-animal cohort; add to each animal's primary pool residual and bound outcomes to[0,1]. Forecasts remain at unconditional .5+case shift. Recompute each environment's true finite-pool mean and loss; nominal signal/null labels are unconditional and may change conditional truth.",
        "truth": "All known means/losses are recomputed by averaging the full finite error pool, after bounding, separately for each environment. Primary truth is .5 per bin; not the realized simulated cohort mean.",
        "bootstrap": "Generate20000 ordered iid20-index resamples using seed202610291, aggregate to integer multinomial counts; reuse this fixed common-random count matrix for every simulated cohort/case. Each resample retains all6bins peranimal. Exact procedure matches production statistics.",
        "coverage": "Report90/95 percentile scalar-bias and descriptive absolute-MAE interval coverage against known finite-population truth. At zero MAE the absolute loss is nonregular; percentile-MAE intervals are not valid equivalence bounds. Also show gain interval coverage as a diagnostic, not a decision requirement.",
        "primary_acceptance": "Point MonteCarlo success rate>=.80 for each +/- .10 signal and false material superiority<=.05 for each primary null. Exact95%binomial intervals reported; no postcontrol tuning. Sensitivities constrain interpretation but do not replace the frozen primary construction.",
        "resource": "Float64 batches of at most16cohorts, one20k x20 count matrix, expected working arrays<200MB. No paid service/network/raw trial access.",
        "source": source_description,
        "pins": {str(p.relative_to(ROOT)): digest(p) for p in pins},
        "external_prefix_or_outcome_access": False,
    }
    path = OUT / "CALIBRATION_FREEZE.json"
    if path.exists():
        previous = json.loads(path.read_text())
        if previous["pins"] != plan["pins"] or previous["repetitions_per_construction_and_case"] != repetitions:
            raise RuntimeError("Existing calibration freeze differs; preserve it and stop")
        return previous, path
    path.write_text(json.dumps(plan, indent=2, sort_keys=True)+"\n")
    return plan, path


def evaluate_construction(name, pools, env_index, draws, counts, batch_size=16):
    """pools has environment x finite population x6 errors around template.5."""
    repetitions = len(draws)
    truth = pools.mean(1)
    store = {}
    for case in CASES:
        store[case] = {
            "success": np.zeros(repetitions, dtype=bool),
            "point_gain": np.zeros((repetitions, 2)),
            "lower_gain": np.zeros((repetitions, 2)),
            "upper_gain": np.zeros((repetitions, 2)),
            "true_gain": np.zeros((repetitions, 2)),
        }
    coverage = {"bias90": [], "bias95": [], "unconditional_bias90": [],
                "unconditional_bias95": [], "mae90": [], "mae95": []}
    bootstrap_mean_error_max = 0.0
    # All source-error/control choices are fixed before this loop.
    weights = counts.astype(np.float64) / COHORT_N
    all_mean_residuals = []
    for start in range(0, repetitions, batch_size):
        stop = min(start+batch_size, repetitions)
        environment = env_index[start:stop]
        errors = pools[environment[:, None], draws[start:stop], :]
        point = errors.mean(1)
        all_mean_residuals.append(point)
        columns = errors.transpose(1, 0, 2).reshape(COHORT_N, -1)
        boot = (weights @ columns).reshape(len(counts), stop-start, 6).transpose(1, 0, 2)
        if start == 0:
            check = np.einsum("bi,ik->bk", weights[:53], errors[0])
            discrepancy = float(np.abs(check-boot[0, :53]).max())
            assert discrepancy < 1e-14
            bootstrap_mean_error_max = max(bootstrap_mean_error_max, discrepancy)
            # Check batch optimized decision against the production API on one cohort.
            expected = external_decision(.5+errors[0], np.full((20,6),.5),
                                         np.full((20,6),.6), np.full((20,6),.6))
            direct_gain = gain_from_residual_means(boot[0], boot[0]-.10)
            assert np.max(np.abs(np.quantile(direct_gain, [.025,.975])-
                                 expected["comparisons"]["growth"]["gain_interval95"])) < 1e-13
        known = truth[environment]
        scalar = boot.mean(2)
        scalar_truth = known.mean(1)
        q = np.quantile(scalar, [.025,.05,.95,.975], axis=1)
        for level, lo, hi in ((90,1,2),(95,0,3)):
            coverage["bias"+str(level)].extend((q[lo]-1e-14 <= scalar_truth) & (scalar_truth <= q[hi]+1e-14))
            coverage["unconditional_bias"+str(level)].extend((q[lo] <= 0) & (0 <= q[hi]))
        mae_boot = curve_mae_from_residual_mean(boot)
        mae_true = curve_mae_from_residual_mean(known)
        mq = np.quantile(mae_boot, [.025,.05,.95,.975], axis=1)
        for level, lo, hi in ((90,1,2),(95,0,3)):
            coverage["mae"+str(level)].extend((mq[lo]-1e-14 <= mae_true) & (mae_true <= mq[hi]+1e-14))
        # Reuse loss distributions for duplicate baseline shifts without approximating the rule.
        shifts = sorted({v for case in CASES.values() for v in case})
        boot_loss = {v: curve_mae_from_residual_mean(boot-v) for v in shifts}
        point_loss = {v: curve_mae_from_residual_mean(point-v) for v in shifts}
        true_loss = {v: curve_mae_from_residual_mean(known-v) for v in shifts}
        for case, (candidate, growth, persistence) in CASES.items():
            row = store[case]
            for j, baseline in enumerate((growth,persistence)):
                gain = boot_loss[baseline]-boot_loss[candidate]
                interval = np.quantile(gain, [.025,.975], axis=1)
                row["point_gain"][start:stop,j] = point_loss[baseline]-point_loss[candidate]
                row["lower_gain"][start:stop,j] = interval[0]
                row["upper_gain"][start:stop,j] = interval[1]
                row["true_gain"][start:stop,j] = true_loss[baseline]-true_loss[candidate]
            row["success"][start:stop] = np.all(
                (row["point_gain"][start:stop] >= MATERIAL_GAIN)
                & (row["lower_gain"][start:stop] > 0.0), axis=1)
        if stop % 256 == 0 or stop == repetitions:
            print(json.dumps({"construction":name,"done":stop,"repetitions":repetitions}), flush=True)
    result = {"name": name, "repetitions": repetitions,
              "known_finite_population_mean_by_environment": (.5+truth).tolist(),
              "environment_counts": np.bincount(env_index, minlength=len(pools)).tolist(),
              "bootstrap_einsum_check_max_abs": bootstrap_mean_error_max,
              "coverage": {k: rate_interval(int(np.sum(v)), repetitions) for k,v in coverage.items()},
              "absolute_MAE_interval_warning": "Descriptive percentile intervals have a nonregular zero boundary; poor coverage is reported and no absolute-MAE equivalence claim follows.",
              "cases": {}}
    for case,row in store.items():
        count = int(row["success"].sum())
        genuinely_material = np.all(row["true_gain"] >= MATERIAL_GAIN-1e-13, axis=1)
        false_positive = row["success"] & ~genuinely_material
        interval_coverage = np.all((row["lower_gain"]-1e-13 <= row["true_gain"])
                                  & (row["true_gain"] <= row["upper_gain"]+1e-13), axis=1)
        result["cases"][case] = {
            "decision_rate": rate_interval(count,repetitions),
            "false_material_among_all_cohorts": rate_interval(int(false_positive.sum()),repetitions),
            "true_material_cohorts": int(genuinely_material.sum()),
            "true_gain_range": [float(row["true_gain"].min()),float(row["true_gain"].max())],
            "mean_point_gain": row["point_gain"].mean(0).tolist(),
            "joint_gain_interval95_coverage": rate_interval(int(interval_coverage.sum()),repetitions),
        }
    arrays = {"draws":draws,"environment_index":env_index,"mean_errors":np.concatenate(all_mean_residuals),
              "finite_environment_truth_residual":truth}
    for case,row in store.items():
        arrays.update({case+"__"+key:value for key,value in row.items()})
    np.savez_compressed(OUT/(name+"_REPLICATES.npz"),**arrays)
    (OUT/(name+"_RESULT.json")).write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
    return result


def run(repetitions=REPETITIONS):
    t0 = time.perf_counter()
    error, subjects, labs, labels, lab_offsets, description = source_pool()
    plan, path = freeze_plan(repetitions,description)
    counts = bootstrap_counts(COHORT_N)
    rng = np.random.default_rng(SIMULATION_SEED)
    draws = rng.integers(0,len(error),(repetitions,COHORT_N))
    environment = rng.integers(0,len(labels),repetitions)
    primary, primary_description = make_bounded_pool(error,1.0)
    doubled, double_description = make_bounded_pool(error,2.0)
    shifted = np.clip(.5+primary[None,:,:]+lab_offsets[:,None,:],0.0,1.0)-.5
    construction = [
        ("primary_pooled64",primary[None,:,:],np.zeros(repetitions,dtype=np.int64)),
        ("double_variability_bounded",doubled[None,:,:],np.zeros(repetitions,dtype=np.int64)),
        ("shared_empirical_lab_offset",shifted,environment),
    ]
    np.savez_compressed(OUT/"FROZEN_CONTROL_INPUTS.npz",centered_source_residual=error,
                        subjects=subjects,labs=labs,bootstrap_counts=counts,
                        primary_bounded_residual=primary,double_bounded_residual=doubled,
                        shared_lab_offset_bounded_residual=shifted,lab_offsets=lab_offsets,
                        simulation_draws=draws,simulation_environment=environment)
    results = {}
    for name,pools,env in construction:
        print(json.dumps({"start":name,"utc":now()}),flush=True)
        results[name] = evaluate_construction(name,pools,env,draws,counts)
    main = results["primary_pooled64"]["cases"]
    checks = {case:(row["decision_rate"]["rate"] >= .8 if case.startswith("signal_")
                   else row["decision_rate"]["rate"] <= .05) for case,row in main.items()}
    result = {
        "utc":now(), "freeze_sha256":digest(path), "duration_seconds":time.perf_counter()-t0,
        "status":"passed" if all(checks.values()) else "failed_primary_control_requirement",
        "primary_controls_passed":all(checks.values()),"primary_checks":checks,
        "primary_pool_bounding":primary_description,"double_pool_bounding":double_description,
        "lab_offset_bounded_cells":int(np.count_nonzero(shifted != primary[None,:,:]+lab_offsets[:,None,:])),
        "self_test":self_test(),"constructions":results,
        "new_raw_or_external_values_read":False,
        "no_access_release":"This control result cannot itself release protected prefixes or outcomes.",
        "further_fit_or_rule_changes_selected_from_controls":False,
    }
    (OUT/"RESULT.json").write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
    write_report(result)
    manifest={str(p.relative_to(CAMPAIGN)):digest(p) for p in sorted(OUT.iterdir())
              if p.is_file() and p.name != "MANIFEST.json"}
    (OUT/"MANIFEST.json").write_text(json.dumps(manifest,indent=2,sort_keys=True)+"\n")
    print(json.dumps({"status":result["status"],"duration_seconds":result["duration_seconds"]}),flush=True)


def write_report(result):
    lines=["# Frozen comparative-decision controls", "", "2026-10-29. Saved source summaries only; no new trial values or protected data opened.", "",
           "The exact external decision requires a5pp population-curve MAE gain over both baselines and paired95%lower gain>0. Each construction uses2,000independent simulated20-animal cohorts and20,000shared count resamples per cohort. All six bins stay together. Neither thresholds nor methods were tuned from these controls.", "",
           "| Construction/case | Decision rate | Exact MonteCarlo95%interval |", "|---|---:|---:|"]
    for construction,ans in result["constructions"].items():
        for case,row in ans["cases"].items():
            rate=row["decision_rate"];lo,hi=rate["interval95_ClopperPearson"]
            lines.append(f"|{construction}: {case}|{100*rate['rate']:.2f}%|[{100*lo:.2f},{100*hi:.2f}]%|")
    lines += ["",f"Primary controls: **{result['status']}**. Both±10pp signals must have at least80%decision success; every primary null must have at most5%false superiority. Gate thresholds use the prespecified point MonteCarlo rates; exact intervals display finite precision.", "",
              "Primary errors are all64consumed source RNN six-bin residual vectors centered by finite-pool bin means. Each simulated cohort is sampled independently from that pool and is not recentered. Outcomes remain bounded around.5. The doubled construction clips/recenters explicitly; its realized scalarSD multiplier is"+f"{result['double_pool_bounding']['realized_scalar_sd_ratio']:.3f}"+", so it is a bounded variability challenge rather than an exact doubling after clipping.", "",
              "The shared-lab construction adds one empirical lab offset to the whole cohort. Forecasts remain centered on the unconditional mixture, while known conditional environment means and true losses are recomputed from the full bounded pool. Thus nominal signal/null labels need not remain true conditional on each lab offset; the saved result separately counts true material effects and false material decisions.", "",
              "| Construction | Scalar bias90%coverage | Scalar bias95%coverage | Descriptive MAE95%coverage |", "|---|---:|---:|---:|"]
    for construction,ans in result["constructions"].items():
        c=ans["coverage"]
        lines.append(f"|{construction}|{100*c['bias90']['rate']:.2f}%|{100*c['bias95']['rate']:.2f}%|{100*c['mae95']['rate']:.2f}%|")
    lines += ["", "Scalar bias coverage uses the known finite-population mean, conditional on the sampled environment. The saved unconditional coverage additionally shows the failure of animal-only intervals to capture an unmodeled shared environmental shift. Absolute-MAE and gain intervals are nonregular when a forecast has exactly zero population loss; percentile intervals can undercover there. They are reported as diagnostics and cannot establish absolute-error equivalence. The known-answer decision sensitivity/specificity, rather than nominal absolute-loss coverage, is the frozen readiness question.", "",
              "No previous failed gate was changed. A failed control criterion stops this implementation branch before Panprefixes; it is not evidence against transferable learning. Even a passing control would require the separately justified access condition, source-readiness check and full prescription freeze before any external prefix.", ""]
    (OUT/"REPORT.md").write_text("\n".join(lines))


if __name__ == "__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("--freeze-only",action="store_true")
    args=parser.parse_args()
    if args.freeze_only:
        error, subjects, labs, labels, offsets, desc = source_pool()
        plan,path=freeze_plan(REPETITIONS,desc)
        print(json.dumps({"freeze":str(path),"sha256":digest(path),"self_test":self_test()}))
    else:
        run()
