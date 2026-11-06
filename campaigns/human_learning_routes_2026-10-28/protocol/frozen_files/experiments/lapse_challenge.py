"""Matched fixed-lapse sensitivity; lapse rates are probes, not identified estimates.

Both hypotheses use the same probability floor/ceiling. This challenges the
primary model's empirical (rather than explicit mixture) lapse flexibility.
"""
import json
import numpy as np
import pandas as pd
from scipy.optimize import minimize
from scipy.special import expit
from model import *
from analysis import *

def fit_mixture(f,variant,rates):
    base=fit_model(f,variant);X,Z,names,rnames,sd=build_design(f,variant)
    mask=f.responded&f.rows.trial.ge(200).to_numpy();X=X[mask];Z=Z[mask];y=f.y[mask];codes=f.subject_codes[mask]
    lapse=np.where(f.group[mask]>0,rates[1],rates[0]);pdim=X.shape[1];q=Z.shape[1];ns=len(f.subjects)
    prior=1/sd**2;rv=1/base.config.random_sd**2
    def fun(theta):
        b=theta[:pdim];u=theta[pdim:].reshape(ns,q)
        eta=np.einsum('ij,j->i',X,b)+np.einsum('ij,ij->i',Z,u[codes]);s=expit(eta);p=lapse/2+(1-lapse)*s
        p=np.clip(p,1e-12,1-1e-12)
        loss=-np.sum(y*np.log(p)+(1-y)*np.log1p(-p))+.5*np.sum(b*b*prior)+.5*rv*np.sum(u*u)
        r=(p-y)/(p*(1-p))*(1-lapse)*s*(1-s)
        gb=np.einsum('ij,i->j',X,r)+b*prior
        gu=np.column_stack([np.bincount(codes,weights=r*Z[:,j],minlength=ns) for j in range(q)])+rv*u
        return loss,np.r_[gb,gu.ravel()]
    initial=np.r_[base.beta,base.random_effects.ravel()];attempts=[];candidates=[]
    for start in [initial,np.zeros_like(initial)]:
        for _ in range(3):
            opt=minimize(fun,start,jac=True,method='L-BFGS-B',options=dict(ftol=1e-14,gtol=1e-5,maxiter=1500,maxcor=20,maxls=50))
            obj,grad=fun(opt.x);attempts.append(dict(objective=float(obj),gradient=float(np.max(np.abs(grad))),success=bool(opt.success)));start=opt.x
            if np.max(np.abs(grad))<.001:break
        assert opt.success and np.max(np.abs(grad))<.001,attempts
        candidates.append((obj,opt))
    obj,opt=min(candidates,key=lambda pair:pair[0]);_,grad=fun(opt.x)
    base.beta=opt.x[:pdim];base.random_effects=opt.x[pdim:].reshape(ns,q)
    base.diagnostics=dict(base.diagnostics,mixture_lapse_rates=rates,mixture_attempts=attempts,objective=float(obj),max_abs_gradient=float(np.max(np.abs(grad))))
    return base

def mixture_probability(fit,f,rates,override=None):
    base=predict_model(fit,f,adaptation_group_override=override)
    lapse=np.where(f.group>0,rates[1],rates[0]);return lapse/2+(1-lapse)*base

def run_case(dev,val,rates):
    f=prepare_features(dev);vf=prepare_features(val,calibration_transform=f.calibration_transform)
    fits={v:fit_mixture(f,v,rates) for v in ['shared','condition']}
    w=windows(attach_split(vf.rows));y=vf.y
    p={v:mixture_probability(fit,vf,rates) for v,fit in fits.items()}
    w['delta_log']=log_score(p['condition'],y)-log_score(p['shared'],y)
    pp=w.loc[w.primary_responded].groupby(['subject','instructions','schedule','partition']).delta_log.mean().reset_index().rename(columns={'instructions':'condition'})
    z=zero_contrast_features(vf);shift=(mixture_probability(fits['condition'],z,rates,1)-mixture_probability(fits['condition'],z,rates,0))*w.old_majority.to_numpy()
    w['shift']=shift;effect=w.loc[w.switch_offset.lt(20)].groupby('subject')['shift'].mean().mean()
    return pp,dict(**bootstrap_mean(pp,'delta_log'),standardized_effect=float(effect),rates=rates),fits

def main():
    assert (ROOT/'protocol/VALIDATION_OPENED.json').exists()
    dev=attach_split(pd.read_csv(ROOT/'inputs/development_numeric.csv',dtype={'subject':str,'session':str}));val=attach_split(pd.read_csv(ROOT/'inputs/validation_numeric.csv',dtype={'subject':str,'session':str}))
    out=ROOT/'outputs/lapse_challenge';out.mkdir(exist_ok=True)
    rows=[]
    for name,rates in [('equal_002',[.002,.002]),('discovery10_taught002',[.10,.002]),('discovery25_taught002',[.25,.002])]:
        pp,summary,fits=run_case(dev,val,rates);pp.to_csv(out/(name+'_participants.csv'),index=False);write_json(out/(name+'_summary.json'),summary)
        for v,fit in fits.items():fit.save(out/(name+'_'+v+'.json'))
        rows.append(dict(name=name,**summary));print(rows[-1],flush=True)
    pd.DataFrame(rows).to_csv(out/'summary.csv',index=False)

if __name__=='__main__':main()
