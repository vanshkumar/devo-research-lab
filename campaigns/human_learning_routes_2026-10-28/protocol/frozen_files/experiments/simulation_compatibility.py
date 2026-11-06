"""Generator-conditioned inversion of fixed score/effect summaries.

Prespecified before validation: not a posterior probability, universal bound,
or evidence that a generator is a true psychological mechanism.
"""
from pathlib import Path
import json
import numpy as np
import pandas as pd
from analysis import ROOT,write_json

def distance(x,reference):
    delta=x-reference.mean(axis=0);cov=np.cov(reference,rowvar=False)
    return float(np.einsum('i,ij,j->',delta,np.linalg.pinv(cov),delta))

def main():
    summary=json.loads((ROOT/'outputs/primary/summary.json').read_text())
    observed=np.array([summary['delta_log']['mean'],summary['standardized_adaptation_effect']['mean']])
    sim=pd.read_csv(ROOT/'outputs/recovery/final/replicates.csv')
    rows=[]
    for scenario,d in sim.groupby('scenario'):
        a=d[['delta_log','effect']].to_numpy();n=len(a)
        assert n>=100,'Final recovery must complete before inversion'
        obs_distance=distance(observed,a)
        loo=np.array([distance(a[i],np.delete(a,i,axis=0)) for i in range(n)])
        p=(1+np.sum(loo>=obs_distance))/(n+1)
        rows.append(dict(scenario=scenario,n=n,mean_true_effect=float(d.truth_effect.mean()),observed_score=observed[0],observed_effect=observed[1],observed_mahalanobis=obs_distance,empirical_tail_fraction=float(p),retained_at_05=bool(p>=.05),score_percentile=float(np.mean(a[:,0]<=observed[0])),effect_percentile=float(np.mean(a[:,1]<=observed[1]))))
    out=ROOT/'outputs/simulation_compatibility';out.mkdir(exist_ok=True)
    pd.DataFrame(rows).to_csv(out/'discrete_accounts.csv',index=False)
    write_json(out/'interpretation.json',dict(statistics=['equal-participant validation delta log score','zero-current-contrast standardized adaptation-only mean'],method='Mahalanobis distance against each scenario; tail fraction calibrated with leave-one-simulation-out distances, plus-one finite Monte Carlo correction.',threshold=.05,scope='Discrete tested synthetic populations and actual stimulus schedules. No claim that retained accounts are true, no posterior probabilities, no interpolation into a universal confidence interval. Real population may fall outside all tested generator families.'))
    print(pd.DataFrame(rows).to_string(index=False))

if __name__=='__main__':main()
