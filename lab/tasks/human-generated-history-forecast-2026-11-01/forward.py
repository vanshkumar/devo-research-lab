"""Frozen-kernel forecasts; separate checks/freeze/forecast/score entry points."""
import os
for k in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','VECLIB_MAXIMUM_THREADS','NUMEXPR_NUM_THREADS'):
    os.environ[k]='1'
import sys
sys.dont_write_bytecode=True
import argparse, hashlib, io, itertools, json, resource, time, traceback
from pathlib import Path
from datetime import datetime, timezone
import numpy as np
from numpy.polynomial.hermite import hermgauss
from scipy.special import expit

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
CAMP=ROOT/'campaigns/human_learning_routes_2026-10-28'
NAMES=('intercept','contrast_0.1','contrast_0.25','contrast_0.5','contrast_1','previous_choice','later_time','sensory_time')
HNAMES=('history_tau2','history_tau8','history_tau32')
DECAY=np.exp(-1/np.array([2.,8.,32.]))
NODES,WEIGHTS=hermgauss(20)
WEIGHTS=WEIGHTS/np.sqrt(np.pi)
CDF=np.cumsum(WEIGHTS); CDF[-1]=1.
PINS=[]

def utc(): return datetime.now(timezone.utc).isoformat()
def read(p,charge=3):
    b=p.read_bytes(); PINS.append(dict(path=str(p.relative_to(ROOT)),bytes=len(b),sha256=hashlib.sha256(b).hexdigest(),charge=len(b)*charge)); return b
def load():
    data=json.loads(read(HERE/'FORECAST_INPUTS.json'))
    fits={v:json.loads(read(CAMP/f'outputs/primary/{v}_fit.json')) for v in ('shared','no_history')}
    return data,fits
def write(p,x): p.write_text(json.dumps(x,indent=2,allow_nan=False)+'\n')
def fingerprint(p): return hashlib.sha256(read(p)).hexdigest()
def verify_freeze():
    lock=json.loads(read(HERE/'FREEZE.json'))
    for rel,digest in lock['sha256'].items(): assert fingerprint(ROOT/rel)==digest,rel
    return lock

def setup(fit,person):
    choice=np.asarray(person['prefix_choice'],float)
    fb=np.asarray(person['prefix_feedback'],float)
    contrast=np.asarray(person['side_contrast'],float)
    cal=[]
    for a,b in ((0,100),(100,200)):
        good=np.isin(choice[a:b],(-1,1)) & (contrast[a:b]!=0)
        cal.append(float(np.mean(choice[a:b][good]*np.sign(contrast[a:b][good]))) if good.any() else 0.)
    good=np.isin(choice,(-1,1))
    cal += [float(np.mean(choice[good])) if good.any() else 0.,float(1.-good.mean())]
    transform=fit['calibration_transform']
    cal=(np.array(cal)-np.array(transform['center']))/np.array(transform['scale'])
    coef=dict(zip(fit['feature_names'],fit['beta'])); g=person['condition']-.5
    bn=np.array([coef[n]+g*coef['condition:'+n]+sum(cal[j]*coef[transform['names'][j]+':'+n] for j in range(4)) for n in NAMES])
    bh=np.zeros(3)
    if fit['variant']=='shared':
        bh=np.array([coef[n]+sum(cal[j]*coef[transform['names'][j]+':'+n] for j in range(4)) for n in HNAMES])
    h=np.zeros(3)
    for a,b in zip(choice,fb): h=DECAY*h+(1-DECAY)*(a*b if a in (-1.,1.) and b in (-1.,1.) else 0.)
    sign=np.sign(contrast[200:]); tm=(np.arange(200,600)-399.5)/200
    n=np.column_stack([np.ones(400)]+[sign*np.isclose(abs(contrast[200:]),z,rtol=0,atol=1e-8) for z in (.1,.25,.5,1.)]+[np.zeros(400),tm,sign*tm])
    return dict(bn=bn,bh=bh,h=h,previous=float(choice[-1]),base=np.einsum('ij,j->i',n,bn),sign=sign,
                side=np.asarray(person['teacher_side'][200:],float),random_sd=float(fit['config']['random_sd']),history=fit['variant']=='shared')

def scalar_prob(s,t,h,previous):
    eta=s['base'][t]+s['bn'][5]*previous+float(h@s['bh'])
    var=s['random_sd']**2*(1+s['sign'][t]**2+(float(h@h) if s['history'] else 0.))
    return float(np.sum(WEIGHTS*expit(eta+np.sqrt(2*var)*NODES)))

def exact_zero(s,steps=400):
    h=s['h'].copy(); mass={s['previous']:1.}; result=[]
    for t in range(steps):
        p=sum(w*scalar_prob(s,t,h,previous) for previous,w in mass.items())
        result.append(p); mass={-1.:1-p,1.:p}; h=DECAY*h+(1-DECAY)*s['side'][t]
    return np.array(result)

def particles(states,calibration,setting,repetition,person_index,n=4096,steps=400):
    rng=np.random.Generator(np.random.PCG64(np.random.SeedSequence([20261102,setting,repetition,person_index])))
    if setting==0: q=rng.beta(calibration['alpha'],calibration['beta'],n)
    elif setting==1: q=np.full(n,min(1.,2*calibration['mean']))
    elif setting==2: q=np.zeros(n)
    else: raise ValueError(setting)
    response_weight=1-q; weight_sum=response_weight.sum()
    h=np.repeat(states[0]['h'][None,:],n,axis=0)
    previous=np.repeat(np.array([s['previous'] for s in states])[:,None],n,axis=1)
    result=np.empty((steps,2)); omissions=0
    for t in range(steps):
        node=NODES[np.searchsorted(CDF,rng.random(n))]
        choice_uniform=rng.random(n); omit=rng.random(n)<q; omissions+=int(omit.sum())
        actions=[]
        for v,s in enumerate(states):
            eta=s['base'][t]+s['bn'][5]*previous[v]+np.einsum('ij,j->i',h,s['bh'])
            var=s['random_sd']**2*(1+s['sign'][t]**2+(np.einsum('ij,ij->i',h,h) if s['history'] else 0.))
            prob=expit(eta+np.sqrt(2*var)*node)
            result[t,v]=float(np.sum(response_weight*prob)/weight_sum)
            action=np.where(choice_uniform<prob,1.,-1.); action[omit]=0.; actions.append(action)
        # The current target enters ONLY after choices, as environmental feedback.
        feedback=actions[0]*states[0]['side'][t]
        evidence=actions[0]*feedback
        h=DECAY*h+(1-DECAY)*evidence[:,None]
        previous=np.asarray(actions)
    # At the initial step every particle shares the prefix, so integrate it exactly.
    for v,s in enumerate(states): result[0,v]=scalar_prob(s,0,s['h'],s['previous'])
    return result,omissions

def checks():
    data,fits=load()
    sys.path.insert(0,str(CAMP/'experiments'))
    import pandas as pd
    from model import FitResult,prepare_features,predict_model
    frames=[]; engine={v:[] for v in fits}
    for p in data['people']:
        choice=list(p['prefix_choice'])+[1,-1,0,1]
        fb=list(p['prefix_feedback'])+[a*s if a else 0 for a,s in zip(choice[200:],p['teacher_side'][200:204])]
        frames.append(pd.DataFrame(dict(subject=p['subject'],trial=np.arange(204),instructions=p['condition'],sideContrast=p['side_contrast'][:204],choice=choice,feedbackType=fb)))
        for v,fit in fits.items():
            s=setup(fit,p); h=s['h'].copy(); previous=s['previous']; pred=[]
            for t in range(4):
                pred.append(scalar_prob(s,t,h,previous)); a=choice[200+t]
                h=DECAY*h+(1-DECAY)*(a*fb[200+t]); previous=a
            engine[v].extend(pred)
    frame=pd.concat(frames,ignore_index=True); comparisons={}
    for v in fits:
        path=CAMP/f'outputs/primary/{v}_fit.json'; fit=FitResult.load(path)
        PINS.append(dict(path=str(path.relative_to(ROOT)),bytes=path.stat().st_size,charge=2*path.stat().st_size,note='additional frozen-class load'))
        f=prepare_features(frame,calibration_transform=fit.calibration_transform,config=fit.config)
        source=predict_model(fit,f)[f.rows.trial.ge(200).to_numpy()]
        difference=float(np.max(abs(source-np.array(engine[v])))); assert difference<1e-12
        comparisons[v]=dict(constructed_probabilities=len(source),max_absolute_error=difference)
    p=data['people'][0]; s=setup(fits['shared'],p); exact=exact_zero(s,4)
    enumerated=np.zeros(4); total=0.
    for path in itertools.product((-1,1),repeat=4):
        h=s['h'].copy(); previous=s['previous']; weight=1.
        for t,a in enumerate(path):
            prob=scalar_prob(s,t,h,previous); weight*=prob if a==1 else 1-prob
            h=DECAY*h+(1-DECAY)*s['side'][t]; previous=a
        total+=weight; enumerated+=weight*(np.array(path)==1)
    assert abs(total-1)<1e-13 and np.max(abs(enumerated-exact))<1e-13
    # Exact all-omission state limit; no biological measurement assumption.
    h=s['h'].copy()
    for t in range(4): h=DECAY*h; previous=0.
    assert np.max(abs(h-s['h']*DECAY**4))<1e-14 and previous==0.
    states=[setup(fits[v],p) for v in ('shared','no_history')]
    cal={x['condition']:x for x in data['observation_calibration']}[p['condition']]
    simulated=np.array([particles(states,cal,2,r,0,n=8192,steps=4)[0] for r in range(8)])
    truth=np.column_stack([exact_zero(x,4) for x in states])
    error=simulated.mean(axis=0)-truth; se=simulated.std(axis=0,ddof=1)/np.sqrt(8)
    assert np.all(abs(error)<6*se+1e-3)
    out=dict(utc=utc(),pass_all=True,constructed_path_source_checks=comparisons,
             four_step=dict(paths=16,total_mass=total,maximum_error=float(np.max(abs(enumerated-exact)))),
             no_omission_particle_control=dict(particles_per_rep=8192,reps=8,max_abs_error=float(np.max(abs(error))),max_mcse=float(np.max(se))),
             all_omission_decay_and_previous_zero=True,actual_later_responses_used=False,
             interpretation='Reference and implementation controls, not full empirical power or recovery.')
    write(HERE/'CHECKS.json',out); print(json.dumps(out,indent=2))

def freeze():
    assert json.loads(read(HERE/'CHECKS.json'))['pass_all']
    assert not (HERE/'FREEZE.json').exists()
    paths=[HERE/'PROTOCOL.md',HERE/'forward.py',HERE/'FORECAST_INPUTS.json',HERE/'FEASIBILITY.json',HERE/'CHECKS.json']
    paths += [CAMP/f'outputs/primary/{v}_fit.json' for v in ('shared','no_history')]
    out=dict(utc=utc(),stage='before main forecasts and new scores',postvalidation_consumed=True,
             sha256={str(p.relative_to(ROOT)):fingerprint(p) for p in paths},
             main=dict(reps=8,particles_per_rep=4096),double_omission=dict(reps=4,particles_per_rep=4096),no_omission='exact two-state recursion',
             utility_gain_nat=.01,maximum_score_mcse=.001)
    write(HERE/'FREEZE.json',out); print(json.dumps(out,indent=2))

def forecast():
    lock=verify_freeze(); assert not (HERE/'FORECASTS.npz').exists()
    data,fits=load(); people=data['people']; calibration={x['condition']:x for x in data['observation_calibration']}
    arrays={}; generated_counts={}
    for setting,label,reps in ((0,'main',8),(1,'double_omission',4)):
        out=np.empty((reps,len(people),400,2)); omitted=0
        for i,p in enumerate(people):
            states=[setup(fits[v],p) for v in ('shared','no_history')]
            for r in range(reps):
                out[r,i],k=particles(states,calibration[p['condition']],setting,r,i); omitted+=k
            if (i+1)%13==0: print(label,i+1,'of',len(people),flush=True)
        arrays[label]=out; generated_counts[label]=omitted
    arrays['no_omission']=np.array([[exact_zero(setup(fits[v],p)) for v in ('shared','no_history')] for p in people]).transpose(0,2,1)
    assert all(np.isfinite(x).all() and np.all((x>0)&(x<1)) for x in arrays.values())
    np.savez_compressed(HERE/'FORECASTS.npz',**arrays)
    out=dict(utc=utc(),subjects=[p['subject'] for p in people],variants=['shared','no_history'],
             shape={k:list(v.shape) for k,v in arrays.items()},generated_omissions_across_replicates=generated_counts,
             forecasts_sha256=fingerprint(HERE/'FORECASTS.npz'),freeze_utc=lock['utc'],
             actual_future_choices_feedback_omissions_read=False,current_response_conditioning='trajectory weight1-q',
             notes='All later target realizations are supplied to the environment by known deterministic source schedule, not generated from a stochastic teacher. No learner-fit uncertainty or joint trajectory score.')
    write(HERE/'FORECAST_META.json',out); print(json.dumps(out,indent=2))

def windows(person):
    bias=np.array(person['teacher_bias']); offset=np.full(600,999)
    starts=np.flatnonzero((bias[1:]!=bias[:-1])&(bias[1:]!=.5)&(bias[:-1]!=.5))+1
    for k in starts:
        if k<200: continue
        end=next((j for j in range(k+1,600) if bias[j]!=bias[k]),600)
        offset[k:end]=np.arange(end-k)
    contrast=abs(np.array(person['side_contrast'][200:]))
    return (offset[200:]<30)&(contrast<=.1),contrast==0

def logscore(p,y):
    p=np.clip(p,1e-12,1-1e-12); return y*np.log(p)+(1-y)*np.log1p(-p)

def score():
    lock=verify_freeze(); meta=json.loads(read(HERE/'FORECAST_META.json'))
    assert fingerprint(HERE/'FORECASTS.npz')==meta['forecasts_sha256']
    data,fits=load(); people=data['people']; ids=[p['subject'] for p in people]
    arrays=dict(np.load(io.BytesIO(read(HERE/'FORECASTS.npz'))))
    import pandas as pd
    validation=pd.read_csv(io.BytesIO(read(CAMP/'inputs/validation_numeric.csv')),dtype={'subject':str,'session':str})
    split=pd.read_csv(io.BytesIO(read(CAMP/'protocol/split_manifest.csv')),dtype={'subject':str}).set_index('subject')
    assert set(validation.subject)==set(ids)
    frames=[validation.loc[validation.subject==s].sort_values('trial').iloc[200:600] for s in ids]
    y=np.array([a.choice.eq(1).to_numpy() for a in frames],float)
    responded=np.array([a.choice.isin([-1,1]).to_numpy() for a in frames])
    input_primary=np.array([windows(p)[0] for p in people]); zero=np.array([windows(p)[1] for p in people])
    masks=dict(primary=input_primary&responded,all_later=responded,zero_primary=input_primary&zero&responded)
    assert input_primary.sum()==2895 and masks['primary'].sum()==2867
    groups={}
    for i,p in enumerate(people): groups.setdefault((p['condition'],p['partition']),[]).append(i)
    def perperson(p,mask):
        delta=logscore(p[:,:,0],y)-logscore(p[:,:,1],y)
        return np.array([delta[i,mask[i]].mean() for i in range(len(ids))])
    def ci(values,seed):
        rng=np.random.default_rng(seed); draws=np.zeros(5000)
        for ix in groups.values(): draws+=rng.choice(values[ix],size=(5000,len(ix)),replace=True).sum(axis=1)/len(values)
        return dict(mean=float(values.mean()),low=float(np.quantile(draws,.025)),high=float(np.quantile(draws,.975)),reps=5000)
    settings={}; rows=[]
    for label,a in arrays.items():
        p=a.mean(axis=0) if a.ndim==4 else a
        values=perperson(p,masks['primary']); loo=[]
        if a.ndim==4:
            for r in range(len(a)): loo.append(perperson((len(a)*p-a[r])/(len(a)-1),masks['primary']))
            loo=np.array(loo); centered=loo-loo.mean(axis=0)
            per_mcse=np.sqrt((len(a)-1)/len(a)*np.sum(centered**2,axis=0))
            overall_mcse=float(np.sqrt((len(a)-1)/len(a)*np.sum((loo.mean(axis=1)-loo.mean())**2)))
        else: per_mcse=np.zeros(len(ids)); overall_mcse=0.
        result=dict(primary=ci(values,20261103),score_mcse=overall_mcse,
                    all_later=ci(perperson(p,masks['all_later']),20261104),zero_primary=ci(perperson(p,masks['zero_primary']),20261105))
        brier=(p[:,:,1]-y)**2-(p[:,:,0]-y)**2
        result['brier_gain']=ci(np.array([brier[i,masks['primary'][i]].mean() for i in range(len(ids))]),20261106)
        result['primary_mean_log_shared']=float(np.mean([logscore(p[i,:,0],y[i])[masks['primary'][i]].mean() for i in range(len(ids))]))
        result['primary_mean_log_baseline']=float(np.mean([logscore(p[i,:,1],y[i])[masks['primary'][i]].mean() for i in range(len(ids))]))
        result['partitions']={part:dict(n_people=len(ix),mean=float(values[ix].mean())) for part,ix in ((part,[i for i,x in enumerate(people) if x['partition']==part]) for part in sorted({x['partition'] for x in people}))}
        result['schedules']={s:dict(n_people=len(ix),mean=float(values[ix].mean())) for s,ix in ((s,[i for i,x in enumerate(people) if split.loc[x['subject'],'schedule']==s]) for s in sorted(split.loc[ids,'schedule'].unique()))}
        result['leave_one_schedule_out']={s:float(np.mean([values[i] for i,x in enumerate(people) if split.loc[x['subject'],'schedule']!=s])) for s in result['schedules']}
        schedule_groups=[[i for i,x in enumerate(people) if split.loc[x['subject'],'schedule']==s] for s in result['schedules']]
        rng=np.random.default_rng(20261107); draws=[]
        for _ in range(5000):
            v=[]
            for selected in rng.integers(0,len(schedule_groups),len(schedule_groups)):
                ix=schedule_groups[selected]; v.extend(rng.choice(values[ix],len(ix),replace=True))
            draws.append(np.mean(v))
        result['schedule_person_interval']=dict(low=float(np.quantile(draws,.025)),high=float(np.quantile(draws,.975)),reps=5000)
        ps,pb=p[:,:,0],p[:,:,1]
        expected_h=logscore(ps,ps)-logscore(pb,ps); expected_b=logscore(ps,pb)-logscore(pb,pb)
        assert np.min(expected_h)>-1e-12 and np.max(expected_b)<1e-12
        result['known_answer']=dict(expected_gain_under_shared=float(np.mean([expected_h[i,input_primary[i]].mean() for i in range(len(ids))])),expected_gain_under_baseline=float(np.mean([expected_b[i,input_primary[i]].mean() for i in range(len(ids))])),scope='Exact marginal Bernoulli proper-score identities, not full generative recovery/power.')
        settings[label]=result
        for i,person in enumerate(people): rows.append(dict(setting=label,subject=person['subject'],condition=person['condition'],partition=person['partition'],schedule=split.loc[person['subject'],'schedule'],n_primary=int(masks['primary'][i].sum()),gain_nat=float(values[i]),mcse=float(per_mcse[i])))
    pd.DataFrame(rows).to_csv(HERE/'PERSON_SCORES.csv',index=False)
    main=settings['main']; passed=(main['primary']['mean']>=.01 and main['primary']['low']>0 and main['score_mcse']<.001)
    robust=passed and all(settings[s]['primary']['mean']>=.01 for s in ('no_omission','double_omission'))
    out=dict(utc=utc(),forecast_saved_utc=meta['utc'],freeze_utc=lock['utc'],postvalidation=True,people=39,primary_opportunities=int(input_primary.sum()),primary_responding=int(masks['primary'].sum()),settings=settings,primary_utility_pass=bool(passed),omission_sensitivity_robust_pass=bool(robust),learning_refits=0,
        scope='Known exact deterministic source-schedule continuation; source-only iid observation-law completion; frozen sequential integrated one-step kernels; marginal responding-choice scores. No generated stochastic teacher, joint trajectory/engagement utility, biological mechanism, cross-policy transport or scientific goal completion.')
    write(HERE/'SCORES.json',out); print(json.dumps(out,indent=2))

def main():
    parser=argparse.ArgumentParser(); parser.add_argument('stage',choices=['checks','freeze','forecast','score']); stage=parser.parse_args().stage
    started=time.monotonic(); error=None
    try: globals()[stage]()
    except BaseException:
        error=traceback.format_exc(); raise
    finally:
        write(HERE/f'RUN_{stage}.json',dict(utc=utc(),stage=stage,wall_seconds=time.monotonic()-started,peak_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,explicit_read_hash_decode_charge=sum(x['charge'] for x in PINS),pins=PINS,error=error,physical_io='unknown',host_runtime_peak='unknown',public_operations=0))

if __name__=='__main__': main()
