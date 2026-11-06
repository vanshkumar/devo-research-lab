#!/usr/bin/env python3
"""Hidden-state-preserving forecasts for the separate postvalidation RNN test.

Imports frozen trainer, observation mapping and scores without changing them.
Default CLI uses development animals only. Protected reads require a separately
frozen challenge record; the external cohort still requires its source gate.
"""
from pathlib import Path
import argparse,hashlib,json,time
import numpy as np
from scipy.special import logit
from learning_models import subject_arrays
from rnn_learning import load_rnn
from baselines import draw_initial,omission_at,fit_competence,subset,load_bank
from trainer import VectorTrainer
from rollout import trajectory_summary
from evaluation import score
from data_io import exposure,load_subject,subjects
from run_forecasts import seed_for,get_prefix,collect,BANK

CAMP=Path(__file__).resolve().parents[1]
DEFAULT_MODEL=CAMP/'artifacts/rnn/main_best.npz'


def calibration_particles(model,prefix,n_particles,seed,method='map'):
    """Rank3 W0-Fisher uncertainty propagated jointly into weights and memory.

    The only fitted individual parameters are the three initial coefficients;
    GRU memory starts at zero and is produced by the prefix. Its uncertainty is
    correlated with the GLM state via the same three-dimensional perturbation.
    Linearized hidden states are clipped to the GRU's [-1,1] domain. At most a
    common scale cap keeps endpoint GLM covariance eigenvalues below4, preserving
    cross-state correlation. No additional free hidden parameter is fitted.
    """
    rng=np.random.default_rng(seed);st=model.initial_state(prefix,method)
    if method=='static':
        _,cov,_=fit_competence(prefix)
        w=rng.multivariate_normal(st['w'],cov,size=n_particles)
        h=np.broadcast_to(st['h'],(n_particles,model.hidden)).copy()
        return dict(w=w,h=h),dict(method=method,w0=st['w0'].tolist(),endpoint=st['w'].tolist(),hidden_endpoint=st['h'].tolist(),endpoint_covariance=cov.tolist(),hidden_uncertainty='fixedprefixmemory for staticcompetencechallenge')
    w0=st['w0'];p,_,end=model.sequence(prefix,w0);_,c,_,_=subject_arrays(prefix);ok=c!=0;eps=1e-3
    ds=[];jw=[];jh=[]
    for j in range(3):
        v=np.eye(3)[j]*eps
        a,_,ae=model.sequence(prefix,w0+v);b,_,be=model.sequence(prefix,w0-v)
        ds.append((logit(np.clip(a,1e-7,1-1e-7))-logit(np.clip(b,1e-7,1-1e-7)))/(2*eps))
        jw.append((ae['w']-be['w'])/(2*eps));jh.append((ae['h']-be['h'])/(2*eps))
    D=np.stack(ds,axis=1);Jw=np.stack(jw,axis=1);Jh=np.stack(jh,axis=1)
    fisher=np.einsum('ni,n,nj->ij',D[ok],p[ok]*(1-p[ok]),D[ok])+.5*np.eye(3)
    cov0=np.linalg.inv(fisher);ev,U=np.linalg.eigh((cov0+cov0.T)/2);cov0=(U*np.clip(ev,1e-7,4.))@U.T
    wcov=Jw@cov0@Jw.T;maxev=float(np.max(np.linalg.eigvalsh((wcov+wcov.T)/2)))
    factor=min(1.,np.sqrt(4./maxev)) if maxev>0 else 1.
    delta=rng.multivariate_normal(np.zeros(3),cov0,size=n_particles)*factor
    w=end['w']+delta@Jw.T;rawh=end['h']+delta@Jh.T;h=np.clip(rawh,-1,1)
    info=dict(method=method,w0=w0.tolist(),endpoint=end['w'].tolist(),hidden_endpoint=end['h'].tolist(),initial_covariance=cov0.tolist(),endpoint_covariance=(wcov*factor**2).tolist(),joint_rank_at_most=3,endpoint_sd_cap_factor=factor,hidden_clipped_fraction=float(np.mean(rawh!=h)),hidden_uncertainty='sameW0perturbation jointlinearpropagation;nofittedhiddenparameters')
    return dict(w=w,h=h),info


def autonomous(model,prefix,future_session_start,bank,n_particles=512,seed=0,
               protocol='standard',subject=None,neighbors=15,calibration_method='map',
               omission_mode='growth',trainer_options=None,bin_size=500,
               replay_signed_contrast=None,reset_weights=False,weight_retention=1.,
               hidden_retention=1.):
    starts=np.asarray(future_session_start,bool);H=len(starts);rng=np.random.default_rng(seed+101)
    common=draw_initial(prefix,bank,n_particles,seed+211,exclude=subject,neighbors=neighbors,competence='growth')
    state,calibration=calibration_particles(model,prefix,n_particles,seed+313,calibration_method)
    initial_w=state['w'].copy();initial_h=state['h'].copy()
    trainer=VectorTrainer.from_prefix(prefix,n_particles,seed+419,protocol,**(trainer_options or {}));initial_trainer=trainer.state_summary()
    xs=np.empty((n_particles,H));cs=np.empty((n_particles,H),np.int8);ww=np.empty((n_particles,H//bin_size,3));pools=[]
    for t in range(H):
        if starts[t]:
            trainer.new_session()
            if reset_weights:state['w']=initial_w.copy();state['h']=initial_h.copy()
            else:state['w']=state['w']*weight_retention;state['h']=state['h']*hidden_retention
        task=trainer.sample();x=task['signed_contrast']
        if replay_signed_contrast is not None:
            xx=float(replay_signed_contrast[t]);x=np.full(n_particles,xx)
            side=task['side'].copy() if xx==0 else np.full(n_particles,-1 if np.signbit(xx) else 1)
            trainer.current['side']=side;trainer.current['contrast']=np.abs(x);trainer.current['correct_choice']=-side
        pr=model.probs(state,x);omit=omission_at(common,t,omission_mode)
        choice=np.where(rng.random(n_particles)<pr,-1,1).astype(np.int8);choice[rng.random(n_particles)<omit]=0
        feedback=trainer.observe(choice)
        model.update(state,x,choice,feedback['feedbackType'],session_start=bool(starts[t]))
        if not np.isfinite(state['w']).all() or not np.isfinite(state['h']).all():raise FloatingPointError('Nonfinite RNN autonomous state')
        xs[:,t]=x;cs[:,t]=choice
        if (t+1)%bin_size==0:ww[:,t//bin_size]=state['w'];pools.append(trainer.pool.mean(axis=0))
    curves,counts=trajectory_summary(xs,cs,bin_size)
    return dict(samples=curves,counts=counts,weights=ww,hidden_final=state['h'],pool_fraction=np.array(pools),calibration=calibration,initial_trainer=initial_trainer,
      mode='actual_schedule_replay_diagnostic' if replay_signed_contrast is not None else 'autonomous',seed=seed,n_particles=n_particles,protocol=protocol,challenge_stage='post_source_validation_RNN')


def conditional(model,prefix,future,bank,n_particles=512,seed=0,subject=None,bin_size=500,
                calibration_method='map',omission_mode='growth'):
    state=model.initial_state(prefix,calibration_method);p,w,end=model.sequence(future,state);s,c,_,_=subject_arrays(future)
    common=draw_initial(prefix,bank,n_particles,seed+211,exclude=subject);rng=np.random.default_rng(seed+101);H=len(c)
    cc=np.empty((n_particles,H),np.int8);omitp=np.empty(H)
    for t in range(H):
        omit=omission_at(common,t,omission_mode);omitp[t]=omit.mean()
        choice=np.where(rng.random(n_particles)<p[t],-1,1).astype(np.int8);choice[rng.random(n_particles)<omit]=0;cc[:,t]=choice
    q=np.clip(p,1e-8,1-1e-8);ok=c!=0;y=(c<0).astype(float)
    catp=np.where(c==0,omitp,(1-omitp)*np.where(c<0,p,1-p));curves,counts=trajectory_summary(np.broadcast_to(s,cc.shape),cc,bin_size)
    return dict(samples=curves,counts=counts,prob_right=p,weights=w,hidden_final=end['h'],binary_nll=float(np.mean((-y*np.log(q)-(1-y)*np.log1p(-q))[ok])),categorical_nll=float(-np.log(np.clip(catp,1e-9,1)).mean()),n_response=int(ok.sum()),mode='teacher_forced_diagnostic')


def forecast_subject(subject,split,tag,model_path=DEFAULT_MODEL,n_particles=512,horizon=5000,
                     freeze=None,gate=None,calibration_path=None,overwrite=False):
    """Save autonomous outcomes before the scoring read, preserving the guard."""
    folder=CAMP/'artifacts/forecasts'/tag;folder.mkdir(parents=True,exist_ok=True);name='rnnglm32';base=seed_for(subject)
    prefix,starts,meta=get_prefix(subject,split,horizon,freeze,gate)
    if prefix is None or starts is None or len(starts)<500:
        (folder/(subject+'_ineligible.json')).write_text(json.dumps(dict(subject=subject,split=split,metadata=meta,reason='fewerthan1000prefix+500futureopportunities'))+'\n');return []
    H=len(starts);bank=load_bank(BANK);model=load_rnn(model_path);path=folder/(subject+'__'+name+'.npz')
    if not path.exists() or overwrite:
        t0=time.monotonic();result=autonomous(model,prefix,starts,bank,n_particles,base,'external' if split=='external' else 'standard',subject)
        primary=result['samples']
        if calibration_path:
            from uncertainty import apply_calibration
            primary=apply_calibration(primary,name,base+647,config_path=calibration_path)
        np.savez_compressed(path,samples=result['samples'],weights=result['weights'],counts=result['counts'],samples_primary=primary,hidden_final=result['hidden_final'],pool_fraction=result['pool_fraction'],seed=np.array(base),session_start=starts)
        path.with_suffix('.json').write_text(json.dumps(dict(subject=subject,split=split,model=name,mode=result['mode'],challenge_stage='post_source_validation_RNN',prefix_n=1000,horizon=H,n_particles=n_particles,conditional_on='realized session opportunities only',calibration=result['calibration'],trainer=result['initial_trainer'],metadata=meta,seconds=time.monotonic()-t0,model_sha256=hashlib.sha256(Path(model_path).read_bytes()).hexdigest()),indent=2)+'\n')
        exposure(dict(event='autonomous_forecast_saved',subject=subject,split=split,model=name,challenge_stage='post_source_validation_RNN',path=str(path.relative_to(CAMP)),future_outcomes_assimilated=False))
    # This first read of future outcomes occurs only after forecast bytes exist.
    future=load_subject(subject,split,purpose='score already-saved postvalidation RNN forecast; conditional diagnostic',freeze_path=freeze,external_gate_path=gate)
    future=subset(future,1000,1000+H);s,c,_,_=subject_arrays(future);observed,counts=trajectory_summary(s,c)
    np.savez_compressed(folder/(subject+'__observed.npz'),observed=observed[0],counts=counts[0]);records=[];z=np.load(path)
    con=conditional(model,prefix,future,bank,n_particles,base,subject)
    np.savez_compressed(folder/(subject+'__'+name+'__conditional.npz'),samples=con['samples'],prob_right=con['prob_right'],weights=con['weights'],hidden_final=con['hidden_final'])
    for hh in [1000,3000,5000]:
        B=min(hh//500,H//500)
        if not B:continue
        records.append(dict(subject=subject,split=split,model=name,arm='autonomous',horizon=hh,actual_horizon=B*500,full_horizon=H>=hh,**score(z['samples_primary'][:,:B],observed[0,:B])))
        if calibration_path:records.append(dict(subject=subject,split=split,model=name,arm='raw_autonomous',horizon=hh,actual_horizon=B*500,full_horizon=H>=hh,**score(z['samples'][:,:B],observed[0,:B])))
        cc=future['choice'][:B*500];qq=np.clip(con['prob_right'][:B*500],1e-8,1-1e-8);ok=cc!=0
        nll=float(-np.mean(np.where(cc[ok]<0,np.log(qq[ok]),np.log1p(-qq[ok]))))
        records.append(dict(subject=subject,split=split,model=name,arm='conditional_diagnostic',horizon=hh,actual_horizon=B*500,full_horizon=H>=hh,binary_nll=nll,**score(con['samples'][:,:B],observed[0,:B])))
    (folder/(subject+'__scores.json')).write_text(json.dumps(records,indent=2)+'\n');return records


def check_freeze(path,_seen=None):
    _seen=set() if _seen is None else _seen
    identity=str(Path(path).resolve())
    if identity in _seen:return
    _seen.add(identity)
    freeze=json.loads(Path(path).read_text())
    for entry in freeze['files']:
        p=CAMP/entry['path']
        if hashlib.sha256(p.read_bytes()).hexdigest()!=entry['sha256']:raise RuntimeError('Frozen challenge artifact changed: '+str(p))
        if entry['path']=='protocols/FREEZE.json':check_freeze(p,_seen)


def audit_calibration(model_path=DEFAULT_MODEL):
    """Development-only linearization check against exact prefix replays."""
    model=load_rnn(model_path);allocation=json.loads((CAMP/'artifacts/models/DEVELOPMENT_MODEL_SPLIT.json').read_text());ids=sorted(allocation['validation'],key=lambda x:hashlib.sha256(x.encode()).hexdigest())
    records=[]
    for subject in ids:
        prefix,starts,_=get_prefix(subject,'dev',500)
        if prefix is None or starts is None or len(starts)<500:continue
        seed=seed_for(subject)+313;n=64
        linear,info=calibration_particles(model,prefix,n,seed)
        rng=np.random.default_rng(seed);delta=rng.multivariate_normal(np.zeros(3),np.asarray(info['initial_covariance']),size=n)*info['endpoint_sd_cap_factor']
        w=[];h=[]
        for v in delta:
            _,_,end=model.sequence(prefix,np.asarray(info['w0'])+v);w.append(end['w']);h.append(end['h'])
        exact=dict(w=np.asarray(w),h=np.asarray(h));errors=[]
        for contrast in [-1.,-.25,.25,1.]:errors.append(np.abs(model.probs(linear,np.full(n,contrast))-model.probs(exact,np.full(n,contrast))))
        errors=np.asarray(errors)
        records.append(dict(subject=subject,particles=n,seed=seed,mean_abs_probability_error=float(np.mean(errors)),max_abs_probability_error=float(np.max(errors)),p95_abs_probability_error=float(np.quantile(errors,.95)),
          mean_abs_hidden_error=float(np.mean(np.abs(linear['h']-exact['h']))),mean_abs_weight_error=float(np.mean(np.abs(linear['w']-exact['w']))),hidden_clipped_fraction=info['hidden_clipped_fraction'],endpoint_covariance_cap_factor=info['endpoint_sd_cap_factor']))
        if len(records)==3:break
    out=dict(model_sha256=hashlib.sha256(Path(model_path).read_bytes()).hexdigest(),scope='development only; first3prefix+500future animals bySHA256ID; no source/external',method='sameW0Fisherdraws;rank3linearendpoint vs exactprefixrecurrence; four fixedprobecontrasts',records=records)
    (CAMP/'artifacts/rnn/PREFIX_LINEARIZATION_AUDIT.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out),flush=True)


def main():
    p=argparse.ArgumentParser();p.add_argument('--split',default='devcv',choices=['devcv','animal_holdout','lab_holdout','external']);p.add_argument('--model',default=str(DEFAULT_MODEL));p.add_argument('--tag',default='rnn_dev');p.add_argument('--particles',type=int,default=512);p.add_argument('--horizon',type=int,default=5000);p.add_argument('--subject');p.add_argument('--freeze');p.add_argument('--gate');p.add_argument('--calibration');p.add_argument('--overwrite',action='store_true');p.add_argument('--collect-only',action='store_true');p.add_argument('--audit-calibration',action='store_true');a=p.parse_args()
    if a.audit_calibration:audit_calibration(a.model);return
    if a.split!='devcv':
        if not a.freeze:raise PermissionError('RNN protected outcomes require separate postvalidation challenge freeze')
        check_freeze(a.freeze)
        if a.split=='external' and not a.gate:raise PermissionError('External cohort remains sealed without source gate')
    if a.collect_only:collect(a.tag);return
    allocation=json.loads((CAMP/'artifacts/models/DEVELOPMENT_MODEL_SPLIT.json').read_text());ids=allocation['validation'] if a.split=='devcv' else subjects(a.split)
    if a.subject:ids=[a.subject]
    for subject in ids:
        t0=time.monotonic();rr=forecast_subject(subject,'dev' if a.split=='devcv' else a.split,a.tag,a.model,a.particles,a.horizon,a.freeze,a.gate,a.calibration,a.overwrite)
        print(json.dumps(dict(subject=subject,records=len(rr),seconds=time.monotonic()-t0)),flush=True)
    _,summary=collect(a.tag);print(json.dumps([r for r in summary if r['horizon']==3000 and r['full_only']],indent=2),flush=True)

if __name__=='__main__':main()
