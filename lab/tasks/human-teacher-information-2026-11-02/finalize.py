"""Record-only projection, pin consistency and finite-allocation closeout.

This does not reopen human outcomes, source workbooks or model fits and does
not rerun either scientific calculation.
"""
from pathlib import Path
import hashlib
import json
from datetime import datetime, timezone

OUT = Path(__file__).resolve().parent
ROOT = OUT.parents[2]


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def save(name, value):
    (OUT / name).write_text(json.dumps(value, indent=2) + "\n")


def main():
    now = datetime.now(timezone.utc).isoformat()
    law_raw = (OUT / "SOURCE_LAW.json").read_bytes()
    law = json.loads(law_raw)
    original = OUT / "SOURCE_LAW_FULL.json"
    assert not original.exists(), "Closeout already performed; do not overwrite archive"
    original.write_bytes(law_raw)
    for loop in law["builder_loops"]:
        inline = loop["params"].pop("conditions", "")
        loop["inline_conditions_characters"] = len(inline)
        loop["inline_conditions_sha256"] = digest(inline.encode())
    law["record_only_projection_utc"] = now
    law["full_original_archive"] = {"path": original.name, "bytes": len(law_raw), "sha256": digest(law_raw)}
    save("SOURCE_LAW.json", law)

    first_raw = (OUT / "FIRST_CALCULATION.json").read_bytes()
    first = json.loads(first_raw)
    people = [{k: v for k, v in p.items() if k != "candidate_counts_through_prefix"} for p in first["people"]]
    save("FIRST_CALCULATION_SUMMARY.json", {"completed_utc": first["completed_utc"], "summary": first["summary"],
                                          "source_tables": first["source_tables"], "people": people, "controls": first["controls"],
                                          "complete_record": {"path": "FIRST_CALCULATION.json", "bytes": len(first_raw), "sha256": digest(first_raw)}})

    inherited_path = ROOT / "lab/tasks/human-generated-history-forecast-2026-11-01/SOURCE_PINS.json"
    inherited = json.loads(inherited_path.read_bytes())
    expected = {p["path"]: p["sha256"] for p in inherited["inspected_source_and_cached_data_pins"]}
    inspected = json.loads((OUT / "SOURCE_INSPECTION.json").read_bytes())
    pins = {p["path"]: p for p in first["pins"] + law["pins"] + inspected["pins"]}
    manifest_path = ROOT / "campaigns/human_learning_routes_2026-10-28/experiments/source_audit/sources/manifest.json"
    manifest = json.loads(manifest_path.read_bytes())
    for p in manifest:
        if p["file"] == "WIN_cursor_ibl_lastrun.py":
            expected["campaigns/human_learning_routes_2026-10-28/experiments/source_audit/sources/" + p["file"]] = p["sha256"]
    for path, pin in pins.items():
        assert pin["sha256"] == expected[path], path
        pin["agrees_with_inherited_primary_pin"] = True
    save("SOURCE_PINS.json", {"utc": now, "scope": "Hashes computed during the scientific reads; closeout compares those saved hashes to inherited primary pins without reopening source payloads.",
                              "task_commit": inherited["task_commit"], "task_url": inherited["task_url"],
                              "analysis_commit": inherited["analysis_commit"], "analysis_url": inherited["analysis_url"],
                              "new_public_operations": 0, "new_ingress_bytes": 0,
                              "original134MBrawCSV_opened": False, "protected_payloads_opened": False,
                              "license_scope": inherited["license_scope"], "pins": list(pins.values())})

    booking = [
        {"stage": "ordinary orientation and inherited records", "allowance_bytes": 10000000},
        {"stage": "source inspection raw/hash/XML/output allowance", "allowance_bytes": 5000000},
        {"stage": "first failed calculation", "allowance_bytes": 20000000},
        {"stage": "successful first calculation explicit compressed/read/decode allowance", "allowance_bytes": first["explicit_source_read_decode_allowance_bytes"]},
        {"stage": "failed static-source parse", "allowance_bytes": 5000000},
        {"stage": "successful source-law parse/workbooks/output allowance", "allowance_bytes": 20000000},
        {"stage": "record compaction, owned output reads/hashes, closeout", "allowance_bytes": 15000000},
        {"stage": "standard-library/import/runtime allowance", "allowance_bytes": 20000000}]
    reserved = 150000000 - sum(x["allowance_bytes"] for x in booking)
    assert reserved > 0
    booking.append({"stage": "remaining record/status/return contingency", "allowance_bytes": reserved})
    resources = {"utc": now, "separate_task_read_hash_decode_cap_bytes": 300000000,
                 "separate_cumulative_booked_allowance_bytes": 150000000, "stages": booking,
                 "allowances_are_not_measured_physical_IO_or_certified_complete_IO_upper_bounds": True,
                 "largest_measured_successful_scientific_rss_bytes": law["rss_bytes_darwin"], "rss_cap_bytes": 800000000,
                 "failed_process_rss": "unknown", "tool_runtime_host_peaks": "unknown", "physical_IO": "unknown",
                 "one_scientific_process_at_a_time": True, "numerical_threads": "standard library only; no BLAS or multiprocessing used",
                 "public_operations": 0, "public_ingress_bytes": 0, "hard_deadline_utc": "2026-11-02T22:31:00Z",
                 "first_numeric_completed_utc": first["completed_utc"], "source_law_completed_utc": law["utc"],
                 "new_fits": 0, "new_learning_forecasts": 0, "new_human_scores": 0,
                 "exposure": {"inherited": "All80people already consumed; all prior raw-summary-auxiliary exposure/failures/resource charges/protections preserved.",
                              "this_task_numeric_cache": "Validation CSV fully UTF8 decoded/CSV tokenized:39people23400rows; numeric choice-feedback interpretation restricted to first200perperson. Development cache not read.",
                              "this_task_sources": "Ten source workbooks' XML strings decoded; numeric interpretation limited to first600planned inputs each. Source0inspection explicitly counted2040source data rows; other whole-sheet row counts were not separately saved. Builder inline conditions/source metadata decoded. No human outcomes in these source workbooks.",
                              "original134MBrawCSV": "not opened", "protected_datasets": "not opened"},
                 "failed_passes": 2, "failed_pass_allowance_bytes": 25000000, "ordinary_guard_denials": 4,
                 "scope_limit": "No science-goal completion, new empirical source access or independent claim review.", "science_jobs_remaining": 0}
    save("RESOURCES.json", resources)
    names = ["BRIEF.md", "PROTOCOL.md", "SOURCE_INFORMATION.md", "FIRST_CALCULATION.json", "FIRST_CALCULATION_SUMMARY.json", "SOURCE_INSPECTION.json",
             "SOURCE_LAW.json", "SOURCE_LAW_FULL.json", "SOURCE_PINS.json", "inspect_source.py", "first_calculation.py", "source_law.py",
             "RESULT.md", "STATE.md", "README.md", "FAILURES.md", "NATIVE_EXITS.json", "RESOURCES.json", "PROPOSED_LEARNING.md", "finalize.py"]
    output_pins = {}
    for name in names:
        raw = (OUT / name).read_bytes()
        output_pins[name] = {"bytes": len(raw), "sha256": digest(raw)}
    assert (OUT / "SOURCE_LAW_FULL.json").read_bytes() == law_raw
    audit = {"utc": now, "pin_count": len(output_pins), "output_pins": output_pins,
             "source_hashes_compared_to_inherited_pins": len(pins), "source_pin_matches": True,
             "full_source_law_archive_byte_exact": True, "main_forecast_score_unrun": True,
             "first_numeric_before_fixed_deadline": first["completed_utc"] < "2026-11-02T21:31:00Z",
             "source_close_before_fixed_gate": now < "2026-11-02T21:41:00Z"}
    assert audit["first_numeric_before_fixed_deadline"] and audit["source_close_before_fixed_gate"]
    save("FINAL_AUDIT.json", audit)
    save("CLOSURE.json", {"utc": now, "decision": "CLOSE", "gate": "source-information/design",
                           "reason": "Original permitted visible prefix uniquely identifies the saved planned teacher; no unknown future realization remains in the admitted source universe.",
                           "strongest_alternative": "Changes under reduced information or different targets can be routine conditioning effects; no learning-rule failure tested.",
                           "main_forecast": "UNRUN", "new_score": "UNRUN", "new_fit": "UNRUN", "independent_claim_review": "not commissioned or earned by this source/design close",
                           "source_law_utc": law["utc"], "first_numeric_utc": first["completed_utc"],
                           "planned_source_future_support": 1, "people": 39, "visible_contrasts_sufficient": 2,
                           "postvalidation": True, "science_jobs": 0, "native_goal_completed": False,
                           "final_audit_sha256": digest((OUT / "FINAL_AUDIT.json").read_bytes())})
    print(json.dumps({"utc": now, "decision": "CLOSE", "primary_pin_matches": len(pins), "saved_pin_count": len(output_pins),
                      "source_law_full_bytes": len(law_raw), "source_law_compact_bytes": (OUT / "SOURCE_LAW.json").stat().st_size,
                      "largest_scientific_rss_bytes": law["rss_bytes_darwin"], "separate_booked_allowance_bytes": 150000000,
                      "science_jobs": 0}, indent=2))


if __name__ == "__main__":
    main()
