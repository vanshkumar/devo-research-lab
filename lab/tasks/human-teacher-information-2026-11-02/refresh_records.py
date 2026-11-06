"""Refresh owned closeout hashes after record-only clarifications.

This reads only owned records/code. It does not redo scientific calculations
or reopen source, cached observations or model assets.
"""
from pathlib import Path
import hashlib
import json
from datetime import datetime, timezone

OUT = Path(__file__).resolve().parent


def main():
    audit = json.loads((OUT / "FINAL_AUDIT.json").read_text())
    audit["record_only_refresh_utc"] = datetime.now(timezone.utc).isoformat()
    audit["record_only_refresh_reason"] = "Qualify unsaved whole-sheet row counts, record actual closeout/guard receipts and reference terminal-delivery sidecar; no numerical change or science rerun."
    names = list(audit["output_pins"])
    if "refresh_records.py" not in names:
        names.append("refresh_records.py")
    for name in names:
        raw = (OUT / name).read_bytes()
        audit["output_pins"][name] = {"bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest()}
    audit["pin_count"] = len(names)
    (OUT / "FINAL_AUDIT.json").write_text(json.dumps(audit, indent=2) + "\n")
    closure = json.loads((OUT / "CLOSURE.json").read_text())
    closure["final_audit_sha256"] = hashlib.sha256((OUT / "FINAL_AUDIT.json").read_bytes()).hexdigest()
    closure["record_only_refresh_utc"] = audit["record_only_refresh_utc"]
    (OUT / "CLOSURE.json").write_text(json.dumps(closure, indent=2) + "\n")
    for name, pin in audit["output_pins"].items():
        assert hashlib.sha256((OUT / name).read_bytes()).hexdigest() == pin["sha256"], name
    print(json.dumps({"record_refresh_utc": audit["record_only_refresh_utc"], "verified_owned_pins": len(names),
                      "scientific_close_utc_unchanged": closure["utc"], "science_jobs": 0}))


if __name__ == "__main__":
    main()
