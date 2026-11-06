"""Acquire one pinned development sample and verify actual event/coverage/schema."""
import os
os.environ['OPENBLAS_NUM_THREADS']='1'
os.environ['OMP_NUM_THREADS']='1'
import json,pathlib,hashlib,urllib.request,datetime,numpy as np
TASK=pathlib.Path(__file__).resolve().parent
ROOT=TASK.parents[2]
SRC=ROOT/'sources/heat_state_forecast_2026-10-31'
s=json.loads((TASK/'SPLIT.json').read_text())
x=next(x for x in s['items'] if x['part']=='development')
assert x['uid']=='2023-01-16-22'
dest=SRC/pathlib.Path(x['path']).name
url=f"https://raw.githubusercontent.com/{s['repo']}/{s['commit']}/{x['path']}"
# The GitHub connector is unsuitable for multi-MB raw numerical payload delivery;
# use the exact pinned raw endpoint, one request, bounded by metadata size.
if dest.exists():
    raise RuntimeError('Do not silently charge a second sample read; inspect accounting before rerun')
cached=ROOT/'sources/looper_repo'/x['path']
if cached.is_file():
    b=cached.read_bytes()
    acquisition_mode='existing local mirror, read charged; no new request'
else:
    with urllib.request.urlopen(url,timeout=45) as r:
        b=r.read(x['size']+1)
    acquisition_mode='pinned public endpoint'
assert len(b)==x['size']
assert hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest()==x['sha']
dest.write_bytes(b)
j=json.loads(b)
t=np.asarray(j['timestamp_confocal'],float)
tr=np.asarray(j['trace_array'],float)
v=np.asarray(j['velocity'],float)
h=np.asarray(j['events']['heat']).reshape(-1)
assert len(h)==1
hi=int(h[0])-1
dt=float(np.median(np.diff(t)))
out=dict(at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),uid=j.get('uid'),source_url=url,acquisition_mode=acquisition_mode,bytes=len(b),sha256=hashlib.sha256(b).hexdigest(),git_blob=x['sha'],keys=list(j),dataset_type=j.get('dataset_type'),shape=list(tr.shape),timestamp_shape=list(t.shape),velocity_shape=list(v.shape),heat_event_export=j['events']['heat'],heat_frame_0based=hi,heat_time_seconds=float(t[hi]),dt_seconds=dt,pre_seconds=float(t[hi]-t[0]),post_seconds=float(t[-1]-t[hi]),time_increasing=bool(np.all(np.diff(t)>0)),finite_trace_fraction=float(np.isfinite(tr).mean()),finite_velocity_fraction=float(np.isfinite(v).mean()),ranges_summary=[dict(n=len(z),first=z[0],last=z[-1]) for z in j['ranges']],label_count=len(j.get('labeled',{})),label_schema=list(j.get('labeled',{}).items())[:3],avg_timestep=j.get('avg_timestep'),timing_caution='pulse is an explicit event, not inferred from neural/behavior outcomes')
(TASK/'FIRST_DATA_CHECK.json').write_text(json.dumps(out,indent=2)+'\n')
print(json.dumps(out,indent=2))
