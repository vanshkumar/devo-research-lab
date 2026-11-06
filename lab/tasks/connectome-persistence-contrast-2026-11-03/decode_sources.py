"""Recover exact source text from saved connector JSON, without network access."""
import hashlib
import json
from pathlib import Path
import resource
import time

ROOT = Path(__file__).resolve().parent
start = time.monotonic()
initial = ROOT / 'SOURCE_AUDIT_INITIAL.json'
if not initial.exists():
    initial.write_bytes((ROOT / 'SOURCE_AUDIT.json').read_bytes())
results = []
for name, response in [
    ('interactome-README.md', 'interactome-readme-response.json'),
    ('interactome-initialize.py', 'interactome-code-response.json'),
    ('interactome-LICENSE', 'interactome-license-response.json')
]:
    obj = json.loads((ROOT / 'sources' / response).read_text())
    value = obj['value']
    data = value['structuredContent']['content'].encode('utf-8')
    target = ROOT / 'sources' / name
    previous = target.read_bytes()
    assert previous == data + b'\n', 'Unexpected discrepancy: stop rather than normalize'
    target.write_bytes(data)
    results.append({'path': name, 'bytes': len(data), 'removed_artifact_newline': True,
                    'sha256': hashlib.sha256(data).hexdigest()})
usage = resource.getrusage(resource.RUSAGE_SELF)
out = {'results': results, 'wall_s': time.monotonic()-start,
       'cpu_s': usage.ru_utime+usage.ru_stime, 'max_rss_bytes_macos': usage.ru_maxrss,
       'note': 'Initial failed pins preserved. Exact connector content, not a change to original model or scientific revision.'}
(ROOT / 'SOURCE_DECODING.json').write_text(json.dumps(out, indent=2)+'\n')
print(json.dumps(out))
