"""Causal numpy forecast API for a published DNNGLM and REINFORCE.

Choice is IBL-native: +1 left, -1 right, 0 omission. Predictions precede
updates. Published binary updates are skipped on omissions, never recoded.
The three GLM coefficients are right contrast, left contrast, and bias.
Training is in fit_learning.py; loading and forecasting do not require torch.
"""
from pathlib import Path
import json
import numpy as np
from scipy.optimize import minimize
from scipy.special import expit

try:
    from numba import njit
except ImportError:
    def njit(*args, **kwargs):
        if args and callable(args[0]):
            return args[0]
        return lambda f: f


def stimulus(s):
    return np.tanh(5.0 * np.asarray(s, dtype=float)) / np.tanh(5.0)


def features(s):
    z = stimulus(s)
    return np.stack((np.maximum(z, 0), np.minimum(z, 0), np.ones_like(z)), axis=-1)


def subject_arrays(prefix):
    """Accept the data reader mapping, or an already normalized mapping."""
    s = np.nan_to_num(np.asarray(prefix['contrastRight'], float)) - np.nan_to_num(np.asarray(prefix['contrastLeft'], float))
    c = np.asarray(prefix['choice'], float)
    r = (np.asarray(prefix['feedbackType'], float) > 0).astype(float)
    if 'session_start' in prefix:
        d = np.asarray(prefix['session_start'], float)
    else:
        key = next((k for k in ('session_index', 'session', 'session_id') if k in prefix), None)
        if key is None:
            d = np.zeros(len(c)); d[0] = 1
        else:
            session = np.asarray(prefix[key])
            d = np.r_[1., (session[1:] != session[:-1]).astype(float)]
    return s, c, r, d


def static_fit(prefix, n=None):
    s, c, _, _ = subject_arrays(prefix)
    if n is not None:
        s, c = s[:n], c[:n]
    ok = c != 0
    X = features(s[ok]); y = (c[ok] < 0).astype(float)
    def obj(w):
        z = np.einsum('ti,i->t',X,w)
        return np.sum(np.logaddexp(0, z) - y*z) + .5*np.sum(w*w), np.einsum('ti,t->i',X,expit(z)-y) + w
    if len(y) < 5:
        return np.zeros(3)
    return minimize(obj, np.zeros(3), jac=True, method='L-BFGS-B', bounds=[(-8, 12), (-8, 12), (-6, 6)]).x


@njit(cache=True)
def _sequence(kind, s, c, r, day, w0, A, a, B, b, C, cc, scale, alpha, baseline):
    """Compiled scalar recurrence used for calibration and conditional scores."""
    T = len(s); w = w0.copy(); out = np.empty(T); ws = np.empty((T, 3))
    den = np.tanh(5.)
    for t in range(T):
        z = np.tanh(5.*s[t])/den
        x = np.array([max(z,0.), min(z,0.), 1.])
        lg = np.dot(w, x)
        p = 1./(1.+np.exp(-max(-50.,min(50.,lg))))
        out[t] = p; ws[t] = w
        if c[t] != 0:
            y = 1. if c[t] < 0 else 0.
            if kind == 0:
                w = w + alpha*(r[t]+baseline)*(y-p)*x
            else:
                inp = np.empty(9)
                inp[:3] = w
                inp[3:] = np.array([z, 1., day[t], y, r[t], 1. if z>0 else 0.])
                h1 = np.maximum(np.dot(A,inp)+a,0)
                h2 = np.maximum(np.dot(B,h1)+b,0)
                dw = scale*(np.dot(C,h2)+cc)
                w = w + dw
    return out, ws, w


class LearningModel:
    def __init__(self, kind, params, metadata=None):
        self.kind = kind
        self.params = params
        self.metadata = metadata or {}
        self.name = self.metadata.get('name', kind)

    def probs(self, state, signed_contrast):
        """Probability of RIGHT conditional on making a response."""
        return expit(np.sum(np.asarray(state['w'])*features(signed_contrast),axis=-1))

    def update(self, state, signed_contrast, choice, feedback, session_start=False):
        """Update in place from generated or observed feedback AFTER prediction."""
        w = np.asarray(state['w'])
        s,c,r,d = np.broadcast_arrays(np.asarray(signed_contrast,float),np.asarray(choice),np.asarray(feedback,float)>0,np.asarray(session_start,float))
        z=stimulus(s); y=(c<0).astype(float); responded=(c!=0)
        if self.kind=='reinforce':
            p=self.probs(state,s)
            dw=self.params['alpha']*(r[...,None]+self.params['baseline'])*(y-p)[...,None]*features(s)
        else:
            target_shape=np.broadcast_shapes(w.shape[:-1],s.shape)
            wb=np.broadcast_to(w,target_shape+(3,))
            inp=np.concatenate((wb,np.stack((z,np.ones_like(z),d,y,r.astype(float),(z>0).astype(float)),axis=-1)),axis=-1)
            p=self.params
            h=np.maximum(np.einsum('...i,ji->...j',inp,p['A'])+p['a'],0)
            h=np.maximum(np.einsum('...i,ji->...j',h,p['B'])+p['b'],0)
            dw=p['scale']*(np.einsum('...i,ji->...j',h,p['C'])+p['cc'])
        state['w']=w+dw*responded[...,None]
        return state

    def sequence(self, data, w0=None):
        s,c,r,d=subject_arrays(data)
        if w0 is None: w0=np.zeros(3)
        p=self.params
        if self.kind=='reinforce':
            return _sequence(0,s,c,r,d,np.asarray(w0,float),np.zeros((16,9)),np.zeros(16),np.zeros((16,16)),np.zeros(16),np.zeros((3,16)),np.zeros(3),np.zeros(3),p['alpha'],p['baseline'])
        return _sequence(1,s,c,r,d,np.asarray(w0,float),p['A'],p['a'],p['B'],p['b'],p['C'],p['cc'],p['scale'],np.zeros(3),np.zeros(3))

    def initial_state(self, prefix, method='map', prior_precision=.5):
        """Prefix-only initial-condition likelihood; frozen law is never refit.

        All prefix trials may calibrate three initial coefficients. Gaussian
        N(0,2I) regularization and fixed bounds are shared across both laws.
        """
        s,c,_,_=subject_arrays(prefix); y=(c<0).astype(float); ok=c!=0
        start=static_fit(prefix,n=min(200,len(c)))
        if method=='zero':
            w0=np.zeros(3)
        elif method=='static':
            # Explicit alternative current-competence initialization, not MAP.
            return {'w':static_fit(prefix),'w0':start,'calibration':'static_all_prefix'}
        else:
            def fun(w):
                p,_,_=self.sequence(prefix,w)
                p=np.clip(p,1e-9,1-1e-9)
                return -np.sum((y*np.log(p)+(1-y)*np.log1p(-p))[ok])+.5*prior_precision*np.sum(w*w)
            res=minimize(fun,start,method='L-BFGS-B',bounds=[(-8,12),(-8,12),(-6,6)],options={'maxiter':80,'ftol':1e-8})
            w0=res.x
        _,_,w=self.sequence(prefix,w0)
        return {'w':w,'w0':w0,'calibration':method}

    def save(self, path):
        path=Path(path); path.parent.mkdir(parents=True,exist_ok=True)
        np.savez(path,kind=np.array(self.kind),metadata=np.array(json.dumps(self.metadata)),**self.params)


def load_model(path):
    z=np.load(path,allow_pickle=False)
    return LearningModel(str(z['kind']),{k:np.asarray(z[k],float) for k in z.files if k not in ('kind','metadata')},json.loads(str(z['metadata'])))


def conditional_forecast(model, prefix, future, method='map'):
    state=model.initial_state(prefix,method)
    p,w,end=model.sequence(future,state['w'])
    return p,w,{'w':end}
