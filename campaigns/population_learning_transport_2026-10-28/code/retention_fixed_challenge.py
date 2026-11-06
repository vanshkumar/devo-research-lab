"""Matched fixed-policy diagnostic for the declared future retention perturbation."""
import json,time
import numpy as np
from campaign import C,MODEL,BANK,load_rnn,load_bank,draw_initial,calibration_particles,fit_competence,simulate,seed_for
from diagnostics import SavedCalibration

def main():
    f=C/'artifacts/forecasts/source';out=C/'artifacts/diagnostics'
    r=json.loads((C/'artifacts/results/SOURCE_RESULT.json').read_text());subjects=r['subjects']
    model=load_rnn(MODEL);bank=load_bank(BANK);fixed=[];probes=[]
    for s in subjects:
        seed=seed_for(s);meta=json.loads((f/(s+'__rnn.json')).read_text())
        with np.load(f/(s+'__prefix.npz'),allow_pickle=False) as z:
            prefix={k:z[k] for k in z.files if k!='future_session_start'};starts=z['future_session_start']
        n=128;common=draw_initial(prefix,bank,n,seed+211,exclude=s,competence='growth')
        state,_=calibration_particles(SavedCalibration(model,meta['calibration']),prefix,n,seed+313)
        w,cov,_=fit_competence(prefix,ridge=.5);pw=np.random.default_rng(seed+313).multivariate_normal(w,cov,size=n)
        a=simulate(model,prefix,starts,common,state,pw,'rnn','external',seed,retention=.8,hidden_retention=.8)
        fixed.append(a['samples'][:,:,:2].mean(2));probes.append(a['probe100'])
        print(s,flush=True)
    a=np.asarray(fixed)
    with np.load(out/'future_retention_0p8.npz',allow_pickle=False) as z:b=z['samples']
    delta=(a-b).mean(2)
    result=dict(scope='postvalidation matched future-only0.8sessionretention under both policies; sourceprefixes only, no external data or fitted replacement',
                n=24,particles=128,standard_mean=float(b.mean()),fixed_mean=float(a.mean()),fixed_minus_adaptive=float(delta.mean()),
                conditional_MC_SE=float(np.sqrt(np.var(delta,axis=1,ddof=1).sum()/128)/24),
                mean_curve=(a-b).mean((0,1)).tolist(),fixed_probe_mean=float(np.mean(probes)),
                interpretation='Magnitude of counterfactual changes with session assumptions; no scientific gate or access release is recomputed')
    np.savez_compressed(out/'future_retention_0p8_fixed.npz',samples=a,probe100=np.asarray(probes))
    (out/'RETENTION_FIXED_RESULT.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2),flush=True)

if __name__=='__main__':main()
