"""Owned review I/O and conservative lineage accounting; no upstream writes."""
import datetime as dt
import hashlib
import io
import json
from pathlib import Path
import re
import zipfile

ROOT=Path('/Users/vanshkumar/Documents/repos/devo-research-lab')
HERE=ROOT/'lab/reviews/sprint-teaching-temporal-2026-10-31'
PILOT=ROOT/'lab/tasks/independent-sprint-pilots-2026-10-30'
SNAP=ROOT/'campaigns/evaluator_optimization_2026-10-28/primary_snapshots'
CACHE=ROOT/'sources/independent_sprint_2026-10-30'
SOURCE=ROOT/'sources/sensory_evaluator_feasibility_2026-10-28'
LEDGER=HERE/'RESUMED_READS.json'
DEADLINE=dt.datetime.fromisoformat('2026-10-31T06:57:25+00:00')

def save(name,obj):
    p=HERE/name;p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(json.dumps(obj,indent=2,allow_nan=False)+'\n')

def initialize():
    if not (HERE/'FAILED_START_MANIFEST.json').exists():
        preserved={}
        for name in ('STATE.md','REVIEW.md','EXPOSURE.json','CHECKS.json'):
            p=HERE/name
            if p.exists():
                raw=p.read_bytes();target=HERE/'failed_start'/name
                target.parent.mkdir(exist_ok=True);target.write_bytes(raw)
                preserved[name]={'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest(),'preserved_at':str(target.relative_to(HERE))}
        save('FAILED_START_MANIFEST.json',preserved)
    if not LEDGER.exists():
        save('RESUMED_READS.json',{'pilot_lineage_bytes':501738182,'failed_start_document_charge':10000000,
            'resumed_context_document_reservation':5000000,'review_total_bytes':15000000,'review_cap_bytes':300000000,
            'lineage_total_bytes':516738182,'lineage_cap_bytes':1000000000,'reads':[]})

def permitted(path):
    path=Path(path).resolve()
    if path.is_relative_to(HERE):return True
    if path.is_relative_to(PILOT):
        return path.suffix in ('.md','.py','.json') or (path.parent==PILOT/'outputs' and path.name.startswith('teaching_') and path.suffix=='.npz')
    if path.is_relative_to(SOURCE):return path.suffix in ('.py','.md','.json','.html','.ipynb')
    if path==ROOT/'experiments/sensory_evaluator_preflight_2026-10-28/preflight.py':return True
    if path.parent==CACHE:return bool(re.fullmatch(r'(noclock|reverse|tonic)_10[012]\.pkl',path.name))
    if path.parent.parent==SNAP and re.fullmatch(r'plant_10[012]',path.parent.name):return path.name in ('state.pkl','inputs.npz','preparation.json')
    return False

def charge(path,n,kind,sha=None):
    initialize();s=json.loads(LEDGER.read_text())
    assert dt.datetime.now(dt.timezone.utc)<DEADLINE,'review deadline'
    assert s['review_total_bytes']+n<=s['review_cap_bytes'],'review read cap'
    s['review_total_bytes']+=n;s['lineage_total_bytes']=s['pilot_lineage_bytes']+s['review_total_bytes']
    assert s['lineage_total_bytes']<=s['lineage_cap_bytes']
    s['reads'].append({'path':str(Path(path).relative_to(ROOT)),'bytes':n,'kind':kind,'sha256':sha})
    save('RESUMED_READS.json',s)

def read(path,kind='cached_document'):
    path=Path(path);assert permitted(path),'input outside admitted teaching scope'
    n=path.stat().st_size;charge(path,n,kind)
    raw=path.read_bytes();assert len(raw)==n,'input changed during read'
    s=json.loads(LEDGER.read_text());s['reads'][-1]['sha256']=hashlib.sha256(raw).hexdigest();save('RESUMED_READS.json',s)
    return raw

def j(path):return json.loads(read(path))

def npz(path):
    import numpy as np
    raw=read(path,'cached_NPZ_file')
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        decoded=sum(info.file_size for info in z.infolist())
    charge(path,decoded,'decoded_NPZ_members_including_headers')
    with np.load(io.BytesIO(raw),allow_pickle=False) as z:
        result={key:z[key].copy() for key in z.files}
    return result
