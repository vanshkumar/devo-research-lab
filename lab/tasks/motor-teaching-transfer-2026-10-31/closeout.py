"""Record completion and hash owned artifacts; no scientific sources are opened."""
import hashlib,json
from datetime import datetime,timezone
from pathlib import Path
HERE=Path(__file__).resolve().parent
now=datetime.now(timezone.utc)
r=json.loads((HERE/'RESOURCES.json').read_text())
r['completed_at_utc']=now.isoformat()
r['elapsed_wall_minutes']=(now-datetime.fromisoformat(r['start_utc'].replace('Z','+00:00'))).total_seconds()/60
r['failures'].append(dict(kind='first artifact verifier Matplotlib default cache warning; fixed scoped MPLCONFIGDIR',
                         raw_scientific_bytes=0,retained='NUMERICAL_WARNING.md'))
(HERE/'RESOURCES.json').write_text(json.dumps(r,indent=2)+'\n')
message=(HERE/'TERMINAL_REPORT.md').read_text()
assert len(message.split())<=400
(HERE/'COMMUNICATION.json').write_text(json.dumps(dict(status='prepared',attempts=0,
    canonical_pi_thread_id='01a193d1-3bf8-7a11-9aef-68fa2e6a4467',report='TERMINAL_REPORT.md',
    words_by_whitespace=len(message.split()),model_or_thinking_overrides=False),indent=2)+'\n')
exclude={'ARTIFACT_MANIFEST.json','STATE.md','COMMUNICATION.json'}
files={}
for p in sorted(HERE.iterdir()):
    if p.is_file() and p.name not in exclude:
        b=p.read_bytes();files[p.name]=dict(bytes=len(b),sha256=hashlib.sha256(b).hexdigest())
(HERE/'ARTIFACT_MANIFEST.json').write_text(json.dumps(dict(created_utc=now.isoformat(),
    note='Mutable STATE/COMMUNICATION are excluded; immutable scientific freeze separately pins13files.',files=files),indent=2)+'\n')
print(json.dumps(dict(completed_at_utc=now.isoformat(),elapsed_wall_minutes=r['elapsed_wall_minutes'],
    terminal_report_words=len(message.split()),manifest_files=len(files),jobs=0),indent=2))
