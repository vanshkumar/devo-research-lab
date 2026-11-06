"""Verify retrieved public text pins. This is not a circuit calculation."""
import hashlib
import json
import pathlib
import resource
import sys
import time

ROOT = pathlib.Path(__file__).resolve().parent
start = time.monotonic()
records = []
for filename in ("github-readme.json", "github-functions-simulation.json", "github-license.json"):
    raw = json.loads((ROOT / "sources" / filename).read_text())
    provider = raw["value"]["structuredContent"]
    payload = provider["content"].encode("utf-8")
    digest = hashlib.sha1(b"blob " + str(len(payload)).encode() + b"\0" + payload).hexdigest()
    records.append({"provider_record": filename, "bytes": len(payload), "expected_git_blob_sha1": provider["sha"], "computed_git_blob_sha1": digest, "matches": digest == provider["sha"]})
fetch = json.loads((ROOT / "sources/FETCH.json").read_text())
tree_raw = json.loads((ROOT / "sources/github-tree-op4.json").read_text())
tree = json.loads(tree_raw["value"]["structuredContent"]["content"])
for request in fetch["requests"]:
    if "git_blob_sha1" in request:
        path = "code/" + request["name"]
        expected = next(row["sha"] for row in tree["tree"] if row["path"] == path)
        records.append({"path": path, "bytes": request["bytes"], "expected_git_blob_sha1": expected, "computed_git_blob_sha1": request["git_blob_sha1"], "matches": expected == request["git_blob_sha1"]})
paper = (ROOT / "sources/paper.xml").read_bytes()
expected_paper = fetch["requests"][0]["sha256"]
records.append({"path": "sources/paper.xml", "bytes": len(paper), "sha256": hashlib.sha256(paper).hexdigest(), "matches": hashlib.sha256(paper).hexdigest() == expected_paper})
out = {"kind": "PUBLIC_SOURCE_PIN_VERIFICATION_ONLY", "original_circuit_execution": False, "interpreter": sys.executable, "tree_sha": tree["sha"], "checks": records, "all_match": all(row["matches"] for row in records), "seconds": time.monotonic()-start, "max_rss_bytes_macos": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss}
(ROOT / "SOURCE_PIN_CHECK.json").write_text(json.dumps(out, indent=2) + "\n")
print(json.dumps(out, indent=2))
assert out["all_match"]
