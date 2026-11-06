"""Frozen comparative statistics; inputs are already-computed animal/bin arrays.

This module performs no data access and does not adopt an access condition.
All six bins travel together whenever an animal or laboratory is resampled.
"""
from __future__ import annotations

import numpy as np

BOOTSTRAP_SEED = 202610291
BOOTSTRAP_REPLICATES = 20000
MATERIAL_GAIN = 0.05


def bootstrap_counts(n, replicates=BOOTSTRAP_REPLICATES, seed=BOOTSTRAP_SEED):
    """Integer multinomial counts, identical to ordered iid index resampling."""
    n, replicates = int(n), int(replicates)
    if n <= 0 or replicates <= 0:
        raise ValueError("Positive resample size and replication count required")
    indices = np.random.default_rng(seed).integers(0, n, (replicates, n))
    counts = np.zeros((replicates, n), dtype=np.int32)
    np.add.at(counts, (np.arange(replicates)[:, None], indices), 1)
    assert np.all(counts.sum(1) == n)
    return counts


def weighted_residual_curves(residual, counts):
    """Mean residual per bin for each resampled cohort, shared finite mask."""
    residual = np.asarray(residual, dtype=np.float64)
    counts = np.asarray(counts)
    if residual.ndim != 2 or residual.shape[1] != 6:
        raise ValueError("Expected animal x six-bin residual array")
    if counts.ndim != 2 or counts.shape[1] != len(residual):
        raise ValueError("Resample counts must match animal count")
    finite = np.isfinite(residual)
    denominator = counts @ finite.astype(np.float64)
    if np.any(denominator == 0):
        raise ValueError("A resampled population bin is empty; no silent imputation")
    return (counts @ np.where(finite, residual, 0.0)) / denominator


def curve_mae_from_residual_mean(residual_mean):
    return np.mean(np.abs(np.asarray(residual_mean)), axis=-1)


def gain_from_residual_means(candidate_residual_mean, baseline_residual_mean):
    return (curve_mae_from_residual_mean(baseline_residual_mean)
            - curve_mae_from_residual_mean(candidate_residual_mean))


def paired_comparison(observed, candidate, baseline, *, counts=None,
                      replicates=BOOTSTRAP_REPLICATES, seed=BOOTSTRAP_SEED):
    """Population-curve MAE gain, rather than mean individual-curve MAE gain."""
    observed, candidate, baseline = np.broadcast_arrays(
        np.asarray(observed, float), np.asarray(candidate, float), np.asarray(baseline, float))
    if observed.ndim != 2 or observed.shape[1] != 6:
        raise ValueError("Expected animal x six-bin arrays")
    if not np.isfinite(candidate).all() or not np.isfinite(baseline).all():
        raise ValueError("Forecasts must remain finite even at missing observed endpoints")
    finite = np.isfinite(observed)
    if not np.all(finite.sum(0)):
        raise ValueError("Empty observed population bin")
    c = np.where(finite, observed - candidate, np.nan)
    b = np.where(finite, observed - baseline, np.nan)
    if counts is None:
        counts = bootstrap_counts(len(observed), replicates, seed)
    cm, bm = np.nanmean(c, 0), np.nanmean(b, 0)
    cg = weighted_residual_curves(c, counts)
    bg = weighted_residual_curves(b, counts)
    gain = gain_from_residual_means(cm, bm)
    bootstrap_gain = gain_from_residual_means(cg, bg)
    lower, upper = np.quantile(bootstrap_gain, [.025, .975])
    return {
        "population_curve_mae_gain": float(gain),
        "gain_interval95": [float(lower), float(upper)],
        "candidate_curve_mae": float(curve_mae_from_residual_mean(cm)),
        "baseline_curve_mae": float(curve_mae_from_residual_mean(bm)),
        "material_point_gain": bool(gain >= MATERIAL_GAIN),
        "positive_lower95": bool(lower > 0.0),
        "comparison_passed": bool(gain >= MATERIAL_GAIN and lower > 0.0),
        "bootstrap_replicates": int(len(counts)), "bootstrap_seed": int(seed),
        "bin_animals": finite.sum(0).tolist(),
    }


def bias_and_error_intervals(observed, predicted, *, counts=None,
                             replicates=BOOTSTRAP_REPLICATES, seed=BOOTSTRAP_SEED):
    observed, predicted = np.broadcast_arrays(np.asarray(observed, float), np.asarray(predicted, float))
    if observed.ndim != 2 or observed.shape[1] != 6 or not np.isfinite(predicted).all():
        raise ValueError("Finite forecast with animal x six-bin shape required")
    residual = np.where(np.isfinite(observed), observed - predicted, np.nan)
    if counts is None:
        counts = bootstrap_counts(len(observed), replicates, seed)
    mean_curve = np.nanmean(residual, axis=0)
    boot = weighted_residual_curves(residual, counts)
    scalar = boot.mean(1)
    mae = curve_mae_from_residual_mean(boot)
    return {
        "scalar_bias": float(mean_curve.mean()),
        "bias_interval90": np.quantile(scalar, [.05, .95]).tolist(),
        "bias_interval95": np.quantile(scalar, [.025, .975]).tolist(),
        "curve_mae": float(curve_mae_from_residual_mean(mean_curve)),
        "curve_mae_percentile_interval90": np.quantile(mae, [.05, .95]).tolist(),
        "curve_mae_percentile_interval95": np.quantile(mae, [.025, .975]).tolist(),
        "curve_mae_interval_warning": "Absolute MAE is nonregular at zero; these descriptive percentile intervals are not calibrated equivalence bounds.",
        "max_absolute_bin_bias": float(np.abs(mean_curve).max()),
        "bias_curve": mean_curve.tolist(),
    }


def external_decision(observed, candidate, growth, persistence, *,
                      replicates=BOOTSTRAP_REPLICATES, seed=BOOTSTRAP_SEED):
    observed = np.asarray(observed, float)
    counts = bootstrap_counts(len(observed), replicates, seed)
    comparisons = {
        "growth": paired_comparison(observed, candidate, growth, counts=counts, seed=seed),
        "persistence": paired_comparison(observed, candidate, persistence, counts=counts, seed=seed),
    }
    return {
        "primary_success": all(x["comparison_passed"] for x in comparisons.values()),
        "comparisons": comparisons,
        "candidate_absolute_error": bias_and_error_intervals(observed, candidate, counts=counts, seed=seed),
        "n": len(observed), "bootstrap_replicates": int(replicates), "bootstrap_seed": int(seed),
        "material_gain": MATERIAL_GAIN,
        "scope": "Animal uncertainty within the selected single-environment mixture; no environment-sampling uncertainty.",
    }


def equal_lab_comparison(observed, candidate, baseline, labs, *,
                         replicates=BOOTSTRAP_REPLICATES, seed=BOOTSTRAP_SEED):
    """Development screen: average each lab's population-curve MAE equally."""
    observed, candidate, baseline = np.broadcast_arrays(
        np.asarray(observed, float), np.asarray(candidate, float), np.asarray(baseline, float))
    labs = np.asarray(labs).astype(str)
    if observed.shape != candidate.shape or observed.ndim != 2 or observed.shape[1] != 6:
        raise ValueError("Expected animal x six-bin arrays")
    if len(labs) != len(observed) or not np.isfinite(candidate).all() or not np.isfinite(baseline).all():
        raise ValueError("Invalid lab mapping or forecasts")
    labels = sorted(set(labs))
    lab_rows = {}
    for lab in labels:
        valid = np.isfinite(observed[labs == lab])
        c = np.where(valid, observed[labs == lab] - candidate[labs == lab], np.nan)
        b = np.where(valid, observed[labs == lab] - baseline[labs == lab], np.nan)
        if np.any(valid.sum(0) == 0):
            raise ValueError("An entire lab/bin is missing")
        lab_rows[lab] = {
            "n": int((labs == lab).sum()),
            "candidate_curve_mae": float(curve_mae_from_residual_mean(np.nanmean(c, 0))),
            "baseline_curve_mae": float(curve_mae_from_residual_mean(np.nanmean(b, 0))),
        }
        lab_rows[lab]["gain"] = lab_rows[lab]["baseline_curve_mae"] - lab_rows[lab]["candidate_curve_mae"]
    gains = np.array([lab_rows[lab]["gain"] for lab in labels])
    counts = bootstrap_counts(len(labels), replicates, seed)
    resampled = counts @ gains / len(labels)
    return {
        "macro_lab_gain": float(gains.mean()),
        "gain_interval95": np.quantile(resampled, [.025, .975]).tolist(),
        "candidate_macro_lab_curve_mae": float(np.mean([x["candidate_curve_mae"] for x in lab_rows.values()])),
        "baseline_macro_lab_curve_mae": float(np.mean([x["baseline_curve_mae"] for x in lab_rows.values()])),
        "labs": lab_rows,
        "leave_one_lab_out_gain": {lab: float(np.delete(gains, i).mean()) for i, lab in enumerate(labels)} if len(labels) > 1 else {},
        "bootstrap_replicates": int(replicates), "bootstrap_seed": int(seed),
        "scope": "Consumed-source robustness screen; laboratory resampling does not certify arbitrary-environment performance.",
    }


def self_test():
    rng = np.random.default_rng(81)
    y = .5 + rng.normal(0, .02, (20, 6))
    counts = bootstrap_counts(20, 137, 412)
    ix = np.random.default_rng(412).integers(0, 20, (137, 20))
    direct = y[ix].mean(1)
    weighted = weighted_residual_curves(y, counts)
    difference = float(np.max(np.abs(direct - weighted)))
    assert difference < 1e-14
    zero = np.full((20, 6), .5)
    good = external_decision(zero, zero, zero+.10, zero-.10, replicates=137)
    assert good["primary_success"]
    null = external_decision(zero, zero, zero, zero, replicates=137)
    assert not null["primary_success"]
    missing = y.copy(); missing[0, 0] = np.nan
    assert np.isfinite(paired_comparison(missing, zero, zero+.10, counts=counts)["population_curve_mae_gain"])
    return {"count_vs_index_max_abs": difference, "deterministic_good_passes": True,
            "identical_forecasts_do_not_pass": True, "shared_missing_mask_checked": True}


if __name__ == "__main__":
    import json
    print(json.dumps(self_test(), sort_keys=True))
