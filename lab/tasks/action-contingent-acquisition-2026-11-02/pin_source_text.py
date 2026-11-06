"""Recover connector-provided exact UTF-8 bytes and verify original Git blob pins."""
import datetime
import hashlib
import json
from pathlib import Path
import resource
ROOT = Path(__file__).resolve().parent
sources = json.loads((ROOT / 'source' / 'CONNECTOR_SOURCE_TEXT.json').read_text())
result = {'utc': datetime.datetime.now(datetime.timezone.utc).isoformat(), 'files': {}, 'explanation': 'Initial apply_patch copies added an extra trailing newline; MATLAB CRLF also normalized. These original saved copies are preserved under source/normalized. Numeric checks are unchanged. Original connector text is materialized without newline conversion and each Git blob is verified.'}
for filename, sc in sources.items():
    data = sc['content'].encode('utf-8')
    blob = hashlib.sha1(('blob ' + str(len(data)) + '\0').encode() + data).hexdigest()
    assert blob == sc['sha'], (filename, blob, sc['sha'])
    target = ROOT / 'source' / filename
    previous = target.read_bytes()
    normalized = ROOT / 'source' / 'normalized' / filename
    normalized.parent.mkdir(exist_ok=True)
    if not normalized.exists():
        normalized.write_bytes(previous)
    target.write_bytes(data)
    result['files'][filename] = {'bytes': len(data), 'git_blob': blob, 'sha256': hashlib.sha256(data).hexdigest(), 'url': sc['display_url'], 'previous_saved_sha256': hashlib.sha256(previous).hexdigest(), 'previous_saved_bytes': len(previous)}
result['maxrss_bytes_darwin'] = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
result['exit_code'] = 0
(ROOT / 'SOURCE_TEXT_PINS.json').write_text(json.dumps(result, indent=2) + '\n')
print(json.dumps(result, indent=2))

