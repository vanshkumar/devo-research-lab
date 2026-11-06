"""Match archived strong forecasts to actual pilot target, without trial rows."""
import hashlib
import json
import math
import os
from pathlib import Path
import resource
import statistics as st
import time

os.environ['OPENBLAS_NUM_THREADS']='1'
os.environ['OMP_NUM_THREADS']='1'
os.environ['VECLIB_MAXIMUM_THREADS']='1'
import numpy as np

OUT=Path(__file__).resolve().parent
ROOT=OUT.parents[2]
ARCH=ROOT/'lab/reviews/learning-forecast-count-joint-audit-2026-11-01/PAIRED_ENDPOINTS.npz'
PILOT=ROOT/'lab/tasks/acquisition-rule-vs-tracker-2026-11-05/GENERATED_SCORES.json'
start=time.monotonic()
cpu=time.process_time()
payload=PILOT.read_bytes()
new=json.loads(payload)
raw=ARCH.read_bytes()
import io
with np.load(io.BytesIO(raw),allow_pickle=False) as z:
    old={k:z[k] for k in ['subjects','labs','models','N','K','observed_N','observed_K']}
assert old['N'].shape==old['K'].shape==(2,24,512,6,2)
assert old['observed_N'].shape==old['observed_K'].shape==(24,6,2)
assert list(old['models'])==['rnnglm32','growth'] or list(old['models'])==['rnn','growth']

def crps(x,y):
    x=np.sort(x)
    m=len(x)
    return float(np.mean(np.abs(x-y))-np.sum((2*np.arange(m)+1-m)*x)/(m*m))

N=old['N'][:,:,:,:4,:].sum(axis=3)
K=old['K'][:,:,:,:4,:].sum(axis=3)
ON=old['observed_N'][:,:4,:].sum(axis=1)
OK=old['observed_K'][:,:4,:].sum(axis=1)
assert np.all(ON>0) and np.all(N>0)
A=K/N
OA=OK/ON
stats={}
target_compatibility=[]
for j,s0 in enumerate(old['subjects']):
    s=str(s0)
    assert s in new['per_animal']
    for model in ['persistence','growth','history_track','growth_track','gru']:
        d=new['per_animal'][s][model]['2000']
        independently_scored=float(np.abs(np.asarray(d['expected_ratio'])-OA[j]).mean())
        target_compatibility.append(abs(independently_scored-d['equal_side_mae']))
    for i,model in enumerate(['old_gru','old_growth']):
        stats.setdefault(s,{})[model]={'ratio_crps':st.mean(crps(A[i,j,:,side],OA[j,side]) for side in [0,1]),
            'equal_side_mae':float(np.abs(A[i,j].mean(axis=0)-OA[j]).mean()),
            'expected_ratio':A[i,j].mean(axis=0).tolist()}
    for model in ['growth','growth_track','gru']:
        d=new['per_animal'][s][model]['2000']
        stats[s]['new_'+model]={k:d[k] for k in ['ratio_crps','equal_side_mae','expected_ratio']}

labs=dict(zip(map(str,old['subjects']),map(str,old['labs'])))
summary={}
for model in next(iter(stats.values())):
    summary[model]={}
    for metric in ['ratio_crps','equal_side_mae']:
        v={s:stats[s][model][metric] for s in stats}
        site=[st.mean(v[s] for s in v if labs[s]==lab) for lab in sorted(set(labs.values()))]
        summary[model][metric]={'equal_animal':st.mean(v.values()),'equal_site':st.mean(site)}

oldgain={s:stats[s]['old_growth']['ratio_crps']-stats[s]['old_gru']['ratio_crps'] for s in stats}
oldsitegain={lab:st.mean(oldgain[s] for s in stats if labs[s]==lab) for lab in sorted(set(labs.values()))}
assert len(oldsitegain)==5
se=st.stdev(oldsitegain.values())/math.sqrt(5)
new_against_old={}
for metric in ['ratio_crps','equal_side_mae']:
    dv={s:stats[s]['old_growth'][metric]-stats[s]['new_gru'][metric] for s in stats}
    ds={lab:st.mean(dv[s] for s in stats if labs[s]==lab) for lab in sorted(set(labs.values()))}
    sse=st.stdev(ds.values())/math.sqrt(5)
    new_against_old[metric]={'sign':'positive favors current GRU over archived growth',
        'equal_animal':st.mean(dv.values()),'equal_site':st.mean(ds.values()),
        'site_t95':[st.mean(ds.values())-2.7764451051977987*sse,st.mean(ds.values())+2.7764451051977987*sse],
        'site_contrasts':ds}
out={'utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),
     'status':'postvalidation archived-reference sensitivity on 24 overlapping consumed animals',
     'target':'sum exact100 N and K over first four saved future500 bins, then ratio; 2000 generated opportunities after original1000 prefix',
     'target_compatibility_max_new_MAE_difference':max(target_compatibility),
     'summary':summary,
     'current_GRU_gain_over_archived_growth':new_against_old,
     'old_gru_gain_over_old_growth':{'equal_animal':st.mean(oldgain.values()),'equal_site':st.mean(oldsitegain.values()),
        'site_t95':[st.mean(oldsitegain.values())-2.7764451051977987*se,st.mean(oldsitegain.values())+2.7764451051977987*se]},
     'limitations':['Archived forecasts and new pilot use different observation uncertainty and comparator implementations; these are distinct recipes.',
        'If target-compatibility check fails, cross-pilot score comparisons do not share the same target and cannot be credited.',
        '24 old animals and five selected sites are consumed; this is not fresh validation or a new-lab population interval.'],
     'resources':{'input_sha256':{str(ARCH.relative_to(ROOT)):hashlib.sha256(raw).hexdigest(),str(PILOT.relative_to(ROOT)):hashlib.sha256(payload).hexdigest()},
        'explicit_file_read_bytes':len(raw)+len(payload),'decoded_array_bytes':sum(v.nbytes for v in old.values()),
        'cpu_seconds':time.process_time()-cpu,'wall_seconds':time.monotonic()-start,
        'peak_rss_native_bytes_on_Mac':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
        'original_trial_row_reads':0,'observation_exposure':'previously saved bin-level N/K summaries only',
        'physical_io_and_runtime_reads':'unknown'}}
(OUT/'ARCHIVED_REFERENCE_CHECK.json').write_text(json.dumps(out,indent=2)+'\n')
print(json.dumps(out,indent=2))
