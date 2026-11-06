import os
os.environ.update(OPENBLAS_NUM_THREADS='1',OMP_NUM_THREADS='1',VECLIB_MAXIMUM_THREADS='1',MKL_NUM_THREADS='1')
import sys,json,time,resource
from pathlib import Path
R=Path(__file__).resolve().parent;sys.path.insert(0,str(R/'deps'))
import numpy as np
from numcodecs import Blosc,VLenUTF8
def scalar(sid,key):return VLenUTF8().decode(Blosc().decode((R/'metadata'/f'{sid}_{key}.bin').read_bytes())).tolist()[0]
units=[]
for sid in ['664851','713655','759434']:
    m=json.loads((R/'metadata'/f'{sid}.json').read_bytes())['metadata'];desc=json.loads((R/'metadata'/f'{sid}_description.json').read_bytes())
    x=dict(subject=scalar(sid,'subject'),session=scalar(sid,'session'),archive_asserted_task_source=scalar(sid,'source'),license=desc['license'],asset_name=desc['name'],tags=desc['tags'],rows=m['intervals/trials/stim_name/.zarray']['shape'][0],trial_table_id=m['intervals/trials/.zattrs']['object_id'])
    assert x['subject']==sid==desc['subject_id'];assert x['session'].startswith(sid+'_');assert x['license']=='CC-BY-4.0'
    units.append(x)
assert len(set(x['subject'] for x in units))==3
d=dict(np.load(R/'development_arrays.npz',allow_pickle=True));c=d['stim_name']=='catch'
catch=dict(count=int(c.sum()),stim_start=d['stim_start_time'][c].tolist(),stim_stop=d['stim_stop_time'][c].tolist(),noncatch_bad_offset=int(np.sum(d['stim_stop_time'][~c]<=d['stim_start_time'][~c])))
out=dict(created_utc=time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),evaluation_units=units,independence_evidence='Capsule explicitly states five sessions from five different mice; unique matching NWB subject/session scalars and asset subject_id verified for development and three evaluation animals. One session per animal; no population representativeness assumed.',excluded='668755_2023-08-31 predates documented task-control lick fixes, excluded before any of its trial payloads; no data acquired for it.',catch_offset_audit=catch,resource_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
(R/'UNIT_CERTIFICATION.json').write_text(json.dumps(out,indent=2)+'\n')
print(json.dumps({k:v for k,v in out.items() if k!='catch_offset_audit'},indent=2));print('CATCH',{'count':catch['count'],'noncatch_bad_offset':catch['noncatch_bad_offset'],'nan_catch_offsets':int(np.isnan(d['stim_stop_time'][c]).sum()),'equal_catch_offsets':int(np.sum(d['stim_stop_time'][c]==d['stim_start_time'][c]))})
