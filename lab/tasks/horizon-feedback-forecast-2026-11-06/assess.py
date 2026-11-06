"""Summarize saved source forecasts in behavior and reward units."""
import json
from pathlib import Path

import numpy as np
from scipy.stats import t


HERE = Path(__file__).resolve().parent
read = lambda name: json.loads((HERE / name).read_text())
data = read("DEVELOPMENT_LOOKAHEAD.json")
rows = list(data["per_person"].values())
models = list(data["summary"]["scores"])


def measure(values):
    values = np.array(values, dtype=float)
    sd = float(values.std(ddof=1))
    return {
        "mean": float(values.mean()),
        "person_sd": sd,
        "planning_95pct_halfwidths": {
            str(n): float(t.ppf(.975, n-1) * sd / n**.5) for n in [6, 25, 30]
        },
    }


def stat(row, model, key):
    s = row["observed_stats"] if model == "observed" else row[model]["stats"]
    if key == "later_reward_per_opportunity":
        return s["mean_later_cumulative_reward"] / 5
    if key == "final_switch_pp":
        return 100 * s["switch_frequency_by_transition"][-1]
    if key == "second_switch_pp":
        return 100 * s["switch_frequency_by_transition"][0]
    if key == "final_less_sampled_pp":
        return 100 * s["fraction_less_sampled_by_step"][-1]
    if key == "always_same_arm_pp":
        return 100 * s["fraction_all_same_arm"]
    if key == "mean_surprise_stay":
        return np.mean(s["reward_surprise_stay_covariation_by_transition"])
    raise KeyError(key)


results = {
    key: {
        "mean_observed": measure([stat(r, "observed", key) for r in rows])["mean"],
        "model_minus_observed": {
            model: measure([stat(r, model, key) - stat(r, "observed", key) for r in rows])
            for model in models
        },
        "model_minus_history": {
            model: measure([stat(r, model, key) - stat(r, "history", key) for r in rows])
            for model in models if model != "history"
        },
    } for key in ["later_reward_per_opportunity", "final_switch_pp", "second_switch_pp",
                  "final_less_sampled_pp", "always_same_arm_pp", "mean_surprise_stay"]
}
results["model_minus_history_joint_score"] = {
    name: measure([r[name]["score"] - r["history"]["score"] for r in rows])
    for name in models if name != "history"
}
last_noise = np.array([r["last_noise_shift_final_switch_reward_I_change"] for r in rows])
results["five_pp_terminal_policy_perturbation"] = {
    "switch_pp": measure(100 * last_noise[:, 0]),
    "last_reward_points": measure(last_noise[:, 1]),
    "final_I_choice_pp": measure(100 * last_noise[:, 2]),
    "expected_score_separation": measure([r["joint_expected_last_noise_shift"] for r in rows]),
    "observed_score_cost": measure([r["observed_score_cost_of_last_noise_shift"] for r in rows]),
}
results["expected_pair_separations"] = {
    "history_vs_posterior": measure([r["joint_expected_score_separation"] for r in rows]),
    "history_vs_lookahead": measure([r["joint_expected_lookahead_separation"] for r in rows]),
}
(HERE / "BEHAVIOR_PRECISION.json").write_text(json.dumps(results, indent=2, allow_nan=False) + "\n")
for label, val in results.items():
    if "model_minus_observed" not in val:
        print(label, val)
        continue
    print(label, "observed", round(val["mean_observed"], 6))
    for model, summary in val["model_minus_observed"].items():
        print(" ", model, "bias / n=6 halfwidth / n=30 halfwidth",
              *(round(v, 6) for v in [summary["mean"], summary["planning_95pct_halfwidths"]["6"],
                                     summary["planning_95pct_halfwidths"]["30"]]))
