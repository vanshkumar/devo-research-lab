"""Record-only closeout: file pins, report length and exact remaining read charge."""
import hashlib,json,re
from datetime import datetime,timezone
from pathlib import Path
OUT=Path(__file__).resolve().parent;ROOT=OUT.parents[2]
resources=json.loads((OUT/'RESOURCES.json').read_text())
charge=(OUT/'RESOURCES.json').stat().st_size
stable=('BRIEF.md','DESIGN.md','RESOURCE_PLAN.json','schema_calculation.py','first_calculation.py','freeze.py','review.py','final_audit.py','closeout.py',
    'SCHEMA_CALCULATION.json','FIRST_CALCULATION.json','FROZEN_PLAN.json','PAIRED_ENDPOINTS.npz','RECONSTRUCTED_SCORES.npz','REVIEW_ARRAYS.npz',
    'REVIEW_NUMBERS.json','AUTHOR_ASSET_AUDIT.json','CONTRARY.json','FINAL_AUDIT.json','REVIEW.md','README.md','PROPOSED_LEARNING.md','EXPOSURE.json')
pins={}
for name in stable:
    p=OUT/name;raw=p.read_bytes();charge+=len(raw)
    pins[name]=dict(sha256=hashlib.sha256(raw).hexdigest(),containing_bytes=len(raw))
message=(OUT/'TERMINAL_REPORT.md').read_text();charge+=(OUT/'TERMINAL_REPORT.md').stat().st_size
words=len(message.split());assert words<=400,words
sf=ROOT/'campaigns/population_learning_transport_2026-10-28/protocols/FREEZE.json'
raw=sf.read_bytes();charge+=len(raw);freeze=json.loads(raw)
cp=ROOT/'campaigns/population_learning_transport_2026-10-28/code/campaign.py'
raw=cp.read_bytes();charge+=len(raw);sha=hashlib.sha256(raw).hexdigest()
matches=[r for r in freeze['files'] if r['path']==str(cp.relative_to(ROOT))]
assert len(matches)==1 and matches[0]['sha256']==sha
source=dict(path=str(cp.relative_to(ROOT)),sha256=sha,frozen_original_source_matches=True,
    inspected_lines='35-145',finding='Same subject seed/particle order, resets seed+101 action stream and seed+419 trainer per method; shared common initialization. Inspected, never executed/imported.')
resources['cumulative_explicit_read_hash_decode_bytes']+=charge
resources['total_conservative_read_hash_decode_allowance_bytes']=resources['cumulative_explicit_read_hash_decode_bytes']+resources['context_runtime_failed_margin_bytes']
assert resources['total_conservative_read_hash_decode_allowance_bytes']<180000000
resources['record_only_closeout_containing_hash_read_bytes']=charge
resources['record_only_closeout_utc']=datetime.now(timezone.utc).isoformat()
resources['terminal_report_words']=words
resources['native_exits']['record_only_closeout']=0
resources['native_exit_note']='Scientific native exits0 confirmed by actual tool returns; record-only closeout emits this receipt and returns normally. No science rerun for status.'
(OUT/'CODE_PINS.json').write_text(json.dumps(dict(utc=resources['record_only_closeout_utc'],pins=pins,original_source=source,
    mutable_records_excluded=['STATE.md','RESOURCES.json','TERMINAL_REPORT.md','CODE_PINS.json'],terminal_report_words=words),indent=2)+'\n')
(OUT/'RESOURCES.json').write_text(json.dumps(resources,indent=2)+'\n')
print(json.dumps(dict(utc=resources['record_only_closeout_utc'],status='record_only_closeout_complete',
    total_conservative_read_hash_decode_allowance_bytes=resources['total_conservative_read_hash_decode_allowance_bytes'],
    explicit_bytes=resources['cumulative_explicit_read_hash_decode_bytes'],peak_rss_bytes=resources['peak_rss_bytes'],terminal_report_words=words,
    source_pin_verified=True,jobs=0),indent=2))
