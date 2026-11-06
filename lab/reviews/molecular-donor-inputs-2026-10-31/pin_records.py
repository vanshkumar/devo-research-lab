"""Record-only final artifact hashes. No scientific input/data reads."""
import datetime
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
NAMES = ('PLAN.md', 'REVIEW.md', 'README.md', 'PROPOSED_LEARNING.md',
         'reconstruct.py', 'pin_records.py', 'EARLY_DATA_CHECK.json',
         'RECONSTRUCTION.json', 'UNIT_SOURCE_DEFINITIONS.json',
         'AUTHOR_COMPARISON.json', 'INPUT_PINS.json', 'ACCOUNTING.json',
         'EXPOSURE.json', 'TERMINAL_REPORT.md')
pins = []
for name in NAMES:
    data = (ROOT / name).read_bytes()
    pins.append({'path': name, 'bytes': len(data),
                 'sha256': hashlib.sha256(data).hexdigest()})
manifest = {'saved_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
            'stable_owned_artifacts': pins,
            'excluded_PI_owned_or_mutable': ['BRIEF.md', 'STATE.md',
                'ARTIFACT_MANIFEST.json', 'DELIVERY_RECEIPT.json'],
            'record_only_direct_bytes_read': sum(p['bytes'] for p in pins),
            'charge': 'Included within ACCOUNTING closeout 10MB allowance',
            'scientific_inputs_opened': 0}
(ROOT / 'ARTIFACT_MANIFEST.json').write_text(json.dumps(manifest, indent=2) + '\n')
print(json.dumps({'stable_output_pins': len(pins),
                  'record_only_direct_bytes': manifest['record_only_direct_bytes_read'],
                  'scientific_inputs_opened': 0}))
