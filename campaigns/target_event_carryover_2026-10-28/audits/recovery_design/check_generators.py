"""Input-only validation of independently coded challenge generators."""
from pathlib import Path
import csv,sys,json
import numpy as np
R=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(R/'experiments'))
from generators import generate, impulse_check, KINDS
S=R.parents[1]/'sources/learning_intervention_feasibility_2026-10-28'
result={'scope':'All empirical outcomes discarded at ingestion; only c/j/SN/TN used.', 'impulses':{},'schedules':[]}
for effect in [-0.2,0.2]:
 result['impulses'][str(effect)]={k:impulse_check(k,effect=effect) for k in KINDS}
 for f in ['tsay_TE_SPE.csv','tsay_controljump.csv']:
  people={}
  with (S/f).open() as h:
   for r in csv.DictReader(h):
    p=r['SN']; people.setdefault(p,[]).append((int(r['TN']),float(r['clamp_size']),float(r['tgt_jump_size'])))
  for person,rows in sorted(people.items(),key=lambda v:int(v[0])):
   rows.sort();c=np.array([x[1] for x in rows]);j=np.array([x[2] for x in rows])
   opts=dict(seed=271828+int(person),effect=effect,omission_rate=0.03,process_sd=0.08)
   r=generate(c,j,kind='retention',**opts)
   p=generate(c,j,kind='perceived_error',**opts)
   e=generate(c,j,kind='expression_storage_equivalent',**opts)
   errp=float(np.nanmax(np.abs(r['y']-p['y'])))
   erre=float(np.nanmax(np.abs(r['y']-e['y'])))
   assert errp<1e-11 and erre<1e-11
   assert np.all(np.isfinite(r['clean']))
   assert 0<sum(~r['observed_mask'])<100
   result['schedules'].append(dict(file=f,person=person,effect=effect,rows=len(c),
    perceived_error_max_discrepancy=errp,expression_equivalence_max_discrepancy=erre,
    min_log_transition=r['truth']['mean_log_fast_transition'],
    peak_abs_state=float(np.max(np.abs(r['state']))),omissions=int(sum(~r['observed_mask']))))
result['max_perceived_error_discrepancy']=max(x['perceived_error_max_discrepancy'] for x in result['schedules'])
result['max_expression_equivalence_discrepancy']=max(x['expression_equivalence_max_discrepancy'] for x in result['schedules'])
(R/'audits/recovery_design/generator_check.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({k:v for k,v in result.items() if k!='schedules'},indent=2))
