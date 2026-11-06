"""Validate structural contrast analytically and by full-history interventions."""
from pathlib import Path
import sys,json
import numpy as np
R=Path(__file__).resolve().parents[2];sys.path.insert(0,str(R/'experiments'))
from analysis import load
from generators import generate
rows=[]
for p in [load('validation',inputs_only=True)[0],load('validation',inputs_only=True)[10]]:
 ix=[t for t in range(120,275) if p['c'][t]==0][::10][:5]
 for t in ix:
  for effect in [-.2,.2]:
   for kind in ['retention','expression_next','rebound']:
    values=[]
    for cc in [4.,-4.]:
     for jj in [4. if p['set']=='A' else 8.,0.]:
      c=p['c'].copy();j=p['j'].copy();c[t-1]=cc;j[t-1]=0;c[t]=0;j[t]=jj
      g=generate(c,j,kind=kind,effect=effect,noise_sd=0,drift_scale=0,process_sd=0)
      values.append(g['clean'][t+1:t+6])
    actual=(values[0]-values[1]-values[2]+values[3])/2
    a=.65;b=.65;delta=effect/(b*np.mean(a**np.arange(5)))
    if kind=='retention':
     v=delta*b;expected=[]
     for h in range(1,6):
      expected.append(v);v*=a+delta*float(p['c'][t+h]==0 and p['j'][t+h]!=0)
    elif kind=='expression_next':expected=[delta*b,0,0,0,0]
    else:expected=[delta*b,-delta*b,0,0,0]
    err=float(np.max(np.abs(actual-expected)));assert err<1e-12
    rows.append(dict(person=p['key'],index_trial=t+1,effect=effect,kind=kind,
                     counterfactual_curve=actual.tolist(),analytic_curve=expected,max_difference=err))
out=dict(scope='Inputs only; full chronological four-way interventions on preceding clamp and index event.',checks=len(rows),max_difference=max(r['max_difference'] for r in rows),rows=rows)
(R/'audits/recovery_design/physical_truth_check.json').write_text(json.dumps(out,indent=2)+'\n')
print(json.dumps({k:v for k,v in out.items() if k!='rows'}))
