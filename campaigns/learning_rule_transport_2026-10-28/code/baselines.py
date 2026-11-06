"""Matched competence persistence and empirical exposure/growth baselines.

Fitting uses development animals only. A test animal supplies exactly its
prefix. Growth borrows a development donor's future *exposure-indexed* GLM
change, never the test animal's intervening choices/rewards. Shared omission
forecasts borrow engagement changes from the same frozen development bank.
"""
import json
from pathlib import Path
import numpy as np
from scipy.optimize import minimize
from scipy.special import expit, logit
from learning_models import features, subject_arrays


def subset(data, start=0, end=None):
    n=len(data['choice'])
    return {k:v[start:end] for k,v in data.items() if isinstance(v,np.ndarray) and v.ndim>0 and len(v)==n}


def fit_competence(data, ridge=1.):
    s,c,_,_=subject_arrays(data);ok=c!=0
    X=features(s[ok]);y=(c[ok]<0).astype(float)
    def obj(w):
        z=np.einsum('ij,j->i',X,w)
        p=expit(z)
        return np.sum(np.logaddexp(0,z)-y*z)+ridge*np.sum(w*w)/2,np.einsum('ij,i->j',X,p-y)+ridge*w
    w=minimize(obj,np.zeros(3),jac=True,method='L-BFGS-B',bounds=[(-8,12),(-8,12),(-6,6)]).x
    pp=expit(np.einsum('ij,j->i',X,w))
    precision=np.einsum('ni,n,nj->ij',X,pp*(1-pp),X)+ridge*np.eye(3)
    cov=np.linalg.inv(precision)
    omit=(np.sum(c==0)+.5)/(len(c)+1)
    return w,cov,omit


def fit_bank(animals, out, prefix=1000, bin_size=500, horizon=5000):
    ids=[];pweights=[];trajectories=[];omissions=[];valid=[]
    nb=horizon//bin_size
    for subject,data in sorted(animals.items()):
        if len(data['choice'])<prefix:continue
        w,_,o=fit_competence(subset(data,prefix-bin_size,prefix))
        ww=[];oo=[];vv=[]
        for b in range(nb):
            lo=prefix+b*bin_size;hi=lo+bin_size
            available=hi<=len(data['choice'])
            if available:
                wb,_,ob=fit_competence(subset(data,lo,hi))
            else:wb=w;ob=o
            ww.append(wb-w);oo.append(logit(np.clip(ob,1e-5,1-1e-5))-logit(o));vv.append(available)
        ids.append(subject);pweights.append(np.r_[w,logit(o)]);trajectories.append(ww);omissions.append(oo);valid.append(vv)
    np.savez_compressed(out,subjects=np.array(ids),prefix=np.array(pweights),delta_w=np.array(trajectories),
                        delta_omit=np.array(omissions),valid=np.array(valid),prefix_n=np.array(prefix),
                        bin_size=np.array(bin_size),horizon=np.array(horizon))
    return load_bank(out)


def load_bank(path):
    with np.load(path,allow_pickle=False) as z:return {k:z[k] for k in z.files}


def draw_initial(prefix, bank, n_particles, seed, exclude=None, neighbors=15,
                 competence='growth', calibration_window=500):
    rng=np.random.default_rng(seed)
    d=subset(prefix,max(0,len(prefix['choice'])-calibration_window))
    w,cov,o=fit_competence(d)
    current=np.r_[w,logit(o)]
    # Fixed-scale distance stops the weakly identified sensory/bias direction
    # and rare omissions from overwhelming competence matching.
    scale=np.array([1.5,1.5,1.5,2.])
    dist=np.sum(((bank['prefix']-current)/scale)**2,axis=1)
    if exclude is not None:dist[bank['subjects']==exclude]=np.inf
    order=np.argsort(dist);order=order[np.isfinite(dist[order])]
    selected=order[:min(neighbors,len(order))]
    if not len(selected):raise ValueError('No independent development donors')
    donor=rng.choice(selected,n_particles)
    wb=rng.multivariate_normal(w,cov,size=n_particles)
    # Exact beta calibration for an observed omission rate; half-count prior.
    c=d['choice'];ob=rng.beta(np.sum(c==0)+.5,np.sum(c!=0)+.5,size=n_particles)
    # Missing donor futures are replaced independently at each horizon from
    # available equally close donors. No target animal selection on outcomes.
    dw=np.empty((n_particles,bank['delta_w'].shape[1],3));do=np.empty(dw.shape[:2])
    for b in range(dw.shape[1]):
        eligible=order[bank['valid'][order,b]][:neighbors]
        if len(eligible)==0:raise ValueError('No development exposure for bin')
        db=donor.copy();missing=~bank['valid'][db,b]
        db[missing]=rng.choice(eligible,np.sum(missing))
        dw[:,b]=bank['delta_w'][db,b]
        do[:,b]=bank['delta_omit'][db,b]
    if competence=='persistence':dw[:]=0
    return dict(w=wb,anchor=wb.copy(),delta_w=dw,delta_omit=do,
                omit_logit=logit(np.clip(ob,1e-6,1-1e-6)),bin_size=int(bank['bin_size']),
                donors=bank['subjects'][donor],current_fit=w,cov=cov)


def competence_at(state, trial):
    b=min(trial//state['bin_size'],state['delta_w'].shape[1]-1)
    return state['anchor']+state['delta_w'][:,b]


def omission_at(state, trial, mode='growth'):
    b=min(trial//state['bin_size'],state['delta_omit'].shape[1]-1)
    delta=state['delta_omit'][:,b] if mode=='growth' else 0
    return expit(state['omit_logit']+delta)


class EvidenceFilter:
    """Conditional diagnostic: a response-likelihood tracker, not a reward law.

    Its expected update under its own generated choices is zero. This is the
    control distinguishing useful behavioral observation from learning.
    """
    def __init__(self,rate=.02):self.rate=rate;self.kind='evidence_filter'
    def probs(self,state,s):return expit(np.sum(state['w']*features(s),axis=-1))
    def update(self,state,s,choice,feedback=None,session_start=False):
        c=np.asarray(choice);p=self.probs(state,s)
        state['w']=state['w']+self.rate*((c<0)-p)[...,None]*features(s)*(c!=0)[...,None]
        return state
