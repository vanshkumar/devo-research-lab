"""Anchored current/history forecasts on six admitted, already-consumed worms."""
import os,sys
sys.dont_write_bytecode=True
for k in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','VECLIB_MAXIMUM_THREADS'):os.environ[k]='2'
import argparse,csv,json,hashlib,time
from pathlib import Path
import numpy as np
from scipy import linalg
from common import ROOT,HERE,SOURCE,read,load_json,save,now
LAM=np.array([.01,.1,1,10,100,1000,1e6])
LAGS=(0,1,2,5,10)
def mm(a,b):return linalg.blas.dgemm(1.,np.asarray(a,order='F'),np.asarray(b,order='F'))
def mse(a,b):return float(np.mean((a-b)**2))
def local_predictions(f,y,va,te,baseva,basete):
    mu=f.mean(0);dm=y.mean(0);a=f-mu;b=y-dm
    g=np.einsum('tnl,tnk->nlk',a,a);q=np.einsum('tnl,tn->nl',a,b)
    best=None
    for lam in LAM:
        coef=np.stack([linalg.solve(g[j]+np.eye(g.shape[-1])*len(f)*lam,q[j],assume_a='pos') for j in range(g.shape[0])])
        pv=baseva+np.einsum('tnl,nl->tn',va-mu,coef)+dm
        value=mse(pv[0] if False else pv,local_predictions.truth)
        if best is None or value<best[0]:best=(value,float(lam),coef)
    value,lam,coef=best
    return basete+np.einsum('tnl,nl->tn',te-mu,coef)+dm,lam,value
def population_predictions(f,y,va,te,baseva,basete,truth):
    mu=f.mean(0);dm=y.mean(0);a=f-mu;b=y-dm
    g=mm(a.T,a);q=mm(a.T,b)
    ev,u=linalg.eigh(g,check_finite=False);ev=np.maximum(ev,0)
    qt=mm(u.T,q);v=mm(va-mu,u);t=mm(te-mu,u);best=None
    for lam in LAM:
        c=qt/(ev[:,None]+len(f)*lam)
        value=mse(baseva+mm(v,c)+dm,truth)
        if best is None or value<best[0]:best=(value,float(lam),c)
    value,lam,c=best
    return basete+mm(t,c)+dm,lam,value

def forecasts(x,dt,uid,seconds=(.6,3,12,30),maxlag=10,pc=True):
    n,p=x.shape; c1=int(.6*n);c2=int(.75*n);gap=int(np.ceil(30/dt))
    if not np.isfinite(x).all():raise ValueError('Nonfinite admitted trace; do not select channels on future outcomes')
    mu=x[:c1].mean(0);sd=x[:c1].std(0);good=sd>1e-10;x=(x[:,good]-mu[good])/sd[good];p=x.shape[1]
    rows=[]
    for sec in seconds:
        h=max(1,int(round(sec/dt)));tr=np.arange(maxlag,c1-h-gap);va=np.arange(c1+gap,c2-h-gap);te=np.arange(c2+gap,n-h)
        assert len(va)>5 and tr[-1]+h<va[0] and va[-1]+h<te[0] and tr[0]>=maxlag
        y=x[tr+h]-x[tr];truth=x[va+h];test=x[te+h]
        rows.append(dict(uid=uid,seconds=sec,method='persistence',mse=mse(x[te],test),lambda_=0.,validation_mse=mse(x[va],truth),n_train=len(tr),n_test=len(te),neurons=p))
        features={}
        for name,lags in [('local_current',(0,)),('local_lags',LAGS)]:
            f=np.stack([x[tr-k] for k in lags],axis=-1);v=np.stack([x[va-k] for k in lags],axis=-1);t=np.stack([x[te-k] for k in lags],axis=-1)
            features[name]=(f,v,t);local_predictions.truth=truth
            pred,lam,val=local_predictions(f,y,v,t,x[va],x[te])
            rows.append(dict(uid=uid,seconds=sec,method=name,mse=mse(pred,test),lambda_=lam,validation_mse=val,n_train=len(tr),n_test=len(te),neurons=p))
        for name,lags in [('population_current',(0,)),('population_lags',LAGS)]:
            f=np.concatenate([x[tr-k] for k in lags],axis=1);v=np.concatenate([x[va-k] for k in lags],axis=1);t=np.concatenate([x[te-k] for k in lags],axis=1)
            pred,lam,val=population_predictions(f,y,v,t,x[va],x[te],truth)
            rows.append(dict(uid=uid,seconds=sec,method=name,mse=mse(pred,test),lambda_=lam,validation_mse=val,n_train=len(tr),n_test=len(te),neurons=p))
        if pc:
            a=x[tr]-x[tr].mean(0);_,u=linalg.eigh(mm(a.T,a));u=u[:,-min(5,p):]
            latent=[mm(x[idx]-x[tr].mean(0),u) for idx in (tr,va,te)]
            base=features['local_lags']
            f,v,t=[np.concatenate([base[k],np.broadcast_to(latent[k][:,None,:],(len(latent[k]),p,latent[k].shape[1]))],axis=2) for k in range(3)]
            local_predictions.truth=truth;pred,lam,val=local_predictions(f,y,v,t,x[va],x[te])
            rows.append(dict(uid=uid,seconds=sec,method='local_plus_pc5',mse=mse(pred,test),lambda_=lam,validation_mse=val,n_train=len(tr),n_test=len(te),neurons=p))
    return rows

def synthetic(seed,kind,n=1600,p=40):
    rng=np.random.default_rng(seed)
    if kind=='independent_ar':
        x=rng.normal(size=(n,p))
        for t in range(1,n):x[t]=.95*x[t-1]+.3*x[t]
        return x
    if kind=='independent_ar2':
        x=rng.normal(size=(n,p))*.2
        for t in range(2,n):x[t]=1.6*x[t-1]-.7*x[t-2]+.2*x[t]
        return x
    z=np.zeros((n,2));r=np.array([[np.cos(.12),-np.sin(.12)],[np.sin(.12),np.cos(.12)]])*.98
    for t in range(1,n):z[t]=r@z[t-1]+.12*rng.normal(size=2)
    return mm(z,rng.normal(size=(2,p)))+.2*rng.normal(size=(n,p))

def write_csv(name,rows):
    path=HERE/name;path.parent.mkdir(parents=True,exist_ok=True)
    with path.open('w') as f:
        writer=csv.DictWriter(f,fieldnames=list(rows[0]));writer.writeheader();writer.writerows(rows)

def summarize(rows):
    out=[]
    for uid in sorted(set(r['uid'] for r in rows)):
        for sec in sorted(set(r['seconds'] for r in rows)):
            group={r['method']:r for r in rows if r['uid']==uid and r['seconds']==sec}
            if not group:continue
            base=group['local_lags']['mse']
            out.append({'uid':uid,'seconds':sec,**{k:float(v['mse']) for k,v in group.items()},
                        'population_current_gain_vs_local_history':1-group['population_current']['mse']/base,
                        'population_history_gain_vs_local_history':1-group['population_lags']['mse']/base,
                        'pc5_gain_vs_local_history':1-group['local_plus_pc5']['mse']/base if 'local_plus_pc5' in group else 0})
    return out

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--stage',choices=['controls','main','shifts'],required=True);args=ap.parse_args();t0=time.monotonic()
    if args.stage=='controls':
        rows=[]
        for kind in ('rotation','independent_ar','independent_ar2'):
            for seed in range(5):rows+=forecasts(synthetic(seed,kind),.6,'%s_%d'%(kind,seed),seconds=(3,),pc=True)
        write_csv('outputs/worm_controls.csv',rows)
        out=summarize(rows);save('outputs/worm_controls.json',{'rows':out,'seconds':time.monotonic()-t0});print(json.dumps(out,indent=2));return
    if args.stage=='main':
        selected=load_json(ROOT/'experiments/neural_dynamics/selection.json')['discovery'];rows=[];reference=[]
        for i,item in enumerate(selected):
            p=ROOT/'data/public'/Path(item['path']).name;b=read(p,'consumed_worm')
            blob=hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest()
            if blob!=item['sha']:raise RuntimeError('Admitted worm blob mismatch')
            d=json.loads(b);x=np.array(d['trace_array'],dtype=float).T;ts=np.array(d['timestamp_confocal']);delta=float(np.median(np.diff(ts)))
            np.savez(SOURCE/('worm_%d.npz'%i),x=x,dt=delta,uid=d['uid'])
            if i==0:
                ref=forecasts(x,delta,d['uid'],maxlag=0,pc=False)
                reference=[r for r in ref if r['method'] in ('local_current','population_current')]
                old=list(csv.DictReader(read(ROOT/'experiments/causal_identification/neural_audit_check.csv').decode().splitlines()))
                for r in reference:
                    key='anchored_diagonal' if r['method']=='local_current' else 'anchored_population'
                    expected=next(float(v['test_mse']) for v in old if float(v['seconds'])==r['seconds'] and v['method']==key)
                    if abs(r['mse']-expected)>1e-8:raise RuntimeError('First-worm anchored reference mismatch')
            r=forecasts(x,delta,d['uid']);rows+=r
            write_csv('outputs/worm_main.csv',rows)
            print(json.dumps({'worm':i,'uid':d['uid'],'rows':len(r),'seconds':round(time.monotonic()-t0,2)}),flush=True)
        out=summarize(rows);save('outputs/worm_reference.json',reference);save('outputs/worm_main.json',{'results':out,'seconds':time.monotonic()-t0,'independent_units':6,'exposure':'all six are prior discovery/consumed; four reserved worms remain unopened'})
        print(json.dumps(out,indent=2));return
    rows=[];permcheck=None
    for i in range(6):
        p=SOURCE/('worm_%d.npz'%i);from io import BytesIO
        d=np.load(BytesIO(read(p,'consumed_derived_worm')),allow_pickle=False);x=d['x'];delta=float(d['dt']);uid=str(d['uid'])
        if i==0:
            a=forecasts(x,delta,uid,seconds=(3,));permutation=np.random.default_rng(711).permutation(x.shape[1]);b=forecasts(x[:,permutation],delta,uid,seconds=(3,));permcheck=max(abs(u['mse']-v['mse']) for u,v in zip(a,b));assert permcheck<1e-8
        for seed in (7100,7101,7102):
            rng=np.random.default_rng(seed);z=np.stack([np.roll(x[:,j],int(rng.integers(200,len(x)-200))) for j in range(x.shape[1])],axis=1)
            r=forecasts(z,delta,uid+'_shift'+str(seed),seconds=(3,));rows+=r
        print(json.dumps({'shift_worm':i,'seconds':time.monotonic()-t0}),flush=True)
    write_csv('outputs/worm_shifts.csv',rows);save('outputs/worm_shifts.json',{'results':summarize(rows),'channel_relabelling_max_mse_difference':permcheck,'seconds':time.monotonic()-t0,'caution':'independent circular shifts preserve univariate history but change temporal origin under nonstationarity'})
if __name__=='__main__':main()
