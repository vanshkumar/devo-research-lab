"""Owned-artifact integrity check. No model, raw data, network or science rerun."""
import hashlib
import json
import re
import resource
import time
from pathlib import Path

root = Path(__file__).resolve().parent
excluded = {"ARTIFACT_PINS.json", "CLOSEOUT_CHECK.json"}
blobs = {p.name: p.read_bytes() for p in sorted(root.iterdir()) if p.is_file() and p.name not in excluded}
parsed = {name: json.loads(blob) for name, blob in blobs.items() if name.endswith(".json")}
milestones = parsed["MILESTONES.json"]
resources = parsed["RESOURCES.json"]
receipts = parsed["SOURCE_BROWSE_RECEIPTS.json"]
assert milestones["decision"] == "CLOSE_current_source_release_allocation"
assert milestones["original_model_task_learning_calculation"] == "UNRUN"
assert milestones["independent_numerical_reference"] == "UNRUN"
assert milestones["measured_training_throughput"] == "UNRUN"
assert milestones["scientific_goal_completed"] is False
assert milestones["jobs"] == resources["jobs_at_close"] == 0
assert resources["public_operations"] == receipts["public_operations"] == 13
assert resources["model_task_data_weights_dependency_payload_acquired_bytes"] == 0
assert resources["scientific_processes_started"] == 0
assert len(receipts["receipts"]) == 8
assert "uw-mad-dash/Accordion" in blobs["SOURCE_BROWSE_RECEIPTS.json"].decode()
assert parsed["ENVIRONMENT.json"]["packages"]["torch"] is None
assert parsed["ENVIRONMENT.json"]["packages"]["torchvision"] is None

pins = {name: {"bytes": len(blob), "sha256": hashlib.sha256(blob).hexdigest()} for name, blob in blobs.items()}
(root / "ARTIFACT_PINS.json").write_text(json.dumps(pins, indent=2) + "\n")
(root / "CLOSEOUT_CHECK.json").write_text("{}\n")
links = []
for name, blob in blobs.items():
    if not name.endswith(".md"):
        continue
    for target in re.findall(r"\]\(([^)]+)\)", blob.decode()):
        if "://" in target or target.startswith("#"):
            continue
        candidate = (root / target.split("#", 1)[0]).resolve()
        assert candidate.parent == root and candidate.is_file(), (name, target)
        links.append({"from": name, "to": target})
check = {
    "utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    "status": "PASS_owned_artifact_integrity_only_no_scientific_claim_validation",
    "json_files_parsed": sorted(parsed),
    "hashed_owned_files": len(pins),
    "explicit_owned_file_read_bytes_this_check": sum(len(x) for x in blobs.values()),
    "local_links_checked": links,
    "max_rss_native_bytes_macos": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
    "unrun_model_task_status_preserved": True,
    "physical_io_and_hook_provider_runtime": "UNKNOWN",
}
(root / "CLOSEOUT_CHECK.json").write_text(json.dumps(check, indent=2) + "\n")
print(json.dumps({k: v for k, v in check.items() if k != "local_links_checked"}, indent=2))
