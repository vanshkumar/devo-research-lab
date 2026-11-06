"""Bounded two-state variable-projection challenge; development only by default.

Reads original files through analysis.load's split guard. No measured lagged
angle is used as an error-free state. State fits are not the primary estimand.
"""
import argparse
import hashlib
import json
import time
from pathlib import Path
import numpy as np
from scipy import linalg, optimize, stats
from threadpoolctl import threadpool_limits
threadpool_limits(1)
from analysis import load, cells_for, mm, ROOT, jsonable
from generators import generate

OUT=ROOT/'outputs'

def cell_design(p):
    cells=cells_for(p)
    ref=cells.index((0.,0.))
    others=[q for q in range(9) if q!=ref]
    rows=[];inputs=[];events=[];blocks=[];times=[];y=[]
    indices=[]
    base=p['y'][:100]
    baseline=float(np.nanmean(base[np.abs(base)<=90]))
    for b in range(4):
        ids=np.arange(100+b*181,280+b*181)
        indices.extend(ids.tolist())
        q=np.array([cells.index((p['c'][r],p['j'][r])) for r in ids])
        u=np.column_stack([q==k for k in others]).astype(float)
        inputs.append(u)
        events.append(((p['c'][ids]==0)&(p['j'][ids]!=0)).astype(float))
        block=np.column_stack([np.full(180,b==k,dtype=float) for k in range(4)])
        tm=(np.arange(180)-89.5)/89.5
        rows.append(np.column_stack([u,block,block*tm[:,None]]))
        y.extend((p['y'][ids]-baseline).tolist())
    N=np.vstack(rows);y=np.asarray(y)
    good=np.isfinite(y)&(np.abs(p['y'][indices])<=90)
    Q,R=linalg.qr(N[good],mode='economic',check_finite=False)
    yr=y[good]-mm(Q,mm(Q.T,y[good]))
    return {'p':p,'cells':cells,'ref':ref,'others':others,'inputs':inputs,'events':events,
        'N':N,'Q':Q,'R':R,'y':y,'yr':yr,'good':good,'indices':np.asarray(indices),
        'baseline':baseline}

def filtered(u,a):
    """History at readout, with updating only after current endpoint."""
    prod=np.cumprod(a)
    initial=np.r_[1.,prod[:-1]]
    scaled=u/prod[:,None]
    hist=initial[:,None]*np.vstack([np.zeros((1,u.shape[1])),np.cumsum(scaled,axis=0)[:-1]])
    assert np.isfinite(hist).all()
    return hist,initial

def state_design(d,pars):
    af,slow,ae=pars
    pieces=[]
    for b,(u,event) in enumerate(zip(d['inputs'],d['events'])):
        hfast,ifast=filtered(u,af+(ae-af)*event)
        hslow,islow=filtered(u,np.full(180,slow))
        block=np.column_stack([np.full(180,b==k,dtype=float) for k in range(4)])
        pieces.append(np.column_stack([hfast,hslow,block*ifast[:,None],block*islow[:,None]]))
    return np.vstack(pieces)

def profile(ds,pars,details=False):
    sse=[];rows=[]
    for d in ds:
        X=state_design(d,pars)
        x=X[d['good']];Q=d['Q'];xr=x-mm(Q,mm(Q.T,x))
        coef,res,rank,_=linalg.lstsq(xr,d['yr'],cond=1e-10,lapack_driver='gelsy',check_finite=False)
        residual=d['yr']-mm(xr,coef)
        sse.append(float(np.sum(residual**2)))
        if details:
            nc=linalg.solve_triangular(d['R'],mm(Q.T,d['y'][d['good']]-mm(x,coef)),check_finite=False)
            pred=mm(X,coef)+mm(d['N'],nc)
            norms=np.linalg.norm(xr,axis=0);norms[norms==0]=1
            singular=linalg.svdvals(xr/norms)
            rows.append({'key':d['p']['key'],'file':d['p']['file'],'set':d['p']['set'],
                         'coef':coef,'nuisance':nc,'prediction':pred,'sse':sse[-1],
                         'state_rank':rank,'state_standardized_condition':float(singular[0]/singular[-1]),
                         'baseline':d['baseline']})
    return np.asarray(sse),rows

def expand(v,alternative):
    return np.asarray(v) if alternative else np.r_[v,v[0]]

def fit(ds,alternative=False,start=None,multi=True,maxiter=70):
    bounds=[(.10,.85),(.86,.995)]+([(.01,1.35)] if alternative else [])
    if start is None:
        starts=[(.35,.90),(.65,.97),(.80,.99)]
        if alternative:starts=[(*q,q[0]) for q in starts]
    else:
        v=np.asarray(start)
        starts=[v if alternative else v[:2]]
        if multi and alternative:
            starts.extend([np.array([v[0],v[1],np.clip(v[0]+shift,.01,1.35)]) for shift in [-.20,.20]])
    if not multi:starts=starts[:1]
    total_n=sum(int(d['good'].sum()) for d in ds)
    history=[]
    for initial in starts:
        calls=[0]
        def fun(v):
            calls[0]+=1
            return float(profile(ds,expand(v,alternative))[0].sum()/total_n)
        opt=optimize.minimize(fun,initial,method='L-BFGS-B',bounds=bounds,
             options={'maxiter':maxiter,'ftol':1e-10,'gtol':1e-6,'maxls':25})
        history.append({'initial':list(initial),'x':opt.x,'mse':float(opt.fun),'success':bool(opt.success),
                        'message':str(opt.message),'calls':calls[0]})
    best=min(history,key=lambda q:q['mse'])
    pars=expand(best['x'],alternative)
    sse,rows=profile(ds,pars,True)
    return {'alternative':alternative,'parameters':pars,'parameter_names':['a_fast','a_slow','a_event_fast'],
            'delta':float(pars[2]-pars[0]),'sse':float(sse.sum()),'mse':float(sse.sum()/total_n),
            'n':total_n,'nonlinear_parameters':3 if alternative else 2,
            'linear_parameters_per_person':40,'starts':history,'people':rows,
            'model_note':'Separate person-specific gains in each state; direct endpoint cell effects, portion intercept/drift and initial states. Current-cell reference=(0,0).'}

def curve_for(d,row,pars,stationary=False,isolated=False):
    af,slow,ae=pars;delta=ae-af
    plus=d['others'].index(d['cells'].index((4.,0.)))
    minus=d['others'].index(d['cells'].index((-4.,0.)))
    gain=.5*(row['coef'][plus]-row['coef'][minus])
    if isolated:return gain*delta*af**np.arange(5)
    p=d['p'];out=[]
    for h in range(1,6):
        factors=[]
        for b in range(4):
            for loc in range(20,175):
                t=100+b*181+loc
                if p['c'][t]!=0 or (stationary and p['j'][t+h]!=0):continue
                ev=(p['c'][t+1:t+h]==0)&(p['j'][t+1:t+h]!=0)
                factors.append(float(np.prod(af+(ae-af)*ev)))
        out.append(gain*delta*np.mean(factors))
    return np.asarray(out)

def curves(ds,model,stationary=False,isolated=False):
    return np.asarray([curve_for(d,row,model['parameters'],stationary,isolated) for d,row in zip(ds,model['people'])])

def summarize_curve(values):
    n=len(values);curve=values.mean(axis=0)
    th=values.mean(axis=1);se=np.std(th,ddof=1)/np.sqrt(n)
    crit=stats.t.ppf(.975,n-1)
    return {'curve':curve,'theta':float(th.mean()),'conditional_person_se':float(se),
            'conditional_ci95':[float(th.mean()-crit*se),float(th.mean()+crit*se)],
            'note':'Conditional on fitted nonlinear parameters; not full uncertainty.'}

def uncertainty(ds,model,step=.001):
    """Participant-cluster profile-score delta method, including nonlinear fit.

    Fixed source strata are centered separately. Boundary/non-positive Hessian
    makes this diagnostic, not a calibrated confidence procedure.
    """
    pars=np.asarray(model['parameters']);n=len(ds)
    base_sse,_=profile(ds,pars)
    base_curve=curves(ds,model)
    grad=np.zeros((n,3));dcurve=np.zeros((5,3));H=np.zeros((3,3))
    for k in range(3):
        e=np.zeros(3);e[k]=step
        sp,rp=profile(ds,pars+e,True);sm,rm=profile(ds,pars-e,True)
        grad[:,k]=(sp-sm)/(2*step)
        H[k,k]=(sp.sum()+sm.sum()-2*base_sse.sum())/step**2
        cp=curves(ds,{'parameters':pars+e,'people':rp});cm=curves(ds,{'parameters':pars-e,'people':rm})
        dcurve[:,k]=(cp.mean(axis=0)-cm.mean(axis=0))/(2*step)
        for l in range(k):
            e2=np.zeros(3);e2[l]=step
            pp=profile(ds,pars+e+e2)[0].sum();pm=profile(ds,pars+e-e2)[0].sum()
            mp=profile(ds,pars-e+e2)[0].sum();mmv=profile(ds,pars-e-e2)[0].sum()
            H[k,l]=H[l,k]=(pp-pm-mp+mmv)/(4*step**2)
    eig=linalg.eigvalsh(H);inv=linalg.pinvh(H)
    centered_grad=grad.copy();centered_curve=base_curve.copy()
    for f in sorted(set(d['p']['file'] for d in ds)):
        ids=[i for i,d in enumerate(ds) if d['p']['file']==f]
        centered_grad[ids]-=centered_grad[ids].mean(axis=0)
        centered_curve[ids]-=centered_curve[ids].mean(axis=0)
    adj=mm(mm(centered_grad,inv),dcurve.T)*n
    influence=centered_curve-adj
    correction=n/(n-2) if n>2 else 1
    covcurve=mm(influence.T,influence)*correction/n**2
    se=float(np.sqrt(max(0,covcurve.mean())))
    est=float(base_curve.mean());crit=stats.t.ppf(.975,n-2)
    covpars=mm(mm(inv,mm(centered_grad.T,centered_grad)),inv)*correction
    scale=np.sqrt(np.maximum(np.diag(covpars),0));den=scale[:,None]*scale[None,:]
    correlation=np.divide(covpars,den,out=np.zeros_like(covpars),where=den>0)
    bounds=np.array([[.10,.85],[.86,.995],[.01,1.35]])
    boundary=bool(np.any(np.minimum(pars-bounds[:,0],bounds[:,1]-pars)<.002))
    return {'theta':est,'cluster_profile_se':se,'cluster_profile_ci95':[est-crit*se,est+crit*se],
            'curve_covariance':covcurve,'parameter_covariance':covpars,'parameter_correlation':correlation,
            'profile_hessian_eigenvalues':eig,'profile_hessian_condition':float(np.max(abs(eig))/np.min(abs(eig))),
            'near_parameter_boundary':boundary,'positive_profile_hessian':bool(np.all(eig>0)),
            'diagnostic_only':boundary or bool(np.any(eig<=0)),
            'method':'Stratified person-cluster profile-score sandwich plus delta-method observable; finite-difference step='+str(step)}

def frozen_set_coefficients(ds,model):
    sets={}
    for file in sorted(set(d['p']['file'] for d in ds)):
        ids=[i for i,d in enumerate(ds) if d['p']['file']==file]
        d=ds[ids[0]]
        sets[file]={'cells':d['cells'],'others':d['others'],
          'coef':np.mean([model['people'][i]['coef'] for i in ids],axis=0),
          'nuisance':np.mean([model['people'][i]['nuisance'] for i in ids],axis=0)}
    return {'parameters':model['parameters'],'sets':sets,
       'baseline_calibration':'Mean finite |Hand_raw|<=90 among original TN1..100; sign reversed. No main-outcome fitting.',
       'prediction_rule':'Use frozen set-average state/input/direct/drift/initial coefficients plus new-person baseline mean.'}

def predicted_full(p,frozen):
    # Build every forecast design from inputs and permitted baseline only.
    # Main outcomes are deliberately absent even from unused QR/residual setup.
    safe=dict(p);safe['y']=np.zeros(824,dtype=float)
    safe['y'][:100]=p['y'][:100]
    d=cell_design(safe);co=frozen['sets'][p['file']]
    pred=mm(state_design(d,np.asarray(frozen['parameters'])),np.asarray(co['coef']))+mm(d['N'],np.asarray(co['nuisance']))+d['baseline']
    full=np.full(824,np.nan);full[d['indices']]=pred
    return full

def fit_development():
    started=time.time();ps=load('development','Hand_raw');ds=[cell_design(p) for p in ps]
    restricted=fit(ds)
    print('restricted',restricted['parameters'],restricted['mse'],'seconds',time.time()-started,flush=True)
    full=fit(ds,True,start=restricted['parameters'])
    print('alternative',full['parameters'],full['mse'],'seconds',time.time()-started,flush=True)
    for model in [restricted,full]:
        model['actual_schedule_curve']=summarize_curve(curves(ds,model))
        model['stationary_readout_curve']=summarize_curve(curves(ds,model,stationary=True))
        model['isolated_common_condition_curve']=summarize_curve(curves(ds,model,isolated=True))
    full['profile_uncertainty']=uncertainty(ds,full)
    out={'scope':'Development only; state-model efficiency challenge does not replace preregistered observable.',
       'restricted':restricted,'alternative':full,'elapsed_seconds':time.time()-started,
       'in_sample_mse_gain':restricted['mse']-full['mse'],
       'split_sha256':hashlib.sha256((ROOT/'protocol/split.json').read_bytes()).hexdigest(),
       'script_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
    (OUT/'state_models_development.json').write_text(json.dumps(jsonable(out),indent=2)+'\n')
    frozen={'restricted':frozen_set_coefficients(ds,restricted),'alternative':frozen_set_coefficients(ds,full),
            'split_sha256':out['split_sha256'],'development_only':True,'script_sha256':out['script_sha256']}
    (OUT/'state_models_frozen_predictions.json').write_text(json.dumps(jsonable(frozen),indent=2)+'\n')
    print(json.dumps(jsonable({'restricted':restricted['parameters'],'alternative':full['parameters'],
        'curve':full['actual_schedule_curve'],'stationary':full['stationary_readout_curve'],
        'uncertainty':full['profile_uncertainty'],'elapsed_seconds':time.time()-started}),indent=2),flush=True)

def recovery(reps=8):
    ps=load('development','Hand_raw',inputs_only=True)
    ps=[p for f in ['tsay_TE_SPE.csv','tsay_controljump.csv'] for p in [q for q in ps if q['file']==f][:4]]
    records=[];started=time.time()
    for noise in [0.,2.5]:
        for effect in [0.,-.2,.2]:
            for rep in range(1 if noise==0 else reps):
                simulated=[];truths=[]
                for i,p in enumerate(ps):
                    pp=dict(p)
                    scale=1.0 if noise==0 else float(np.exp(np.random.default_rng(12000+rep*10+i).normal(0,.20)-.02))
                    g=generate(p['c'],p['j'],seed=80000+rep*20+i,
                        kind='two_timescale' if effect==0 else 'retention',effect=effect,
                        noise_sd=noise,drift_scale=0 if noise==0 else .6,
                        process_sd=0,person_scale=scale,omission_rate=0 if noise==0 else .01)
                    pp['y']=g['y'];simulated.append(pp);truths.append(g['truth'])
                ds=[cell_design(p) for p in simulated]
                rr=fit(ds,multi=False,start=[.65,.97,.65],maxiter=45)
                ff=fit(ds,True,multi=False,start=rr['parameters'],maxiter=55)
                u=uncertainty(ds,ff)
                # Actual-schedule truth matches mean counterfactual future products.
                truth_curves=[]
                for d,tr in zip(ds,truths):
                    co=np.zeros(24)
                    for q,cell in enumerate(d['cells']):
                        if q==d['ref']:continue
                        c,j=cell;mult=1-.4*(j!=0)+.1*np.sign(c*j)
                        co[d['others'].index(q)]=(c/4)*tr['gains'][0]*mult+.025*j*(tr['gains'][0]/.65)
                    truthpars=[.65,.97,.65+tr['delta_retention']]
                    truth_curves.append(curve_for(d,{'coef':co},truthpars))
                true=float(np.mean(truth_curves));ci=u['cluster_profile_ci95']
                records.append({'noise_sd':noise,'effect_reference_isolated':effect,'rep':rep,
                    'true_actual_schedule_theta':true,'fit_parameters':ff['parameters'],
                    'fit_theta':ff['actual_schedule_curve']['theta'] if 'actual_schedule_curve' in ff else float(curves(ds,ff).mean()),
                    'profile_ci95':ci,'profile_se':u['cluster_profile_se'],
                    'coverage':bool(ci[0]<=true<=ci[1]),'detect_zero_exclusion':bool(ci[0]>0 or ci[1]<0),
                    'diagnostic_only':u['diagnostic_only'],'mse_gain':rr['mse']-ff['mse'],
                    'n_people':len(ds)})
                (OUT/'state_models_recovery.json').write_text(json.dumps(jsonable({'records':records,'elapsed_seconds':time.time()-started}),indent=2)+'\n')
                print('recovery',noise,effect,rep,'truth',round(true,4),'fit',round(records[-1]['fit_theta'],4),'CI',np.round(ci,4),'elapsed',round(time.time()-started),flush=True)

def prediction_score_summary(rows):
    """Equal fixed-source means; uncertainty uses within-source people only."""
    summaries=[]
    for file in sorted(set(r['file'] for r in rows)):
        selected=[r for r in rows if r['file']==file]
        gains=np.asarray([r['mse_gain'] for r in selected]);n=len(gains)
        variance=float(np.var(gains,ddof=1)/n)
        summaries.append({'file':file,'set':selected[0]['set'],'n_people':n,
            'mean_person_mse_gain':float(gains.mean()),'se':float(np.sqrt(variance)),
            'mean_variance':variance,'df':n-1})
    variances=np.asarray([r['mean_variance'] for r in summaries])
    denominator=float(np.sum(variances**2/np.asarray([r['df'] for r in summaries])))
    df=float(variances.sum()**2/denominator) if denominator>0 else float('inf')
    estimate=float(np.mean([r['mean_person_mse_gain'] for r in summaries]))
    se=float(np.sqrt(variances.sum())/len(summaries));crit=stats.t.ppf(.975,df)
    return {'mean_person_mse_gain':estimate,'se':se,'df':df,
        'ci95':[estimate-crit*se,estimate+crit*se],'set_summaries':summaries,
        'inference':'Equal fixed-source means; within-source participant variances and Welch-Satterthwaite degrees of freedom.'}

def evaluate():
    assert (ROOT/'protocol/VALIDATION_RELEASE.json').exists(),'Reserved outcomes sealed'
    frozen=json.loads((OUT/'state_models_frozen_predictions.json').read_text())
    people=load('validation','Hand_raw');rows=[]
    for p in people:
        preds={k:predicted_full(p,frozen[k]) for k in ['restricted','alternative']}
        yy=[];pr={k:[] for k in preds}
        for b in range(4):
            for loc in range(20,175):
                t=100+b*181+loc
                if p['c'][t]!=0:continue
                observed=p['y'][np.r_[np.arange(t-5,t),np.arange(t+1,t+6)]]
                if not np.isfinite(observed).all() or np.any(abs(observed)>90):continue
                for h in range(1,6):
                    yy.append(p['y'][t+h]-p['y'][t-5:t].mean())
                    for k in preds:pr[k].append(preds[k][t+h]-preds[k][t-5:t].mean())
        yy=np.asarray(yy)
        losses={k:float(np.mean((np.asarray(v)-yy)**2)) for k,v in pr.items()}
        rows.append({'person':p['key'],'file':p['file'],'set':p['set'],'n_lag_events':len(yy),**losses,'mse_gain':losses['restricted']-losses['alternative']})
    out={'scope':'Reserved-person prediction with frozen state-model coefficients. Baseline mean only calibration.',
       'people':rows,**prediction_score_summary(rows)}
    (OUT/'state_models_validation.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out,indent=2))

def bootstrap(reps=100):
    ps=load('development','Hand_raw');ds=[cell_design(p) for p in ps]
    empirical=json.loads((OUT/'state_models_development.json').read_text())['alternative']
    start=empirical['parameters'];rng=np.random.default_rng(420281)
    strata=[[d for d in ds if d['p']['file']==f] for f in sorted(set(d['p']['file'] for d in ds))]
    records=[];started=time.time()
    for rep in range(reps):
        sample=[part[i] for part in strata for i in rng.integers(0,len(part),len(part))]
        fitm=fit(sample,True,start=start,multi=False,maxiter=60)
        pars=fitm['parameters'];curve=curves(sample,fitm).mean(axis=0)
        records.append({'rep':rep,'parameters':pars,'theta':float(curve.mean()),'curve':curve,
            'slow_at_upper_bound':bool(pars[1]>=.995-1e-5),
            'any_at_bound':bool(pars[0]<=.10001 or pars[0]>=.84999 or pars[1]<=.86001 or pars[1]>=.99499 or pars[2]<=.01001 or pars[2]>=1.34999),
            'success':fitm['starts'][0]['success']})
        if rep%10==0 or rep==reps-1:
            theta=np.array([r['theta'] for r in records])
            out={'records':records,'percentile_ci95':np.quantile(theta,[.025,.975]),
                'sd':float(np.std(theta,ddof=1)) if len(theta)>1 else None,
                'slow_upper_bound_count':sum(r['slow_at_upper_bound'] for r in records),
                'elapsed_seconds':time.time()-started}
            (OUT/'state_models_bootstrap.json').write_text(json.dumps(jsonable(out),indent=2)+'\n')
            print('bootstrap',rep+1,'thetaCI',out['percentile_ci95'],'slowupper',out['slow_upper_bound_count'],'elapsed',round(time.time()-started),flush=True)

def counts_for_truth(p):
    counts=[]
    for h in range(1,6):
        v=[]
        for b in range(4):
            for loc in range(20,175):
                t=100+b*181+loc
                if p['c'][t]!=0:continue
                v.append(int(np.sum((p['c'][t+1:t+h]==0)&(p['j'][t+1:t+h]!=0))))
        counts.append(np.asarray(v))
    return counts

def calibrated_delta(target,a,b,scales,countsets):
    def theta(delta):
        return np.mean([np.mean([b*scale*delta*np.mean(a**(h-k)*(a+delta)**k)
           for h,k in enumerate(counts)]) for scale,counts in zip(scales,countsets)])
    delta=optimize.brentq(lambda d:theta(d)-target,-a+.001,1.45-a,xtol=1e-12)
    return float(delta),float(theta(delta))

def stress(reps=100,altreps=50):
    """Full20 schedules; actual-schedule boundary effects and strong alternatives."""
    ps=load('development','Hand_raw',inputs_only=True)
    countsets=[counts_for_truth(p) for p in ps]
    scenarios=[('fixed_two_state',0.,reps),('fast_modulation',-.2,reps),('fast_modulation',.2,reps),
               ('delayed_expression',-.2,altreps),('delayed_expression',.2,altreps),
               ('rebound',0.,altreps),('online_expression',0.,altreps),
               ('slow_modulation',-.2,altreps),('slow_modulation',.2,altreps)]
    records=[];started=time.time()
    for name,target,count in scenarios:
        for rep in range(count):
            rng=np.random.default_rng(932000+rep)
            scales=np.exp(rng.normal(0,.20,len(ps)));scales/=scales.mean()
            # The slow-modulated generator is deliberately outside the model's
            # one-fast-state event law; fixed-retention two-state part overlaps.
            a,b=((.92,.9) if name=='slow_modulation' else (.65,1.))
            if name in ['fast_modulation','slow_modulation']:
                delta,true=calibrated_delta(target,a,b,scales,countsets)
                kind='retention'
            elif name=='delayed_expression':
                delta=target*5/b;true=target;kind='expression_next'
            elif name=='rebound':
                delta=1./b;true=0.;kind='rebound'
            elif name=='online_expression':
                delta=0.;true=0.;kind='online'
            else:
                delta=0.;true=0.;kind='two_timescale'
            effect=delta*b*np.mean(a**np.arange(5))
            retentions=(a,.50) if name=='slow_modulation' else (a,.97)
            gains=(b,.30) if name=='slow_modulation' else (b,.20)
            sample=[]
            for i,p in enumerate(ps):
                pp=dict(p)
                g=generate(p['c'],p['j'],seed=382000+rep*100+i,kind=kind,effect=effect,
                   noise_sd=2.5,drift_scale=.6,retentions=retentions,gains=gains,
                   person_scale=float(scales[i]),omission_rate=.01)
                pp['y']=g['y'];sample.append(pp)
            ds=[cell_design(p) for p in sample]
            rr=fit(ds,multi=False,start=[.65,.97,.65],maxiter=50)
            ff=fit(ds,True,multi=False,start=rr['parameters'],maxiter=60)
            u=uncertainty(ds,ff);ci=u['cluster_profile_ci95'];pars=ff['parameters']
            est=float(curves(ds,ff).mean())
            eq=bool(ci[0]>-.2 and ci[1]<.2)
            cov=np.asarray(u['parameter_covariance']);sds=np.sqrt(np.maximum(np.diag(cov),0))
            slow_bound_se=float((.995-pars[1])/sds[1]) if sds[1]>0 else None
            records.append({'scenario':name,'target_theta':target,'rep':rep,'true_theta':true,
                 'fit_theta':est,'profile_se':u['cluster_profile_se'],'profile_ci95':ci,
                 'coverage':bool(ci[0]<=true<=ci[1]),'detect_zero_exclusion':bool(ci[0]>0 or ci[1]<0),
                 'interval_inside_margin':eq,
                 'false_equivalence_at_or_outside_boundary':eq and abs(true)>=.2-1e-8,
                 'fit_parameters':pars,'generating_retention':retentions,'generating_event_retention':a+delta,
                 'near_boundary':u['near_parameter_boundary'],'slow_distance_to_upper_in_se':slow_bound_se,
                 'slow_at_upper_bound':bool(pars[1]>=.995-1e-5),
                 'positive_profile_hessian':u['positive_profile_hessian'],
                 'diagnostic_only':u['diagnostic_only'],'mse_gain':rr['mse']-ff['mse'],
                 'n_people':len(ds)})
            if rep%10==0 or rep==count-1:
                done=[r for r in records if r['scenario']==name and r['target_theta']==target]
                (OUT/'state_models_stress.json').write_text(json.dumps(jsonable({'records':records,'elapsed_seconds':time.time()-started}),indent=2)+'\n')
                print('stress',name,target,rep+1,'bias',round(np.mean([r['fit_theta']-r['true_theta'] for r in done]),4),
                      'coverage',sum(r['coverage'] for r in done),'falseEq',sum(r['false_equivalence_at_or_outside_boundary'] for r in done),
                      'slowupper',sum(r['slow_at_upper_bound'] for r in done),'elapsed',round(time.time()-started),flush=True)

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('mode',choices=['fit','recovery','evaluate','bootstrap','stress']);ap.add_argument('--reps',type=int,default=100);ap.add_argument('--altreps',type=int,default=50);args=ap.parse_args()
    if args.mode=='fit':fit_development()
    elif args.mode=='recovery':recovery(args.reps)
    elif args.mode=='bootstrap':bootstrap(args.reps)
    elif args.mode=='stress':stress(args.reps,args.altreps)
    else:evaluate()
