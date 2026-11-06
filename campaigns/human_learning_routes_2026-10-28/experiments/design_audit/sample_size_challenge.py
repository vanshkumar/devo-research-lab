"""Additional-observation design on replicated input assignments.

New independent people/choices are simulated; no behavioral trajectory is
duplicated. Ten actual schedules and the locked partition proportions remain.
No empirical outcomes or validation responses are opened.
"""
from pathlib import Path
from dataclasses import replace
from concurrent.futures import ProcessPoolExecutor,as_completed
import argparse,hashlib,json,sys,time
import numpy as np
import pandas as pd

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
sys.path.insert(0,str(ROOT/'experiments'))
import model,recovery,analysis
from calibration_challenge import independent_measurement,replace_calibration


def expanded_inputs(factor):
    original,_=recovery.load_inputs();pieces=[]
    for k in range(factor):
        copy=original.copy()
        copy['subject']=copy.subject+f'R{k:02d}'
        pieces.append(copy)
    inputs=pd.concat(pieces,ignore_index=True).sort_values(['subject','trial']).reset_index(drop=True)
    assert inputs.subject.nunique()==80*factor
    assert inputs.groupby('subject').size().eq(600).all()
    return inputs


def one_job(factor,scenario,rep,scale):
    started=time.monotonic();inputs=expanded_inputs(factor)
    index=list(recovery.SCENARIOS).index(scenario)
    seed=402610280+1000000*factor+10000*index+rep
    frame,truth=recovery.simulate(inputs,scenario,seed,scale)
    subjects=inputs[['subject','instructions','partition']].drop_duplicates()
    rng=np.random.default_rng(seed);u=rng.normal(0,.55,len(subjects));g=subjects.instructions.to_numpy()-.5
    shared_skill=u+(.23/.22)*g;bias=.2*g+rng.normal(0,.35,len(subjects))
    measured=independent_measurement(subjects,shared_skill,bias,seed,sizes=(800,))[800]
    dev=frame[frame.partition.eq('development')];val=frame[~frame.partition.eq('development')]
    df=model.prepare_features(dev);vf=model.prepare_features(val,df.calibration_transform)
    rows=[]
    for variant in ['original','independent800_wide3']:
        if variant=='original': nf,nv=df,vf;cfg=model.ModelConfig()
        else:
            nf=replace_calibration(df,measured)
            nv=replace_calibration(vf,measured,np.asarray(nf.calibration_transform['center']))
            nv=replace(nv,calibration_transform=nf.calibration_transform)
            cfg=model.ModelConfig(condition_history_sd=3.)
        fits={v:model.fit_model(nf,v,config=cfg) for v in ['shared','condition']}
        w=analysis.windows(nv.rows)
        delta=model.log_score(model.predict_model(fits['condition'],nv),nv.y)-model.log_score(model.predict_model(fits['shared'],nv),nv.y)
        score=w[['subject','instructions','partition','schedule']].copy();score['delta_log']=delta
        score=score[w.primary_responded].groupby(['subject','instructions','partition','schedule']).delta_log.mean().reset_index().rename(columns={'instructions':'condition'})
        lo,hi=recovery.score_ci(score,np.random.default_rng(seed+9000000),reps=2000)
        effect,_=analysis.standardized_effect(fits['condition'],nv)
        unseen=score[score.partition.eq('validation_unseen_schedule')]
        ulo,uhi=recovery.score_ci(unseen,np.random.default_rng(seed+9000001),reps=2000)
        rows.append(dict(factor=factor,n_people=80*factor,n_development=41*factor,n_validation=39*factor,
            scenario=scenario,replicate=rep,seed=seed,variant=variant,truth_effect=truth['mean'],
            effect=effect['mean'],effect_bias=effect['mean']-truth['mean'],
            delta_log=float(score.delta_log.mean()),score_low=lo,score_high=hi,score_detect=lo>0,
            unseen_delta_log=float(unseen.delta_log.mean()),unseen_low=ulo,unseen_high=uhi,
            unseen_detect=ulo>0,both_detect=lo>0 and ulo>0,
            max_gradient=max(f.diagnostics['max_abs_gradient'] for f in fits.values()),
            converged=all(f.diagnostics['success'] for f in fits.values()),seconds=time.monotonic()-started))
    return rows


def summarize(d):
    rows=[]
    for (factor,scenario,variant),g in d.groupby(['factor','scenario','variant']):
        n=len(g);k=int(g.score_detect.sum());p=k/n;z=1.96
        den=1+z*z/n;center=(p+z*z/(2*n))/den;radius=z*np.sqrt(p*(1-p)/n+z*z/(4*n*n))/den
        rows.append(dict(factor=factor,n_people=80*factor,scenario=scenario,variant=variant,reps=n,
            truth=float(g.truth_effect.mean()),effect=float(g.effect.mean()),bias=float(g.effect_bias.mean()),
            effect_sd=float(g.effect.std()),score_gain=float(g.delta_log.mean()),score_detections=k,
            score_detection=p,detection_wilson_low=center-radius,detection_wilson_high=center+radius,
            unseen_detection=float(g.unseen_detect.mean()),both_detection=float(g.both_detect.mean()),
            all_converged=bool(g.converged.all())))
    return pd.DataFrame(rows)


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--reps',type=int,default=30);ap.add_argument('--workers',type=int,default=2)
    ap.add_argument('--factors',nargs='+',type=int,default=[2,4]);ap.add_argument('--label',default='sample_size_challenge')
    args=ap.parse_args();out=HERE/args.label;out.mkdir(exist_ok=True)
    assert not (out/'replicates.csv').exists(),'Choose a new output label'
    scenarios=['carryover_null','slow_05','slow_minus05']
    definitions=json.loads((ROOT/'outputs/recovery/final/scenario_definitions.json').read_text())
    scales={s:definitions[s]['scale'] for s in scenarios}
    manifest=dict(args=vars(args),scales=scales,
        scope='Fresh independent simulated people and choices on replicated exact schedules; no real outcomes. Conditional on fixed ten schedules and three held-out schedules.',
        condition='Original assignment proportions, original41/39 development/validation proportions, fresh suffixed IDs.',
        added_observations='Combined variant adds800 independent fully learned sensory choices per person, known lapse/no history, estimated bias; priorSD3 for condition-history effects. Optimistic calibration design.',
        criterion='Report observed detection>=80% for both signs plus null false-detection and Wilson uncertainty; no universal power or new-schedule guarantee.',
        seed_rule='402610280+1000000*factor+10000*scenario_index+replicate',
        hashes={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in ['experiments/model.py','experiments/recovery.py','experiments/analysis.py','experiments/design_audit/calibration_challenge.py','experiments/design_audit/sample_size_challenge.py']})
    (out/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    rows=[]
    with ProcessPoolExecutor(max_workers=args.workers) as executor:
        jobs=[executor.submit(one_job,factor,s,rep,scales[s]) for rep in range(args.reps) for factor in args.factors for s in scenarios]
        for future in as_completed(jobs):
            ans=future.result();rows.extend(ans);d=pd.DataFrame(rows)
            d.to_csv(out/'replicates.csv',index=False);summarize(d).to_csv(out/'summary.csv',index=False)
            print(json.dumps(dict(factor=ans[0]['factor'],scenario=ans[0]['scenario'],rep=ans[0]['replicate'],seconds=round(ans[-1]['seconds'],1))),flush=True)
    print(summarize(pd.DataFrame(rows)).to_string(index=False),flush=True)


if __name__=='__main__':main()
