"""Independent counterfactual check of the strong slow-state challenge."""
from pathlib import Path
import sys,json
import numpy as np
R=Path(__file__).resolve().parents[2];sys.path.insert(0,str(R/'experiments'))
from analysis import load
from generators import generate
from state_models import counts_for_truth,calibrated_delta
ps=load('development',inputs_only=True);counts=[counts_for_truth(p) for p in ps];out=[]
for target in [-.2,.2]:
 a=.92;b=.9;delta,truth=calibrated_delta(target,a,b,np.ones(20),counts)
 effect=delta*b*np.mean(a**np.arange(5));checks=[]
 for p in [ps[0],ps[10]]:
  inds=[t for t in range(120,275) if p['c'][t]==0][::20][:3]
  for t in inds:
   curves=[]
   for c0 in [4.,-4.]:
    for j0 in [4. if p['set']=='A' else 8.,0.]:
     c=p['c'].copy();j=p['j'].copy();c[t-1]=c0;j[t-1]=0;c[t]=0;j[t]=j0
     rr=generate(c,j,kind='retention',effect=effect,retentions=(a,.5),gains=(b,.3),noise_sd=0,drift_scale=0)
     curves.append(rr['clean'][t+1:t+6])
   direct=(curves[0]-curves[1]-curves[2]+curves[3])/2
   expected=[];v=delta*b
   for h in range(1,6):
    expected.append(v);v*=a+delta*int(p['c'][t+h]==0 and p['j'][t+h]!=0)
   err=float(np.max(np.abs(direct-expected)));assert err<1e-12
   checks.append(dict(person=p['key'],trial=t+1,direct=direct.tolist(),analytic=expected,max_difference=err))
 out.append(dict(target=target,analytic_global_truth=truth,delta=delta,baseline_retention=a,event_retention=a+delta,checks=checks))
(R/'audits/adversarial_review/slow_truth_check.json').write_text(json.dumps(out,indent=2)+'\n')
print(json.dumps([{k:v for k,v in x.items() if k!='checks'} for x in out],indent=2))
