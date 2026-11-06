"""Compare new frozen primary counts with preserved consumed development output."""
import time,resource
BEGIN=time.monotonic();CPU=time.process_time()
import io,json,hashlib
from pathlib import Path
from datetime import datetime,timezone
import numpy as np
import source_models as sm
from source_models import inherited as e
from main_scores import metrics

HERE=Path(__file__).resolve().parent;READ=0;DECODE=0;PINS={}
def load(path,keys):
    global READ,DECODE
    b=path.read_bytes();READ+=len(b);PINS[str(path)]=hashlib.sha256(b).hexdigest()
    with np.load(io.BytesIO(b),allow_pickle=False) as z:out={k:z[k] for k in keys}
    DECODE+=sum(v.nbytes for v in out.values());return out

old=load(sm.DEVELOPMENT/'EARLY_COUNTS.npz',['samples','observed','subjects','names'])
new=load(HERE/'MAIN_COUNTS.npz',['samples','subjects'])
target=load(HERE/'MAIN_OBSERVED.npz',['observed'])
assert np.array_equal(old['subjects'],new['subjects']) and np.array_equal(old['observed'],target['observed'])
first=new['samples'][:,0,:,:,0][:,:,[0,1,3]]
assert first.shape==old['samples'].shape
errors=np.max(np.abs(first-old['samples']),axis=(0,3,4))
assert np.array_equal(first[:,:,:,:,:,:4],old['samples'][:,:,:,:,:,:4])
checks=[]
for i in sorted(range(64),key=lambda j:hashlib.sha256(str(old['subjects'][j]).encode()).hexdigest())[:3]:
    for ci,c in enumerate((200,1000)):
        for ni,name in enumerate(('growth','recent100','recent250','gru')):
            S=new['samples'][i,0,ci,ni,:,:,1,:].reshape(512,7)
            a=metrics(S,target['observed'][i,1],2000);b=e.score_window(S,target['observed'][i,1],2000)
            err=max(abs(a[0]-b['equal_side_mae']),abs(a[1]-b['mixed_ratio_score']),abs(a[2]-b['joint']),abs(a[3]-b['count']))
            assert err<1e-12
            checks.append(dict(subject=str(old['subjects'][i]),cutoff=c,model=name,max_primary_score_difference=float(err)))
out=dict(utc=datetime.now(timezone.utc).isoformat(),reference='Preserved EARLY_COUNTS feasibility ensembles, same original256-particle stream',
         primary_exact_NK_counts_identical_all64=True,observed_counts_identical=True,
         per_cutoff_model_column_max_count_difference=errors.tolist(),fast_vs_legacy_score_checks=checks,
         scientific_cpu_seconds=time.process_time()-CPU,process_wall_seconds=time.monotonic()-BEGIN,
         io=dict(explicit_read_bytes=READ,decoded_array_bytes=DECODE),explicit_read_decode_bytes=READ+DECODE,
         peak_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,pins=PINS,
         scope='Source/prescription implementation fidelity only; no new biological replication or restored holdout')
(HERE/'REFERENCE_TO_DEVELOPMENT.json').write_text(json.dumps(out,indent=2)+'\n')
print(json.dumps(out))
