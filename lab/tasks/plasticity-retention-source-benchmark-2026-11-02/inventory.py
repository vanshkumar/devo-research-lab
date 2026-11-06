"""Read-only dependency availability and source-byte audit; no learning result."""
import hashlib
import importlib.util
import json
from pathlib import Path
import resource
import sys
import time

root = Path(__file__).resolve().parent
t0 = time.perf_counter()
manifest = json.loads((root / 'SOURCE_MANIFEST.json').read_text())
checked = []
read_bytes = 0
for row in manifest['files']:
    p = root / 'vendor' / row['path']
    b = p.read_bytes()
    read_bytes += len(b)
    # apply_patch Add File can preserve an extra final empty line. Restore only
    # bytes after the source-declared size, after checking they are newlines.
    expected = row['bytes']
    if len(b) != expected:
        assert len(b) > expected and b[expected:].strip(b'\n') == b''
        b = b[:expected]
        p.write_bytes(b)
    blob = hashlib.sha1(b'blob ' + str(len(b)).encode() + b'\0' + b).hexdigest()
    assert blob == row['blob_sha1'], (str(p), blob, row['blob_sha1'])
    checked.append({'path': row['path'], 'bytes': len(b), 'git_blob_sha1': blob,
                    'sha256': hashlib.sha256(b).hexdigest()})
result = {'utc': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
          'python': sys.version, 'executable': sys.executable,
          'available': {m: bool(importlib.util.find_spec(m)) for m in ('numpy', 'torch', 'tqdm')},
          'source_files': checked, 'source_read_bytes': read_bytes,
          'seconds': time.perf_counter() - t0,
          'max_rss_native': resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
          'max_rss_unit': 'bytes on this macOS host',
          'scientific_learning': 'UNRUN'}
(root / 'INVENTORY.json').write_text(json.dumps(result, indent=2) + '\n')
print(json.dumps(result))
