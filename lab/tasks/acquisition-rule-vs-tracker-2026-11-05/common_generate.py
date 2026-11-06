"""A future-updater ablation: same uncertain starting policy, strong simple growth."""
import time
import resource
import hashlib
import numpy as np
from scipy.special import expit
from numba import njit
from pilot import (HERE,PREV,OLD,IO,PINS,read,get,save,arrays,seed,utc,cal,track,subject,VectorTrainer)
from rnn_learning import load_rnn
from generate import gru_particles,empirical_summary,score_counts,HORIZONS
from common_state import smooth_growth

N=144
H=2000
NAMES=('common_growth','common_hybrid','gru')

@njit(cache=True)
def warm_omission(logits,c,day,eta):
    state=np.zeros(logits.shape[1])
    for t in range(len(c)):
        if day[t]:state*=.85
        for j in range(len(state)):
            q=1/(1+np.exp(-max(-40.,min(40.,logits[t,j]+state[j]))))
            state[j]=.996*state[j]+eta*((c[t]==0)-q)
    return state

def setup(s,a,model,fit,common,bank,boot,oldboot,n=N,uncertain=True):
    p=fit['prefix'][s];stream=seed(s)+20261105
    neural,error=gru_particles(model,a,p['gru'],np.random.default_rng(stream+313),n)
    if not uncertain:
        neural=dict(w=np.tile(p['gru']['endpoint'],(n,1)),h=np.tile(p['gru']['hidden_endpoint'],(n,1)))
    rng=np.random.default_rng(stream+211)
    ombase=rng.multivariate_normal(p['base'][1],p['cov'][1],n) if uncertain else np.tile(p['base'][1],(n,1))
    si=np.arange(n)%12
    ombeta=oldboot['history_omit'][si] if uncertain else np.tile(fit['history_coeff'][1],(n,1))
    beta=boot['beta'][si] if uncertain else np.tile(common['beta'],(n,1))
    d=cal.prepare(a);prefix=d.copy();prefix={k:v[:1000] for k,v in d.items()}
    tr,pos,_=cal.summarize_history(*(prefix[k] for k in ('x','c','r','day')))
    z=cal.predictors(prefix['x'],np.arange(1000),pos,tr)[2][1]
    logits=cal.omission_basis(prefix['x'])@ombase.T+z@ombeta.T
    omission=warm_omission(logits,prefix['c'],prefix['day'],fit['omission_eta'])
    origin=np.asarray(common['origin_features'][s]);cues=np.asarray(common['origin_cues'])
    pools=[np.asarray(v) for v in common['donor_pools'][s]]
    rng=np.random.default_rng(stream+511);chosen=rng.choice(pools[0],n);delta=[]
    for b in range(10):
        chosen_b=chosen.copy();missing=~np.isin(chosen_b,pools[b]);chosen_b[missing]=rng.choice(pools[b],int(missing.sum()))
        delta.append(bank['delta'][chosen_b,b])
    # Curve interpolation is deterministic once a source donor was sampled.
    curves=np.stack([smooth_growth(np.array(delta)[:,j],np.arange(H)) for j in range(n)],axis=1)
    return dict(neural=neural,reference_error=error,ombase=ombase,ombeta=ombeta,beta=beta,
                omission=omission,origin=origin,cues=cues,curves=curves,stream=stream)

def simulate(s,a,name,model,fit,common,initial,n=N,horizon=H,teacher_options=None):
    p=fit['prefix'][s];stream=initial['stream']
    action=np.random.default_rng(stream+101)
    state={k:v.copy() for k,v in initial['neural'].items()}
    anchor=state['w'].copy();online=np.zeros((n,3));omission=initial['omission'].copy()
    trace=np.tile(p['trace'],(n,1,1));pos=p['pos']
    teacher=VectorTrainer.from_prefix(subject(a[:1000]),n,stream+419,'standard',**(teacher_options or {}))
    counts=np.zeros((n,7),np.int32);out=[];first_error=None
    for t in range(horizon):
        day=bool(a[1000+t,6])
        if day:teacher.new_session();trace[:,:2]=0;pos=0;omission*=.85;online*=.85
        task=teacher.sample();x=task['signed_contrast'];f=track.psych(x)
        X,Z=cal.predictors(x,1000+t,pos,trace)[2]
        q=expit(np.einsum('ij,ij->i',cal.omission_basis(x),initial['ombase'])+
                np.einsum('ij,ij->i',Z,initial['ombeta'])+omission)
        if name=='gru':pr=model.probs(state,x)
        else:
            v=np.einsum('ij,ij->i',f,anchor+initial['curves'][t])
            if name=='common_hybrid':
                cue=np.abs(x[:,None]-initial['cues']).argmin(1)
                v+=np.einsum('ij,ij->i',X-initial['origin'][cue],initial['beta'])+np.einsum('ij,ij->i',f,online)
            pr=expit(v)
        if t==0:
            first_error=float(np.max(np.abs(pr-model.probs(initial['neural'],x))))
            assert first_error<1e-14,('Initial policies unmatched',s,name,first_error)
        c=np.where(action.random(n)<pr,-1,1).astype(np.int8);c[action.random(n)<q]=0
        result=teacher.observe(c);r=result['feedbackType']
        for j,side in ((0,-1),(2,1)):
            keep=x==side;counts[:,j]+=keep;counts[:,j+1]+=keep&(c==-side)
        counts[:,4]+=c==0;counts[:,5]+=c<0;counts[:,6]+=result['correct']
        if name=='gru':model.update(state,x,c,r,session_start=day)
        if name=='common_hybrid':
            online=.996*online+common['eta']*(((c<0)-pr)*(c!=0))[:,None]*f
        omission=.996*omission+fit['omission_eta']*((c==0)-q)
        ev=cal.signal(x,c,r);trace[:,0]=ev;trace[:,1]=cal.FAST*trace[:,1]+(1-cal.FAST)*ev
        trace[:,2]=cal.SLOW*trace[:,2]+(1-cal.SLOW)*ev;pos+=1
        if t+1 in HORIZONS:out.append(counts.copy())
    return np.stack(out,axis=1),first_error

def main():
    begin=time.monotonic();fit=get(HERE/'DEVELOPED_FIT.json');common=get(HERE/'COMMON_FIT.json')
    ev=arrays(PREV/'CAPPED_ROWS.npz');bank=arrays(HERE/'COMMON_GROWTH_BANK.npz')
    boot=arrays(HERE/'COMMON_SOURCE_BOOTSTRAP.npz');oldboot=arrays(HERE/'SOURCE_BOOTSTRAP.npz')
    path=OLD/'artifacts/rnn/rnnglm32_nested_best.npz';read(path,'c7f675d18f4143891ed7d2c76d91f74be74da9565fbae5407952768e2c146940');model=load_rnn(path)
    save('COMMON_GENERATION_FREEZE.json',dict(utc=utc(),code_sha256=hashlib.sha256(read(HERE/'common_generate.py')).hexdigest(),
          pins=PINS.copy(),particles=N,horizon=H,horizons=HORIZONS,names=NAMES,roster=list(ev),
          information='common original correlated uncertain neural prefix state; identical warmed omission law; own generated default teacher/choice/feedback; actual session opportunity boundaries only',
          controls='exact initial policy equality every cue; separate common action/trainer/calibration streams; original default-teacher violations remain; source-roster fit and donor path; no old gate change',
          limitation='This gives the simple challenger the neural prefix estimator and its cost. A positive or negative concerns incremental future update utility, not an end-to-end model family or training-cost claim.'))
    saved=[];observed=[];scores={};checks={}
    for i,(s,a) in enumerate(ev.items()):
        initial=setup(s,a,model,fit,common,bank,boot,oldboot)
        x=np.nan_to_num(a[:,1])-np.nan_to_num(a[:,0]);c=a[:,2]
        obs=np.array([empirical_summary(x[1000:],c[1000:],h) for h in HORIZONS]);observed.append(obs)
        sample=[];scores[s]={};checks[s]=dict(reference_error=initial['reference_error'])
        for name in NAMES:
            sim,error=simulate(s,a,name,model,fit,common,initial);sample.append(sim)
            checks[s][name]=dict(first_policy_error=error)
            scores[s][name]={str(h):score_counts(sim[:,j],obs[j],h) for j,h in enumerate(HORIZONS)}
        saved.append(np.stack(sample))
        if (i+1)%8==0:print('Common-state generation',i+1,'/64 seconds',round(time.monotonic()-begin,1),flush=True)
    np.savez_compressed(HERE/'COMMON_GENERATED_COUNTS.npz',samples=np.stack(saved),observed=np.stack(observed),
                        subjects=list(ev),names=NAMES,horizons=HORIZONS)
    save('COMMON_GENERATED_SCORES.json',dict(utc=utc(),per_animal=scores,checks=checks,
          seconds=time.monotonic()-begin,io=dict(IO),peak_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss))
    print('SAVED',utc(),'seconds',time.monotonic()-begin,flush=True)

if __name__=='__main__':main()
