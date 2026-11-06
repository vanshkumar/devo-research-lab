"""One opaque pinned notebook request, then frozen source-only projection."""
import hashlib
import json
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from notebook_source_reader import Reader, literal_alerts

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
NEW = ROOT / "sources/schema_learning_data_audit_2026-10-29"
DEADLINE = datetime.fromisoformat("2026-10-29T21:43:02+00:00")


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def check_preserved(freeze):
    for name, expected in freeze["preserved_first_block_sha256"].items():
        path = NEW / "SOURCE_PINS.json" if name == "sources/SOURCE_PINS.json" else HERE / name
        assert sha(path.read_bytes()) == expected, "first-block immutable hash changed"


def main():
    now = datetime.now(timezone.utc)
    assert now < DEADLINE, "revision deadline"
    freeze = json.loads((HERE / "NOTEBOOK_READER_FREEZE.json").read_text())
    assert freeze["all_passed"] and len(freeze["checks"]) == 41
    assert sha((HERE / "notebook_source_reader.py").read_bytes()) == freeze["reader_sha256"]
    assert sha((HERE / "notebook_source_checks.py").read_bytes()) == freeze["tests_sha256"]
    check_preserved(freeze)
    old = json.loads((HERE / "ACQUISITION.json").read_text())
    assert len(old["requests"]) == 6 and old["body_bytes"] == 9671
    ledger_path = HERE / "REVISION_ACQUISITION.json"
    ledger = json.loads(ledger_path.read_text()) if ledger_path.exists() else {"requests": [], "new_body_bytes": 0, "original_attempts": 6, "original_body_bytes": 9671}
    assert len(ledger["requests"]) < 2
    assert not ledger["requests"], "notebook request is single-use, no automatic retry"
    url = "https://raw.githubusercontent.com/PrincetonCompMemLab/blocked_training_facilitates_learning/" + freeze["commit"] + "/" + freeze["selected_path"]
    entry = {"cumulative_number": 7, "utc": now.isoformat(), "url": url, "expected_bytes": freeze["expected_bytes"], "body_bytes": 0, "status": "started"}
    ledger["requests"].append(entry)
    ledger_path.write_text(json.dumps(ledger, indent=2) + "\n")
    try:
        request = urllib.request.Request(url, headers={"User-Agent": "research-lab-schema-audit", "Accept-Encoding": "identity"})
        with urllib.request.build_opener(NoRedirect()).open(request, timeout=25) as response:
            entry["http_status"] = response.status
            entry["etag"] = response.headers.get("ETag")
            entry["content_type"] = response.headers.get("Content-Type")
            opaque = response.read(freeze["body_cap"] + 1)
        entry["body_bytes"] = len(opaque)
        ledger["new_body_bytes"] += len(opaque)
        assert len(opaque) == freeze["expected_bytes"], "opaque body length mismatch/cap"
        assert old["body_bytes"] + ledger["new_body_bytes"] <= 8_000_000
        git_blob = hashlib.sha1(b"blob " + str(len(opaque)).encode() + b"\0" + opaque).hexdigest()
        assert git_blob == freeze["selected_git_blob"], "opaque notebook Git blob mismatch"
        (NEW / (freeze["selected_path"] + ".opaque")).write_bytes(opaque)
        entry["git_blob"] = git_blob
        entry["sha256"] = sha(opaque)
        entry["status"] = "opaque_saved_hash_verified"
        reader = Reader(opaque, body_cap=freeze["body_cap"], source_cap=freeze["code_source_total_bytes_cap"],
                        cell_cap=freeze["cell_count_cap"], depth_cap=freeze["depth_cap"])
        selected = reader.extract()
        alerts = [{"cell_index": index, **alert} for index, text in selected for alert in literal_alerts(text)]
        projection = {
            "projected_utc": datetime.now(timezone.utc).isoformat(),
            "frozen_before_request": freeze["frozen_utc"] < entry["utc"],
            "opaque_sha256": entry["sha256"], "opaque_git_blob": git_blob,
            "notebook_structural_cell_count": reader.cell_count,
            "code_cell_indices": [index for index, text in selected],
            "decoded_code_source_utf8_bytes": sum(len(text.encode("utf-8")) for index, text in selected),
            "selected_code_string_json_token_bytes": sum(end - start for start, end in reader.decoded_spans),
            "selected_code_string_spans": reader.decoded_spans,
            "excluded_notebook_values_decoded": 0,
            "excluded_values_policy": "All non-code-source bytes stay opaque. JSON grammar traversal and fixed structural-label matching only; no excluded JSON objects constructed.",
            "literal_alerts": alerts,
            "notebook_code_executed": False,
            "code_rendered": False,
        }
        if alerts:
            entry["status"] = "STOP_possible_embedded_participant_literal_or_unverifiable_source"
            projection["stop"] = "Source-only extraction encountered possible embedded participant/data literals or non-Python source; do not render/use. This is an exposure problem requiring PI assessment, not permission for more access."
        else:
            code = "\n\n".join("# Notebook code cell %d\n%s" % (index, text) for index, text in selected)
            (NEW / "notebook_code_only.py").write_text(code)
            projection["code_source_file_sha256"] = sha((NEW / "notebook_code_only.py").read_bytes())
            projection["code_source_file"] = "notebook_code_only.py"
            entry["status"] = "projected_code_only_no_literal_alerts"
        (HERE / "NOTEBOOK_PROJECTION.json").write_text(json.dumps(projection, indent=2) + "\n")
        check_preserved(freeze)
        entry["code_cells_projected"] = len(selected)
        entry["literal_alert_count"] = len(alerts)
    except Exception as exc:
        entry["status"] = "failed_STOP"
        entry["error_type"] = type(exc).__name__
        entry["error"] = str(exc)[:200]
    ledger["cumulative_attempts"] = 6 + len(ledger["requests"])
    ledger["cumulative_body_bytes"] = old["body_bytes"] + ledger["new_body_bytes"]
    ledger_path.write_text(json.dumps(ledger, indent=2) + "\n")
    print(json.dumps(entry))


if __name__ == "__main__":
    main()
