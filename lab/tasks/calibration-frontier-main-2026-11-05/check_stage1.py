"""Small source-only reference and saved-output inspection, not an all64 main."""
import time
import resource
BEGIN = time.monotonic()
CPU = time.process_time()
import io
import json
import hashlib
from pathlib import Path
from datetime import datetime, timezone
import numpy as np
import source_models as sm
from source_models import inherited as e
from rnn_learning import load_rnn

HERE=Path(__file__).resolve().parent
DEV=sm.DEVELOPMENT
ROOT=HERE.parents[2]
OLD=ROOT/'campaigns/learning_rule_transport_2026-10-28'
IO=dict(explicit_read_bytes=0,decoded_array_bytes=0)
def read(p):
    b=p.read_bytes();IO['explicit_read_bytes']+=len(b);return b
def arrays(p,keys=None):
    with np.load(io.BytesIO(read(p)),allow_pickle=False) as z:
        r={k:z[k] for k in (z.files if keys is None else keys)}
    IO['decoded_array_bytes']+=sum(v.nbytes for v in r.values());return r
def get(p):return json.loads(read(p))

selection=get(HERE/'SOURCE_SELECTION.json')
s=sorted(selection['cv']['100']['200']['per_animal'],key=lambda r:hashlib.sha256(r['subject'].encode()).hexdigest())[0]['subject']
raw=arrays(DEV/'TRAIN6000_ROWS.npz',[s]);chosen=selection['chosen'];half=float(chosen)
modelpath=OLD/'artifacts/rnn/rnnglm32_nested_best.npz'
IO['explicit_read_bytes']+=modelpath.stat().st_size
model=load_rnn(modelpath)
IO['decoded_array_bytes']+=sum(v.nbytes for v in model.params.values() if isinstance(v,np.ndarray))
reference=[]
for c in (200,1000):
    canonical=arrays(HERE/f'SOURCE_CANONICAL_BANK_{c}.npz')
    bank=arrays(HERE/f'SOURCE_RECENT_BANK_{chosen}_{c}.npz')
    for name in ('growth','recent_growth','gru'):
        old,_=e.simulate(s,raw[s],c,name,model,canonical,bank,half,n=16)
        new,_,_=sm.simulate(s,raw[s],c,name,model,canonical,bank,half,n=16)
        assert np.array_equal(old,new)
        reference.append(dict(subject=s,cutoff=c,model=name,particles=16,max_count_error=int(np.max(np.abs(old-new)))))
checks=get(HERE/'SOURCE_PRETRIAL_CHECKS.json')
conditional={}
for c in ('200','1000'):
    conditional[c]={}
    for name in ('primary_offset','source_calibrated_engagement'):
        rows=[r for r in checks['engagement'][c] if r['condition']==name]
        labs=sorted({r['lab'] for r in rows})
        conditional[c][name]={k:float(np.mean([np.mean([r[k] for r in rows if r['lab']==lab]) for lab in labs]))
                              for k in ('log_loss','brier','predicted_rate','observed_rate')}
z=arrays(HERE/'SOURCE_COUNTS.npz',['samples','observed','subjects'])
outer=arrays(HERE/'SOURCE_ONE_RESAMPLE_COUNTS.npz',['samples'])
perturbation={}
for ci,c in enumerate((200,1000)):
    perturbation[str(c)]={}
    for ni,name in enumerate(('growth','recent_growth')):
        differences=[]
        for i,sid in enumerate(z['subjects']):
            base=e.score_window(z['samples'][i,0,ci,ni,:,1],z['observed'][i,1],2000)
            change=e.score_window(outer['samples'][i,ci,ni,:,1],z['observed'][i,1],2000)
            differences.append(dict(subject=str(sid),mixed_score_shift=change['mixed_ratio_score']-base['mixed_ratio_score'],
                                    accuracy_mae_shift=change['equal_side_mae']-base['equal_side_mae']))
        perturbation[str(c)][name]=dict(equal_animal_score_shift=float(np.mean([r['mixed_score_shift'] for r in differences])),
             equal_animal_accuracy_mae_shift=float(np.mean([r['accuracy_mae_shift'] for r in differences])),per_animal=differences)
out=dict(utc=datetime.now(timezone.utc).isoformat(),source_reference=reference,
         conditional_engagement_equal_site=conditional,one_source_perturbation=perturbation,
         interpretation='Reference agreement is implementation fidelity, not independent scientific/biological validation; one perturbation is not a source confidence interval.',
         process_wall_seconds=time.monotonic()-BEGIN,scientific_cpu_seconds=time.process_time()-CPU,
         io=IO,peak_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
(HERE/'SOURCE_INSPECTION.json').write_text(json.dumps(out,indent=2)+'\n')
print(json.dumps({k:v for k,v in out.items() if k!='one_source_perturbation'},indent=2))
