"""Elapsed-time memory sensitivity using only already-observed feedback.

Fixed seconds scales are2,8,32 times the development median later inter-onset
interval. Current onset time is available; future/current choices are not used.
"""
from dataclasses import replace
import json
import numpy as np
import pandas as pd
from model import *
from analysis import *

def time_features(f,seconds_per_trial):
    h=np.zeros_like(f.history);taus=seconds_per_trial*np.array([2,8,32])
    for subject,s in f.rows.groupby('subject',sort=True):
        onset=s['dot.started'].to_numpy(float);rt=s.response_times_from_stim.to_numpy(float)
        ch=s.choice.to_numpy(float);fb=s.feedbackType.to_numpy(float);ix=s.index.to_numpy()
        assert np.isfinite(onset).all() and (np.diff(onset)>0).all()
        num=np.zeros(3);den=np.ones(3)
        for t in range(len(s)):
            if t:
                decay=np.exp(-(onset[t]-onset[t-1])/taus);num*=decay;den*=decay
                if ch[t-1] in [-1,1] and fb[t-1] in [-1,1]:
                    delay=onset[t]-(onset[t-1]+rt[t-1])
                    assert delay>=0,'Feedback cannot arrive after next stimulus'
                    w=np.exp(-delay/taus);num+=w*ch[t-1]*fb[t-1];den+=w
            h[ix[t]]=num/np.maximum(den,1e-30)
    return replace(f,history=h)

def development_scale(dev):
    gaps=[]
    for _,s in dev.groupby('subject'):
        a=s.sort_values('trial');gap=np.diff(a['dot.started'].to_numpy(float))
        gaps.extend(gap[199:])
    return float(np.median(gaps))

def main():
    assert (ROOT/'protocol/VALIDATION_OPENED.json').exists()
    dev=attach_split(pd.read_csv(ROOT/'inputs/development_numeric.csv',dtype={'subject':str,'session':str}));val=attach_split(pd.read_csv(ROOT/'inputs/validation_numeric.csv',dtype={'subject':str,'session':str}))
    scale=development_scale(dev);f0=prepare_features(dev);f=time_features(f0,scale)
    vf=time_features(prepare_features(val,calibration_transform=f0.calibration_transform),scale)
    fits={v:fit_model(f,v) for v in ['shared','condition']}
    assert all(x.diagnostics['success'] for x in fits.values())
    d,pp,sch,summary=score_predictions(vf,fits);eff,_=standardized_effect(fits['condition'],vf)
    summary['standardized_effect']=eff;summary['seconds_per_trial']=scale;summary['time_constants_seconds']=(scale*np.array([2,8,32])).tolist()
    out=ROOT/'outputs/time_history';out.mkdir(exist_ok=True);pp.to_csv(out/'participant_scores.csv',index=False);sch.to_csv(out/'schedule_scores.csv',index=False)
    write_json(out/'summary.json',summary)
    for v,fit in fits.items():fit.save(out/(v+'_fit.json'))
    print(json.dumps(summary,indent=2))

if __name__=='__main__':main()
