"""Inspect the pooling design using archived aggregates and synthetic laws only."""

import json
import math
import resource


RAW_GAP = 0.012098
HALF_GAP = RAW_GAP / 2
OLD = {
    "recent100": {"M": 0.031705649496248836, "V": 0.02012864687544292,
                  "B": 0.019664138758065, "S": 0.14730543963821832},
    "GRU975": {"M": 0.03555914464527628, "V": 0.005782112182309936,
               "B": 0.0077047725031700485, "S": 0.13681240009411277},
}
LATER = {
    "recent100": {"B": 0.025057, "S": 0.161386, "bias": -0.04149},
    "GRU975": {"B": 0.013171, "S": 0.137402, "bias": 0.00652},
}
TARGET_MEAN = 0.60251


def gain(variation, matching, weight):
    return weight * ((2 - weight) * variation - matching)


def best_weight(variation, matching):
    return max(0, min(1, 1 - matching / (2 * variation))) if variation else 0


def binary_moments(probabilities, outcomes, length):
    mean_p = sum(probabilities) / len(probabilities)
    mean_y = sum(outcomes) / len(outcomes)
    variation = length * sum((p - mean_p)**2 for p in probabilities) / len(probabilities)
    mismatch = length * (mean_p - mean_y)**2
    matching = 2 * length * sum(
        (p - mean_p) * (y - mean_y) for p, y in zip(probabilities, outcomes)
    ) / len(probabilities)
    direct_risk = length * sum((p - y)**2 for p, y in zip(probabilities, outcomes)) / len(outcomes)
    return {"V": variation, "M": mismatch, "B": matching, "raw": direct_risk}


def opposed_law(length, source_weights):
    # Four equally likely synthetic types. The forecast is constant within type.
    # Target supports are centered at the archived scalar target mean.
    outcomes = (0, 0, 1, 1)
    target_variation = length / 4
    support = [TARGET_MEAN - length / 2, TARGET_MEAN + length / 2]
    assert 0 <= support[0] <= support[1] <= 1
    result = {}
    for actor, info in LATER.items():
        mismatch = info["bias"]**2 / length
        variation = info["S"] - target_variation - mismatch
        mean_p = 0.5 + info["bias"] / length
        matched_offset = info["B"] / length
        unmatched_offset = math.sqrt(variation / length - matched_offset**2)
        probabilities = [
            mean_p + matched_offset * (2 * y - 1) + unmatched_offset * s
            for y, s in zip(outcomes, (-1, 1, -1, 1))
        ]
        assert all(0 <= p <= 1 for p in probabilities)
        moments = binary_moments(probabilities, outcomes, length)
        assert abs(moments["B"] - info["B"]) < 1e-12
        assert abs(moments["M"] + moments["V"] + target_variation - info["S"]) < 1e-12
        assert abs(moments["raw"] - (info["S"] - info["B"])) < 1e-12
        weight = source_weights[actor]
        pooled_probabilities = [(1 - weight) * p + weight * mean_p for p in probabilities]
        pooled = binary_moments(pooled_probabilities, outcomes, length)
        assert abs(moments["raw"] - pooled["raw"] - gain(variation, info["B"], weight)) < 1e-12
        assert abs(length * (sum(probabilities) / 4 - 0.5) - info["bias"]) < 1e-12
        result[actor] = {
            **moments, "probabilities_of_upper_atom": probabilities,
            "source_weight_gain": moments["raw"] - pooled["raw"],
            "oracle_gain": gain(variation, info["B"], best_weight(variation, info["B"])),
        }
    ordinary, rich = result["recent100"], result["GRU975"]
    common_variation = min(ordinary["V"], rich["V"])
    case_advantage = (
        math.sqrt(common_variation / rich["V"]) * rich["B"]
        - math.sqrt(common_variation / ordinary["V"]) * ordinary["B"]
    )
    return {
        "support": support, "target_variation": target_variation, "actors": result,
        "matched_weight_residual": RAW_GAP - ordinary["source_weight_gain"] + rich["source_weight_gain"],
        "equal_variation_rich_case_advantage": case_advantage,
    }


weights = {}
old_result = {}
for actor, info in OLD.items():
    variation, matching = info["V"], info["B"]
    weight = best_weight(variation, matching)
    weights[actor] = weight
    old_result[actor] = {
        "weight": weight,
        "full_pool_gain": gain(variation, matching, 1),
        "best_constant_weight_gain": gain(variation, matching, weight),
    }

matching = LATER["recent100"]["B"]
weight = weights["recent100"]
oracle_variation_gate = (matching + HALF_GAP + math.sqrt(HALF_GAP * (2 * matching + HALF_GAP))) / 2
frozen_variation_gate = (HALF_GAP / weight + matching) / (2 - weight)
assert abs(gain(oracle_variation_gate, matching, best_weight(oracle_variation_gate, matching)) - HALF_GAP) < 1e-12
assert abs(gain(frozen_variation_gate, matching, weight) - HALF_GAP) < 1e-12

examples = {"low_gain": opposed_law(0.546, weights), "high_gain": opposed_law(0.50, weights)}
assert examples["low_gain"]["actors"]["recent100"]["oracle_gain"] < HALF_GAP
assert examples["high_gain"]["actors"]["recent100"]["source_weight_gain"] > HALF_GAP

# Same matching covariance, different raw variation and mean mismatch.
control = {
    "ordinary": binary_moments((0, 0.8, 0.2, 1), (0, 0, 1, 1), 1),
    "rich": binary_moments((0.45, 0.45, 0.65, 0.65), (0, 0, 1, 1), 1),
}
assert abs(control["ordinary"]["B"] - control["rich"]["B"]) < 1e-12
for info in control.values():
    info["identity_gain"] = gain(info["V"], info["B"], 0)
    info["full_pool_gain"] = gain(info["V"], info["B"], 1)
    assert info["identity_gain"] == 0
    assert abs(info["raw"] - info["full_pool_gain"] - (info["M"] + 0.25)) < 1e-12

# Exchangeable-ICC illustration with the two Churchland labels merged.
min_cluster_square_sum = 85**2 + 31**2 + 76**2 / 8
effective_n_upper = {
    str(icc): 192 / (1 + (min_cluster_square_sum / 192 - 1) * icc)
    for icc in (0.01, 0.05)
}
record = {
    "input_sources": {
        "old": "../acquisition-calibration-envelope-2026-11-05/CALCULATIONS.json, actual_matching aggregates",
        "later": "../independent-confirmation-result-2026-11-05/REVIEW.md, rounded aggregates",
    },
    "old_aggregates": OLD,
    "later_aggregates": LATER,
    "material_gain": HALF_GAP,
    "old_pooling": old_result,
    "later_recent100_V_gate_oracle": oracle_variation_gate,
    "later_recent100_V_gate_old_weight": frozen_variation_gate,
    "later_recent100_gain_at_old_V": gain(OLD["recent100"]["V"], matching, weight),
    "later_V_ratio_gate_for_positive_equal_V_rich_case_term": (matching / LATER["GRU975"]["B"])**2,
    "opposed_population_laws": examples,
    "equal_covariance_control": control,
    "working_ICC_effective_n_uppers": effective_n_upper,
}
usage = resource.getrusage(resource.RUSAGE_SELF)
record["process_usage"] = {
    "cpu_seconds_at_report": usage.ru_utime + usage.ru_stime,
    "peak_rss_bytes_at_report_on_darwin": usage.ru_maxrss,
}
print(json.dumps(record, indent=2))
