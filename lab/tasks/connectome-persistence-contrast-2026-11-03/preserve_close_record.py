"""Record-only exact preservation before incorporating PI closeout guidance."""
import hashlib
import json
from pathlib import Path
import resource

ROOT = Path(__file__).resolve().parent
history = ROOT / 'history'
history.mkdir(exist_ok=True)
records = []
for name in ['SOURCE_GATE.md', 'RESULT.md', 'STATE.md', 'README.md',
             'MODEL_REFERENCE_STATUS.json', 'RESOURCES.json', 'TERMINAL_REPORT.md', 'LEARNINGS_PROPOSED.md']:
    data = (ROOT / name).read_bytes()
    target = history / ('INITIAL_CLOSE_' + name)
    assert not target.exists()
    target.write_bytes(data)
    assert target.read_bytes() == data
    records.append({'original': name, 'archive': str(target.relative_to(ROOT)),
                    'bytes': len(data), 'sha256': hashlib.sha256(data).hexdigest()})
out = {'purpose': 'Record-only preservation before PI scope clarification; no new science',
       'files': records, 'rss_bytes_macos': resource.getrusage(resource.RUSAGE_SELF).ru_maxrss}
(ROOT / 'CLOSE_RECORD_PRESERVATION.json').write_text(json.dumps(out, indent=2) + '\n')
print(json.dumps({'preserved_files': len(records), 'all_bytes_equal': True,
                  'rss_bytes_macos': out['rss_bytes_macos']}))
