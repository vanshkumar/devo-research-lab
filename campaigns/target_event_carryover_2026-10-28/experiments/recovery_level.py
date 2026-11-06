"""Recovery of the already prespecified endpoint-level sensitivity.

Same frozen nuisance/contrast, schedules, masks and core generators as main
recovery; only outcome is y[t+h] rather than y[t+h]-mean(y[t-5:t]). Main analysis
and all original outputs remain unchanged. Reserved INPUTS ONLY.
"""
import json,hashlib,time,argparse
import numpy as np
from analysis import load,make_design,prepare,fit,curve_summary,pooled_summary,mm,ROOT,FILES,jsonable
from recovery import estimate,simulate_scenario,summarize


def map_level(out,weights,d,key_index):
    weights=np.atleast_2d(weights)
    for r,(key,tn,_,_) in enumerate(d['meta']):
        out[:,key_index[key]*824+tn-1+d['h']] += weights[:,r]


def build_level(people):
    rng=np.random.default_rng(194192);masks={p['key']:rng.uniform(size=824)>=.03 for p in people}
    keys={p['key']:i for i,p in enumerate(people)};total=len(people)*824
    for p in people:p['y']=np.where(masks[p['key']],0.,np.nan)
    sets=[];preps={}
    for file in FILES:
        pp=[p for p in people if p['file']==file];K=np.zeros(total);scores=np.zeros((10,total));lagK=np.zeros((5,total));ds=[]
        for h in range(1,6):
            d=make_design(pp,h,level=True);pr=prepare(d);preps[(file,h)]=pr;ds.append(d)
            w=mm(d['contrast'],pr['W']);G=d['groups'];n=len(w)
            U=np.array([w*(G==g) for g in range(10)])
            S=U-mm(mm(U,pr['Q']),pr['Q'].T)-mm(mm(U,pr['RZ']),pr['W'])
            S*=np.sqrt(10/9*(n-1)/(n-pr['p']))
            tmp=np.zeros((1,total));map_level(tmp,w,d,keys);lagK[h-1]=tmp[0];K+=tmp[0]/5
            tmp=np.zeros((10,total));map_level(tmp,S,d,keys);scores+=tmp/5
        sets.append(dict(file=file,K=K,scores=scores,lagK=lagK,ds=ds))
    return dict(sets=sets,K=sum(s['K'] for s in sets)/2,lagK=sum(s['lagK'] for s in sets)/2,
                scores=np.vstack([s['scores']/2 for s in sets]),masks=masks,preps=preps,
                key_index=keys,omit=.03,people=people)


def verify(op):
    Y=np.random.default_rng(81129).normal(size=(20,824));ss=[]
    for file in FILES:
        ff=[]
        for h in range(1,6):
            prep=op['preps'][(file,h)];d=prep['d']
            yy=np.array([Y[op['key_index'][key],tn-1+h] for key,tn,_,_ in d['meta']])
            ff.append(fit(prep,yy))
        ss.append(curve_summary(ff))
    direct=pooled_summary(ss);fast=estimate(op,Y)
    err=max(abs(direct[k]-fast[k]) for k in ['estimate','se','low','high']);assert err<1e-10
    return err


def run(reps=300):
    started=time.time();people=load('validation',inputs_only=True);op=build_level(people)
    old=json.loads((ROOT/'outputs/recovery/summary.json').read_text())
    scenarios=[('two_timescale_null','two_timescale',0.,(.65,.20),819281)]
    for k,key in enumerate(['actual_margin_negative','actual_margin_positive']):
        v=old['scenarios'][key]
        scenarios.append((key,'retention',v['isolated_reference_effect'],tuple(v['gains']),819281+(8+k)*100000))
    out=dict(scope='Prespecified endpoint-level sensitivity; main analysis unchanged. Reserved INPUT schedules only.',
       inference='Same participant-cluster CR1 and Welch set pooling as primary; all five pre/future eligibility masks retained.',
       operators_verified_max_difference=verify(op),replicates=reps,paired_to_original=True,
       analysis_sha256=hashlib.sha256((ROOT/'experiments/analysis.py').read_bytes()).hexdigest(),scenarios={})
    for name,kind,effect,gains,seed in scenarios:
        rows=simulate_scenario(op,kind,effect,reps,seed,gains=gains)
        (ROOT/'outputs'/('recovery_level_'+name+'.json')).write_text(json.dumps(rows,indent=2)+'\n')
        v=summarize(rows);v.update(kind=kind,isolated_reference_effect=effect,gains=list(gains))
        original=json.loads((ROOT/'outputs/recovery'/(name+'.json')).read_text())[:reps]
        v['change_comparison']=dict(original_mean_se=old['scenarios'][name]['mean_se'],
            original_detection=old['scenarios'][name]['reject_zero']['rate'],
            mean_paired_estimate_difference=float(np.mean([r['estimate']-s['estimate'] for r,s in zip(rows,original)])),
            se_ratio=float(np.mean([r['se'] for r in rows])/np.mean([r['se'] for r in original])))
        out['scenarios'][name]=v
        (ROOT/'outputs/recovery_level_summary.json').write_text(json.dumps(jsonable(out),indent=2)+'\n')
        print(name,json.dumps(v),flush=True)
    out['seconds']=time.time()-started
    (ROOT/'outputs/recovery_level_summary.json').write_text(json.dumps(jsonable(out),indent=2)+'\n')
    return out

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--reps',type=int,default=300);a=ap.parse_args();run(a.reps)
