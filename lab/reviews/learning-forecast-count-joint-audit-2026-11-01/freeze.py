"""Pin the independent design/ONE contrary and code before execution."""
import hashlib,json
from datetime import datetime,timezone
from pathlib import Path
OUT=Path(__file__).resolve().parent
pins={}
for name in ('DESIGN.md','RESOURCE_PLAN.json','schema_calculation.py','first_calculation.py','review.py','freeze.py','PAIRED_ENDPOINTS.npz'):
    pins[name]=hashlib.sha256((OUT/name).read_bytes()).hexdigest()
record=dict(utc=datetime.now(timezone.utc).isoformat(),status='review_design_and_single_contrary_frozen_before_contrary_calculation',
    first_calculation_utc=json.loads((OUT/'FIRST_CALCULATION.json').read_text())['utc'],
    contrary_scores_yet_computed=False,pins=pins,freeze_read_hash_bytes=sum((OUT/n).stat().st_size for n in pins))
assert record['utc']<'2026-11-01T13:48:03'
(OUT/'FROZEN_PLAN.json').write_text(json.dumps(record,indent=2)+'\n')
print(json.dumps(record,indent=2))
