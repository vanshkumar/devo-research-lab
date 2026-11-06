"""One locked validation execution (and deterministic offline reproduction)."""
import argparse,csv,hashlib,json,sys,time
from datetime import datetime,timezone
from pathlib import Path
from dataclasses import replace
import numpy as np
import pandas as pd
from model import *
from analysis import *

def acquire_numeric_validation():
    # This is the first code path that parses reserved response values.
    split=load_split();ids=set(split.loc[split.partition!='development','subject'])
    fields=list(pd.read_csv(ROOT/'inputs/development_numeric.csv',nrows=0).columns)
    out=ROOT/'inputs/validation_numeric.csv'
    if not out.exists():
        with (ROOT/'inputs/processed_data_2026.csv').open(newline='') as inp,out.open('w',newline='') as dest:
            reader=csv.DictReader(inp);writer=csv.DictWriter(dest,fieldnames=fields);writer.writeheader()
            for row in reader:
                if row['subject'] in ids: writer.writerow({k:row[k] for k in fields})
        write_json(ROOT/'protocol/VALIDATION_OPENED.json',dict(utc=datetime.now(timezone.utc).isoformat(),operation='First reserved response extraction under frozen protocol',sha256=hashlib.sha256(out.read_bytes()).hexdigest(),participants=len(ids)))
    return pd.read_csv(out,dtype={'subject':str,'session':str})

def model_old_context(fit,f):
    """Oracle-aligned diagnostic removing pre-switch feedback contribution only.

    Labels define a counterfactual probe, never an ordinary choice predictor.
    Lagged choices remain unchanged; this isolates the feedback trace component.
    """
    w=windows(f.rows);h=f.history.copy();decay=np.exp(-1/np.array(fit.config.taus))
    for subject,s in w.groupby('subject',sort=True):
        for sw,a in s.loc[s.switch_trial.ge(200)&s.switch_offset.lt(30)].groupby('switch_trial'):
            ix=s.index[s.trial==sw][0];h[a.index]-=f.history[ix][None,:]*decay[None,:]**a.switch_offset.to_numpy()[:,None]
    zf=zero_contrast_features(f);reset=replace(zf,history=h)
    full=predict_model(fit,zf);resetp=predict_model(fit,reset)
    w['old_context_component']=(full-resetp)*w.old_majority.to_numpy()
    w['standardized_old_probability']=.5+(full-.5)*w.old_majority.to_numpy()
    rows=[]
    for lo,hi in [(0,5),(5,10),(10,20),(20,30)]:
        a=w.loc[w.switch_offset.ge(lo)&w.switch_offset.lt(hi)]
        p=a.groupby(['subject','instructions']).agg(component=('old_context_component','mean'),old_probability=('standardized_old_probability','mean')).reset_index()
        for g,b in p.groupby('instructions'):
            rows.append(dict(start=lo,stop=hi,condition=int(g),n_people=len(b),component=float(b.component.mean()),old_probability=float(b.old_probability.mean())))
    return pd.DataFrame(rows)

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--out',default='outputs/primary');ap.add_argument('--bootstrap',type=int,default=200);a=ap.parse_args()
    lock=json.loads((ROOT/'protocol/FINAL_FREEZE.json').read_text())
    for name,expected in lock['sha256'].items():
        actual=hashlib.sha256((ROOT/name).read_bytes()).hexdigest()
        assert actual==expected, f'Frozen file changed: {name}'
    out=ROOT/a.out;out.mkdir(parents=True,exist_ok=True)
    assert not (out/'summary.json').exists(), 'Choose a new --out to preserve original results'
    dev=attach_split(pd.read_csv(ROOT/'inputs/development_numeric.csv',dtype={'subject':str,'session':str}))
    # Fit before loading reserved choices. No validation-dependent fitting occurs.
    f=prepare_features(dev);fits={}
    for v in ['no_history','shared','condition']:
        fits[v]=fit_model(f,v);fits[v].save(out/(v+'_fit.json'))
        assert fits[v].diagnostics['success'],fits[v].diagnostics
    val=attach_split(acquire_numeric_validation());vf=prepare_features(val,calibration_transform=f.calibration_transform)
    audit=coding_audit(val);assert not any(audit[k] for k in ['identity_mismatches','response_without_feedback','omission_with_feedback','nonzero_side_mismatch','rt_missing_responded'])
    write_json(out/'validation_coding_audit.json',audit)
    scored,pp,sch,summary=score_predictions(vf,fits)
    scored.to_csv(out/'trial_predictions.csv',index=False);pp.to_csv(out/'participant_scores.csv',index=False);sch.to_csv(out/'schedule_scores.csv',index=False)
    curves(scored).to_csv(out/'observable_curves.csv',index=False)
    model_old_context(fits['shared'],vf).to_csv(out/'shared_old_context_component.csv',index=False)
    eff,eper=standardized_effect(fits['condition'],vf);eper.to_csv(out/'participant_standardized_effect.csv')
    summary['standardized_adaptation_effect']=eff
    summary['fit_diagnostics']={v:fit.diagnostics for v,fit in fits.items()}
    write_json(out/'summary_prebootstrap.json',summary)
    print(json.dumps(summary,indent=2),flush=True)
    if a.bootstrap:
        boot=refit_bootstrap(dev,val,reps=a.bootstrap);boot.to_csv(out/'development_refit_bootstrap.csv',index=False)
        summary['standardized_effect_interval']=dict(low=float(boot.effect.quantile(.025)),high=float(boot.effect.quantile(.975)),reps=a.bootstrap,scope='Development whole-subject resampling within condition; schedule composition varies within observed development schedules. Reference histories/calibration fixed to validation people.',all_converged=bool(boot.success.all()))
    write_json(out/'summary.json',summary)
    print('Completed:',out,flush=True)

if __name__=='__main__':main()
