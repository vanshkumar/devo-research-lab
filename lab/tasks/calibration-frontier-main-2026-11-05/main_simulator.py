"""Frozen main simulator with cached original prefix inference and causal views."""
import numpy as np
from scipy.special import expit,logit
import source_models as sm
from source_models import inherited as e
from pilot import subject,track
from baselines import draw_initial,competence_at,omission_at
from trainer import VectorTrainer
from rnn_rollout import calibration_particles


def causal_view(a,cutoff):
    out=np.full((3000,7),np.nan)
    out[:cutoff]=a[:cutoff]
    out[:,6]=a[:3000,6]
    assert np.isnan(out[cutoff:,:6]).all()
    return out


def initial_neural(model,a,cutoff,n,stream):
    prefix=subject(a[:cutoff])
    state,info=calibration_particles(model,prefix,n,stream+313)
    return state,info


def exact_initial_neural(model,a,cutoff,n,stream,info):
    prefix=subject(a[:cutoff]);rng=np.random.default_rng(stream+313)
    delta=rng.multivariate_normal(np.zeros(3),np.asarray(info['initial_covariance']),size=n)
    delta*=info['endpoint_sd_cap_factor']
    w=[];h=[]
    for v in delta:
        _,_,end=model.sequence(prefix,np.asarray(info['w0'])+v)
        w.append(end['w']);h.append(end['h'])
    return dict(w=np.array(w),h=np.array(h))


def simulate(s,a,cutoff,name,model,canonical,candidate=None,half=None,n=256,
             condition='primary',input_fit=None,lab=None,engagement_fit=None,
             stream_offset=0,neural_state=None):
    assert a.shape==(3000,7) and np.isnan(a[cutoff:,:6]).all()
    stream=e.original_seed(s)+stream_offset;prefix=subject(a[:cutoff])
    shared=draw_initial(prefix,canonical,n,stream+211,exclude=s,neighbors=15,competence='growth')
    if name=='gru':
        if neural_state is None:state,_=initial_neural(model,a,cutoff,n,stream)
        else:state={k:v.copy() for k,v in neural_state.items()}
    elif name=='recent_growth':choice=e.choice_draw(s,a,cutoff,half,candidate,n,stream)
    if cutoff==1000:action=np.random.default_rng(stream+101);teacher_seed=stream+419
    else:action=np.random.default_rng(stream+900101);teacher_seed=stream+900419
    if condition=='source_context_input':
        teacher=sm.SourceContextTrainer.from_prefix(prefix,n,teacher_seed,'standard',input_fit=input_fit,lab=lab)
    else:teacher=VectorTrainer.from_prefix(prefix,n,teacher_seed,'standard')
    cc=sm.causal_contexts(a[:cutoff]);position=int(cc['position'][-1])+1
    previous=np.full(n,a[cutoff-1,2]==0,dtype=float)
    counts=np.zeros((n,7),np.int32);saved=[]
    blocks=[];block=np.zeros(n,np.int32)
    for absolute in range(cutoff,3000):
        t=absolute-cutoff
        if absolute==1000 and cutoff<1000:
            action=np.random.default_rng(stream+101);teacher.rng=np.random.default_rng(stream+419)
        day=bool(a[absolute,6])
        if day:teacher.new_session();position=0;previous[:]=0
        task=teacher.sample();x=task['signed_contrast'];f=track.psych(x)
        if name=='gru':p=model.probs(state,x)
        elif name=='growth':p=expit(np.sum(competence_at(shared,t)*f,axis=1))
        else:p=expit(np.sum(competence_at(choice,t)*f,axis=1))
        q=omission_at(shared,t,'growth')
        if condition=='source_calibrated_engagement':
            b=np.asarray(engagement_fit[cutoff]['beta'])
            q=expit(b[0]+b[1]*logit(np.clip(q,1e-12,1-1e-12))+b[2]*np.log1p(position/50)+b[3]*previous)
        c=np.where(action.random(n)<p,-1,1).astype(np.int8)
        c[action.random(n)<q]=0;feedback=teacher.observe(c)
        if name=='gru':model.update(state,x,c,feedback['feedbackType'],session_start=day)
        if absolute>=1000:
            for j,sign in ((0,-1),(2,1)):
                keep=x==sign;counts[:,j]+=keep;counts[:,j+1]+=keep&(c==-sign)
            counts[:,4]+=c==0;counts[:,5]+=c<0;counts[:,6]+=feedback['correct']
            block+=c==0
            if (absolute+1-1000)%50==0:blocks.append(block.copy());block[:]=0
        previous=(c==0).astype(float);position+=1
        if absolute+1 in (1500,3000):saved.append(counts.copy())
    out=np.stack(saved,axis=1)
    assert np.isfinite(out).all() and (out>=0).all()
    assert (out[:,:,1]<=out[:,:,0]).all() and (out[:,:,3]<=out[:,:,2]).all()
    assert (out[:,:,4]<=np.array([500,2000])[None,:]).all()
    return out,np.stack(blocks,axis=1)
