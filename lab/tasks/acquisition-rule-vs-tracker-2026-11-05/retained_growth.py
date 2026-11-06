"""Retain original strong growth construction and share its omission law fairly."""
import time
import hashlib
import resource
import numpy as np
from scipy.special import expit
from pilot import (HERE,PREV,OLD,IO,PINS,read,get,save,arrays,seed,utc,cal,track,subject,VectorTrainer)
from baselines import draw_initial,competence_at,omission_at
from rnn_learning import load_rnn
from generate import gru_particles,empirical_summary,score_counts,HORIZONS
from common_generate import setup

N=256
H=2000
NAMES=('frozen_growth','common_hybrid','gru')

def original_seed(s):return int(hashlib.sha256(s.encode()).hexdigest()[:8],16)%(2**31-1)

def simulate(s,a,name,model,fit,common,bank,commonbank,boot,oldboot,n=N):
    stream=original_seed(s);prefix=subject(a[:1000])
    shared=draw_initial(prefix,bank,n,stream+211,exclude=s,neighbors=15,competence='growth')
    neural,error=gru_particles(model,a,fit['prefix'][s]['gru'],np.random.default_rng(stream+313),n)
    initial=setup(s,a,model,fit,common,commonbank,boot,oldboot,n=n) if name=='common_hybrid' else None
    # Anchor uses the EXACT same neural prefix draw as the neural law here.
    anchor=neural['w'].copy();online=np.zeros((n,3));state={k:v.copy() for k,v in neural.items()}
    trace=np.tile(fit['prefix'][s]['trace'],(n,1,1));pos=fit['prefix'][s]['pos']
    action=np.random.default_rng(stream+101);teacher=VectorTrainer.from_prefix(prefix,n,stream+419,'standard')
    counts=np.zeros((n,7),np.int32);saved=[];first=None
    for t in range(H):
        day=bool(a[1000+t,6])
        if day:teacher.new_session();trace[:,:2]=0;pos=0;online*=.85
        task=teacher.sample();x=task['signed_contrast'];f=track.psych(x)
        q=omission_at(shared,t,'growth')
        if name=='frozen_growth':pr=expit(np.sum(competence_at(shared,t)*f,axis=1))
        elif name=='gru':pr=model.probs(state,x)
        else:
            X=cal.predictors(x,1000+t,pos,trace)[2][0]
            cue=np.abs(x[:,None]-initial['cues']).argmin(1)
            pr=expit(np.einsum('ij,ij->i',f,anchor+initial['curves'][t])+
                     np.einsum('ij,ij->i',X-initial['origin'][cue],initial['beta'])+
                     np.einsum('ij,ij->i',f,online))
        if t==0 and name!='frozen_growth':
            first=float(np.max(np.abs(pr-model.probs(neural,x))));assert first<1e-14
        c=np.where(action.random(n)<pr,-1,1).astype(np.int8);c[action.random(n)<q]=0
        result=teacher.observe(c);r=result['feedbackType']
        for j,side in ((0,-1),(2,1)):
            keep=x==side;counts[:,j]+=keep;counts[:,j+1]+=keep&(c==-side)
        counts[:,4]+=c==0;counts[:,5]+=c<0;counts[:,6]+=result['correct']
        if name=='gru':model.update(state,x,c,r,session_start=day)
        if name=='common_hybrid':online=.996*online+common['eta']*(((c<0)-pr)*(c!=0))[:,None]*f
        ev=cal.signal(x,c,r);trace[:,0]=ev;trace[:,1]=cal.FAST*trace[:,1]+(1-cal.FAST)*ev
        trace[:,2]=cal.SLOW*trace[:,2]+(1-cal.SLOW)*ev;pos+=1
        if t+1 in HORIZONS:saved.append(counts.copy())
    return np.stack(saved,axis=1),dict(prefix_reference_error=error,first_neural_policy_error=first)

def main():
    begin=time.monotonic();fit=get(HERE/'DEVELOPED_FIT.json');common=get(HERE/'COMMON_FIT.json')
    ev=arrays(PREV/'CAPPED_ROWS.npz');bp=OLD/'artifacts/baselines/nested_growth_bank.npz'
    read(bp,'036f3cfedd56e915b051fb29a80a2622cf5a747366ea31aa46b9249a922eea01');bank=arrays(bp)
    roster=get(OLD/'artifacts/models/DEVELOPMENT_MODEL_SPLIT.json')['train']
    assert set(bank['subjects'])<=set(roster)
    # Eligibility of the full original donor windows was saved before raw read.
    proof=get(HERE/'SOURCE_FIT6000_MANIFEST.json');assert all(s in proof['exposure_proof'] for s in bank['subjects'])
    cb=arrays(HERE/'COMMON_GROWTH_BANK.npz');boot=arrays(HERE/'COMMON_SOURCE_BOOTSTRAP.npz');ob=arrays(HERE/'SOURCE_BOOTSTRAP.npz')
    path=OLD/'artifacts/rnn/rnnglm32_nested_best.npz';read(path,'c7f675d18f4143891ed7d2c76d91f74be74da9565fbae5407952768e2c146940');model=load_rnn(path)
    save('RETAINED_GROWTH_FREEZE.json',dict(utc=utc(),particles=N,horizon=H,horizons=HORIZONS,names=NAMES,roster=list(ev),
         pins=PINS.copy(),code_sha256=hashlib.sha256(read(HERE/'retained_growth.py')).hexdigest(),
         information='Original prefix-last500 growth anchor, original ridge Gaussian and beta omission calibration, nearest15 donor paths, original adaptive teacher, own future choices/rewards. All actors share original donor omission law and common action/trainer streams.',
         note='Retained frozen growth weights/bank and per-person construction. New 2000-opportunity exact100 functional remains development; no old gate retuned. Common hybrid retains neural prefix initialization cost.'))
    allsamples=[];observed=[];scores={};checks={};reference={}
    for i,(s,a) in enumerate(ev.items()):
        x=np.nan_to_num(a[:,1])-np.nan_to_num(a[:,0]);c=a[:,2]
        obs=np.array([empirical_summary(x[1000:],c[1000:],h) for h in HORIZONS]);observed.append(obs)
        sample=[];scores[s]={};checks[s]={}
        for name in NAMES:
            sim,check=simulate(s,a,name,model,fit,common,bank,cb,boot,ob)
            sample.append(sim);checks[s][name]=check
            scores[s][name]={str(h):score_counts(sim[:,j],obs[j],h) for j,h in enumerate(HORIZONS)}
            if i==0 and name=='frozen_growth':
                # Execute the unchanged reference on identical streams. Its
                # accuracy target uses>=.5, so compare exact all-trial moments.
                from rollout import autonomous
                old=autonomous(None,subject(a[:1000]),a[1000:3000,6].astype(bool),bank,
                      n_particles=N,seed=original_seed(s),subject=s,competence='growth')
                err=[]
                for j,h in enumerate(HORIZONS):
                    if h%500:continue
                    for col,metric in ((4,3),(5,2)):
                        v=np.rint(old['samples'][:,:h//500,metric].sum(1)*500).astype(int)
                        err.append(int(np.max(np.abs(v-sim[:,j,col]))))
                assert max(err)==0;reference=dict(subject=s,reference_moment_max_integer_error=max(err),scope='unchanged original growth rollout; all-trial omission/right counts at500/1000/2000')
        allsamples.append(np.stack(sample))
        if (i+1)%8==0:print('Retained strong growth',i+1,'/64 seconds',round(time.monotonic()-begin,1),flush=True)
    np.savez_compressed(HERE/'RETAINED_GROWTH_COUNTS.npz',samples=np.stack(allsamples),observed=np.stack(observed),subjects=list(ev),names=NAMES,horizons=HORIZONS)
    save('RETAINED_GROWTH_SCORES.json',dict(utc=utc(),per_animal=scores,checks=checks,reference=reference,
         seconds=time.monotonic()-begin,io=dict(IO),peak_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss))
    print('SAVED',utc(),'seconds',time.monotonic()-begin,flush=True)

if __name__=='__main__':main()
