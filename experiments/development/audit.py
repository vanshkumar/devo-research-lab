#!/usr/bin/env python3
"""Independent analytic checks of two synthetic pilots (standard library only)."""
import csv
from fractions import Fraction as F
import json
import math
from pathlib import Path

HERE = Path(__file__).resolve().parent


def phi(x):
    return 0.5 * (1 + math.erf(x / math.sqrt(2)))


def analytic_accuracy(b, core, short, p):
    sd = math.sqrt(core ** 2 + (0.25 * short) ** 2)
    return 0.5 * sum(p * phi((ys * b + core + short) / sd) +
                     (1 - p) * phi((ys * b + core - short) / sd)
                     for ys in [-1, 1])


def main():
    with (HERE / "results/curriculum.csv").open() as f:
        rows = list(csv.DictReader(f))
    analytic_rows = []
    for row in rows:
        a = analytic_accuracy(float(row["w_intercept"]), float(row["w_core"]),
                              float(row["w_shortcut"]), float(row["test_shortcut_agreement"]))
        observed = float(row["accuracy"])
        error = observed - a
        analytic_rows.append({"seed": int(row["seed"]), "schedule": row["schedule"],
                              "stage": row["stage"],
                              "test_shortcut_agreement": float(row["test_shortcut_agreement"]),
                              "analytic_accuracy": a, "sample_accuracy": observed,
                              "sample_minus_analytic": error,
                              "absolute_error_in_binomial_SE": abs(error) / math.sqrt(a * (1-a) / 10000)})
    with (HERE / "results/analytic_accuracy.csv").open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(analytic_rows[0]))
        writer.writeheader()
        writer.writerows(analytic_rows)

    # Exact rational arithmetic independent of NumPy simulation/enumeration.
    joint = {(t, y): F(0) for t in [0, 1] for y in [0, 1]}
    for u in [0, 1]:
        for t in [0, 1]:
            for y in [0, 1]:
                joint[t, y] += F(1, 2) * (F(4, 5) if t == u else F(1, 5)) * (F(9, 10) if y == u else F(1, 10))
    direct = {(0, 0): F(37, 100), (0, 1): F(13, 100),
              (1, 0): F(13, 100), (1, 1): F(37, 100)}
    assert joint == direct
    observed_gap = joint[1, 1] / (joint[1, 0] + joint[1, 1]) - joint[0, 1] / (joint[0, 0] + joint[0, 1])
    assert observed_gap == F(12, 25)
    summary = {
        "rational_joint_equal_exactly": joint == direct,
        "joint_T_Y": {str(k): str(v) for k, v in joint.items()},
        "observational_gap_exact": str(observed_gap),
        "selection_world_ATE_exact": "0", "direct_world_ATE_exact": "12/25",
        "analytic_core_oracle_accuracy": phi(1),
        "max_sample_analytic_accuracy_difference": max(abs(r["sample_minus_analytic"]) for r in analytic_rows),
        "max_absolute_accuracy_error_in_binomial_SE": max(r["absolute_error_in_binomial_SE"] for r in analytic_rows),
        "rows_above_3_binomial_SE": sum(r["absolute_error_in_binomial_SE"] > 3 for r in analytic_rows),
        "number_of_accuracy_rows": len(analytic_rows),
        "note": "Rows share test data and weights, so counts of deviations are descriptive, not independent hypothesis tests."
    }
    (HERE / "results/analytic_audit.json").write_text(json.dumps(summary, indent=2) + "\n")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
