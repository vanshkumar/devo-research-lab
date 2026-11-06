"""Finalize saved evidence only; no network, notebook decode or source execution."""
import hashlib
import json
import resource
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
NEW = ROOT / "sources/schema_learning_data_audit_2026-10-29"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    checks = []

    def check(name, passed):
        assert passed, name
        checks.append({"name": name, "passed": True})

    freeze = json.loads((HERE / "NOTEBOOK_READER_FREEZE.json").read_text())
    for name, expected in freeze["preserved_first_block_sha256"].items():
        path = NEW / "SOURCE_PINS.json" if name == "sources/SOURCE_PINS.json" else HERE / name
        check("first_block_unchanged_" + name, sha(path) == expected)
    check("notebook_reader_freeze_hash_unchanged", sha(HERE / "notebook_source_reader.py") == freeze["reader_sha256"])
    check("notebook_reader_tests_unchanged", sha(HERE / "notebook_source_checks.py") == freeze["tests_sha256"])
    check("41_projection_checks_passed", len(freeze["checks"]) == 41 and all(c["passed"] for c in freeze["checks"]))
    correction = json.loads((HERE / "SOURCE_TRIAGE_CORRECTION_FREEZE.json").read_text())
    check("syntax_correction_hash_unchanged", sha(HERE / "source_triage_correction.py") == correction["correction_source_sha256"])
    check("12_syntax_correction_checks_passed", len(correction["checks"]) == 12 and all(c["passed"] for c in correction["checks"]))
    hf = json.loads((HERE / "REVISION_HEADER_FREEZE.json").read_text())
    check("header_profile_source_hash_unchanged", sha(HERE / "revision_header.py") == hf["profile_and_acquisition_source_sha256"])
    check("13_header_profile_checks_passed", len(hf["checks"]) == 13 and all(c["passed"] for c in hf["checks"]))
    projection = json.loads((HERE / "NOTEBOOK_PROJECTION.json").read_text())
    triage = json.loads((HERE / "NOTEBOOK_SOURCE_TRIAGE.json").read_text())
    check("first_notebook_STOP_preserved", projection["literal_alerts"] == [{"cell_index": 0, "line": 0, "category": "source_not_plain_Python_requires_stop"}] and projection["code_rendered"] is False)
    check("correction_is_canonical_directives_only", triage["literal_alerts"] == [] and triage["canonical_directive_counts"] == {"0": 3, "2": 0, "4": 0, "8": 0, "9": 0})
    check("corrected_code_source_hash_matches", sha(NEW / "notebook_code_only.py") == triage["source_file_sha256"] == hf["source_file_sha256"])
    opaque = (NEW / (freeze["selected_path"] + ".opaque")).read_bytes()
    check("opaque_notebook_length", len(opaque) == 14953)
    actual_blob = hashlib.sha1(b"blob " + str(len(opaque)).encode() + b"\0" + opaque).hexdigest()
    check("opaque_notebook_git_blob", actual_blob == freeze["selected_git_blob"])
    check("opaque_notebook_sha256", hashlib.sha256(opaque).hexdigest() == projection["opaque_sha256"])
    ledger_path = HERE / "REVISION_ACQUISITION.json"
    ledger = json.loads(ledger_path.read_text())
    check("exactly_two_revision_requests", len(ledger["requests"]) == 2)
    last = ledger["requests"][1]
    check("failed_header_response_range_evidence", last["http_status"] == 206 and last["content_range"] == "bytes 0-4095/2081832" and last["content_length"] == "4096")
    check("rejection_after_full_bounded_read", last["error_type"] == "Reject" and last["error"] == "not an unambiguous identifier header" and last["status"] == "failed_STOP")
    # The reader completed read(4096) before this lexical Reject. The failure
    # path did not return its counters; preserve its receipt and correct bytes.
    failure_path = HERE / "REVISION_HEADER_FAILURE.json"
    if not failure_path.exists():
        failure = {
            "recorded_utc": datetime.now(timezone.utc).isoformat(),
            "original_failed_acquisition_entry": dict(last),
            "read_body_bytes": 4096, "retained_header_bytes": 0,
            "all_unretained_body_bytes_discarded": 4096,
            "candidate_header_length": None, "post_header_overread_bytes": None,
            "post_header_overread_upper_bound": 4095,
            "reason_split_unknown": "Original bounded reader found a newline then rejected a candidate header token; its exception path did not return the header-end counter. No received bytes were retained, so no exact candidate-header/overread split is reconstructed or invented.",
            "why_total_read_is_known": "HTTP206 Content-Range0-4095, Content-Length4096; header_only calls read(4096) before finding the first newline and reaching the exact lexical Reject. No network/body-read error occurred.",
            "candidate_header_or_body_values_rendered": False,
            "row_values_decoded": 0, "excluded_row_bytes_parsed_or_logged": False,
            "actual_column_names": "not retained or rendered",
            "whole_export_git_blob_verified": False,
            "expected_profile_passed": False,
        }
        failure_path.write_text(json.dumps(failure, indent=2) + "\n")
    last["body_bytes_before_accounting_correction"] = 0
    last["body_bytes"] = 4096
    last["discarded_unretained_body_bytes"] = 4096
    last["candidate_header_length_unknown_on_exception"] = True
    last["accounting_correction"] = "REVISION_HEADER_FAILURE.json; read completed before lexical rejection. Status remains failed_STOP; no header was recovered/relabelled."
    ledger["new_body_bytes"] = 14953 + 4096
    ledger["cumulative_attempts"] = 8
    ledger["cumulative_body_bytes"] = 9671 + ledger["new_body_bytes"]
    ledger_path.write_text(json.dumps(ledger, indent=2) + "\n")
    check("cumulative_request_cap_exhausted", ledger["cumulative_attempts"] == 8)
    check("cumulative_body_bytes_exact", ledger["cumulative_body_bytes"] == 28720)
    check("cumulative_body_cap_respected", ledger["cumulative_body_bytes"] <= 8_000_000)
    check("projection_freeze_precedes_notebook_request", freeze["frozen_utc"] < ledger["requests"][0]["utc"])
    check("profile_freeze_precedes_header_request", hf["frozen_utc"] < last["utc"])
    check("no_rejected_header_file_retained", not (NEW / "blocked_thresh0_header.csv").exists())
    check("excluded_notebook_values_remain_undecoded", projection["excluded_notebook_values_decoded"] == triage["excluded_notebook_values_decoded"] == 0)
    check("no_downloaded_code_executed", projection["notebook_code_executed"] is False and triage["code_executed"] is False)
    end = datetime.now(timezone.utc).isoformat()
    exposure = {
        "recorded_utc": end, "revision_start_utc": "2026-10-29T21:28:02Z", "revision_deadline_utc": "2026-10-29T21:43:02Z",
        "original_block_files": "Preserved byte-exact as listed in NOTEBOOK_READER_FREEZE.json, including original RESULT/CERTIFICATION/EXPOSURE/ACQUISITION/freezes/pins. STATE append only.",
        "revision_new_requests": 2, "cumulative_charged_request_attempts": 8,
        "original_body_bytes": 9671, "revision_opaque_notebook_bytes": 14953, "revision_human_CSV_range_bytes": 4096,
        "cumulative_application_read_body_bytes": 28720,
        "notebook_code_source_utf8_bytes_unique": 2107,
        "notebook_code_source_json_string_token_bytes_unique": 2330,
        "notebook_non_source_token_bytes_opaque": 12623,
        "notebook_code_source_decoding_passes": 3,
        "notebook_code_source_utf8_bytes_including_repeated_passes": 6321,
        "notebook_code_cells_static_inspected": [0,2,4,8,9],
        "notebook_outputs_attachments_markdown_metadata_payload_values_decoded": 0,
        "structural_metadata_policy": "Fixed cells/cell_type/source/code labels matched without materializing arbitrary JSON scalar/container values; excluded bytes validated/skipped structurally only.",
        "source_literal_triage": "Initial non-Python syntax stop preserved. Diagnostic found3percent directives;12synthetic correction checks added support only for canonical %matplotlib inline/%load_ext autoreload/%autoreload2. Frozen JSON projection and literal checks unchanged; no participant-data literals detected in inspected source.",
        "human_CSV_range_bytes_acquired_and_discarded": 4096,
        "candidate_CSV_header_names_or_bytes_retained": 0,
        "candidate_header_post_header_split": "unknown on rejection; exact total4096discarded; post-header overread<4096. See failure receipt.",
        "human_response_attention_correctness_performance_personal_free_text_values_decoded": 0,
        "human_row_environmental_values_keys_counts_or_stories_decoded": 0,
        "human_body_hash_or_full_export_hash_computed": False,
        "whole_notebook_git_blob_verified": True,
        "whole_notebook_JSON_decode": False,
        "new_model_fitting_scoring": False, "downloaded_code_execution": False,
        "prior_summary_exposure": "Unchanged inherited article/consumed synthetic findings; notebook outputs and raw CSV rows not read as values.",
        "archive_deployed_correspondence": "unknown",
        "protected_boundaries": "All Pan20/Flesch81/B2/B20/later HABITS and historical restrictions unchanged",
        "usage": "PI supplied fresh67%remaining; local October29 human10%floor. No spend/reset or automatic usage query.",
        "resources": "One Python process at a time; no installs/subagents/chats/contact/publication/continuation; no jobs remain.",
        "final_verifier_maxrss_bytes_macOS": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
        "stop": "Eight-request cap exhausted; notebook gives outcome-column roles but no deployed task/export/inclusion law; sole candidate header failed frozen profile before rendering. No source-to-target protocol justified."
    }
    (HERE / "REVISION_EXPOSURE.json").write_text(json.dumps(exposure, indent=2) + "\n")
    pins = {"commit": freeze["commit"], "notebook_path": freeze["selected_path"], "notebook_bytes": 14953,
            "notebook_git_blob": actual_blob, "notebook_sha256": hashlib.sha256(opaque).hexdigest(),
            "code_only_file_sha256": sha(NEW / "notebook_code_only.py"), "CSV_header_path": hf["selected_path"],
            "CSV_expected_manifest_git_blob_only": hf["expected_manifest_git_blob"], "CSV_whole_blob_verified": False,
            "CSV_range": "bytes0-4095/2081832; body discarded on lexical rejection; no header retained",
            "archived_paper_deployment_equivalence": "unknown",
            "note": "Revision pins only; original SOURCE_PINS.json unchanged."}
    (NEW / "REVISION_SOURCE_PINS.json").write_text(json.dumps(pins, indent=2) + "\n")
    (HERE / "REVISION_CHECKS.json").write_text(json.dumps({"checked_utc": end, "checks": checks, "all_passed": True,
         "scope": "within-worker source/preservation/exposure integrity; not independent review or human validation"}, indent=2) + "\n")
    print(json.dumps({"checks_passed": len(checks), "end_utc": end, "cumulative_attempts": 8, "cumulative_body_bytes": 28720,
                      "initial_files_unchanged": True, "maxrss_bytes": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss}))


if __name__ == "__main__":
    main()
