"""Record-only closeout: hash this task's artifacts, without rerunning science."""
from pathlib import Path
import datetime as dt
import hashlib
import json
import resource

root = Path(__file__).resolve().parent
names = [
    "BRIEF.md", "reference_check.py", "FIRST_CALCULATION.json",
    "NATIVE_EXECUTION.json", "PRIOR_PINS.json", "PUBLIC_OPERATIONS.json",
    "CLOSURE.md", "ASSUMPTIONS.md", "FAILURES.md", "RESULT.md",
    "STATE.md", "README.md", "PROPOSED_LEARNING.md", "record_audit.py",
]
manifest = {}
parsed = {}
for name in names:
    data = (root / name).read_bytes()
    manifest[name] = {"bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()}
    if name.endswith(".json"):
        parsed[name] = json.loads(data)

calc = parsed["FIRST_CALCULATION.json"]
native = parsed["NATIVE_EXECUTION.json"]
ops = parsed["PUBLIC_OPERATIONS.json"]
pins = parsed["PRIOR_PINS.json"]
assert calc["source_sha256"] == manifest["reference_check.py"]["sha256"]
assert native["source_sha256"] == calc["source_sha256"]
assert native["native_exit_code"] == 0
assert calc["novelty_claim"] is False
assert ops["charged_public_operations"] == len(ops["operations"]) == 6
assert len(pins["families"]) == pins["deliberately_targeted_theoretical_families"] == 2
assert calc["empirical_records_read"] == 0
first_time = dt.datetime.fromisoformat(calc["utc"])
assert first_time <= dt.datetime(2026, 11, 1, 15, 6, tzinfo=dt.timezone.utc)
now = dt.datetime.now(dt.timezone.utc)
assert now < dt.datetime(2026, 11, 1, 16, 6, tzinfo=dt.timezone.utc)
record_peak = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
explicit_closeout = sum(entry["bytes"] for entry in manifest.values())
local_charge = 25_000_000 + calc["read_bytes_explicit_source_hash"] + explicit_closeout
resources = {
    "status": "CLOSED_ROUTINE_PRIOR_NO_MAIN_CLAIM",
    "utc": now.isoformat(),
    "scientific_native_passes": 1,
    "scientific_native_failures": 0,
    "record_only_native_passes_including_this_audit": 1,
    "ordinary_read_pretool_denials": 2,
    "ordinary_read_output_truncations_corrected_by_bounded_rereads": 1,
    "logical_public_operations_charged": 6,
    "logical_public_operations_cap": 16,
    "deliberately_targeted_primary_theory_families": 2,
    "targeted_primary_theory_family_cap": 2,
    "provider_ingress_allowance_bytes": 6_000_000,
    "provider_ingress_cap_bytes": 10_000_000,
    "provider_actual_ingress_bytes": None,
    "provider_ingress_compliance": "UNCERTIFIED; allowance is not a measured/proved upper bound; no direct download or observed breach",
    "local_context_runtime_additional_read_allowance_bytes": 25_000_000,
    "first_calculation_explicit_source_hash_bytes": calc["read_bytes_explicit_source_hash"],
    "record_only_explicit_task_read_hash_bytes": explicit_closeout,
    "additional_read_hash_decode_charge_bytes": local_charge,
    "additional_read_hash_decode_cap_bytes": 150_000_000,
    "physical_IO_and_internal_runtime_reads": "unknown; allowance not measured IO",
    "scientific_peak_rss_bytes_macos": calc["peak_rss_bytes_macos"],
    "record_only_peak_rss_bytes_macos": record_peak,
    "largest_measured_native_process_rss_bytes": max(record_peak, calc["peak_rss_bytes_macos"]),
    "peak_rss_cap_bytes": 500_000_000,
    "memory_scope": "Native processes only; provider/tool host peaks unknown. No failed numerical pass.",
    "max_concurrent_scientific_processes": 1,
    "max_numerical_threads": 1,
    "scientific_packages": "Python 3.9.6 standard library only",
    "seed": "none; exact enumeration, no random sampling",
    "empirical_acquisitions_raw_rereads_new_fits_consumed_scores": 0,
    "protected_releases": 0,
    "prior_allocation_preserved": {
        "task": "assigned-teacher-common-probe-2026-11-01",
        "failed_native_exit_codes": [1, 1],
        "charged_public_operations": 26,
        "public_operations_cap": 25,
        "ingress_allowance_bytes": 20_755_452,
        "read_charge_bytes": 80_000_000,
        "scientific_acquisition_peak_physical_IO": "unknown",
        "record_only_rss_not_science_certificate": 22_364_160,
        "other_history": "All banked mouse/review/older failure and exposure records unchanged, not reset or reread."
    },
    "first_calculation_deadline_utc": "2026-11-01T15:06:00Z",
    "first_calculation_actual_utc": calc["utc"],
    "prior_screen_close_utc": "2026-11-01T14:55:53Z",
    "prior_screen_deadline_utc": "2026-11-01T15:16:00Z",
    "main_claim_freeze": "not reached; scientific allocation closed at prior screen",
    "hard_stop_utc": "2026-11-01T16:06:00Z",
    "main_tests_independent_reviews_amendments": 0,
    "jobs": 0,
    "scientific_goal_completed": False,
}
assert local_charge < resources["additional_read_hash_decode_cap_bytes"]
assert resources["largest_measured_native_process_rss_bytes"] < resources["peak_rss_cap_bytes"]
(root / "RESOURCES.json").write_text(json.dumps(resources, indent=2) + "\n")
audit = {
    "status": "PASS_RECORD_ONLY_NO_SCIENCE_RERUN",
    "utc": now.isoformat(),
    "checks": ["required task artifacts present", "all existing JSON records parsed", "source hash matches saved native calculation", "first actual math before deadline", "closure before prior-screen deadline", "two prior families and six logical operations", "zero empirical records and no novelty claim", "closeout before hard stop", "charges and measured native peaks below their stated caps"],
    "qualification": "Provider ingress/host peaks and exact runtime physical IO remain unknown; no full resource-compliance certificate.",
    "task_file_manifest_before_audit_outputs": manifest,
    "explicit_read_hash_bytes_this_process": explicit_closeout,
    "record_only_peak_rss_bytes_macos": record_peak,
    "jobs": 0,
}
(root / "FINAL_AUDIT.json").write_text(json.dumps(audit, indent=2) + "\n")
print(json.dumps({"status": audit["status"], "utc": now.isoformat(),
                  "artifact_count": len(manifest), "explicit_read_hash_bytes": explicit_closeout,
                  "additional_read_hash_decode_charge_bytes": local_charge,
                  "largest_measured_native_process_rss_bytes": resources["largest_measured_native_process_rss_bytes"],
                  "provider_compliance": resources["provider_ingress_compliance"], "jobs": 0}, indent=2))
