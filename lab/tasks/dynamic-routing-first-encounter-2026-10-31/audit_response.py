"""Post-freeze source discrepancy audit only. No model change or scoring."""
import os
os.environ.update(OPENBLAS_NUM_THREADS='1',OMP_NUM_THREADS='1',VECLIB_MAXIMUM_THREADS='1',MKL_NUM_THREADS='1')
import sys,json,time,resource
from pathlib import Path
import numpy as np
R=Path(__file__).resolve().parent;sys.path.insert(0,str(R/'deps'))
from numcodecs import Blosc
final=len(sys.argv)>1 and sys.argv[1]=='final'
out={};todo=[]
inventory=json.loads((R.parent/'dynamic-routing-rule-transfer-2026-10-31/zarr.json').read_bytes())
base={x['nwb_path'].split('/')[-1].split('_')[0]:x['nwb_path'].replace('s3://aind-open-data/','https://aind-open-data.s3.us-west-2.amazonaws.com/') for x in inventory}
for sid in ['664851','713655','759434']:
    d=dict(np.load(R/(sid+'_evaluation_arrays.npz'),allow_pickle=True));m=json.loads((R/'metadata'/f'{sid}.json').read_bytes())['metadata'];z=d['is_response'];r=d['response_time'];w=d['reward_time'];a=d['response_window_start_time'];b=d['response_window_stop_time'];c=d['is_contingent_reward']
    mismatch=z!=np.isfinite(r);cr=c&(~z|~np.isfinite(r)|(w<r))
    rows=np.flatnonzero(mismatch|cr);records=[]
    task=None
    if final and sid in ['713655','759434']:
        spec=m['intervals/trials/task_control_response_time/.zarray'];task=np.frombuffer(Blosc().decode((R/'raw'/sid/'task_control_response_time.bin').read_bytes()),dtype=spec['dtype']);assert list(task.shape)==spec['shape']
    for i in rows:
        rec={k:(v[i].item() if hasattr(v[i],'item') else v[i]) for k,v in d.items()}
        rec['trial_position_0based']=int(i)
        if task is not None:rec['task_control_response_time']=float(task[i]);rec['task_registered_in_export_window']=bool(a[i]<=task[i]<b[i])
        records.append(rec)
    out[sid]=dict(rows=len(z),response_flag_time_mismatch_count=int(mismatch.sum()),true_flag_missing_time_count=int(np.sum(z&~np.isfinite(r))),false_flag_finite_time_count=int(np.sum(~z&np.isfinite(r))),contingent_reward_check_failure_count=int(cr.sum()),mismatch_positions=rows.tolist(),records=records,definitions={k:m['intervals/trials/'+k+'/.zattrs'] for k in ['is_response','response_time','task_control_response_time','is_contingent_reward','is_noncontingent_reward']})
    if task is not None:out[sid]['task_control_finite_count']=int(np.isfinite(task).sum());out[sid]['task_control_response_flag_agreement']=bool(np.array_equal(z,np.isfinite(task)))
    if sid in ['713655','759434']:todo.append((base[sid]+'/intervals/trials/task_control_response_time/0','raw/'+sid+'/task_control_response_time.bin',100000))
name='RESPONSE_DISCREPANCY_AUDIT.json' if final else 'RESPONSE_DISCREPANCY_PRECHECK.json'
def finite_json(x):
    if isinstance(x,float) and not np.isfinite(x):return None
    if isinstance(x,dict):return {k:finite_json(v) for k,v in x.items()}
    if isinstance(x,list):return [finite_json(v) for v in x]
    return x
(R/name).write_text(json.dumps(finite_json(dict(created_utc=time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),postvalidation_source_diagnostic=True,primary_scoring='BLOCKED by immutable frozen chronology rule; no model/gate revision or replacement animal',subjects=out,rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)),indent=2,allow_nan=False)+'\n')
if not final:(R/'remaining_two_source_checks.json').write_text(json.dumps(todo,indent=2)+'\n')
for sid,x in out.items():print(sid,json.dumps({k:v for k,v in x.items() if k not in ['records','definitions']}),json.dumps(x['records']))
