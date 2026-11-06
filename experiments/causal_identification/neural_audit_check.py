"""Bounded exploratory check on FIRST discovery worm only; no validation access."""
import importlib.util, csv, pathlib
import numpy as np
from scipy import linalg
HERE=pathlib.Path(__file__).resolve().parent
p=HERE.parent/'neural_dynamics'/'run.py'
spec=importlib.util.spec_from_file_location('target',p);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
uid,x,dt,d=next(m.records('discovery'))
n=len(x);c1=int(.6*n);c2=int(.75*n);gap=int(np.ceil(30/dt));x,_=m.standardize(x,np.arange(c1))
rows=[]
for sec in [.6,3,12,30]:
 h=max(1,round(sec/dt));tr=np.arange(c1-h-gap);va=np.arange(c1+gap,c2-h-gap);te=np.arange(c2+gap,n-h)
 X=x[tr];D=x[tr+h]-X;xm=X.mean(0);dm=D.mean(0);A=X-xm;B=D-dm
 g=m.mm(A.T,A);q=m.mm(A.T,B)
 for method in ['anchored_population','anchored_diagonal']:
  candidates=[]
  for lam in [.01,.1,1,10,100,1000,1e6]:
   if method=='anchored_population': coef=linalg.solve(g+np.eye(g.shape[0])*len(tr)*lam,q,assume_a='pos')
   else: coef=np.diag(np.diag(q)/(np.diag(g)+len(tr)*lam))
   pv=x[va]+m.mm(x[va]-xm,coef)+dm
   candidates.append((m.mse(x[va+h],pv),lam,coef))
  val,lam,coef=min(candidates,key=lambda z:z[0]);pt=x[te]+m.mm(x[te]-xm,coef)+dm
  rows.append(dict(uid=uid,seconds=sec,method=method,lambda_=lam,validation_mse=val,test_mse=m.mse(x[te+h],pt)))
with (HERE/'neural_audit_check.csv').open('w') as f:
 w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
print(rows)
