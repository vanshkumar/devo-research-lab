"""Scoring, switch extraction and uncertainty. No implicit data acquisition."""
from pathlib import Path
from dataclasses import replace
import json
import numpy as np
import pandas as pd
from model import prepare_features,fit_model,predict_model,predict_adaptation_contrast,log_score,ModelConfig
ROOT=Path(__file__).resolve().parents[1]

def load_split():
    return pd.read_csv(ROOT/'protocol/split_manifest.csv',dtype={'subject':str,'session':str})

def attach_split(d):
    missing=[c for c in ['schedule','partition'] if c not in d]
    if not missing:return d
    split=load_split()
    if 'schedule' in d:
        expected=d.subject.map(split.set_index('subject').schedule)
        assert d.schedule.eq(expected).all(),'Existing schedule disagrees with frozen split'
    return d.merge(split[['subject']+missing],on='subject',validate='many_to_one')

def windows(d):
    d=d.copy().sort_values(['subject','trial']).reset_index(drop=True)
    d['switch_offset']=999;d['old_majority']=0;d['switch_trial']=-1
    for subject,s in d.groupby('subject',sort=True):
        p=s.probabilityLeft.to_numpy();t=s.trial.to_numpy();idx=s.index.to_numpy()
        starts=np.where((p[1:]!=p[:-1])&(p[1:]!=.5)&(p[:-1]!=.5))[0]+1
        for k in starts:
            if t[k]<200: continue
            stop=next((j for j in range(k+1,len(s)) if p[j]!=p[k]),len(s))
            ii=idx[k:stop]
            d.loc[ii,'switch_offset']=t[k:stop]-t[k]
            d.loc[ii,'switch_trial']=t[k]
            d.loc[ii,'old_majority']=1 if p[k-1]>.5 else -1
    d['primary']=(d.trial>=200)&(d.trial<600)&(d.switch_offset<30)&(d.stimContrast<=.1)
    d['responded']=d.choice.isin([-1,1]) if 'choice' in d else True
    d['primary_responded']=d.primary&d.responded
    return d

def zero_contrast_features(f):
    n=f.nuisance.copy();n[:,1:5]=0;n[:,7]=0
    if n.shape[1]>8: n[:,8:]=0
    rows=f.rows.copy();rows['sideContrast']=0.;rows['stimContrast']=0.
    return replace(f,rows=rows,nuisance=n)

def standardized_effect(fit,f):
    w=windows(f.rows);zf=zero_contrast_features(f)
    shift=predict_adaptation_contrast(fit,zf)*w.old_majority.to_numpy()
    mask=(w.switch_offset<20)&(w.switch_offset>=0)&(w.trial>=200)
    # Every post-switch stimulus history is eligible; zero contrast is imposed.
    x=pd.DataFrame(dict(subject=w.subject,shift=shift,mask=mask,offset=w.switch_offset))
    per=x.loc[x['mask']].groupby('subject')['shift'].mean()
    rms=x.loc[x['mask']].groupby('subject')['shift'].apply(lambda a:np.mean(a*a))
    bins=[]
    for lo,hi in [(0,5),(5,10),(10,20),(20,30)]:
        b=x.loc[x.offset.ge(lo)&x.offset.lt(hi)].groupby('subject')['shift'].mean()
        bins.append(float(b.mean()))
    return dict(mean=float(per.mean()),rms=float(np.sqrt(rms.mean())),bins=bins),per

def bootstrap_mean(table,column,seed=20261029,reps=5000,strata=('partition','condition')):
    rng=np.random.default_rng(seed)
    groups=[a[column].to_numpy() for _,a in table.groupby(list(strata),sort=True)]
    draws=np.zeros(reps);n=sum(len(a) for a in groups)
    for a in groups:
        draws+=rng.choice(a,(reps,len(a)),replace=True).sum(axis=1)/n
    return dict(mean=float(table[column].mean()),low=float(np.quantile(draws,.025)),high=float(np.quantile(draws,.975)),n=len(table),reps=reps)

def score_predictions(f,fits,evaluation_min_trial=200):
    d=windows(attach_split(f.rows));y=f.y
    d['primary'] &= d.trial.ge(evaluation_min_trial)
    d['primary_responded'] = d.primary & d.responded
    for variant,fit in fits.items():
        p=predict_model(fit,f);d['p_'+variant]=p;d['log_'+variant]=log_score(p,y);d['brier_'+variant]=(p-y)**2
    d['delta_log']=d.log_condition-d.log_shared
    d['delta_brier']=d.brier_shared-d.brier_condition
    if 'no_history' in fits: d['history_gain']=d.log_shared-d.log_no_history
    cols=['delta_log','delta_brier']+(['history_gain'] if 'no_history' in fits else [])
    pp=d.loc[d.primary_responded].groupby(['subject','instructions','schedule','partition']).agg(n=('trial','size'),**{c:(c,'mean') for c in cols}).reset_index().rename(columns={'instructions':'condition'})
    sch=pp.groupby(['schedule','partition']).agg(n_people=('subject','size'),n_trials=('n','sum'),**{c:(c,'mean') for c in cols}).reset_index()
    summary={c:bootstrap_mean(pp,c) for c in cols}
    for part,a in pp.groupby('partition'):
        summary[part]={c:bootstrap_mean(a,c,strata=('condition',)) for c in cols}
    # Two-stage schedule then participant bootstrap, conditional on observed split.
    rng=np.random.default_rng(20261030);draw=[]
    groups=[a for _,a in pp.groupby('schedule')]
    for _ in range(5000):
        picked=rng.integers(0,len(groups),len(groups));v=[]
        for k in picked:
            a=groups[k].delta_log.to_numpy();v.extend(rng.choice(a,len(a)))
        draw.append(np.mean(v))
    summary['schedule_participant_bootstrap_delta_log']=dict(mean=float(pp.delta_log.mean()),low=float(np.quantile(draw,.025)),high=float(np.quantile(draw,.975)),note='resamples observed schedules then people; ten schedules total, only three unseen')
    summary['leave_one_schedule_out_delta_log']={str(s):float(pp.loc[pp.schedule!=s,'delta_log'].mean()) for s in pp.schedule.unique()}
    return d,pp,sch,summary

def curves(d):
    rows=[]
    d=d.copy();d['old_choice']=(1+d.choice*d.old_majority)/2
    for contrast_label,contrast_mask in [('low',d.stimContrast.le(.1)),('zero',d.stimContrast.eq(0))]:
      for lo,hi in [(0,5),(5,10),(10,20),(20,30)]:
        a=d.loc[d.switch_offset.ge(lo)&d.switch_offset.lt(hi)&contrast_mask&d.responded]
        pp=a.groupby(['subject','instructions','schedule','partition']).agg(value=('old_choice','mean'),n=('trial','size')).reset_index().rename(columns={'instructions':'condition'})
        for g,b in pp.groupby('condition'):
          ci=bootstrap_mean(b,'value',strata=('partition',))
          rows.append(dict(contrast=contrast_label,start=lo,stop=hi,condition=g,n_people=len(b),n_trials=int(b.n.sum()),**ci))
    return pd.DataFrame(rows)

def refit_bootstrap(dev,reference,config=None,reps=200,seed=20261031,stratify_schedule=False):
    rng=np.random.default_rng(seed);dev=attach_split(dev)
    strata=['schedule','instructions'] if stratify_schedule else ['instructions']
    groups=[g for _,g in dev[['subject','instructions','schedule']].drop_duplicates().groupby(strata)]
    ds={str(s):x for s,x in dev.groupby('subject')};rows=[]
    for rep in range(reps):
        pieces=[];k=0
        for group in groups:
            for subject in rng.choice(group.subject.to_numpy(),len(group),replace=True):
                x=ds[str(subject)].copy();x['subject']=f'boot{k:03d}';pieces.append(x);k+=1
        b=pd.concat(pieces,ignore_index=True);bf=prepare_features(b,config=config)
        fit=fit_model(bf,'condition',config=config)
        assert fit.diagnostics['success'],fit.diagnostics
        rf=prepare_features(reference,calibration_transform=bf.calibration_transform,config=config)
        eff,_=standardized_effect(fit,rf)
        rows.append(dict(replicate=rep,effect=eff['mean'],rms=eff['rms'],max_gradient=fit.diagnostics['max_abs_gradient'],success=fit.diagnostics['success']))
        if (rep+1)%20==0: print('Bootstrap',rep+1,flush=True)
    return pd.DataFrame(rows)

def coding_audit(d):
    assert d.choice.isin([-1,0,1]).all(),'Invalid/missing choice code; requires explicit amendment'
    assert d.probabilityLeft.isin([.2,.5,.8]).all()
    assert d.stimContrast.isin([0,.1,.25,.5,1]).all()
    r=d.choice.isin([-1,1]);fb=d.feedbackType.isin([-1,1])
    return dict(rows=len(d),subjects=d.subject.nunique(),omissions=int((~r).sum()),identity_mismatches=int(((d.choice*d.feedbackType!=d.stimSide)&r&fb).sum()),response_without_feedback=int((r&~fb).sum()),omission_with_feedback=int((~r&fb).sum()),nonzero_side_mismatch=int(((np.sign(d.sideContrast)!=d.stimSide)&d.stimContrast.gt(0)).sum()),rt_missing_responded=int((r&d.response_times_from_stim.isna()).sum()))

def write_json(path,obj): Path(path).write_text(json.dumps(obj,indent=2,allow_nan=False)+'\n')
