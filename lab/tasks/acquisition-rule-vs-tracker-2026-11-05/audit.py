"""Targeted scalar reference, causal information test, source and state checks."""
import time
import numpy as np
from scipy.special import expit
from pilot import (HERE,PREV,OLD,IO,PINS,read,get,save,arrays,seed,utc,subject)
from rnn_learning import load_rnn
from retained_growth import simulate,original_seed
from baselines import draw_initial

def scalar_step(model,state,x,c,r,day):
    p=model.params;w=state['w'].copy();h=state['h'].copy();H=len(h)
    z=np.tanh(5*x)/np.tanh(5)
    u=np.r_[w,z,1.,float(day),float(c<0),float(r>0),float(z>0)]
    gi=np.array([sum(float(a)*float(b) for a,b in zip(row,u))+bb for row,bb in zip(p['Wih'],p['bih'])])
    gh=np.array([sum(float(a)*float(b) for a,b in zip(row,h))+bb for row,bb in zip(p['Whh'],p['bhh'])])
    rr=expit(gi[:H]+gh[:H]);zz=expit(gi[H:2*H]+gh[H:2*H])
    hh=(1-zz)*np.tanh(gi[2*H:]+rr*gh[2*H:])+zz*h
    def linear(A,v,b):return np.array([sum(float(a)*float(x) for a,x in zip(row,v))+bb for row,bb in zip(A,b)])
    aa=np.maximum(linear(p['A'],hh,p['a']),0);bb=np.maximum(linear(p['B'],aa,p['b']),0)
    ww=w+p['scale']*linear(p['C'],bb,p['cc'])
    return (ww,hh) if c else (w,h)

def main():
    begin=time.monotonic();fit=get(HERE/'DEVELOPED_FIT.json');common=get(HERE/'COMMON_FIT.json')
    raw=arrays(PREV/'CAPPED_ROWS.npz');bank=arrays(OLD/'artifacts/baselines/nested_growth_bank.npz')
    cb=arrays(HERE/'COMMON_GROWTH_BANK.npz');boot=arrays(HERE/'COMMON_SOURCE_BOOTSTRAP.npz');ob=arrays(HERE/'SOURCE_BOOTSTRAP.npz')
    model=load_rnn(OLD/'artifacts/rnn/rnnglm32_nested_best.npz')
    s=next(iter(raw));a=raw[s];cr=fit['prefix'][s]['gru'];state=dict(w=np.array(cr['endpoint']),h=np.array(cr['hidden_endpoint']))
    errors=[];omit=[]
    for x,c,r,day in ((.5,-1,1,False),(-1,1,1,True),(.25,0,-1,True),(-.5,-1,-1,False)):
        w,h=scalar_step(model,state,x,c,r,day);v={k:z[None,:].copy() for k,z in state.items()}
        model.update(v,np.array([x]),np.array([c]),np.array([r]),session_start=day)
        errors.extend([np.max(abs(v['w'][0]-w)),np.max(abs(v['h'][0]-h))])
        if not c:omit.append(max(np.max(abs(v['w'][0]-state['w'])),np.max(abs(v['h'][0]-state['h']))))
    assert max(errors)<1e-13 and max(omit)==0
    # Poison EVERY factual future contrast/choice/reward/probabilityLeft value.
    # Preserve only the explicitly conditioned opportunity/session vector.
    poisoned=a.copy();rng=np.random.default_rng(281)
    poisoned[1000:,:6]=rng.normal(50,20,poisoned[1000:,:6].shape)
    chronology={}
    for name in ('frozen_growth','common_hybrid','gru'):
        first,_=simulate(s,a,name,model,fit,common,bank,cb,boot,ob,n=16)
        second,_=simulate(s,poisoned,name,model,fit,common,bank,cb,boot,ob,n=16)
        chronology[name]=int(np.max(abs(first-second)))
        assert np.array_equal(first,second)
    # Capture actual generated stimuli/choices from the unchanged original
    # rollout to verify our new exact100 summaries, not just the old>=.5 target.
    import rollout
    captured={};original=rollout.trajectory_summary
    def capture(x,c,*args,**kwargs):
        captured['x']=x;captured['c']=c
        return original(x,c,*args,**kwargs)
    rollout.trajectory_summary=capture
    n=32
    rollout.autonomous(None,subject(a[:1000]),a[1000:3000,6].astype(bool),bank,n_particles=n,
                      seed=original_seed(s),subject=s,competence='growth')
    reproduced,_=simulate(s,a,'frozen_growth',model,fit,common,bank,cb,boot,ob,n=n)
    exact=[]
    for b,horizon in enumerate((200,500,1000,2000)):
        x=captured['x'][:,:horizon];c=captured['c'][:,:horizon]
        for j,sign in ((0,-1),(2,1)):
            exact.extend([int(np.max(abs((x==sign).sum(1)-reproduced[:,b,j]))),
                          int(np.max(abs(((x==sign)&(c==-sign)).sum(1)-reproduced[:,b,j+1])))])
    assert max(exact)==0
    structural={}
    for file in ('GENERATED_COUNTS.npz','COMMON_GENERATED_COUNTS.npz','RETAINED_GROWTH_COUNTS.npz'):
        z=arrays(HERE/file);v=z['samples'];obs=z['observed'];checks=[]
        for j,h in enumerate(z['horizons']):
            q=v[:,:,:,j];checks.append(bool((q>=0).all() and (q<=h).all() and
                    (q[...,1]<=q[...,0]).all() and (q[...,3]<=q[...,2]).all()))
        assert all(checks)
        structural[file]=dict(count_support_valid=True,subjects=len(z['subjects']),shape=list(v.shape))
    save('AUDIT.json',dict(utc=utc(),scalar_gru_max_error=float(max(errors)),omission_update_error=float(max(omit)),
         future_poison_max_count_difference=chronology,original_rollout_exact100_max_count_error=max(exact),
         structural=structural,seconds=time.monotonic()-begin,io=dict(IO),pins=PINS,
         note='Numerical and information checks on consumed contexts. This is not independent biological validation or full reproduction of source fitting.'))
    print('AUDIT PASS',max(errors),chronology,max(exact),'seconds',time.monotonic()-begin,flush=True)

if __name__=='__main__':main()
