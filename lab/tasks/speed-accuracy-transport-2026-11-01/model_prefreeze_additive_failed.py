"""Compact conditional Wiener prescription and source-fixed empirical forecasts."""
import os
for _n in ['OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','VECLIB_MAXIMUM_THREADS','MKL_NUM_THREADS']:
    os.environ[_n]='1'
from pathlib import Path
import sys, json, hashlib, datetime, resource
import numpy as np
from scipy.special import expit, logit
from scipy.optimize import minimize
from numpy.polynomial.legendre import leggauss
ROOT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT/'deps'))
import rdata
W=np.array([1/6,1/6,1/6,1/2])
SIGMA=np.array([.6,.8,.10,.9,.9,.9,.9])
QUAD={n:leggauss(n) for n in [64,96,192,384]}
K=np.arange(1,33,dtype=float)
IM=np.arange(-5,6,dtype=float)

def stamp(): return datetime.datetime.now(datetime.timezone.utc).isoformat()
def dump(name,obj):
    (ROOT/name).write_text(json.dumps(obj,indent=2,default=lambda x:x.tolist() if isinstance(x,np.ndarray) else x.item()))
def load(name): return json.loads((ROOT/name).read_text())
def run_record(stage,charge=30000000):
    dump(stage+'_RESOURCE.json',{'at':stamp(),'read_decode_hash_charge_bytes':charge,'peak_rss_bytes_macos':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,'one_numerical_thread_env':True})

def data():
    df=rdata.read_rda(ROOT/'speed_acc.RData')['speed_acc']
    df.columns=[str(x) for x in df.columns]
    df['pid']=df.id.astype(str).astype(int)
    df['block']=df.block.astype(str).astype(int)
    for c in ['condition','response','stim_cat','frequency']:
        df[c]=df[c].astype(str)
    df['cat']=np.where(df.stim_cat=='nonword',3,df.frequency.map({'high':0,'low':1,'very_low':2}))
    assert df.cat.notna().all()
    df['cat']=df.cat.astype(int)
    df['upper']=(df.response=='word').astype(int)
    df['correct']=(df.response==df.stim_cat).astype(int)
    return df

def trials(df,pid,block,cutoff=(.18,3)):
    g=df[(df.pid==pid)&(df.block==block)].copy()
    assert len(g)==96,(pid,block,len(g))
    expected='speed' if block==1 else 'accuracy'
    assert set(g.condition)=={expected}
    rule=(~g.response.isin(['word','nonword']))|(~np.isfinite(g.rt))|(g.rt<.18)|(g.rt>3)
    assert np.array_equal(rule.to_numpy(),g.censor.to_numpy()),'Released censor rule mismatch'
    g=g[g.response.isin(['word','nonword'])&np.isfinite(g.rt)&g.rt.between(*cutoff)]
    return {'rt':g.rt.to_numpy(float),'cat':g.cat.to_numpy(int),'upper':g.upper.to_numpy(int),'correct':g.correct.to_numpy(int)}

def summary(g):
    ys=[];fs=[];counts=[]
    for c in range(4):
        ix=g['cat']==c; n=int(ix.sum()); assert n>=8,(c,n)
        rt=g['rt'][ix]; nc=int(g['correct'][ix].sum())
        ys.append([nc/n,float(rt.mean())]);counts.append(n)
        fs.append([(nc+.5)/(n+1),float(rt.mean()),float(rt.std(ddof=1)),float(g['correct'].mean()),float(g['rt'].mean()),float(g['rt'].std(ddof=1))])
    return np.array(ys),np.array(fs),np.array(counts)

def unpack(p):
    p=np.asarray(p,float)
    return np.exp(p[0]),expit(p[1]),p[2],np.exp(p[3:])*np.array([1,1,1,-1])

def fzero(t,a,d,mode='auto'):
    t=np.asarray(t,float);ans=np.zeros_like(t);ok=t>0
    small=ok&(t/a**2<.25) if mode=='auto' else ok if mode=='image' else np.zeros_like(ok)
    if np.any(small):
        tt=t[small,None];dd=d+2*a*IM[None,:]
        ans[small]=np.sum(dd*np.exp(-dd**2/(2*tt)),axis=1)/np.sqrt(2*np.pi*tt[:,0]**3)
    big=ok&~small
    if np.any(big):
        tt=t[big,None]
        ans[big]=np.pi/a**2*np.sum(K[None,:]*np.sin(K[None,:]*np.pi*d/a)*np.exp(-K[None,:]**2*np.pi**2*tt/(2*a*a)),axis=1)
    return np.maximum(ans,0)

def densities(rt,cat,p):
    a,z,t0,vs=unpack(p); t=np.asarray(rt)-t0; v=vs[np.asarray(cat)]
    lo=fzero(t,a,a*z)*np.exp(np.clip(-v*a*z-v*v*t/2,-700,700))
    hi=fzero(t,a,a*(1-z))*np.exp(np.clip(v*a*(1-z)-v*v*t/2,-700,700))
    return lo,hi

def integrals(p,n=96,cutoff=(.18,3)):
    a,z,t0,v=unpack(p);low=max(cutoff[0],t0)
    assert low<cutoff[1]
    x,w=QUAD[n];rt=(x+1)*(cutoff[1]-low)/2+low;w=w*(cutoff[1]-low)/2
    rr=np.tile(rt,4);cat=np.repeat(np.arange(4),n)
    lo,hi=densities(rr,cat,p);lo=lo.reshape(4,n);hi=hi.reshape(4,n)
    norm=np.sum((lo+hi)*w,axis=1)
    pc=np.sum(np.vstack([hi[:3],lo[3:]])*w,axis=1)/np.maximum(norm,1e-250)
    mrt=np.sum((lo+hi)*w*rt,axis=1)/np.maximum(norm,1e-250)
    return norm,np.column_stack([pc,mrt])

def nll(p,g):
    try:
        norm,_=integrals(p)
        lo,hi=densities(g['rt'],g['cat'],p)
        pdf=np.where(g['upper']>0,hi,lo)
        val=-np.sum(np.log(np.maximum(pdf,1e-250))-np.log(np.maximum(norm[g['cat']],1e-250)))
        return float(val) if np.isfinite(val) else 1e100
    except (AssertionError,FloatingPointError):return 1e100

def combine(gs): return {k:np.concatenate([g[k] for g in gs]) for k in gs[0]}
def baseline(g,center=None):
    tmax=min(float(np.min(g['rt']))-.005,.7)
    assert tmax>.03
    bounds=[(np.log(.25),np.log(4)),(logit(.15),logit(.85)),(.03,tmax)]+[(np.log(.05),np.log(12))]*4
    initial=np.array([np.log(1.4),0,min(.25,tmax-.01),np.log(3),np.log(2),np.log(1.2),np.log(2.5)]) if center is None else np.array(center,float)
    initial=np.array([np.clip(v,*b) for v,b in zip(initial,bounds)])
    fun=lambda p:nll(p,g)+(0 if center is None else .5*np.sum(((p-center)/SIGMA)**2))
    starts=[initial,initial+np.array([-.15,.1,-.015,.15,.15,.15,.15])]
    results=[]
    for st in starts:
        st=np.array([np.clip(v,*b) for v,b in zip(st,bounds)])
        rr=minimize(fun,st,method='L-BFGS-B',bounds=bounds,options={'maxiter':350,'ftol':1e-9,'gtol':1e-5})
        results.append(rr)
    best=min(results,key=lambda r:r.fun)
    return best.x,{'objective':float(best.fun),'success':bool(best.success),'message':str(best.message),'iterations':int(best.nit),'bounds_hit':[i for i,(v,b) in enumerate(zip(best.x,bounds)) if min(v-b[0],b[1]-v)<1e-5], 'starts_objectives':[float(r.fun) for r in results]}

def transport(p,m,quality=False):
    a,z,t0,vs=unpack(p);lower=a*z*np.exp(m[0]);upper=a*(1-z)*np.exp(m[1])
    q=np.array(p,float).copy();q[0]=np.log(lower+upper);q[1]=logit(lower/(lower+upper));q[2]+=m[2]
    if quality:q[3:]+=m[3]
    return q

def mapping(ps,targets,quality=False):
    dtlo=max(-.10,max(.03-p[2] for p in ps));dthi=min(.25,min(np.min(g['rt'])-.005-p[2] for p,g in zip(ps,targets)))
    assert dtlo<dthi,('No common physical t0 shift',dtlo,dthi)
    bounds=[(np.log(.5),np.log(3)),(np.log(.5),np.log(3)),(dtlo,dthi)]+([(np.log(.5),np.log(1.5))] if quality else [])
    def fun(m):return sum(nll(transport(p,m,quality),g) for p,g in zip(ps,targets))
    starts=[np.array([np.log(1.3),np.log(1.3),np.clip(0,dtlo,dthi)]+([0] if quality else [])),np.array([0,0,np.clip(.02,dtlo,dthi)]+([np.log(.9)] if quality else []))]
    rs=[minimize(fun,s,method='L-BFGS-B',bounds=bounds,options={'maxiter':250,'ftol':1e-9,'gtol':1e-5}) for s in starts]
    r=min(rs,key=lambda x:x.fun)
    return r.x,{'objective':float(r.fun),'success':bool(r.success),'message':str(r.message),'iterations':int(r.nit),'starts_objectives':[float(x.fun) for x in rs],'bounds':[list(b) for b in bounds],'bounds_hit':[i for i,(v,b) in enumerate(zip(r.x,bounds)) if min(v-b[0],b[1]-v)<1e-5]}

def clamp(y):
    y=np.array(y,float).copy(); y[...,0]=np.clip(y[...,0],.005,.995);y[...,1]=np.clip(y[...,1],.18,3);return y
def losses(pred,obs):
    sq=np.sum((pred-obs)**2*W[None,:,None],axis=1)
    return np.column_stack([sq,.5*np.sum(sq/.05**2,axis=1)])

def ridge_fit(F,Y,penalty):
    nf=F.reshape(-1,6);yy=Y.reshape(-1,2);mu=nf.mean(axis=0);sd=nf.std(axis=0);sd[sd<1e-8]=1
    cats=np.tile(np.eye(4),(len(F),1)); X=np.column_stack([cats,(nf-mu)/sd]);ww=np.tile(W,len(F))
    A=np.einsum('ni,nj,n->ij',X,X,ww)+np.diag([1e-8]*4+[penalty]*6)
    rhs=np.einsum('ni,nj,n->ij',X,yy,ww);coef=np.linalg.solve(A,rhs)
    return {'mean':mu.tolist(),'sd':sd.tolist(),'coef':coef.tolist(),'penalty':penalty}
def ridge_predict(F,r):
    nf=F.reshape(-1,6);X=np.column_stack([np.tile(np.eye(4),(len(F),1)),(nf-r['mean'])/r['sd']])
    return clamp(np.einsum('ni,ij->nj',X,np.array(r['coef'])).reshape(len(F),4,2))

def empirical(B,F,Y):
    cv={};penalties=[.01,.1,1,10,100]
    for name in ['POP','DELTA']+[f'RIDGE_{p}' for p in penalties]:
        pp=[]
        for i in range(len(Y)):
            train=np.arange(len(Y))!=i
            if name=='POP':p=Y[train].mean(axis=0)
            elif name=='DELTA':p=B[i]+(Y[train]-B[train]).mean(axis=0)
            else:p=ridge_predict(F[i:i+1],ridge_fit(F[train],Y[train],float(name[6:])))[0]
            pp.append(clamp(p))
        cv[name]=float(losses(np.array(pp),Y)[:,2].mean())
    bestpen=min(penalties,key=lambda p:cv[f'RIDGE_{p}']); best=min(['POP','DELTA',f'RIDGE_{bestpen}'],key=lambda k:cv[k])
    return {'POP':Y.mean(axis=0).tolist(),'DELTA':(Y-B).mean(axis=0).tolist(),'RIDGE':ridge_fit(F,Y,bestpen),'source_CV_joint_loss':cv,'reference':'RIDGE' if best.startswith('RIDGE') else best}

def empirical_predict(B,F,e):
    return {'IDENTITY':clamp(B),'POP':clamp(np.tile(e['POP'],(len(B),1,1))),'DELTA':clamp(B+e['DELTA']),'RIDGE':ridge_predict(F,e['RIDGE'])}

def freeze_pins(names):
    return {name:hashlib.sha256((ROOT/name).read_bytes()).hexdigest() for name in names}
