"""Independent source-only quadrature and exact selected-curve means.

Uses a separately written vector learner and forward/backward finite-state
calculation. No fit, no target response, no combined MAT, no authored kernel.
"""
import os
os.environ['OPENBLAS_NUM_THREADS']='1'
os.environ['OMP_NUM_THREADS']='1'
from pathlib import Path
import numpy as np
from numpy.polynomial.hermite import hermgauss
import json, math, resource, sys, time

HERE=Path(__file__).resolve().parent; REPO=HERE.parents[2]
SRC=REPO/'sources/flesch_source_calibration_2026-10-29'
TASK=REPO/'lab/tasks/flesch-source-calibration-2026-10-29'
started=time.time()
m=json.loads((TASK/'MASKS.json').read_text()); cols=m['source_columns'];P=len(cols)
fitids=[cols.index(c) for g in ['B200','Interleaved'] for c in m['split'][g]['fit']]
checkids=[cols.index(c) for g in ['B200','Interleaved'] for c in m['split'][g]['check']]
x=np.load(SRC/'inputs_only.npz'); r=np.load(SRC/'source_responses.npz')
branches=x['expt_branchIDX'][:,cols].T.astype(int)-1
leaves=x['expt_leafIDX'][:,cols].T.astype(int)-1
contexts=x['expt_contextIDX'][:,cols].T.astype(int)-1
reward=x['expt_rewardIDX'][:400,cols].T/25
category=x['expt_catIDX'][:,cols].T; truth=category>=0; boundary=category==0
action=r['resp_category'].T; rt=r['resp_reactiontime'].T
timing=np.where(~np.isfinite(action),2,np.where(rt>5,1,0))
actual=np.where(np.isfinite(action),action,-1).astype(int)
grid=np.linspace(0,1,5);gx,gy=np.meshgrid(grid,grid)
blobs=np.array([[np.exp(-((gx-(.2+.15*b))**2+(gy-(.2+.15*l))**2)/.16).ravel() for l in range(5)] for b in range(5)])
blobs/=blobs.max(axis=2,keepdims=True); blobs-=blobs.mean(axis=(0,1))
features=blobs[branches,leaves]; coords=np.stack([(branches-2)/2,(leaves-2)/2],axis=-1)
def sigmoid(z):
    return 1/(1+np.exp(-z))
def logits(name,theta,z):
    lr,alpha,temp,bias,rho,sd=theta[:6]
    speed=np.exp(np.exp(sd)*z); rate=np.exp(lr)*speed
    value=np.empty((P,600)); cue=np.eye(2)[contexts[:,0]].copy()
    weights=np.zeros((P,2,26)); accumulation=np.zeros((P,2,2)); counts=np.zeros((P,2))
    rows=np.arange(P)
    for t in range(600):
        ctx=contexts[:,t]; one=np.eye(2)[ctx]
        if t<400:cue=(1-alpha)*cue+alpha*one
        use=cue if t<400 else one
        if name=='context_value':
            vals=np.einsum('pcf,pf->pc',weights[:,:,:25],features[:,t])+weights[:,:,25]
        else:
            norms=np.sqrt(np.sum(accumulation**2,axis=2)); norms=np.where(norms>1e-12,norms,1)
            vals=2*np.einsum('pcf,pf->pc',accumulation,coords[:,t])/norms*(1-np.exp(-rate*counts))
        value[:,t]=np.sum(use*vals,axis=1)
        if t<400:
            if name=='context_value':
                delta=rate*(reward[:,t]-vals[rows,ctx])/(1+np.sum(features[:,t]**2,axis=1))
                weights[rows,ctx,:25]+=delta[:,None]*features[:,t];weights[rows,ctx,25]+=delta
            else:
                accumulation[rows,ctx]+=reward[:,t,None]*coords[:,t];counts[rows,ctx]+=1
    return sigmoid(np.exp(temp)*speed*value[:,:,None]+bias+rho*np.arange(-1,2)[None,None,:])
def selected_curve(prob,q):
    late,miss=q; on=1-late-miss
    # For each possible last action at the end of training, sum test paths.
    dp=np.zeros((P,3,90,3));dp[:,:,0,:]=np.eye(3)[None,:,:]
    for t in range(400,600):
        nxt=np.zeros_like(dp);a=prob[:,t]
        sums=[np.sum(dp*(1-a[:,None,None,:]),axis=3),np.sum(dp*a[:,None,None,:],axis=3)]
        for act in [0,1]:
            mass=sums[act];hit=((truth[:,t]==bool(act)) & ~boundary[:,t]).astype(float)[:,None,None]
            nxt[:,:,:,2*act]+=mass*(late+on*(1-hit))
            nxt[:,:,1:,2*act]+=mass[:,:,:-1]*on*hit
            nxt[:,:,89,2*act]+=mass[:,:,89]*on*hit[:,:,0]
        nxt[:,:,:,1]+=miss*dp.sum(axis=3);dp=nxt
    accept_from=dp[:,:,89,:].sum(axis=2)
    # Forward and backward distributions through all training opportunities.
    f=np.zeros((P,401,3));f[:,0,1]=1
    for t in range(400):
        a=prob[:,t];f[:,t+1,0]=(1-miss)*np.sum(f[:,t]*(1-a),axis=1)
        f[:,t+1,2]=(1-miss)*np.sum(f[:,t]*a,axis=1);f[:,t+1,1]=miss
    b=accept_from.copy();joint=np.empty((P,400));rows=np.arange(P)
    for t in range(399,-1,-1):
        a=prob[:,t];correctprob=np.where(truth[:,t,None],a,1-a)
        joint[:,t]=on*np.sum(f[:,t]*correctprob,axis=1)*b[rows,truth[:,t].astype(int)*2]
        b=(1-miss)*((1-a)*b[:,0,None]+a*b[:,2,None])+miss*b[:,1,None]
    A=b[:,1]
    assert np.max(abs(A-np.sum(f[:,400]*accept_from,axis=1)))<2e-13
    assert np.max(abs(dp.sum(axis=(2,3))-1))<2e-13
    bins=np.empty((P,8))
    for k in range(8):
        keep=~boundary[:,50*k:50*k+50]
        bins[:,k]=np.sum(joint[:,50*k:50*k+50]*keep,axis=1)/keep.sum(axis=1)
    # Complete observed trajectory likelihood, with the actual prior action.
    prev=np.c_[np.ones(P,dtype=int),(actual[:,:-1]+1)]
    # actual actions -1/0/1 map to last-state 1/0/2, respectively.
    prev=np.c_[np.ones(P,dtype=int),np.where(actual[:,:-1]<0,1,2*actual[:,:-1])]
    pp=prob[np.arange(P)[:,None],np.arange(600)[None,:],prev]
    obs=np.where(timing==2,miss,np.where(timing==1,late,on)*np.where(actual==1,pp,1-pp))
    ll=np.log(obs).sum(axis=1)
    return A,bins,ll
def logsumexp(a,axis):
    mx=a.max(axis=axis,keepdims=True);return (mx+np.log(np.exp(a-mx).sum(axis=axis,keepdims=True))).squeeze(axis)
obs=np.empty((P,8))
for k in range(8):
    keep=~boundary[:,50*k:50*k+50]
    cor=(actual[:,50*k:50*k+50]==truth[:,50*k:50*k+50])&(timing[:,50*k:50*k+50]==0)
    obs[:,k]=(cor*keep).sum(axis=1)/keep.sum(axis=1)
out={}
for name in ['context_value','exposure_growth']:
    fit=json.loads((TASK/f'two_start_{name}_fit.json').read_text());theta=np.array(fit['theta'])
    q=np.array([sigmoid(theta[-1]) if fit['active_late'] else 0,sigmoid(theta[-2])])
    out[name]={}
    for nq in [3,5,9]:
        zz,ww=hermgauss(nq);zz*=np.sqrt(2);ww/=np.sqrt(np.pi)
        AA=[];BB=[];LL=[]
        for z in zz:
            A,B,L=selected_curve(logits(name,theta,z),q);AA.append(A);BB.append(B);LL.append(L)
        AA=np.array(AA);BB=np.array(BB);LL=np.array(LL)
        denom=ww@AA;mean=np.einsum('z,zpb->pb',ww,BB)/denom[:,None]
        selected_ll=logsumexp(LL+np.log(ww)[:,None],axis=0)-np.log(denom)
        nll=float(-selected_ll[fitids].sum());groups={}
        for g in ['B200','Interleaved']:
            ids=[cols.index(c) for c in m['split'][g]['check']]
            forecast=mean[ids].mean(axis=0);observed=obs[ids].mean(axis=0)
            groups[g]={'exact_population_curve_mae_pp':float(100*np.abs(forecast-observed).mean()),'forecast_mean_curve':forecast.tolist(),'observed_mean_curve':observed.tolist()}
        out[name][str(nq)]={'fit_negative_selected_log_likelihood':nll,'group_checks':groups,
            'acceptance_range':[float(denom.min()),float(denom.max())]}
        if nq==3:
            assert abs(nll-fit['negative_selected_log_likelihood'])<1e-7,(name,nll,fit['negative_selected_log_likelihood'])
result={'status':'independent exact finite-state selected source means; no fitting or target responses', 'models':out,
    'elapsed_seconds':time.time()-started,'max_rss_bytes':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*(1 if sys.platform=='darwin' else 1024)}
assert result['max_rss_bytes']<512*1024*1024
(HERE/'exact_source_results.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result,indent=2))
