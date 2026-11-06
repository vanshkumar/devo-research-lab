"""Save source-only descriptive and final Monte Carlo scoring checks."""
from pathlib import Path
import numpy as np,json
HERE=Path(__file__).resolve().parent;REPO=HERE.parents[2];SRC=REPO/'sources/flesch_source_calibration_2026-10-29';TASK=REPO/'lab/tasks/flesch-source-calibration-2026-10-29'
m=json.loads((TASK/'MASKS.json').read_text());x=np.load(SRC/'inputs_only.npz');r=np.load(SRC/'source_responses.npz')
a=r['resp_category'];rt=r['resp_reactiontime'];cats=x['expt_catIDX'][:,:95];truth=cats>=0
ok=(a==truth)&np.isfinite(a)&(rt<=5)
out={'scope':'Consumed source development; no causal or initial-knowledge identification','B200_early_nonboundary':{}}
for scope,cols in [('fit',m['split']['B200']['fit']),('check',m['split']['B200']['check']),('all',m['groups']['B200'])]:
 out['B200_early_nonboundary'][scope]={}
 for begin in [0,200]:
  stats={}
  for n in [1,2,5,10,20,40]:
   vals=[];positive=[]
   for c in cols:
    ix=np.arange(begin,begin+200);ix=ix[cats[ix,c]!=0][:n]
    vals.append(ok[ix,c].mean());positive.extend(truth[ix,c])
   stats[str(n)]={'mean_accuracy':float(np.mean(vals)),'positive_truth_fraction':float(np.mean(positive))}
  out['B200_early_nonboundary'][scope][str(begin)]=stats
saved=np.load(SRC/'source_stability_256draws.npz');stability=json.loads((TASK/'SOURCE_STABILITY.json').read_text())
columns=saved['columns'];obs=saved['observed'];out['final_256_scoring']={};energy_rows={}
for name in ['sgd_oja','context_value','exposure_growth']:
 sims=saved[name];out['final_256_scoring'][name]={};n=sims.shape[1];perm=np.random.default_rng(74301).permutation(n//2)
 es=np.array([np.sqrt(((s-y)**2).sum(1)).mean()-.5*np.sqrt(((s[:n//2]-s[n//2:][perm])**2).sum(1)).mean() for s,y in zip(sims,obs)])
 energy_rows[name]=es
 for group in ['B200','Interleaved']:
  ix=[j for j,c in enumerate(columns) if c in m['groups'][group]]
  delta=sims[ix].mean((0,1))-obs[ix].mean(0);mae=float(100*np.abs(delta).mean());energy=float(es[ix].mean())
  signed_draw_mean=(sims[ix]*np.sign(delta)[None,None,:]).mean(2)
  mcse=float(100*np.sqrt(signed_draw_mean.var(1,ddof=1).sum()/(len(ix)**2*n)))
  claimed=stability['models'][name]['groups'][group]
  assert abs(mae-claimed['population_curve_mae_pp'])<1e-11 and abs(energy-claimed['energy_score'])<1e-13
  out['final_256_scoring'][name][group]={'population_curve_mae_pp':mae,'energy_score':energy,'conditional_mc_se_mae_pp':mcse}
adv=energy_rows['exposure_growth']-energy_rows['context_value'];rng=np.random.default_rng(74301);boot=np.zeros(10000)
for group in ['B200','Interleaved']:
 ix=[j for j,c in enumerate(columns) if c in m['groups'][group]]
 boot+=.5*adv[ix][rng.integers(0,len(ix),(10000,len(ix)))].mean(1)
out['development_utility']={'equal_group_energy_advantage':float(adv.mean()),'stratified_person_bootstrap_two_sided95':np.quantile(boot,[.025,.975]).tolist(),'interpretation':'Development only; full calibration unfinished; no demonstrated source utility advantage'}
out['target_response_values_read']=0
(HERE/'source_descriptive_results.json').write_text(json.dumps(out,indent=2)+'\n')
print(json.dumps({'final_256_scoring':out['final_256_scoring'],'development_utility':out['development_utility']},indent=2))
