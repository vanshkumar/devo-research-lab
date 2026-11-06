"""Create compact result tables and local resource/pin records; no science rerun."""
from pathlib import Path
import csv
import datetime
import hashlib
import json
import resource
import sys

HERE = Path(__file__).resolve().parent


def main():
    bounds = json.loads((HERE / "BOUNDS.json").read_text())
    reference = json.loads((HERE / "REFERENCE_CHECKS.json").read_text())
    first = json.loads((HERE / "FIRST_CALCULATION.json").read_text())
    freezes = json.loads((HERE / "FREEZE.json").read_text())
    # Reconfirm actual frozen bytes after documentation/contrary checks.
    for name, key in (("PROTOCOL.md", "protocol_sha256"), ("config.json", "config_sha256"),
                      ("main.py", "main_code_sha256"), ("FIRST_CALCULATION.json", "first_calculation_sha256")):
        assert hashlib.sha256((HERE / name).read_bytes()).hexdigest() == freezes[key]
    with (HERE / "BOUNDS_TABLE.csv").open("w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["K", "source_lower", "source_upper", "source_diameter",
                         "count_audit_worst_diameter", "score_probe_worst_attained",
                         "score_probe_worst_upper", "probe_bound_method"])
        for source, probe in zip(bounds["main_source_calibrated"], bounds["worst_case_score_return_probe"]):
            analytic_zero = source["K"] == 0
            writer.writerow([source["K"], source["lower"], source["upper"], source["diameter"],
                             source["count_audit_worst_diameter"],
                             0 if analytic_zero else probe["attained_lower_bound_on_worst_diameter"],
                             0 if analytic_zero else probe["envelope_upper_bound_on_worst_diameter"],
                             "known-count algebraic zero; generic run cap retained" if analytic_zero else
                             "monotone envelope; floating precision controls"])
    primary = next(z for z in bounds["main_source_calibrated"] if z["K"] == 4)
    probe4 = next(z for z in bounds["worst_case_score_return_probe"] if z["K"] == 4)
    success = next(z for z in bounds["all_successes_logged_contrary"]["worst_score_probe"] if z["K"] == 4)
    asym = reference["postvalidation_directional_retention"]
    designs = [
        ["shared", "certificates only, K4", bounds["original_certificate_only"][4]["diameter"], bounds["original_certificate_only"][4]["diameter"]],
        ["shared", "two calibrated source endpoints, K4", primary["diameter"], primary["diameter"]],
        ["shared", "re-audit retained certificates", primary["diameter"], primary["diameter"]],
        ["shared", "source endpoint probes plus total-count/full-source audit", primary["count_audit_worst_diameter"], primary["count_audit_worst_diameter"]],
        ["shared", "source endpoints plus calibrated A-return", probe4["attained_lower_bound_on_worst_diameter"], probe4["envelope_upper_bound_on_worst_diameter"]],
        ["shared", "source endpoints plus count audit plus calibrated A-return", 0, 0],
        ["shared; ALL successes logged", "source endpoints plus calibrated A-return, K4", success["attained_lower_bound_on_worst_diameter"], success["envelope_upper_bound_on_worst_diameter"]],
        ["directional sensitivity; counts3,3", "complete source and A-return; B-loss unobserved", asym["diameter"], asym["diameter"]],
        ["directional sensitivity; counts3,3", "also one A intervention followed by B score probe", 0, 0]
    ]
    with (HERE / "MEASUREMENT_TABLE.csv").open("w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["class", "information_or_design", "worst_diameter_attained_lower", "worst_diameter_upper"])
        writer.writerows(designs)
    rss_runs = [{"name": name, **x["resources"]} for name, x in
                (("first", first), ("main", bounds), ("reference", reference))]
    native_max = max([z["peak_rss_native"] for z in rss_runs] + [resource.getrusage(resource.RUSAGE_SELF).ru_maxrss])
    maximum_bytes = native_max if sys.platform == "darwin" else native_max * 1024
    resources = {
        "recorded_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "fixed_start": "2026-11-01T05:00:11.866Z", "fixed_first_checkpoint": "2026-11-01T05:15:11.866Z",
        "first_actual_calculation_completed": first["completed_utc"],
        "fixed_deadline": "2026-11-01T06:15:11.866Z",
        "main_completed": bounds["completed_utc"], "contrary_reference_completed": reference["completed_utc"],
        "python_version": sys.version, "platform": sys.platform, "dependencies": "Python standard library only",
        "randomness": "none", "scientific_execution": "one process at a time, one numerical thread, no background jobs",
        "manual_usage_at_start": {"remaining_percent": 43, "reserve_percent": 20,
                                  "PI_coordination_time": "2026-11-01T04:59:47.466Z",
                                  "worker_checked_or_reset_credits": False},
        "public_operations": {"used": 5, "cap": 18, "failures_included": 1,
                              "families_used": 2, "families_cap": 2,
                              "details": "SOURCES.json includes both initial queries, failed403, abstract and extracted PDF open"},
        "ingress": {"known_serialized_tool_return_utf8_bytes": 65954,
                    "direct_empirical_or_original_pdf_bytes_acquired_locally": 0,
                    "charged_bytes": 5000000, "cap_bytes": 8000000,
                    "charge_basis": "1MB each query +.5MB each primary open including failure +2MB PDF-provider extraction",
                    "provider_wire_bytes": "unknown; charge is conservative accounting, not a certified network upper bound",
                    "failed_provider_transfers_and_peaks": "unknown, included in charge; no further requests"},
        "additional_scientific_reads": {"charged_bytes": 20000000, "cap_bytes": 250000000,
                                        "basis": "conservative charge covering small owned code/JSON/CSV/text reads, decoded source returns, source hash/removal and repeated control/packaging passes; no dataset payloads",
                                        "exact_all_pass_byte_counter": "not instrumented; no new metering infrastructure"},
        "memory": {"largest_measured_local_scientific_RSS_bytes": maximum_bytes, "cap_bytes": 500000000,
                   "runs": rss_runs, "provider_process_peaks": "unknown",
                   "local_native_units": "bytes on darwin; converted from KiB otherwise"},
        "failures_and_limits": [
            "Manski primary open403; counted, no source repairs",
            "generic K0 score-probe envelope reached50000boxes before1e-5gap; saved upper1.224596e-5/tolerancefalse; separate algebra proves exactzero",
            "initial shell-composition context inventory rejected before execution; replaced by simple reads",
            "one inline Python summary rejected by local hook before execution; replaced by owned script; no calculation process started",
            "initial coarse two-point parameter grid does not support continuous-class or binary-probe point identification",
            "postvalidation directional retention invalidates a general one-return-probe sufficiency claim"
        ],
        "exposure": {"new_empirical_data": 0, "old_raw_or_protected_payloads_opened": False,
                     "synthetic_input_status": "all artificial cases are development/consumed; no pristine validation set or population observations",
                     "ordinary_context": "AGENTS, full LEARNINGS, LAB_WORKFLOW, independent-sprint instructions, brief/current state; initial100lineSTATEread also exposed older ordinary historical summaries",
                     "source_summaries": "all snippets/PDF extraction exposed; compact digest retained, full transient tool snapshot removed without resetting exposure",
                     "historical_records": "all prior failures/freezes/raw-summary exposure/resources/protected targets inherited unchanged; no shared record writes"},
        "jobs_at_completion": 0,
        "unrun": ["independent review by another context", "empirical validation or target release", "complete novelty/priority audit", "formal directed-rounding certificate", "stochastic response/selection-law calibration", "state-dependent gains or retention", "validation that any biological probe is calibrated and nonlearning", "hidden-event random-sample audit design"],
        "no_resource_extension_or_new_reservation": True
    }
    (HERE / "RESOURCES.json").write_text(json.dumps(resources, indent=2) + "\n")
    # Pins omit their own mutable record and the terminal delivery record.
    pins = []
    for path in sorted(HERE.iterdir()):
        if path.is_file() and path.name not in ("ARTIFACT_PINS.json", "DELIVERY_STATUS.json"):
            data = path.read_bytes()
            pins.append({"name": path.name, "bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()})
    (HERE / "ARTIFACT_PINS.json").write_text(json.dumps({"recorded_utc": resources["recorded_utc"], "files": pins}, indent=2) + "\n")
    print(json.dumps({"packaged_utc": resources["recorded_utc"], "pins": len(pins),
                      "pinned_file_bytes": sum(z["bytes"] for z in pins),
                      "largest_measured_local_RSS_bytes": maximum_bytes,
                      "public_operations": 5, "charged_ingress_bytes": 5000000,
                      "charged_additional_read_bytes": 20000000,
                      "jobs": 0, "frozen_pins_valid": True}, indent=2))


if __name__ == "__main__":
    main()
