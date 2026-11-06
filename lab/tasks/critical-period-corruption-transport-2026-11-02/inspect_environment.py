"""Read-only local feasibility inventory; no task arrays or numerical training."""
import importlib.util
import json
import platform
import resource
import sys
import time
from pathlib import Path

start = time.time()
report = {
    "utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    "python": sys.version,
    "executable": sys.executable,
    "machine": platform.machine(),
    "packages": {},
}
for name in ("torch", "torchvision", "numpy", "PIL", "scipy"):
    spec = importlib.util.find_spec(name)
    report["packages"][name] = str(spec.origin) if spec else None
report["wall_seconds"] = time.time() - start
report["max_rss_native_bytes_macos"] = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
Path(__file__).with_name("ENVIRONMENT.json").write_text(json.dumps(report, indent=2) + "\n")
print(json.dumps(report, indent=2))
