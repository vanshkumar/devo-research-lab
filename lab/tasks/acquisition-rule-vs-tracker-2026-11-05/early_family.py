"""Feasibility of simultaneous useful-benefit bounds, with paired animal resampling."""
import time
import numpy as np
from pilot import HERE,IO,get,save,utc

def main():
    began=time.monotonic();sc=get(HERE/'EARLY_SCORES.json');ids=list(sc['per_animal']);n=len(ids)
    raw=[];base=[]
    for cutoff in ('200','1000'):
        raw.append(np.array([sc['per_animal'][s][cutoff]['recent_growth']['2000']['equal_side_mae']-
                             sc['per_animal'][s][cutoff]['gru']['2000']['equal_side_mae'] for s in ids]))
        base.append(np.ones(n))
    for cutoff in ('200','1000'):
        b=np.array([sc['per_animal'][s][cutoff]['recent_growth']['2000']['mixed_ratio_score'] for s in ids])
        g=np.array([sc['per_animal'][s][cutoff]['gru']['2000']['mixed_ratio_score'] for s in ids])
        raw.append(b-g);base.append(b)
    raw=np.stack(raw,axis=1);base=np.stack(base,axis=1)
    estimate=raw.mean(0)/base.mean(0)
    influence=(raw-base*estimate)/base.mean(0);se=influence.std(0,ddof=1)/np.sqrt(n)
    rng=np.random.default_rng(202611055);draws=rng.integers(0,n,(12000,n))
    boot=raw[draws].mean(1)/base[draws].mean(1);z=(boot-estimate)/se
    c=float(np.quantile(np.max(-z,axis=1),.95));c_two=float(np.quantile(np.max(abs(z),axis=1),.95))
    accuracy_c=float(np.quantile(np.max(-z[:,:2],axis=1),.95))
    out=dict(utc=utc(),labels=['accuracy_gain200','accuracy_gain1000','relative_mixed_score_gain200','relative_mixed_score_gain1000'],
       estimate=estimate.tolist(),influence_se=se.tolist(),replicates=12000,
       simultaneous_one_sided95_critical=c,simultaneous_upper95=(estimate+c*se).tolist(),
       simultaneous_two_sided95_critical=c_two,simultaneous_two_sided95=np.stack([estimate-c_two*se,estimate+c_two*se],axis=1).tolist(),
       accuracy_only_upper95=(estimate[:2]+accuracy_c*se[:2]).tolist(),
       limitation='Postvalidation precision check; paired independent-mouse working resampling of same fixed/source-site mixture. Source bank/recency selection, neural fit and teacher uncertainty remain outside. No main gate or claim repaired.',
       seconds=time.monotonic()-began,io=dict(IO))
    save('EARLY_FAMILY_PRECISION.json',out);print(out,flush=True)

if __name__=='__main__':main()
