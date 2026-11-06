"""Best-case interoceptive decoder under a noisy attention/update gate; see PLAN."""
import pathlib,json,csv,math
import numpy as np
from scipy.linalg import lstsq
H=pathlib.Path(__file__).parent

def simulate(seed,n,pi,rho,fp):
 rng=np.random.default_rng(seed);selfmode=rng.random(n)<pi;o=rng.normal(size=n);own=np.where(selfmode,o,rho*o+np.sqrt(1-rho*rho)*rng.normal(size=n))
 latent=np.c_[o,rng.normal(size=(n,3))];rot,_=np.linalg.qr(rng.normal(size=(4,4)));z=np.einsum('ni,ij->nj',latent,rot,optimize=False);target=own+.1*rng.normal(size=n)
 gate=rng.random(n)<np.where(selfmode,.9,fp);coef=lstsq(z[gate],target[gate])[0]
 # Query imagined other states in the same representational code: target is o, not own physiology.
 truth=np.einsum('ij,j->i',rot.T,np.array([1.,0,0,0]),optimize=False)
 err=float(np.sum((coef-truth)**2));gain=float(np.sum(coef*truth));pred=(pi*.9+(1-pi)*fp*rho)/(pi*.9+(1-pi)*fp)
 return dict(seed=seed,n=n,self_fraction=pi,label_rho=rho,false_update_rate=fp,n_accepted=int(gate.sum()),decoder_gain=gain,ideal_gain=pred,query_mse=err,population_query_mse=(pred-1)**2)

def main():
 rows=[simulate(s,n,pi,rho,fp) for s in range(20) for n in [200,2000] for pi in [.05,.2,.5] for rho in [-.5,0,.8] for fp in [0,.01,.05,.2,1]]
 with (H/'per_seed.csv').open('w') as f:w=csv.DictWriter(f,fieldnames=rows[0]);w.writeheader();w.writerows(rows)
 checks=[simulate(20261028,200000,.2,0,fp) for fp in [0,.05,1]]
 assert checks[0]['query_mse']<.001
 assert max(abs(r['decoder_gain']-r['ideal_gain']) for r in checks)<.02
 summaries=[]
 for n in [200,2000]:
  for pi in [.05,.2,.5]:
   for rho in [-.5,0,.8]:
    for fp in [0,.01,.05,.2,1]:
     q=[r for r in rows if (r['n'],r['self_fraction'],r['label_rho'],r['false_update_rate'])==(n,pi,rho,fp)];summaries.append(dict(n=n,self_fraction=pi,label_rho=rho,false_update_rate=fp,median_query_mse=float(np.median([r['query_mse'] for r in q])),mean_gain=float(np.mean([r['decoder_gain'] for r in q])),ideal_gain=q[0]['ideal_gain']))
 (H/'summary.json').write_text(json.dumps(dict(conditions=summaries,positive_controls=checks,seeds=list(range(20)),interpretation='synthetic gate-contamination regime, not empirical human evidence'),indent=2)+'\n')
 print('rows',len(rows),'positive control query MSE',checks[0]['query_mse'],'max gain error',max(abs(r['decoder_gain']-r['ideal_gain']) for r in checks))
 for r in summaries:
  if r['n']==2000 and r['self_fraction']==.05 and r['label_rho']==0:print(r)
if __name__=='__main__':main()
