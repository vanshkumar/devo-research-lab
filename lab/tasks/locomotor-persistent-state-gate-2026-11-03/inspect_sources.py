"""Inspect only public paper/code and available dependencies, not recordings."""
import importlib.util
import json
import pathlib
import resource
import shutil
import time
import xml.etree.ElementTree as ET

root = pathlib.Path(__file__).resolve().parent
start = time.monotonic()
doc = ET.parse(root / "sources/paper.xml")
sections = []
for sec in doc.iter("sec"):
    title = sec.find("title")
    if title is not None:
        name = "".join(title.itertext())
        if any(w in name.lower() for w in ["model dynamics", "gap junction", "intrinsic", "signal propagation", "heat", "timescale"]):
            sections.append({"id": sec.get("id"), "title": name, "text": " ".join("".join(c.itertext()) for c in sec if c.tag in ("p", "disp-formula"))})
out = {
    "sections": sections,
    "available": {name: importlib.util.find_spec(name) is not None for name in ("numpy", "scipy", "h5py", "pandas")},
    "julia": shutil.which("julia"),
    "seconds": time.monotonic() - start,
    "max_rss_bytes_macos": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
}
(root / "SOURCE_INSPECTION.json").write_text(json.dumps(out, indent=2) + "\n")
print(json.dumps(out, indent=2))
