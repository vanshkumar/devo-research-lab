"""Bounded source acquisition and metadata audit for this single pilot."""
import csv
import hashlib
import io
import json
import os
from pathlib import Path
import sys
import time
import urllib.request

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent
COMMIT = "29599fcb13a74a908c986ad69d68fc3e4a3cf6d0"
BASE = ROOT / "campaigns/byrnes_todo_2026-10-28"


def ledger():
    p = OUT / "ACCOUNTING.json"
    return json.loads(p.read_text()) if p.exists() else {
        "context_code_output_reserve_bytes": 25000000,
        "public_requests": 0, "new_ingress_bytes": 0,
        "explicit_read_decoded_bytes": 0, "reads": [], "requests": []}


def save(a):
    a["charged_read_bytes"] = a["context_code_output_reserve_bytes"] + a["explicit_read_decoded_bytes"]
    assert a["charged_read_bytes"] <= 1000000000
    assert a["public_requests"] <= 20 and a["new_ingress_bytes"] <= 100000000
    (OUT / "ACCOUNTING.json").write_text(json.dumps(a, indent=2) + "\n")


def read(p, purpose):
    a = ledger()
    n = p.stat().st_size
    assert a["context_code_output_reserve_bytes"] + a["explicit_read_decoded_bytes"] + n < 1000000000
    a["explicit_read_decoded_bytes"] += n
    a["reads"].append({"path": str(p.relative_to(ROOT)), "bytes": n, "purpose": purpose})
    save(a)  # charge even if decoding fails
    return p.read_bytes()


def fetch(url, name, cap):
    a = ledger()
    assert a["public_requests"] < 20
    assert a["new_ingress_bytes"] + cap <= 100000000
    assert a["charged_read_bytes"] + 2 * cap < 1000000000
    a["public_requests"] += 1
    rec = {"url": url, "file": name, "cap_bytes": cap, "started_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}
    a["requests"].append(rec)
    save(a)
    buf = bytearray()
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "bounded-public-research-pilot", "Accept-Encoding": "identity"})
        with urllib.request.urlopen(req, timeout=40) as r:
            rec["status"] = r.status
            rec["headers"] = dict(r.headers)
            while len(buf) < cap:
                b = r.read(min(65536, cap - len(buf)))
                if not b:
                    break
                buf.extend(b)
            assert len(buf) < cap, "capped response; conservatively charged"
        dest = OUT / "sources" / name
        dest.parent.mkdir(exist_ok=True)
        dest.write_bytes(buf)
        rec["sha256"] = hashlib.sha256(buf).hexdigest()
        rec["git_blob_sha1"] = hashlib.sha1(b"blob " + str(len(buf)).encode() + b"\0" + buf).hexdigest()
        rec["complete"] = True
    except Exception as e:
        rec["error"] = repr(e)
        rec["complete"] = False
        raise
    finally:
        rec["application_bytes"] = len(buf)
        # Network bytes plus decoded in-memory bytes, conservatively counted twice.
        a["new_ingress_bytes"] += len(buf)
        a["explicit_read_decoded_bytes"] += 2 * len(buf)
        save(a)
    print(json.dumps({"file": name, "bytes": len(buf), "sha256": rec.get("sha256")}))


def inventory():
    out = {}
    for name in ["cluster_annotations_and_statistics.txt", "matched_clusters_scviCorPruned.tsv", "human_mouse_corresponding_clusters.txt"]:
        p = BASE / "data/atlas" / name
        b = read(p, "ordinary reused mapping metadata; no evaluation-gene values")
        rows = list(csv.DictReader(io.StringIO(b.decode()), delimiter="\t"))
        rec = {"bytes": len(b), "sha256": hashlib.sha256(b).hexdigest(), "rows": len(rows), "columns": list(rows[0])}
        if "from" in rows[0] and "to" in rows[0]:
            rec["human_clusters"] = len({r["from"] for r in rows})
            rec["mouse_clusters"] = len({r["to"] for r in rows})
        out[name] = rec
    for name in ["selected_counts.npz", "peptide_counts.npz", "obs.csv", "selected_obs.csv", "raw_var.csv"]:
        p = ROOT / "campaigns/hypomap_quantitative_2026-10-28/inputs" / name
        out[name] = {"file_bytes_only_no_payload_read": p.stat().st_size}
    (OUT / "SOURCE_INVENTORY.json").write_text(json.dumps(out, indent=2) + "\n")
    print(json.dumps(out, indent=2))


def import_connector():
    p = OUT / (sys.argv[2] if len(sys.argv) > 2 else "CONNECTOR_RECEIPTS.json")
    receipts = json.loads(read(p, "exact public connector payload import; includes tree and source code"))
    a = ledger()
    tree = json.loads((OUT / "sources/hypomap_tree.json").read_text())
    expected = {x["path"]: x for x in tree["tree"]}
    mp = OUT / "SOURCE_MANIFEST.json"
    manifest = json.loads(mp.read_text()) if mp.exists() else []
    old_urls = {r["url"] for r in manifest}
    for r in receipts:
        if r["url"] in old_urls:
            continue
        b = r["content"].encode("utf-8")
        (OUT / "sources" / r["name"]).write_bytes(b)
        blob = hashlib.sha1(b"blob " + str(len(b)).encode() + b"\0" + b).hexdigest()
        e = expected.get(r.get("path"))
        if e:
            assert len(b) == e["size"] and blob == e["sha"], (r["name"], len(b), blob, e)
        a["public_requests"] += 1
        a["new_ingress_bytes"] += len(b)
        # Count source ingress + decoded source; receipt import was charged separately.
        a["explicit_read_decoded_bytes"] += 2 * len(b)
        rec = {"url": r["url"], "file": r["name"], "transport": "GitHub connector", "application_bytes": len(b), "sha256": hashlib.sha256(b).hexdigest(), "git_blob_sha1": blob, "tree_verified": bool(e), "complete": True}
        a["requests"].append(rec)
        manifest.append(rec)
    a["connector_receipts_imported"] = True
    save(a)
    (OUT / "SOURCE_MANIFEST.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print(json.dumps({"verified_files": len(manifest)-1, "requests_including_failed": a["public_requests"], "ingress_bytes": a["new_ingress_bytes"], "charged_read_bytes": a["charged_read_bytes"]}))


def import_web():
    w = json.loads(read(OUT/"WEB_RECEIPTS.json", "public source tool receipts and source-specific excerpts"))
    a = ledger()
    assert not a.get("web_receipts_imported")
    for r in w["records"]:
        a["public_requests"] += r["application_url_requests_charged"]
        a["new_ingress_bytes"] += r["ingress_allowance"]
        a["explicit_read_decoded_bytes"] += 2*r["ingress_allowance"]
        a["requests"].append({**r, "transport":"web tool", "exact_provider_network_bytes":"unavailable; conservative source allowance charged"})
    a["web_receipts_imported"] = True
    save(a)
    print(json.dumps({"public_requests_charged":a["public_requests"],"new_ingress_bytes_charged":a["new_ingress_bytes"],"read_bytes_charged":a["charged_read_bytes"]}))


if __name__ == "__main__":
    if sys.argv[1] == "inventory":
        inventory()
    elif sys.argv[1] == "tree":
        fetch(f"https://api.github.com/repos/lsteuernagel/HYPOMAP/git/trees/{COMMIT}?recursive=1", "hypomap_tree.json", 2000000)
    elif sys.argv[1] == "import-connector":
        import_connector()
    elif sys.argv[1] == "import-web":
        import_web()
    elif sys.argv[1] == "human-parameters":
        b = read(BASE/"data/atlas/parameters_human_hypo_v2.json", "cached pinned human integration parameter source, no expression outcomes")
        print(b.decode())
        print(json.dumps({"charged_read_bytes":ledger()["charged_read_bytes"]}))
    elif sys.argv[1] == "fetch":
        fetch(sys.argv[2], sys.argv[3], int(sys.argv[4]))
