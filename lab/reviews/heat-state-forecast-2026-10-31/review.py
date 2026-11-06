"""Independent heat review. Cached, serial, scoped output only; no author imports."""
import os
os.environ['OPENBLAS_NUM_THREADS'] = '1'
os.environ['OMP_NUM_THREADS'] = '1'
os.environ['MKL_NUM_THREADS'] = '1'
import argparse
import datetime as dt
import hashlib
import io
import json
import math
from pathlib import Path
import zipfile
import shutil
import subprocess
import importlib.util
import base64
import difflib
import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
AUTHOR = ROOT / 'lab/tasks/heat-state-forecast-2026-10-31'
SOURCE = ROOT / 'sources/heat_state_forecast_2026-10-31'
LEDGER = HERE / 'ACCOUNTING.json'

def now():
    return dt.datetime.now(dt.timezone.utc).isoformat()

def save(name, value):
    (HERE / name).write_text(json.dumps(value, indent=2, allow_nan=False) + '\n')

def account():
    if LEDGER.exists():
        return json.loads(LEDGER.read_text())
    start = dt.datetime.now(dt.timezone.utc)
    a = dict(actual_scientific_start_utc=start.isoformat(),
             deadline_utc=(start+dt.timedelta(minutes=80)).isoformat(),
             review_cap_bytes=250000000, author_spent_bytes=413641303,
             lineage_cap_bytes=750000000, new_requests=0, new_acquisition_bytes=0,
             inherited_acquisition_bytes=191385005, inherited_requests=28,
             charged_bytes=2000000, context_reservation_bytes=2000000,
             context_note='Conservative 2MB ordinary context/code/JSON reads reservation, not raw outcome exposure.',
             reads=[])
    save('ACCOUNTING.json', a)
    return a

def reserve(path, size, kind):
    a = account()
    assert dt.datetime.now(dt.timezone.utc) < dt.datetime.fromisoformat(a['deadline_utc'])
    assert a['charged_bytes']+size <= a['review_cap_bytes']
    assert a['author_spent_bytes']+a['charged_bytes']+size <= a['lineage_cap_bytes']
    a['charged_bytes'] += int(size)
    a['reads'].append(dict(path=str(path.relative_to(ROOT)), reserved_at_utc=now(), bytes=int(size), kind=kind))
    save('ACCOUNTING.json', a)

def read(path):
    reserve(path, path.stat().st_size, 'file read/hash in same pass')
    return path.read_bytes()

def load_npz(path):
    b = read(path)
    expanded = sum(x.file_size for x in zipfile.ZipFile(io.BytesIO(b)).infolist())
    reserve(path, expanded, 'conservative expanded NPZ decoding charge, bytes already in memory')
    with np.load(io.BytesIO(b), allow_pickle=False) as z:
        return {k:z[k].copy() for k in z.files}

def scalar_loss(pred, truth, scales):
    values=[]
    for i in range(len(truth)):
        cells=[]
        for c in range(truth.shape[1]):
            for t in range(truth.shape[2]):
                if math.isfinite(float(truth[i,c,t])):
                    assert math.isfinite(float(pred[i,c,t]))
                    cells.append(((float(pred[i,c,t])-float(truth[i,c,t]))/float(scales[c]))**2)
        values.append(math.fsum(cells)/len(cells))
    return np.array(values)

def paired(a, b, rng):
    idx=rng.integers(len(a),size=(20000,len(a)))
    delta=(a-b)[idx].mean(axis=1)
    gain=1-b[idx].mean(axis=1)/a[idx].mean(axis=1)
    lo,hi=np.quantile(delta,[.025,.975])
    return dict(simple_mse=float(a.mean()),state_mse=float(b.mean()),
                state_fraction_gain=float(1-b.mean()/a.mean()),
                paired_difference_bootstrap95=[float(lo),float(hi)],
                fraction_gain_bootstrap95=np.quantile(gain,[.025,.975]).tolist(),
                state_better_animals=int(np.sum(b<a)),
                passes_investment_rule=bool(1-b.mean()/a.mean()>=.1 and lo>0),
                simple_per_animal=a.tolist(),state_per_animal=b.tolist())

def early():
    account()
    cfgbytes=read(AUTHOR/'EVALUATION_FREEZE.json')
    freeze=json.loads(cfgbytes)
    cfg=freeze['configuration']
    forecast_bytes=read(AUTHOR/'EVALUATION_FORECASTS.npz')
    expanded=sum(x.file_size for x in zipfile.ZipFile(io.BytesIO(forecast_bytes)).infolist())
    reserve(AUTHOR/'EVALUATION_FORECASTS.npz', expanded, 'expanded NPZ decode')
    with np.load(io.BytesIO(forecast_bytes)) as z:p={k:z[k].copy() for k in z.files}
    y=load_npz(AUTHOR/'EVALUATION_TRUTH.npz')
    recorded=json.loads(read(AUTHOR/'EVALUATION_RESULT.json'))
    saved=json.loads(read(AUTHOR/'FORECAST_SAVED.json'))
    access=json.loads(read(AUTHOR/'EVALUATION_OUTCOME_ACCESS.json'))
    assert hashlib.sha256(forecast_bytes).hexdigest()==saved['sha256']
    assert hashlib.sha256(cfgbytes).hexdigest()==saved['freeze_sha256']
    verified={}
    for name,digest in freeze['code_and_config_sha256'].items():
        got=hashlib.sha256(read(AUTHOR/name)).hexdigest()
        assert got==digest,name
        verified[name]=got
    assert all(dt.datetime.fromisoformat(x['at_utc'])>dt.datetime.fromisoformat(saved['at_utc']) for x in access)
    rng=np.random.default_rng(20261031)
    out=dict(at_utc=now(),method='independent scalar fsum endpoint loss; author helper not imported',
             uids=p['uids'].tolist(),frozen_hashes_verified=verified,
             forecast_hash_verified=True,freeze_hash_verified=True,
             recorded_forecast_precedes_all_recorded_numeric_access=True,
             chronology_limit='Saved records and unchanged bytes checked; no external proof of absence of earlier access.',
             modalities={})
    biggest=0.
    for mode in ['neural','behavior']:
        truth=y[mode+'_truth']
        a=scalar_loss(p[mode+'__simple'],truth,cfg['scales'][mode])
        b=scalar_loss(p[mode+'__state'],truth,cfg['scales'][mode])
        out['modalities'][mode]=paired(a,b,rng)
        keep=p['uids']!='2023-01-05-01'
        out['modalities'][mode]['without_named_uid']=paired(a[keep],b[keep],rng)
        out['modalities'][mode]['coverage']=np.isfinite(truth[:,:,0]).sum(axis=1).tolist()
        for label,loss in [('simple',a),('state',b)]:
            biggest=max(biggest,float(np.max(np.abs(loss-np.asarray(recorded['modalities'][mode]['per_worm_losses'][label])))))
    a=scalar_loss(p['fractional__local'],y['fractional_truth'],np.ones(len(cfg['classes'])))
    b=scalar_loss(p['fractional__state'],y['fractional_truth'],np.ones(len(cfg['classes'])))
    out['fractional']=paired(a,b,rng)
    out['largest_per_animal_loss_disagreement']=biggest
    out['joint_rule_passes']=all(x['passes_investment_rule'] for x in out['modalities'].values())
    save('EARLY_INDEPENDENT_CHECK.json',out)
    print(json.dumps(dict(at_utc=out['at_utc'],joint_rule_passes=out['joint_rule_passes'],
                         loss_disagreement=biggest,neural=out['modalities']['neural']['state_fraction_gain'],
                         behavior=out['modalities']['behavior']['state_fraction_gain'],
                         fractional=out['fractional']['state_fraction_gain'],
                         hashes_verified=len(verified)),indent=2))

ALPHAS=[.01,.1,1.,10.,100.]
EDGES=np.arange(30.,451.,60.)
SIMPLE=['persistence','recent','shared','relative','shared_constant','relax5','relax30','relax120']

def from_raw(j):
    """Rebuild allowed observations; no author extraction or feature code."""
    t_abs=np.array(j['timestamp_confocal'],dtype=float)
    event=j['events']['heat']
    assert len(event)==1
    hi=int(event[0])-1
    t=t_abs-t_abs[hi]
    a=np.array(j['trace_original'],dtype=float)
    assert a.shape==(int(j['num_neurons']),len(t))
    assert np.all(np.isfinite(a)) and np.all(np.diff(t)>0)
    pre=np.flatnonzero((t>=-450)&(t<-5))
    means=np.mean(a[:,pre],axis=1)
    sds=np.std(a[:,pre],axis=1)
    assert np.all(means>0) and np.all(sds>0)
    groups={}
    for index,label in j.get('labeled',{}).items():
        n=int(index)-1
        if float(label.get('confidence',0))<4 or '?' in label.get('label',''):
            continue
        name=label.get('neuron_class')
        if name and 0<=n<a.shape[0]: groups.setdefault(name,[]).append(n)
    labels=sorted(groups)
    standardized=(a-means[:,None])/sds[:,None]
    fractional=a/means[:,None]
    neural=np.stack([np.mean(standardized[groups[c]],axis=0) for c in labels])
    ratio=np.stack([np.mean(fractional[groups[c]],axis=0) for c in labels])
    velocity=np.array(j['velocity'],dtype=float)
    behavior=np.stack([velocity,velocity<0,np.array(j['pumping'],dtype=float),np.array(j['head_curvature'],dtype=float)])
    assert behavior.shape==(4,len(t)) and np.isfinite(behavior).all()
    return dict(uid=j['uid'],t=t,neural=neural,ratio=ratio,classes=np.array(labels),
                behavior=behavior,pre_mean=means,pre_sd=sds,
                groups=groups,heat_frame_1based=hi+1)

def channel(v,t,ratio=None):
    pre=(t>=-450)&(t<-5)
    mu=float(np.mean(v[pre]))
    last=float(np.mean(v[(t>=-65)&(t<-5)]))
    drift=float(np.mean(v[(t>=-125)&(t<-5)])-np.mean(v[(t>=-450)&(t<-330)]))
    lag=int(round(30./float(np.median(np.diff(t)))))
    centered=v[pre]-mu
    den=float(np.einsum('i,i->',centered,centered))
    autoc=float(np.einsum('i,i->',centered[:-lag],centered[lag:])/den) if den>1e-15 else 0.
    cv=float(np.std(ratio[pre])) if ratio is not None else float(np.std(v[pre])/(abs(mu)+.1))
    return [mu,last,drift,autoc,cv]

def bundle(data,classes,mode,scale='standardized'):
    n=len(data);nc=len(classes) if mode=='neural' else 2
    x=np.full((n,nc,5),np.nan);y=np.full((n,nc,7),np.nan)
    g=np.empty((n,2));r=np.full((n,len(classes)),np.nan)
    history=np.empty((n,10))
    for i,d in enumerate(data):
        t=d['t'];pre=(t>=-450)&(t<-5)
        g[i]=np.mean(d['behavior'][1:3][:,pre],axis=1)
        history[i]=np.array([channel(v,t) for v in d['behavior'][1:3]]).reshape(-1)
        neural=d['neural'] if scale=='standardized' else d['ratio']-1.
        mapping={str(c):k for k,c in enumerate(d['classes'])}
        for c,cl in enumerate(classes):
            if cl in mapping:r[i,c]=channel(neural[mapping[cl]],t,d['ratio'][mapping[cl]])[1]
        for c in range(nc):
            if mode=='neural':
                if classes[c] not in mapping:continue
                row=mapping[classes[c]];v=neural[row];rat=d['ratio'][row]
            else:v=d['behavior'][c+1];rat=None
            x[i,c]=channel(v,t,rat)
            for k,(left,right) in enumerate(zip(EDGES[:-1],EDGES[1:])):
                use=(t>=left)&(t<right)
                # Prefix-only data have no future endpoint; keep it NaN.
                if np.any(use):y[i,c,k]=np.mean(v[use])
    return dict(X=x,Y=y,G=g,R=r,H=history,mode=mode,uids=[d['uid'] for d in data])

def subset(b,ids):
    return {k:(v[ids] if isinstance(v,np.ndarray) else v) for k,v in b.items()}

def pcs(tr,te):
    m=np.nanmean(tr['R'],axis=0)
    a=np.where(np.isfinite(tr['R']),tr['R'],m)-m
    z=np.where(np.isfinite(te['R']),te['R'],m)-m
    _,_,vt=np.linalg.svd(a,full_matrices=False)
    return np.einsum('ij,kj->ik',a,vt[:2]),np.einsum('ij,kj->ik',z,vt[:2])

def independent_ridge(x,y,z,alpha):
    """Independent spectral ridge, rather than author's normal-equation solve."""
    center=np.mean(x,axis=0);scale=np.std(x,axis=0)
    scale=np.where(scale<1e-10,1.,scale)
    a=(x-center)/scale;zz=(z-center)/scale
    ym=np.mean(y,axis=0)
    u,s,vt=np.linalg.svd(a,full_matrices=False)
    projection=np.einsum('ij,ik->jk',u,y-ym)
    weights=(s/(s*s+len(x)*alpha))[:,None]*projection
    coefficient=np.einsum('ij,ik->jk',vt,weights)
    return ym+np.einsum('ij,jk->ik',zz,coefficient)

def base(x,model):
    if model in ['persistence','relative']:
        return np.repeat(x[:,:,0,None],7,axis=2)
    if model=='recent':return np.repeat(x[:,:,1,None],7,axis=2)
    if model.startswith('relax'):
        tau=float(model[5:])
        q=tau/60*(np.exp(-EDGES[:-1]/tau)-np.exp(-EDGES[1:]/tau))
        return x[:,:,0,None]+(x[:,:,1]-x[:,:,0])[:,:,None]*q
    return np.zeros((*x.shape[:2],7))

def predict(tr,te,model,alpha=None):
    y=tr['Y'];out=np.full((len(te['X']),y.shape[1],7),np.nan)
    if model in ['local','state','mean_behavior','history_behavior','history_behavior_pcs']:
        train_extra=test_extra=None
        if model in ['state','history_behavior_pcs']:
            pt,pe=pcs(tr,te)
        if model=='state':train_extra=np.concatenate([tr['G'],pt],axis=1);test_extra=np.concatenate([te['G'],pe],axis=1)
        if model=='mean_behavior':train_extra=tr['G'];test_extra=te['G']
        if model=='history_behavior':train_extra=tr['H'];test_extra=te['H']
        if model=='history_behavior_pcs':train_extra=np.concatenate([tr['H'],pt],axis=1);test_extra=np.concatenate([te['H'],pe],axis=1)
        for c in range(y.shape[1]):
            ok=np.isfinite(tr['X'][:,c]).all(axis=1)&np.isfinite(y[:,c]).all(axis=1)
            use=np.isfinite(te['X'][:,c]).all(axis=1)
            x=tr['X'][ok,c];z=te['X'][use,c]
            if train_extra is not None:
                x=np.concatenate([x,train_extra[ok]],axis=1)
                z=np.concatenate([z,test_extra[use]],axis=1)
            out[use,c]=independent_ridge(x,y[ok,c],z,alpha)
    else:
        out=base(te['X'],model)
        if model not in ['persistence','recent']:
            curve=np.nanmean(y-base(tr['X'],model),axis=0)
            if model=='shared_constant':curve=np.repeat(np.mean(curve,axis=1)[:,None],7,axis=1)
            out+=curve
    if tr['mode']=='behavior':
        out[:,0]=np.clip(out[:,0],0,1)
        out[:,1]=np.maximum(out[:,1],0)
    return out

def cv(tr,model,alpha):
    p=np.full_like(tr['Y'],np.nan)
    for i in range(len(p)):
        ids=np.delete(np.arange(len(p)),i)
        p[i]=predict(subset(tr,ids),subset(tr,np.array([i])),model,alpha)[0]
    return p

def maxdiff(a,b):
    assert a.shape==b.shape,(a.shape,b.shape)
    assert np.array_equal(np.isfinite(a),np.isfinite(b)), 'mask mismatch'
    mask=np.isfinite(a)
    return float(np.max(np.abs(a[mask]-b[mask]))) if np.any(mask) else 0.

def full():
    account()
    plan=read(HERE/'CONTRARY_PLAN.md')
    cfg=json.loads(read(AUTHOR/'EVALUATION_FREEZE.json'))['configuration']
    split=json.loads(read(AUTHOR/'SPLIT.json'))
    manifest=json.loads(read(SOURCE/'SOURCE_MANIFEST.json'))
    digests={x['uid']:x for x in manifest['items']}
    items=split['items'];data=[];raw_records=[];prefix_checks={}
    expected=sorted(items,key=lambda x:hashlib.sha256(('heat-state-v1:'+x['uid']).encode()).hexdigest())
    assert [x['uid'] for x in items]==[x['uid'] for x in expected]
    assert [x['part'] for x in items]==['development']*12+['evaluation']*7
    for item in items:
        raw=read(SOURCE/Path(item['path']).name)
        sha256=hashlib.sha256(raw).hexdigest()
        sha1=hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest()
        assert len(raw)==item['size'] and sha1==item['sha'] and sha256==digests[item['uid']]['sha256']
        j=json.loads(raw)
        d=from_raw(j);assert d['uid']==item['uid']
        data.append(d)
        raw_records.append(dict(uid=d['uid'],bytes=len(raw),sha256=sha256,git_blob=sha1,
                                heat_frame_1based=d['heat_frame_1based'],
                                pre_seconds=float(-d['t'][0]),post_seconds=float(d['t'][-1]),
                                classes=len(d['classes']),bilateral_classes=sum(len(v)>1 for v in d['groups'].values())))
        if item['part']=='evaluation':
            stored=load_npz(SOURCE/('prefix_'+item['uid']+'.npz'))
            cut=int(np.searchsorted(d['t'],-5.,side='left'))
            diffs={k:maxdiff(d[k][...,:cut],stored[k]) for k in ['t','neural','ratio','behavior']}
            diffs.update({k:maxdiff(d[k],stored[k]) for k in ['pre_mean','pre_sd']})
            assert np.array_equal(d['classes'],stored['classes'])
            assert max(diffs.values())<1e-12
            prefix_checks[item['uid']]=dict(cut=cut,last_allowed_time=float(d['t'][cut-1]),max_disagreements=diffs)
        del raw,j
    save('RAW_RECONSTRUCTION_PROGRESS.json',dict(at_utc=now(),raw_files=len(data),pinned_raw_bytes=sum(x['bytes'] for x in raw_records),all_hashes_verified=True,prefix_checks=prefix_checks))
    classes=cfg['classes']
    eligible=sorted(c for c in set(c for d in data[:12] for c in d['classes'].tolist()) if sum(c in d['classes'] for d in data[:12])>=10)
    assert eligible==classes
    pairs={}
    for scale in ['standardized','fractional']:
        pairs[scale]=(bundle(data[:12],classes,'neural',scale),bundle(data[12:],classes,'neural',scale))
    bt,be=bundle(data[:12],classes,'behavior'),bundle(data[12:],classes,'behavior')
    bscales=np.maximum(np.mean([np.std(d['behavior'][1:3][:,(d['t']>=-450)&(d['t']<-5)],axis=1) for d in data[:12]],axis=0),[.05,.1])
    assert np.max(np.abs(bscales-cfg['scales']['behavior']))<1e-12
    # Rebuild feature bundles using only a literal prefix slice; also poison all
    # future allowed channels, keeping source normalization already fixed.
    literal=[];poison=[]
    for d in data:
        cut=int(np.searchsorted(d['t'],-5.,side='left'))
        p=dict(d);q=dict(d)
        for key in ['t','neural','ratio','behavior']:p[key]=d[key][...,:cut].copy()
        for key in ['neural','ratio','behavior']:
            q[key]=d[key].copy();q[key][...,cut:]=1e100
        literal.append(p);poison.append(q)
    invariant={}
    for scale in ['standardized','fractional']:
        bb=bundle(data,classes,'neural',scale)
        pp=bundle(literal,classes,'neural',scale)
        qq=bundle(poison,classes,'neural',scale)
        invariant[scale]={k:dict(prefix_difference=maxdiff(bb[k],pp[k]),future_poison_difference=maxdiff(bb[k],qq[k])) for k in ['X','G','R','H']}
    assert max(v[key] for s in invariant.values() for v in s.values() for key in v)<1e-12
    del literal,poison
    saved_cv=load_npz(AUTHOR/'DEVELOPMENT_CV.npz')
    saved_y=load_npz(AUTHOR/'EVALUATION_TRUTH.npz')
    saved_p=load_npz(AUTHOR/'EVALUATION_FORECASTS.npz')
    tr,te=pairs['standardized']
    checks={}
    for mode,a,b in [('neural',tr,te),('behavior',bt,be)]:
        for source_name,key in [('own_features','X'),('global_features','G'),('recent_neural','R'),('truth','Y')]:
            checks['development_'+mode+'_'+source_name]=maxdiff(a[key],saved_cv[mode+'_'+source_name])
        checks['evaluation_'+mode+'_truth']=maxdiff(b['Y'],saved_y[mode+'_truth'])
    checks['evaluation_fractional_truth']=maxdiff(pairs['fractional'][1]['Y'],saved_y['fractional_truth'])
    forecasts={}
    cv_checks={}
    for mode,a,b in [('neural',tr,te),('behavior',bt,be)]:
        for model in SIMPLE+['local','state']:
            conf=cfg['primary'][mode]['configs'][model]
            forecasts[mode+'__'+model]=predict(a,b,model,conf['alpha'])
            cv_checks[mode+'__'+model]=maxdiff(cv(a,model,conf['alpha']),saved_cv[mode+'__'+conf['key']])
        if mode=='neural':forecasts[mode+'__simple']=forecasts[mode+'__local']
        else:
            combined=np.empty_like(be['Y'])
            for k,conf in enumerate(cfg['behavior_simple_components']):
                combined[:,k]=0. if conf['model']=='zero' else predict(bt,be,conf['model'],conf['alpha'])[:,k]
            forecasts[mode+'__simple']=combined
        for model in ['simple','state']:
            p=forecasts[mode+'__'+model]
            delay=np.empty_like(p);delay[:,:,:2]=b['X'][:,:,0,None];delay[:,:,2:]=p[:,:,:-2]
            forecasts[mode+'__'+model+'_delay120']=delay
        forecasts[mode+'__no_stimulus_relax120']=base(b['X'],'relax120')
    for model in ['shared','local','state']:
        forecasts['fractional__'+model]=predict(*pairs['fractional'],model,cfg['fractional'][model]['alpha'])
    replay={k:maxdiff(p,saved_p[k]) for k,p in forecasts.items()}
    assert max(checks.values())<1e-12 and max(replay.values())<1e-11 and max(cv_checks.values())<1e-11
    saved_inputs={}
    for scale,(a,b) in pairs.items():
        for part,part_bundle in [('development',a),('evaluation',b)]:
            for key in ['X','Y','G','R','H']:saved_inputs[scale+'_'+part+'_'+key]=part_bundle[key]
    for part,b in [('development',bt),('evaluation',be)]:
        for key in ['X','Y','G','R','H']:saved_inputs['behavior_'+part+'_'+key]=b[key]
    saved_inputs['classes']=np.array(classes);saved_inputs['uids']=saved_p['uids']
    np.savez_compressed(HERE/'INDEPENDENT_INPUTS.npz',**saved_inputs)
    np.savez_compressed(HERE/'RECONSTRUCTED_FORECASTS.npz',**forecasts)
    reconstruction=dict(at_utc=now(),raw_files=raw_records,source_manifest=str((SOURCE/'SOURCE_MANIFEST.json').relative_to(ROOT)),
                        source_commit=split['commit'],classes=classes,classes_reconstructed_from_source_labels=True,
                        behavior_scales=bscales.tolist(),prefix_checks=prefix_checks,
                        feature_invariance=invariant,input_disagreements=checks,
                        frozen_forecast_disagreements=replay,source_cv_disagreements=cv_checks,
                        checked_frozen_forecast_arrays=len(replay),author_helpers_imported=False,
                        limit='Mirror bytes, exported identities/events and processed observations checked. Original acquisition/raw calcium processing and label validity not independently reconstructed.')
    save('INDEPENDENT_RECONSTRUCTION.json',reconstruction)
    # Execute only the families declared in the saved plan, without evaluation
    # feature/penalty selection. Keep every source CV score and selected fit.
    families=['state','mean_behavior','history_behavior','history_behavior_pcs']
    out=dict(at_utc=now(),plan_sha256=hashlib.sha256(plan).hexdigest(),
             status='postvalidation consumed-data contrary comparison; no new primary test',
             alphas=ALPHAS,scales={})
    predictions={}
    rng=np.random.default_rng(20261031)
    for scale,(a,b) in pairs.items():
        rows={};chosen={};matched={}
        for model in families:
            scores={}
            for alpha in ALPHAS:
                p=cv(a,model,alpha)
                ls=scalar_loss(p,a['Y'],np.ones(len(classes)))
                scores[str(alpha)]=dict(mean_mse=float(ls.mean()),per_animal=ls.tolist())
            selected=min(ALPHAS,key=lambda v:scores[str(v)]['mean_mse'])
            pred=predict(a,b,model,selected)
            ls=scalar_loss(pred,b['Y'],np.ones(len(classes)))
            chosen[model]=ls
            predictions[scale+'__'+model]=pred
            rows[model]=dict(source_cv=scores,source_selected_alpha=selected,
                             evaluation_mse=float(ls.mean()),evaluation_per_animal=ls.tolist())
        original_alpha=rows['state']['source_selected_alpha']
        for model in families:
            pred=predict(a,b,model,original_alpha)
            ls=scalar_loss(pred,b['Y'],np.ones(len(classes)))
            matched[model]=ls
            predictions[scale+'__matched_'+model]=pred
            rows[model]['matched_original_full_alpha']=dict(alpha=original_alpha,evaluation_mse=float(ls.mean()),evaluation_per_animal=ls.tolist())
        comparisons={}
        for label,left,right in [('full_vs_mean_behavior','mean_behavior','state'),
                                 ('full_vs_history_behavior','history_behavior','state'),
                                 ('history_PC_increment','history_behavior','history_behavior_pcs'),
                                 ('history_vs_mean_behavior','mean_behavior','history_behavior')]:
            comparisons[label]=paired(chosen[left],chosen[right],rng)
            comparisons[label+'_matched_penalty']=paired(matched[left],matched[right],rng)
        frozen_local=scalar_loss(forecasts[('neural__simple' if scale=='standardized' else 'fractional__local')],b['Y'],np.ones(len(classes)))
        comparisons['full_vs_frozen_local']=paired(frozen_local,chosen['state'],rng)
        out['scales'][scale]=dict(families=rows,comparisons=comparisons)
    np.savez_compressed(HERE/'CONTRARY_FORECASTS.npz',**predictions)
    save('CONTRARY_RESULT.json',out)
    # Predesignated composition/influence and behavioral component checks.
    neural_truth=te['Y'];simple=forecasts['neural__simple'];state=forecasts['neural__state']
    common=np.isfinite(neural_truth).all(axis=(0,2))
    a=scalar_loss(simple,neural_truth,np.ones(len(classes)))
    b=scalar_loss(state,neural_truth,np.ones(len(classes)))
    influence=dict(at_utc=now(),common_classes=np.array(classes)[common].tolist(),
                   common_class_comparison=paired(scalar_loss(simple[:,common],neural_truth[:,common],np.ones(common.sum())),scalar_loss(state[:,common],neural_truth[:,common],np.ones(common.sum())),rng),
                   leave_one_worm_out_gain={},leave_one_class_out_gain={},class_errors={},behavior_components={})
    for i,uid in enumerate(saved_p['uids']):
        keep=np.arange(7)!=i
        influence['leave_one_worm_out_gain'][str(uid)]=float(1-b[keep].mean()/a[keep].mean())
    for c,cl in enumerate(classes):
        mask=np.arange(len(classes))!=c
        aa=scalar_loss(simple[:,mask],neural_truth[:,mask],np.ones(mask.sum()))
        bb=scalar_loss(state[:,mask],neural_truth[:,mask],np.ones(mask.sum()))
        influence['leave_one_class_out_gain'][cl]=float(1-bb.mean()/aa.mean())
        cells=np.isfinite(neural_truth[:,c])
        delta=((simple[:,c]-neural_truth[:,c])**2-(state[:,c]-neural_truth[:,c])**2)[cells]
        influence['class_errors'][cl]=dict(animals=int(cells[:,0].sum()),mean_squared_improvement=float(delta.mean()))
    for c,label in enumerate(['reverse_fraction','pumping']):
        per={model:np.mean((forecasts['behavior__'+model][:,c]-be['Y'][:,c])**2,axis=1) for model in ['persistence','shared','simple','state']}
        influence['behavior_components'][label]=dict(mean_mse={k:float(v.mean()) for k,v in per.items()},
                 per_animal={k:v.tolist() for k,v in per.items()},
                 simple_vs_shared=paired(per['shared'],per['simple'],rng),
                 simple_vs_persistence=paired(per['persistence'],per['simple'],rng))
    save('INFLUENCE_AND_BEHAVIOR.json',influence)
    print(json.dumps(dict(at_utc=now(),raw_files=len(data),checked_forecasts=len(replay),
                         max_input_disagreement=max(checks.values()),max_forecast_disagreement=max(replay.values()),
                         max_cv_disagreement=max(cv_checks.values()),
                         contrary={scale:{m:(r['source_selected_alpha'],r['evaluation_mse']) for m,r in s['families'].items()} for scale,s in out['scales'].items()},
                         charged_bytes=account()['charged_bytes']),indent=2))

def summarize():
    c=json.loads(read(HERE/'CONTRARY_RESULT.json'))
    influence=json.loads(read(HERE/'INFLUENCE_AND_BEHAVIOR.json'))
    scales={}
    for name,scale in c['scales'].items():
        scales[name]=dict(fits={m:dict(alpha=v['source_selected_alpha'],mse=v['evaluation_mse'],matched=v['matched_original_full_alpha']['evaluation_mse']) for m,v in scale['families'].items()},
                          comparisons={k:dict(gain=v['state_fraction_gain'],ci=v['fraction_gain_bootstrap95'],wins=v['state_better_animals']) for k,v in scale['comparisons'].items()})
    out=dict(at_utc=now(),scales=scales,influence=influence)
    save('DERIVED_SUMMARY.json',out)
    compact=dict(scales=scales,
                 common_classes=len(influence['common_classes']),
                 common_class_gain=influence['common_class_comparison']['state_fraction_gain'],
                 common_class_ci=influence['common_class_comparison']['fraction_gain_bootstrap95'],
                 leave_one_worm_out=influence['leave_one_worm_out_gain'],
                 leave_one_class_out_gain_range=[min(influence['leave_one_class_out_gain'].values()),max(influence['leave_one_class_out_gain'].values())],
                 top_class_improvements=sorted(influence['class_errors'].items(),key=lambda x:x[1]['mean_squared_improvement'],reverse=True)[:5],
                 behavior={label:dict(mse=r['mean_mse'],simple_vs_shared={k:v for k,v in r['simple_vs_shared'].items() if k in ['state_fraction_gain','fraction_gain_bootstrap95']},simple_vs_persistence={k:v for k,v in r['simple_vs_persistence'].items() if k in ['state_fraction_gain','fraction_gain_bootstrap95']}) for label,r in influence['behavior_components'].items()})
    print(json.dumps(compact,indent=2))

def exact_bootstrap(a,b):
    """All 1716 count vectors = all 7^7 ordered resamples with weights."""
    n=len(a)
    counts=[];weights=[]
    def visit(prefix,left):
        if len(prefix)==n-1:
            c=prefix+[left]
            counts.append(c)
            weights.append(math.factorial(n)/math.prod(math.factorial(x) for x in c)/n**n)
            return
        for x in range(left+1):visit(prefix+[x],left-x)
    visit([],n)
    c=np.array(counts);w=np.array(weights)
    assert abs(float(w.sum())-1)<1e-12
    ma=np.einsum('ij,j->i',c,a)/n
    mb=np.einsum('ij,j->i',c,b)/n
    gains=1-mb/ma;delta=ma-mb
    def interval(values):
        order=np.argsort(values,kind='stable')
        cumulative=np.cumsum(w[order])
        return [float(values[order[min(np.searchsorted(cumulative,p,side='left'),len(order)-1)]]) for p in [.025,.975]]
    return dict(count_vectors=len(c),ordered_resamples=n**n,weight_sum=float(w.sum()),
                fraction_gain_interval95=interval(gains),paired_difference_interval95=interval(delta),
                conditional_probability_nonpositive_gain=float(w[gains<=0].sum()),
                note='Exact conditional empirical bootstrap; no coverage/multiplicity/biological power guarantee.')

def final_checks():
    read(HERE/'FINAL_CHECK_PLAN.md')
    early_result=json.loads(read(HERE/'EARLY_INDEPENDENT_CHECK.json'))
    contrary=json.loads(read(HERE/'CONTRARY_RESULT.json'))
    exact={}
    for name,row in early_result['modalities'].items():
        exact['primary_'+name]=exact_bootstrap(np.array(row['simple_per_animal']),np.array(row['state_per_animal']))
    for scale,s in contrary['scales'].items():
        row=s['comparisons']['history_PC_increment']
        exact['history_PC_'+scale]=exact_bootstrap(np.array(row['simple_per_animal']),np.array(row['state_per_animal']))
    save('EXACT_BOOTSTRAP_CHECK.json',dict(at_utc=now(),results=exact))
    print(json.dumps(dict(exact_bootstrap=exact),indent=2))
    source_check()

def source_check():
    doc=read(ROOT/'sources/looper_repo/atanas-data/DATASET.md')
    docsha=hashlib.sha1(b'blob '+str(len(doc)).encode()+b'\0'+doc).hexdigest()
    record=dict(at_utc=now(),mirror_documentation_blob_actual=docsha,
                mirror_documentation_blob_claimed='38353b53afffeac6c41c8fea6a7ec9bd09269b69',
                mirror_documentation_blob_matches=docsha=='38353b53afffeac6c41c8fea6a7ec9bd09269b69',
                pdf='sources/atanas2023.pdf',network_requests=0,extractor=None,excerpts={})
    if not record['mirror_documentation_blob_matches']:
        save('SOURCE_PIN_FAILURE.json',dict(at_utc=now(),actual=docsha,claimed=record['mirror_documentation_blob_claimed'],
               failed_command='review.py --final-checks',exit_code=1,
               effect='Independent exact-bootstrap output saved before documentation assertion failed. All19 raw payload pins passed separately. Documentation provenance mismatch needs qualification.'))
    extractor=shutil.which('pdftotext')
    if extractor:
        pdf=read(ROOT/'sources/atanas2023.pdf')
        completed=subprocess.run([extractor,'-','-'],input=pdf,capture_output=True,check=True,timeout=45)
        plain=completed.stdout.decode('utf-8',errors='replace')
        record.update(extractor=extractor,pdf_sha256=hashlib.sha256(pdf).hexdigest(),pdf_bytes=len(pdf),extracted_characters=len(plain))
        (HERE/'ATANAS_CACHED_TEXT.txt').write_text(plain)
        lower=plain.lower()
        for term in ['interpolat','bleach','0.39','single time','1436','state-dependent','neuroPAL','10.0']:
            starts=[];p=0
            while len(starts)<5:
                at=lower.find(term.lower(),p)
                if at<0:break
                starts.append(plain[max(0,at-300):at+700]);p=at+len(term)
            record['excerpts'][term]=starts
    else:
        record['limit']='pdftotext unavailable; primary paper not independently reread. Mirror documentation and inherited author source audit remain explicit.'
    save('SOURCE_CHECK.json',record)
    print(json.dumps(dict(source={k:v for k,v in record.items() if k!='excerpts'},excerpts=record['excerpts']),indent=2))

def reserve_document_request(base64_request=False):
    a=account()
    assert a['new_requests']<2
    assert a['new_acquisition_bytes']+2000000<=5000000
    assert a['inherited_acquisition_bytes']+a['new_acquisition_bytes']+2000000<200000000
    a['new_requests']+=1
    a['new_acquisition_bytes']+=2000000
    previous=a.get('request_reservation')
    a['request_reservation']=dict(at_utc=now(),bytes=2000000,
          purpose='Resolve named cached-vs-pinned documentation mismatch, exact commit contents API text only.',
          url='https://api.github.com/repos/vanshkumar/LOOPER-freely-moving-worms/contents/atanas-data/DATASET.md?ref=513782b42ad77e75f35adfbc70064b7418ff674a')
    if base64_request:a['request_reservation']['purpose']='Retrieve exact base64 bytes of same pinned documentation to separate connector text normalization from true source-pin mismatch.'
    if 'request_reservations' not in a:a['request_reservations']=([previous] if previous else [])
    a['request_reservations'].append(a['request_reservation'])
    save('ACCOUNTING.json',a)
    reserve(HERE/'SOURCE_DOCUMENT_RESPONSE.json',2000000,'conservative connector text response reservation before one public request')
    print(json.dumps(a['request_reservation'],indent=2))

def primary_text():
    options=[m for m in ['pypdf','PyPDF2','pdfplumber'] if importlib.util.find_spec(m) is not None]
    record=dict(at_utc=now(),available_existing_modules=options,network_requests=0,excerpts={})
    if not options:
        record['limit']='No existing PDF text module or pdftotext; primary PDF not independently reread. Source/author literature audit remains attributed.'
    else:
        pdf=read(ROOT/'sources/atanas2023.pdf')
        if options[0]=='pdfplumber':
            import pdfplumber
            with pdfplumber.open(io.BytesIO(pdf)) as reader:plain='\n'.join(page.extract_text() or '' for page in reader.pages)
        else:
            module=__import__(options[0])
            reader=module.PdfReader(io.BytesIO(pdf))
            plain='\n'.join(page.extract_text() or '' for page in reader.pages)
        record.update(extractor=options[0],pdf_bytes=len(pdf),pdf_sha256=hashlib.sha256(pdf).hexdigest(),extracted_characters=len(plain))
        (HERE/'ATANAS_CACHED_TEXT.txt').write_text(plain)
        lower=plain.lower()
        for term in ['interpolat','bleach','0.39','single time','1436','state-dependent','neuropal','10.0']:
            at=0;snippets=[]
            while len(snippets)<4:
                found=lower.find(term,at)
                if found<0:break
                snippets.append(plain[max(0,found-250):found+750]);at=found+len(term)
            record['excerpts'][term]=snippets
    save('PRIMARY_TEXT_CHECK.json',record)
    print(json.dumps(record,indent=2))

def verify_document():
    raw_response=json.loads(read(HERE/'SOURCE_DOCUMENT_EXACT_RESPONSE.json'))
    content=raw_response['structuredContent']['content']
    remote=base64.b64decode(content)
    reserve(HERE/'SOURCE_DOCUMENT_EXACT_RESPONSE.json',len(remote),'decoded exact public documentation bytes')
    local=read(ROOT/'sources/looper_repo/atanas-data/DATASET.md')
    def blob(b):return hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest()
    diff=''.join(difflib.unified_diff(remote.decode().splitlines(True),local.decode().splitlines(True),fromfile='pinned_remote_DATASET.md',tofile='working_cache_DATASET.md'))
    (HERE/'SOURCE_DOCUMENT_DIFF.txt').write_text(diff)
    (HERE/'PINNED_DATASET.md').write_bytes(remote)
    out=dict(at_utc=now(),remote_url='https://api.github.com/repos/vanshkumar/LOOPER-freely-moving-worms/contents/atanas-data/DATASET.md?ref=513782b42ad77e75f35adfbc70064b7418ff674a',
             remote_bytes=len(remote),remote_git_blob=blob(remote),remote_sha256=hashlib.sha256(remote).hexdigest(),
             local_bytes=len(local),local_git_blob=blob(local),claimed_blob='38353b53afffeac6c41c8fea6a7ec9bd09269b69',
             claimed_pin_matches_exact_remote=blob(remote)=='38353b53afffeac6c41c8fea6a7ec9bd09269b69',
             cache_matches_remote=local==remote,
             normalized_newlines_match=local.replace(b'\r\n',b'\n')==remote.replace(b'\r\n',b'\n'),
             diff_lines=len(diff.splitlines()),new_specific_public_text_requests=2,
             upstream_limit='This is mirror documentation, not original acquisition/preprocessing-code reconstruction. Primary paper was not independently reread: no existing local PDF extractor.')
    save('SOURCE_DOCUMENT_VERIFICATION.json',out)
    print(json.dumps(out,indent=2));print(diff[:5000])

def joint_behavior():
    inputs=load_npz(HERE/'INDEPENDENT_INPUTS.npz')
    forecasts=load_npz(HERE/'RECONSTRUCTED_FORECASTS.npz')
    cfg=json.loads(read(AUTHOR/'EVALUATION_FREEZE.json'))['configuration']
    y=inputs['behavior_evaluation_Y'];scales=cfg['scales']['behavior']
    per={m:scalar_loss(forecasts['behavior__'+m],y,scales) for m in ['simple','shared','persistence','state']}
    rng=np.random.default_rng(20261031)
    out=dict(at_utc=now(),independent_truth_and_forecasts=True,scales=scales,
             per_animal={m:x.tolist() for m,x in per.items()},
             mean_mse={m:float(x.mean()) for m,x in per.items()},
             simple_vs_shared=paired(per['shared'],per['simple'],rng),
             exact_simple_vs_shared=exact_bootstrap(per['shared'],per['simple']))
    save('JOINT_BEHAVIOR_CHECK.json',out)
    print(json.dumps(out,indent=2))

def closeout():
    import sys
    names=['EARLY_INDEPENDENT_CHECK.json','INDEPENDENT_RECONSTRUCTION.json','CONTRARY_RESULT.json',
           'CONTRARY_FORECASTS.npz','INDEPENDENT_INPUTS.npz','RECONSTRUCTED_FORECASTS.npz',
           'INFLUENCE_AND_BEHAVIOR.json','JOINT_BEHAVIOR_CHECK.json','EXACT_BOOTSTRAP_CHECK.json',
           'SOURCE_DOCUMENT_VERIFICATION.json','SOURCE_DOCUMENT_EXACT_RESPONSE.json','PINNED_DATASET.md',
           'CONTRARY_PLAN.md','FINAL_CHECK_PLAN.md','review.py']
    outputs={}
    for name in names:
        b=read(HERE/name)
        outputs[name]=dict(bytes=len(b),sha256=hashlib.sha256(b).hexdigest())
    save('OUTPUT_MANIFEST.json',dict(at_utc=now(),artifacts=outputs,
         runtime=dict(python=sys.version,numpy=np.__version__,platform=sys.platform,blas_omp_threads=1),
         inputs='INDEPENDENT_RECONSTRUCTION.json pins all19 original payloads; ACCOUNTING.json retains every reservation.',
         jobs=0,job_basis='All launched commands/subprocesses returned; no background jobs were started.',
         original_source_url='https://github.com/vanshkumar/LOOPER-freely-moving-worms/tree/513782b42ad77e75f35adfbc70064b7418ff674a/atanas-data/heat',
         license='Original data license and equivalence to Zenodo deposit not independently certified; local research cache only.'))
    a=account();a['scientific_complete_utc']=now();a['jobs']=0
    a['combined_scientific_read_bytes']=a['charged_bytes']+a['author_spent_bytes']
    a['combined_acquisition_bytes_reserved']=a['inherited_acquisition_bytes']+a['new_acquisition_bytes']
    a['combined_requests']=a['inherited_requests']+a['new_requests']
    a['status']='complete; finite assignment ended; no continuation or new acquisition authorized'
    save('ACCOUNTING.json',a)
    print(json.dumps({k:a[k] for k in ['actual_scientific_start_utc','deadline_utc','scientific_complete_utc','charged_bytes','combined_scientific_read_bytes','combined_acquisition_bytes_reserved','combined_requests','jobs']},indent=2))

if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--early', action='store_true')
    parser.add_argument('--full', action='store_true')
    parser.add_argument('--summarize', action='store_true')
    parser.add_argument('--final-checks', action='store_true')
    parser.add_argument('--sources', action='store_true')
    parser.add_argument('--reserve-document-request', action='store_true')
    parser.add_argument('--reserve-base64-request', action='store_true')
    parser.add_argument('--primary-text', action='store_true')
    parser.add_argument('--verify-document', action='store_true')
    parser.add_argument('--joint-behavior', action='store_true')
    parser.add_argument('--closeout', action='store_true')
    args=parser.parse_args()
    if args.early: early()
    if args.full: full()
    if args.summarize: summarize()
    if args.final_checks: final_checks()
    if args.sources: source_check()
    if args.reserve_document_request: reserve_document_request()
    if args.reserve_base64_request: reserve_document_request(True)
    if args.primary_text: primary_text()
    if args.verify_document: verify_document()
    if args.joint_behavior: joint_behavior()
    if args.closeout: closeout()
