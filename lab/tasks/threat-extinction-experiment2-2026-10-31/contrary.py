import argparse
import datetime as dt
import hashlib
import json
import resource
import numpy as np
from analysis import ROOT,source_data,scaled,arrays,prior_fit,unit_losses,predict,save

def static(units,params):
    initial=np.array([u['y'][u['first']] for u in units])
    mean=initial.mean(axis=1,keepdims=True)
    levels=params['s']*mean+params['z']*(initial-mean)
    cue=np.array([u['cue'] for u in units])
    pred=np.take_along_axis(levels,cue,axis=1)
    return np.clip(pred,0.,1.) if units[0]['channel']=='expectancy' else np.maximum(pred,0.)

def fit_static(units):
    a=arrays(units,prior_fit(units))
    best=None
    for s in [0.,.25,.5,.75,1.,1.25,1.5]:
        for z in [0.,.25,.5,.75,1.,1.5]:
            parameters={'s':s,'z':z}
            mse=float(unit_losses(a,static(units,parameters)).mean())
            if best is None or mse<best['training_mse']-1e-15:
                best={'parameters':parameters,'training_mse':mse}
    return best

def freeze():
    assert not (ROOT/'CONTRARY_FREEZE.json').exists()
    data,_=source_data('development')
    models={}
    for channel,units in data.items():
        for mode in ['primary']+(['past_acquisition_scale'] if channel=='physiology' else []):
            models[channel+'/'+mode]=fit_static(scaled(units,mode!='primary'))
    save('CONTRARY_MODELS.json',models)
    names=['contrary.py','CONTRARY_PLAN.md','CONTRARY_MODELS.json','FREEZE.json','EVALUATION.json']
    save('CONTRARY_FREEZE.json',{'utc':dt.datetime.now(dt.timezone.utc).isoformat(),
        'postvalidation':True,'pins':{n:hashlib.sha256((ROOT/n).read_bytes()).hexdigest() for n in names},
        'read_charge_bytes':3000000,'peak_rss_bytes':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss})
    print(json.dumps(models,indent=2))

def score():
    frozen=json.loads((ROOT/'CONTRARY_FREEZE.json').read_text())
    assert all(hashlib.sha256((ROOT/n).read_bytes()).hexdigest()==h for n,h in frozen['pins'].items())
    assert not (ROOT/'CONTRARY.json').exists()
    test,_=source_data('evaluation')
    static_models=json.loads((ROOT/'CONTRARY_MODELS.json').read_text())
    main_models=json.loads((ROOT/'FROZEN_MODELS.json').read_text())
    result={}
    rng=np.random.default_rng(202611010233)
    forecasts=[]
    for key,model in static_models.items():
        channel,mode=key.split('/')
        units=scaled(test[channel],mode!='primary')
        a,pc=predict(units,main_models[key]['common'])
        ps=static(units,model['parameters'])
        lc,ls=unit_losses(a,pc),unit_losses(a,ps)
        delta=lc-ls
        index=rng.integers(0,len(units),size=(10000,len(units)))
        sample=delta[index].mean(axis=1)
        ratio=sample/lc[index].mean(axis=1)
        out={'n':len(units),'common_mse':float(lc.mean()),'static_mse':float(ls.mean()),
             'static_gain_mse':float(delta.mean()),'static_fractional_reduction':float(delta.mean()/lc.mean()),
             'static_gain_mse_bootstrap95':np.quantile(sample,[.025,.975]).tolist(),
             'static_fractional_reduction_bootstrap95':np.quantile(ratio,[.025,.975]).tolist(),
             'static_participants_improving':int(np.sum(delta>0)),
             'per_participant':[{'id':u['id'],'common_loss':float(lc[i]),'static_loss':float(ls[i])} for i,u in enumerate(units)]}
        result[key]=out
        for i,u in enumerate(units):
            for j in np.flatnonzero(u['future']):
                forecasts.append({'comparison':key,'id':u['id'],'position':int(j+1),'cue':int(u['cue'][j]),
                                  'observed':float(u['y'][j]),'static':float(ps[i,j]),'common':float(pc[i,j])})
        print(key,json.dumps({k:v for k,v in out.items() if k!='per_participant'},indent=2))
    save('CONTRARY_FORECASTS.json',forecasts)
    save('CONTRARY.json',{'utc':dt.datetime.now(dt.timezone.utc).isoformat(),'postvalidation':True,
        'results':result,'bootstrap_seed':202611010233,'read_charge_bytes':6000000,
        'peak_rss_bytes':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss})

if __name__=='__main__':
    ap=argparse.ArgumentParser()
    ap.add_argument('stage',choices=['freeze','score'])
    globals()[ap.parse_args().stage]()
