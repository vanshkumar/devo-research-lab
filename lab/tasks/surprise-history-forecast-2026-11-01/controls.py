"""Frozen conditional fixed-feature null/positive controls; no human simulation."""
from data import ROOT,wrap
from model import LAMBDAS,design,circular_loss,person_means
from evaluate import gains
import datetime,json,resource
import numpy as np

def prep(X,ids,Xval):
    unique,inverse,counts=np.unique(ids,return_inverse=True,return_counts=True)
    w=1/counts[inverse];w/=w.sum()
    mean=np.sum(X*w[:,None],axis=0);sd=np.sqrt(np.sum((X-mean)**2*w[:,None],axis=0));sd[sd<1e-10]=1
    z=np.column_stack([np.ones(len(X)),(X-mean)/sd])
    zv=np.column_stack([np.ones(len(Xval)),(Xval-mean)/sd])
    gram=np.einsum('ni,n,nj->ij',z,w,z,optimize=False)
    inverses=[]
    for lam in LAMBDAS:
        pen=np.eye(z.shape[1])*lam/len(unique);pen[0,0]=0
        inverses.append(np.linalg.solve(gram+pen,np.eye(len(gram))))
    return dict(z=z,zv=zv,w=w,inverses=inverses)

def cache(d,e,which):
    X=design(d,which);Xe=design(e,which);ids=d['keys'][:,0]
    fold={v:j%5 for j,v in enumerate(np.unique(ids))}
    folds=[]
    for k in range(5):
        val=np.array([fold[v]==k for v in ids]);train=~val
        folds.append((train,val,prep(X[train],ids[train],X[val])))
    return dict(folds=folds,full=prep(X,ids,Xe))

def cached_predict(pre,y,lamidx):
    Y=np.column_stack([np.cos(y),np.sin(y)])
    rhs=np.einsum('ni,n,nj->ij',pre['z'],pre['w'],Y,optimize=False)
    coef=np.einsum('ij,jk->ik',pre['inverses'][lamidx],rhs,optimize=False)
    v=np.einsum('ni,ij->nj',pre['zv'],coef,optimize=False)
    hat=np.arctan2(v[:,1],v[:,0]);hat[np.linalg.norm(v,axis=1)<1e-12]=0
    return hat

def refit(pre,y,ids):
    losses=[]
    for j in range(len(LAMBDAS)):
        hat=np.empty(len(y))
        for train,val,part in pre['folds']:hat[val]=cached_predict(part,y[train],j)
        losses.append(float(person_means(circular_loss(y,hat),ids).mean()))
    j=int(np.argmin(losses))
    return cached_predict(pre['full'],y,j),LAMBDAS[j]

def noise(keys,rng):
    result=np.empty(len(keys));ids=np.unique(keys[:,0]);bias={sid:rng.normal(0,.1) for sid in ids}
    last=None;state=0
    for t,key in enumerate(keys):
        group=tuple(key[:3])
        if group!=last:state=rng.normal(0,.5);last=group
        else:state=.35*state+rng.normal(0,.5*np.sqrt(1-.35**2))
        result[t]=bias[key[0]]+state
    return result

def main():
    assert not (ROOT/'CONTROLS.json').exists()
    d=dict(np.load(ROOT/'development_features.npz'));e=dict(np.load(ROOT/'evaluation_features.npz'))
    # This prescribed H state is past absolute error (.25 EMA) in both contexts.
    signal_d=d['extra'][:,0]+d['extra'][:,24]
    signal_e=e['extra'][:,0]+e['extra'][:,24]
    B=d['B'];mean=B.mean(axis=0);sd=B.std(axis=0);sd[sd<1e-10]=1
    z=np.column_stack([np.ones(len(B)),(B-mean)/sd]);ze=np.column_stack([np.ones(len(e['B'])),(e['B']-mean)/sd])
    g=np.einsum('ni,nj->ij',z,z,optimize=False)
    rhs=np.einsum('ni,n->i',z,signal_d,optimize=False)
    pen=np.eye(g.shape[0])*.001;pen[0,0]=0
    coef=np.linalg.solve(g+pen,rhs)
    rd=signal_d-np.einsum('ni,i->n',z,coef,optimize=False)
    re=signal_e-np.einsum('ni,i->n',ze,coef,optimize=False)
    scale=rd.std();assert scale>1e-6
    hd=np.clip(rd/scale,-3,3);he=np.clip(re/scale,-3,3)
    prepared={which:cache(d,e,which) for which in ['B','H']}
    out=dict(started_at=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope='Conditional on the fixed original feature matrices; inputs/response histories do not regenerate with synthetic updates. Not human trajectories or a biological power calculation.',null_mean='current PE, exactly representable as a unit complex conditional mean by B',positive_mean='current PE + .35 * clipped[-3,3] standardized residual past-absolute-error state; residual projection fitted on development features only',noise='person normalSD.1rad plus block/context-restarted stationary AR1 rho.35 SD.5rad, independent of fixed features',signal_training_sd=float(scale),rows=[],summary={})
    for label,beta,offset in [('null',0.,0),('positive',.35,10000)]:
        records=[]
        for rep in range(100):
            seed=20261101+offset+rep;rng=np.random.default_rng(seed)
            md=wrap(d['diagnostics'][:,0]+beta*hd);me=wrap(e['diagnostics'][:,0]+beta*he)
            yd=wrap(md+noise(d['keys'],rng));ye=wrap(me+noise(e['keys'],rng))
            forecasts={};lams={}
            for which in ['B','H']:forecasts[which],lams[which]=refit(prepared[which],yd,d['keys'][:,0])
            check=gains(e['keys'],ye,forecasts['B'],forecasts['H'],seed=seed+30000,reps=10000)
            check.update(label=label,rep=rep,seed=seed,lambdas=lams,oracle_loss=float(person_means(circular_loss(ye,me),e['keys'][:,0]).mean()),current_PE_oracle_loss=float(person_means(circular_loss(ye,e['diagnostics'][:,0]),e['keys'][:,0]).mean()))
            records.append(check)
            if rep==0:np.savez(ROOT/('control_'+label+'_example.npz'),keys=e['keys'],y=ye,mean=me,B=forecasts['B'],H=forecasts['H'])
            if rep%20==0:print(label,rep,'passes',sum(r['passes'] for r in records),flush=True)
        out['rows'].extend(records)
        out['summary'][label]=dict(passes=sum(r['passes'] for r in records),n=100,mean_gain=float(np.mean([r['gain'] for r in records])),mean_oracle_loss=float(np.mean([r['oracle_loss'] for r in records])),mean_current_PE_oracle_loss=float(np.mean([r['current_PE_oracle_loss'] for r in records])))
    out['ended_at']=datetime.datetime.now(datetime.timezone.utc).isoformat()
    out['peak_rss_bytes']=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    out['calibration_rule']='Positive>=80/100 and null<=10/100 are a finite fixed-generator interpretation check, not confidence guarantees.'
    out['calibration_passes']=out['summary']['positive']['passes']>=80 and out['summary']['null']['passes']<=10
    (ROOT/'CONTROLS.json').write_text(json.dumps(out,indent=2))
    print(json.dumps({k:v for k,v in out.items() if k!='rows'},indent=2))

if __name__=='__main__':main()
