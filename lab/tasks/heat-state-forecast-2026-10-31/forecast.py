"""Small autonomous across-animal heat forecasts; no post-heat observations as inputs."""
import os
os.environ['OPENBLAS_NUM_THREADS']='1'
os.environ['OMP_NUM_THREADS']='1'
import argparse,datetime,hashlib,json,pathlib
import numpy as np
TASK=pathlib.Path(__file__).resolve().parent
ROOT=TASK.parents[2]
SRC=ROOT/'sources/heat_state_forecast_2026-10-31'
BINS=np.arange(30.,451.,60.)
ALPHAS=[.01,.1,1.,10.,100.]
SIMPLE=['persistence','recent','shared','relative','shared_constant','relax5','relax30','relax120']
def now(): return datetime.datetime.now(datetime.timezone.utc).isoformat()
def save(name,obj): (TASK/name).write_text(json.dumps(obj,indent=2,allow_nan=False)+'\n')
def load_development():
    sp=json.loads((TASK/'SPLIT.json').read_text())
    out=[]
    for x in sp['items']:
        if x['part']=='development':
            with np.load(SRC/('derived_'+x['uid']+'.npz')) as z:
                d={k:z[k].copy() for k in z.files}
            d['uid']=x['uid'];out.append(d)
    return out
def class_selection(ds):
    allc=sorted(set(c for d in ds for c in d['classes'].tolist()))
    counts={c:sum(c in d['classes'] for d in ds) for c in allc}
    return [c for c in allc if counts[c]>=10],counts
def one_channel(v,t,ratio=None):
    pre=(t>=-450)&(t<-5)
    recent=(t>=-65)&(t<-5)
    early=(t>=-450)&(t<-330)
    late=(t>=-125)&(t<-5)
    mu=float(np.mean(v[pre]));last=float(np.mean(v[recent]))
    drift=float(np.mean(v[late])-np.mean(v[early]))
    lag=int(round(30./np.median(np.diff(t))))
    vv=v[pre]-mu
    den=float(np.dot(vv,vv))
    ac=float(np.dot(vv[:-lag],vv[lag:])/den) if den>1e-15 else 0.
    cv=float(np.std(ratio[pre])) if ratio is not None else float(np.std(v[pre])/(abs(mu)+.1))
    return [mu,last,drift,ac,cv]
def make_bundle(ds,classes,mode,with_outcomes=True):
    n=len(ds);c=len(classes) if mode=='neural' else 2
    X=np.full((n,c,5),np.nan); Y=np.full((n,c,7),np.nan)
    G=np.empty((n,2)); R=np.full((n,len(classes)),np.nan)
    for i,d in enumerate(ds):
        t=d['t']; pre=(t>=-450)&(t<-5)
        assert np.any(pre) and max(t[pre])<0
        G[i]=[np.mean(d['behavior'][1,pre]),np.mean(d['behavior'][2,pre])]
        for k,cl in enumerate(classes):
            wh=np.where(d['classes']==cl)[0]
            if len(wh): R[i,k]=one_channel(d['neural'][wh[0]],t,d['ratio'][wh[0]])[1]
        for k in range(c):
            if mode=='neural':
                wh=np.where(d['classes']==classes[k])[0]
                if not len(wh): continue
                v=d['neural'][wh[0]];ratio=d['ratio'][wh[0]]
            else:
                v=d['behavior'][k+1];ratio=None
            X[i,k]=one_channel(v,t,ratio)
            if with_outcomes:
                for b in range(7):
                    use=(t>=BINS[b])&(t<BINS[b+1])
                    assert np.any(use)
                    Y[i,k,b]=np.mean(v[use])
    return dict(X=X,Y=Y,G=G,R=R,mode=mode,uids=[d['uid'] for d in ds])
def global_features(train,test):
    m=np.nanmean(train['R'],axis=0)
    a=np.where(np.isfinite(train['R']),train['R'],m)-m
    z=np.where(np.isfinite(test['R']),test['R'],m)-m
    _,_,vh=np.linalg.svd(a,full_matrices=False)
    pc=vh[:2].T
    return np.concatenate([train['G'],np.einsum('ij,jk->ik',a,pc)],axis=1),np.concatenate([test['G'],np.einsum('ij,jk->ik',z,pc)],axis=1)
def ridge(x,y,z,alpha):
    m=x.mean(axis=0);sd=x.std(axis=0);sd[sd<1e-10]=1.
    a=(x-m)/sd;zz=(z-m)/sd;ym=y.mean(axis=0)
    lhs=np.einsum('ij,ik->jk',a,a)+alpha*len(a)*np.eye(a.shape[1])
    rhs=np.einsum('ij,ik->jk',a,y-ym)
    coef=np.linalg.solve(lhs,rhs)
    return ym+np.einsum('ij,jk->ik',zz,coef)
def subset(b,idx):
    return {k:(v[idx] if isinstance(v,np.ndarray) else v) for k,v in b.items()}
def simple_base(X,model):
    n,c,_=X.shape
    if model in ['persistence','relative']: out=np.repeat(X[:,:,0,None],7,axis=2)
    elif model=='recent':out=np.repeat(X[:,:,1,None],7,axis=2)
    elif model.startswith('relax'):
        tau=float(model[5:]);q=tau/60*(np.exp(-BINS[:-1]/tau)-np.exp(-BINS[1:]/tau))
        out=X[:,:,0,None]+(X[:,:,1]-X[:,:,0])[:,:,None]*q
    else:out=np.zeros((n,c,7))
    return out
def predict(train,test,model,alpha=None):
    Y=train['Y']; out=np.full((len(test['X']),Y.shape[1],7),np.nan)
    if model in ['local','state']:
        if model=='state':gt,ge=global_features(train,test)
        for c in range(Y.shape[1]):
            ok=np.isfinite(train['X'][:,c]).all(axis=1)&np.isfinite(Y[:,c]).all(axis=1)
            te=np.isfinite(test['X'][:,c]).all(axis=1)
            x=train['X'][ok,c];z=test['X'][te,c]
            if model=='state':x=np.concatenate([x,gt[ok]],axis=1);z=np.concatenate([z,ge[te]],axis=1)
            assert len(x)>=5
            out[te,c]=ridge(x,Y[ok,c],z,alpha)
    else:
        out=simple_base(test['X'],model)
        if model in ['shared','relative','shared_constant'] or model.startswith('relax'):
            residual=Y-simple_base(train['X'],model)
            curve=np.nanmean(residual,axis=0)
            if model=='shared_constant':curve=np.repeat(np.nanmean(curve,axis=1)[:,None],7,axis=1)
            out+=curve
    if train['mode']=='behavior':
        out[:,0]=np.clip(out[:,0],0,1)
        out[:,1]=np.maximum(out[:,1],0)
    return out
def losses(pred,y,scale):
    e=((pred-y)/np.asarray(scale)[None,:,None])**2
    return np.nanmean(e,axis=(1,2))
def cv_predict(b,model,alpha=None):
    out=np.full_like(b['Y'],np.nan)
    for i in range(len(out)):
        tr=np.array([j for j in range(len(out)) if i!=j]);te=np.array([i])
        out[i]=predict(subset(b,tr),subset(b,te),model,alpha)[0]
    return out
def run_dev():
    ds=load_development();classes,counts=class_selection(ds)
    # Scales are fixed from development prefixes, never evaluation responses.
    bstd=[]
    for d in ds:
        p=(d['t']>=-450)&(d['t']<-5)
        bstd.append(np.std(d['behavior'][1:3,p],axis=1))
    scales={'neural':[1.]*len(classes),'behavior':np.maximum(np.mean(bstd,axis=0),[.05,.1]).tolist()}
    result=dict(at_utc=now(),classes=classes,class_counts=counts,bins=BINS.tolist(),scales=scales,uids=[d['uid'] for d in ds],modalities={})
    arrays={}
    for mode in ['neural','behavior']:
        b=make_bundle(ds,classes,mode)
        scores={};configs={};predictions={}
        for model in SIMPLE+['local','state']:
            aa=ALPHAS if model in ['local','state'] else [None]
            choices=[]
            for a in aa:
                p=cv_predict(b,model,a);ls=losses(p,b['Y'],scales[mode]);key=model if a is None else model+'_'+str(a)
                scores[key]=dict(mean=float(np.mean(ls)),per_worm=ls.tolist())
                predictions[key]=p
                choices.append((float(np.mean(ls)),a,key))
            best=min(choices,key=lambda z:z[0]);configs[model]=dict(alpha=best[1],key=best[2],cv_mse=best[0])
        simple=min([m for m in configs if m!='state'],key=lambda m:configs[m]['cv_mse'])
        st=configs['state'];ss=configs[simple]
        own=configs['local']
        result['modalities'][mode]=dict(configs=configs,all_scores=scores,strongest_simple=simple,state_gain_over_simple=1-st['cv_mse']/ss['cv_mse'],state_gain_over_local=1-st['cv_mse']/own['cv_mse'],state_gain_over_shared=1-st['cv_mse']/configs['shared']['cv_mse'])
        arrays[mode+'_truth']=b['Y'];arrays[mode+'_own_features']=b['X'];arrays[mode+'_global_features']=b['G'];arrays[mode+'_recent_neural']=b['R']
        for k,p in predictions.items():arrays[mode+'__'+k]=p
        print(json.dumps(dict(mode=mode,classes=len(classes),strongest_simple=simple,configs=configs,state_gain_over_simple=result['modalities'][mode]['state_gain_over_simple'])),flush=True)
    np.savez_compressed(TASK/'DEVELOPMENT_CV.npz',**arrays)
    save('DEVELOPMENT_RESULT.json',result)
if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--development',action='store_true');a=ap.parse_args()
    if a.development:run_dev()
