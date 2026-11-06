"""Bounded, public source-code/text acquisition; never fetch recordings."""
import hashlib
import json
import pathlib
import resource
import time
import urllib.request

ROOT = pathlib.Path(__file__).resolve().parent
DEST = ROOT / "sources"
DEST.mkdir(exist_ok=True)
REQUESTS = [
    ("paper.xml", "https://journals.plos.org/ploscompbiol/article/file?id=10.1371/journal.pcbi.1013818&type=manuscript", 4_000_000),
    ("simulations.ipynb", "https://raw.githubusercontent.com/mmtree/Celegans_premotor/main/code/simulations.ipynb", 10_000_000),
    ("computer_avg_weights.ipynb", "https://raw.githubusercontent.com/mmtree/Celegans_premotor/main/code/computer_avg_weights.ipynb", 1_000_000),
]
start = time.monotonic()
records = []
for name, url, cap in REQUESTS:
    rec = {"name": name, "url": url, "cap_bytes": cap}
    try:
        with urllib.request.urlopen(url, timeout=25) as response:
            payload = response.read(cap + 1)
            rec.update(status=response.status, final_url=response.url, bytes=len(payload))
        if len(payload) > cap:
            raise RuntimeError("source cap exceeded")
        rec["sha256"] = hashlib.sha256(payload).hexdigest()
        if name.endswith("ipynb"):
            rec["git_blob_sha1"] = hashlib.sha1(b"blob " + str(len(payload)).encode() + b"\0" + payload).hexdigest()
            nb = json.loads(payload)
            cells = ["# CELL %d\n%s" % (i, "".join(c.get("source", []))) for i, c in enumerate(nb["cells"]) if c.get("cell_type") in ("code", "markdown")]
            target = DEST / (name + ".source.txt")
            target.write_text("\n\n".join(cells))
            rec["cells"] = len(cells)
            rec["exposure"] = "Whole source notebook acquired and JSON decoded, including opaque unrendered output strings. Only code/markdown saved/interpreted. No empirical recording file acquired or decoded."
        else:
            target = DEST / name
            target.write_bytes(payload)
        rec["saved"] = str(target.relative_to(ROOT))
    except Exception as exc:
        rec["failure"] = repr(exc)
    records.append(rec)
out = {"requests": records, "seconds": time.monotonic() - start, "max_rss_native": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss, "rss_units": "bytes on macOS"}
(DEST / "FETCH.json").write_text(json.dumps(out, indent=2) + "\n")
print(json.dumps(out, indent=2))
