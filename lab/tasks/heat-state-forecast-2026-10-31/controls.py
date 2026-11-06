"""Finite source/held-animal known-answer controls, 12 fit + 7 held per draw.

Control data are synthetic latent outcomes. This tests an estimator under an
explicit generator, not the biological availability or absence of a slow state.
"""
import os
os.environ['OPENBLAS_NUM_THREADS']='1'
os.environ['OMP_NUM_THREADS']='1'
import json
import numpy as np
import forecast as f
def make(rng,gain):
    n,c=19,4
    X=rng.normal(size=(n,c,5));G=rng.normal(size=(n,2));latent=rng.normal(size=(n,2))
    loading=np.array([[1.,0.,.7,.2],[0.,1.,.2,.7]])
    R=np.einsum('ij,jk->ik',latent,loading)
    # One source-fixed shared global feature, orthogonal in the generator to own
    # features. Per-worm noise is shared over bins/channels; no frame replication.
    shared=rng.normal(size=(n,1,1))
    coef=np.array([1.,-.8,.6,-1.2])
    Y=.4*X[:,:,0,None]+gain*G[:,0,None,None]*coef[None,:,None]+shared
    Y=np.repeat(Y,7,axis=2)
    return dict(X=X,G=G,R=R,Y=Y,mode='synthetic',uids=[str(i) for i in range(n)])
def selected(b,model):
    choices=[]
    for alpha in f.ALPHAS:
        p=f.cv_predict(b,model,alpha)
        score=float(np.mean(f.losses(p,b['Y'],np.ones(4))))
        choices.append((score,alpha))
    return min(choices)[1]
def main():
    results={};rng=np.random.default_rng(20261031)
    for gain in [0.,2.]:
        rows=[]
        for i in range(100):
            b=make(rng,gain);tr=f.subset(b,np.arange(12));te=f.subset(b,np.arange(12,19))
            al=selected(tr,'local');ast=selected(tr,'state')
            lp=f.predict(tr,te,'local',al);sp=f.predict(tr,te,'state',ast)
            le=f.losses(lp,te['Y'],np.ones(4));se=f.losses(sp,te['Y'],np.ones(4))
            ix=rng.integers(0,7,(2000,7));dif=(le-se)[ix].mean(axis=1)
            lo,hi=np.quantile(dif,[.025,.975]);frac=1-se.mean()/le.mean()
            rows.append(dict(seed_index=i,local_alpha=al,state_alpha=ast,local_mse=float(le.mean()),state_mse=float(se.mean()),gain=float(frac),paired_difference_ci=[float(lo),float(hi)],passes_declared_investment_rule=bool(frac>=.1 and lo>0)))
        results[str(gain)]=dict(generator_gain=gain,trials=len(rows),mean_fraction_gain=float(np.mean([r['gain'] for r in rows])),median_fraction_gain=float(np.median([r['gain'] for r in rows])),positive_gain_trials=sum(r['gain']>0 for r in rows),passes_declared_rule=sum(r['passes_declared_investment_rule'] for r in rows),rows=rows)
        print(json.dumps({k:v for k,v in results[str(gain)].items() if k!='rows'}),flush=True)
    f.save('KNOWN_ANSWER_CONTROLS.json',dict(at_utc=f.now(),source_animals=12,held_animals=7,units='independent synthetic animals; within-animal noise shared over outcomes',generator='linear own-channel signal + independent global signal + common per-worm Gaussian noise; fixed held-out weights; alpha selected on source only',seed=20261031,results=results,limitation='Generator-specific finite control; not power for the actual worm data or proof of equivalence.'))
if __name__=='__main__':main()
