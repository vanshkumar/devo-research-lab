"""Frozen readout definitions for saved cumulative count ensembles."""
import numpy as np
from scipy.spatial.distance import cdist

METRICS=['mae','mixed','joint_NK','count','omission','literal_success','median_mae','mixed_U']


def crps(x,y):
    x=np.asarray(x,float);n=len(x);z=np.sort(x)
    half_pair=np.sum((2*np.arange(n)+1-n)*z)
    return float(np.mean(np.abs(x-y))-half_pair/n**2)


def mixed_score(n,k,on,ok):
    positive=n>0;v=k[positive]/n[positive];N=len(n);missing=int((~positive).sum())
    g=np.sqrt(v*v-v+1)
    if on>0:
        y=ok/on;first=(np.sum(np.abs(v-y))+missing*np.sqrt(y*y-y+1))/N
    else:first=float(g.sum()/N)
    z=np.sort(v);half_pair=float(np.sum((2*np.arange(len(z))+1-len(z))*z)+missing*g.sum())
    return first-half_pair/N**2,first-half_pair/(N*(N-1))


def metrics(sample,observed,horizon):
    n_particles=len(sample);mae=[];med=[];mixed=[];unbiased=[];joint=[];count=[]
    for j in (0,2):
        n,k=sample[:,j],sample[:,j+1];on,ok=observed[j:j+2];positive=n>0
        m,u=mixed_score(n,k,on,ok);mixed.append(m);unbiased.append(u)
        ratios=k[positive]/n[positive]
        # No0-imputation and no silent animal deletion when conditional accuracy is undefined.
        if on==0 or not positive.any():mae.append(np.nan);med.append(np.nan)
        else:mae.append(abs(ratios.mean()-ok/on));med.append(abs(np.median(ratios)-ok/on))
        x=np.column_stack([k,n-k,horizon-n])/horizon
        target=np.array([ok,on-ok,horizon-on])/horizon
        joint.append(np.linalg.norm(x-target,axis=1).mean()-.5*cdist(x,x).mean())
        count.append(crps(n/horizon,on/horizon))
    return np.array([np.mean(mae),np.mean(mixed),np.mean(joint),np.mean(count),
                     crps(sample[:,4]/horizon,observed[4]/horizon),
                     crps(sample[:,6]/horizon,observed[6]/horizon),np.mean(med),np.mean(unbiased)])


def calibration(sample,observed,horizon,rng):
    result=[]
    for j in (0,2):
        n,k=sample[:,j],sample[:,j+1];on,ok=observed[j:j+2];positive=n>0
        ratios=k[positive]/n[positive]
        row=dict(sign=-1 if j==0 else 1,positive_mass=float(positive.mean()),
                 expected_ratio=float(ratios.mean()) if len(ratios) else None,
                 median_ratio=float(np.median(ratios)) if len(ratios) else None,
                 count_pooled=float(k.sum()/n.sum()) if n.sum() else None,
                 observed_ratio=float(ok/on) if on else None,readouts={})
        for label,values,truth in [('N',n,on),('K',k,ok),('omissions',sample[:,4],observed[4]),
                                   ('literal_success',sample[:,6],observed[6])]:
            row['readouts'][label]=dict(mean=float(np.mean(values)),observed=int(truth),
                 interval80=np.quantile(values,[.1,.9]).tolist(),interval95=np.quantile(values,[.025,.975]).tolist(),
                 covered80=bool(np.quantile(values,.1)<=truth<=np.quantile(values,.9)),
                 covered95=bool(np.quantile(values,.025)<=truth<=np.quantile(values,.975)),
                 randomized_PIT=float(np.mean(values<truth)+rng.random()*np.mean(values==truth)))
        if on and len(ratios):
            truth=ok/on
            row['readouts']['conditional_ratio']=dict(mean=float(ratios.mean()),observed=float(truth),
                 interval80=np.quantile(ratios,[.1,.9]).tolist(),interval95=np.quantile(ratios,[.025,.975]).tolist(),
                 covered80=bool(np.quantile(ratios,.1)<=truth<=np.quantile(ratios,.9)),
                 covered95=bool(np.quantile(ratios,.025)<=truth<=np.quantile(ratios,.975)),
                 randomized_PIT=float(np.mean(ratios<truth)+rng.random()*np.mean(ratios==truth)))
        result.append(row)
    return result
