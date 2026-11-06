"""Autonomous forecasts; future arguments contain opportunities, never outcomes.

An actual-input replay is separately named and tagged as a conditional
diagnostic. It is not permitted as the main autonomous forecast.
"""
import numpy as np
from scipy.special import expit, logit
from learning_models import features, subject_arrays
from baselines import draw_initial, competence_at, omission_at, fit_competence, subset
from trainer import VectorTrainer

METRICS=['left_high_correct','right_high_correct','right_choice_share','omission']


def trajectory_summary(signed_contrast, choice, bin_size=500):
    """Observable curve. High-contrast accuracy counts no-response as failure.

    Right-choice share uses every task trial, so omission is a separate
    recorded response category. Empty side cells are missing, never zero.
    """
    x=np.asarray(signed_contrast);c=np.asarray(choice)
    if x.ndim==1:x=x[None,:];c=c[None,:]
    nb=x.shape[1]//bin_size
    out=np.full((x.shape[0],nb,4),np.nan);denom=np.zeros((x.shape[0],nb,4),int)
    for b in range(nb):
        xx=x[:,b*bin_size:(b+1)*bin_size];cc=c[:,b*bin_size:(b+1)*bin_size]
        for j,sgn in enumerate([-1,1]):
            mask=(np.abs(xx)>=.5-1e-9)&(np.sign(xx)==sgn)
            den=mask.sum(axis=1);num=(mask&(cc==-sgn)).sum(axis=1)
            out[:,b,j]=np.divide(num,den,out=np.full(len(den),np.nan),where=den>0)
            denom[:,b,j]=den
        out[:,b,2]=(cc<0).mean(axis=1);out[:,b,3]=(cc==0).mean(axis=1)
        denom[:,b,2:]=bin_size
    return out,denom


def calibration_particles(model,prefix,n_particles,seed,method='map'):
    """Prefix-only MAP and local likelihood uncertainty propagated to endpoint.

    A finite-difference sensitivity of the causal recurrence gives the Fisher
    matrix for three initial GLM coefficients. No update-law coefficient is
    refitted. This approximate calibration is checked in synthetic recovery.
    """
    rng=np.random.default_rng(seed);state=model.initial_state(prefix,method=method)
    _,c,_,_=subject_arrays(prefix);ok=c!=0
    if method=='static':
        _,cov,_=fit_competence(prefix)
    else:
        w0=state['w0'];eps=1e-3;ds=[];de=[]
        p,_,end=model.sequence(prefix,w0)
        for j in range(3):
            v=np.eye(3)[j]*eps
            a,_,ae=model.sequence(prefix,w0+v);b,_,be=model.sequence(prefix,w0-v)
            ds.append((logit(np.clip(a,1e-7,1-1e-7))-logit(np.clip(b,1e-7,1-1e-7)))/(2*eps))
            de.append((ae-be)/(2*eps))
        D=np.stack(ds,axis=1);J=np.stack(de,axis=1)
        H=np.einsum('ni,n,nj->ij',D[ok],p[ok]*(1-p[ok]),D[ok])+.5*np.eye(3)
        cov=J@np.linalg.inv(H)@J.T
    ev,U=np.linalg.eigh((cov+cov.T)/2)
    cov=(U*np.clip(ev,1e-7,4.))@U.T
    w=rng.multivariate_normal(state['w'],cov,size=n_particles)
    return dict(w=w),dict(w0=np.asarray(state['w0']).tolist(),endpoint=np.asarray(state['w']).tolist(),
                         endpoint_covariance=cov.tolist(),method=method)


def autonomous(model,prefix,future_session_start,bank,n_particles=256,seed=0,
               protocol='standard',subject=None,competence=None,neighbors=15,
               calibration_method='map',omission_mode='growth',trainer_options=None,
               bin_size=500,replay_signed_contrast=None,reset_weights=False,
               weight_retention=1.0):
    """Generate all post-prefix decisions, feedback, updates and trainer state.

    ``future_session_start`` is the ONLY realized future input in the primary
    mode. It expresses a forecast conditional on training opportunities. A
    replay argument is an explicitly labeled sensitivity and never primary.
    """
    future_session_start=np.asarray(future_session_start,bool);H=len(future_session_start)
    rng=np.random.default_rng(seed+101)
    common=draw_initial(prefix,bank,n_particles,seed+211,exclude=subject,
                        neighbors=neighbors,competence=competence or 'growth')
    if competence is None:
        state,calibration=calibration_particles(model,prefix,n_particles,seed+313,calibration_method)
    else:
        if competence=='persistence':
            # A truly fixed-competence animal benefits from using every
            # calibration observation. The shared engagement bank still uses
            # exactly the same recent-prefix conditioning as the other actors.
            w,cov,_=fit_competence(prefix,ridge=.5)
            wb=np.random.default_rng(seed+313).multivariate_normal(w,cov,size=n_particles)
            common['anchor']=wb;common['w']=wb.copy();common['delta_w'][:]=0
            calibration=dict(endpoint=w.tolist(),method='all1000_static')
        else:calibration=dict(endpoint=common['current_fit'].tolist(),method='last500_static')
        state=dict(w=common['w'].copy())
    initial_w=state['w'].copy()
    trainer=VectorTrainer.from_prefix(prefix,n_particles,seed+419,protocol,**(trainer_options or {}))
    initial_trainer=trainer.state_summary()
    xs=np.empty((n_particles,H));cs=np.empty((n_particles,H),np.int8)
    # Keep latent summaries for diagnostics, not as the scored observable.
    ww=np.empty((n_particles,H//bin_size,3));pools=[]
    for t in range(H):
        if future_session_start[t]:
            trainer.new_session()
            if reset_weights:state['w']=initial_w.copy()
            elif weight_retention!=1.0:state['w']=state['w']*weight_retention
        task=trainer.sample();x=task['signed_contrast']
        if replay_signed_contrast is not None:
            # Replaying actual adaptive inputs is deliberately a separate
            # conditional diagnostic. Feedback still follows generated action.
            xx=float(replay_signed_contrast[t]);x=np.full(n_particles,xx)
            side=task['side'].copy() if xx==0 else np.full(n_particles,-1 if np.signbit(xx) else 1)
            trainer.current['side']=side
            trainer.current['contrast']=np.abs(x)
            trainer.current['correct_choice']=-side
        if competence is not None:state['w']=competence_at(common,t)
        p=expit(np.sum(state['w']*features(x),axis=-1))
        omit=omission_at(common,t,omission_mode)
        choice=np.where(rng.random(n_particles)<p,-1,1).astype(np.int8)
        choice[rng.random(n_particles)<omit]=0
        feedback=trainer.observe(choice)
        if competence is None:
            model.update(state,x,choice,feedback['feedbackType'],session_start=bool(future_session_start[t]))
        xs[:,t]=x;cs[:,t]=choice
        if (t+1)%bin_size==0:
            ww[:,t//bin_size]=state['w']
            pools.append(trainer.pool.mean(axis=0))
    curves,counts=trajectory_summary(xs,cs,bin_size)
    return dict(samples=curves,counts=counts,weights=ww,pool_fraction=np.array(pools),
                calibration=calibration,initial_trainer=initial_trainer,
                mode='actual_schedule_replay_diagnostic' if replay_signed_contrast is not None else 'autonomous',
                seed=seed,n_particles=n_particles,protocol=protocol)


def conditional(model,prefix,future,bank,n_particles=256,seed=0,subject=None,bin_size=500,
                calibration_method='map',omission_mode='growth'):
    """Teacher-forced probabilities, with valid sequential log scores.

    The curve samples hold real histories fixed. They are descriptive
    conditional diagnostics and do not define autonomous joint trajectories.
    """
    state=model.initial_state(prefix,method=calibration_method)
    p,w,_=model.sequence(future,state['w']);s,c,_,_=subject_arrays(future)
    ok=c!=0;y=(c<0).astype(float);q=np.clip(p,1e-8,1-1e-8)
    nll=(-y*np.log(q)-(1-y)*np.log1p(-q))[ok]
    common=draw_initial(prefix,bank,n_particles,seed+211,exclude=subject)
    rng=np.random.default_rng(seed+101);H=len(c)
    cc=np.empty((n_particles,H),np.int8);omitp=np.empty(H)
    for t in range(H):
        omit=omission_at(common,t,omission_mode);omitp[t]=omit.mean()
        choice=np.where(rng.random(n_particles)<p[t],-1,1).astype(np.int8)
        choice[rng.random(n_particles)<omit]=0;cc[:,t]=choice
    catp=np.where(c==0,omitp,(1-omitp)*np.where(c<0,p,1-p))
    curves,counts=trajectory_summary(np.broadcast_to(s,cc.shape),cc,bin_size)
    return dict(samples=curves,counts=counts,prob_right=p,weights=w,
                binary_nll=float(np.mean(nll)),categorical_nll=float(-np.log(np.clip(catp,1e-9,1)).mean()),
                n_response=int(ok.sum()),mode='teacher_forced_diagnostic')
