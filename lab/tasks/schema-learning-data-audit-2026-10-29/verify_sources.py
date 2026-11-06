"""Verify local source pins/metadata and exposure; never read human payloads."""
import ast
import hashlib
import json
import resource
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
OLD = ROOT / "sources/noise_context_feasibility_2026-10-29"
NEW = ROOT / "sources/schema_learning_data_audit_2026-10-29"


def digest(data):
    return hashlib.sha256(data).hexdigest()


def blob(data):
    return hashlib.sha1(b"blob " + str(len(data)).encode() + b"\0" + data).hexdigest()


def main():
    checks = []

    def check(name, value):
        assert value, name
        checks.append({"name": name, "passed": True})

    oldpins = json.loads((OLD / "SOURCE_PINS.json").read_text())
    oldtree = json.loads((OLD / "github_tree.json").read_text())
    treefiles = {entry["path"]: entry for entry in oldtree["tree"] if entry["type"] == "blob"}
    metadata = json.loads((NEW / "latest_commit.json").read_text())
    check("one_commit_metadata_record", len(metadata) == 1)
    commit = metadata[0]
    check("previous_provisional_reference_is_verified_commit", commit["sha"] == oldpins["tree_sha"])
    pins = {
        "repository": oldpins["repository"],
        "commit_sha": commit["sha"],
        "commit_date_utc": commit["commit"]["committer"]["date"],
        "actual_root_tree_sha": commit["commit"]["tree"]["sha"],
        "previous_reference_interpretation_corrected": "Prior SOURCE_PINS called eb0edbe a tree without verified commit. Official commit-list metadata now confirms it is a commit; its root tree is fd577b16d7711c3a500f26ef245c8fb92a415220. Old artifacts are preserved unchanged.",
        "archive_doi": oldpins["published_archive_doi"],
        "archive_correspondence": "unknown; no new archival metadata route used and no Zenodo request repeated",
        "metadata_original_bytes": "latest_commit.json",
        "metadata_sha256": digest((NEW / "latest_commit.json").read_bytes()),
        "human_payload_hashes": "expected Git blobs only, inherited from the saved manifest; no human payload byte was acquired or verified",
        "files": {},
    }
    for name in ["model.py", "utils.py", "sim_to_args.json"]:
        raw = (OLD / name).read_bytes()
        expected = oldpins["files"][name]
        check(name + "_sha256_unchanged", digest(raw) == expected["sha256"])
        check(name + "_git_blob_unchanged", blob(raw) == expected["git_blob"])
        pins["files"][name] = {**expected, "source": "reused saved source, never imported by this audit"}
    for name in ["analysis.py", "humanUtils.py"]:
        raw = (NEW / name).read_bytes()
        check(name + "_git_blob_matches_saved_manifest", blob(raw) == treefiles[name]["sha"])
        check(name + "_byte_length_matches_saved_manifest", len(raw) == treefiles[name]["size"])
        parsed = ast.parse(raw, filename=name)  # syntax only; never execute/import
        check(name + "_plain_source_syntax", isinstance(parsed, ast.Module))
        pins["files"][name] = {"repository_path": name, "bytes": len(raw), "git_blob": blob(raw),
                               "sha256": digest(raw), "source": "new plain code read at exact commit; never imported"}
    manifest = json.loads((OLD / "human_payload_manifest.json").read_text())
    check("35_entry_human_manifest_reused", len(manifest) == 35)
    freeze = json.loads((HERE / "HEADER_READER_FREEZE.json").read_text())
    check("frozen_reader_hash_unchanged", digest((HERE / "bounded_reader.py").read_bytes()) == freeze["reader_sha256"])
    check("frozen_test_hash_unchanged", digest((HERE / "reader_checks.py").read_bytes()) == freeze["test_sha256"])
    check("26_synthetic_checks_passed", len(freeze["checks"]) == 26 and all(c["passed"] for c in freeze["checks"]))
    acq = json.loads((HERE / "ACQUISITION.json").read_text())
    check("within_8_request_attempt_cap", len(acq["requests"]) == 6)
    check("body_accounting_exact", sum(e["body_bytes"] for e in acq["requests"]) == acq["body_bytes"] == 9671)
    check("within_8MB_body_cap", acq["body_bytes"] <= 8_000_000)
    check("freeze_precedes_every_remote_attempt", all(freeze["frozen_utc"] < e["utc"] for e in acq["requests"]))
    check("only_metadata_and_two_plain_sources_requested", all(e["action"] in {"commit", "head", "latest", "analysis.py", "humanUtils.py"} for e in acq["requests"]))
    for e in acq["requests"]:
        if e["status"] == "saved":
            name = {"latest": "latest_commit.json", "analysis.py": "analysis.py", "humanUtils.py": "humanUtils.py"}[e["action"]]
            check("request_%d_saved_bytes_match_ledger" % e["number"], digest((NEW / name).read_bytes()) == e["sha256"])
    completed = datetime.now(timezone.utc).isoformat()
    exposure = {
        "recorded_utc": completed,
        "request_attempts_charged": 6,
        "network_attempts": 5,
        "sandbox_DNS_failures": 1,
        "additional_connector_attempt_denied_before_dispatch": {"tool": "mcp__codex_apps__github_fetch", "reason": "unclassified worker tool blocked by local role guard", "remote_request": False, "body_bytes": 0},
        "new_successful_response_bodies_bytes": 9671,
        "new_code_bytes": 6069,
        "new_metadata_bytes": 3602,
        "new_successful_body_files": ["latest_commit.json", "analysis.py", "humanUtils.py"],
        "failed_HTTP_body_read_bytes": 0,
        "accounting_scope": "Application-read body bytes; error bodies were never read and transport/socket buffers are not claimed to be byte-audited. New metadata includes normal public commit-author information, not participant personal data.",
        "headers_acquired": 0,
        "human_body_bytes_acquired": 0,
        "human_body_bytes_blindly_discarded": 0,
        "human_rows_or_stories_parsed": 0,
        "human_anonymous_keys_or_counts_decoded": 0,
        "environmental_state_option_probe_values_decoded": 0,
        "response_attention_correctness_performance_personal_free_text_values_decoded": 0,
        "full_CSV_JSON_dataframe_pickle_or_spreadsheet_reads": 0,
        "human_expected_schema": "not certifiable from inspected plain code; no real header request made",
        "human_row_projection": "NONE; no projection freeze or execution",
        "source_code_execution": False,
        "new_fit_model_or_scoring": False,
        "summary_exposure": "Only inherited Beukers article qualitative/Methods summaries and consumed synthetic reviewer findings. No new human outcome/accuracy summary fetched; analysis.py column names were read without its data.",
        "protected_boundaries": "Pan20, Flesch81/B2/B20, later HABITS and all historical restrictions unchanged",
        "shared_state_writes": False,
        "remote_contact_publication_payment_credit_reset": False,
        "subagents_chats_installs_continuation": False,
        "processes": "One Python process at a time; no jobs remain. Read-only shell commands were also used.",
        "verify_process_maxrss_bytes_macOS": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
        "usage": "PI-supplied manual 68% remaining; 10% local-date floor. Investigator did not query or alter account usage.",
        "stop": "No deployed export/task parser among inspected allowed plain-code candidates; input/attention/omission/inclusion semantics cannot be certified, so stopped before headers/rows.",
    }
    (NEW / "SOURCE_PINS.json").write_text(json.dumps(pins, indent=2) + "\n")
    (HERE / "EXPOSURE.json").write_text(json.dumps(exposure, indent=2) + "\n")
    (HERE / "SOURCE_CHECKS.json").write_text(json.dumps({"checked_utc": completed, "checks": checks,
        "all_passed": True, "scope": "within-worker source integrity/exposure checks, not independent review or human validation"}, indent=2) + "\n")
    print(json.dumps({"checks_passed": len(checks), "completed_utc": completed, "new_body_bytes": 9671,
                      "commit": pins["commit_sha"], "root_tree": pins["actual_root_tree_sha"], "maxrss_bytes": exposure["verify_process_maxrss_bytes_macOS"]}))


if __name__ == "__main__":
    main()
