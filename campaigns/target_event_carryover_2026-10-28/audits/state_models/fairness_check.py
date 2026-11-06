"""Replay prespecified and worst-bias positive-boundary replicates with exact empirical multistarts."""
import json,sys,time
from pathlib import Path
import numpy as np
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parents[1]/'experiments'))
import state_models as s

records=json.loads((s.OUT/'state_models_stress.json').read_text())['records']
old={r['rep']:r for r in records if r['scenario']=='fast_modulation' and r['target_theta']==.2}
assert len(old)==100
uniform=list(np.linspace(0,99,20).astype(int))
worst=sorted(old,key=lambda k:old[k]['fit_theta']-old[k]['true_theta'])[:10]
chosen=sorted(set(uniform+worst))
ps=s.load('development','Hand_raw',inputs_only=True)
counts=[s.counts_for_truth(p) for p in ps]
out=[];started=time.time()
for rep in chosen:
    rng=np.random.default_rng(932000+rep)
    scales=np.exp(rng.normal(0,.20,len(ps)));scales/=scales.mean()
    delta,true=s.calibrated_delta(.2,.65,1.,scales,counts)
    effect=delta*np.mean(.65**np.arange(5))
    ds=[]
    for i,p in enumerate(ps):
        pp=dict(p)
        pp['y']=s.generate(p['c'],p['j'],seed=382000+rep*100+i,kind='retention',effect=effect,
            noise_sd=2.5,drift_scale=.6,retentions=(.65,.97),gains=(1.,.20),
            person_scale=float(scales[i]),omission_rate=.01)['y']
        ds.append(s.cell_design(pp))
    rr=s.fit(ds)
    ff=s.fit(ds,True,start=rr['parameters'])
    unc=s.uncertainty(ds,ff)
    theta=float(s.curves(ds,ff).mean());ci=unc['cluster_profile_ci95']
    out.append({'rep':int(rep),'uniform_subset':rep in uniform,'worst_bias_subset':rep in worst,
        'old_theta':old[rep]['fit_theta'],'theta':theta,'difference':theta-old[rep]['fit_theta'],
        'profile_ci95':ci,'old_ci95':old[rep]['profile_ci95'],
        'old_parameters':old[rep]['fit_parameters'],'parameters':ff['parameters'],
        'old_mse_gain':old[rep]['mse_gain'],'mse_gain':rr['mse']-ff['mse'],
        'coverage':bool(ci[0]<=true<=ci[1]),'false_equivalence':bool(ci[0]>-.2 and ci[1]<.2),
        'restricted_starts':rr['starts'],'alternative_starts':ff['starts']})
    (s.OUT/'state_models_optimizer_fairness.json').write_text(json.dumps(s.jsonable({'records':out,'elapsed_seconds':time.time()-started}),indent=2)+'\n')
    print('fairness',rep,'theta_diff',round(theta-old[rep]['fit_theta'],7),'old_falseeq',old[rep]['false_equivalence_at_or_outside_boundary'],
          'new_falseeq',out[-1]['false_equivalence'],'elapsed',round(time.time()-started),flush=True)
