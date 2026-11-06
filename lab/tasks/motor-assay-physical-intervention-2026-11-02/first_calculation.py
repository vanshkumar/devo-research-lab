"""Source-constrained causal chronology and transition/error reference.

Standard library only. No empirical data, imports of old models, or source access.
The calculation challenges delay + no-cursor next-probe as an exclusion device.
"""
from fractions import Fraction as F
from pathlib import Path
import datetime
import hashlib
import json
import resource

ROOT = Path(__file__).resolve().parent
raw = (ROOT / "PROTOCOL_INPUTS.json").read_bytes()
protocol = json.loads(raw)
honda = protocol["honda_2012_delay_program"]
brudner = protocol["brudner_2016_endpoint_program"]
assert not honda["probe_cursor_present"]
assert brudner["remain_at_endpoint_until_feedback_ends"]
actual_delays = [honda["reported_system_delay_ms"] + d
                 for d in honda["additional_delay_ms"]]
assert actual_delays == [60, 160, 260, 360]

# A source-constrained causal fact, not an invented exact trial clock:
# the next target follows completion of the delayed cursor, return, and a hold.
# Unknown return, reaction, and movement times only increase this lower bound.
timing = {
    "honda_physical_cursor_delays_ms": actual_delays,
    "honda_cursor_to_next_target_lower_bound_ms": honda["start_hold_ms"],
    "honda_measurement": honda["observation"],
    "honda_previous_perturbation_delivered_before_probe": [True] * 4,
    "honda_own_probe_visual_error_absent": True,
    "honda_neural_processing_complete": "NOT certified by delivery order alone",
    "brudner_earliest_nominal_next_target_after_terminal_crossing_ms": [
        d + brudner["error_display_duration_ms"] + brudner["robot_start_hold_ms"]
        for d in brudner["nominal_error_delay_ms"]
    ],
    "brudner_omitted_from_lower_bound": "robot return time, reaction time, display lag and movement time",
    "brudner_current_heading_precedes_terminal_feedback":
        max(brudner["initial_heading_referent_radii_cm"]) < brudner["terminal_radius_cm"],
    "early_probe_before_delayed_feedback_supported_by_source": False,
}

# Grant an observer MORE information than the source provides: exact precursor
# X and exact programmed signed perturbation U. A physical cursor offset is
# not the internal prediction error. A local model is E=U-c*X.
# In a delay cell the observable row is [X,U], with coefficients
# (a-b*c,b). Its Jacobian has a null direction (b,0,1) for (a,b,c).
# This is a structural equality, not a fitted or biologically measured c.
a, b, c = F(97, 100), F(1, 5), F(1, 2)
shift = F(1, 20)
rows = []
max_gap = F(0)
null_gaps = []
for d in actual_delays:
    for X in (F(-3, 2), F(3, 2)):
        for U in map(F, honda["perturbation_angle_degrees"]):
            # World T attributes +shift*X to altered intrinsic transition.
            y_transition = (a + shift) * X + b * (U - c * X)
            # World E keeps a unchanged and alters predicted-error loading.
            c_error = c - shift / b
            y_error = a * X + b * (U - c_error * X)
            assert y_transition == y_error
            # Independently multiply the three Jacobian entries by the null
            # vector. Both signed U values and all delay cells remain equal.
            derivative = X * b + (U - c * X) * 0 + (-b * X) * 1
            assert derivative == 0
            null_gaps.append(derivative)
            max_gap = max(max_gap, abs(y_transition - y_error))
            rows.append({"physical_delay_ms": d, "X": str(X), "U": str(U),
                         "Y_transition": str(y_transition), "Y_error": str(y_error)})

# The alternate scalar check eliminates the error variable FIRST, independent
# of the two world update expressions above. It verifies the coefficient pair.
coefficient_T = (a + shift - b * c, b)
coefficient_E = (a - b * (c - shift / b), b)
assert coefficient_T == coefficient_E

# Timing can exclude a response before a particular visual signal arrives,
# but it excludes both mechanisms if both are driven by that signal.
# Delay-specific gains may be arbitrary: the invariance is pointwise.
kernel_checks = []
for d in actual_delays:
    for measured_ms in (d - 1, d, d + honda["start_hold_ms"]):
        for kernel in (F(0), F(1, 4), F(1)):
            # Causal gate uses only whether this visual input has arrived.
            w = F(0) if measured_ms < d else kernel
            X, U = F(3, 2), F(10)
            T = a * X + w * (shift * X + b * (U - c * X))
            E = a * X + w * b * (U - (c - shift / b) * X)
            assert T == E
            kernel_checks.append({"delay_ms": d, "measurement_ms": measured_ms,
                                  "supplied_kernel": str(kernel), "gap": str(T - E)})

# Separate storage/expression check. Any observable effective state B=S+Z
# with B_next=A*B+b*U can be represented with ANY storage coefficient q by
# S_next=q*S and Z_next=A*(S+Z)+b*U-q*S. This is not evidence that such a
# biological expression state exists, and no-cursor probes do not anchor S.
A = coefficient_T[0]
expression_checks = []
for S in (F(-1), F(1)):
    for Z in (F(-1, 2), F(0), F(1, 2)):
        for U in map(F, honda["perturbation_angle_degrees"]):
            for q in (F(1, 2), F(97, 100)):
                B = S + Z
                S_next = q * S
                Z_next = A * B + b * U - q * S
                assert S_next + Z_next == A * B + b * U
                expression_checks.append(str(S_next + Z_next - (A * B + b * U)))

out = {
    "status": "PASS: standard source-constrained exclusion check; not a new identifiability theorem",
    "completed_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
    "protocol_input_sha256": hashlib.sha256(raw).hexdigest(),
    "timing": timing,
    "reference_equation": "Y=(a-b*c)*X+b*U; null direction (da,db,dc)=(b,0,1)",
    "supplied_values": {"a": str(a), "b": str(b), "c_T": str(c),
                        "transition_shift": str(shift), "c_E": str(c - shift/b)},
    "source_certifies_these_coefficients": False,
    "crossed_reference_rows": rows,
    "exact_world_max_gap": str(max_gap),
    "independent_eliminated_coefficients_T": list(map(str, coefficient_T)),
    "independent_eliminated_coefficients_E": list(map(str, coefficient_E)),
    "exact_null_checks": len(null_gaps),
    "causal_kernel_checks": kernel_checks,
    "storage_expression_exact_checks": len(expression_checks),
    "biological_interpretation": "UNIDENTIFIED; neither c freedom nor expression state measured",
    "original_point_two_degree_five_probe_scale": "UNCHANGED and not re-estimated; no precision or collection-N claim",
    "empirical_records_accessed": 0,
    "peak_rss_bytes_this_process": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
    "platform_peak_units": "macOS bytes",
}
encoded = json.dumps(out, indent=2) + "\n"
(ROOT / "FIRST_CALCULATION.json").write_text(encoded)
print(json.dumps({"status": out["status"], "completed_utc": out["completed_utc"],
                  "reference_rows": len(rows), "exact_world_max_gap": str(max_gap),
                  "kernel_checks": len(kernel_checks),
                  "expression_checks": len(expression_checks),
                  "peak_rss_bytes": out["peak_rss_bytes_this_process"]}))
