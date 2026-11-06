"""Same-mean-family covariance-aware diagnostic and one-pass feasible GLS.

Original OLS files remain intact. Oracle covariance is simulation-only.
Practical covariance uses restricted DEVELOPMENT main residuals and is fixed
and identical for the two models. Recovery repeats that calibration step.
"""
import argparse,json,sys,time,hashlib
from pathlib import Path
import numpy as np
from scipy import linalg,stats
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parents[1]/'experiments'))
import state_models as s
OLS_PROFILE=s.profile

def whiten(d,z):
    if 'gls_matrix' in d:
        return linalg.blas.dgemm(1.,d['gls_matrix'],z) if z.ndim==2 else linalg.blas.dgemv(1.,d['gls_matrix'],z)
    result=z.copy();power=d['gls_power'];scale=np.sqrt(1-power**2)
    if z.ndim==2:result[1:]=(z[1:]-power[:,None]*z[:-1])/scale[:,None]
    else:result[1:]=(z[1:]-power*z[:-1])/scale
    return result

def setup(ds,phi=None,oracle=False):
    for d in ds:
        idx=d['indices'][d['good']]
        if oracle:
            distance=abs(idx[:,None]-idx[None,:]);z=idx/823-.5
            covariance=6.25*(.35*.7**distance+.65*.25**distance)
            covariance+=.18*np.cos(2*np.pi*distance/260)+.36*z[:,None]*z[None,:]
            chol=linalg.cholesky(covariance,lower=True,check_finite=False)
            d['gls_matrix']=linalg.solve_triangular(chol,np.eye(len(idx)),lower=True,check_finite=False)
        else:
            d['gls_power']=phi**np.diff(idx)
        nw=whiten(d,d['N'][d['good']]);yw=whiten(d,d['y'][d['good']])
        q,r=linalg.qr(nw,mode='economic',check_finite=False)
        d.update(gN=nw,gQ=q,gR=r,gy=yw,gyr=yw-s.mm(q,s.mm(q.T,yw)))

def profile(ds,pars,details=False):
    ss=[];rows=[]
    for d in ds:
        X=s.state_design(d,pars);wx=whiten(d,X[d['good']]);q=d['gQ']
        xr=wx-s.mm(q,s.mm(q.T,wx))
        coef,_,rank,_=linalg.lstsq(xr,d['gyr'],cond=1e-10,lapack_driver='gelsy',check_finite=False)
        residual=d['gyr']-s.mm(xr,coef);ss.append(float(np.sum(residual**2)))
        if details:
            nc=linalg.solve_triangular(d['gR'],s.mm(q.T,d['gy']-s.mm(wx,coef)),check_finite=False)
            pred=s.mm(X,coef)+s.mm(d['N'],nc)
            norms=np.linalg.norm(xr,axis=0);norms[norms==0]=1
            singular=linalg.svdvals(xr/norms)
            rows.append({'key':d['p']['key'],'file':d['p']['file'],'set':d['p']['set'],
                'coef':coef,'nuisance':nc,'prediction':pred,'sse':ss[-1],
                'state_rank':rank,'state_standardized_condition':float(singular[0]/singular[-1]),'baseline':d['baseline']})
    return np.asarray(ss),rows

def calibrate_phi(ds,ols):
    cross=0.;square=0.
    for d,row in zip(ds,ols['people']):
        residual=d['y']-row['prediction']
        keep=np.isfinite(residual[:-1])&np.isfinite(residual[1:])&(np.arange(719)%180!=179)
        x=residual[:-1][keep];y=residual[1:][keep]
        cross+=float(np.sum(x*y));square+=float(np.sum(x*x))
    return float(np.clip(cross/square,-.8,.8))

def fit_pair(ds,oracle=False,multi=True):
    if oracle:
        phi=None;setup(ds,oracle=True)
    else:
        s.profile=OLS_PROFILE
        preliminary=s.fit(ds,multi=multi)
        phi=calibrate_phi(ds,preliminary)
        setup(ds,phi=phi)
    s.profile=profile
    restricted=s.fit(ds,multi=multi)
    alternative=s.fit(ds,True,start=restricted['parameters'],multi=multi)
    return restricted,alternative,phi

def simulate(name,target,rep,ps,counts):
    rng=np.random.default_rng(932000+rep)
    scales=np.exp(rng.normal(0,.20,len(ps)));scales/=scales.mean()
    a,b=((.92,.9) if name=='slow_modulation' else (.65,1.))
    if name in ['fast_modulation','slow_modulation']:
        delta,true=s.calibrated_delta(target,a,b,scales,counts);kind='retention'
    elif name=='delayed_expression':delta=target*5/b;true=target;kind='expression_next'
    elif name=='online_expression':delta=0.;true=0.;kind='online'
    else:delta=0.;true=0.;kind='two_timescale'
    effect=delta*b*np.mean(a**np.arange(5));ds=[]
    for i,p in enumerate(ps):
        pp=dict(p)
        g=s.generate(p['c'],p['j'],seed=382000+rep*100+i,kind=kind,effect=effect,
             noise_sd=2.5,drift_scale=.6,retentions=(a,.50) if name=='slow_modulation' else (a,.97),
             gains=(b,.30) if name=='slow_modulation' else (b,.20),person_scale=float(scales[i]),omission_rate=.01)
        pp['y']=g['y'];ds.append(s.cell_design(pp))
    return ds,true

def entry(ds,alt,true,rep,phi=None):
    unc=s.uncertainty(ds,alt);ci=unc['cluster_profile_ci95'];theta=float(s.curves(ds,alt).mean())
    return {'rep':rep,'truth':true,'theta':theta,'se':unc['cluster_profile_se'],'ci95':ci,
       'coverage':bool(ci[0]<=true<=ci[1]),'false_equivalence':bool(ci[0]>-.2 and ci[1]<.2 and abs(true)>=.2-1e-8),
       'detect_zero_exclusion':bool(ci[0]>0 or ci[1]<0),'interval_inside_margin':bool(ci[0]>-.2 and ci[1]<.2),
       'phi':phi,'parameters':alt['parameters'],'diagnostic_only':unc['diagnostic_only'],
       'slow_at_upper_bound':bool(alt['parameters'][1]>=.99499),'starts':alt['starts']}

def oracle_check():
    original=json.loads((s.OUT/'state_models_stress.json').read_text())['records']
    rows=[r for r in original if r['scenario']=='fast_modulation' and r['target_theta']==.2]
    failures=[r['rep'] for r in rows if r['false_equivalence_at_or_outside_boundary']]
    rest=[r for r in list(np.linspace(0,99,20).astype(int)) if r not in failures]
    chosen=sorted(failures+rest[:20-len(failures)])
    ps=s.load('development','Hand_raw',inputs_only=True);counts=[s.counts_for_truth(p) for p in ps]
    out=[];start=time.time()
    for rep in chosen:
        ds,true=simulate('fast_modulation',.2,rep,ps,counts)
        restricted,alt,phi=fit_pair(ds,oracle=True,multi=True)
        r=entry(ds,alt,true,int(rep));old=next(q for q in rows if q['rep']==rep)
        r.update(old_theta=old['fit_theta'],old_ci95=old['profile_ci95'],old_false_equivalence=old['false_equivalence_at_or_outside_boundary'])
        out.append(r)
        result={'selection':'All14 OLS false-equivalence cases plus6 evenly spaced other cases; diagnostic paired test, not unbiased coverage estimate.',
                'records':out,'elapsed_seconds':time.time()-start,
                'covariance':'Exact generator mixture AR(.70,.25) weights(.35,.65), SD2.5 plus random-phase sinusoid and random-slope drift covariance.'}
        (s.OUT/'state_models_gls_oracle.json').write_text(json.dumps(s.jsonable(result),indent=2)+'\n')
        print('oracle',rep,'old',round(old['fit_theta'],4),'new',round(r['theta'],4),'CI',np.round(r['ci95'],4),'falseEq',r['false_equivalence'],'elapsed',round(time.time()-start),flush=True)

def empirical():
    ps=s.load('development','Hand_raw');ds=[s.cell_design(p) for p in ps];start=time.time()
    rr,ff,phi=fit_pair(ds,multi=True)
    for m in [rr,ff]:
        m['actual_schedule_curve']=s.summarize_curve(s.curves(ds,m))
        m['stationary_readout_curve']=s.summarize_curve(s.curves(ds,m,stationary=True))
        m['isolated_common_condition_curve']=s.summarize_curve(s.curves(ds,m,isolated=True))
    ff['profile_uncertainty']=s.uncertainty(ds,ff)
    out={'scope':'Development-only same-family one-pass AR1 feasible GLS; profile interval conditional on calibrated covariance shape.',
        'restricted':rr,'alternative':ff,'phi':phi,'elapsed_seconds':time.time()-start,
        'calibration':'Pooled same-portion adjacent covariance / lagged residual sum squares from OLS restricted DEVELOPMENT fit; clipped to[-.8,.8]. One pass; common fixed phi in both models.'}
    (s.OUT/'state_models_fgls_development.json').write_text(json.dumps(s.jsonable(out),indent=2)+'\n')
    frozen={'restricted':s.frozen_set_coefficients(ds,rr),'alternative':s.frozen_set_coefficients(ds,ff),
        'phi':phi,'development_only':True,'script_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        'state_models_dependency_sha256':hashlib.sha256(Path(s.__file__).read_bytes()).hexdigest(),
        'split_sha256':hashlib.sha256((s.ROOT/'protocol/split.json').read_bytes()).hexdigest()}
    (s.OUT/'state_models_fgls_frozen_predictions.json').write_text(json.dumps(s.jsonable(frozen),indent=2)+'\n')
    print(json.dumps(s.jsonable({'phi':phi,'pars':ff['parameters'],'curve':ff['actual_schedule_curve'],
        'uncertainty':ff['profile_uncertainty'],'elapsed_seconds':time.time()-start}),indent=2),flush=True)

def recovery(reps=100,scope='core'):
    ps=s.load('development','Hand_raw',inputs_only=True);counts=[s.counts_for_truth(p) for p in ps]
    scenarios=[('fixed_two_state',0.),('fast_modulation',.2),('fast_modulation',-.2)]
    if scope=='alternatives':scenarios=[('slow_modulation',-.2),('slow_modulation',.2),('delayed_expression',.2),('online_expression',0.)]
    rows=[];start=time.time()
    for name,target in scenarios:
        for rep in range(reps):
            ds,true=simulate(name,target,rep,ps,counts)
            rr,alt,phi=fit_pair(ds,multi=False)
            r=entry(ds,alt,true,rep,phi);r.update(scenario=name,target=target)
            rows.append(r)
            if rep%10==0 or rep==reps-1:
                result={'scope':scope,'records':rows,'elapsed_seconds':time.time()-start,
                    'procedure':'Each replicate reestimates common AR1 from its restricted OLS main residuals, then refits both matched mean models. Profile CI holds estimated phi fixed; recovery assesses that full procedure.'}
                (s.OUT/('state_models_fgls_recovery_'+scope+'.json')).write_text(json.dumps(s.jsonable(result),indent=2)+'\n')
                cur=[q for q in rows if q['scenario']==name and q['target']==target]
                print('fgls',name,target,rep+1,'bias',round(np.mean([q['theta']-q['truth'] for q in cur]),4),
                      'coverage',sum(q['coverage'] for q in cur),'falseEq',sum(q['false_equivalence'] for q in cur),
                      'phi',round(np.mean([q['phi'] for q in cur]),3),'elapsed',round(time.time()-start),flush=True)

def bootstrap(reps=100):
    ps=s.load('development','Hand_raw');ds=[s.cell_design(p) for p in ps]
    strata=[[d for d in ds if d['p']['file']==f] for f in sorted(set(d['p']['file'] for d in ds))]
    rng=np.random.default_rng(420281);rows=[];start=time.time()
    for rep in range(reps):
        sample=[part[i] for part in strata for i in rng.integers(0,len(part),len(part))]
        rr,alt,phi=fit_pair(sample,multi=False);theta=float(s.curves(sample,alt).mean())
        rows.append({'rep':rep,'theta':theta,'parameters':alt['parameters'],'phi':phi,
             'slow_at_upper_bound':bool(alt['parameters'][1]>=.99499)})
        if rep%10==0 or rep==reps-1:
            th=[r['theta'] for r in rows]
            out={'records':rows,'percentile_ci95':np.quantile(th,[.025,.975]),'sd':float(np.std(th,ddof=1)) if len(th)>1 else None,
                'elapsed_seconds':time.time()-start,'recalibration':'AR1 recalibrated from OLS restricted main residuals in every person bootstrap.'}
            (s.OUT/'state_models_fgls_bootstrap.json').write_text(json.dumps(s.jsonable(out),indent=2)+'\n')
            print('fgls_bootstrap',rep+1,'ci',out['percentile_ci95'],'elapsed',round(time.time()-start),flush=True)

def evaluate():
    assert (s.ROOT/'protocol/VALIDATION_RELEASE.json').exists(),'Reserved outcomes sealed'
    frozen=json.loads((s.OUT/'state_models_fgls_frozen_predictions.json').read_text())
    people=s.load('validation','Hand_raw');rows=[]
    for p in people:
        preds={k:s.predicted_full(p,frozen[k]) for k in ['restricted','alternative']}
        observed=[];pr={k:[] for k in preds}
        for b in range(4):
            for loc in range(20,175):
                t=100+b*181+loc
                if p['c'][t]!=0:continue
                all_y=p['y'][np.r_[np.arange(t-5,t),np.arange(t+1,t+6)]]
                if not np.isfinite(all_y).all() or np.any(abs(all_y)>90):continue
                for h in range(1,6):
                    observed.append(p['y'][t+h]-p['y'][t-5:t].mean())
                    for k in preds:pr[k].append(preds[k][t+h]-preds[k][t-5:t].mean())
        y=np.asarray(observed);loss={k:float(np.mean((np.asarray(v)-y)**2)) for k,v in pr.items()}
        rows.append({'person':p['key'],'file':p['file'],'set':p['set'],'n_lag_events':len(y),**loss,'mse_gain':loss['restricted']-loss['alternative']})
    out={'scope':'Frozen FGLS same-family forecasts; reserved baseline mean only, no reserved covariance or state fit.',
        'people':rows,**s.prediction_score_summary(rows)}
    (s.OUT/'state_models_fgls_validation.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out,indent=2))

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('mode',choices=['oracle','empirical','recovery','bootstrap','evaluate']);ap.add_argument('--reps',type=int,default=100);ap.add_argument('--scope',choices=['core','alternatives'],default='core');args=ap.parse_args()
    if args.mode=='oracle':oracle_check()
    elif args.mode=='empirical':empirical()
    elif args.mode=='recovery':recovery(args.reps,args.scope)
    elif args.mode=='bootstrap':bootstrap(args.reps)
    else:evaluate()
