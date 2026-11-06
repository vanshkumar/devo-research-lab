"""Separate postvalidation source-RNN challenge. Torch-free forecast API.

The frozen first-stage model and rollout files are deliberately unchanged.
State includes BOTH GLM coefficients w and recurrent memory h. Choices use
native ALF coding: +1left, -1right, 0omission. Predict before update.
"""
from pathlib import Path
import json
import numpy as np
from scipy.optimize import minimize
from scipy.special import expit
from learning_models import features, stimulus, static_fit, subject_arrays, njit


@njit(cache=True)
def _rnn_sequence(s,c,r,day,w0,h0,Wih,Whh,bih,bhh,A,a,B,b,C,cc,scale):
    n=len(c);w=w0.copy();h=h0.copy();pout=np.empty(n);ws=np.empty((n,3));den=np.tanh(5.)
    H=len(h)
    for t in range(n):
        z=np.tanh(5.*s[t])/den;x=np.array([max(z,0.),min(z,0.),1.])
        lg=np.dot(w,x);pout[t]=1./(1.+np.exp(-max(-50.,min(50.,lg))));ws[t]=w
        if c[t]!=0:
            inp=np.empty(9);inp[:3]=w
            inp[3:]=np.array([z,1.,day[t],1. if c[t]<0 else 0.,r[t],1. if z>0 else 0.])
            gi=np.dot(Wih,inp)+bih;gh=np.dot(Whh,h)+bhh
            reset=1./(1.+np.exp(-(gi[:H]+gh[:H])))
            update=1./(1.+np.exp(-(gi[H:2*H]+gh[H:2*H])))
            candidate=np.tanh(gi[2*H:]+reset*gh[2*H:])
            h=(1.-update)*candidate+update*h
            a1=np.maximum(np.dot(A,h)+a,0.)
            a2=np.maximum(np.dot(B,a1)+b,0.)
            w=w+scale*(np.dot(C,a2)+cc)
    return pout,ws,w,h


class RNNLearningModel:
    def __init__(self,params,metadata=None):
        self.params=params;self.metadata=metadata or {};self.name='rnnglm32'
        self.hidden=len(params['bhh'])//3

    def probs(self,state,signed_contrast):
        return expit(np.sum(state['w']*features(signed_contrast),axis=-1))

    def update(self,state,signed_contrast,choice,feedback,session_start=False):
        p=self.params
        s,c,r,d=np.broadcast_arrays(np.asarray(signed_contrast,float),np.asarray(choice),np.asarray(feedback)>0,np.asarray(session_start,float))
        shape=np.broadcast_shapes(np.shape(state['w'])[:-1],s.shape)
        w=np.broadcast_to(state['w'],shape+(3,));h=np.broadcast_to(state['h'],shape+(self.hidden,))
        z=stimulus(s)
        cov=np.stack((z,np.ones_like(z),d,(c<0).astype(float),r.astype(float),(z>0).astype(float)),axis=-1)
        cov=np.broadcast_to(cov,shape+(6,));inp=np.concatenate((w,cov),axis=-1)
        gi=np.einsum('...i,ji->...j',inp,p['Wih'])+p['bih']
        gh=np.einsum('...i,ji->...j',h,p['Whh'])+p['bhh'];H=self.hidden
        reset=expit(gi[...,:H]+gh[...,:H]);update=expit(gi[...,H:2*H]+gh[...,H:2*H])
        candidate=np.tanh(gi[...,2*H:]+reset*gh[...,2*H:])
        hnew=(1.-update)*candidate+update*h
        a=np.maximum(np.einsum('...i,ji->...j',hnew,p['A'])+p['a'],0.)
        a=np.maximum(np.einsum('...i,ji->...j',a,p['B'])+p['b'],0.)
        dw=p['scale']*(np.einsum('...i,ji->...j',a,p['C'])+p['cc'])
        ok=(c!=0)[...,None]
        state['w']=np.where(ok,w+dw,w);state['h']=np.where(ok,hnew,h)
        return state

    def sequence(self,data,initial=None,h0=None):
        s,c,r,d=subject_arrays(data);p=self.params
        if initial is None:initial=np.zeros(3)
        if isinstance(initial,dict):w0=np.asarray(initial['w'],float);hh=np.asarray(initial['h'],float)
        else:w0=np.asarray(initial,float);hh=np.zeros(self.hidden) if h0 is None else np.asarray(h0,float)
        probs,ws,w,h=_rnn_sequence(s,c,r,d,w0,hh,p['Wih'],p['Whh'],p['bih'],p['bhh'],p['A'],p['a'],p['B'],p['b'],p['C'],p['cc'],p['scale'])
        return probs,ws,dict(w=w,h=h)

    def initial_state(self,prefix,method='map',prior_precision=.5):
        _,c,_,_=subject_arrays(prefix);ok=c!=0;y=(c<0).astype(float)
        start=static_fit(prefix,n=min(200,len(c)))
        if method=='zero':w0=np.zeros(3)
        elif method=='static':
            # The recurrent memory is still prefix-derived, never zeroed at
            # forecast onset merely because static current competence is used.
            _,_,st=self.sequence(prefix,start);st['w']=static_fit(prefix);st['w0']=start
            st['calibration']='static';return st
        else:
            def fun(w):
                q,_,_=self.sequence(prefix,w);q=np.clip(q,1e-9,1-1e-9)
                return -np.sum((y*np.log(q)+(1-y)*np.log1p(-q))[ok])+.5*prior_precision*np.sum(w*w)
            res=minimize(fun,start,method='L-BFGS-B',bounds=[(-8,12),(-8,12),(-6,6)],options={'maxiter':80,'ftol':1e-8})
            w0=res.x
        _,_,st=self.sequence(prefix,w0);st['w0']=w0;st['calibration']=method;return st

    def save(self,path):
        path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
        np.savez(path,kind=np.array('rnnglm'),metadata=np.array(json.dumps(self.metadata)),**self.params)


def load_rnn(path):
    with np.load(path,allow_pickle=False) as z:
        return RNNLearningModel({k:np.asarray(z[k],float) for k in z.files if k not in ('kind','metadata')},json.loads(str(z['metadata'])))
