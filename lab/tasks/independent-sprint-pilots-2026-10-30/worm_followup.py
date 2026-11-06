"""Exploratory strong-local-family and finite-history falsification follow-up."""
import os,sys
sys.dont_write_bytecode=True
for k in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','VECLIB_MAXIMUM_THREADS'):os.environ[k]='2'
import csv,json
from io import BytesIO
import numpy as np
from scipy import linalg
from common import ROOT,HERE,SOURCE,read,save
from worm_pilot import local_predictions,population_predictions,mse,mm

def choose(rows):
    out=[]
    for uid in sorted({r['uid'] for r in rows}):
        g={r['method']:r for r in rows if r['uid']==uid and float(r['seconds'])==3}
        local=min((g[k] for k in ('persistence','local_current','local_lags')),key=lambda r:float(r['validation_mse']))
        pop=min((g[k] for k in ('population_current','population_lags','local_plus_pc5')),key=lambda r:float(r['validation_mse']))
        joint=min((local,pop),key=lambda r:float(r['validation_mse']))
        out.append({'uid':uid,'selected_local':local['method'],'local_test_mse':float(local['mse']),
                    'selected_population':pop['method'],'population_test_mse':float(pop['mse']),
                    'selected_with_fallback':joint['method'],'population_gain':1-float(pop['mse'])/float(local['mse']),
                    'with_fallback_gain':1-float(joint['mse'])/float(local['mse'])})
    return out

def main():
    mainrows=list(csv.DictReader(read(HERE/'outputs/worm_main.csv','derived_result').decode().splitlines()))
    shiftrows=list(csv.DictReader(read(HERE/'outputs/worm_shifts.csv','derived_result').decode().splitlines()))
    families=choose(mainrows);nullfamilies=choose(shiftrows);ladder=[];checks=[]
    for i in range(6):
        d=np.load(BytesIO(read(SOURCE/('worm_%d.npz'%i),'consumed_derived_worm')),allow_pickle=False);x=d['x'];delta=float(d['dt']);uid=str(d['uid']);n,p=x.shape
        c1=int(.6*n);c2=int(.75*n);gap=int(np.ceil(30/delta));h=max(1,int(round(3/delta)))
        x=(x-x[:c1].mean(0))/x[:c1].std(0)
        tr=np.arange(50,c1-h-gap);va=np.arange(c1+gap,c2-h-gap);te=np.arange(c2+gap,n-h)
        y=x[tr+h]-x[tr];truth=x[va+h]
        assert va.min()-50>tr.max()+h and te.min()-50>va.max()+h
        for name,lags in [('lag1',[0]),('lag2',[0,1]),('lag5',[0,1,2,5,10]),('lag8',[0,1,2,5,10,20,35,50])]:
            f,v,t=[np.stack([x[idx-k] for k in lags],axis=-1) for idx in (tr,va,te)]
            local_predictions.truth=truth;pred,lam,val=local_predictions(f,y,v,t,x[va],x[te])
            ladder.append({'uid':uid,'method':name,'mse':mse(pred,x[te+h]),'validation_mse':val,'lambda':lam,'common_training_start':50})
        pred,lam,val=population_predictions(x[tr],y,x[va],x[te],x[va],x[te],truth)
        ladder.append({'uid':uid,'method':'population_current','mse':mse(pred,x[te+h]),'validation_mse':val,'lambda':lam,'common_training_start':50})
        ladder.append({'uid':uid,'method':'persistence','mse':mse(x[te],x[te+h]),'validation_mse':mse(x[va],truth),'lambda':0,'common_training_start':50})
        if i==0:
            # Independent direct linear solve of the population eigensolver result.
            a=x[tr]-x[tr].mean(0);b=y-y.mean(0);coef=linalg.solve(a.T@a+len(tr)*lam*np.eye(p),a.T@b,assume_a='pos')
            direct=x[te]+(x[te]-x[tr].mean(0))@coef+y.mean(0)
            err=float(np.max(np.abs(direct-pred)));assert err<1e-9
            checks.append({'independent_direct_solve_prediction_max_error':err})
    save('outputs/worm_followup.json',{'families':families,'shifted_families':nullfamilies,'history_ladder':ladder,'checks':checks,
                                      'interpretation':'selection uses middle-segment validation only; exploratory follow-up on consumed animals; no absence-of-information or independent replication claim'})
    print(json.dumps({'families':families,'real_median_gain':float(np.median([x['population_gain'] for x in families])),
                      'shifted_median_gain':float(np.median([x['population_gain'] for x in nullfamilies])),
                      'history_ladder':ladder,'checks':checks},indent=2))
if __name__=='__main__':main()
