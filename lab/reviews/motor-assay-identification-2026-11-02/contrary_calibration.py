"""ONE predeclared calibration challenge; exact identities, no human data."""
from fractions import Fraction as F
from datetime import datetime, timezone
from pathlib import Path
import json
import math
import resource

HERE = Path(__file__).resolve().parent


def logistic(z):
    return 1 / (1 + math.exp(-float(z)))


def run():
    X, b, retention, margin = F(3, 2), F(1, 5), F(97, 100), F(1, 5)
    factors = [retention ** j for j in range(5)]
    M = sum(factors) / 5
    delta = margin / (X * M)
    B = margin / (4 * b * M)
    scale, button_bias = F(3), F(17, 100)
    probes = [F(-20), F(-10), F(-333, 100), F(333, 100), F(10), F(20)]
    catches = [F(-1), F(0), F(1)]
    cases = []
    all_hand_gaps, shared_catch_gaps, retained_catch_gaps = [], [], []
    numerical_k_errors, retained_hand_gaps = [], []
    exact_checks = 0
    for s in (-1, 1):
        a = [[F(17, 20), F(17, 20)],
             [F(17, 20) - s * delta / 2, F(17, 20) + s * delta / 2]]
        observable = [F(7, 10), F(7, 10) + s * delta]
        recovered = [[], []]
        midpoint_recovered = []
        for event in (0, 1):
            local_recovered = [[], []]
            local_midpoint = []
            for x in (-X, X):
                for c in (F(-1), F(0), F(1)):
                    y = observable[event] * x + b * c
                    e = [(y - a[w][event] * x) / b for w in (0, 1)]
                    R = sum(e) / 2
                    q = [R - t for t in e]
                    assert q[0] == -q[1]
                    assert abs(q[0]) == B
                    # Calibrate a shared k and the logit scale from known catches.
                    k_hat = []
                    for w in (0, 1):
                        catch_logit = lambda g, m: (m * (g + q[w]) + button_bias) / scale
                        measured_slope = (catch_logit(F(1), 1) - catch_logit(F(-1), 1)) / 2
                        k = (catch_logit(F(0), 1) - catch_logit(F(0), -1)) / (2 * measured_slope)
                        d = (catch_logit(F(0), 1) + catch_logit(F(0), -1)) / (2 * measured_slope)
                        assert k == q[w] and d == button_bias
                        assert 1 / measured_slope == scale
                        k_hat.append(k)
                        # Same recovery from float response probabilities.
                        logit = lambda p: math.log(p / (1 - p))
                        plus = lambda g: logit(logistic(catch_logit(g, 1)))
                        slope_float = (plus(F(1)) - plus(F(-1))) / 2
                        k_float = (plus(F(0)) - logit(logistic(catch_logit(F(0), -1)))) / (2 * slope_float)
                        numerical_k_errors.append(abs(k_float - float(k)))
                        a_recovered = (y - b * (R - k)) / x
                        assert a_recovered == a[w][event]
                        local_recovered[w].append(a_recovered)
                    local_midpoint.append((y - b * R) / x)
                    for mapping in (-1, 1):
                        for v in probes:
                            # Hypothesis A: q is all a common criterion.
                            z = [(mapping * (e[w] + k_hat[w] - v) + button_bias) / scale
                                 for w in (0, 1)]
                            assert z[0] == z[1]
                            all_hand_gaps.append(abs(logistic(z[0]) - logistic(z[1])))
                            # Hypothesis B: shared k is calibrated at zero, but
                            # hand-specific u=q. Same observation function.
                            z_u = [(mapping * (e[w] + q[w] + F(0) - v) + button_bias) / scale
                                   for w in (0, 1)]
                            assert z_u[0] == z_u[1] == z[0]
                            retained_hand_gaps.append(abs(logistic(z_u[0]) - logistic(z_u[1])))
                            exact_checks += 2
                        for g in catches:
                            z_shared = [(mapping * (g + q[w]) + button_bias) / scale
                                        for w in (0, 1)]
                            assert abs(z_shared[0] - z_shared[1]) == 2 * B / scale
                            shared_catch_gaps.append(abs(logistic(z_shared[0]) - logistic(z_shared[1])))
                            z_retained = [(mapping * (g + F(0)) + button_bias) / scale for w in (0, 1)]
                            assert z_retained[0] == z_retained[1]
                            retained_catch_gaps.append(abs(logistic(z_retained[0]) - logistic(z_retained[1])))
                            exact_checks += 2
            for w in (0, 1):
                assert len(set(local_recovered[w])) == 1
                recovered[w].append(local_recovered[w][0])
            assert len(set(local_midpoint)) == 1
            midpoint_recovered.append(local_midpoint[0])
        corrected_curves = [[X * (aa[1] - aa[0]) * r for r in factors] for aa in recovered]
        corrected_means = [sum(curve) / 5 for curve in corrected_curves]
        assert corrected_means == [0, s * margin]
        retained_mean = X * M * (midpoint_recovered[1] - midpoint_recovered[0])
        assert retained_mean == s * margin / 2
        cases.append({"sign": s,
                      "calibrated_shared_criterion_transition_curves": [list(map(float, v)) for v in corrected_curves],
                      "calibrated_shared_criterion_transition_means": list(map(float, corrected_means)),
                      "same_calibration_with_hand_specific_mismatch_naive_mean": float(retained_mean),
                      "true_means_in_indistinguishable_augmented_worlds": [0.0, float(s * margin)]})
    result = {"generated_utc": datetime.now(timezone.utc).isoformat(),
              "predeclaration": "CONTRARY_PREDECLARATION.md",
              "test": "known all-visual catches plus response-mapping reversal",
              "both_signed_boundaries": True,
              "exact_identity_checks": exact_checks,
              "ordinary_hand_max_probability_gap": max(all_hand_gaps),
              "shared_criterion_only": {
                  "augmented_world_equality": False,
                  "minimum_catch_probability_gap_on_declared_grid": min(shared_catch_gaps),
                  "maximum_catch_probability_gap_on_declared_grid": max(shared_catch_gaps),
                  "catch_logit_separation_absolute": float(2 * B / scale),
                  "max_numerical_criterion_recovery_error_degrees": max(numerical_k_errors),
                  "criterion_and_logit_scale_exactly_recovered": True,
                  "conclusion": "The added calibration excludes a wholly shared spatial/response criterion rival."},
              "hand_specific_signal_mismatch_allowed": {
                  "augmented_world_equality": True,
                  "maximum_hand_probability_gap": max(retained_hand_gaps),
                  "maximum_catch_probability_gap": max(retained_catch_gaps),
                  "shared_criterion": 0,
                  "common_button_bias": float(button_bias),
                  "required_hand_specific_mismatch_radius_degrees": float(B),
                  "conclusion": "Catch calibration cannot test its transfer to the hand-report/learning-signal relation."},
              "cases": cases,
              "logistic_scale_degrees_supplied_not_empirical": float(scale),
              "no_empirical_power_coverage_or_people": True,
              "max_rss_bytes_macos": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss}
    (HERE / "CONTRARY.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({k: result[k] for k in ("generated_utc", "exact_identity_checks",
                     "shared_criterion_only", "hand_specific_signal_mismatch_allowed", "max_rss_bytes_macos")}))


if __name__ == "__main__":
    run()
