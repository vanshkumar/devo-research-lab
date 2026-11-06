"""Matched prefix-limited development forecasts with own generated teacher history."""
import time
import resource
import json
import hashlib
import numpy as np
from scipy.special import expit
from scipy.spatial.distance import cdist
from pilot import (HERE,PREV,OLD,REV,IO,PINS,read,get,save,arrays,seed,utc,cal,track,subject,
                   VectorTrainer)
from rnn_learning import load_rnn
from develop import NAMES

N=144
H=2000
HORIZONS=(200,500,1000,2000)

def gru_particles(model,a,cr,rng,n):
    prefix=subject(a[:1000]); w0=np.asarray(cr['w0'])
    _,_,end=model.sequence(prefix,w0); jw=[];jh=[]
    for j in range(3):
        v=np.eye(3)[j]*1e-3
        up=model.sequence(prefix,w0+v)[2]; down=model.sequence(prefix,w0-v)[2]
        jw.append((up['w']-down['w'])/2e-3);jh.append((up['h']-down['h'])/2e-3)
    jw=np.stack(jw,axis=1);jh=np.stack(jh,axis=1)
    cov=np.asarray(cr['initial_covariance']);factor=cr['endpoint_sd_cap_factor']
    delta=rng.multivariate_normal(np.zeros(3),cov,n)*factor
    w=end['w']+delta@jw.T;h=np.clip(end['h']+delta@jh.T,-1,1)
    error=max(float(np.max(np.abs(end['w']-cr['endpoint']))),float(np.max(np.abs(end['h']-cr['hidden_endpoint']))))
    assert error<1e-10
    return dict(w=w,h=h),error

def empirical_summary(x,c,stop):
    x=x[:stop];c=c[:stop]
    out=[]
    for s in (-1,1):
        mask=x==s
        out.extend([int(mask.sum()),int((mask&(c==-s)).sum())])
    out.extend([int((c==0).sum()),int((c<0).sum()),int(((x!=0)&(c==-np.sign(x))).sum())])
    return out

def crps(sample,y):
    v=np.sort(sample); n=len(v)
    return float(np.abs(v-y).mean()-np.sum((2*np.arange(n)-n+1)*v)/(n*n))

def score_counts(samples,observed,horizon):
    # Side order is (N_L,K_L,N_R,K_R); exact opportunity units fixed in advance.
    joint=[];count=[];ratio=[];er=[];pooled=[];ratio_mass=[];ind_mae=[]
    coverage=[]
    for j in (0,2):
        n,k=samples[:,j],samples[:,j+1];on,ok=observed[j:j+2]
        v=np.column_stack([k,n-k,horizon-n])/horizon
        y=np.array([ok,on-ok,horizon-on])/horizon
        joint.append(float(np.linalg.norm(v-y,axis=1).mean()-cdist(v,v).mean()/2))
        count.append(crps(n/horizon,on/horizon))
        use=n>0; a=k[use]/n[use]; actual=ok/on
        ratio.append(crps(a,actual));er.append(float(a.mean()));pooled.append(float(k.mean()/n.mean()))
        ratio_mass.append(float(use.mean()));ind_mae.append(float(abs(a.mean()-actual)))
        interval=np.quantile(a,[.1,.9]);coverage.append(bool(interval[0]<=actual<=interval[1]))
    return dict(joint=float(np.mean(joint)),count=float(np.mean(count)),ratio_crps=float(np.mean(ratio)),
                expected_ratio=er,count_pooled=pooled,positive_count_mass=ratio_mass,
                equal_side_mae=float(np.mean(ind_mae)),ratio_80_coverage=float(np.mean(coverage)),
                omission_crps=crps(samples[:,4]/horizon,observed[4]/horizon),
                all_correct_crps=crps(samples[:,6]/horizon,observed[6]/horizon),
                expected_omission=float(samples[:,4].mean()/horizon),
                expected_all_correct=float(samples[:,6].mean()/horizon))

def simulate(model,name,a,prefix,fit,bank,boot,n=N,horizon=H,uncertain=True,teacher_options=None):
    rng=np.random.default_rng(seed(name)+seed(str(a[0,:3]))+77)
    # Caller uses animal-specific stream; common random numbers across laws.
    rng=np.random.default_rng(int(teacher_options.pop('simulation_seed')) if teacher_options and 'simulation_seed' in teacher_options else 789)
    source_index=np.arange(n)%12
    base=[]
    for b,cov in zip(prefix['base'],prefix['cov']):
        b=np.asarray(b);cov=np.asarray(cov)
        base.append(rng.multivariate_normal(b,cov,n) if uncertain else np.tile(b,(n,1)))
    drift=np.zeros((horizon,n,3))
    # Reuse one donor per particle where possible, preserving its path dependence.
    pools=[np.asarray(v) for v in prefix['donor_pools']]
    chosen=rng.choice(pools[0],n)
    for b in range((horizon+499)//500):
        pool=pools[b]; use=chosen.copy(); missing=~np.isin(use,pool)
        use[missing]=rng.choice(pool,int(missing.sum()))
        dw=bank['delta'][use,b]
        drift[b*500:min(horizon,(b+1)*500)]=dw
    state=dict(trace=np.tile(prefix['trace'],(n,1,1)),w=np.zeros((n,3)),omission=np.zeros(n))
    reference_error=0.
    if name=='gru':state.update(gru_particles(model,a,prefix['gru'],rng,n)[0]);reference_error=gru_particles(model,a,prefix['gru'],np.random.default_rng(91),1)[1]
    if uncertain:
        history_choice=boot['history_choice'][source_index]
        history_omit=boot['history_omit'][source_index]
        hybrid_choice=boot['hybrid_choice'][source_index]
    else:
        history_choice=np.tile(fit['history_coeff'][0],(n,1));history_omit=np.tile(fit['history_coeff'][1],(n,1))
        hybrid_choice=np.tile(fit['hybrid_coeff'][0],(n,1))
    tr=VectorTrainer.from_prefix(subject(a[:1000]),n,seed(str(a.shape))+913,'standard',**(teacher_options or {}))
    # Seed overwritten by caller from the recorded animal-specific seed.
    tr.rng=np.random.default_rng(rng.integers(0,2**32))
    before=dict(pool=tr.pool[0].tolist(),reward=float(tr.reward_ul[0]))
    counts=np.zeros((n,7),np.int32);saved=[];pos=prefix['pos']
    for t in range(horizon):
        day=bool(a[1000+t,6])
        if day:
            tr.new_session();state['trace'][:,:2]=0;pos=0;state['omission']*=.85
            if name in ('history_track','growth_track'):state['w']*=.85
        task=tr.sample();x=task['signed_contrast'];f=track.psych(x)
        matrices=cal.predictors(x,1000+t,pos,state['trace'])[2]
        qlog=np.einsum('ij,ij->i',cal.omission_basis(x),base[1])+np.einsum('ij,ij->i',matrices[1],history_omit)+state['omission']
        q=expit(qlog)
        if name=='gru':p=model.probs(state,x)
        else:
            logit=np.einsum('ij,ij->i',cal.signed_basis(x),base[0])
            if name in ('growth','growth_track'):logit+=np.einsum('ij,ij->i',f,drift[t])
            if name in ('history_track','growth_track'):
                beta=history_choice if name=='history_track' else hybrid_choice
                logit+=np.einsum('ij,ij->i',matrices[0],beta)+np.einsum('ij,ij->i',f,state['w'])
            p=expit(logit)
        c=np.where(rng.random(n)<p,-1,1).astype(np.int8);c[rng.random(n)<q]=0
        feedback=tr.observe(c);r=feedback['feedbackType']
        for j,s in ((0,-1),(2,1)):
            select=x==s;counts[:,j]+=select;counts[:,j+1]+=select&(c==-s)
        counts[:,4]+=c==0;counts[:,5]+=c<0;counts[:,6]+=feedback['correct']
        if name=='gru':model.update(state,x,c,r,session_start=day)
        if name in ('history_track','growth_track'):
            state['w']*=.996
            state['w']+=fit['select'][name]['eta']*(((c<0)-p)*(c!=0))[:,None]*f
        state['omission']=.996*state['omission']+fit['omission_eta']*((c==0)-q)
        ev=cal.signal(x,c,r);trace=state['trace'];trace[:,0]=ev
        trace[:,1]=cal.FAST*trace[:,1]+(1-cal.FAST)*ev
        trace[:,2]=cal.SLOW*trace[:,2]+(1-cal.SLOW)*ev
        pos+=1
        if t+1 in HORIZONS:saved.append(counts.copy())
    assert np.isfinite(state['w']).all() and np.isfinite(state['trace']).all()
    return np.stack(saved,axis=1),dict(reference_error=reference_error,teacher_initial=before)

def main():
    begin=time.monotonic();fit=get(HERE/'DEVELOPED_FIT.json');ev=arrays(PREV/'CAPPED_ROWS.npz')
    bank=arrays(HERE/'GROWTH_BANK.npz');boot=arrays(HERE/'SOURCE_BOOTSTRAP.npz')
    modelpath=OLD/'artifacts/rnn/rnnglm32_nested_best.npz';read(modelpath,'c7f675d18f4143891ed7d2c76d91f74be74da9565fbae5407952768e2c146940')
    model=load_rnn(modelpath);names=NAMES
    freeze=dict(utc=utc(),particles=N,horizon=H,horizons=HORIZONS,names=names,roster=list(ev),
         sources=PINS.copy(),code_sha256=hashlib.sha256(read(HERE/'generate.py')).hexdigest(),
         target='exact signed100 count/success joint energy, accuracy-ratio CRPS and count CRPS; all correct/omission CRPS; mean ratio and count pooling kept separate',
         information='first1000 only; factual future opportunity/session boundaries conditional; default source teacher generates all future stimuli, choices, feedback. No actual future stimulus enters.',
         uncertainty='prefix ridge/Laplace draws, original correlated GRU prefix Fisher states, whole-original-fitting-animal bootstrap of shared simple coefficients, empirical donor trajectories. No source neural refit/uncertainty or posterior claim.',
         teacher_qualification='default source input kernel has saved actual violations in11/64; generation is a qualified model-based development calculation, not certified autonomous biological validation',
         seed_rule='SHA256 subject ID first4 little endian +20261105; same per-person streams across models')
    save('GENERATION_FREEZE.json',freeze)
    sims=[];scores={};observed=[];checks={}
    for i,(s,a) in enumerate(ev.items()):
        p=fit['prefix'][s]; x=np.nan_to_num(a[:,1])-np.nan_to_num(a[:,0]);c=a[:,2]
        obs=np.array([empirical_summary(x[1000:],c[1000:],h) for h in HORIZONS]);observed.append(obs)
        current=[];scores[s]={};checks[s]={}
        for name in names:
            stream=seed(s)+20261105
            sample,check=simulate(model,name,a,p,fit,bank,boot,
                                  teacher_options=dict(simulation_seed=stream))
            current.append(sample);checks[s][name]=check
            scores[s][name]={str(h):score_counts(sample[:,j],obs[j],h) for j,h in enumerate(HORIZONS)}
        sims.append(np.stack(current))
        if (i+1)%4==0:print('Generated',i+1,'/64 seconds',round(time.monotonic()-begin,1),flush=True)
    sims=np.stack(sims);obs=np.stack(observed)
    np.savez_compressed(HERE/'GENERATED_COUNTS.npz',samples=sims,observed=obs,subjects=list(ev),names=names,horizons=HORIZONS)
    save('GENERATED_SCORES.json',dict(utc=utc(),per_animal=scores,checks=checks,seconds=time.monotonic()-begin,
          io=dict(IO),peak_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss))
    print('SAVED',utc(),'seconds',time.monotonic()-begin,flush=True)

if __name__=='__main__':main()
