"""Single-request public metadata/code acquisition; no generic human fetch."""
import hashlib
import json
import sys
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
OUT = ROOT / "sources/schema_learning_data_audit_2026-10-29"
REPO = "PrincetonCompMemLab/blocked_training_facilitates_learning"
CAP = 8_000_000


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def main():
    freeze = json.loads((HERE / "HEADER_READER_FREEZE.json").read_text())
    assert freeze["all_passed"]
    assert hashlib.sha256((HERE / "bounded_reader.py").read_bytes()).hexdigest() == freeze["reader_sha256"]
    action = sys.argv[1]
    ledger_path = HERE / "ACQUISITION.json"
    ledger = json.loads(ledger_path.read_text()) if ledger_path.exists() else {"requests": [], "body_bytes": 0}
    assert len(ledger["requests"]) < 8
    # Paths/refs originate in the saved repository tree or official metadata.
    if action in {"commit", "head"}:
        ref = "master" if action == "commit" else "HEAD"
        url = "https://api.github.com/repos/" + REPO + "/git/commits/" + ref
        target = "commit.json"
        limit = 65536
    elif action == "latest":
        url = "https://api.github.com/repos/" + REPO + "/commits?per_page=1"
        target = "latest_commit.json"
        limit = 65536
    elif action in {"analysis.py", "humanUtils.py"}:
        commit = json.loads((OUT / "commit.json").read_text())["sha"]
        url = "https://raw.githubusercontent.com/" + REPO + "/" + commit + "/" + action
        target = action
        limit = 131072
    elif action == "releases":
        url = "https://api.github.com/repos/" + REPO + "/releases?per_page=20"
        target = "releases.json"
        limit = 262144
    else:
        raise ValueError("Action is not an allowed metadata/plain-code request")
    entry = {"number": len(ledger["requests"]) + 1, "utc": datetime.now(timezone.utc).isoformat(),
             "action": action, "url": url, "cap_bytes": limit, "body_bytes": 0, "status": "started"}
    ledger["requests"].append(entry)
    OUT.mkdir(parents=True, exist_ok=True)
    ledger_path.write_text(json.dumps(ledger, indent=2) + "\n")
    try:
        request = urllib.request.Request(url, headers={"User-Agent": "research-lab-schema-audit", "Accept-Encoding": "identity"})
        with urllib.request.build_opener(NoRedirect()).open(request, timeout=25) as response:
            entry["http_status"] = response.status
            entry["content_type"] = response.headers.get("Content-Type")
            entry["etag"] = response.headers.get("ETag")
            data = response.read(limit + 1)
        entry["body_bytes"] = len(data)
        ledger["body_bytes"] += len(data)
        assert len(data) <= limit and ledger["body_bytes"] <= CAP, "body cap exceeded"
        data.decode("utf-8")
        (OUT / target).write_bytes(data)
        if action == "latest":
            metadata = json.loads(data)
            assert len(metadata) == 1
            normalized = {"sha": metadata[0]["sha"], "tree": metadata[0]["commit"]["tree"],
                          "raw_metadata_file": target}
            (OUT / "commit.json").write_text(json.dumps(normalized, indent=2) + "\n")
        entry["sha256"] = hashlib.sha256(data).hexdigest()
        entry["status"] = "saved"
    except Exception as exc:
        entry["status"] = "failed"
        entry["error_type"] = type(exc).__name__
        entry["error"] = str(exc)[:240]
    ledger_path.write_text(json.dumps(ledger, indent=2) + "\n")
    print(json.dumps(entry))


if __name__ == "__main__":
    main()
