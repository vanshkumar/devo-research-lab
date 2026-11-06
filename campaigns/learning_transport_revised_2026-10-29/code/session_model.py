"""One coherent pretrial session-transition extension of the frozen GRU updater.

The inherited updater parameters never change. A shared fitted ``rho`` scales
both GLM coefficients and GRU memory before the first prediction in each new
session. An omitted first trial still receives this transition. The existing
session-start covariate remains in the post-response update.

An array/None initial state denotes the beginning of an indexed history: the
first row is already initialized, so its start flag does not apply a transition.
A dict initial state denotes continuation from a previous segment: a first-row
start flag DOES apply the transition. This convention makes split and continuous
histories identical without treating forecast onset as a session boundary.
"""
from pathlib import Path
import json
import sys
import numpy as np

OLD = Path(__file__).resolve().parents[2] / 'learning_rule_transport_2026-10-28'
sys.dont_write_bytecode = True
sys.path.insert(0, str(OLD / 'code'))
from rnn_learning import RNNLearningModel, load_rnn
from learning_models import subject_arrays, njit


@njit(cache=True)
def _session_sequence(s,c,r,day,w0,h0,rho,continuing,Wih,Whh,bih,bhh,A,a,B,b,C,cc,scale):
    n=len(c);w=w0.copy();h=h0.copy();pout=np.empty(n);ws=np.empty((n,3));den=np.tanh(5.)
    H=len(h)
    for t in range(n):
        if day[t] and (t>0 or continuing) and rho != 1.:
            w=w*rho;h=h*rho
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


class SessionTransitionModel(RNNLearningModel):
    """Frozen within-session GRU plus one fitted shared boundary coefficient."""
    def __init__(self,params,rho,metadata=None):
        super().__init__(params,metadata)
        if not np.isfinite(rho) or not 0.5 <= float(rho) <= 1.0:
            raise ValueError('rho must be finite and in the prescribed [0.5,1] interval')
        self.rho=float(rho)
        self.name='session_transition_rnn'

    def pretrial(self,state,session_start=False):
        """Apply once BEFORE prediction; caller owns genuine session chronology."""
        if self.rho == 1.:
            return state
        start=np.asarray(session_start,bool)
        if start.ndim==0:
            if bool(start):
                state['w']=state['w']*self.rho
                state['h']=state['h']*self.rho
        else:
            factor=np.where(start,self.rho,1.)[...,None]
            state['w']=state['w']*factor
            state['h']=state['h']*factor
        return state

    def sequence(self,data,initial=None,h0=None):
        s,c,r,d=subject_arrays(data);p=self.params
        continuing=isinstance(initial,dict)
        if initial is None:initial=np.zeros(3)
        if continuing:
            w0=np.asarray(initial['w'],float);hh=np.asarray(initial['h'],float)
        else:
            w0=np.asarray(initial,float)
            hh=np.zeros(self.hidden) if h0 is None else np.asarray(h0,float)
        probs,ws,w,h=_session_sequence(s,c,r,d,w0,hh,self.rho,continuing,
            p['Wih'],p['Whh'],p['bih'],p['bhh'],p['A'],p['a'],p['B'],p['b'],p['C'],p['cc'],p['scale'])
        return probs,ws,dict(w=w,h=h)

    def save(self,path):
        path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
        np.savez(path,kind=np.array('session_transition_rnn'),rho=np.array(self.rho),
            metadata=np.array(json.dumps(self.metadata)),**self.params)


def from_frozen(path,rho,metadata=None):
    old=load_rnn(path)
    return SessionTransitionModel(old.params,rho,{**old.metadata,**(metadata or {}),
        'transition':'w,h multiplied by shared rho before genuine session-first prediction',
        'new_history_first_row':'initialized before first row; no initial transition',
        'continued_segment_first_row':'transition applies if session_start',
        'within_session_parameters':'frozen inherited GRU; no refit',
        'biological_retention_claim':False})


def load_session(path):
    with np.load(path,allow_pickle=False) as z:
        params={k:np.asarray(z[k],float) for k in z.files if k not in ('kind','metadata','rho')}
        return SessionTransitionModel(params,float(z['rho']),json.loads(str(z['metadata'])))


def semantic_audit(model_path):
    """Known-answer chronology and rho=1 checks on synthetic inputs only."""
    old=load_rnn(model_path);one=from_frozen(model_path,1.);alt=from_frozen(model_path,.7)
    rng=np.random.default_rng(202610291)
    n=221;s=rng.choice([-1,-.25,-.125,0,.125,.25,1],n)
    c=rng.choice([-1,0,1],n);r=rng.choice([-1,1],n)
    d=np.zeros(n,dtype=bool);d[[0,73,151]]=True;c[73]=0
    data=dict(contrastLeft=np.maximum(-s,0),contrastRight=np.maximum(s,0),
        choice=c,feedbackType=r,session_start=d)
    w0=np.array([.7,-.4,.2])
    po,wo,eo=old.sequence(data,w0);p1,w1,e1=one.sequence(data,w0)
    rho1=float(max(np.max(np.abs(po-p1)),np.max(np.abs(wo-w1)),
        np.max(np.abs(eo['w']-e1['w'])),np.max(np.abs(eo['h']-e1['h']))))
    assert rho1==0.,rho1
    pa,wa,ea=alt.sequence(data,w0)
    first={k:v[:73] for k,v in data.items()};second={k:v[73:] for k,v in data.items()}
    pfirst,wfirst,endfirst=alt.sequence(first,w0)
    psecond,wsecond,endsplit=alt.sequence(second,endfirst)
    split=float(max(np.max(np.abs(np.r_[pfirst,psecond]-pa)),
        np.max(np.abs(np.r_[wfirst,wsecond]-wa)),np.max(np.abs(endsplit['w']-ea['w'])),
        np.max(np.abs(endsplit['h']-ea['h']))))
    assert split==0.,split
    st={'w':endfirst['w'].copy(),'h':endfirst['h'].copy()}
    alt.pretrial(st,True)
    boundary_before_probability=float(np.max(np.abs(st['w']-wsecond[0])))
    assert boundary_before_probability==0.
    prew=st['w'].copy();preh=st['h'].copy()
    alt.update(st,s[73],0,r[73],True)
    omitted_skip=float(max(np.max(np.abs(st['w']-prew)),np.max(np.abs(st['h']-preh))))
    assert omitted_skip==0.
    assert np.allclose(wsecond[1],.7*endfirst['w'],rtol=0,atol=0)
    initial_no_decay=float(np.max(np.abs(wa[0]-w0)))
    assert initial_no_decay==0.
    vector={'w':np.broadcast_to(w0,(7,3)).copy(),'h':np.zeros((7,old.hidden))}
    pv=[]
    for t in range(n):
        if t>0:alt.pretrial(vector,bool(d[t]))
        pv.append(alt.probs(vector,np.full(7,s[t])))
        alt.update(vector,np.full(7,s[t]),np.full(7,c[t]),np.full(7,r[t]),bool(d[t]))
    vector_error=float(max(np.max(np.abs(np.asarray(pv)[:,0]-pa)),
        np.max(np.abs(vector['w'][0]-ea['w'])),np.max(np.abs(vector['h'][0]-ea['h']))))
    assert vector_error<1e-10,vector_error
    return dict(synthetic_only=True,seed=202610291,trials=n,
        rho1_vs_old_max_abs=rho1,split_continuation_max_abs=split,
        boundary_before_probability_max_abs=boundary_before_probability,
        omitted_trial_skips_only_response_update_max_abs=omitted_skip,
        new_history_initial_row_no_decay_max_abs=initial_no_decay,
        vector_update_vs_numba_sequence_max_abs=vector_error,
        first_future_boundary_applies=True,day_covariate_retained=True)
