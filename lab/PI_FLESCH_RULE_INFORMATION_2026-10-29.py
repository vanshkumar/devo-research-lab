"""Source-input-only information diagnostic, not a fitted scientific forecaster."""
from pathlib import Path
import json, numpy as np
root=Path(__file__).resolve().parents[1]
p=root/'lab/tasks/flesch-source-calibration-2026-10-29'
m=json.loads((p/'MASKS.json').read_text())
with np.load(root/'sources/flesch_source_calibration_2026-10-29/inputs_only.npz') as archive:
 d={k:archive[k] for k in ('expt_contextIDX','expt_branchIDX','expt_leafIDX','expt_rewardIDX')}
# These eight linear hypotheses are declared from the task's two-dimensional
# feature design; no true rule, response, target value or curriculum label enters
# their prior. Counterfactual reward is revealed only after the present input.
h=np.array([[1,0],[-1,0],[0,1],[0,-1],[.5,.5],[.5,-.5],[-.5,.5],[-.5,-.5]])
result={}
for group in ('B200','Interleaved'):
 rows=[]
 for col in m['groups'][group]:
  for ctx in (1,2):
   remaining=np.ones(8,dtype=bool);first_unique=None;ent=[];n=0
   for t in range(400):
    if int(d['expt_contextIDX'][t,col])!=ctx:continue
    x=np.array([d['expt_branchIDX'][t,col]-3,d['expt_leafIDX'][t,col]-3])
    r=d['expt_rewardIDX'][t,col]/25.
    n+=1;remaining &= np.isclose(h@x,r,atol=1e-12,rtol=0)
    assert remaining.any(),(group,col,ctx,t,x,r)
    ent.append(float(np.log2(remaining.sum())))
    if remaining.sum()==1 and first_unique is None:first_unique=n
   rows.append({'column':col,'context':ctx,'first_unique_after_feedback':first_unique,'entropy_first10':ent[:10]})
 vals=np.array([r['first_unique_after_feedback'] for r in rows])
 result[group]={'context_histories':len(rows),'first_unique_min_median_p95_max':[float(x) for x in np.quantile(vals,[0,.5,.95,1])],'unique_within_5':float(np.mean(vals<=5)),'rows':rows}
report={'kind':'declared_noiseless_task_information_diagnostic_not_fitted_model_or_biological_claim','hypotheses':h.tolist(),'source_input_columns':m['source_columns'],'source_response_values_read':0,'target_response_values_read':0,'target_input_columns_used':False,'assumptions':['linear noiseless reward hypotheses and known2Dfeaturecoordinates are an analyst-declared inductive bias','eight equal-prior hypotheses per context; feedback visible aftertrial','knowncurrentcontext assignment for this information diagnostic; not an account of context-confused humanlearning'],'groups':result}
out=root/'lab/PI_FLESCH_RULE_INFORMATION_2026-10-29.json';out.write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({g:{k:v for k,v in z.items() if k!='rows'} for g,z in result.items()},indent=2))
