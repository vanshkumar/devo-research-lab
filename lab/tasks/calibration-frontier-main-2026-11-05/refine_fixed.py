"""One authorized numerical refinement of the original primary condition only."""
import time,resource
BEGIN=time.monotonic();CPU=time.process_time()
import io,json,hashlib
from pathlib import Path
from datetime import datetime,timezone
from collections import Counter
import numpy as np
import main_simulator as ms
from source_models import inherited as e
from rnn_learning import load_rnn

HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[2];IO=Counter();PINS={}
def serial(x):
    if isinstance(x,np.ndarray):return x.tolist()
    if isinstance(x,np.generic):return x.item()
    raise TypeError(type(x).__name__)
def save(name,x):(HERE/name).write_text(json.dumps(x,indent=2,allow_nan=False,default=serial)+'\n')
def read(p,pin=None):
    b=p.read_bytes();IO['explicit_read_bytes']+=len(b);h=hashlib.sha256(b).hexdigest();PINS[str(p.relative_to(ROOT))]=h
    if pin is not None:assert h==pin
    return b
def get(p):return json.loads(read(p))
def arrays(p,pin=None):
    with np.load(io.BytesIO(read(p,pin)),allow_pickle=False) as z:r={k:z[k] for k in z.files}
    IO['decoded_array_bytes']+=sum(v.nbytes for v in r.values());return r
def utc():return datetime.now(timezone.utc).isoformat()

def main():
    access=get(HERE/'MAIN_ACCESS.json');run=get(HERE/'MAIN_RUN_FREEZE.json');get(HERE/'REFINEMENT_START.json')
    read(HERE/'NUMERICAL_REFINEMENT.md')
    ev=arrays(HERE.parent/'acquisition-reactive-sequence-2026-11-04/CAPPED_ROWS.npz','a417bbff6c989495b1fbba77777ce09b2939794b7e4016ca63105d828ea99b80')
    ids=list(ev);assert ids==run['subjects']==access['evaluation_subjects']
    for s,a in ev.items():assert 3000<=len(a)<=4000
    canonical={c:arrays(HERE/f'SOURCE_CANONICAL_BANK_{c}.npz') for c in (200,1000)}
    banks={key:{c:arrays(HERE/f'SOURCE_RECENT_BANK_{key}_{c}.npz') for c in (200,1000)} for key in ('100','250')}
    modelpath=ROOT/'campaigns/learning_rule_transport_2026-10-28/artifacts/rnn/rnnglm32_nested_best.npz'
    read(modelpath,'c7f675d18f4143891ed7d2c76d91f74be74da9565fbae5407952768e2c146940')
    IO['explicit_read_bytes']+=modelpath.stat().st_size;model=load_rnn(modelpath)
    IO['decoded_model_bytes']+=sum(v.nbytes for v in model.params.values() if isinstance(v,np.ndarray))
    out=np.empty((64,2,4,2,256,2,7),np.int32);offsets=[20000038,30000057]
    names=['growth','recent100','recent250','gru'];(HERE/'refine_chunks').mkdir(exist_ok=True)
    base=get(HERE/'MAIN_EXECUTION.json')['scientific_cpu_seconds']+get(HERE/'MAIN_CONTROLS.json')['scientific_cpu_seconds']+get(HERE/'ANALYSIS_RESOURCES_INITIAL512.json')['scientific_cpu_seconds']+get(HERE/'REFERENCE_TO_DEVELOPMENT.json')['scientific_cpu_seconds']
    for i,s in enumerate(ids):
        for ci,c in enumerate((200,1000)):
            view=ms.causal_view(ev[s],c)
            for st,offset in enumerate(offsets):
                state,_=ms.initial_neural(model,view,c,256,e.original_seed(s)+offset)
                for ni,name in enumerate(names):
                    actor='recent_growth' if name.startswith('recent') else name
                    half=float(name[6:]) if actor=='recent_growth' else None
                    sample,_=ms.simulate(s,view,c,actor,model,canonical[c],
                         banks[str(int(half))][c] if half is not None else None,half,n=256,
                         stream_offset=offset,neural_state=state if actor=='gru' else None)
                    out[i,ci,ni,st]=sample
        np.savez_compressed(HERE/'refine_chunks'/f'{s}.npz',samples=out[i])
        if (i+1)%8==0:
            elapsed=time.process_time()-CPU
            print('REFINED',i+1,'/64 CPU',round(elapsed,2),flush=True)
            save('REFINEMENT_EXECUTION.json',dict(utc=utc(),status='running',completed_animals=i+1,
                  scientific_cpu_seconds=elapsed,process_wall_seconds=time.monotonic()-BEGIN,
                  io=dict(IO),explicit_read_decode_bytes=sum(IO.values()),prior_stage2_cpu_seconds=base,
                  peak_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,pins=PINS))
            if base+elapsed>7800:raise RuntimeError('Original totalStage2 compute stop preserving analysis allowance')
    np.savez_compressed(HERE/'REFINED_ADDITIONAL_COUNTS.npz',samples=out,subjects=ids,names=names,
          cutoffs=[200,1000],windows=[500,2000],stream_offsets=offsets)
    save('REFINEMENT_EXECUTION.json',dict(utc=utc(),status='complete',completed_animals=64,
         scientific_cpu_seconds=time.process_time()-CPU,process_wall_seconds=time.monotonic()-BEGIN,
         io=dict(IO),explicit_read_decode_bytes=sum(IO.values()),prior_stage2_cpu_seconds=base,
         peak_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,pins=PINS,
         scope='Two additional256streams; pool with original512 to1,024; primary condition only'))

if __name__=='__main__':
    try:main()
    except BaseException as exc:
        save('REFINEMENT_FAILURE_'+str(time.time())+'.json',dict(error=repr(exc),scientific_cpu_seconds=time.process_time()-CPU,
             process_wall_seconds=time.monotonic()-BEGIN,io=dict(IO)))
        raise
