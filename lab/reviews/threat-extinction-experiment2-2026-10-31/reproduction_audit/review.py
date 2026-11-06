"""Independent reconstruction and one frozen matched-decay assay diagnostic.

No author Python module is imported and no author artifact is mutated.
"""
import os
for _v in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','VECLIB_MAXIMUM_THREADS','NUMEXPR_NUM_THREADS'):
    os.environ[_v] = '1'
import argparse
import collections
import copy
import datetime as dt
import hashlib
import io
import itertools
import json
import resource
import zipfile
import numpy as np
import independent_source as src

HERE, AUTHOR = src.HERE, src.AUTHOR
CUES = ['CSplus1','CSplus2','CSmin']
QS = [0.,.25,.5,1.]
KS = [0.,.05,.15,.4,1.,2.]
AS = [0.,.05,.15,.4,1.,2.]
WS = [1.,.75,.5,.25,0.]
SEED = 202611010244
REPS = 100

def load(name):
    return json.loads(src.read(AUTHOR/name))

def save(name,obj):
    src.write(name,obj)

def stamp():
    return dt.datetime.now(dt.timezone.utc).isoformat()

def stats(charge):
    return {'source_artifact_bytes_read':src.READ_BYTES,'conservative_stage_charge_bytes':charge,
            'peak_rss_bytes':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
            'public_operations':0,'ingress_bytes':0,'numerical_threads':1,'jobs_after_command':0}

def split(ids):
    forced={1,109,110}
    ranked=sorted(set(ids)-forced,key=lambda i:hashlib.sha256(('extinction2-20261031-'+str(i)).encode()).hexdigest())
    test=sorted(ranked[:20])
    return sorted(set(ids)-set(test)),test

def cue_value(code):
    return {'CS1':0,'CS2':1,'CSm':2}[code.split('_')[0]]

def transform(v):
    return 0. if v/1000<=.02 else np.sqrt(v/1000)

def data():
    s=src.source()
    log=collections.defaultdict(list)
    for row in s['log']:
        log[int(row['subject'])].append(row)
    ids=sorted(s['scr'])
    assert ids==sorted(s['expectancy'])==sorted(log)
    dev,test=split(ids)
    groups={'development':{},'evaluation':{}}
    rating_checks=scoring_checks=0
    max_score_error=0.
    zero_ids=[]
    phasecounts={}
    for pid in ids:
        sc,ex=s['scr'][pid],s['expectancy'][pid]
        assert sc['CS_counterbalancing']==ex['CS_counterbalancing']
        assert sc['Conditie']==ex['Conditie'] or pid==120 and sc['Conditie']==''
        phases={}
        for block,phase in [('3','Acq'),('4','Ext')]:
            rows=[r for r in log[pid] if r['blocknum']==block and r['trialcode'].startswith('CS')]
            assert len(rows)==(15 if block=='3' else 18)
            count=collections.Counter()
            cue,occ=[],[]
            for r in rows:
                c=cue_value(r['trialcode'])
                n=count[c]
                count[c]+=1
                cue.append(c)
                occ.append(n)
                assert float(r['response'])==ex[f'{phase}_{CUES[c]}_{n+1}']
                rating_checks+=1
            assert sorted(count.values())==([5]*3 if block=='3' else [6]*3)
            phases[phase]=(np.array(cue),np.array(occ))
        assert sum(r['trialcode']=='shock' for r in log[pid])==3
        assert not any(r['trialcode']=='shock' for r in log[pid] if r['blocknum']=='4')
        phasecounts[pid]={'acquisition_CS':15,'extinction_CS':18,'later_shock_rows':3}
        # Verify every finite supplied cue feature and its published range sqrt.
        for c in CUES:
            for n in range(1,14 if c=='CSplus1' else 15):
                key=c+'_'+str(n)
                raw,val,sqrtval=sc['GSR1'+key],sc[key],sc['SQRT_'+key]
                if raw is not None and val is not None:
                    err=abs(val-(raw/1000 if raw/1000>.02 else 0.))
                    assert err<1e-12
                    scoring_checks+=1
                    max_score_error=max(max_score_error,err)
                    if sqrtval is not None and sc['SCR_max'] is not None and sc['SCR_max']>0:
                        err=abs(np.sqrt(val/sc['SCR_max'])-sqrtval)
                        assert err<1e-12
                        scoring_checks+=1
                        max_score_error=max(max_score_error,err)
        cue,occ=phases['Ext']
        first=np.array([list(cue).index(c) for c in range(3)])
        end=int(first.max()+1)
        mask=np.arange(18)>=end
        scale=np.sqrt(max([.02]+[max(sc[f'GSR1{c}_{n}']/1000,0.) for c in CUES for n in range(1,6) if sc[f'GSR1{c}_{n}'] is not None]))
        us=[transform(sc['GSR1US_'+str(n)]) for n in range(1,11) if sc['GSR1US_'+str(n)] is not None]
        for channel in ['physiology','expectancy']:
            raw=[sc[f'GSR1{CUES[c]}_{6+n}'] if channel=='physiology' else ex[f'Ext_{CUES[c]}_{1+n}'] for c,n in zip(cue,occ)]
            if any(x is None or not np.isfinite(x) for x in raw):
                assert channel=='physiology' and pid==120
                continue
            y=np.array([transform(x) for x in raw]) if channel=='physiology' else (np.array(raw)-1)/8
            if channel=='expectancy':
                assert np.all((y>=0)&(y<=1))
            elif np.all(y==0):
                zero_ids.append(pid)
            u={'id':pid,'channel':channel,'y':y,'cue':cue,'occ':occ,'first':first,'end':end,
               'mask':mask,'delay':np.maximum((np.arange(18)+1-end)/3,0.),'scale':float(scale),
               'us':float(np.mean(us)) if channel=='physiology' and us else None}
            group='development' if pid in dev else 'evaluation'
            groups[group].setdefault(channel,[]).append(u)
    meta={'development_ids':dev,'evaluation_ids':test,'paired_ids':ids,'phasecounts':phasecounts,
          'raw_rating_checks':rating_checks,'supplied_scoring_checks':scoring_checks,
          'max_scoring_error':float(max_score_error),'all_zero_physiology_ids':zero_ids,
          'member_sha256':s['members'],'archive':s['archive'],
          'prefix_lengths':sorted({u['end'] for g in groups.values() for units in g.values() for u in units})}
    return groups,meta

def scaled(units):
    return [dict(u,y=u['y']/u['scale'],us=u['us']/u['scale'] if u['us'] is not None else None) for u in units]

def prior(units):
    initial=np.array([u['y'][u['first']] for u in units])
    means=initial.mean(0)
    us=np.array([np.nan if u['us'] is None else u['us'] for u in units])
    if np.all(np.isnan(us)):
        return {'means':means.tolist(),'us_mean':0.,'slope':0.,'uses_acquisition_US':False}
    center=float(np.nanmean(us))
    x=np.where(np.isfinite(us),us,center)-center
    slope=float(np.sum(x*(initial.mean(1)-initial.mean()))/(1.001*np.sum(x*x)+1e-12))
    return {'means':means.tolist(),'us_mean':center,'slope':slope,'uses_acquisition_US':True}

def forecast(units,p,pr=None,augment=True):
    initial=np.array([u['y'][u['first']] for u in units])
    if p['w']!=1:
        assert pr is not None
        us=np.array([pr['us_mean'] if u['us'] is None else u['us'] for u in units])
        base=np.maximum(0.,np.array(pr['means'])[None,:]+pr['slope']*(us-pr['us_mean'])[:,None])
        if units[0]['channel']=='expectancy':
            base=np.minimum(base,1.)
        initial=p['w']*initial+(1-p['w'])*base
    cue=np.array([u['cue'] for u in units])
    level=np.take_along_axis(initial,cue,1)
    if augment:
        minus=initial[:,2,None]
        level=minus+(level-minus)*np.exp(-p['alpha']*np.array([u['occ'] for u in units]))
    floor=p['q']*initial.mean(1)[:,None]
    pred=floor+(level-floor)*np.exp(-p['k']*np.array([u['delay'] for u in units]))
    return np.maximum(pred,0.) if units[0]['channel']=='physiology' else np.clip(pred,0.,1.)

def unitloss(units,pred):
    y=np.array([u['y'] for u in units])
    mask=np.array([u['mask'] for u in units])
    return np.sum(np.where(mask,(y-pred)**2,0.),1)/mask.sum(1)

def grid(units,augmented=False,weights=None):
    pr=prior(units)
    params=[dict(w=w,q=q,k=k,alpha=alpha,allow_above1=units[0]['channel']=='physiology')
            for w,q,k,alpha in itertools.product([1.] if weights is None else weights,QS,KS,AS if augmented else [0.])]
    predictions=np.array([forecast(units,p,pr,augmented) for p in params])
    return params,predictions,pr

def choose(units,g):
    params,predictions,pr=g
    y=np.array([u['y'] for u in units])
    mask=np.array([u['mask'] for u in units])
    losses=np.mean(np.sum(np.where(mask[None,:,:],(predictions-y[None,:,:])**2,0.),axis=2)/mask.sum(1)[None,:],axis=1)
    best=0
    for j in range(1,len(losses)):
        if losses[j]<losses[best]-1e-15:
            best=j
    return {'parameters':params[best],'prior':pr,'training_mse':float(losses[best])},predictions[best]

def fit(units,augmented=False,weights=None):
    return choose(units,grid(units,augmented,weights))[0]

def sourcecurve(train,test):
    curve=np.zeros((3,6))
    for c,n in itertools.product(range(3),range(6)):
        curve[c,n]=np.mean([u['y'][np.flatnonzero((u['cue']==c)&(u['occ']==n))[0]] for u in train])
    return np.array([curve[u['cue'],u['occ']] for u in test])

def compare(train,test,common,update):
    pc=forecast(test,common['parameters'],common['prior'],False)
    pu=forecast(test,update['parameters'],update['prior'],True)
    prefix=np.array([u['y'][u['first']] for u in test])
    pconst=np.take_along_axis(prefix,np.array([u['cue'] for u in test]),1)
    predictions={'common':pc,'update':pu,'constant':pconst,'source_curve':sourcecurve(train,test)}
    return predictions,{k:unitloss(test,p) for k,p in predictions.items()}

def bootstrap(losses,reps=10000,seed=20261031):
    lc,lu=losses['common'],losses['update']
    delta=lc-lu
    indexes=np.random.default_rng(seed).integers(0,len(delta),size=(reps,len(delta)))
    changes=delta[indexes].mean(1)
    ratio=changes/np.maximum(lc[indexes].mean(1),1e-30)
    interval=np.quantile(changes,[.025,.975])
    reduction=float(delta.mean()/max(float(lc.mean()),1e-30))
    baselines=all(lu.mean()<losses[k].mean() for k in ['constant','source_curve'])
    return {'mse':{k:float(v.mean()) for k,v in losses.items()},'gain_mse':float(delta.mean()),
            'gain_mse_bootstrap95':interval.tolist(),'fractional_reduction':reduction,
            'fractional_reduction_bootstrap95':np.quantile(ratio,[.025,.975]).tolist(),
            'participants_improving':int(np.sum(delta>0)),'beats_both_simple_baselines':bool(baselines),
            'passes_five_percent_positive_lower_and_baselines':bool(reduction>=.05 and interval[0]>0 and baselines)}

def static(units,parameters):
    initial=np.array([u['y'][u['first']] for u in units])
    means=initial.mean(1,keepdims=True)
    levels=parameters['s']*means+parameters['z']*(initial-means)
    p=np.take_along_axis(levels,np.array([u['cue'] for u in units]),1)
    return np.maximum(p,0.) if units[0]['channel']=='physiology' else np.clip(p,0.,1.)

def fitstatic(units):
    best=None
    for s,z in itertools.product([0.,.25,.5,.75,1.,1.25,1.5],[0.,.25,.5,.75,1.,1.5]):
        p={'s':s,'z':z}
        mse=float(unitloss(units,static(units,p)).mean())
        if best is None or mse<best['training_mse']-1e-15:
            best={'parameters':p,'training_mse':mse}
    return best

def check_pins(name):
    f=load(name)
    pins={n:hashlib.sha256(src.read(AUTHOR/n)).hexdigest()==h for n,h in f['pins'].items()}
    assert all(pins.values())
    return pins

def audit():
    groups,meta=data()
    cert=load('SOURCE_CERTIFICATION.json')
    for key in ['development_ids','evaluation_ids']:
        assert cert[key]==meta[key]
    frozen=load('FROZEN_MODELS.json')
    saved=load('EVALUATION.json')['results']
    forecasts=load('FORECASTS.json')
    sf=load('CONTRARY_FORECASTS.json')
    sm=load('CONTRARY_MODELS.json')
    savedstatic=load('CONTRARY.json')['results']
    out={'utc':stamp(),'source':meta,'main_pins':check_pins('FREEZE.json'),
         'contrary_pins':check_pins('CONTRARY_FREEZE.json'),'comparisons':{},'pilot':{},
         'author_helper_imports':False}
    all_forecast_errors=[]
    all_loss_errors=[]
    future_errors=[]
    nesting_errors=[]
    # Independent development inner split and rejected one-revision decision.
    for channel in ['physiology','expectancy']:
        units=groups['development'][channel]
        order=sorted(units,key=lambda u:hashlib.sha256(('inner-ext2-'+str(u['id'])).encode()).hexdigest())
        tr,te=order[:len(order)//2],order[len(order)//2:]
        candidates={}
        for pooling in [False,True]:
            cm=fit(tr,False,WS if pooling else [1.])
            um=fit(tr,True,WS if pooling else [1.])
            _,ls=compare(tr,te,cm,um)
            candidates[str(pooling)]={'common':cm,'update':um,'validation':bootstrap(ls,2000)}
        a=candidates['False']['validation']['mse']['common']
        b=candidates['True']['validation']['mse']['common']
        out['pilot'][channel]={'candidates':candidates,'pooling_reduction':float(1-b/a),'adopt':bool(b<.98*a)}
        assert not b<.98*a
    for key,models in frozen.items():
        channel,mode=key.split('/')
        tr=groups['development'][channel]
        te=groups['evaluation'][channel]
        if mode!='primary':
            tr,te=scaled(tr),scaled(te)
        cm,um=fit(tr),fit(tr,True)
        assert cm['parameters']==models['common']['parameters']
        assert um['parameters']==models['update']['parameters']
        for ours,theirs in [(cm,models['common']),(um,models['update'])]:
            assert abs(ours['training_mse']-theirs['training_mse'])<1e-13
            assert np.max(np.abs(np.array(ours['prior']['means'])-theirs['prior']['means']))<1e-13
        p,losses=compare(tr,te,cm,um)
        if 'past_US_prior_common' in models:
            pm=fit(tr,False,[0.])
            assert pm['parameters']==models['past_US_prior_common']['parameters']
            p['past_US_prior_common']=forecast(te,pm['parameters'],pm['prior'],False)
            losses['past_US_prior_common']=unitloss(te,p['past_US_prior_common'])
        result=bootstrap(losses)
        for field in ['gain_mse','gain_mse_bootstrap95','fractional_reduction','fractional_reduction_bootstrap95']:
            err=float(np.max(np.abs(np.array(result[field])-saved[key][field])))
            assert err<1e-13
        assert result['participants_improving']==saved[key]['participants_improving']
        assert result['passes_five_percent_positive_lower_and_baselines']==saved[key]['passes_five_percent_positive_lower_and_baselines']
        positions={u['id']:i for i,u in enumerate(te)}
        for row in forecasts:
            if row['comparison']!=key:
                continue
            i,j=positions[row['id']],row['position']-1
            assert row['cue']==CUES[int(te[i]['cue'][j])]
            assert row['cue_occurrence']==te[i]['occ'][j]+1
            all_forecast_errors.append(abs(row['observed']-te[i]['y'][j]))
            for name,pred in p.items():
                all_forecast_errors.append(abs(row[name]-pred[i,j]))
        for i,row in enumerate(saved[key]['per_participant_losses']):
            assert row['id']==te[i]['id']
            for name,values in losses.items():
                all_loss_errors.append(abs(row[name]-values[i]))
        altered=[dict(u,y=np.where(u['mask'],99.25,u['y'])) for u in te]
        for model,aug in [(cm,False),(um,True)]:
            old=forecast(te,model['parameters'],model['prior'],aug)
            changed=forecast(altered,model['parameters'],model['prior'],aug)
            future_errors.append(float(np.max(np.abs(old-changed))))
        alpha0=dict(cm['parameters'],alpha=0.)
        nesting_errors.append(float(np.max(np.abs(forecast(te,alpha0,cm['prior'],True)-forecast(te,alpha0,cm['prior'],False)))))
        initial=forecast(te,dict(alpha0,q=0.,k=0.),cm['prior'],False)
        assert np.array_equal(initial,np.array([u['y'][u['first']][u['cue']] for u in te]))
        st=fitstatic(tr)
        assert st['parameters']==sm[key]['parameters']
        ps=static(te,st['parameters'])
        for row in sf:
            if row['comparison']==key:
                i,j=positions[row['id']],row['position']-1
                all_forecast_errors.extend([abs(row['static']-ps[i,j]),abs(row['common']-p['common'][i,j]),abs(row['observed']-te[i]['y'][j])])
        sl=unitloss(te,ps)
        delta=losses['common']-sl
        assert abs(sl.mean()-savedstatic[key]['static_mse'])<1e-13
        result.update({'common_fit':cm,'update_fit':um,'static_fit':st,'static_mse':float(sl.mean()),
                       'static_gain_mse':float(delta.mean()),'n':len(te),
                       'per_participant':[{'id':u['id'],**{k:float(v[i]) for k,v in losses.items()},'static':float(sl[i])} for i,u in enumerate(te)]})
        out['comparisons'][key]=result
    assert max(all_forecast_errors)<1e-13 and max(all_loss_errors)<1e-13
    assert max(future_errors)==0 and max(nesting_errors)<1e-14
    out['verification']={'main_forecast_rows':len(forecasts),'contrary_forecast_rows':len(sf),
                         'forecast_observation_scalar_checks':len(all_forecast_errors),'maximum_forecast_error':float(max(all_forecast_errors)),
                         'main_individual_loss_checks':len(all_loss_errors),'maximum_loss_error':float(max(all_loss_errors)),
                         'future_suffix_max_error':max(future_errors),'alpha0_max_nesting_error':max(nesting_errors)}
    # Inspect the actual source syntax/README within the permitted cached archive.
    z=zipfile.ZipFile(io.BytesIO(src.read(AUTHOR/'sources/experiment2.zip')))
    syntax={}
    for entry in z.infolist():
        if entry.filename.endswith('.sps') or entry.filename.endswith('READ_ME.txt'):
            b=z.read(entry.filename)
            src.READ_BYTES+=len(b)
            syntax[entry.filename]=b.decode('utf8','replace')
    save('SOURCE_SYNTAX.json',syntax)
    out['resources']=stats(20000000)
    save('RECONSTRUCTION.json',out)
    print(json.dumps({'verification':out['verification'],'ratings':meta['raw_rating_checks'],'scoring':meta['supplied_scoring_checks'],
                      'comparisons':{k:{a:v[a] for a in ['n','mse','gain_mse_bootstrap95','fractional_reduction','static_mse']} for k,v in out['comparisons'].items()},
                      'resources':out['resources']},indent=2))

def cube(units,values):
    out=np.zeros((len(units),3,6))
    for i,u in enumerate(units):
        out[i,u['cue'],u['occ']]=values[i]
    return out

def noise(units,model):
    prediction=forecast(units,model['parameters'],model['prior'],False)
    residual=cube(units,np.array([u['y'] for u in units])-prediction)
    order=np.argsort(residual,axis=0,kind='stable')
    ranks=np.empty_like(order)
    for c,n in itertools.product(range(3),range(6)):
        ranks[order[:,c,n],c,n]=np.arange(len(units))
    return ranks,np.mean(cube(units,np.array([u['y'] for u in units]))>0,axis=0)

def testdesign(train,templates,rng):
    out=[]
    for template in templates:
        donor=train[int(rng.integers(len(train)))]
        values=np.zeros((3,6))
        values[donor['cue'],donor['occ']]=donor['y']
        u=dict(donor,id=template['id'],cue=template['cue'],occ=template['occ'],first=template['first'],end=template['end'],mask=template['mask'],delay=template['delay'])
        u['y']=values[u['cue'],u['occ']].copy()
        out.append(u)
    return out

def uniforms(rng,ranks,n):
    donor=rng.integers(0,len(ranks),size=n)
    return (ranks[donor]+rng.random((n,3,6)))/len(ranks)

def generate(units,parameters,ranks,positive,rng):
    mean=forecast(units,parameters,None,parameters['alpha']>0)
    n=len(units)
    def draw():
        un=uniforms(rng,ranks,n)
        return np.array([un[i,u['cue'],u['occ']] for i,u in enumerate(units)])
    if units[0]['channel']=='expectancy':
        values=np.zeros_like(mean)
        for _ in range(8):
            values+=(draw()<mean)/8
    else:
        a,b=draw(),draw()
        fraction=np.array([positive[u['cue'],u['occ']] for u in units])
        threshold=np.sqrt(.02)
        probability=np.minimum(np.clip(fraction,.05,.95),.99*mean/threshold)
        active=np.divide(mean,probability,out=np.full_like(mean,threshold),where=probability>0)
        amplitude=threshold+(active-threshold)*(-np.log1p(-b))
        values=np.where(a<probability,amplitude,0.)
    return [dict(u,y=np.where(u['mask'],values[i],u['y'])) for i,u in enumerate(units)],mean

def oracle(units,p,positive):
    mean=forecast(units,p,None,p['alpha']>0)
    target=[dict(u,y=np.where(u['mask'],mean[i],u['y'])) for i,u in enumerate(units)]
    best=fit(target,False)
    separation=best['training_mse']
    template=unitloss(target,forecast(units,dict(p,alpha=0.),None,False)).mean()
    if units[0]['channel']=='expectancy':
        var=mean*(1-mean)/8
    else:
        t=np.sqrt(.02)
        fraction=np.array([positive[u['cue'],u['occ']] for u in units])
        prob=np.minimum(np.clip(fraction,.05,.95),.99*mean/t)
        active=np.divide(mean,prob,out=np.full_like(mean,t),where=prob>0)
        var=np.maximum(prob*(active**2+(active-t)**2)-mean**2,0.)
    mask=np.array([u['mask'] for u in units])
    noise_mse=float(np.mean(np.sum(np.where(mask,var,0.),1)/mask.sum(1)))
    # Exact expected risk relative to closest common conditional-mean grid.
    relative=separation/(noise_mse+separation) if noise_mse+separation>0 else 0.
    return {'best_common_separation_mse':float(separation),'same_qk_alpha0_separation_mse':float(template),
            'conditional_marginal_noise_mse':noise_mse,'ideal_expected_fractional_gain':float(relative),
            'oracle_common_parameters':best['parameters']}

def wilson(k,n):
    z=1.959963984540054
    p=k/n
    center=(p+z*z/(2*n))/(1+z*z/n)
    width=z*np.sqrt(p*(1-p)/n+z*z/(4*n*n))/(1+z*z/n)
    return [float(center-width),float(center+width)]

def fit_control(st,se,train_grid,rep,seed):
    cm,_=choose(st,train_grid[0])
    um,_=choose(st,train_grid[1])
    _,ls=compare(st,se,cm,um)
    result=bootstrap(ls,500,seed+rep)
    return {'replicate':rep,'gain_mse':result['gain_mse'],'fractional_reduction':result['fractional_reduction'],
            'positive_bootstrap_lower':result['gain_mse_bootstrap95'][0]>0,
            'passes_full_rule':result['passes_five_percent_positive_lower_and_baselines'],
            'selected_alpha':um['parameters']['alpha']}

def reconstruct_controls():
    groups,meta=data()
    saved=load('CONTROLS.json')
    models=load('FROZEN_MODELS.json')
    rng=np.random.default_rng(202611010231)
    out={'utc':stamp(),'seed':202611010231,'channels':{},'replicates':100}
    maxerr=0.
    checked=0
    for channel in ['physiology','expectancy']:
        train=groups['development'][channel]
        templates=groups['evaluation'][channel]
        cm=models[channel+'/primary']['common']
        ranks,positive=noise(train,cm)
        tg=(grid(train),grid(train,True))
        out['channels'][channel]={}
        for effect,alpha in [('null',0.),('known_alpha1',1.)]:
            p=dict(cm['parameters'],alpha=alpha)
            records=[]
            for rep in range(100):
                te=testdesign(train,templates,rng)
                st,_=generate(train,p,ranks,positive,rng)
                se,mean=generate(te,p,ranks,positive,rng)
                row=fit_control(st,se,tg,rep,202611010231)
                oo=oracle(te,p,positive)
                row['oracle_best_common_mean_separation_mse']=oo['best_common_separation_mse']
                target=saved['channels'][channel][effect]['records'][rep]
                for key in ['gain_mse','fractional_reduction','oracle_best_common_mean_separation_mse']:
                    err=abs(row[key]-target[key])
                    maxerr=max(maxerr,err)
                    assert err<1e-12,(channel,effect,rep,key,row[key],target[key])
                for key in ['positive_bootstrap_lower','passes_full_rule','selected_alpha']:
                    assert row[key]==target[key],(channel,effect,rep,key)
                records.append(row)
                checked+=1
            count=sum(x['passes_full_rule'] for x in records)
            assert count==saved['channels'][channel][effect]['full_rule_count']
            out['channels'][channel][effect]={'full_rule_count':count,'wilson95':wilson(count,100),'records':records,
                'mean_oracle_separation':float(np.mean([x['oracle_best_common_mean_separation_mse'] for x in records]))}
            print('RECONSTRUCTED',channel,effect,count,'/100',flush=True)
    out.update({'checked_replicates':checked,'maximum_scalar_difference':maxerr,'resources':stats(15000000)})
    save('CONTROL_RECONSTRUCTION.json',out)
    print('CONTROL_RESOURCE',json.dumps(out['resources']))

def freeze():
    assert not (HERE/'CONTRARY_FREEZE.json').exists()
    names=['CONTRARY_PLAN.md','review.py','independent_source.py']
    save('CONTRARY_FREEZE.json',{'utc':stamp(),'postvalidation':True,'seed':SEED,'replicates':REPS,
         'pins':{n:hashlib.sha256(src.read(HERE/n)).hexdigest() for n in names},'resources':stats(1000000)})
    print((HERE/'CONTRARY_FREEZE.json').read_text())

def diagnostic():
    freeze=json.loads(src.read(HERE/'CONTRARY_FREEZE.json'))
    assert all(hashlib.sha256(src.read(HERE/n)).hexdigest()==h for n,h in freeze['pins'].items())
    assert not (HERE/'CONTRARY.json').exists()
    groups,meta=data()
    models=load('FROZEN_MODELS.json')
    out={'utc':stamp(),'seed':SEED,'replicates':REPS,'postvalidation':True,'channels':{},'real_evaluation_outcomes_used_to_fit_generator':False}
    for ci,channel in enumerate(['physiology','expectancy']):
        train=groups['development'][channel]
        templates=groups['evaluation'][channel]
        base=models[channel+'/primary']['common']
        ranks,positive=noise(train,base)
        tg=(grid(train),grid(train,True))
        cells={}
        for label,k,alpha in [('source_k_null',base['parameters']['k'],0.),('source_k_alpha1',base['parameters']['k'],1.),
                              ('k0_null',0.,0.),('k0_alpha1',0.,1.)]:
            p=dict(base['parameters'],k=k,alpha=alpha)
            records=[]
            exact={'development':oracle(train,p,positive),'actual_evaluation_prefix_design':oracle(templates,p,positive)}
            for rep in range(REPS):
                rng=np.random.default_rng(SEED+ci*10000+rep+1)
                te=testdesign(train,templates,rng)
                st,_=generate(train,p,ranks,positive,rng)
                se,_=generate(te,p,ranks,positive,rng)
                row=fit_control(st,se,tg,rep,SEED)
                row['oracle']=oracle(te,p,positive)
                records.append(row)
            count=sum(x['passes_full_rule'] for x in records)
            cells[label]={'generator':p,'full_rule_count':count,'wilson95':wilson(count,REPS),'exact_source_design_oracles':exact,
                          'mean_oracle_best_common_separation_mse':float(np.mean([x['oracle']['best_common_separation_mse'] for x in records])),
                          'mean_conditional_noise_mse':float(np.mean([x['oracle']['conditional_marginal_noise_mse'] for x in records])),
                          'mean_ideal_expected_fractional_gain':float(np.mean([x['oracle']['ideal_expected_fractional_gain'] for x in records])),
                          'records':records}
            print('DIAGNOSTIC',channel,label,count,'/100','oracle_fraction',cells[label]['mean_ideal_expected_fractional_gain'],flush=True)
        a=np.array([x['passes_full_rule'] for x in cells['source_k_alpha1']['records']])
        b=np.array([x['passes_full_rule'] for x in cells['k0_alpha1']['records']])
        out['channels'][channel]={'cells':cells,'paired_known_effect_detection':{'source_only':int(np.sum(a&~b)),
                 'k0_only':int(np.sum(b&~a)),'both':int(np.sum(a&b)),'neither':int(np.sum(~a&~b))}}
    out['resources']=stats(30000000)
    save('CONTRARY.json',out)
    print('DIAGNOSTIC_RESOURCE',json.dumps(out['resources']))

if __name__=='__main__':
    ap=argparse.ArgumentParser()
    ap.add_argument('stage',choices=['audit','controls','freeze','diagnostic'])
    {'audit':audit,'controls':reconstruct_controls,'freeze':freeze,'diagnostic':diagnostic}[ap.parse_args().stage]()
