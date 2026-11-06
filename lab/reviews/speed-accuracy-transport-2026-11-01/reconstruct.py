"""Independent original-release, Wiener, ridge, score and conditional-control audit.

Only generic cached rdata/scipy/numpy are imported. Author files are data/read-only
audit targets. This is not an independent full optimization of the original model.
"""
from pathlib import Path
import sys, json, hashlib, base64, datetime, resource
import numpy as np
from scipy.special import expit
from scipy.integrate import quad
from numpy.polynomial.legendre import leggauss

HERE = Path(__file__).resolve().parent
AUTHOR = HERE.parents[1] / 'tasks' / HERE.name
sys.path.insert(0,str(AUTHOR/'deps'))
import rdata

WEIGHTS = np.array([1.,1.,1.,3.])/6
PRIOR_SD = np.array([.6,.8,.10,.9,.9,.9,.9])
NODES = {}

def stamp(): return datetime.datetime.now(datetime.timezone.utc).isoformat()
def read(name): return json.loads((AUTHOR/name).read_text())
def save(name,value):
    def enc(v):
        if isinstance(v,np.ndarray): return v.tolist()
        if isinstance(v,np.generic): return v.item()
        raise TypeError(type(v))
    (HERE/name).write_text(json.dumps(value,indent=2,default=enc)+'\n')

def original():
    d = rdata.read_rda(AUTHOR/'speed_acc.RData')['speed_acc']
    return {'id':d.id.astype(str).astype(int).to_numpy(),
            'block':d.block.astype(str).astype(int).to_numpy(),
            'condition':d.condition.astype(str).to_numpy(),
            'rt':d.rt.to_numpy(float), 'response':d.response.astype(str).to_numpy(),
            'stimulus':d.stim_cat.astype(str).to_numpy(),
            'frequency':d.frequency.astype(str).to_numpy(),
            'censor':d.censor.to_numpy(bool)}

def selected(d,person,block,limits=(.18,3.)):
    nominal = (d['id']==person)&(d['block']==block)
    assert nominal.sum()==96
    assert set(d['condition'][nominal])==({'speed'} if block==1 else {'accuracy'})
    valid = np.isin(d['response'],['word','nonword']) & np.isfinite(d['rt'])
    released = valid & (d['rt']>=.18) & (d['rt']<=3.)
    assert np.array_equal(~released[nominal],d['censor'][nominal])
    take = nominal & valid & (d['rt']>=limits[0]) & (d['rt']<=limits[1])
    freq = d['frequency'][take]
    cat = np.full(take.sum(),3,int)
    for c,label in enumerate(['high','low','very_low']): cat[freq==label]=c
    assert np.array_equal(cat==3,d['stimulus'][take]=='nonword')
    return {'rt':d['rt'][take], 'category':cat,
            'upper':d['response'][take]=='word',
            'correct':d['response'][take]==d['stimulus'][take]}

def summarize(rows):
    outcome,features,counts = [],[],[]
    for c in range(4):
        take=rows['category']==c
        t=rows['rt'][take]; y=rows['correct'][take]; n=len(t)
        counts.append(n); outcome.append([y.mean(),t.mean()])
        features.append([(y.sum()+.5)/(n+1),t.mean(),t.std(ddof=1),
                         rows['correct'].mean(),rows['rt'].mean(),rows['rt'].std(ddof=1)])
    return np.array(outcome),np.array(features),np.array(counts)

def zero_drift_hit(t,a,d,force=None):
    """Flux to a boundary distance d away; two independent series regimes."""
    t=np.asarray(t,float)
    ans=np.zeros_like(t)
    short=(t>0)&(t<.18*a*a) if force is None else ((t>0) if force=='image' else np.zeros_like(t,dtype=bool))
    if short.any():
        u=t[short,None]
        distances=d+2*a*np.arange(-8,9)[None,:]
        ans[short]=(distances*np.exp(-distances**2/(2*u))).sum(axis=1)/np.sqrt(2*np.pi*t[short]**3)
    long=(t>0)&~short
    if long.any():
        k=np.arange(1,81)[None,:]
        u=t[long,None]
        ans[long]=(np.pi/a**2)*(k*np.sin(np.pi*k*d/a)*np.exp(-.5*(np.pi*k/a)**2*u)).sum(axis=1)
    return np.maximum(ans,0.)

def physical(p):
    p=np.asarray(p)
    return np.exp(p[0]),expit(p[1]),p[2],np.exp(p[3:])*[1,1,1,-1]

def hit_densities(times,category,p,force=None):
    a,z,t0,drifts=physical(p)
    t=np.asarray(times)-t0; v=drifts[np.asarray(category)]
    lower=zero_drift_hit(t,a,a*z,force)*np.exp(np.clip(-v*a*z-.5*v*v*t,-700,700))
    upper=zero_drift_hit(t,a,a*(1-z),force)*np.exp(np.clip(v*a*(1-z)-.5*v*v*t,-700,700))
    return lower,upper

def moments(p,n=256):
    if n not in NODES: NODES[n]=leggauss(n)
    low=max(.18,float(p[2])); width=3.-low
    assert width>0
    x,w=NODES[n]; t=low+width*(x+1)/2; w=w*width/2
    lower,upper=hit_densities(np.tile(t,4),np.repeat(np.arange(4),n),p)
    lower=lower.reshape(4,n);upper=upper.reshape(4,n)
    total=lower+upper
    mass=(total*w).sum(axis=1)
    accuracy=(np.r_[upper[:3],lower[3:]]*w).sum(axis=1)/mass
    mean=(total*w*t).sum(axis=1)/mass
    return mass,np.stack([accuracy,mean],axis=-1)

def likelihood(p,rows,n=256):
    mass,_=moments(p,n)
    lower,upper=hit_densities(rows['rt'],rows['category'],p)
    observed=np.where(rows['upper'],upper,lower)
    return float((-np.log(np.maximum(observed,1e-250))+np.log(np.maximum(mass[rows['category']],1e-250))).sum())

def original_map(p,m,quality=False):
    p=np.array(p,float)
    a,z,t0,_=physical(p)
    below=a*z*np.exp(m[0]);above=a*(1-z)*np.exp(m[1])
    znew=below/(above+below)
    p[0]=np.log(above+below);p[1]=np.log(znew)-np.log1p(-znew)
    p[2]=.03+np.exp(m[2])*(t0-.03)
    if quality: p[3:]+=m[3]
    return p

def clamp(p):
    p=np.array(p,float,copy=True)
    p[...,0]=np.clip(p[...,0],.005,.995)
    p[...,1]=np.clip(p[...,1],.18,3.)
    return p

def fit_ridge(features,targets,penalty):
    f=features.reshape(-1,6);y=targets.reshape(-1,2)
    mean=f.mean(axis=0);sd=f.std(axis=0);sd[sd<1e-8]=1
    design=np.c_[np.tile(np.eye(4),(len(features),1)),(f-mean)/sd]
    scale=np.sqrt(np.tile(WEIGHTS,len(features)))
    regularizer=np.diag(np.sqrt([1e-8]*4+[penalty]*6))
    design=np.r_[design*scale[:,None],regularizer]
    y=np.r_[y*scale[:,None],np.zeros((10,2))]
    coef=np.linalg.lstsq(design,y,rcond=None)[0]
    return {'mean':mean,'sd':sd,'coef':coef,'penalty':penalty}

def ridge_predict(f,fit):
    flat=f.reshape(-1,6)
    design=np.c_[np.tile(np.eye(4),(len(f),1)),(flat-fit['mean'])/fit['sd']]
    return clamp(np.einsum('ij,jk->ik',design,fit['coef']).reshape(len(f),4,2))

def per_person_loss(pred,obs):
    endpoints=np.einsum('nce,c->ne',(pred-obs)**2,WEIGHTS)
    return np.c_[endpoints,200.*endpoints.sum(axis=1)]

def empirical_fit(baseline,features,target):
    cv={}
    for name in ['POP','DELTA']+['RIDGE_'+str(x) for x in [.01,.1,1,10,100]]:
        guesses=[]
        for omitted in range(len(target)):
            keep=np.arange(len(target))!=omitted
            if name=='POP': guess=target[keep].mean(axis=0)
            elif name=='DELTA': guess=baseline[omitted]+(target[keep]-baseline[keep]).mean(axis=0)
            else:
                fit=fit_ridge(features[keep],target[keep],float(name.split('_')[1]))
                guess=ridge_predict(features[omitted:omitted+1],fit)[0]
            guesses.append(clamp(guess))
        cv[name]=float(per_person_loss(np.array(guesses),target)[:,2].mean())
    bestpen=min([.01,.1,1,10,100],key=lambda x:cv['RIDGE_'+str(x)])
    best=min(['POP','DELTA','RIDGE_'+str(bestpen)],key=cv.get)
    return {'POP':target.mean(axis=0),'DELTA':(target-baseline).mean(axis=0),
            'RIDGE':fit_ridge(features,target,bestpen),'source_CV_joint_loss':cv,
            'reference':'RIDGE' if best.startswith('RIDGE') else best}

def empirical_predictions(b,f,e):
    return {'IDENTITY':clamp(b), 'POP':clamp(np.broadcast_to(e['POP'],b.shape)),
            'DELTA':clamp(b+e['DELTA']), 'RIDGE':ridge_predict(f,e['RIDGE'])}

def scores(pred,obs,ref,seed=20261101):
    losses={name:per_person_loss(p,obs) for name,p in pred.items()}
    ix=np.random.default_rng(seed).integers(0,len(obs),(10000,len(obs)))
    out={}
    base=losses[ref]
    for name,p in pred.items():
        loss=losses[name];mean=loss.mean(axis=0)
        gains=1.-loss[ix,2].mean(axis=1)/base[ix,2].mean(axis=1)
        absolute=np.einsum('nce,c->ne',np.abs(p-obs),WEIGHTS).mean(axis=0)
        out[name]={'accuracy_mse':mean[0], 'rt_mean_mse_s2':mean[1], 'joint_loss':mean[2],
                   'joint_fractional_gain_over_reference':1.-mean[2]/base[:,2].mean(),
                   'conditional_bootstrap_gain_percentiles':np.percentile(gains,[2.5,97.5]),
                   'accuracy_MAE':absolute[0], 'rt_mean_MAE_s':absolute[1],
                   'people_joint_better':int((loss[:,2]<base[:,2]).sum()),
                   'per_person_losses':loss}
    p=out['P'];r=out[ref]
    gates={'joint_gain_ge10percent':p['joint_fractional_gain_over_reference']>=.10,
           'paired_interval_lower_positive':p['conditional_bootstrap_gain_percentiles'][0]>0,
           'accuracy_mse_better':p['accuracy_mse']<r['accuracy_mse'],
           'rt_mse_better':p['rt_mean_mse_s2']<r['rt_mean_mse_s2'],
           'accuracy_MAE_le5pp':p['accuracy_MAE']<=.05,
           'rt_MAE_le50ms':p['rt_mean_MAE_s']<=.05}
    return {'reference':ref,'models':out,'primary_P_rule_passes':bool(all(gates.values())), 'gates':gates}

def error(a,b): return float(np.max(np.abs(np.asarray(a,float)-np.asarray(b,float))))

def audit():
    d=original();source=read('SOURCE_FIT.json');saved=read('PREDICTIONS.json');author_scores=read('SCORES.json')
    first={(p,b):selected(d,p,b) for p in range(1,18) for b in [1,2]}
    summaries={key:summarize(rows) for key,rows in first.items()}
    b=np.array([summaries[p,1][0] for p in range(1,10)])
    f=np.array([summaries[p,1][1] for p in range(1,10)])
    y=np.array([summaries[p,2][0] for p in range(1,10)])
    held_b=np.array([summaries[p,1][0] for p in range(10,18)])
    held_f=np.array([summaries[p,1][1] for p in range(10,18)])
    held_y=np.array([summaries[p,2][0] for p in range(10,18)])
    held_n=np.array([summaries[p,2][2] for p in range(10,18)])
    e=empirical_fit(b,f,y);pred=empirical_predictions(held_b,held_f,e)
    ps=np.array(saved['baseline_parameters'])
    pred['P']=np.array([moments(original_map(p,source['P_mapping']))[1] for p in ps])
    pred['Q']=np.array([moments(original_map(p,source['Q_mapping'],True))[1] for p in ps])
    evaluated=scores(pred,held_y,e['reference'])
    discrepancies={}
    for name,model in evaluated['models'].items():
        discrepancies[name]={key:error(value,author_scores['models'][name][key]) for key,value in model.items()}
    pooled={key:np.concatenate([first[p,1][key] for p in range(1,10)]) for key in first[1,1]}
    center=np.array(source['center']);p_source=np.array(source['source_baseline_parameters'])
    objectives=[]
    for label,p,rows,claimed,prior in [('pooled',center,pooled,source['pooled_fit']['objective'],None)]+[
            ('source_'+str(i+1),p,first[i+1,1],source['source_baseline_fit_status'][i]['objective'],center) for i,p in enumerate(p_source)]+[
            ('held_'+str(i+10),p,first[i+10,1],saved['baseline_status'][i]['objective'],center) for i,p in enumerate(ps)]:
        penalty=0. if prior is None else .5*np.sum(((p-prior)/PRIOR_SD)**2)
        v96=likelihood(p,rows,96)+penalty;v256=likelihood(p,rows,256)+penalty
        objectives.append({'fit':label,'saved':claimed,'independent96':v96,'independent256':v256,
                           'saved_abs_difference':abs(v96-claimed),'refinement_difference':abs(v256-v96)})
    mapping=[]
    for name,q in [('P',False),('Q',True)]:
        m=source[name+'_mapping'];claimed=source[name+'_status']['objective']
        val96=sum(likelihood(original_map(p,m,q),first[i+1,2],96) for i,p in enumerate(p_source))
        val256=sum(likelihood(original_map(p,m,q),first[i+1,2],256) for i,p in enumerate(p_source))
        mapping.append({'fit':name,'saved':claimed,'independent96':val96,'independent256':val256,
                        'saved_abs_difference':abs(val96-claimed),'refinement_difference':abs(val256-val96)})
    pins=read('FREEZE.json')
    pin_status={name:hashlib.sha256((AUTHOR/name).read_bytes()).hexdigest()==pin for name,pin in pins['files'].items()}
    pred_pin=read('PREDICTION_PIN.json')['sha256']['PREDICTIONS.json']
    pin_status['PREDICTIONS.json']=hashlib.sha256((AUTHOR/'PREDICTIONS.json').read_bytes()).hexdigest()==pred_pin
    transport=base64.b64decode((AUTHOR/'speed_acc.RData.base64').read_bytes())
    pin_status['base64_vs_original']=transport==(AUTHOR/'speed_acc.RData').read_bytes()
    changed={key:np.array(value,copy=True) for key,value in d.items()}
    suffix=(changed['id']>=10)&(changed['block']>=2)
    changed['rt'][suffix]=2.99;changed['response'][suffix]='word'
    # Censor is a derived check; update consistently for the deliberately changed suffix.
    changed['censor'][suffix]=False
    invariant=all(error(summarize(selected(changed,p,1))[1],summaries[p,1][1])==0 for p in range(10,18))
    influence=[]
    for i in range(8):
        keep=np.arange(8)!=i
        pp=per_person_loss(pred['P'],held_y)[keep].mean(axis=0)
        rr=per_person_loss(pred[e['reference']],held_y)[keep].mean(axis=0)
        influence.append({'omitted_id':i+10,'joint_P_fractional_gain':1.-pp[2]/rr[2],
                          'accuracy_MSE_gain':1.-pp[0]/rr[0], 'RT_MSE_gain':1.-pp[1]/rr[1]})
    paper_y=np.array([summarize(selected(d,p,2,(.3,2.5)))[0] for p in range(10,18)])
    paper_result=scores(pred,paper_y,e['reference'])
    counts_all={str(p):{'first_block':summaries[p,1][2], 'second_block':summaries[p,2][2]} for p in range(1,18)}
    out={'at_utc':stamp(),'independence':'Own raw parsing, image/eigenfunction density, augmented least-squares ridge/CV and scoring code; no author scientific imports/runs. Original full optimizer/source refits UNRUN.',
         'raw_summary_discrepancies':{'source_baseline':error(b,source['source_baseline_observed']),
             'source_target':error(y,source['source_target_observed']), 'held_baseline':error(held_b,saved['baseline_observed']),
             'held_features':error(held_f,saved['baseline_features']), 'held_target_64_scalars':error(held_y,author_scores['target_values']),
             'held_counts':error(held_n,author_scores['target_counts'])},
         'forecast_discrepancies_384_scalars':{name:error(p,saved['predictions'][name]) for name,p in pred.items()},
         'CV_joint_loss':e['source_CV_joint_loss'],'CV_discrepancies':{name:abs(v-source['empirical']['source_CV_joint_loss'][name]) for name,v in e['source_CV_joint_loss'].items()},
         'selected_reference':e['reference'],'selected_penalty':e['RIDGE']['penalty'],
         'score_discrepancies':discrepancies,'baseline_objectives':objectives,'mapping_objectives':mapping,
         'freeze_and_prediction_pins':pin_status,'ordering':{'freeze':pins['at'],'predictions':saved['at'],'scores':author_scores['at'],
             'ordered':pins['at']<saved['at']<author_scores['at'],'limitation':'Saved ordering, code filters and pins do not prove historical non-access; full release derived in author RAM prefreeze.'},
         'nominal_firstpair_counts_per_category':[16,16,16,48],'valid_counts':counts_all,
         'target_valid_responses':int(held_n.sum()),'future_suffix_baseline_feature_invariance':invariant,
         'leave_one_person':influence,'original_joint_rule_passes':evaluated['primary_P_rule_passes'],
         'largest_measured_process_rss_bytes_macos':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
         'read_decode_hash_charge_bytes':100000000}
    assert all(pin_status.values())
    assert max(out['raw_summary_discrepancies'].values())<1e-12
    assert max(out['forecast_discrepancies_384_scalars'].values())<1e-7
    assert max(out['CV_discrepancies'].values())<1e-8
    assert max(x['saved_abs_difference'] for x in objectives+mapping)<1e-5
    assert out['largest_measured_process_rss_bytes_macos']<800000000
    save('RECONSTRUCTION.json',out)
    save('RECONSTRUCTED_FORECASTS.json',{'at_utc':stamp(),'ids':list(range(10,18)),'predictions':pred,'target':held_y,'counts':held_n})
    save('RECONSTRUCTED_SCORES.json',evaluated)
    save('PAPER_CUTOFF_AUDIT.json',paper_result)
    print(json.dumps({'at':out['at_utc'],'max_forecast_difference':max(out['forecast_discrepancies_384_scalars'].values()),
         'target_valid_responses':out['target_valid_responses'],'source_reference':e['reference'],
         'primary_pass':out['original_joint_rule_passes'],'P':{k:v for k,v in evaluated['models']['P'].items() if k!='per_person_losses'},
         'rss':out['largest_measured_process_rss_bytes_macos']},default=lambda v:np.asarray(v).tolist()),flush=True)

def numerical_audit():
    records=[]
    for v in [-3.,0.,2.]:
        a,z,t0=1.3,.37,0.
        def flux(t,upper):
            distance=a*(1-z) if upper else a*z
            sign=1 if upper else -1
            return float(zero_drift_hit(np.array([t]),a,distance)[0]*np.exp(sign*v*distance-.5*v*v*t))
        masses=[quad(lambda t:flux(t,u),0,np.inf,epsabs=1e-10,epsrel=1e-10,limit=200)[0] for u in [False,True]]
        mean=sum(quad(lambda t:t*flux(t,u),0,np.inf,epsabs=1e-10,epsrel=1e-10,limit=200)[0] for u in [False,True])
        prob=z if v==0 else (-np.expm1(-2*v*a*z))/(-np.expm1(-2*v*a))
        expected=a*a*z*(1-z) if v==0 else (a*prob-a*z)/v
        t=np.geomspace(.05*a*a,1.2*a*a,60)
        image=zero_drift_hit(t,a,a*z,'image');spectral=zero_drift_hit(t,a,a*z,'spectral')
        records.append({'drift':v,'mass':sum(masses),'upper_mass':masses[1],'analytic_upper':prob,
                        'mean_decision_time':mean,'analytic_mean':expected,
                        'probability_error':abs(masses[1]-prob),'mean_error':abs(mean-expected),
                        'image_spectral_max_difference':error(image,spectral)})
    source=read('SOURCE_FIT.json');held=read('PREDICTIONS.json')
    refined=[]
    for i,p in enumerate(held['baseline_parameters']):
        for name,q in [('P',False),('Q',True)]:
            transformed=original_map(p,source[name+'_mapping'],q)
            n256,p256=moments(transformed,256);n384,p384=moments(transformed,384)
            refined.append({'id':i+10,'model':name,'mean_probability_max_difference':error(p256,p384),
                            'normalization_max_difference':error(n256,n384)})
    out={'at_utc':stamp(),'analytic_mass_probability_mean_checks':records,'held_quadrature_256_384':refined,
         'scope':'Independent analytical first-passage checks and alternative 80-term/17-image implementation; original full model optimizer refits UNRUN.',
         'largest_measured_process_rss_bytes_macos':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss}
    assert max(r['probability_error'] for r in records)<1e-7
    assert max(r['mean_error'] for r in records)<1e-7
    save('NUMERICAL_AUDIT.json',out)
    print('Independent Wiener analytical and 256/384 quadrature checks saved',flush=True)

def controls():
    author=read('CONTROLS.json');author_contrary=read('CONTRARY.json')
    persons=np.arange(8)[:,None]-3.5
    truthp=np.array([.90,.82,.70,.86])+persons*.005
    truthrt=np.array([.60,.66,.72,.68])+persons*.015
    truth=np.stack([truthp,truthrt],axis=-1)
    counts=np.array([16,16,16,48])
    results=[];worst=0.;gatecounts={};changed={'remove_accuracy_noise':0,'remove_rt_noise':0,'remove_both':0}
    for kind in ['substantial_signal','equal_expected_loss_null']:
        for rep in range(100):
            seed=2026110200+rep+(1000 if kind.endswith('null') else 0)
            rng=np.random.default_rng(seed)
            pc=np.clip(truthp+rng.normal(0,.01,(8,1)),.01,.99)
            measured=np.stack([rng.binomial(counts,pc)/counts,truthrt+rng.normal(0,.015,(8,1))+rng.normal(0,.20/np.sqrt(counts),(8,4))],axis=-1)
            pred={'P':truth.copy() if kind=='substantial_signal' else truth+.015,
                  'REFERENCE':truth-.10 if kind=='substantial_signal' else truth-.015}
            rr=scores(pred,measured,'REFERENCE',seed)
            saved=author['records'][rep+(100 if kind.endswith('null') else 0)]
            assert saved['kind']==kind and saved['rep']==rep and saved['seed']==seed
            for model in ['P','REFERENCE']:
                for key,value in rr['models'][model].items():
                    worst=max(worst,error(value,saved[model][key]))
            assert rr['primary_P_rule_passes']==saved['passes']
            results.append({'kind':kind,'rep':rep,'seed':seed,'passes':rr['primary_P_rule_passes'],'gates':rr['gates']})
            if kind=='substantial_signal':
                for key,passed in rr['gates'].items():gatecounts[key]=gatecounts.get(key,0)+int(passed)
                for removal in changed:
                    altered=measured.copy()
                    if removal in ['remove_accuracy_noise','remove_both']:altered[:,:,0]=truthp
                    if removal in ['remove_rt_noise','remove_both']:altered[:,:,1]=truthrt
                    changed[removal]+=int(scores(pred,altered,'REFERENCE',seed)['primary_P_rule_passes'])
    out={'at_utc':stamp(),'original_signal_passes':sum(x['passes'] for x in results if x['kind']=='substantial_signal'),
         'original_null_passes':sum(x['passes'] for x in results if x['kind']=='equal_expected_loss_null'),
         'all_200_saved_scores_max_difference':worst,'signal_gate_pass_counts':gatecounts,
         'changed_observation_diagnostics':changed,'records':results,
         'limitation':'Conditional score controls, not Wiener/source-refit recovery,10%boundary power or calibrated coverage. Noise-removal changes observations, not the original gate. Real P passes accuracy cap and fails RT.',
         'largest_measured_process_rss_bytes_macos':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss}
    assert out['original_signal_passes']==author['signal_passes']==18
    assert out['original_null_passes']==author['null_passes']==2
    assert changed=={x['changed_observation']:x['passes'] for x in author_contrary['changed_observation_diagnostics']}
    assert worst<1e-10
    save('CONTROL_AUDIT.json',out)
    print(json.dumps({k:v for k,v in out.items() if k not in ['records','limitation']},default=lambda v:np.asarray(v).tolist()),flush=True)

if __name__=='__main__':
    audit()
    numerical_audit()
    controls()
