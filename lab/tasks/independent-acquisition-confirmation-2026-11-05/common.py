"""Assignment-local helpers. Never reads unlisted outcomes or mutates old artifacts."""
import time
START_WALL=time.monotonic();START_CPU=time.process_time()
from pathlib import Path
from datetime import datetime,timezone
from collections import Counter
import hashlib,io,json,os,resource,sys
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[2]
OLD=ROOT/'campaigns/learning_rule_transport_2026-10-28'
PREV=HERE.parent/'calibration-frontier-main-2026-11-05'
SOURCE=HERE.parent/'independent-acquisition-cohort-2026-11-05'
os.environ['NUMBA_CACHE_DIR']=str(HERE/'cache/numba')
os.environ['MPLCONFIGDIR']=str(HERE/'cache/matplotlib')
sys.dont_write_bytecode=True
sys.path.insert(0,str(PREV))
import numpy as np
IO=Counter();PINS={}
def utc():return datetime.now(timezone.utc).isoformat()
def serial(v):
    if isinstance(v,np.ndarray):return v.tolist()
    if isinstance(v,np.generic):return v.item()
    if isinstance(v,Path):return str(v)
    raise TypeError(type(v).__name__)
def save(name,v):
    p=HERE/name;p.parent.mkdir(parents=True,exist_ok=True);q=p.with_suffix(p.suffix+'.tmp')
    q.write_text(json.dumps(v,indent=2,allow_nan=False,default=serial)+'\n');q.replace(p)
def read(p,pin=None):
    b=Path(p).read_bytes();IO['explicit_file_bytes']+=len(b);h=hashlib.sha256(b).hexdigest()
    PINS[str(Path(p).relative_to(ROOT))]=h
    if pin is not None:assert pin==h,(str(p),h,pin)
    return b
def get(p,pin=None):return json.loads(read(p,pin))
def arrays(p,pin=None):
    with np.load(io.BytesIO(read(p,pin)),allow_pickle=False) as z:out={k:z[k] for k in z.files}
    IO['decoded_array_bytes']+=sum(a.nbytes for a in out.values());return out
def npz(name,**v):
    p=HERE/name;p.parent.mkdir(parents=True,exist_ok=True);q=p.with_suffix('.tmp.npz')
    np.savez_compressed(q,**v);q.replace(p)
def receipt(stage,status='complete',**extra):
    r=dict(utc=utc(),stage=stage,status=status,pid=os.getpid(),cpu_seconds=time.process_time()-START_CPU,
        process_wall_seconds=time.monotonic()-START_WALL,io=dict(IO),read_decode_bytes=sum(IO.values()),
        peak_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,pins=PINS.copy(),
        physical_provider_import_io='unknown',**extra)
    save(stage+'_RESOURCES.json',r);return r
def load_prescriptions():
    import main_simulator as ms
    from source_models import inherited as e
    from rnn_learning import load_rnn
    pins=get(PREV/'MAIN_RUN_FREEZE.json')['pins']
    def bank(n):return arrays(PREV/n,pins[str((PREV/n).relative_to(ROOT))])
    canonical={c:bank(f'SOURCE_CANONICAL_BANK_{c}.npz') for c in (200,1000)}
    recent={h:{c:bank(f'SOURCE_RECENT_BANK_{h}_{c}.npz') for c in (200,1000)} for h in (100,250)}
    p=OLD/'artifacts/rnn/rnnglm32_nested_best.npz';read(p,'c7f675d18f4143891ed7d2c76d91f74be74da9565fbae5407952768e2c146940')
    IO['explicit_file_bytes']+=p.stat().st_size;model=load_rnn(p)
    IO['decoded_model_bytes']+=sum(v.nbytes for v in model.params.values())
    return ms,e,model,canonical,recent
def reindex_bank(bank,donors):
    index={str(s):i for i,s in enumerate(bank['subjects'])};ii=[index[s] for s in donors]
    return {k:(v[ii].copy() if v.ndim and len(v)==len(index) else v.copy()) for k,v in bank.items()}
