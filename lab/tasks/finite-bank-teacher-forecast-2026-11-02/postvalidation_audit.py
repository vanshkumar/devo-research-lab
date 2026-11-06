"""Numerical audit of saved data only; does not rerun or revise the forecast."""
from datetime import datetime, timezone
from pathlib import Path
import hashlib
import json
import math
import resource
import numpy as np

HERE = Path(__file__).resolve().parent
NFORECAST = 65536
TARGET = 62.5
Z99 = 2.5758293035489004


def describe(x):
    point = float(np.mean(x))
    se = float(np.std(x, ddof=1)/math.sqrt(len(x)))
    return {"estimate":point, "MCSE":se, "MC99":[point-Z99*se, point+Z99*se]}


def main():
    frozen = json.loads((HERE/"FREEZE.json").read_text())
    for name, pin in frozen["files"].items():
        assert hashlib.sha256((HERE/name).read_bytes()).hexdigest() == pin
    out = {"utc":datetime.now(timezone.utc).isoformat(), "scope":"postvalidation numerical reliability of saved experiments only",
           "frozen_files_unchanged":True, "new_simulations":0, "new_fits":0, "gate_revisions":0}
    with np.load(HERE/"EXPERIMENTS.npz", allow_pickle=False) as f:
        totals = f["totals"].astype(float)
        expected = f["expected"]
        condvar = f["uniform_condvar"]
        params = f["params"]
        bankmean = f["bank_mean"]
    assert totals.shape == (131072, 3, 2)
    assert np.all((totals >= 0) & (totals <= 125))
    assert np.all(np.isfinite(expected))
    assert np.all((params[:, 0] >= 0) & (params[:, 0] <= 20))
    assert np.all((params[:, 1:4] >= 0) & (params[:, 1:4] <= 1))
    assert np.all(np.abs(params[:, 4:]) <= 20)
    out["parameter_support_and_count_bounds_pass"] = True
    out["uniform_known_answer"] = {}
    for j, law in enumerate(["source_bank", "fresh_iid", "Gaussian_common_mean"]):
        # Total variance law using the independently known symmetry mean62.5.
        conditional_second_moment = (expected[:, j, 1]-TARGET)**2 + condvar[:, j]
        realized_second_moment = (totals[:, j, 1]-TARGET)**2
        difference = describe(realized_second_moment-conditional_second_moment)
        symmetry = describe(expected[:, j, 1]-TARGET)
        assert difference["MC99"][0] <= 0 <= difference["MC99"][1]
        assert symmetry["MC99"][0] <= 0 <= symmetry["MC99"][1]
        out["uniform_known_answer"][law] = {"exact_ensemble_mean":TARGET,
            "Rao_Blackwell_mean_minus_exact":symmetry,
            "reward_second_moment_minus_conditional_identity":difference,
            "conditional_total_variance_estimate":float(np.mean(conditional_second_moment))}
    # Each empirical evaluation CDF is uniformly within epsilon with probability
    # >= .995 by DKW. A union bound gives >=.99 for the two laws, even though
    # the paired laws are correlated. Subtracting two interval probabilities
    # costs 4epsilon; it holds for any cutoffs, including estimated cutoffs.
    epsilon = math.sqrt(math.log(400)/(2*NFORECAST))
    cuts = np.quantile(totals[:NFORECAST, 1, 0], [.05,.95], method="inverted_cdf")
    ev = totals[NFORECAST:, :, 0]
    cover = (ev >= cuts[0]) & (ev <= cuts[1])
    difference = float(np.mean(cover[:, 0].astype(float)-cover[:, 1].astype(float)))
    out["conservative_uniform_CDF_MC_bound"] = {"method":"two-law DKW + union bound, postvalidation reliability check",
        "confidence":.99, "epsilon_per_CDF":epsilon,
        "coverage_difference":difference, "coverage_difference_bound":[difference-4*epsilon, difference+4*epsilon],
        "absolute_upper_bound":abs(difference)+4*epsilon,
        "under_original_five_pp_boundary":abs(difference)+4*epsilon < .05,
        "quantile_estimation_not_required_for_uniform_bound":True}
    out["bank_mean_known_SD"] = .025/math.sqrt(1000)
    out["bank_mean_observed_SD"] = float(np.std(bankmean))
    out["maxrss_bytes_darwin"] = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    out["compressed_input_bytes"] = (HERE/"EXPERIMENTS.npz").stat().st_size
    out["decoded_array_bytes_including_float_conversion"] = totals.nbytes+expected.nbytes+condvar.nbytes+params.nbytes+bankmean.nbytes
    out["exit_code"] = 0
    (HERE/"POSTVALIDATION_AUDIT.json").write_text(json.dumps(out, indent=2)+"\n")
    print(json.dumps(out, indent=2))


if __name__ == "__main__":
    main()
