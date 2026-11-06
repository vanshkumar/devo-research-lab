"""Frozen held-unit conditional comparison. All observations are development."""
import os
for k in ['OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','VECLIB_MAXIMUM_THREADS','NUMEXPR_NUM_THREADS']:os.environ[k]='1'
from pathlib import Path
import json, hashlib, datetime, sys, time, resource
import numpy as np
import pandas as pd
from scipy.special import expit
from scipy.optimize import minimize
from input_support import load

OUT=Path(__file__).resolve().parent
RIDGE=1e-4
TAUS=[2,8,32]

def ewma(e,start,tau):
    h=0.;a=np.exp(-1./tau);v=np.zeros(len(e))
    for t in range(len(e)):
        if start[t]:h=0.
        v[t]=h;h=a*h+(1-a)*e[t]
    return v

def digest(s):return hashlib.sha256(('20261031:'+s).encode()).hexdigest()

def features():
    data=load();schedules=sorted({str(d['schedule']) for d in data if str(d['species'])=='human'},key=digest)
    sf={s:i%5 for i,s in enumerate(schedules)};mf={}
    labs=sorted({str(d['lab']) for d in data if str(d['species'])=='mouse'})
    for lab in labs:
        ids=sorted([str(d['subject']) for d in data if str(d['species'])=='mouse' and str(d['lab'])==lab],key=digest)
        mf.update({s:i%5 for i,s in enumerate(ids)})
    ns=[];hs=[];stim=[];zs=[];om=[];records=[];timing_errors=[];checks=[]
    base_names=['intercept']+['signed_contrast_'+str(v) for v in [.0625,.1,.125,.25,.5,1.]]+['previous_choice']+['choice_tau'+str(v) for v in TAUS]+['exposure','sensory_exposure','early_sensory','early_bias','early_omission','sensory_early_sensory','sensory_early_bias','session','session_position']
    for ui,d in enumerate(data):
        species=str(d['species']);sid=str(d['subject']);c=d['choice'].astype(float);fb=d['feedback'].astype(float);x=d['contrast'];start=d['session_start'].astype(bool)
        sign=np.sign(x);n=len(c);ix=np.arange(n)
        e=c*fb*(c!=0);es=sign;ez=e*(x==0);eo=sign*(c==0)
        H=np.column_stack([ewma(e,start,t) for t in TAUS]);S=np.column_stack([ewma(es,start,t) for t in TAUS]);Z=np.column_stack([ewma(ez,start,t) for t in TAUS]);O=np.column_stack([ewma(eo,start,t) for t in TAUS])
        err=float(np.max(np.abs(H-S-Z+O)));timing_errors.append(err)
        assert err<3e-15,(sid,err)
        assert np.max(np.abs(H-np.column_stack([d['h'+str(t)] for t in TAUS])))<1e-15
        # Changing every current/future suffix cannot change the prediction features at cut.
        cut=min(250,n-1);alt=e.copy();alt[cut:]=-alt[cut:]+.123
        assert np.max(np.abs(np.column_stack([ewma(alt,start,t) for t in TAUS])[:cut+1]-H[:cut+1]))==0
        early=(ix<200);valid=early&(c!=0);sens=valid&(x!=0)
        calib=[float(np.mean(c[sens]*sign[sens])) if sens.any() else 0.,float(np.mean(c[valid])) if valid.any() else 0.,float(np.mean(c[early]==0))]
        t=(ix-399.5)/200.
        C=np.column_stack([ewma(c,start,v) for v in TAUS])
        b=np.column_stack([np.ones(n)]+[sign*np.isclose(np.abs(x),v,rtol=0,atol=1e-10) for v in [.0625,.1,.125,.25,.5,1.]]+[d['prev_choice']]+[C[:,j] for j in range(3)]+[t,sign*t,np.full(n,calib[0]),np.full(n,calib[1]),np.full(n,calib[2]),sign*calib[0],sign*calib[1],d['session']/5.,np.minimum(d['session_trial'],600)/600.])
        assert b.shape[1]==len(base_names)
        g=int(d['condition']) if species=='human' else 2
        N=np.zeros((n,3*b.shape[1]));N[:,g*b.shape[1]:(g+1)*b.shape[1]]=b
        St=np.zeros((n,9));St[:,g*3:(g+1)*3]=S
        m=(ix>=200)&(ix<600)&(d['session_trial']>=32)&np.isin(np.abs(x),[0,.25,.5,1.])
        ii=np.where(m)[0]
        for j in ii:
            # Current/past predictor bins; labels never enter these cells.
            cell='|'.join(map(str,[float(x[j]),int(H[j,0]>=0),int(np.digitize(H[j,1],[-.5,0,.5])),int(np.digitize(H[j,2],[-.25,0,.25]))]))
            records.append(dict(unit=ui,subject=sid,species=species,schedule=str(d['schedule']),lab=str(d['lab']),condition=int(d['condition']),trial=int(j),session=int(d['session'][j]),session_trial=int(d['session_trial'][j]),contrast=float(x[j]),choice=float(c[j]),feedback=float(fb[j]),responded=bool(c[j]!=0),fold=sf[str(d['schedule'])] if species=='human' else mf[sid],cell=cell,repNum=float(d['repNum'][j])))
        ns.append(N[m]);stim.append(St[m]);hs.append(H[m]);zs.append(Z[m]);om.append(O[m])
        checks.append(dict(subject=sid,species=species,rows=int(m.sum()),early_calibration=calib,history_identity_error=err))
    frame=pd.DataFrame(records);N=np.concatenate(ns);H=np.concatenate(hs);S=np.concatenate(stim);Z=np.concatenate(zs);O=np.concatenate(om)
    cells=[];admit=set()
    for key,g in frame.groupby('cell',sort=True):
        a=g[g.species=='human'];b=g[g.species=='mouse']
        ok=len(a)>=20 and len(b)>=20 and a.unit.nunique()>=5 and b.unit.nunique()>=5 and a.schedule.nunique()>=2
        if ok:admit.add(key)
        cells.append(dict(cell=key,human_rows=len(a),mouse_rows=len(b),human_units=a.unit.nunique(),mouse_units=b.unit.nunique(),human_schedules=a.schedule.nunique(),admitted=ok))
    frame['common_support']=frame.cell.isin(admit)
    names=[g+':'+v for g in ['human_discovery','human_taught','mouse'] for v in base_names]
    return frame,N,H,S,Z,O,names,checks,cells

def weights(frame,mask):
    a=frame.loc[mask];w=np.zeros(len(frame))
    for species,g in a.groupby('species'):
        sizes=g.groupby('unit').size();nu=len(sizes)
        for u,n in sizes.items():w[g.index[g.unit==u]]=1./(2*nu*n)
    assert w.sum()>0
    w/=w.sum()
    return w[mask]

def objective(beta,X,y,w,offset=None):
    eta=X@beta
    if offset is not None:eta=eta+offset
    loss=float(np.sum(w*(np.logaddexp(0,eta)-y*eta))+.5*RIDGE*np.dot(beta,beta))
    grad=X.T@(w*(expit(eta)-y))+RIDGE*beta
    return loss,grad

def fit(X,y,w,offset=None):
    init=np.zeros(X.shape[1]);r=None
    for retry in range(3):
        r=minimize(objective,init,args=(X,y,w,offset),jac=True,method='L-BFGS-B',options=dict(maxiter=1200,ftol=1e-14,gtol=1e-8,maxls=40))
        if np.max(np.abs(r.jac))<=1e-6:break
        init=r.x
    diag=dict(success=bool(np.max(np.abs(r.jac))<=1e-6),gradient_max=float(np.max(np.abs(r.jac))),objective=float(r.fun),iterations=int(r.nit),message=str(r.message))
    if not diag['success']:raise RuntimeError(str(diag))
    return r.x,diag

def structural(frame,N,H,S,model,aug=False):
    base=np.column_stack([N,S]) if aug else N
    if model=='B':return base
    if model=='H':return np.column_stack([base,H])
    species=(frame.species=='mouse').to_numpy()
    return np.column_stack([base,H*(~species[:,None]),H*species[:,None]])

def crossfit(frame,N,H,S,y,aug=False,transfer=False,tag='main'):
    valid=frame.responded.to_numpy();preds={k:np.full(len(y),np.nan) for k in ['B','H','T']}
    if transfer:preds.update({k:np.full(len(y),np.nan) for k in ['human_fixed','mouse_fixed']})
    fitlog=[]
    for fold in range(5):
        train=valid&(frame.fold.to_numpy()!=fold);test=valid&(frame.fold.to_numpy()==fold);w=weights(frame,train)
        for model in ['B','H','T']:
            X=structural(frame,N,H,S,model,aug)
            beta,diag=fit(X[train],y[train],w)
            preds[model][test]=expit(X[test]@beta)
            fitlog.append(dict(tag=tag,augmented=aug,fold=fold,model=model,coefficients=beta.tolist(),**diag))
        if transfer:
            base=structural(frame,N,H,S,'B',aug)
            for source in ['human','mouse']:
                # Fix source coefficients; only target nuisance is recalibrated.
                sm=train&(frame.species.to_numpy()==source);sw=weights(frame,sm);sw=sw/sw.sum()
                beta,diag=fit(np.column_stack([base[sm],H[sm]]),y[sm],sw)
                theta=beta[-3:];offset=H@theta
                # Refitting nuisance jointly with fixed history is algebraically block-separable.
                nb,nd=fit(base[train],y[train],w,offset=offset[train])
                preds[source+'_fixed'][test]=expit(base[test]@nb+offset[test])
                fitlog.append(dict(tag=tag,augmented=aug,fold=fold,model=source+'_fixed',source_history=theta.tolist(),nuisance_coefficients=nb.tolist(),source_diagnostics=diag,**nd))
        print(json.dumps(dict(progress=tag,augmented=aug,fold=fold,fit_count=len(fitlog))),flush=True)
    for p in preds.values():assert np.isfinite(p[valid]).all() and ((p[valid]>0)&(p[valid]<1)).all()
    return preds,fitlog

def unit_scores(frame,preds,y):
    records=[]
    for scope in ['support','all_common_contrast','zero','high']:
        m=frame.responded.to_numpy().copy()
        if scope=='support':m &= frame.common_support.to_numpy()
        if scope=='zero':m &= frame.contrast.to_numpy()==0
        if scope=='high':m &= np.abs(frame.contrast.to_numpy())>=.5
        for u,a in frame.loc[m].groupby('unit'):
            ii=a.index.to_numpy();r={k:a.iloc[0][k] for k in ['unit','subject','species','schedule','lab','condition','fold']};r.update(scope=scope,n=len(ii))
            for name,p in preds.items():
                pp=np.clip(p[ii],1e-9,1-1e-9)
                r[name+'_loss']=float(np.mean(-(y[ii]*np.log(pp)+(1-y[ii])*np.log1p(-pp))))
                r[name+'_brier']=float(np.mean((pp-y[ii])**2))
            records.append(r)
    return pd.DataFrame(records)

def bootstrap(g,column,reps=2000):
    rng=np.random.default_rng(20261031);vals=[]
    if len(g)==0:return [None,None]
    if g.iloc[0].species=='human':
        clusters=[a for _,a in g.groupby('schedule')]
        for _ in range(reps):
            draw=[]
            for j in rng.integers(len(clusters),size=len(clusters)):
                a=clusters[j];draw.extend(a[column].to_numpy()[rng.integers(len(a),size=len(a))])
            vals.append(np.mean(draw))
    else:
        clusters=[a for _,a in g.groupby('lab')]
        for _ in range(reps):
            draw=[]
            for a in clusters:draw.extend(a[column].to_numpy()[rng.integers(len(a),size=len(a))])
            vals.append(np.mean(draw))
    return np.quantile(vals,[.025,.975]).tolist()

def summarize(scores,intervals=True):
    rows=[];contrasts=[('H','B'),('T','H'),('T','B'),('human_fixed','B'),('mouse_fixed','B'),('T','human_fixed'),('T','mouse_fixed')]
    for (species,scope),g in scores.groupby(['species','scope']):
        for a,b in contrasts:
            if a+'_loss' not in g:continue
            g=g.copy();g['gain']=g[b+'_loss']-g[a+'_loss']
            gain=float(g.gain.mean());ci=bootstrap(g,'gain') if intervals else [None,None]
            r=dict(species=species,scope=scope,comparison=a+'-minus-'+b,units=len(g),rows=int(g.n.sum()),gain_nat=gain,interval95=ci,brier_gain=float(np.mean(g[b+'_brier']-g[a+'_brier'])),meaningful_positive=(gain>=.005 and ci[0] is not None and ci[0]>0))
            if species=='mouse':r['leave_one_lab_out']={lab:float(a0.gain.mean()) for lab in g.lab.unique() for a0 in [g[g.lab!=lab]] if len(a0)}
            if species=='human':r['leave_one_schedule_out']={s:float(a0.gain.mean()) for s in g.schedule.unique() for a0 in [g[g.schedule!=s]] if len(a0)}
            rows.append(r)
    return rows

def diagnostics(frame,N,H,S,Z,O,checks,cells):
    b=np.arange(N.shape[1])*.001;valid=frame.responded.to_numpy();y=(frame.choice.to_numpy()==1).astype(float);w=weights(frame,valid)
    loss,grad=objective(b,N[valid],y[valid],w);rng=np.random.default_rng(17);errors=[]
    for i in range(5):
        v=rng.normal(size=len(b));v/=np.linalg.norm(v);eps=1e-5
        fd=(objective(b+eps*v,N[valid],y[valid],w)[0]-objective(b-eps*v,N[valid],y[valid],w)[0])/(2*eps)
        errors.append(abs(fd-grad@v))
    assert max(errors)<1e-8
    rows=[]
    # Fixed +1 revealed/-1 stimulus shift. Each task has its own stimulus nuisance.
    for species in ['human','mouse']:
        m=(frame.species.to_numpy()==species)&frame.responded.to_numpy();res=Z[m]-O[m];delta=np.sum(res,axis=1)
        ident=float(np.max(np.abs(H[m]-S[m].reshape((-1,3,3)).sum(axis=1)-res)))
        assert ident<3e-15
        rows.append(dict(species=species,rows=int(m.sum()),decomposition_max_error=ident,residual_rms=np.sqrt(np.mean(res**2,axis=0)).tolist(),history_rms=np.sqrt(np.mean(H[m]**2,axis=0)).tolist(),
                         logit_shift_quantiles=np.quantile(delta,[0,.01,.05,.5,.95,.99,1]).tolist(),logit_shift_rms=float(np.sqrt(np.mean(delta**2))),
                         identical_to_stimulus_rows=int(np.sum(np.max(np.abs(res),axis=1)<1e-12)),
                         max_choice_probability_shift_bound=float(np.max(np.tanh(np.abs(delta)/4))),
                         mean_choice_probability_shift_bound=float(np.mean(np.tanh(np.abs(delta)/4)))))
    report=dict(gradient_directional_errors=errors,history_current_future_invariance=True,per_unit_checks=checks,cells=cells,coefficient_shift_witness=rows,
                interpretation='Restricted actual-input near ambiguity, not exact equivalence on all rows or a neural-mechanism claim')
    (OUT/'DIAGNOSTICS.json').write_text(json.dumps(report,indent=2)+'\n')

def main():
    controls='--controls' in sys.argv;start=time.time();frame,N,H,S,Z,O,names,checks,cells=features()
    y=(frame.choice.to_numpy()==1).astype(float);valid=frame.responded.to_numpy()
    if not controls:
        diagnostics(frame,N,H,S,Z,O,checks,cells)
        frame.to_csv(OUT/'scoring_rows.csv',index=False)
        (OUT/'FEATURES.json').write_text(json.dumps(dict(nuisance_names=names,stimulus_names=[g+':stimulus_tau'+str(t) for g in ['human_discovery','human_taught','mouse'] for t in TAUS],history_names=['revealed_tau'+str(t) for t in TAUS],ridge=RIDGE),indent=2)+'\n')
        all_summary=[];all_fit=[];prob={}
        for aug in [False,True]:
            preds,logs=crossfit(frame,N,H,S,y,aug,transfer=True)
            scores=unit_scores(frame,preds,y);scores.to_csv(OUT/('unit_scores_S.csv' if aug else 'unit_scores_B.csv'),index=False)
            summ=summarize(scores)
            for r in summ:r['baseline']='S' if aug else 'B'
            all_summary.extend(summ);all_fit.extend(logs)
            for k,v in preds.items():prob[('S_' if aug else 'B_')+k]=v
            (OUT/'FITS.json').write_text(json.dumps(all_fit,indent=2)+'\n')
            (OUT/'SUMMARY.json').write_text(json.dumps(all_summary,indent=2)+'\n')
        np.savez_compressed(OUT/'predictions.npz',**prob,y=y)
        print(json.dumps([r for r in all_summary if r['scope']=='support'],indent=2),flush=True)
    else:
        w=weights(frame,valid);base,_=fit(N[valid],y[valid],w);eta=N@base
        output=[];fitlogs=[]
        for family in ['null','shared','different']:
            for seed in range(6):
                rng=np.random.default_rng(20261101+100*['null','shared','different'].index(family)+seed)
                shift=np.zeros(len(frame)) if family=='null' else 1.5*H[:,1]
                if family=='different':shift*=np.where(frame.species=='human',1.,-1.)
                yy=rng.binomial(1,expit(eta+shift)).astype(float)
                for aug in [False,True]:
                    pp,ll=crossfit(frame,N,H,S,yy,aug,False,tag=family+str(seed))
                    ss=summarize(unit_scores(frame,pp,yy),False)
                    for r in ss:r.update(family=family,seed=seed,baseline='S' if aug else 'B')
                    output.extend(ss);fitlogs.extend(ll)
                (OUT/'CONTROLS.json').write_text(json.dumps(output,indent=2)+'\n')
                (OUT/'CONTROL_FITS.json').write_text(json.dumps(fitlogs,indent=2)+'\n')
        print(json.dumps([r for r in output if r['scope']=='support'],indent=2),flush=True)
    r=dict(utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),elapsed_seconds=time.time()-start,rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
           input_npz_bytes=(OUT/'consumed_inputs.npz').stat().st_size,decoded_array_bytes=sum(a.nbytes for a in [N,H,S,Z,O]),scoring_rows=len(frame),responding_rows=int(valid.sum()),mode='controls' if controls else 'main')
    (OUT/('CONTROL_RUN.json' if controls else 'ANALYSIS_RUN.json')).write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r),flush=True)

if __name__=='__main__':main()
