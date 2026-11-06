"""Sequential fixed-source public requests. Run once per named list; no retries."""
import json, sys, time, urllib.request, urllib.error, hashlib, resource
from pathlib import Path
R=Path(__file__).resolve().parent
OLD=R.parent/'dynamic-routing-rule-transfer-2026-10-31'
inventory=json.loads((OLD/'zarr.json').read_bytes())
base={x['nwb_path'].split('/')[-1].split('_')[0]:x['nwb_path'].replace('s3://aind-open-data/','https://aind-open-data.s3.us-west-2.amazonaws.com/') for x in inventory}
def request(url,name,cap):
    path=R/name
    if path.exists():
        print('ALREADY_EXISTS',name,flush=True);return
    path.parent.mkdir(parents=True,exist_ok=True)
    status=None; headers={}; err=None; data=b''; started=time.time()
    try:
        with urllib.request.urlopen(urllib.request.Request(url,headers={'User-Agent':'bounded-public-research/1.0'}),timeout=20) as f:
            status=f.status;headers=dict(f.headers);data=f.read(cap+1)
    except urllib.error.HTTPError as e:
        status=e.code;headers=dict(e.headers);data=e.read(cap+1);err=repr(e)
    except Exception as e: err=repr(e)
    if len(data)>cap:err='CAP_EXCEEDED'
    path.write_bytes(data)
    rec=dict(url=url,path=name,status=status,bytes=len(data),sha256=hashlib.sha256(data).hexdigest(),headers=headers,error=err,utc_epoch=started,elapsed_s=time.time()-started,rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
    with (R/'ACQUISITIONS.jsonl').open('a') as f:f.write(json.dumps(rec)+'\n')
    print(json.dumps({k:rec[k] for k in ['path','status','bytes','error']}),flush=True)
    if err or status!=200:raise RuntimeError('Request failed; inspect before next request')
stage=sys.argv[1]
if stage=='sources':
    todo=[('https://pypi.org/pypi/numcodecs/0.12.1/json','codec_pypi.json',200000),('https://raw.githubusercontent.com/AllenNeuralDynamics/conect-dev-capsule/main/README.md','capsule_README.md',200000),('https://api.github.com/repos/samgale/DynamicRoutingTask/git/blobs/244201ae2db302db4a1bec043ede6a16ea7ec080','task_blob.json',250000)]
elif stage=='development':
    cols=['stim_name','stim_start_time','stim_stop_time','response_window_start_time','response_window_stop_time','response_time','task_control_response_time','start_time','stop_time','block_index','is_response','is_instruction','is_reward_scheduled','is_noncontingent_reward','is_contingent_reward','is_opto','is_repeat','is_rewarded','trial_index','rewarded_modality']
    paths=['intervals/trials/'+c for c in cols]+['general/subject/subject_id','general/subject/species','general/session_id','session_start_time','general/source_script','general/experiment_description','session_description']
    todo=[(base['742903']+'/'+p+'/0','raw/742903/'+p.replace('/','__')+'.bin',250000) for p in paths]
else:
    todo=json.loads((R/(stage+'.json')).read_bytes())
for args in todo:request(*args)
