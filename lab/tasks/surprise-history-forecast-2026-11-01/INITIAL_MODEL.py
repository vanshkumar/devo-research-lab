"""Frozen candidate feature maps and circular ridge forecasts for this study."""
from data import ROOT, wrap
import numpy as np

LAMBDAS=[.001,.01,.1,1.,10.]

def approximate(pe,context,block,hazard=1/7):
    """Direct recurrence from pinned getTrialVarsFromPEs_cannon, radians."""
    n=len(pe);ru=np.empty(n);q=np.empty(n);alpha=np.empty(n)
    nv=.1;dv=0 if context else 1/30
    for t in range(n):
        if t==0 or block[t]!=block[t-1]:ru[t]=.99
        else:
            a,b,e=ru[t-1],q[t-1],pe[t-1]
            if context:num=b*nv+(1-b)*a*nv+b*(1-b)*(e*(1-a))**2
            else:
                r=(1-a)/a
                num=b*nv/r+(1-b)*nv/(r+1)+b*(1-b)*(e*a)**2
            num+=dv;ru[t]=num/(num+nv)
        total=nv/(1-ru[t])
        ps=(1-hazard)*np.exp(-pe[t]**2/(2*total))/np.sqrt(2*np.pi*total)
        pn=hazard/(2*np.pi);q[t]=pn/(ps+pn)
        alpha[t]=ru[t]+q[t]-ru[t]*q[t] if context else ru[t]*(1-q[t])
    return ru,q,alpha*pe

def grid_filter(outcome,context,block,grid=360):
    """Circular grid HMM; hidden safety counter is not an observed predictor.

    CP random means follow round(U*359); oddball random outcomes use the same
    rounded-uniform probabilities. VM kernels are quadrature approximations.
    """
    step=2*np.pi/grid;theta=np.arange(grid)*step
    # Integrate rounded observation bin using three-point Simpson quadrature.
    offsets=np.array([-.5,0,.5])*np.pi/180
    weights=np.array([1,4,1])/6
    def vm_kernel(kappa):
        v=np.exp(kappa*(np.cos(theta)-1));return v/v.sum()
    drift_fft=np.fft.rfft(vm_kernel(30))
    source_uniform=np.zeros(grid)
    nodes=np.rint(np.arange(360)*grid/360).astype(int)%grid
    source_uniform[nodes]=1/359
    source_uniform[nodes[[0,-1]]]=.5/359
    uniform_ob=np.ones(360)/359;uniform_ob[[0,-1]]=.5/359
    p=np.zeros((4,grid));p[0]=1/grid
    means=[];rs=[];events=[];minp=1.;maxnorm=0.
    for t,y in enumerate(outcome):
        fresh=t==0 or block[t]!=block[t-1]
        if context:
            if fresh:
                prior=np.zeros_like(p);prior[3]=source_uniform;evprior=prior[3].copy()
            else:
                prior=np.zeros_like(p)
                prior[0]=p[1]+.75*p[0]
                prior[1]=p[2];prior[2]=p[3]
                prior[3]=.25*p[0].sum()*source_uniform
                evprior=prior[3].copy()
        else:
            if fresh:
                counters=p.sum(axis=1) if t else np.array([1.,0,0,0])
                aimprior=counters[:,None]*np.ones((1,grid))/grid
            else:
                aimprior=np.fft.irfft(np.fft.rfft(p,axis=1)*drift_fft, n=grid,axis=1)
                aimprior=np.maximum(aimprior,0)
            prior=np.zeros_like(p)
            prior[0]=aimprior[1]+.75*aimprior[0]
            prior[1]=aimprior[2];prior[2]=aimprior[3]
            prior[3]=.25*aimprior[0]
            evprior=prior[3].copy()
        # Density integrated over the observed rounded-degree bin.
        lk=np.sum(weights[:,None]*np.exp(10*(np.cos(y+offsets[:,None]-theta)-1)),axis=0)
        # Kernel needs its circular-density constant to compare with uniforms.
        lk*= (np.pi/180)/(2*np.pi*np.i0(10)*np.exp(-10))
        post=prior*lk
        if not context:
            iy=int(np.rint(np.rad2deg(y)))%360
            post[3]=prior[3]*uniform_ob[iy]
        total=post.sum()
        eventmass=(evprior*lk).sum() if context else post[3].sum()
        p=post/total
        marginal=p.sum(axis=0)
        z=np.sum(marginal*np.exp(1j*theta))
        means.append(np.angle(z));rs.append(abs(z));events.append(eventmass/total)
        minp=min(minp,float(p.min()));maxnorm=max(maxnorm,abs(float(p.sum())-1))
    return np.asarray(means),np.asarray(rs),np.asarray(events),dict(min_probability=minp,max_norm_error=maxnorm,grid=grid)

def block_features(person):
    pred=person['pred'];out=person['outcome'];block=person['block'];c=person['context'];r=person['raw']
    pe=wrap(out-pred);ru,q,nup=approximate(pe,c,block)
    aim,resultant,event,filtercheck=grid_filter(out,c,block)
    up=wrap(pred[1:]-pred[:-1])
    bfeatures=[];hfeatures=[];targets=[];keys=[];diagnostics=[]
    es=np.zeros(2);qs=np.zeros(2)
    # Online gain is inferred only from earlier (PE, realized update) pairs.
    nums=np.array([.05,.05,.05]);dens=np.array([.1,.1,.1]);past_out=[]
    for t in range(len(pred)):
        new=t==0 or block[t]!=block[t-1]
        if new:
            start=t;es[:]=0;qs[:]=0;nums[:]=.05;dens[:]=.1;past_out=[]
        else:
            e0=pe[t-1];u0=wrap(pred[t]-pred[t-1])
            for j,a in enumerate([1.,.25,.0625]):
                if j==0:nums[j]+=e0*u0;dens[j]+=e0*e0
                else:nums[j]=(1-a)*nums[j]+a*e0*u0;dens[j]=(1-a)*dens[j]+a*e0*e0
            for j,a in enumerate([.25,.0625]):
                es[j]=(1-a)*es[j]+a*abs(e0)/np.pi
                qs[j]=(1-a)*qs[j]+a*q[t-1]
            past_out.append(out[t-1])
        lag1=wrap(pred[t]-pred[t-1]) if t>start else 0.
        lag2=wrap(pred[t-1]-pred[t-2]) if t>start+1 else 0.
        prevpe=pe[t-1] if t>start else 0.
        gains=np.clip(nums/dens,-1,2)
        base=[1.]
        for k in range(1,5):base.extend([np.sin(k*pe[t]),np.cos(k*pe[t])])
        base.extend([np.sin(nup[t]),np.cos(nup[t]),ru[t],q[t],ru[t]*np.sin(pe[t]),q[t]*np.sin(pe[t]),ru[t]*q[t]*np.sin(pe[t])])
        da=wrap(aim[t]-pred[t])
        base.extend([np.sin(da),np.cos(da),resultant[t],event[t],resultant[t]*np.sin(pe[t])])
        base.extend([float(r['hit'][t]),float(r['actRew'][t])-1,np.log1p(float(r['allASS'][t]))])
        for lag in [lag1,lag2,prevpe]:base.extend([np.sin(lag),np.cos(lag)])
        for g in gains:base.extend([np.sin(pe[t]*g),np.cos(pe[t]*g)])
        first=(int(r['cBal'][t])==2) if c else (int(r['cBal'][t])==1)
        base.extend([(t-start)/59,(int(block[t])-1)/3,float(first)])
        z4=np.mean(np.exp(1j*np.asarray(past_out[-4:]))) if past_out else 0j
        z16=np.mean(np.exp(1j*np.asarray(past_out[-16:]))) if past_out else 0j
        delta=np.angle(z4*np.conj(z16)) if past_out else 0.
        states=[*es,*qs,abs(z4),abs(z16),np.sin(delta),np.cos(delta) if past_out else 0.]
        hist=[]
        for v in states:hist.extend([v,v*np.sin(pe[t]),v*np.cos(pe[t])])
        if t+1<len(pred) and block[t+1]==block[t]:
            bv=np.asarray(base);hv=np.asarray(hist)
            bfeatures.append(np.concatenate([bv*(1-c),bv*c]))
            hfeatures.append(np.concatenate([hv*(1-c),hv*c]))
            targets.append(up[t]);keys.append([int(person['id']),c,int(block[t]),int(r['trial'][t])])
            diagnostics.append([pe[t],ru[t],q[t],nup[t],pred[t],out[t],float(r['hit'][t]),float(event[t])])
    return np.array(bfeatures),np.array(hfeatures),np.array(targets),np.array(keys),np.array(diagnostics),filtercheck

def assemble(people):
    pieces=[block_features(p) for p in people]
    return dict(B=np.concatenate([x[0] for x in pieces]),extra=np.concatenate([x[1] for x in pieces]),y=np.concatenate([x[2] for x in pieces]),keys=np.concatenate([x[3] for x in pieces]),diagnostics=np.concatenate([x[4] for x in pieces]),filterchecks=[x[5] for x in pieces])

def design(d,which):return d['B'] if which=='B' else np.column_stack([d['B'],d['extra']])
def circular_loss(y,hat):return 1-np.cos(y-hat)
def person_means(v,ids):return np.array([np.mean(v[ids==i]) for i in np.unique(ids)])

def fit(X,y,ids,lam):
    # Each person contributes total weight1, regardless of valid-row count.
    unique,inverse,counts=np.unique(ids,return_inverse=True,return_counts=True)
    weights=1/counts[inverse];weights/=weights.sum()
    mean=np.sum(X*weights[:,None],axis=0)
    scale=np.sqrt(np.sum((X-mean)**2*weights[:,None],axis=0));scale[scale<1e-10]=1
    Z=(X-mean)/scale;Z=np.column_stack([np.ones(len(X)),Z])
    Y=np.column_stack([np.cos(y),np.sin(y)])
    gram=np.einsum('ni,n,nj->ij',Z,weights,Z,optimize=False)
    rhs=np.einsum('ni,n,nj->ij',Z,weights,Y,optimize=False)
    penalty=np.eye(gram.shape[0])*lam/len(np.unique(ids));penalty[0,0]=0
    coef=np.linalg.solve(gram+penalty,rhs)
    assert np.all(np.isfinite(coef))
    return dict(mean=mean,scale=scale,coef=coef,lam=float(lam))

def predict(m,X):
    Z=np.column_stack([np.ones(len(X)),(X-m['mean'])/m['scale']])
    v=np.einsum('ni,ij->nj',Z,m['coef'],optimize=False)
    angle=np.arctan2(v[:,1],v[:,0]);angle[np.linalg.norm(v,axis=1)<1e-12]=0
    return angle

def choose_fit(d,which,y=None):
    X=design(d,which);y=d['y'] if y is None else y;ids=d['keys'][:,0]
    unique=np.unique(ids);fold={v:j%5 for j,v in enumerate(unique)}
    rows=[];allpred=[]
    for lam in LAMBDAS:
        hat=np.empty(len(y))
        for k in range(5):
            val=np.array([fold[v]==k for v in ids]);train=~val
            m=fit(X[train],y[train],ids[train],lam);hat[val]=predict(m,X[val])
        loss=float(person_means(circular_loss(y,hat),ids).mean())
        rows.append(dict(lam=lam,mean_person_loss=loss));allpred.append(hat)
    best=min(range(len(rows)),key=lambda k:rows[k]['mean_person_loss'])
    return fit(X,y,ids,LAMBDAS[best]),rows,allpred[best]
