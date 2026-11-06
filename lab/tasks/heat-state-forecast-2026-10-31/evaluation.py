"""Separate forecast-saving and subsequent held-out outcome scoring commands."""
import os
os.environ['OPENBLAS_NUM_THREADS']='1'
os.environ['OMP_NUM_THREADS']='1'
import argparse,copy,hashlib,json,pathlib
import numpy as np
import forecast as f
from prepare import extract
def check_freeze():
    freeze=json.loads((f.TASK/'EVALUATION_FREEZE.json').read_text())
    for name,digest in freeze['code_and_config_sha256'].items():
        assert hashlib.sha256((f.TASK/name).read_bytes()).hexdigest()==digest,(name,'freeze changed')
    return freeze
def prefixes():
    out=[]
    for x in json.loads((f.TASK/'SPLIT.json').read_text())['items']:
        if x['part']=='evaluation':
            with np.load(f.SRC/('prefix_'+x['uid']+'.npz')) as z:d={k:z[k].copy() for k in z.files}
            d['uid']=x['uid'];out.append(d)
    return out
def baseline(train,test,cfg):
    if train['mode']=='neural':return f.predict(train,test,cfg['neural_simple']['model'],cfg['neural_simple']['alpha'])
    out=np.empty((len(test['X']),2,7))
    for k,c in enumerate(cfg['behavior_simple_components']):
        if c['model']=='zero':out[:,k]=0.
        else:out[:,k]=f.predict(train,test,c['model'],c['alpha'])[:,k]
    return out
def delay(p,b):
    q=np.empty_like(p);q[:,:,:2]=b['X'][:,:,0,None];q[:,:,2:]=p[:,:,:-2]
    return q
def predict_all():
    freeze=check_freeze();cfg=freeze['configuration'];ds=f.load_development();ps=prefixes()
    arrays={};log={}
    for mode in ['neural','behavior']:
        train=f.make_bundle(ds,cfg['classes'],mode);test=f.make_bundle(ps,cfg['classes'],mode,False)
        for model in f.SIMPLE+['local','state']:
            conf=cfg['primary'][mode]['configs'][model]
            arrays[mode+'__'+model]=f.predict(train,test,model,conf['alpha'])
        arrays[mode+'__simple']=baseline(train,test,cfg)
        arrays[mode+'__simple_delay120']=delay(arrays[mode+'__simple'],test)
        arrays[mode+'__state_delay120']=delay(arrays[mode+'__state'],test)
        arrays[mode+'__no_stimulus_relax120']=f.simple_base(test['X'],'relax120')
        log[mode]=dict(shape=list(arrays[mode+'__simple'].shape),finite_cells=int(np.isfinite(arrays[mode+'__simple']).sum()),future_outcome_cells_used=0)
    dd=copy.deepcopy(ds);pp=copy.deepcopy(ps)
    for d in dd+pp:d['neural']=d['ratio']-1.
    train=f.make_bundle(dd,cfg['classes'],'neural');test=f.make_bundle(pp,cfg['classes'],'neural',False)
    for model in ['shared','local','state']:
        arrays['fractional__'+model]=f.predict(train,test,model,cfg['fractional'][model]['alpha'])
    arrays['uids']=np.asarray([d['uid'] for d in ps])
    dest=f.TASK/'EVALUATION_FORECASTS.npz';assert not dest.exists()
    np.savez_compressed(dest,**arrays)
    f.save('FORECAST_SAVED.json',dict(at_utc=f.now(),uids=arrays['uids'].tolist(),forecast_file=dest.name,sha256=hashlib.sha256(dest.read_bytes()).hexdigest(),freeze_sha256=hashlib.sha256((f.TASK/'EVALUATION_FREEZE.json').read_bytes()).hexdigest(),status='all evaluation forecasts saved before full numeric outcome decoding',modalities=log))
    print(json.dumps(json.loads((f.TASK/'FORECAST_SAVED.json').read_text()),indent=2))
def summary(simple,state,idx,rng):
    a=simple[idx];b=state[idx];n=len(idx)
    boot=rng.integers(0,n,(20000,n));difference=(a-b)[boot].mean(axis=1)
    fraction=1-b[boot].mean(axis=1)/a[boot].mean(axis=1)
    dlo,dhi=np.quantile(difference,[.025,.975]);flo,fhi=np.quantile(fraction,[.025,.975])
    gain=1-b.mean()/a.mean()
    return dict(animals=n,simple_mse=float(a.mean()),state_mse=float(b.mean()),state_fraction_gain=float(gain),paired_difference=float(np.mean(a-b)),paired_difference_bootstrap95=[float(dlo),float(dhi)],fraction_gain_bootstrap95=[float(flo),float(fhi)],state_better_animals=int(np.sum(b<a)),passes_investment_rule=bool(gain>=.1 and dlo>0))
def score():
    freeze=check_freeze();cfg=freeze['configuration']
    pre=json.loads((f.TASK/'FORECAST_SAVED.json').read_text());fp=f.TASK/pre['forecast_file']
    assert hashlib.sha256(fp.read_bytes()).hexdigest()==pre['sha256']
    access=[];ds=[]
    for x in json.loads((f.TASK/'SPLIT.json').read_text())['items']:
        if x['part']!='evaluation':continue
        raw=f.SRC/pathlib.Path(x['path']).name;b=raw.read_bytes()
        assert hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest()==x['sha']
        j=json.loads(b);d=extract(j);d['uid']=x['uid'];ds.append(d)
        np.savez_compressed(f.SRC/('derived_'+x['uid']+'.npz'),**d)
        access.append(dict(uid=x['uid'],bytes=len(b),at_utc=f.now(),numerical_outcomes_status='full outcomes decoded after FORECAST_SAVED timestamp',raw_sha256=hashlib.sha256(b).hexdigest()))
        f.save('EVALUATION_OUTCOME_ACCESS.json',access)
    rng=np.random.default_rng(20261031);result=dict(at_utc=f.now(),forecast_saved_utc=pre['at_utc'],uids=[d['uid'] for d in ds],modalities={},all_endpoints={},interpretation='one untouched numeric-outcome test after full source freeze; source/publication summaries previously exposed; bootstrap conditional on this selected family, not equivalence or biological mechanism')
    arrays={}
    with np.load(fp) as preds:
        for mode in ['neural','behavior']:
            bundle=f.make_bundle(ds,cfg['classes'],mode);y=bundle['Y'];arrays[mode+'_truth']=y
            names=[k.split('__',1)[1] for k in preds.files if k.startswith(mode+'__')]
            per={}
            for name in names:
                p=preds[mode+'__'+name];ls=f.losses(p,y,cfg['scales'][mode]);per[name]=ls
            main=summary(per['simple'],per['state'],np.arange(len(ds)),rng)
            main['per_worm_losses']={k:v.tolist() for k,v in per.items()}
            main['mean_losses']={k:float(v.mean()) for k,v in per.items()}
            main['local_simple_gain_over_shared']=float(1-per['simple'].mean()/per['shared'].mean())
            main['without_individually_named_publication_uid']=summary(per['simple'],per['state'],np.array([i for i,d in enumerate(ds) if d['uid']!='2023-01-05-01']),rng)
            if mode=='neural':main['class_coverage_per_worm']=np.isfinite(y[:,:,0]).sum(axis=1).tolist()
            else:
                comp={}
                for name in names:
                    c=np.mean((preds[mode+'__'+name]-y)**2,axis=(0,2))
                    comp[name]=dict(reverse_fraction_mse=float(c[0]),pumping_mse=float(c[1]))
                main['component_mse']=comp
            result['modalities'][mode]=main
        frac=copy.deepcopy(ds)
        for d in frac:d['neural']=d['ratio']-1.
        y=f.make_bundle(frac,cfg['classes'],'neural')['Y'];arrays['fractional_truth']=y
        per={m:f.losses(preds['fractional__'+m],y,np.ones(len(cfg['classes']))) for m in ['shared','local','state']}
        result['fractional_fluorescence']=summary(per['local'],per['state'],np.arange(len(ds)),rng)
        result['fractional_fluorescence']['mean_losses']={k:float(v.mean()) for k,v in per.items()}
    result['main_rule_passes_both_modalities']=all(x['passes_investment_rule'] for x in result['modalities'].values())
    np.savez_compressed(f.TASK/'EVALUATION_TRUTH.npz',**arrays)
    f.save('EVALUATION_RESULT.json',result)
    print(json.dumps(result,indent=2))
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--predict',action='store_true');p.add_argument('--score',action='store_true');a=p.parse_args()
    assert a.predict!=a.score,'Use distinct commands so forecast saving precedes outcome interpretation'
    if a.predict:predict_all()
    if a.score:score()
