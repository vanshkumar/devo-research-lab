"""Port and intervention tests for the published HVC synaptic-sequence model.

No claim of identical MATLAB PRNG. Network update equations and source parameters
are retained. Independent numpy implementation verifies the C++ kernel on small
controlled cases. Simulation replicates are networks, not biological birds.
"""
import argparse,ctypes,json,subprocess,time,hashlib,os
from pathlib import Path
import numpy as np
from scipy.io import loadmat

BASE=Path(__file__).resolve().parents[1]
HERE=Path(__file__).resolve().parent
OUT=BASE/'outputs'/'hvc';OUT.mkdir(parents=True,exist_ok=True)
PARAMS=np.array([.115,30,.025,.2,12,.01,1,5,10.],dtype=np.float64)

def build():
    lib=OUT/'hvc_kernel.dylib'
    src=HERE/'hvc_kernel.cpp'
    if not lib.exists() or lib.stat().st_mtime<src.stat().st_mtime:
        subprocess.run(['clang++','-O3','-std=c++17','-dynamiclib',str(src),'-o',str(lib)],check=True)
    f=ctypes.CDLL(str(lib)).hvc_run
    arr=np.ctypeslib.ndpointer
    f.argtypes=[ctypes.c_int,ctypes.c_int,arr(dtype=np.float64,flags='C_CONTIGUOUS'),
        arr(dtype=np.uint8,flags='C_CONTIGUOUS'),arr(dtype=np.uint8,flags='C_CONTIGUOUS'),
        arr(dtype=np.float64,flags='C_CONTIGUOUS'),arr(dtype=np.uint8,flags='C_CONTIGUOUS')]
    f.restype=None
    return f

def run(w,noise,onset,params=PARAMS):
    w=np.ascontiguousarray(w.copy(),dtype=np.float64)
    act=np.zeros_like(noise,dtype=np.uint8)
    build()(w.shape[0],len(noise),w,noise,np.ascontiguousarray(onset,dtype=np.uint8),params,act)
    return w,act

def reference(w,noise,onset,params):
    beta,alpha,eta,eps,tau,gamma,wmax,Wmax,k=params;k=int(k)
    w=w.copy();n=w.shape[0];old=np.zeros(n);y=np.zeros(n);act=[]
    for t in range(len(noise)):
        y=y+(old-y)/tau
        b=noise[t].astype(float);b[:k]=10 if onset[t] else -10
        a=np.maximum(0,np.einsum('ij,j->i',w,old)-beta*old.sum()-alpha*y+b)
        x=(a-gamma*a.sum()>0).astype(float)
        d=eta*(np.outer(x,old)-np.outer(old,x))
        pre=eta*np.maximum(0,(w+d).sum(axis=0)-Wmax)
        post=eta*np.maximum(0,(w+d).sum(axis=1)-Wmax)
        if eta>0:
            w=np.clip(w+d-eps*(pre[None,:]+post[:,None]),0,wmax)
            np.fill_diagonal(w,0)
        old=x;act.append(x)
    return w,np.array(act,dtype=np.uint8)

def verify():
    r=np.random.default_rng(20261028);errors=[]
    for eta in [0,.025]:
      for n in [12,20]:
        p=PARAMS.copy();p[2]=eta;p[8]=3
        w=r.uniform(0,1,(n,n));noise=(r.random((400,n))<.03).astype(np.uint8)
        onset=(np.arange(400)%10==0).astype(np.uint8)
        wc,xc=run(w,noise,onset,p);wr,xr=reference(w,noise,onset,p)
        assert np.array_equal(xc,xr)
        error=float(np.max(np.abs(wc-wr)));assert error<1e-12
        errors.append(error)
    # Known sequence readout: seed then four succeeding layers -> 50 ms activity.
    p=PARAMS.copy();p[2]=0;p[8]=1;p[0]=0;p[5]=0
    w=np.zeros((5,5));w[np.arange(1,5),np.arange(4)]=1
    ons=np.zeros(20,dtype=np.uint8);ons[0]=1
    _,act=run(w,np.zeros((20,5),dtype=np.uint8),ons,p)
    assert length(act)==50
    z={'max_weight_difference':max(errors),'exact_activity_agreement':True,
       'cases':4,'known_chain_duration_ms':length(act),'kernel_source_sha256':hashlib.sha256((HERE/'hvc_kernel.cpp').read_bytes()).hexdigest()}
    (OUT/'kernel_verification.json').write_text(json.dumps(z,indent=2)+'\n')
    return z

def length(act):
    # Matches MATLAB find(actSums(2:end)==0,1) in 10 ms units.
    off=np.flatnonzero(act[1:].sum(axis=1)==0)
    return int((off[0]+1)*10) if len(off) else None

def source_times():
    files=list((BASE/'inputs'/'prior_work').rglob('trialTimes.mat'))
    if not files:raise FileNotFoundError('source trialTimes.mat is required')
    d=loadmat(files[0]);return np.asarray(d['trialTimes']).ravel().astype(int)-1

def simulate(seed=1,period=10,steps=360000,mode='source',ntrials=7200,eta_scale=1.,tau_scale=1.):
    started=time.monotonic();n=100;r=np.random.default_rng(seed)
    p=PARAMS.copy();p[2]*=eta_scale;p[4]*=tau_scale
    w0=r.uniform(0,.1,(n,n)) # same law as source 2*rand*Wmax/n
    if mode=='source':
        times=source_times();times=times[(times>=0)&(times<steps-100)]
    else:
        # Matched train onsets with >=1.2s separation; avoids crossing train boundaries.
        rr=np.random.default_rng(1701)
        times=10+np.r_[0,np.cumsum(120+rr.poisson(50,ntrials-1))]
        steps=int(times[-1]+200)
    onset=np.zeros(steps,dtype=np.uint8)
    offsets=[0] if period==0 else [0,period,2*period,3*period]
    for t in times:
        idx=t+np.array(offsets);idx=idx[idx<steps];onset[idx]=1
    # Uint8 input/activity uses <80 MB for source runs. RNG differs from MATLAB.
    # Chunk to avoid a steps*n float temporary (~1 GB in matched designs).
    noise=np.empty((steps,n),dtype=np.uint8)
    for start in range(0,steps,4096):
        end=min(start+4096,steps)
        noise[start:end]=(r.random((end-start,n))<.001)
    w,act=run(w0,noise,onset,p)
    # Source script readout while plasticity and stimulation are still active.
    last_offset=offsets[-1]
    training=[length(act[t+last_offset:t+100]) for t in times[-10:]]
    training_status=('unavailable: last impulse outside source100-step readout window' if last_offset>=100
                     else 'measured during training; null means no silence within source readout window')
    # Methods-matched readout: freeze learned weights and use a single pulse.
    # Report both noise and no-noise, without conflating activity with vocal output.
    probe=[];p_eval=p.copy();p_eval[2]=0
    for rep in range(10):
        pn=(r.random((200,n))<.001).astype(np.uint8)
        po=np.zeros(200,dtype=np.uint8);po[0]=1
        _,pa=run(w,pn,po,p_eval);probe.append(length(pa))
    _,clean=run(w,np.zeros((200,n),dtype=np.uint8),po,p_eval)
    z={'seed':seed,'period_steps':period,'mode':mode,'steps':steps,'trains':len(times),
       'parameters':p.tolist(),'training_readout_ms':training,'training_readout_status':training_status,'frozen_probe_ms':probe,
       'clean_probe_ms':length(clean),'elapsed_seconds':time.monotonic()-started,
       'limitation':'neural activity duration, not measured syllable duration; source PRNG not reproduced'}
    tag=f'{mode}_seed{seed}_period{period}_eta{eta_scale:g}_tau{tau_scale:g}_steps{steps}'
    np.savez_compressed(OUT/(tag+'.npz'),weights=w,probe_activity=clean,onsets=onset[-1000:],last_activity=act[-1000:])
    (OUT/(tag+'.json')).write_text(json.dumps(z,indent=2)+'\n')
    print(json.dumps(z),flush=True);return z

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--verify',action='store_true')
    ap.add_argument('--seed',type=int,default=1);ap.add_argument('--period',type=int,default=10)
    ap.add_argument('--steps',type=int,default=360000);ap.add_argument('--mode',choices=['source','matched'],default='source')
    ap.add_argument('--ntrials',type=int,default=7200);ap.add_argument('--eta-scale',type=float,default=1.)
    ap.add_argument('--tau-scale',type=float,default=1.);args=ap.parse_args()
    if args.verify:print(json.dumps(verify()))
    else:simulate(args.seed,args.period,args.steps,args.mode,args.ntrials,args.eta_scale,args.tau_scale)
