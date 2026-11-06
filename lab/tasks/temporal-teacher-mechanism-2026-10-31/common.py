import datetime as dt,hashlib,json
from pathlib import Path
ROOT=Path('/Users/vanshkumar/Documents/repos/devo-research-lab')
HERE=ROOT/'lab/tasks/temporal-teacher-mechanism-2026-10-31'
SOURCE=ROOT/'sources/temporal_teacher_mechanism_2026-10-31'
SOURCE.mkdir(parents=True,exist_ok=True)
DEADLINE=dt.datetime(2026,10,31,14,13,16,tzinfo=dt.timezone.utc)
def now():return dt.datetime.now(dt.timezone.utc).isoformat()
def encode(x):
    if hasattr(x,'tolist'):return x.tolist()
    if hasattr(x,'item'):return x.item()
    raise TypeError(type(x).__name__)
def save(name,x):
    p=HERE/name;p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(json.dumps(x,indent=2,default=encode,allow_nan=False)+'\n')
def charge(path,n,kind):
    p=HERE/'READS.json'
    d=json.loads(p.read_text()) if p.exists() else {'known_prior_bytes':657291860,'pilot_bytes':501738182,'review_spent_bytes':155553678,'review_reserved_remaining_bytes':144446322,'additional_bytes':2000000,'additional_cap_bytes':190000000,'reads':[{'path':'initial ordinary text/source context reservation','bytes':2000000,'kind':'context'}]}
    assert d['additional_bytes']+n<=d['additional_cap_bytes'],'main190MBread cap'
    assert d['known_prior_bytes']+d['review_reserved_remaining_bytes']+d['additional_bytes']+n<=1000000000,'lineage cap with full reviewer reservation'
    d['additional_bytes']+=n;d['reads'].append({'path':str(path),'bytes':int(n),'kind':kind});save('READS.json',d)
def read(path,kind='scientific_input'):
    p=Path(path);charge(str(p.relative_to(ROOT)),p.stat().st_size,kind);return p.read_bytes()
def check_deadline():assert dt.datetime.now(dt.timezone.utc)<DEADLINE,'deadline reached'
def sha(b):return hashlib.sha256(b).hexdigest()
