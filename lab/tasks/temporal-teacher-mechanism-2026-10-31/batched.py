"""Batched simultaneous-Euler implementation of the frozen zero-HVC source."""
import os,sys
sys.dont_write_bytecode=True
for k in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','VECLIB_MAXIMUM_THREADS'):os.environ[k]='2'
import numpy as np
from scipy.special import erf
import core as c
from common import check_deadline

class Circuit:
    def __init__(self,net,h):
        dense=lambda a:a.toarray() if hasattr(a,'toarray') else np.asarray(a)
        self.JT=np.ascontiguousarray(np.block([[dense(net.JEE),-dense(net.JEI)],[dense(net.JIE),-dense(net.JII)]]).T)
        self.h=np.r_[h[0],h[1]];self.NE=net.NE;self.NI=net.NI
        self.inv_tau=1/np.r_[np.full(net.NE,net.tauE),np.full(net.NI,net.tauI)]
        self.maximum=np.r_[np.full(net.NE,net.phiE[0]),np.full(net.NI,net.phiI[0])]
        self.threshold=np.r_[np.full(net.NE,net.phiE[1]),np.full(net.NI,net.phiI[1])]
        self.width=np.sqrt(2)*np.r_[np.full(net.NE,net.phiE[2]),np.full(net.NI,net.phiI[2])]
        self.quiet_rate=float(self.phi(self.h)[...,:self.NE].mean())
    def phi(self,h):return self.maximum/2*(1+erf((h-self.threshold)/self.width))
    def run(self,y,starts,ends,trace=False,noise=None):
        check_deadline();b=len(y);h=np.broadcast_to(self.h,(b,len(self.h))).copy();r=self.phi(h)
        yy=np.repeat(y,6,axis=2);summ=r[:,:self.NE]/100.;summ=summ.copy();sq=summ*summ;trace_values=[]
        if trace:trace_values.append(r[:,:self.NE].copy())
        for t in range(1,c.T):
            flow=r@self.JT-h
            for k in range(6):
                active=(starts[:,k]<=t-1)&(t-1<ends[:,k])
                if active.any():flow[active,:self.NE]+=yy[active,k]
            if noise is not None:flow[:,:self.NE]+=np.repeat(noise[t-1],6,axis=1)
            h+=flow*self.inv_tau;r=self.phi(h);z=r[:,:self.NE]/100.
            summ+=z;sq+=z*z
            if trace:trace_values.append(r[:,:self.NE].copy())
        moments=np.concatenate([summ/c.T,sq/c.T],axis=1)
        return moments,(np.stack(trace_values,axis=1) if trace else None)

def signals(actions,basis,bias,orders,phases):
    actions=np.asarray(actions);y=c.features(actions[:,:4],basis,bias)
    y=np.take_along_axis(y,orders[actions[:,4].astype(int),:,None],axis=1)
    starts=150+np.asarray(phases)[:,None]+np.rint(np.arange(6)[None,:]*150*actions[:,5,None]).astype(int)
    ends=starts+np.rint(100*actions[:,5,None]).astype(int)
    valid=np.mean(y*y,axis=2)>1e-8
    return y,starts,ends,valid

def rle_from_waveform(a):
    active=np.mean(a*a,axis=1)>1e-8;edge=np.diff(np.r_[False,active,False].astype(int))
    starts=np.flatnonzero(edge==1);ends=np.flatnonzero(edge==-1)
    if not len(starts):return np.empty((0,c.N)),starts,ends
    return np.stack([a[s:e].mean(0) for s,e in zip(starts,ends)]),starts-starts[0],ends-starts[0]

def segment_loss(y,starts,ends,valid,target):
    ty,ts,te=target
    origin=np.where(valid,starts,c.T).min(axis=1);origin=np.where(origin==c.T,0,origin)
    ss=starts-origin[:,None];ee=ends-origin[:,None]
    lengths=(ee-ss)*valid
    current=(lengths*np.mean(y*y,axis=2)).sum(1)
    target_energy=np.sum((te-ts)*np.mean(ty*ty,axis=1))
    cross=np.einsum('bsc,kc->bsk',y,ty)/c.N
    overlap=np.maximum(0,np.minimum(ee[:,:,None],te[None,None,:])-np.maximum(ss[:,:,None],ts[None,None,:]))*valid[:,:,None]
    value=(current+target_energy-2*(cross*overlap).sum((1,2)))/c.T
    return np.maximum(value,0.)

def input_moments(y,starts,ends,valid):
    weights=((ends-starts)*valid)[:,:,None]/c.T
    return np.concatenate([(weights*y/2).sum(1),(weights*y*y/4).sum(1)],axis=1)
