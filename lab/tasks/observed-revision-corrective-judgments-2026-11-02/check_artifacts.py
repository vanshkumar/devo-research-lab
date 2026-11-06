"""Final saved-report checks only: no raw data read and no new experiment."""
import datetime
import json
import pathlib
import re
import sys

root = pathlib.Path(__file__).resolve().parent
files = sorted(root.glob('*.json'))
data = {p.name: json.loads(p.read_text()) for p in files}
missing = [(p.name, m) for p in root.glob('*.md') for m in re.findall(r'\]\(([^)]+)\)', p.read_text()) if '://' not in m and not (p.parent / m).exists()]
assert not missing, missing
assert data['FIRST_DATA_CHECK.json']['word_counts'] == [19, 19]
assert data['FIRST_DATA_CHECK.json']['better_votes'] == 7
assert data['SOURCE_MANIFEST.json']['operation_count'] == 25
result = {'checked_at': datetime.datetime.now(datetime.timezone.utc).isoformat(), 'python': sys.version, 'parsed_json_files': [p.name for p in files], 'missing_local_markdown_targets': missing, 'scope': 'Saved original-record quantities, JSON syntax, logical operation count and local report links only; no raw reread or new scientific test.', 'jobs': 0}
(root / 'ARTIFACT_CHECK.json').write_text(json.dumps(result, indent=2) + '\n')
print(json.dumps(result, indent=2))
