"""Independent exact reconstruction. Stdlib; no author code/data imports."""
from fractions import Fraction as F
from datetime import datetime, timezone
from pathlib import Path
import json
import resource

HERE = Path(__file__).resolve().parent


def value(x):
    return {"fraction": str(x), "degrees": float(x)}


def run():
    x_abs, gain, probe = F(3, 2), F(1, 5), F(97, 100)
    margin = F(1, 5)
    multipliers = [probe ** k for k in range(5)]
    average = sum(multipliers) / 5
    da = margin / (x_abs * average)
    radius = margin / (4 * gain * average)
    cases = []
    for direction in (-1, 1):
        observed_a = [F(7, 10), F(7, 10) + direction * da]
        null_a = [F(17, 20)] * 2
        changed_a = [F(17, 20) - direction * da / 2,
                     F(17, 20) + direction * da / 2]
        # Build the reported signal from the midpoint coefficient, then recover
        # each world's required latent error from its own transition equation.
        center_a = [(u + v) / 2 for u, v in zip(null_a, changed_a)]
        rows = []
        for event in (0, 1):
            for precursor in (-x_abs, x_abs):
                for cursor in (F(-1), F(0), F(1)):
                    observed_next = observed_a[event] * precursor + gain * cursor
                    reported = cursor + (observed_a[event] - center_a[event]) * precursor / gain
                    truth = [(observed_next - a[event] * precursor) / gain
                             for a in (null_a, changed_a)]
                    biases = [reported - e for e in truth]
                    paths = [[(a[event] * precursor + gain * e) * p for p in multipliers]
                             for a, e in zip((null_a, changed_a), truth)]
                    assert paths[0] == paths[1]
                    assert max(abs(q) for q in biases) == radius
                    assert all(e + q == reported for e, q in zip(truth, biases))
                    rows.append({"event": event, "precursor": float(precursor),
                                 "cursor": float(cursor), "next": float(observed_next),
                                 "report": float(reported), "truths": list(map(float, truth)),
                                 "biases": list(map(float, biases)),
                                 "probe_path": list(map(float, paths[0]))})
        curve = [direction * da * x_abs * p for p in multipliers]
        true_contributions = [x_abs * average * (a[1] - a[0]) for a in (null_a, changed_a)]
        oracle_report_contribution = x_abs * average * (center_a[1] - center_a[0])
        assert true_contributions == [0, direction * margin]
        assert sum(curve) / 5 == direction * margin
        assert oracle_report_contribution == direction * margin / 2
        assert all(0 < a < 1 for a in null_a + changed_a)
        cases.append({"direction": direction, "observable_curve": list(map(float, curve)),
                      "curve_mean": value(sum(curve) / 5),
                      "true_transition_contributions": list(map(value, true_contributions)),
                      "report_as_truth_contribution": value(oracle_report_contribution),
                      "intrinsic_coefficients": {"null": list(map(float, null_a)),
                                                 "changed": list(map(float, changed_a))},
                      "rows": rows})
    # Derivation independent of witness: |q| <= B for each world implies
    # |error_P - error_N| <= 2B. At x=+X, |a_P,j-a_N,j| <= 2bB/X;
    # thus the event contrast differs by at most 4bMB between worlds.
    assert 4 * gain * average * radius == margin
    result = {"generated_utc": datetime.now(timezone.utc).isoformat(),
              "author_code_imported_or_executed": False,
              "empirical_files_read": 0,
              "average_probe_multiplier": value(average),
              "coefficient_difference": value(da),
              "critical_per_cell_bias": value(radius),
              "single_world_systematic_half_width": value(2 * gain * average * radius),
              "two_world_target_diameter": value(4 * gain * average * radius),
              "exact_rational_equalities": True,
              "matched_crossed_cells": sum(len(c["rows"]) for c in cases),
              "cases": cases,
              "max_rss_bytes_macos": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss}
    (HERE / "FIRST_CALCULATION.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({k: result[k] for k in ("generated_utc", "critical_per_cell_bias",
                     "exact_rational_equalities", "matched_crossed_cells", "max_rss_bytes_macos")}))


if __name__ == "__main__":
    run()
