"""Author-side independent arithmetic/implementation and contrary checks.

Does not import main.py or alter frozen outputs. No external libraries.
"""
from pathlib import Path
from decimal import Decimal, localcontext
import datetime
import hashlib
import json
import math
import resource
import sys

HERE = Path(__file__).resolve().parent


def run_events(a, b, retention_A, retention_B, schedule, initial=(0.0, 0.0)):
    xa, xb = initial
    values, rows = [], []
    for task in schedule:
        if task == "A":
            values.append(xa)
            rows.append([task, xa])
            xa = a + (1 - a) * xa
            xb = retention_B * xb
        else:
            values.append(xb)
            rows.append([task, xb])
            xb = b + (1 - b) * xb
            xa = retention_A * xa
    return sum(values) / len(values), xa, xb, rows


def allowed(k):
    return [(n, m) for n in range(2, 3 + k) for m in range(2, 3 + k) if n + m - 4 <= k]


def local_rate(n, endpoint=.75):
    return 1 - (1 - endpoint) ** (1.0 / n)


def targets_at(k, r):
    v = []
    for n, m in allowed(k):
        if r < .75 * (.5 ** m) or r > .75:
            continue
        retention = (r / .75) ** (1 / m)
        pred = run_events(local_rate(n), local_rate(m), retention, retention, "AB" * 6)[0]
        v.append((pred, n, m, retention))
    return v


def decimal_prediction(n, m, r):
    with localcontext() as ctx:
        ctx.prec = 80
        one, endpoint = Decimal(1), Decimal(3) / 4
        a = one - ctx.power(one - endpoint, one / n)
        b = one - ctx.power(one - endpoint, one / m)
        rho = ctx.power(Decimal(str(r)) / endpoint, one / m)
        x, y, total = Decimal(0), Decimal(0), Decimal(0)
        for _ in range(6):
            total += x
            x = a + (one - a) * x
            y = rho * y
            total += y
            y = b + (one - b) * y
            x = rho * x
        return str(total / 12), str(rho)


def main():
    started = datetime.datetime.now(datetime.timezone.utc).isoformat()
    raw = (HERE / "BOUNDS.json").read_bytes()
    results = json.loads(raw)
    cfg = json.loads((HERE / "config.json").read_text())
    frozen = json.loads((HERE / "FREEZE.json").read_text())
    actual = {}
    for key, name in (("protocol_sha256", "PROTOCOL.md"), ("config_sha256", "config.json"),
                      ("main_code_sha256", "main.py"), ("first_calculation_sha256", "FIRST_CALCULATION.json")):
        h = hashlib.sha256((HERE / name).read_bytes()).hexdigest()
        assert h == frozen[key]
        actual[name] = h
    assert json.loads((HERE / "FIRST_CALCULATION.json").read_text())["completed_utc"] < frozen["main_started_utc"]
    assert frozen["main_started_utc"] < results["completed_utc"] < started

    # The reference sampler uses direct event updates and independently
    # derives gain/rho from observations; no geometric code is imported.
    grid_tests = []
    for row in results["worst_case_score_return_probe"]:
        k = row["K"]
        low = min(.75 * .5 ** m for _, m in allowed(k))
        probes = {low + (.75 - low) * j / 2000 for j in range(2001)}
        probes.update(.75 * .5 ** m for _, m in allowed(k))
        probes.add(row["best_attaining_observation"]["return_score"])
        maximum, witness = -1.0, None
        for r in sorted(probes):
            vals = targets_at(k, r)
            if not vals:
                continue
            mn, mx = min(vals), max(vals)
            width = mx[0] - mn[0]
            assert width <= row["envelope_upper_bound_on_worst_diameter"] + 2e-10
            if width > maximum:
                maximum = width
                witness = {"return_score": r, "low": mn, "high": mx}
        grid_tests.append({"K": k, "observations_checked": len(probes),
                           "reference_grid_maximum_width": maximum, "witness": witness,
                           "main_attained_width": row["attained_lower_bound_on_worst_diameter"],
                           "main_envelope_upper": row["envelope_upper_bound_on_worst_diameter"]})

    # Reconstruct both extrema at every fixed return observation using
    # Decimal roots and event updates at 80 digits.
    precision = []
    for row in results["fixed_score_return_probe"]:
        for bound in ("lower_witness", "upper_witness"):
            w = row[bound]
            value, rho = decimal_prediction(w["n_A"], w["n_B"], row["return_score"])
            error = abs(float(value) - w["target"])
            rho_error = abs(float(rho) - w["rho"])
            assert error < 1e-14 and rho_error < 1e-14
            precision.append({"K": row["K"], "bound": bound,
                              "target_80digit_from_observation": value,
                              "rho_80digit_from_observation": rho,
                              "target_float_error": error, "rho_float_error": rho_error})

    # Test the calibrated-score enclosures with feasible exact measurement
    # triples, retaining the coupling between the A gain and retention.
    calibration = []
    for row in results["count_plus_return_calibration"]:
        e = row["epsilon"]
        na, nb = row["counts_known"]
        observed_values = []
        for j in range(1001 if e else 1):
            sa = .75 - e + 2 * e * j / (1000 if e else 1)
            for sb in sorted({.75 - e, .75 + e}):
                for r in sorted({cfg["reference_return_score"] - e, cfg["reference_return_score"] + e}):
                    rho = (r / sa) ** (1 / nb)
                    if not .5 <= rho <= 1:
                        continue
                    a, b = local_rate(na, sa), local_rate(nb, sb)
                    score = run_events(a, b, rho, rho, "AB" * 6)[0]
                    assert row["target_lower_enclosure"] - 2e-14 <= score <= row["target_upper_enclosure"] + 2e-14
                    observed_values.append(score)
        calibration.append({"epsilon": e, "feasible_triples_checked": len(observed_values),
                            "grid_attained_width": max(observed_values) - min(observed_values),
                            "main_width_upper": row["diameter_upper_enclosure"]})

    # Highest-value added contrary test: let interference be directional.
    a = b = local_rate(3)
    directional = []
    for retained_b in (.5, 1.0):
        _, _, _, source_a = run_events(a, b, .75, retained_b, "AAA")
        _, xa, xb, source_all = run_events(a, b, .75, retained_b, "AAABBB")
        value, _, _, target_rows = run_events(a, b, .75, retained_b, "AB" * 6)
        # Execute one A teaching event from the actual nonzero source
        # state; verify the B ratio separately from that event simulator.
        _, after_a_A, after_a_B, intervention_trace = run_events(
            a, b, .75, retained_b, "A", initial=(xa, xb))
        assert abs(after_a_B - retained_b * xb) < 1e-14
        recovered_rho_B = after_a_B / xb
        recovered_rho_A = (xa / .75) ** (1 / 3)
        recovered_score = run_events(a, b, recovered_rho_A, recovered_rho_B, "AB" * 6)[0]
        assert abs(recovered_rho_B - retained_b) < 1e-14
        assert abs(recovered_rho_A - .75) < 1e-14
        assert abs(value - recovered_score) < 1e-14
        directional.append({"alpha_A": a, "alpha_B": b,
                            "rho_A_loss_on_B": .75, "rho_B_loss_on_A": retained_b,
                            "source_full_own_score_trace": source_all,
                            "source_score_A_after_A": .75,
                            "source_score_B_after_B": xb,
                            "source_return_score_A_after_B": xa,
                            "source_certificates": [int(score >= .5) for _, score in source_all],
                            "target": value, "target_trace": target_rows,
                            "extra_one_A_intervention_then_B_probe": after_a_B,
                            "extra_intervention_A_final_state": after_a_A,
                            "extra_intervention_pre_score_trace": intervention_trace,
                            "recovered_rho_B": recovered_rho_B,
                            "target_after_parameter_recovery": recovered_score})
    dlow, dhigh = directional
    assert dlow["source_full_own_score_trace"] == dhigh["source_full_own_score_trace"]
    assert dlow["source_return_score_A_after_B"] == dhigh["source_return_score_A_after_B"]
    assert dlow["source_score_B_after_B"] == dhigh["source_score_B_after_B"]
    directional_gap = dhigh["target"] - dlow["target"]
    assert directional_gap > cfg["precision_criterion"]

    # Closed identified zero at K=0, notwithstanding the intentionally
    # retained generic envelope's finite refinement cap.
    zero = results["worst_case_score_return_probe"][0]
    assert zero["K"] == 0 and zero["attained_lower_bound_on_worst_diameter"] == 0
    assert len(allowed(0)) == 1
    known_zero = {"identified_diameter": 0,
                  "reason": "Only counts(2,2); source endpoints identify gains; r=.75*rho^2 uniquely identifies rho.",
                  "generic_main_algorithm_tolerance_met": zero["tolerance_met"],
                  "generic_main_algorithm_active_boxes": zero["active_boxes"],
                  "generic_main_algorithm_upper": zero["envelope_upper_bound_on_worst_diameter"],
                  "generic_main_output_preserved": True}
    primary_summary = {
        "original_certificate_only_K4": results["original_certificate_only"][4],
        "main_source_K4": results["main_source_calibrated"][4],
        "binary_return_K4": results["binary_return_probe_primary_K"],
        "all_successes_logged_source_K4": results["all_successes_logged_contrary"]["source"][4],
        "all_successes_logged_worst_probe_K4": results["all_successes_logged_contrary"]["worst_score_probe"][2],
        "main_strong_alternatives": results["controls"]["strong_alternatives"]}
    output = {"started_utc": started,
              "completed_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
              "frozen_pins_verified": actual,
              "independent_event_grid": grid_tests, "high_precision_roots": precision,
              "calibration_reference": calibration,
              "known_zero_and_generic_algorithm_limit": known_zero,
              "postvalidation_directional_retention": {"attaining_worlds": directional,
                                                        "identified_target_lower": dlow["target"],
                                                        "identified_target_upper": dhigh["target"],
                                                        "diameter": directional_gap,
                                                        "precision_criterion_failed": True,
                                                        "extra_intervention_recovers_missing_direction": True,
                                                        "scope": "Additional sensitivity class only, not a revision of frozen main class."},
              "primary_summaries": primary_summary,
              "resources": {"peak_rss_native": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
                            "platform": sys.platform, "input_bounds_bytes": len(raw),
                            "one_process": True, "threads": 1}}
    (HERE / "REFERENCE_CHECKS.json").write_text(json.dumps(output, indent=2) + "\n")
    print(json.dumps({"completed_utc": output["completed_utc"],
                      "all_checks_passed": True,
                      "reference_observations": sum(z["observations_checked"] for z in grid_tests),
                      "precision_max_error": max(z["target_float_error"] for z in precision),
                      "known_zero": known_zero,
                      "success_complete_source_K4_bounds": {k: primary_summary["all_successes_logged_source_K4"][k]
                                                            for k in ("lower", "upper", "diameter", "count_pairs")},
                      "success_complete_worst_probe_K4": primary_summary["all_successes_logged_worst_probe_K4"],
                      "directional_gap": directional_gap,
                      "directional_target_bounds": [dlow["target"], dhigh["target"]],
                      "extra_intervention_B_scores": [dlow["extra_one_A_intervention_then_B_probe"],
                                                       dhigh["extra_one_A_intervention_then_B_probe"]],
                      "peak_rss_native": output["resources"]["peak_rss_native"]}, indent=2))


if __name__ == "__main__":
    main()
