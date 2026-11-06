"""Bounded inspection; named to avoid shadowing Python's stdlib inspect module."""
import collections
import csv
import hashlib
import json
import resource
from datetime import datetime, timezone
from pathlib import Path

OUT = Path(__file__).resolve().parent
ROOT = OUT.parents[2]
DATA = ROOT / 'data/social_learning'

def main():
    inventory = [{'path': str(p.relative_to(ROOT)), 'bytes': p.stat().st_size}
                 for p in sorted(DATA.iterdir()) if p.is_file()]
    p = DATA / 'data_primacy.csv'
    assert p.stat().st_size < 100000
    raw = p.read_bytes()
    assert hashlib.sha256(raw).hexdigest() == '0f723df5825865d214e3064c1e16f0e489211f25e45f3eb34e7dfb5c4ebf568b'
    rows = list(csv.DictReader(raw.decode().splitlines()))
    columns = {}
    for key in rows[0]:
        c = collections.Counter(r[key] for r in rows)
        columns[key] = {'unique': len(c), 'missing': c['NA'] + c[''],
                        'values': sorted(c.items()) if len(c) <= 25 else c.most_common(8)}
    result = {'created_utc': datetime.now(timezone.utc).isoformat(),
              'inventory': inventory, 'csv_bytes': len(raw),
              'sha256': hashlib.sha256(raw).hexdigest(), 'n': len(rows),
              'columns': columns, 'first_six_rows': rows[:6],
              'peak_rss_bytes': resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
              'scientific_input_bytes': len(raw), 'new_requests': 0}
    (OUT / 'SCHEMA.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result, indent=2))

if __name__ == '__main__':
    main()
