#!/usr/bin/env python3
"""Outcome-informed model diagnostic and direct count controls; see IMPLEMENTATION.md."""
import json
import numpy as np
import pandas as pd
from scipy import stats
from run import load,prepare_model,model_cv,OUT,SEED
x,o,f,ji=load();t,folds=prepare_model(o);rng=np.random.default_rng(SEED+30)
M=t.M.values;B=t.B.values
q=np.empty(len(t));co=o[o.pool.eq('non_neuronal')]
for (donor,gene),ix in t.groupby(['donor_id','minor_gene']).groups.items():
    c=co[co.donor_id.eq(donor)];q[list(ix)]=(c[gene].sum()+.5)/(c.B.sum()+1)
rows=[]
for name,w,beta,k in [('null_k10',0,.1,10),('mixed30_ratio25_k10',.3,.25,10),('mixed50_ratio50_k10',.5,.5,10),('mixed100_ratio25_k10',1.,.25,10)]:
    for rep in range(10):
        z=rng.random(len(t))<w;mu=q*B+np.where(z,beta,.001)*M;p=k/(k+mu);F=stats.nbinom.cdf(M,k,p)
        y=stats.nbinom.ppf(rng.random(len(t))*F,k,p).astype(int)
        r,_=model_cv(t,folds,y=y,truncated=True)
        for _,a in r.iterrows():rows.append(dict(scenario=name,replicate=rep,**a.to_dict()))
    print(name,'done',flush=True)
pd.DataFrame(rows).to_csv(OUT/'model_moderate_noise_diagnostics.csv',index=False)
# Untruncated addition to the observed minor count; denominator includes all cells in five useful donors.
t=o[o.pool.eq('candidate')].copy();t=t[t.donor_id.map(t.donor_id.value_counts())>=20].reset_index(drop=True);M=t.M.values
rows=[]
for frac in [.1,.25,.5]:
    for rep in range(200):
        y=t.m.values+rng.poisson(frac*M);m=np.minimum(M,y);MM=np.maximum(M,y);hit=(m>=10)&(m/np.maximum(MM,1)>=.1)
        for donor,g in t.groupby('donor_id'):
            ix=g.index.values;rows.append(dict(injected_ratio=frac,replicate=rep,donor=donor,n=len(ix),detected=int(hit[ix].sum()),fraction=float(hit[ix].mean())))
pd.DataFrame(rows).to_csv(OUT/'direct_injection_recovery.csv',index=False)
# Pure dominant programs plus 1 or 2 stray transcripts on average. This is a constructed null,
# calibrated to observed count scale, not an estimate of actual ambient rates.
rows=[]
for lam in [.5,1.,2.,5.]:
    for rep in range(500):
        y=rng.poisson(lam,size=len(t));m=np.minimum(M,y);MM=np.maximum(M,y);hit=(m>=10)&(m/np.maximum(MM,1)>=.1);joint=(M>0)&(y>0)
        for donor,g in t.groupby('donor_id'):
            ix=g.index.values;rows.append(dict(mean_spurious_counts=lam,replicate=rep,donor=donor,n=len(ix),joint_fraction=float(joint[ix].mean()),primary_fraction=float(hit[ix].mean()),minor10_fraction=float((m[ix]>=10).mean())))
pd.DataFrame(rows).to_csv(OUT/'trace_null_controls.csv',index=False)
print('direct controls done',flush=True)
