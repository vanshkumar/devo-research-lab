"""Frozen source-derived header profile; zero data-row projection."""
import hashlib
import io
import json
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from bounded_reader import header_only, Reject

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
NEW = ROOT / "sources/schema_learning_data_audit_2026-10-29"
REQUIRED = frozenset({"correct_response", "false_tonode", "true_tonode", "true_rfc"})
PATH = "data/human/blocked_thresh0.csv"
COMMIT = "eb0edbe51042ffaf065bd90839f4f999de5f3ffb"
DEADLINE = datetime.fromisoformat("2026-10-29T21:43:02+00:00")


def profile(stream):
    result, raw = header_only(stream)
    if not REQUIRED.issubset(result["fields"]):
        raise Reject("header lacks source-derived required field profile")
    return result, raw


def freeze():
    checks = []

    def check(name, passed):
        assert passed, name
        checks.append({"name": name, "passed": True})

    sentinel = b"FORBIDDEN_RESPONSE_VALUES_MUST_STAY_OPAQUE"
    prefix = b",correct_response,false_tonode,true_tonode,true_rfc,unknown_metadata\n"
    result, raw = profile(io.BytesIO(prefix + sentinel * 200))
    check("required_source_fields_match", REQUIRED.issubset(result["fields"]))
    check("uninterpreted_extra_identifiers_allowed_header_only", result["fields"][-1] == "unknown_metadata")
    check("only_header_retained", raw == prefix)
    check("no_response_sentinel_retained", sentinel not in raw and sentinel.decode() not in json.dumps(result))
    check("read_cap_4096_and_discard_exact", result["acquired_body_bytes"] == 4096 and result["blind_discard_bytes"] == 4096 - len(prefix))
    check("no_rows_or_excluded_values_parsed", result["rows_parsed"] == result["excluded_values_materialized"] == 0)
    reordered = b"true_rfc,true_tonode,false_tonode,correct_response\n"
    check("source_profile_independent_of_column_order", set(profile(io.BytesIO(reordered))[0]["fields"]) == REQUIRED)
    for name, payload in [
        ("missing_required_field", b"true_rfc,true_tonode,false_tonode\n"),
        ("numeric_first_row", b"0,1,2,3\n"),
        ("ambiguous_quote", b'"correct_response",false_tonode,true_tonode,true_rfc\n'),
        ("duplicate_field", b"correct_response,correct_response,false_tonode,true_tonode,true_rfc\n"),
        ("truncated_header", reordered[:-1]),
    ]:
        try:
            profile(io.BytesIO(payload))
        except Reject:
            check(name + "_rejected", True)
        else:
            raise AssertionError("accepted " + name)
    oldfreeze = json.loads((HERE / "HEADER_READER_FREEZE.json").read_text())
    check("original_bounded_reader_unchanged", hashlib.sha256((HERE / "bounded_reader.py").read_bytes()).hexdigest() == oldfreeze["reader_sha256"])
    frozen = {"frozen_utc": datetime.now(timezone.utc).isoformat(),
              "selected_path": PATH, "commit": COMMIT,
              "expected_manifest_git_blob": "540af0ca2ba73344c6b6181de9cab8a1b593ec4a", "whole_blob_hash_will_not_be_verified_from_header": True,
              "profile_basis": "Pinned notebook code cell4 directly references these four names. Full schema/order are not asserted; all additional fields must satisfy the original frozen ASCII-identifier header policy.",
              "required_fields": sorted(REQUIRED), "data_row_projection": "NONE for every column, including named input candidates/anonymous keys/counts",
              "request_read_cap": 4096, "blind_header_overread_cap": 4096,
              "source_file_sha256": hashlib.sha256((NEW / "notebook_code_only.py").read_bytes()).hexdigest(),
              "profile_and_acquisition_source_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
              "original_reader_sha256": oldfreeze["reader_sha256"], "checks": checks, "all_passed": True}
    (HERE / "REVISION_HEADER_FREEZE.json").write_text(json.dumps(frozen, indent=2) + "\n")
    print(json.dumps({"header_profile_checks_passed": len(checks), "frozen_utc": frozen["frozen_utc"], "new_request": False}))


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def acquire():
    now = datetime.now(timezone.utc)
    assert now < DEADLINE
    frozen = json.loads((HERE / "REVISION_HEADER_FREEZE.json").read_text())
    assert frozen["all_passed"]
    assert hashlib.sha256(Path(__file__).read_bytes()).hexdigest() == frozen["profile_and_acquisition_source_sha256"]
    assert hashlib.sha256((HERE / "bounded_reader.py").read_bytes()).hexdigest() == frozen["original_reader_sha256"]
    assert hashlib.sha256((NEW / "notebook_code_only.py").read_bytes()).hexdigest() == frozen["source_file_sha256"]
    lp = HERE / "REVISION_ACQUISITION.json"
    ledger = json.loads(lp.read_text())
    assert len(ledger["requests"]) == 1 and ledger["cumulative_attempts"] == 7
    url = "https://raw.githubusercontent.com/PrincetonCompMemLab/blocked_training_facilitates_learning/" + COMMIT + "/" + PATH
    entry = {"cumulative_number": 8, "utc": now.isoformat(), "url": url, "kind": "capped_header_only", "body_bytes": 0, "status": "started"}
    ledger["requests"].append(entry)
    lp.write_text(json.dumps(ledger, indent=2) + "\n")
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "research-lab-schema-audit", "Accept-Encoding": "identity", "Range": "bytes=0-4095"})
        with urllib.request.build_opener(NoRedirect()).open(req, timeout=25) as response:
            entry["http_status"] = response.status
            entry["etag"] = response.headers.get("ETag")
            entry["content_range"] = response.headers.get("Content-Range")
            entry["content_length"] = response.headers.get("Content-Length")
            # This is the only human-body read. No body/row is hashed or saved.
            result, header = profile(response)
        entry["body_bytes"] = result["acquired_body_bytes"]
        ledger["new_body_bytes"] += result["acquired_body_bytes"]
        entry["header_bytes"] = result["header_bytes"]
        entry["blind_discard_bytes"] = result["blind_discard_bytes"]
        entry["status"] = "header_only_profile_passed_zero_rows"
        (NEW / "blocked_thresh0_header.csv").write_bytes(header)
        (HERE / "REVISION_HEADER_RESULT.json").write_text(json.dumps({**result, "path": PATH, "code_semantics_certified_only_for_column_roles": "correct_response is an outcome; response_node is derived from it. true/false_tonode and true_rfc naming/use do not establish deployed inputs/chronology.",
             "header_read_utc": now.isoformat(), "frozen_before_request": frozen["frozen_utc"] < now.isoformat(),
             "whole_export_git_blob_verified": False, "data_row_projection": "NONE"}, indent=2) + "\n")
    except Exception as exc:
        entry["status"] = "failed_STOP"
        entry["error_type"] = type(exc).__name__
        entry["error"] = str(exc)[:200]
    ledger["cumulative_attempts"] = 6 + len(ledger["requests"])
    ledger["cumulative_body_bytes"] = 9671 + ledger["new_body_bytes"]
    lp.write_text(json.dumps(ledger, indent=2) + "\n")
    print(json.dumps(entry))


if __name__ == "__main__":
    import sys
    if sys.argv[1] == "freeze":
        freeze()
    elif sys.argv[1] == "acquire":
        acquire()
