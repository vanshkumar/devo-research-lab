#!/usr/bin/env python3
"""Offline reproduction from pinned original bytes and frozen forecasts.

Run with the campaign .modelenv Python. No data downloads, model fitting,
network calls, or external-outcome reads occur. See --help for the smaller
score-only mode. Main forecast replay defaults to every forecastable source
animal and all six original frozen models.
"""
import argparse,datetime as dt,hashlib,importlib.util,json,socket,sys,time
from pathlib import Path
import numpy as np

C=Path(__file__).resolve().parent
sys.path.insert(0,str(C/'code'))


def forbidden(*args,**kwargs):raise RuntimeError('Offline reproduction forbids network access')


def digest(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def dump(p,x):p.parent.mkdir(exist_ok=True,parents=True);p.write_text(json.dumps(x,indent=2)+'\n')


def verify_bytes():
    manifest={}
    for line in(C/'data/DOWNLOAD_MANIFEST.jsonl').read_text().splitlines():
        r=json.loads(line)
        if r.get('verified'):manifest[r['path']]=r
    files=[]
    for r in json.loads((C/'data/INDEX.json').read_text()):
        m=manifest[r['path']];p=C/r['path']
        if p.stat().st_size!=m['bytes']or digest(p)!=m['sha256']:
            raise RuntimeError('Original-byte pin mismatch '+str(p))
        files.append(dict(path=r['path'],bytes=p.stat().st_size,sha256=m['sha256']))
    fz=json.loads((C/'protocols/FREEZE.json').read_text())
    for r in fz['files']:
        if digest(C/r['path'])!=r['sha256']:raise RuntimeError('Frozen method mismatch '+r['path'])
    return dict(raw_files=len(files),raw_bytes=sum(r['bytes']for r in files),
                freeze_sha256=digest(C/'protocols/FREEZE.json'),external_bytes_hashed_only=True)


def independent_reconstruction(output):
    import independent_reconstruction as ir
    ir.OUT=output/'independent_reconstruction';ir.OUT.mkdir(exist_ok=True,parents=True)
    ir.verify_freeze();n=0
    for a in ir.source_allocation():
        if not ir.completed(a['subject'],a['split']):continue
        ir.reconstruct_subject(a['subject'],a);n+=1
    ir.aggregate();ir.exposure_order_audit()
    return dict(source_animals=n,output=str(ir.OUT.relative_to(C)),independent_original_bytes=True)


def replay(output,mode):
    from data_io import load_prefix_and_opportunities,exposure
    from run_forecasts import MODEL_FILES,seed_for
    from baselines import load_bank
    from learning_models import load_model
    from rollout import autonomous
    from uncertainty import apply_calibration
    fz=C/'protocols/FREEZE.json';config=C/'artifacts/calibration/CONFIG.json'
    bank=load_bank(C/'artifacts/baselines/nested_growth_bank.npz')
    alloc={r['subject']:r for r in json.loads((C/'protocols/SPLIT.json').read_text())['standard']}
    ids=[]
    for split,tag in [('animal_holdout','source_animals'),('lab_holdout','source_labs')]:
        ids+=sorted({p.name.split('__')[0]for p in(C/'artifacts/forecasts'/tag).glob('*__growth.npz')})
    if mode=='six':ids=sorted(ids,key=lambda s:hashlib.sha256(s.encode()).hexdigest())[:6]
    rows=[]
    for index,s in enumerate(ids):
        split=alloc[s]['split'];tag='source_animals'if split=='animal_holdout'else'source_labs'
        prefix,starts,meta=load_prefix_and_opportunities(s,split,freeze_path=fz,purpose='offline exact forecast regeneration from original prefix; no new future outcome input')
        seed=seed_for(s)
        for name in ['persistence','growth','reinforce','reinforce_pure','dnnglm','dnnglm32']:
            p=C/'artifacts/forecasts'/tag/(s+'__'+name+'.npz');old=np.load(p)
            competence=name if name in('persistence','growth')else None
            model=None if competence else load_model(MODEL_FILES[name])
            fresh=autonomous(model,prefix,starts,bank,n_particles=512,seed=seed,subject=s,competence=competence)
            primary=apply_calibration(fresh['samples'],name,seed+647,config_path=config)
            rawdiff=float(np.max(np.abs(fresh['samples']-old['samples'])))
            pdiff=float(np.max(np.abs(primary-old['samples_primary'])))
            wdiff=float(np.max(np.abs(fresh['weights']-old['weights'])))
            if max(rawdiff,pdiff,wdiff)>1e-10:raise AssertionError((s,name,rawdiff,pdiff,wdiff))
            rows.append(dict(subject=s,model=name,raw_curve_max_abs_difference=rawdiff,
                             primary_curve_max_abs_difference=pdiff,latent_weight_max_abs_difference=wdiff))
        print(json.dumps(dict(offline_forecast_subject=s,index=index+1,total=len(ids),max_difference=max(max(r['raw_curve_max_abs_difference'],r['primary_curve_max_abs_difference'],r['latent_weight_max_abs_difference'])for r in rows[-6:]))),flush=True)
    dump(output/'FORECAST_REPLAY.json',rows)
    exposure(dict(event='offline_original_forecasts_replayed',source_subjects=ids,models=6,network_calls=False,external_outcomes_read=False))
    return dict(subjects=len(ids),model_forecasts=len(rows),max_abs_difference=max([max(r['raw_curve_max_abs_difference'],r['primary_curve_max_abs_difference'],r['latent_weight_max_abs_difference'])for r in rows]or[0]))


def main():
    p=argparse.ArgumentParser();p.add_argument('--replay',choices=['all','six','none'],default='all')
    p.add_argument('--skip-reconstruction',action='store_true');p.add_argument('--output',default='artifacts/offline_reproduction')
    a=p.parse_args();out=C/a.output;out.mkdir(exist_ok=True,parents=True)
    # Explicitly disable Python network entry points. All artifact/dependency
    # reads below are local; no installer or acquisition command is invoked.
    socket.create_connection=forbidden;socket.socket.connect=forbidden
    started=time.monotonic();result=dict(utc=dt.datetime.now(dt.timezone.utc).isoformat(),python=sys.version,
            mode='offline; local original source bytes + frozen artifacts',network_entrypoints_disabled=True,external_outcomes_read=False)
    result['pins']=verify_bytes()
    if not a.skip_reconstruction:result['scores']=independent_reconstruction(out)
    if a.replay!='none':result['forecasts']=replay(out,a.replay)
    result['seconds']=time.monotonic()-started
    dump(out/'RESULT.json',result);print(json.dumps(result,indent=2),flush=True)

if __name__=='__main__':main()
