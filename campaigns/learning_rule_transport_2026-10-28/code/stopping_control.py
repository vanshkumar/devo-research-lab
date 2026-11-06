#!/usr/bin/env python3
"""Postvalidation known-rule challenge: outcome-dependent training termination.

This censors independently generated closed-loop histories at a rule based on
their past outcomes. It tests one selection mechanism, not the real RT/time
stopping mechanism or all conditional-opportunity models. No empirical data.
"""
import json
from pathlib import Path
import numpy as np
from learning_models import subject_arrays
from evaluation import score,paired_interval
from baselines import subset,load_bank
from learning_models import load_model
from rollout import autonomous,trajectory_summary

C=Path(__file__).resolve().parents[1];R=C/'artifacts/recovery';O=C/'artifacts/stopping_control'
O.mkdir(exist_ok=True,parents=True)


def main():
    # Initial85%pilot produced no pre4000termination. Preserve it, then use a
    # fixed75%challenge on a NEW independently seeded cohort. Threshold choice
    # is explicitly exploratory; no empirical source outcomes enter it.
    old=O/'RESULT.json'
    if old.exists()and not(O/'INITIAL_85_PERCENT_PILOT.json').exists():
        (O/'INITIAL_85_PERCENT_PILOT.json').write_bytes(old.read_bytes())
    from recovery import generate
    source=R/'synthetic/stopping_challenge'
    if not source.exists():generate('stopping_challenge',n=24,trials=6000,protocol='standard',seed=8739)
    dispositions=[];rows=[]
    for index,path in enumerate(sorted(source.glob('*.npz'))):
        z=np.load(path);d={k:z[k]for k in z.files};x,c,_,_=subject_arrays(d)
        block=[]
        for start in range(0,len(c),500):
            xx=x[start:start+500];cc=c[start:start+500];hi=np.abs(xx)>=.5
            block.append(float(np.mean((cc==-np.sign(xx))[hi])))
        end=len(c);reason='maximum6000'
        for b in range(3,len(block)):
            if min(block[b-1:b+1])>=.75:
                end=(b+1)*500;reason='two consecutive high-accuracy sessions >=75%';break
            if max(block[b-2:b+1])<.45:
                end=(b+1)*500;reason='three consecutive low-accuracy sessions <45%';break
        dispositions.append(dict(subject=path.stem,stop=end,reason=reason,primary_full=end>=4000))
        for model in ['oracle','pipeline_fitted','growth','persistence']:
            B=min(6,(end-1000)//500)
            if B<=0:continue
            fp=O/(path.stem+'__'+model+'.npz')
            if not fp.exists():
                from recovery import true_model
                actor=true_model()if model=='oracle'else(load_model(R/'pipeline_fitted_reinforce.npz')if model=='pipeline_fitted'else None)
                result=autonomous(actor,subset(d,0,1000),d['session_start'][1000:1000+B*500],load_bank(R/'learn_bank.npz'),
                    n_particles=128,seed=48739+index,subject=path.stem,competence=model if model in('growth','persistence')else None)
                y,_=trajectory_summary(x[1000:1000+B*500],c[1000:1000+B*500])
                np.savez_compressed(fp,samples=result['samples'],observed=y[0])
            f=np.load(fp)
            rows.append(dict(subject=path.stem,model=model,full=end>=4000,bins=B,**score(f['samples'][:,:B],f['observed'][:B])))
    summary=[];comparisons=[]
    for full_only in [True,False]:
        for model in ['oracle','pipeline_fitted','growth','persistence']:
            rr=[r for r in rows if r['model']==model and(r['full']or not full_only)]
            summary.append(dict(model=model,full_only=full_only,n=len(rr),crps=float(np.mean([r['crps']for r in rr])),
                high_mae=float(np.mean([r['high_accuracy_mae']for r in rr])),coverage80=float(np.mean([r['coverage']['0.8']for r in rr]))))
        a={r['subject']:r for r in rows if r['model']=='pipeline_fitted'and(r['full']or not full_only)}
        b={r['subject']:r for r in rows if r['model']=='growth'and(r['full']or not full_only)}
        gain=paired_interval([b[s]['crps']-a[s]['crps']for s in sorted(a)])
        if len(a)<3:
            gain.update(lo=None,hi=None,interval_status='too few independent animals for an informative interval')
        comparisons.append(dict(full_only=full_only,gain=gain))
    result=dict(timing='post-source-validation diagnostic; no real data used',seed='NEW independent stopping_challenge8739 generator, forecast48739+animalindex',
        law='same known transferable REINFORCE; histories truly generated closed-loop before censoring',
        terminal_policy='begin afterfour500trialsessions; stopafter2consecutive>=75%highcorrect or3consecutive<45%,otherwise6000',
        interpretation='Operational forecast conditions on opportunities without conditioning latent state on termination event. This bounded stopping selection does not validate real RT/fatigue/session-duration stopping.',
        dispositions=dispositions,summary=summary,comparisons=comparisons)
    (O/'RESULT.json').write_text(json.dumps(result,indent=2)+'\n')
    (O/'individual_scores.json').write_text(json.dumps(rows,indent=2)+'\n')
    print(json.dumps(dict(summary=summary,comparisons=comparisons),indent=2))

if __name__=='__main__':main()
