"""Actual-schedule recovery using INPUTS ONLY from reserved primary people.

Creates no release record and never accesses empirical validation outcomes.
The frozen estimator is evaluated through exactly equivalent linear operators.
"""
from pathlib import Path
import json, argparse, hashlib, time, csv
import numpy as np
from scipy import linalg, stats, optimize
from analysis import load, make_design, prepare, fit, curve_summary, pooled_summary, mm, ROOT, FILES, jsonable
from generators import generate


def put_series_kernel(out, row_weights, d, key_index):
    # Algebraically expand Y_row=y[t+h]-mean(y[t-5:t]) without joining gaps.
    row_weights=np.atleast_2d(row_weights)
    for r,(key,tn,b,loc) in enumerate(d['meta']):
        off=key_index[key]*824;t=tn-1
        out[:,off+t+d['h']] += row_weights[:,r]
        for k in range(1,6):out[:,off+t-k] -= row_weights[:,r]/5


def build_operators(people, omit=0.03):
    mask_rng=np.random.default_rng(194192)
    masks={p['key']:mask_rng.uniform(size=824)>=omit for p in people}
    key_index={p['key']:i for i,p in enumerate(people)}
    for p in people:p['y']=np.where(masks[p['key']],0.,np.nan)
    sets=[]; preps={}; total=len(people)*824
    for file in FILES:
        pp=[p for p in people if p['file']==file]
        K=np.zeros(total); scores=np.zeros((len(pp),total)); lagK=np.zeros((5,total));ds=[]
        for h in range(1,6):
            d=make_design(pp,h); prep=prepare(d);ds.append(d);preps[(file,h)]=prep
            v=d['contrast']; w=mm(v,prep['W']);G=d['groups'];ng=len(pp);n=len(w)
            U=np.array([w*(G==g) for g in range(ng)])
            # Cluster score = c' W_g (I-QQ'-RZ W) y, with exact CR1 factor.
            scoreW=U-mm(mm(U,prep['Q']),prep['Q'].T)-mm(mm(U,prep['RZ']),prep['W'])
            scoreW*=np.sqrt(ng/(ng-1)*(n-1)/(n-prep['p']))
            temp=np.zeros((1,total));put_series_kernel(temp,w,d,key_index)
            lagK[h-1]=temp[0];K+=temp[0]/5
            temp=np.zeros((ng,total));put_series_kernel(temp,scoreW,d,key_index);scores+=temp/5
        sets.append(dict(file=file,K=K,scores=scores,lagK=lagK,ds=ds))
    return dict(sets=sets,K=sum(s['K'] for s in sets)/2,
                lagK=sum(s['lagK'] for s in sets)/2,
                scores=np.vstack([s['scores']/2 for s in sets]),
                masks=masks,preps=preps,key_index=key_index,omit=omit,
                people=people)


def estimate(op,series):
    yy=np.nan_to_num(series).reshape(-1)
    est=float(mm(op['K'],yy));scores=mm(op['scores'],yy)
    variances=[float(mm(scores[:10],scores[:10])),float(mm(scores[10:],scores[10:]))]
    se=float(np.sqrt(sum(variances)));df=sum(variances)**2/sum(v*v/9 for v in variances) if se>0 else 18.
    q=stats.t.ppf(.975,df)
    return dict(estimate=est,se=se,df=df,set_variances=variances,low=est-q*se,high=est+q*se,
                curve=mm(op['lagK'],yy).tolist())


def event_truth(op,kind,effect,scales,gains=(.65,.20)):
    # Direct structural four-way old c=+4/-4,j=0 x index jump/no jump.
    # Later actual input schedules are held fixed. Each person contributes
    # equally; set and five future horizons also receive equal weight.
    curves=[]
    a=.65;b=gains[0];delta=effect/(b*np.mean(a**np.arange(5)))
    for p,scale in zip(op['people'],scales):
        d=op['preps'][(p['file'],1)]['d']
        events=[tn-1 for key,tn,_,_ in d['meta'] if key==p['key']]
        vals=[]
        for t in events:
            if kind in ['retention','perceived_error','expression_storage_equivalent']:
                v=delta*b*scale;curve=[]
                for h in range(1,6):
                    curve.append(v)
                    v*=a+delta*float(p['c'][t+h]==0 and p['j'][t+h]!=0)
            elif kind=='expression_next':curve=[delta*b*scale,0,0,0,0]
            elif kind=='rebound':curve=[delta*b*scale,-delta*b*scale,0,0,0]
            else:curve=[0]*5
            vals.append(curve)
        curves.append(np.mean(vals,axis=0))
    return np.mean(curves,axis=0)


def verify_operator(op):
    rng=np.random.default_rng(8319);synthetic=rng.normal(size=(20,824))
    summaries=[]
    for f in FILES:
        fits=[]
        for h in range(1,6):
            prep=op['preps'][(f,h)];d=prep['d'];Y=[]
            for key,tn,_,_ in d['meta']:
                y=synthetic[op['key_index'][key]];t=tn-1
                Y.append(y[t+h]-y[t-5:t].mean())
            fits.append(fit(prep,np.array(Y)))
        summaries.append(curve_summary(fits))
    normal=pooled_summary(summaries);fast=estimate(op,synthetic)
    for k in ['estimate','se','low','high']:assert abs(normal[k]-fast[k])<1e-10,(k,normal[k],fast[k])
    return dict(max_error=max(abs(normal[k]-fast[k]) for k in ['estimate','se','low','high']),normal=normal,operator=fast)


def simulate_scenario(op,kind,effect,reps,seed,gains=(.65,.20)):
    rows=[];rng=np.random.default_rng(seed)
    mean_reference=[];directs=[]
    for p in op['people']:
        g=generate(p['c'],p['j'],kind=kind,effect=effect,gains=gains,noise_sd=0,drift_scale=0,process_sd=0)
        direct=.035*p['j']-.025*p['c']
        if kind=='online':direct+=.04*p['c']*(p['j']!=0)
        mean_reference.append(g['clean']);directs.append(direct)
    for rep in range(reps):
        scales=np.exp(.20*rng.normal(size=20)-.5*.20**2)
        noise_scales=np.exp(.15*rng.normal(size=20)-.5*.15**2)
        y=[];clean=[]
        for i,p in enumerate(op['people']):
            g=generate(p['c'],p['j'],seed=seed+10000+rep*20+i,kind=kind,
                  effect=effect,gains=gains,noise_sd=3*noise_scales[i],person_scale=scales[i],
                  drift_scale=.6,process_sd=.08,empirical_mask=op['masks'][p['key']])
            y.append(g['y']);clean.append(scales[i]*(mean_reference[i]-directs[i])+directs[i])
        e=estimate(op,np.array(y));proj=estimate(op,np.array(clean))['estimate']
        physical=event_truth(op,kind,effect,scales,gains);truth=float(physical.mean())
        rows.append(dict(rep=rep,truth=truth,isolated_reference_effect=effect,gains=list(gains),noiseless_projection=proj,
                         structural_curve=physical.tolist(),**e))
        if rep and rep%100==0:print(kind,effect,'rep',rep,flush=True)
    return rows


def summarize(rows):
    a=np.array([r['estimate'] for r in rows]);t=np.array([r['truth'] for r in rows]);
    pr=np.array([r['noiseless_projection'] for r in rows]);lo=np.array([r['low'] for r in rows]);hi=np.array([r['high'] for r in rows]);se=np.array([r['se'] for r in rows]);
    detect=(lo>0)|(hi<0);correct=detect&(np.sign(a)==np.sign(t))
    def rate(x):
        n=len(x);k=int(np.sum(x));ci=stats.binomtest(k,n).proportion_ci(confidence_level=.95)
        return dict(rate=k/n,n=k,total=n,binomial95=[float(ci.low),float(ci.high)])
    return dict(replicates=len(rows),mean_estimate=float(a.mean()),mean_physical_truth=float(t.mean()),
                mean_noiseless_projection=float(pr.mean()),bias_to_physical=float((a-t).mean()),
                mean_projection_bias=float((pr-t).mean()),rmse=float(np.sqrt(np.mean((a-t)**2))),
                empirical_sd=float(a.std(ddof=1)),mean_se=float(se.mean()),
                coverage_physical=rate((lo<=t)&(hi>=t)),coverage_noiseless_projection=rate((lo<=pr)&(hi>=pr)),
                reject_zero=rate(detect),correct_sign_detection=rate(correct),
                intervals_inside_02=rate((lo>-.2)&(hi<.2)),
                falsely_inside_02_at_or_beyond_margin=rate((lo>-.2)&(hi<.2)&(np.abs(t)>=.2)),
                mean_curve=np.mean([r['curve'] for r in rows],axis=0).tolist(),
                physical_curve=np.mean([r['structural_curve'] for r in rows],axis=0).tolist())


def linear_control(op,effect,reps,seed):
    # Correctly specified event-level linear model, distinct from a physical
    # chronological generator. Shared 5-lag cluster errors test joint CI code.
    # For each lag the same rows are present and groups identical.
    rng=np.random.default_rng(seed);rows=[]
    for r in range(reps):
        summaries=[]
        for f in FILES:
            p0=op['preps'][(f,1)];d0=p0['d'];n=len(d0['Y']);g=d0['groups'];
            shared=rng.normal(size=n)*2.5;group_slope=rng.normal(size=10)*.10
            fits=[]
            for h in range(1,6):
                prep=op['preps'][(f,h)];d=prep['d'];beta=2*effect*d['contrast']
                # contrast has entries +.5/-.5, so c'(2effect*c)=effect.
                mean=mm(d['Z'],beta)
                mean+=mm(d['Z'],2*d['contrast'])*group_slope[g]
                # Arbitrary nuisance exactly within N; never fit on outcomes.
                mean+=d['NF'][:,0]*.4+d['NF'][:,4]*.3
                y=mean+shared+rng.normal(size=n)*1.0
                fits.append(fit(prep,y))
            summaries.append(curve_summary(fits))
        ans=pooled_summary(summaries)
        rows.append(dict(rep=r,truth=effect,noiseless_projection=effect,structural_curve=[effect]*5,**ans))
    return rows


def run(reps=300):
    outdir=ROOT/'outputs/recovery';outdir.mkdir(exist_ok=True)
    t0=time.time();people=load('validation',inputs_only=True);op=build_operators(people,.03)
    verification=verify_operator(op)
    source=(ROOT/'outputs/development_Hand_raw_change_all.json').read_bytes()
    dev=json.loads(source)
    summary=dict(scope='Validation INPUT schedules only; empirical validation outcomes never read',
         seed=819281,replicates=reps,analysis_sha256=hashlib.sha256((ROOT/'experiments/analysis.py').read_bytes()).hexdigest(),
         noise_calibration=dict(source='development_Hand_raw_change_all.json',sha256=hashlib.sha256(source).hexdigest(),
           development_residual_sd={f:[v['residual_sd'] for v in dev[f]['lags']] for f in FILES},
           simulation_endpoint_noise_sd=3.0,rationale='Conservative: 3 degrees at each endpoint before pre-window subtraction, compared with development differenced residual SD 2.79–3.09 degrees.'),
         omissions=dict(rate=.03,mask_seed=194192,rule='Independent fixed outcome mask; all chronological state updates retained. Conditional-on-mask recovery.'),
         inference='Welch–Satterthwaite df from independent set-level variances and 9 person-cluster degrees each.',
         operator_verification=verification,scenarios={})
    cases=[('two_timescale',0),('gain_only',0),('online',0),('expression_current',.2),
           ('retention',-.2),('retention',.2),('expression_next',.2),('rebound',.2)]
    for k,(kind,effect) in enumerate(cases):
        name=kind+('_negative' if effect<0 else '_positive' if effect>0 else '_null')
        print('START',name,flush=True)
        rows=simulate_scenario(op,kind,effect,reps,819281+k*100000)
        (outdir/(name+'.json')).write_text(json.dumps(rows,indent=2)+'\n')
        summary['scenarios'][name]=summarize(rows)
        (outdir/'summary.json').write_text(json.dumps(jsonable(summary),indent=2)+'\n')
        print('RESULT',name,json.dumps(summary['scenarios'][name]),flush=True)
    # Calibrate the *actual-schedule* physical scalar to the unchanged .2°
    # margin. A larger but fixed fast gain keeps negative modulation within
    # nonnegative transitions; this is an additional declared generator.
    for k,target in enumerate([-.2,.2]):
        gains=(.90,.20)
        effect=optimize.brentq(lambda e:event_truth(op,'retention',e,np.ones(20),gains).mean()-target,-.29,.25)
        name='actual_margin_'+('negative' if target<0 else 'positive')
        print('START',name,'calibrated isolated effect',effect,flush=True)
        rows=simulate_scenario(op,'retention',effect,reps,819281+(8+k)*100000,gains=gains)
        (outdir/(name+'.json')).write_text(json.dumps(rows,indent=2)+'\n')
        summary['scenarios'][name]=dict(summarize(rows),isolated_reference_effect=effect,gains=list(gains),physical_reference_target=target)
        (outdir/'summary.json').write_text(json.dumps(jsonable(summary),indent=2)+'\n')
        print('RESULT',name,json.dumps(summary['scenarios'][name]),flush=True)
    # One event-level correctly specified null and both signed alternatives.
    for k,effect in enumerate([0.,-.2,.2]):
        name='specified_linear_'+str(effect)
        rows=linear_control(op,effect,reps,918120+k*100000)
        (outdir/(name+'.json')).write_text(json.dumps(rows,indent=2)+'\n')
        summary['scenarios'][name]=summarize(rows)
        (outdir/'summary.json').write_text(json.dumps(jsonable(summary),indent=2)+'\n')
        print('RESULT',name,json.dumps(summary['scenarios'][name]),flush=True)
    summary['seconds']=time.time()-t0
    (outdir/'summary.json').write_text(json.dumps(jsonable(summary),indent=2)+'\n')
    with (outdir/'summary.csv').open('w',newline='') as f:
        cols=['scenario','mean_estimate','mean_physical_truth','mean_noiseless_projection','bias_to_physical','empirical_sd','mean_se','coverage_physical','reject_zero','correct_sign_detection','intervals_inside_02']
        w=csv.DictWriter(f,fieldnames=cols);w.writeheader()
        for name,s in summary['scenarios'].items():
            row={'scenario':name}
            for c in cols[1:]:row[c]=s[c]['rate'] if isinstance(s[c],dict) else s[c]
            w.writerow(row)
    return summary

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--reps',type=int,default=300);a=ap.parse_args();run(a.reps)
