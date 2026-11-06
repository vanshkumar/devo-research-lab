#!/usr/bin/env python3
"""Summarize the frozen source test without fitting or selecting a new law."""
import csv,hashlib,json
from pathlib import Path
import numpy as np
from scipy.special import expit
from evaluation import score
from baselines import subset,fit_competence
from learning_models import subject_arrays,features
from data_io import load_subject,exposure

C=Path(__file__).resolve().parents[1]
O=C/'artifacts/results';O.mkdir(parents=True,exist_ok=True)
T=C/'tables';T.mkdir(parents=True,exist_ok=True)
MODELS=['persistence','growth','reinforce_pure','reinforce','dnnglm','dnnglm32']
CANDIDATES=['dnnglm32','dnnglm','reinforce','reinforce_pure']


def dump(path,value):path.write_text(json.dumps(value,indent=2,allow_nan=True)+'\n')


def write_csv(path,rows):
    keys=list(dict.fromkeys(k for r in rows for k in r))
    with open(path,'w',newline='')as f:
        w=csv.DictWriter(f,fieldnames=keys);w.writeheader()
        for r in rows:w.writerow({k:json.dumps(v)if isinstance(v,(list,dict))else v for k,v in r.items()})


def records():
    rows=[]
    for tag in ['source_animals','source_labs']:
        rows.extend(json.loads((C/'artifacts/forecasts'/tag/'scores.json').read_text()))
    return rows


def allocation():return {r['subject']:r for r in json.loads((C/'protocols/SPLIT.json').read_text())['standard']}


def curve(subject,model):
    split=allocation()[subject]['split'];tag='source_animals'if split=='animal_holdout'else'source_labs'
    folder=C/'artifacts/forecasts'/tag
    z=np.load(folder/(subject+'__'+model+'.npz'))
    y=np.load(folder/(subject+'__observed.npz'))['observed']
    return z,y


def paired(d,seed=891):
    d=np.asarray(d,float);rng=np.random.default_rng(seed)
    bs=d[rng.integers(len(d),size=(10000,len(d)))].mean(axis=1)
    return dict(n=len(d),mean=float(d.mean()),lo=float(np.quantile(bs,.025)),hi=float(np.quantile(bs,.975)),
                gate_lower=float(np.quantile(bs,.00625)),gate_percentile=.00625)


def main():
    rr=records();amap=allocation();subject_order=[]
    for split in ['animal_holdout','lab_holdout']:
        subject_order+=sorted({r['subject']for r in rr if r['arm']=='autonomous'and r['horizon']==3000 and r['full_horizon']and r['split']==split})
    dump(O/'SUBJECT_ORDER.json',subject_order)
    lookup={(r['subject'],r['model'],r['arm'],r['horizon']):r for r in rr}
    groups={'all':subject_order,'animal_holdout':[s for s in subject_order if amap[s]['split']=='animal_holdout'],
            'lab_holdout':[s for s in subject_order if amap[s]['split']=='lab_holdout']}
    for lab in sorted({amap[s]['lab']for s in subject_order}):groups[lab]=[s for s in subject_order if amap[s]['lab']==lab]
    summaries=[];calibration=[]
    for group,ids in groups.items():
      for model in MODELS:
       for arm in ['autonomous','raw_autonomous','conditional_diagnostic']:
        rs=[lookup[(s,model,arm,3000)]for s in ids if(s,model,arm,3000)in lookup]
        if not rs:continue
        out=dict(group=group,n=len(rs),model=model,arm=arm)
        for key in ['crps','mae','high_accuracy_mae','binary_nll','energy']:
            if key in rs[0]:out[key]=float(np.mean([r[key]for r in rs]))
        out['crps_by_metric']=np.mean([r['crps_by_metric']for r in rs],axis=0).tolist()
        out['mae_by_metric']=np.mean([r['mae_by_metric']for r in rs],axis=0).tolist()
        out['coverage80']=float(np.mean([r['coverage']['0.8']for r in rs]));out['width80']=float(np.mean([r['width']['0.8']for r in rs]))
        if arm=='autonomous':
            highcoverage=[];highwidth=[]
            for s in ids:
                z,y=curve(s,model);a=z['samples_primary'][:,:6];y=y[:6]
                lo,hi=np.quantile(a,[.1,.9],axis=0)
                valid=np.isfinite(y[:,:2]);highcoverage.append(np.mean(((y[:,:2]>=lo[:,:2])&(y[:,:2]<=hi[:,:2]))[valid]));highwidth.append(np.mean((hi[:,:2]-lo[:,:2])[valid]))
            out['high_coverage80']=float(np.mean(highcoverage));out['high_width80']=float(np.mean(highwidth))
        summaries.append(out)
    for model in MODELS:
      for b in range(6):
       for j,metric in enumerate(['left_high_correct','right_high_correct','right_choice_share','omission']):
        vals=[];width=[];errors=[]
        for s in subject_order:
            z,y=curve(s,model);a=z['samples_primary'];lo,hi=np.quantile(a[:,b,j],[.1,.9]);yy=y[b,j]
            if np.isfinite(yy):vals.append(lo<=yy<=hi);width.append(hi-lo);errors.append(abs(a[:,b,j].mean()-yy))
        calibration.append(dict(model=model,bin=b+1,metric=metric,n=len(vals),coverage80=float(np.mean(vals)),width80=float(np.mean(width)),mae=float(np.mean(errors))))
    write_csv(T/'primary_scores.csv',summaries);dump(O/'PRIMARY_SUMMARY.json',summaries)
    write_csv(T/'calibration_by_bin_metric.csv',calibration)
    comparisons=[]
    for group,ids in groups.items():
      if not ids:continue
      for model in CANDIDATES:
       for baseline in ['growth','persistence']:
        a=[lookup[(s,baseline,'autonomous',3000)]['crps']-lookup[(s,model,'autonomous',3000)]['crps']for s in ids]
        h=[lookup[(s,baseline,'autonomous',3000)]['high_accuracy_mae']-lookup[(s,model,'autonomous',3000)]['high_accuracy_mae']for s in ids]
        base=float(np.mean([lookup[(s,baseline,'autonomous',3000)]['crps']for s in ids]));baseh=float(np.mean([lookup[(s,baseline,'autonomous',3000)]['high_accuracy_mae']for s in ids]))
        comparisons.append(dict(group=group,model=model,baseline=baseline,crps_gain=paired(a),
                                crps_relative_gain=float(np.mean(a)/base),high_mae_gain=paired(h),high_mae_relative_gain=float(np.mean(h)/baseh)))
    dump(O/'PAIRED_COMPARISONS.json',comparisons);write_csv(T/'paired_comparisons.csv',comparisons)
    sm={(r['group'],r['model'],r['arm']):r for r in summaries}
    gate=[]
    for model in CANDIDATES:
        reasons=[];r=sm[('all',model,'autonomous')]
        for baseline in ['growth','persistence']:
            comp=next(x for x in comparisons if x['group']=='all'and x['model']==model and x['baseline']==baseline)
            if comp['crps_gain']['mean']<.002:reasons.append('overall absoluteCRPSgain<.002 vs'+baseline)
            if comp['crps_relative_gain']<.10:reasons.append('overall relativeCRPSgain<10% vs'+baseline)
            if comp['crps_gain']['gate_lower']<=0:reasons.append('family-screen lower scoregain<=0 vs'+baseline)
            if comp['high_mae_relative_gain']<.10:reasons.append('highcontrastMAEimprovement<10% vs'+baseline)
            lab=next(x for x in comparisons if x['group']=='lab_holdout'and x['model']==model and x['baseline']==baseline)
            if lab['crps_relative_gain']<.05:reasons.append('heldlabCRPSgain<5% vs'+baseline)
            if lab['high_mae_gain']['mean']<0:reasons.append('heldlabhighMAEworsens vs'+baseline)
            for lname in ['hoferlab','wittenlab']:
                ll=next(x for x in comparisons if x['group']==lname and x['model']==model and x['baseline']==baseline)
                if ll['crps_gain']['mean']<=0:reasons.append(lname+'meanCRPSgain<=0 vs'+baseline)
        if r['high_accuracy_mae']>.15:reasons.append('highcontrastMAE>15pp')
        if not .70<=r['coverage80']<=.95:reasons.append('overall80%coverageoutside70–95%')
        if not .70<=r['high_coverage80']<=.95:reasons.append('highcontrast80%coverageoutside70–95%')
        gate.append(dict(model=model,earned=not reasons,reasons=reasons))
    decision=dict(freeze_sha256=hashlib.sha256((C/'protocols/FREEZE.json').read_bytes()).hexdigest(),
                  source_gate_earned=any(g['earned']for g in gate),candidates=gate,
                  external_status='sealed; no new prefixes/outcomes accessed',
                  interpretation='Failure to earn practical gate is not equivalence or proof that no model can predict acquisition.',
                  subject_order='SUBJECT_ORDER.json',n_primary=len(subject_order))
    dump(O/'SOURCE_GATE.json',decision)
    if decision['source_gate_earned']:
        passed=[g['model']for g in gate if g['earned']];best=min(passed,key=lambda m:sm[('all',m,'autonomous')]['crps'])
        dump(C/'protocols/EXTERNAL_ACCESS_EARNED.json',dict(**decision,selected_rule=best))
    # Same-input sequential log-loss comparison: this avoids mistaking the
    # conditional curve score for an autonomous score.
    nllrows=[];prefix_metrics=[]
    for s in subject_order:
        split=amap[s]['split'];d=load_subject(s,split,purpose='frozen source same-input staticNLL and predeclared prefix strata',freeze_path=C/'protocols/FREEZE.json')
        pr=subset(d,0,1000);fu=subset(d,1000,4000);w,_,_=fit_competence(pr,ridge=.5)
        x,c,_,_=subject_arrays(fu);ok=c!=0;p=expit(np.einsum('ni,i->n',features(x),w));p=np.clip(p,1e-8,1-1e-8)
        static=float(-np.mean(np.where(c[ok]<0,np.log(p[ok]),np.log1p(-p[ok]))))
        for model in CANDIDATES:
            con=lookup[(s,model,'conditional_diagnostic',3000)]
            nllrows.append(dict(subject=s,split=split,lab=amap[s]['lab'],model=model,conditional_nll=con['binary_nll'],static_nll=static,gain=static-con['binary_nll']))
        xx,cc,_,_=subject_arrays(pr);hi=np.abs(xx)>=.5
        prefix_metrics.append(dict(subject=s,split=split,lab=amap[s]['lab'],prefix_high_accuracy=float(np.mean((cc==-np.sign(xx))[hi])),prefix_omission=float(np.mean(cc==0)),cache_left_edge=amap[s]['first_indexed_date']=='2019-06-11'))
    write_csv(T/'conditional_nll.csv',nllrows);write_csv(T/'prefix_strata_inputs.csv',prefix_metrics)
    nllsummary=[]
    for m in CANDIDATES:
        r=[a for a in nllrows if a['model']==m]
        nllsummary.append(dict(model=m,n=len(r),conditional_nll=float(np.mean([a['conditional_nll']for a in r])),
                               static_nll=float(np.mean([a['static_nll']for a in r])),gain_nats=paired([a['gain']for a in r])))
    dump(O/'CONDITIONAL_NLL.json',nllsummary)
    # Predeclared prefix/left-truncation strata, diagnostic only.
    strata={'prefix_high<.8':[a['subject']for a in prefix_metrics if a['prefix_high_accuracy']<.8],
            'prefix_high>=.8':[a['subject']for a in prefix_metrics if a['prefix_high_accuracy']>=.8],
            'first_indexed_after_cache_left_edge':[a['subject']for a in prefix_metrics if not a['cache_left_edge']]}
    srows=[]
    for name,ids in strata.items():
      for m in MODELS:
       r=[lookup[(s,m,'autonomous',3000)]for s in ids]
       if r:srows.append(dict(stratum=name,model=m,n=len(r),crps=float(np.mean([v['crps']for v in r])),high_mae=float(np.mean([v['high_accuracy_mae']for v in r]))))
    write_csv(T/'prefix_strata_results.csv',srows)
    write_csv(T/'individual_scores.csv',rr)
    exposure(dict(event='frozen_source_gate_scored',source_gate_earned=decision['source_gate_earned'],n_primary=len(subject_order),external_outcomes_open=False))
    print(json.dumps(dict(primary=[r for r in summaries if r['group']=='all'and r['arm']=='autonomous'],gate=decision,nll=nllsummary),indent=2))

if __name__=='__main__':main()
