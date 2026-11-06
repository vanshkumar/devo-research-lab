import importlib.util
import json
from pathlib import Path
import resource
import sys
import time

started = time.perf_counter()
root = Path(__file__).resolve().parents[3]
tree_path = root / 'lab/tasks/plasticity-retention-source-benchmark-2026-11-02/SOURCE_TREE.json'
raw = tree_path.read_bytes()
tree = json.loads(raw)
selected = [x for x in tree['tree'] if any(k in x['path'].lower() for k in ('mnist', 'nets/', 'setup.py', 'miscellaneous', 'README.md'))]
out = {'python': sys.version, 'executable': sys.executable,
       'available': {k: bool(importlib.util.find_spec(k)) for k in ('numpy','torch','torchvision','scipy','tqdm')},
       'source_read_bytes': len(raw), 'source_tree': selected,
       'seconds': time.perf_counter()-started,
       'max_rss_bytes_macos': resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
       'original_benchmark_calculation': 'UNRUN'}
print(json.dumps(out, indent=2))
(Path(__file__).parent / ('INVENTORY_' + str(sys.version_info.major) + str(sys.version_info.minor) + '.json')).write_text(json.dumps(out, indent=2)+'\n')
