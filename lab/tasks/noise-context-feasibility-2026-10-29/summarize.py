from pathlib import Path
import json,numpy as np
P=Path(__file__).resolve().parent
M=json.loads((P/'scored_metrics.json').read_text())
M=[m for m in M if not m['permuted']]
rng=np.random.default_rng(77201);ix=rng.integers(0,20,(10000,20))
def ci(v):
 v=np.array(v);return [float(x) for x in np.percentile(v[ix].mean(1),(2.5,97.5))]
def val(f,c,r,k):return [m[k] for m in M if m['family']==f and m['curriculum']==c and m['role']==r]
rows=[]
for f in ('original','relocated','deterministic'):
 for c in ('blocked','interleaved','early','middle','late'):
  row={'family':f,'curriculum':c,'roles':{}}
  for r in ('no_oracle','oracle','learned'):
   a=[m for m in M if m['family']==f and m['curriculum']==c and m['role']==r]
   row['roles'][r]={k:float(np.mean([m[k] for m in a])) for k in a[0] if k not in ('role','seed','family','curriculum','permuted') and a[0][k] is not None}
   row['roles'][r]['test_signal_probability_ci']=ci([m['test_signal_probability'] for m in a])
  gain=np.array(val(f,c,'learned','test_signal_probability'))-np.array(val(f,c,'no_oracle','test_signal_probability'))
  oracle=np.array(val(f,c,'learned','test_signal_probability'))-np.array(val(f,c,'oracle','test_signal_probability'))
  row['learned_gain']=float(gain.mean());row['learned_gain_ci']=ci(gain)
  row['learned_minus_oracle']=float(oracle.mean());row['learned_minus_oracle_ci']=ci(oracle)
  rows.append(row)
def row(f,c):return next(r for r in rows if r['family']==f and r['curriculum']==c)
a=row('original','blocked');b=row('relocated','blocked');d=row('deterministic','blocked')
checks=json.loads((P/'scored_permutation_checks.json').read_text())
scientific={
 'original_blocked_gain_ge_10pp':a['learned_gain']>=.10,
 'original_signal_weight_ge_75pct':a['roles']['learned']['signal_w_last40']>=.75,
 'original_noise_weight_le_25pct':a['roles']['learned']['noise_w_last40']<=.25,
 'relocated_blocked_drop_le_5pp':b['roles']['learned']['test_signal_probability']>=a['roles']['learned']['test_signal_probability']-.05,
 'relocated_noise_weight_le_25pct':b['roles']['learned']['noise_w_last40']<=.25,
 'deterministic_context_signal_weight_ge_75pct':d['roles']['learned']['signal_w_last40']>=.75,
 'permutation_equal':all(m['permutation_probability_max_error']<=1e-13 and m['permutation_weight_max_error']<=1e-13 and m['assignments_equal'] for m in checks),
}
contrast={}
for f in ('original','relocated','deterministic'):
 g=np.array(val(f,'early','learned','test_signal_probability'))-np.array(val(f,'late','learned','test_signal_probability'))
 contrast[f]={'early_minus_late':float(g.mean()),'ci':ci(g)}
result={'summary':rows,'scientific_controls':scientific,'all_scientific_controls_pass':all(scientific.values()),'mixed_contrasts':contrast,'bootstrap_note':'20 paired invented seeds, 10000 resamples, seed77201; generator Monte Carlo uncertainty only.'}
(P/'summary.json').write_text(json.dumps(result,indent=2)+'\n')
print('scientific_controls',json.dumps(scientific));print('mixed_contrasts',json.dumps(contrast))
for r in rows:
 print(r['family'],r['curriculum'],'P',','.join(f'{x}:{r["roles"][x]["test_signal_probability"]:.4f}' for x in ('no_oracle','oracle','learned')),'gain',r['learned_gain'],'CI',r['learned_gain_ci'],'w_sig_noise',r['roles']['learned']['signal_w_last40'],r['roles']['learned'].get('noise_w_last40'),'purity',r['roles']['learned']['test_context_purity'])
