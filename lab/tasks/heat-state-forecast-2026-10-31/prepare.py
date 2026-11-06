"""Pinned heat development acquisition/extraction, single serial process.

No outcome-derived annotations used. Evaluation mode requires explicit later freeze.
Raw JSON is retained unchanged; output arrays use source timestamps/event/labels.
"""
import os
os.environ['OPENBLAS_NUM_THREADS']='1'
os.environ['OMP_NUM_THREADS']='1'
import argparse,datetime,hashlib,json,pathlib,urllib.request
import numpy as np
TASK=pathlib.Path(__file__).resolve().parent
ROOT=TASK.parents[2]
SRC=ROOT/'sources/heat_state_forecast_2026-10-31'
def now(): return datetime.datetime.now(datetime.timezone.utc).isoformat()
def extract(j,prefix_only=False,heat_time=None):
    t=np.asarray(j['timestamp_confocal'],float)
    h=np.asarray(j['events']['heat']).reshape(-1)
    assert len(h)==1
    hi=int(h[0])-1
    t=t-(t[hi] if heat_time is None else heat_time)
    a=np.asarray(j['trace_original'],float)
    assert a.shape[1]==len(t) and np.isfinite(a).all() and np.all(np.diff(t)>0)
    assert np.any(t<-450)
    if prefix_only: assert np.all(t<-5)
    else: assert np.any(t>450)
    pre=(t>=-450)&(t<-5)
    mean=a[:,pre].mean(axis=1)
    sd=a[:,pre].std(axis=1)
    assert (mean>0).all() and (sd>0).all()
    # Prefix-only normalization removes whole-record affine scaling but cannot undo
    # source interpolation or exponential bleaching fit on the full recording.
    z=(a-mean[:,None])/sd[:,None]
    ratio=a/mean[:,None]
    labels={}
    for idx,lab in j.get('labeled',{}).items():
        n=int(idx)-1
        if float(lab.get('confidence',0))>=4 and '?' not in lab.get('label',''):
            c=lab.get('neuron_class')
            if c and 0<=n<len(a): labels.setdefault(c,[]).append(n)
    classes=sorted(labels)
    neural=np.stack([z[labels[c]].mean(axis=0) for c in classes])
    ratio=np.stack([ratio[labels[c]].mean(axis=0) for c in classes])
    v=np.asarray(j['velocity'],float)
    pump=np.asarray(j['pumping'],float)
    curv=np.asarray(j['head_curvature'],float)
    assert all(len(x)==len(t) for x in [v,pump,curv])
    # Raw signed velocity, reverse fraction and pumping are behavioral outcomes.
    # Binary reverse threshold is source sign convention, checked in development.
    b=np.stack([v,(v<0).astype(float),pump,curv])
    return dict(t=t,neural=neural,ratio=ratio,classes=np.asarray(classes),behavior=b,behavior_names=np.asarray(['velocity','reverse_fraction','pumping','head_curvature']),pre_sd=sd,pre_mean=mean)
def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--part',choices=['development','evaluation'],default='development'); args=ap.parse_args()
    if args.part=='evaluation':
        assert (TASK/'EVALUATION_FREEZE.json').exists(), 'Evaluation still sealed'
        raise RuntimeError('Evaluation outcomes must use separate prefix-first forecast reader; no blanket decoding')
    split=json.loads((TASK/'SPLIT.json').read_text())
    manifest=[]
    for x in split['items']:
        if x['part']!=args.part: continue
        dest=SRC/pathlib.Path(x['path']).name
        if dest.exists():
            b=dest.read_bytes(); mode='charged cache reread'
        else:
            url=f"https://raw.githubusercontent.com/{split['repo']}/{split['commit']}/{x['path']}"
            with urllib.request.urlopen(url,timeout=45) as r: b=r.read(x['size']+1)
            assert len(b)==x['size']; dest.write_bytes(b); mode='new pinned request'
        assert len(b)==x['size']
        assert hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest()==x['sha']
        j=json.loads(b)
        assert j['uid']==x['uid'] and 'heat' in j['dataset_type']
        data=extract(j)
        np.savez_compressed(SRC/('derived_'+x['uid']+'.npz'),**data)
        t=data['t']; pre=(t>=-450)&(t<-5)
        post=(t>=30)&(t<=450)
        record=dict(uid=x['uid'],part=args.part,bytes=len(b),sha256=hashlib.sha256(b).hexdigest(),git_blob=x['sha'],mode=mode,heat_event=j['events']['heat'],dt=float(np.median(np.diff(t))),pre_s=float(-t[0]),post_s=float(t[-1]),classes=data['classes'].tolist(),n_classes=len(data['classes']),neural_count=j['num_neurons'],behavior_finite=[float(np.isfinite(z).mean()) for z in data['behavior']],behavior_pre_mean=np.nanmean(data['behavior'][:,pre],axis=1).tolist(),behavior_post_mean=np.nanmean(data['behavior'][:,post],axis=1).tolist(),at_utc=now())
        manifest.append(record)
        (TASK/'DEVELOPMENT_DATA.json').write_text(json.dumps(manifest,indent=2)+'\n')
        print(json.dumps({k:record[k] for k in ['uid','n_classes','behavior_finite','behavior_pre_mean','behavior_post_mean']}),flush=True)
    print('development complete',len(manifest),flush=True)
if __name__=='__main__': main()
