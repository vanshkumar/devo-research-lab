"""Finite conditional-extinction forecast comparison; no network access."""
import os
for _thread_var in ['OPENBLAS_NUM_THREADS', 'OMP_NUM_THREADS', 'MKL_NUM_THREADS', 'VECLIB_MAXIMUM_THREADS', 'NUMEXPR_NUM_THREADS']:
    os.environ[_thread_var] = '1'
import argparse
import collections
import datetime as dt
import hashlib
import json
import pathlib
import resource
import zipfile
import numpy as np
from first_data_check import first_sav

ROOT = pathlib.Path(__file__).resolve().parent
CUES = ['CSplus1', 'CSplus2', 'CSmin']
GRID = {'q': [0., .25, .5, 1.], 'k': [0., .05, .15, .4, 1., 2.],
        'alpha': [0., .05, .15, .4, 1., 2.], 'w': [1., .75, .5, .25, 0.]}

def save(name, obj):
    (ROOT / name).write_text(json.dumps(obj, indent=2, allow_nan=False)+'\n')

def source_data(group):
    cert = json.loads((ROOT / 'SOURCE_CERTIFICATION.json').read_text())
    ids = cert[group+'_ids']
    if group == 'evaluation':
        assert (ROOT / 'FREEZE.json').exists(), 'evaluation requires saved final freeze'
    meta = cert['metadata']
    z = zipfile.ZipFile(ROOT / 'sources/experiment2.zip')
    channels = {}
    for file, metadata in meta.items():
        indices = {k for k, row in enumerate(metadata) if int(row['PP_number']) in ids}
        name = next(n for n in z.namelist() if n.endswith('/'+file))
        parsed = first_sav(z.read(name), case_limit=60, case_indices=indices)['cases']
        channels[file] = {int(row['PP_number']): row for row in parsed if row}
    units, checks = {}, []
    for participant in ids:
        scr = channels['SCR data_SE_exp2.sav'][participant]
        expect = channels['US expectancy_SE_exp2.sav'][participant]
        rows = [r for r in cert['inputs'][str(participant)] if r['blocknum']=='4' and r['trialcode'].startswith('CS')]
        occurrence = collections.Counter()
        cue, ordinal, phys, rating = [], [], [], []
        for r in rows:
            c = {'CS1':0, 'CS2':1, 'CSm':2}[r['trialcode'].split('_')[0]]
            n = occurrence[c]
            occurrence[c] += 1
            cue.append(c)
            ordinal.append(n)
            phys.append(scr[f'GSR1{CUES[c]}_{6+n}'])
            rating.append(expect[f'Ext_{CUES[c]}_{1+n}'])
        first = [cue.index(c) for c in range(3)]
        prefix_end = max(first)+1
        acq = [scr[f'GSR1{c}_{n}'] for c in CUES for n in range(1,6)]
        us = [scr[f'GSR1US_{n}'] for n in range(1,11)]
        available_acq = [max(v/1000, 0.) for v in acq if v is not None and np.isfinite(v)]
        scale = max([.02]+available_acq)
        u = [np.sqrt(v/1000) if v/1000>.02 else 0. for v in us if v is not None and np.isfinite(v)]
        for kind, raw in [('physiology', phys), ('expectancy', rating)]:
            if any(v is None or not np.isfinite(v) for v in raw):
                checks.append({'id': participant, 'channel': kind, 'included':False,
                               'reason':'missing/nonfinite required extinction feature',
                               'missing_count':sum(v is None or not np.isfinite(v) for v in raw)})
                continue
            v = np.array(raw, dtype=float)
            if kind == 'physiology':
                y = np.sqrt(np.where(v/1000>.02, v/1000, 0.))
            else:
                assert np.all((v>=1)&(v<=9))
                y = (v-1)/8
            unit = {'id':participant, 'channel':kind, 'y':y, 'cue':np.array(cue),
                    'ordinal':np.array(ordinal), 'first':np.array(first), 'prefix_end':prefix_end,
                    'future':np.arange(18)>=prefix_end, 'us':float(np.mean(u)) if u and kind=='physiology' else None,
                    'scale':float(np.sqrt(scale)), 'condition':expect['Conditie']}
            units.setdefault(kind, []).append(unit)
            checks.append({'id':participant, 'channel':kind, 'included':True,
                           'prefix_end':prefix_end, 'future_count':int(unit['future'].sum()),
                           'zero_extinction_features':int(np.sum(y==0))})
        # Check numeric decoder/scoring against supplied derived fields, development only.
        if group == 'development':
            for c in CUES:
                for n in range(1,12):
                    raw, supplied = scr[f'GSR1{c}_{n}'], scr[f'{c}_{n}']
                    if raw is not None and supplied is not None:
                        expected = raw/1000 if raw/1000>.02 else 0.
                        assert abs(expected-supplied)<1e-12, (participant,c,n,expected,supplied)
    save(group.upper()+'_INCLUSION.json', checks)
    return units, checks

def scaled(units, sensitivity=False):
    out=[]
    for unit in units:
        u=dict(unit)
        u['y'] = unit['y'] / unit['scale'] if sensitivity else unit['y'].copy()
        u['us'] = unit['us'] / unit['scale'] if sensitivity and unit['us'] is not None else unit['us']
        out.append(u)
    return out

def prior_fit(units):
    prefix = np.array([u['y'][u['first']] for u in units])
    means = prefix.mean(axis=0)
    us = np.array([np.nan if u['us'] is None else u['us'] for u in units])
    if np.all(np.isnan(us)):
        return {'means':means.tolist(), 'us_mean':0., 'slope':0., 'uses_acquisition_US':False}
    center = float(np.nanmean(us))
    us = np.where(np.isfinite(us),us,center)
    x = us-center
    slope = float(np.sum(x*(prefix.mean(axis=1)-prefix.mean()))/(1.001*np.sum(x*x)+1e-12))
    return {'means':means.tolist(), 'us_mean':center, 'slope':slope, 'uses_acquisition_US':True}

def arrays(units, prior):
    initial, floorbase, delay, count, contrasts, observed, masks = [],[],[],[],[],[],[]
    source = []
    for u in units:
        prefix = u['y'][u['first']]
        us = prior['us_mean'] if u['us'] is None else u['us']
        pred = np.maximum(0.,np.array(prior['means']) + prior['slope']*(us-prior['us_mean']))
        if u['channel']=='expectancy':
            pred = np.minimum(pred,1.)
        initial.append(prefix)
        source.append(pred)
        delay.append(np.maximum(0., (np.arange(18)+1-u['prefix_end'])/3))
        count.append(u['ordinal'])
        observed.append(u['y'])
        masks.append(u['future'])
    return {'initial':np.array(initial), 'source':np.array(source), 'delay':np.array(delay),
            'count':np.array(count), 'y':np.array(observed), 'mask':np.array(masks),
            'cue':np.array([u['cue'] for u in units])}

def forecast(a, parameters, augmented):
    w,q,k,alpha = [parameters[key] for key in ['w','q','k','alpha']]
    levels = w*a['initial']+(1-w)*a['source']
    floor = q*levels.mean(axis=1,keepdims=True)
    ac = np.take_along_axis(levels,a['cue'],axis=1)
    if augmented:
        amin = levels[:,2:3]
        ac = amin+(ac-amin)*np.exp(-alpha*a['count'])
    pred = floor+(ac-floor)*np.exp(-k*a['delay'])
    return np.maximum(pred,0.) if parameters['allow_above1'] else np.clip(pred,0.,1.)

def unit_losses(a, pred):
    return np.sum(np.where(a['mask'],(a['y']-pred)**2,0.),axis=1)/a['mask'].sum(axis=1)

def fit(units, augmented=False, shrink=False, fixed_prior=None, fixed_w=None):
    prior = prior_fit(units) if fixed_prior is None else fixed_prior
    a = arrays(units,prior)
    best = None
    weights = [fixed_w] if fixed_w is not None else (GRID['w'] if shrink else [1.])
    for w in weights:
        for q in GRID['q']:
            for k in GRID['k']:
                for alpha in GRID['alpha'] if augmented else [0.]:
                    p = {'w':w,'q':q,'k':k,'alpha':alpha,'allow_above1':units[0]['channel']=='physiology'}
                    loss = float(unit_losses(a,forecast(a,p,augmented)).mean())
                    if best is None or loss<best['training_mse']-1e-15:
                        best = {'parameters':p,'training_mse':loss,'prior':prior,'augmented':augmented,'shrink_family':shrink}
    return best

def predict(units, model):
    a = arrays(units,model['prior'])
    return a,forecast(a,model['parameters'],model['augmented'])

def source_curve(train,test):
    curve=np.zeros((3,6))
    for c in range(3):
        for n in range(6):
            curve[c,n] = np.mean([u['y'][(u['cue']==c)&(u['ordinal']==n)][0] for u in train])
    return np.array([curve[u['cue'],u['ordinal']] for u in test])

def losses(train,test,common,update):
    a,pc=predict(test,common)
    _,pu=predict(test,update)
    pconstant=np.take_along_axis(a['initial'],a['cue'],axis=1)
    ps=source_curve(train,test)
    return a,{'common':pc,'update':pu,'constant':pconstant,'source_curve':ps}, {
        'common':unit_losses(a,pc),'update':unit_losses(a,pu),
        'constant':unit_losses(a,pconstant),'source_curve':unit_losses(a,ps)}

def boot_summary(loss, reps=10000, seed=20261031):
    rng=np.random.default_rng(seed)
    n=len(loss['common'])
    index=rng.integers(0,n,size=(reps,n))
    paired=loss['common']-loss['update']
    delta=paired[index].mean(axis=1)
    reductions=delta/np.maximum(loss['common'][index].mean(axis=1),1e-30)
    point=float(paired.mean())
    reduction=point/max(float(loss['common'].mean()),1e-30)
    interval=np.quantile(delta,[.025,.975]).tolist()
    beats_simple=all(float(loss['update'].mean())<float(loss[k].mean()) for k in ['constant','source_curve'])
    return {'n_participants':n, 'mse':{k:float(v.mean()) for k,v in loss.items()},
            'gain_mse':point,'gain_mse_bootstrap95':interval,'fractional_reduction':reduction,
            'fractional_reduction_bootstrap95':np.quantile(reductions,[.025,.975]).tolist(),
            'participants_improving':int(np.sum(paired>0)), 'beats_both_simple_baselines':beats_simple,
            'passes_five_percent_positive_lower_and_baselines':bool(reduction>=.05 and interval[0]>0 and beats_simple),
            'bootstrap_seed':seed, 'bootstrap_replicates':reps,
            'uncertainty_scope':'conditional participant bootstrap; no population coverage or exploration correction certified'}

def pilot():
    data,inclusion=source_data('development')
    out={'utc':dt.datetime.now(dt.timezone.utc).isoformat(),'grid':GRID,'channels':{},
         'read_charge_bytes':8000000,'peak_rss_bytes':0}
    recipes={}
    for channel,units in data.items():
        order=sorted(units,key=lambda u:hashlib.sha256(f'inner-ext2-{u["id"]}'.encode()).hexdigest())
        train,test=order[:len(order)//2],order[len(order)//2:]
        candidates={}
        for shrink in [False,True]:
            common=fit(train,False,shrink)
            update=fit(train,True,shrink)
            a,p,l=losses(train,test,common,update)
            candidates[str(shrink)]={'common':common,'update':update,'validation':boot_summary(l,reps=2000),
                                     'fit_ids':[u['id'] for u in train], 'development_validation_ids':[u['id'] for u in test]}
        original=candidates['False']['validation']['mse']['common']
        revised=candidates['True']['validation']['mse']['common']
        use_shrink=revised<.98*original
        recipes[channel]={'shrink_family':use_shrink,'revision_common_mse_reduction':1-revised/original}
        out['channels'][channel]={'n':len(units),'candidates':candidates,'decision':recipes[channel]}
        print(channel,json.dumps(out['channels'][channel],indent=2))
    out['peak_rss_bytes']=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    save('DEVELOPMENT.json',out)
    save('SELECTED_RECIPES.json',recipes)
    print('RESOURCE',out['read_charge_bytes'],out['peak_rss_bytes'])

def freeze():
    assert not (ROOT/'FREEZE.json').exists()
    data,_=source_data('development')
    recipes=json.loads((ROOT/'SELECTED_RECIPES.json').read_text())
    models={}
    for channel,units in data.items():
        modes=[('primary',False)]+([('past_acquisition_scale',True)] if channel=='physiology' else [])
        for mode,sensitivity in modes:
            train=scaled(units,sensitivity)
            common=fit(train,False,recipes[channel]['shrink_family'])
            update=fit(train,True,recipes[channel]['shrink_family'])
            models[channel+'/'+mode]={'common':common,'update':update}
            if channel=='physiology':
                models[channel+'/'+mode]['past_US_prior_common']=fit(train,False,False,fixed_w=0.)
    save('FROZEN_MODELS.json',models)
    names=['analysis.py','first_data_check.py','controls.py','audit.py','DEVELOPMENT_PLAN.md','PROTOCOL.md','SOURCE_CERTIFICATION.json',
           'SELECTED_RECIPES.json','FROZEN_MODELS.json']
    pins={name:hashlib.sha256((ROOT/name).read_bytes()).hexdigest() for name in names}
    out={'utc':dt.datetime.now(dt.timezone.utc).isoformat(),'pins':pins,
         'evaluation_payload_interpreted':False,'read_charge_bytes':5000000,
         'peak_rss_bytes':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss}
    save('FREEZE.json',out)
    print(json.dumps(out,indent=2))

def evaluate():
    frozen=json.loads((ROOT/'FREEZE.json').read_text())
    assert all(hashlib.sha256((ROOT/n).read_bytes()).hexdigest()==h for n,h in frozen['pins'].items())
    assert not (ROOT/'EVALUATION.json').exists()
    train,_=source_data('development')
    test,_=source_data('evaluation')
    models=json.loads((ROOT/'FROZEN_MODELS.json').read_text())
    results={}
    forecasts=[]
    for key,model in models.items():
        channel,mode=key.split('/')
        tr=scaled(train[channel],mode!='primary')
        te=scaled(test[channel],mode!='primary')
        a,p,l=losses(tr,te,model['common'],model['update'])
        if 'past_US_prior_common' in model:
            _,p_us=predict(te,model['past_US_prior_common'])
            p['past_US_prior_common']=p_us
            l['past_US_prior_common']=unit_losses(a,p_us)
        summary=boot_summary(l)
        summary['per_participant_losses']=[{'id':u['id'],**{k:float(v[i]) for k,v in l.items()}} for i,u in enumerate(te)]
        summary['cue_mse']={}
        for c in range(3):
            cmask=a['mask']&(a['cue']==c)
            summary['cue_mse'][CUES[c]]={k:float(np.sum(np.where(cmask,(a['y']-v)**2,0))/cmask.sum()) for k,v in p.items()}
        # Fixed past-US median split is descriptive, never a new gate.
        if channel=='physiology':
            threshold=float(np.median([u['us'] for u in tr if u['us'] is not None]))
            summary['past_US_strata']={}
            for label,mask in [('low',np.array([(u['us'] or 0)<=threshold for u in te])),('high',np.array([(u['us'] or 0)>threshold for u in te]))]:
                summary['past_US_strata'][label]={'n':int(mask.sum()),'gain_mse':float(np.mean(l['common'][mask]-l['update'][mask])) if mask.any() else None}
        for i,u in enumerate(te):
            for j in np.flatnonzero(u['future']):
                forecasts.append({'comparison':key,'id':u['id'],'position':int(j+1),'cue':CUES[int(u['cue'][j])],
                                  'cue_occurrence':int(u['ordinal'][j]+1),'observed':float(u['y'][j]),
                                  **{k:float(v[i,j]) for k,v in p.items()}})
        results[key]=summary
        print(key,json.dumps({k:v for k,v in summary.items() if k!='per_participant_losses'},indent=2))
    save('FORECASTS.json',forecasts)
    save('EVALUATION.json',{'utc':dt.datetime.now(dt.timezone.utc).isoformat(),'results':results,
                           'read_charge_bytes':10000000,'peak_rss_bytes':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss})

if __name__=='__main__':
    ap=argparse.ArgumentParser()
    ap.add_argument('stage',choices=['pilot','freeze','evaluate'])
    args=ap.parse_args()
    globals()[args.stage]()
