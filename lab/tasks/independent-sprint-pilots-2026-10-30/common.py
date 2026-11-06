"""Small owned-path output and explicit input-byte accounting for this block."""
import datetime as dt
import hashlib
import json
from pathlib import Path
ROOT=Path('/Users/vanshkumar/Documents/repos/devo-research-lab')
HERE=ROOT/'lab/tasks/independent-sprint-pilots-2026-10-30'
SOURCE=ROOT/'sources/independent_sprint_2026-10-30'
SOURCE.mkdir(parents=True,exist_ok=True)
LEDGER=HERE/'READS.json'

def now(): return dt.datetime.now(dt.timezone.utc).isoformat()
def save(name,obj):
    p=HERE/name; p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(json.dumps(obj,indent=2,allow_nan=False)+'\n')
def charge(path,n,kind,digest=None):
    state=json.loads(LEDGER.read_text()) if LEDGER.exists() else {'context_allowance_bytes':20000000,'total_bytes':20000000,'reads':[]}
    if state['total_bytes']+n>1000000000: raise RuntimeError('1 GB decoded/derived read cap')
    state['total_bytes']+=n
    state['reads'].append({'path':str(Path(path).relative_to(ROOT)),'bytes':n,'kind':kind,'sha256':digest})
    save('READS.json',state)
def read(path,kind='context'):
    p=Path(path); n=p.stat().st_size
    charge(p,n,kind)
    b=p.read_bytes()
    return b
def load_json(path,kind='context'): return json.loads(read(path,kind))
def digest(b): return hashlib.sha256(b).hexdigest()

