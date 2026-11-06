#!/usr/bin/env python3
"""Exact observational-equivalence counterexample; known-model excitation study.
Reproduction: .venv/bin/python experiments/causal_identification/run.py
"""
import csv
import json
import math
from pathlib import Path
import numpy as np

OUT = Path(__file__).resolve().parent
CONFIG = dict(radius=0.94, angle=0.18, sigma=0.1, sample_size=2000,
              burn_in=200, excitation=[0., .01, .03, .1, .3, 1.],
              exploratory_seeds=list(range(1000,1050)),
              verification_seeds=list(range(2000,2050)), exact_seed=101,
              clamp_trials=10000)
th=CONFIG['angle']
F=CONFIG['radius']*np.array([[np.cos(th),-np.sin(th)],[np.sin(th),np.cos(th)]])
SIGMA=CONFIG['sigma']

def simulate(A,B,T,rng,q=0., x0=None, eps=None, z=None):
    x=np.empty((T+1,2)); y=np.empty((T,2))
    x[0]=np.zeros(2) if x0 is None else x0
    if eps is None: eps=SIGMA*rng.normal(size=(T,2))
    if z is None: z=rng.normal(size=(T,2))
    for t in range(T):
        y[t]=x[t]+q*z[t]
        x[t+1]=A@x[t]+B@y[t]+eps[t]
    return x,y

def exact_check(T,seed):
    rng=np.random.default_rng(seed); eps=SIGMA*rng.normal(size=(T,2))
    x1,y1=simulate(F,np.zeros((2,2)),T,rng,eps=eps,x0=[1.,0.])
    x2,y2=simulate(np.zeros((2,2)),F,T,rng,eps=eps,x0=[1.,0.])
    # Independent reference implementation: scalar matrix recurrence with list.
    ref=[np.array([1.,0.])]
    for e in eps: ref.append(F.dot(ref[-1])+e)
    reference_error=float(np.max(np.abs(np.asarray(ref)-x1)))
    gram=np.column_stack([x1[:-1],y1])
    sv=np.linalg.svd(gram,compute_uv=False)
    nll=[]
    for c in np.linspace(0.,1.,11):
        mean=x1[:-1]@(c*F).T+y1@((1-c)*F).T
        resid=x1[1:]-mean
        # Constants are identical; include quadratic Gaussian term only.
        nll.append(float(np.sum(resid**2)/(2*SIGMA**2)))
    return dict(T=T,seed=seed,max_path_error=float(np.max(np.abs(x1-x2))),
                max_behavior_error=float(np.max(np.abs(y1-y2))),
                direct_reference_error=reference_error,
                design_rank=int(np.linalg.matrix_rank(gram)),design_singular_values=sv.tolist(),
                nll_range=max(nll)-min(nll),nll_by_c=nll)

def fit_one(seed,q):
    rng=np.random.default_rng(seed)
    A=.2*F; B=.8*F
    T=CONFIG['sample_size']; burn=CONFIG['burn_in']
    x,y=simulate(A,B,T+burn,rng,q=q)
    current=x[burn:-1]; yy=y[burn:]; nxt=x[burn+1:]
    design=np.column_stack([current,yy])
    coef=np.linalg.lstsq(design,nxt,rcond=None)[0]
    ah=coef[:2].T; bh=coef[2:].T
    sv=np.linalg.svd(design,compute_uv=False)
    # Alternative implementation: residualize y and future x on current x (FWL).
    fwl_error=None
    if q>0:
        proj_y=np.linalg.lstsq(current,yy,rcond=None)[0]
        proj_n=np.linalg.lstsq(current,nxt,rcond=None)[0]
        yr=yy-current@proj_y; nr=nxt-current@proj_n
        bh2=np.linalg.lstsq(yr,nr,rcond=None)[0].T
        fwl_error=float(np.max(np.abs(bh-bh2)))
    return dict(seed=seed,q=q,A_error=float(np.linalg.norm(ah-A)),B_error=float(np.linalg.norm(bh-B)),
                F_error=float(np.linalg.norm(ah+bh-F)),min_to_max_sv=float(sv[-1]/sv[0]),
                rank=int(np.linalg.matrix_rank(design)),fwl_max_error=fwl_error)

def normal_cdf(z): return .5*(1+math.erf(z/math.sqrt(2)))

def main():
    (OUT/'config.json').write_text(json.dumps(CONFIG,indent=2)+'\n')
    exact=dict(minimal=exact_check(20,1),substantive=exact_check(2000,101))
    assert exact['minimal']['max_path_error']==0
    assert exact['substantive']['max_path_error']==0
    assert exact['substantive']['design_rank']==2
    assert exact['substantive']['nll_range']<1e-8
    # Analytic covariance: rotational F with isotropic innovations gives v I.
    v=SIGMA**2/(1-CONFIG['radius']**2)
    exact['stationary_covariance_variance']=v
    exact['analytic_covariance_residual']=float(np.max(np.abs(v*np.eye(2)-(F@(v*np.eye(2))@F.T+SIGMA**2*np.eye(2)))))
    x0=np.array([1.,0.]); mu=F@x0; d=float(np.linalg.norm(mu))
    rng=np.random.default_rng(301)
    # Independent samples, not shared innovations, for actual classification test.
    obs_internal=mu+SIGMA*rng.normal(size=(CONFIG['clamp_trials'],2))
    obs_feedback=SIGMA*rng.normal(size=(CONFIG['clamp_trials'],2))
    direction=mu/d; boundary=d/2
    err_i=float(np.mean(obs_internal@direction<boundary))
    err_f=float(np.mean(obs_feedback@direction>=boundary))
    clamp=dict(internal_conditional_mean=mu.tolist(),feedback_conditional_mean=[0.,0.],
               mean_separation=d,noise_sd=SIGMA,
               mean_difference_se_per_component=SIGMA*np.sqrt(2/CONFIG['clamp_trials']),
               bayes_error_analytic=normal_cdf(-d/(2*SIGMA)),
               observed_classification_error=(err_i+err_f)/2,
               internal_sample_mean=obs_internal.mean(0).tolist(),
               feedback_sample_mean=obs_feedback.mean(0).tolist(),
               horizon_mean_separation={str(h):float(np.linalg.norm(np.linalg.matrix_power(F,h)@x0)) for h in [1,5,10,20]})
    exact['clamp']=clamp
    (OUT/'exact_checks.json').write_text(json.dumps(exact,indent=2)+'\n')
    records=[]; summary=[]
    for phase,key in [('exploration','exploratory_seeds'),('verification','verification_seeds')]:
        for q in CONFIG['excitation']:
            rows=[fit_one(seed,q) for seed in CONFIG[key]]
            for row in rows: records.append(dict(phase=phase,**row))
            summ=dict(phase=phase,q=q,n_seeds=len(rows))
            for metric in ['A_error','B_error','F_error','min_to_max_sv']:
                vals=np.array([r[metric] for r in rows])
                summ[metric+'_median']=float(np.median(vals))
                summ[metric+'_q10']=float(np.quantile(vals,.1))
                summ[metric+'_q90']=float(np.quantile(vals,.9))
            summ['all_rank4']=all(r['rank']==4 for r in rows)
            if q>0:
                summ['fwl_max_error']=max(r['fwl_max_error'] for r in rows)
                assert summ['fwl_max_error']<1e-8
            summary.append(summ)
    with (OUT/'per_seed.csv').open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(records[0])); w.writeheader(); w.writerows(records)
    (OUT/'summary.json').write_text(json.dumps(summary,indent=2)+'\n')
    print(json.dumps(dict(exact=exact,summary=summary),indent=2))
if __name__=='__main__': main()
