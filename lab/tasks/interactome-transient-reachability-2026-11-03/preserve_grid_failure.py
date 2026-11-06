"""Record-only preservation of the first incomplete pilot, without rerunning science."""
import hashlib
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path

root=Path(__file__).resolve().parent
history=root/'history'
history.mkdir(exist_ok=True)
report={'utc':datetime.now(timezone.utc).isoformat(),'native_session':33461,
 'native_failure_chunk':'d103cc','native_exit_code':1,
 'error':'ValueError: Values in t_eval are not within t_span',
 'completed_branches':0,'baseline_saved':'seed0_baseline.npz',
 'exposure':'Full seed0 baseline and all solver calculations before failure consumed; no reset',
 'pins':{}}
for name in ['pilot.py','PILOT_STARTED.json']:
    src=root/name
    dst=history/('GRID_FAILURE_'+name)
    assert not dst.exists()
    shutil.copyfile(src,dst)
    report['pins'][name]=hashlib.sha256(src.read_bytes()).hexdigest()
(history/'GRID_FAILURE.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2))
