"""Predeclared robustness analyses; run only after frozen validation opens."""
from pathlib import Path
import json
import numpy as np
import pandas as pd
from model import *
from analysis import *

def main():
    assert (ROOT/'protocol/VALIDATION_OPENED.json').exists()
    dev=attach_split(pd.read_csv(ROOT/'inputs/development_numeric.csv',dtype={'subject':str,'session':str}))
    val=attach_split(pd.read_csv(ROOT/'inputs/validation_numeric.csv',dtype={'subject':str,'session':str}))
    out=ROOT/'outputs/sensitivities';out.mkdir(exist_ok=True)
    meta=load_split();meta['day']=meta.session_start.str.slice(0,10)
    lo=meta.groupby('condition').day.min().max();hi=meta.groupby('condition').day.max().min()
    overlap=set(meta.loc[meta.day.ge(lo)&meta.day.le(hi),'subject'])
    cases=[('sd035',ModelConfig(random_sd=.35),dev,val,200),('sd140',ModelConfig(random_sd=1.4),dev,val,200),
      ('condition_history_prior_sd3',ModelConfig(condition_history_sd=3.),dev,val,200),
      ('exclude_assignment_exceptions',ModelConfig(),dev[~dev.subject.isin(['006','009','010'])],val[~val.subject.isin(['006','009','010'])],200),
      ('common_date_support',ModelConfig(),dev[dev.subject.isin(overlap)],val[val.subject.isin(overlap)],200),
      ('later_301_600',ModelConfig(fit_start=300),dev,val,300),
      ('asymmetric_saturation',ModelConfig(asymmetric_saturation=True),dev,val,200)]
    rows=[]
    for name,cfg,train,test,start in cases:
        f=prepare_features(train,config=cfg);vf=prepare_features(test,calibration_transform=f.calibration_transform,config=cfg)
        fits={v:fit_model(f,v,config=cfg) for v in ['shared','condition']}
        assert all(a.diagnostics['success'] for a in fits.values())
        d,pp,ss,summ=score_predictions(vf,fits,evaluation_min_trial=start)
        eff,_=standardized_effect(fits['condition'],vf)
        pp.to_csv(out/(name+'_participants.csv'),index=False)
        for v,fit in fits.items():fit.save(out/(name+'_'+v+'.json'))
        write_json(out/(name+'_summary.json'),summ)
        rows.append(dict(sensitivity=name,n_development=train.subject.nunique(),n_validation=test.subject.nunique(),delta_log=summ['delta_log']['mean'],low=summ['delta_log']['low'],high=summ['delta_log']['high'],adaptation_effect=eff['mean'],effect_note='All first20 windows, even when scoring interval starts301'))
        print(rows[-1],flush=True)
    primary=pd.read_csv(ROOT/'outputs/primary/trial_predictions.csv',dtype={'subject':str})
    for name,mask in [('zero_contrast',primary.primary_responded&primary.stimContrast.eq(0)),('all_later_responses',primary.trial.ge(200)&primary.responded)]:
        p=primary.loc[mask].groupby(['subject','instructions','schedule','partition']).agg(n=('trial','size'),delta_log=('delta_log','mean')).reset_index().rename(columns={'instructions':'condition'})
        ci=bootstrap_mean(p,'delta_log');p.to_csv(out/(name+'_participants.csv'),index=False)
        rows.append(dict(sensitivity=name,n_development=dev.subject.nunique(),n_validation=len(p),delta_log=ci['mean'],low=ci['low'],high=ci['high'],adaptation_effect=np.nan,effect_note='Primary fits; alternate score subset'))
    # Equal schedule/group weighting is a finite-data weighting sensitivity.
    p=pd.read_csv(ROOT/'outputs/primary/participant_scores.csv',dtype={'subject':str})
    means=p.groupby(['schedule','condition']).delta_log.mean()
    rows.append(dict(sensitivity='equal_schedule_condition_weight',n_development=41,n_validation=len(p),delta_log=float(means.mean()),low=np.nan,high=np.nan,adaptation_effect=np.nan,effect_note='Descriptive weighting sensitivity; no interval'))
    pd.DataFrame(rows).to_csv(out/'summary.csv',index=False)
    write_json(out/'date_support.json',dict(earliest_common_day=lo,latest_common_day=hi,excluded_subjects=sorted(set(meta.subject)-overlap),selection='Metadata only; intersection of observed calendar date ranges in the two conditions'))

if __name__=='__main__':main()
