"""Existing dependency inventory only; this is not student learning."""
import importlib.metadata as md
import json
import platform
import resource
import sys
import time
from pathlib import Path

start = time.monotonic()
packages = {}
for name in ['numpy', 'scipy', 'keras', 'tensorflow', 'tensorflow-macos', 'torch', 'jax', 'jaxlib', 'numba', 'autograd', 'threadpoolctl']:
    try:
        packages[name] = md.version(name)
    except md.PackageNotFoundError:
        packages[name] = None
out = dict(python=sys.version, executable=sys.executable, platform=platform.platform(), packages=packages,
           elapsed_seconds=time.monotonic()-start, peak_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
           student_examples=0, student_updates=0, status='ENVIRONMENT_INVENTORY_NOT_LEARNING')
Path(__file__).with_name('ENVIRONMENT_CHECK.json').write_text(json.dumps(out, indent=2)+'\n')
print(json.dumps(out, indent=2))
