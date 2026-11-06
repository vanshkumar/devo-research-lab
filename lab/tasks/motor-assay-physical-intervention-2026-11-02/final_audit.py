"""Audit saved evidence and primary-method transcription without rerunning science."""
from pathlib import Path
from fractions import Fraction as F
import datetime
import hashlib
import json
import resource
import re
import unicodedata

ROOT = Path(__file__).resolve().parent
read_bytes = 0
def read(name):
    global read_bytes
    raw = (ROOT/name).read_bytes()
    read_bytes += len(raw)
    return raw

protocol_raw = read("PROTOCOL_INPUTS.json")
protocol_hash = hashlib.sha256(protocol_raw).hexdigest()
p = json.loads(protocol_raw)
first = json.loads(read("FIRST_CALCULATION.json"))
contrary = json.loads(read("CONTRARY.json"))
source = read("HONDA_PRIMARY_METHOD_EXCERPT.txt").decode()
source_normal = " ".join(unicodedata.normalize("NFKC",source).split())

source_checks = {
    "reported_system_delay_60_ms": "60 ms system delay" in source_normal,
    "additional_delays_are_additional": "additional delays" in source_normal,
    "four_delay_values": "0-, 100-, 200-, or 300-ms" in source_normal,
    "two_second_start_hold": "2-s holding time" in source_normal,
    "return_after_cursor_stops": "after the cursor stopped" in source_normal,
    "next_probe_no_cursor": "during the probe trials, no visual feedback of the cursor" in source_normal,
    "direction_measured_at_peak_velocity": "actual hand position at the PV" in source_normal,
    "known_perturbation_signed_ten_degrees": "10° clockwise (12 trials) or counterclockwise (12 trials)" in source_normal,
    "error_and_sensitivity_both_considered": "alter not only the sensitivity but also the degree of the sensory prediction error" in source_normal,
}
assert all(source_checks.values()), source_checks
assert first["protocol_input_sha256"] == contrary["protocol_input_sha256"] == protocol_hash
assert first["timing"]["honda_physical_cursor_delays_ms"] == [60,160,260,360]
assert first["timing"]["brudner_earliest_nominal_next_target_after_terminal_crossing_ms"] == [2500,7500]
assert first["timing"]["honda_cursor_to_next_target_lower_bound_ms"] == 2000
assert len(first["crossed_reference_rows"]) == 16
assert first["exact_world_max_gap"] == "0"
assert first["exact_null_checks"] == 16
assert first["independent_eliminated_coefficients_T"] == first["independent_eliminated_coefficients_E"]
assert len(first["causal_kernel_checks"]) == 36
assert all(F(r["gap"]) == 0 for r in first["causal_kernel_checks"])
assert first["storage_expression_exact_checks"] == 24
assert contrary["recovered_from_observations"]["a"] == "97/100"
assert contrary["recovered_from_observations"]["c"] == "1/2"
assert contrary["distinct_relaxed_world"]["a"] != contrary["recovered_from_observations"]["a"]
assert contrary["distinct_relaxed_world"]["max_exact_observation_gap"] == "0"
assert not contrary["restriction_source_certified"]
assert first["empirical_records_accessed"] == contrary["empirical_records_accessed"] == 0
reference_gate = datetime.datetime.fromisoformat("2026-11-03T00:41:00+00:00")
assert datetime.datetime.fromisoformat(first["completed_utc"]) < reference_gate
assert datetime.datetime.fromisoformat(contrary["completed_utc"]) < reference_gate
assert max(first["peak_rss_bytes_this_process"],contrary["peak_rss_bytes_this_process"]) < 500000000

# Pin original artifacts; mutable terminal-delivery STATE is intentionally not
# treated as a frozen scientific result. No old source/payload is read here.
manifest = {}
names = ["BRIEF.md","PROTOCOL_INPUTS.json","HONDA_PRIMARY_METHOD_EXCERPT.txt",
         "first_calculation.py","FIRST_CALCULATION.json",
         "CONTRARY_PREDECLARATION.md","favorable_restriction_check.py","CONTRARY.json",
         "RIVALS_AND_ASSUMPTIONS.md","SOURCES.md","CLOSURE.md","RESULT.md",
         "README.md","RESOURCES.json","PROPOSED_LEARNING.md","final_audit.py"]
for name in names:
    raw = read(name)
    manifest[name] = {"bytes":len(raw),"sha256":hashlib.sha256(raw).hexdigest()}

rss = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
assert rss < 500000000
out = {
    "status":"PASS",
    "completed_utc":datetime.datetime.now(datetime.timezone.utc).isoformat(),
    "honda_primary_transcription_checks":source_checks,
    "brudner_primary_transcription_check":"Facts read in initial provider/search rendering; no complete local article copy; not independently reverified from primary bytes",
    "exact_saved_reference_and_contrary_checks":"PASS",
    "early_reference_gate":"PASS; both scientific outputs predate 00:41Z",
    "original_evidence_manifest":manifest,
    "explicit_input_bytes_read_this_audit":read_bytes,
    "runtime_import_context_toolhost_physical_io":"UNKNOWN; full separate task read allowance charged in RESOURCES.json",
    "peak_rss_bytes_this_process":rss,
    "peak_units":"macOS bytes",
    "no_raw_empirical_reads":True,
    "no_rerun_or_new_scientific_test":True,
}
(ROOT/"FINAL_AUDIT.json").write_text(json.dumps(out,indent=2)+"\n")
print(json.dumps({"status":"PASS","completed_utc":out["completed_utc"],
                  "source_checks":len(source_checks),"pinned_files":len(manifest),
                  "explicit_read_bytes":read_bytes,"peak_rss_bytes":rss}))
