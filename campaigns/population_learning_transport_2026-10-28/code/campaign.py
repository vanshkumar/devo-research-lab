"""Frozen-rule population forecasts; no future observations in simulation API.

The original recurrent learner, calibration and development donor bank are
imported read-only. This campaign changes the estimand to exact +/-100% observed
accuracy and freezes it prospectively; it does not refit a learning law.
"""
from pathlib import Path
import os, sys, json, hashlib, datetime as dt
import numpy as np
from scipy.special import expit

C = Path(__file__).resolve().parents[1]
ROOT = C.parents[1]
OLD = ROOT / 'campaigns/learning_rule_transport_2026-10-28'
sys.dont_write_bytecode = True
os.environ.setdefault('NUMBA_CACHE_DIR', str(C / 'artifacts/numba_cache'))
sys.path.insert(0, str(OLD / 'code'))
from rnn_learning import load_rnn
from rnn_rollout import calibration_particles
from baselines import load_bank, draw_initial, competence_at, omission_at, fit_competence
from learning_models import features, subject_arrays
from trainer import VectorTrainer
from evaluation import marginal_crps

MODEL = OLD / 'artifacts/rnn/rnnglm32_nested_best.npz'
BANK = OLD / 'artifacts/baselines/nested_growth_bank.npz'
MODELS = ('rnn', 'growth', 'persistence')

def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def stamp():
    return dt.datetime.now(dt.timezone.utc).isoformat()

def event(kind, **kw):
    with (C / 'protocols/EXPOSURE.jsonl').open('a') as f:
        f.write(json.dumps({'utc':stamp(), 'event':kind, **kw}, sort_keys=True)+'\n')

def seed_for(subject):
    return int(hashlib.sha256(subject.encode()).hexdigest()[:8], 16) % (2**31-1)

def summarize(x, choice, bin_size=500):
    """Side-specific exact-100% shares; every omission is an incorrect trial.

    Remaining metrics: right-choice share/all opportunities, omission share.
    Counts are retained. Empty side cells are NaN and must use a common mask.
    """
    x=np.asarray(x); choice=np.asarray(choice)
    if x.ndim==1: x=x[None,:]; choice=choice[None,:]
    n,h=x.shape; nb=h//bin_size
    y=np.full((n,nb,4),np.nan); counts=np.zeros((n,nb,4),int)
    for b in range(nb):
        xx=x[:,b*bin_size:(b+1)*bin_size]; cc=choice[:,b*bin_size:(b+1)*bin_size]
        for j,side in enumerate((-1,1)):
            mask=np.isclose(xx,side,atol=1e-9,rtol=0)
            den=mask.sum(1); num=(mask & (cc==-side)).sum(1)
            y[:,b,j]=np.divide(num,den,out=np.full(n,np.nan),where=den>0)
            counts[:,b,j]=den
        y[:,b,2]=(cc<0).mean(1); y[:,b,3]=(cc==0).mean(1)
        counts[:,b,2:]=bin_size
    return y, counts

def make_initial(prefix, subject, n, seed, model, bank, method='map'):
    common=draw_initial(prefix,bank,n,seed+211,exclude=subject,competence='growth')
    state,cal=calibration_particles(model,prefix,n,seed+313,method)
    w,cov,_=fit_competence(prefix,ridge=.5)
    persistence=np.random.default_rng(seed+313).multivariate_normal(w,cov,size=n)
    return common,state,persistence,cal

def simulate(model,prefix,starts,common,initial,persistence,kind,policy,seed,
             trainer_options=None,omission_mode='growth',retention=1.,hidden_retention=1.):
    """Own stimuli/actions/rewards/updates; starts is the only future input.

    Unknown legacy reward volume stays unknown in input. The frozen trainer
    reconstructs its water bookkeeping with zero observed water for unavailable
    entries; this is an explicitly unmeasured metadata nuisance. Water/gain do
    not enter the frozen actor, stimulus sampling or binary feedback. The audit
    tests that changing those metadata cannot alter any generated choice.
    """
    n=len(common['w']); h=len(starts); nb=h//500
    state={k:v.copy() for k,v in initial.items()}
    if kind=='persistence': state['w']=persistence.copy()
    rng=np.random.default_rng(seed+101)
    trainer=VectorTrainer.from_prefix(prefix,n,seed+419,policy,**(trainer_options or {}))
    first_trainer=trainer.state_summary()
    xs=np.empty((n,h)); choices=np.empty((n,h),np.int8)
    weights=np.empty((n,nb,3)); probes=np.zeros((n,nb)); pool=[]
    for t in range(h):
        if starts[t]:
            trainer.new_session()
            state['w']*=retention; state['h']*=hidden_retention
        task=trainer.sample(); x=task['signed_contrast']
        if kind=='growth': state['w']=competence_at(common,t)
        omit=omission_at(common,t,omission_mode)
        w=state['w']
        probes[:,t//500]+=(1-omit)*((1-expit(-w[:,1]+w[:,2]))+expit(w[:,0]+w[:,2]))/1000
        pr=expit(np.sum(w*features(x),axis=-1))
        choice=np.where(rng.random(n)<pr,-1,1).astype(np.int8)
        choice[rng.random(n)<omit]=0
        feedback=trainer.observe(choice)
        if kind=='rnn': model.update(state,x,choice,feedback['feedbackType'],session_start=bool(starts[t]))
        if not all(np.isfinite(state[k]).all() for k in ('w','h')):
            raise FloatingPointError('Nonfinite recurrent state: no forecast abstention permitted')
        xs[:,t]=x; choices[:,t]=choice
        if (t+1)%500==0:
            weights[:,t//500]=state['w']; pool.append(trainer.pool.mean(0))
    samples,counts=summarize(xs,choices)
    if not np.isfinite(samples).all():
        raise FloatingPointError('Generated empty endpoint cell; increase particles/trials by frozen rule only')
    return dict(samples=samples,counts=counts,probe100=probes,weights=weights,
                hidden_final=state['h'],pool_fraction=np.asarray(pool),initial_trainer=first_trainer)

def verify_freeze(path):
    obj=json.loads(Path(path).read_text())
    for r in obj['files']:
        p=ROOT/r['path']
        if digest(p)!=r['sha256']: raise RuntimeError('Frozen file changed: '+str(p))
    return obj

def forecast_all(cohort='source',n=512,freeze_path=None,policy='standard'):
    import time
    sys.path.insert(0,str(C/'code'))
    import mixed_reader as reader
    freeze_path=Path(freeze_path or C/'protocols/FREEZE.json')
    freeze=verify_freeze(freeze_path)
    ids=freeze['source_subjects'] if cohort=='source' else freeze['external_subjects']
    model=load_rnn(MODEL); bank=load_bank(BANK); records=[]; swapped=[]
    folder=C/'artifacts/forecasts'/cohort; folder.mkdir(parents=True,exist_ok=True)
    for subject in ids:
        t=time.monotonic(); seed=seed_for(subject)
        prefix,starts,meta=reader.load_prefix_and_opportunities(subject,prefix_n=1000,horizon=3000,freeze_path=freeze_path)
        h=(len(starts)//500)*500; starts=starts[:h]
        if len(prefix['choice'])<1000 or h<500:
            records.append(dict(subject=subject,eligible=False,metadata=meta)); continue
        common,initial,persistence,cal=make_initial(prefix,subject,n,seed,model,bank)
        prefix_path=folder/(subject+'__prefix.npz')
        np.savez_compressed(prefix_path,**{k:v for k,v in prefix.items() if isinstance(v,np.ndarray)},future_session_start=starts)
        for kind in MODELS:
            out=simulate(model,prefix,starts,common,initial,persistence,kind,policy,seed)
            p=folder/(subject+'__'+kind+'.npz')
            np.savez_compressed(p,**{k:v for k,v in out.items() if isinstance(v,np.ndarray)},session_start=starts,seed=np.array(seed))
            m=dict(subject=subject,model=kind,cohort=cohort,policy=policy,particles=n,horizon=h,
                   calibration=cal if kind=='rnn' else dict(method='last500_static' if kind=='growth' else 'all1000_static'),
                   metadata=meta,initial_trainer=out['initial_trainer'],prefix_sha256=digest(prefix_path),
                   model_sha256=digest(MODEL),bank_sha256=digest(BANK),freeze_sha256=digest(freeze_path))
            jp=p.with_suffix('.json'); jp.write_text(json.dumps(m,indent=2)+'\n')
            records.append(dict(subject=subject,model=kind,eligible=True,horizon=h,path=str(p.relative_to(ROOT)),
                                sha256=digest(p),metadata_path=str(jp.relative_to(ROOT)),metadata_sha256=digest(jp)))
            event('forecast_saved',subject=subject,cohort=cohort,model=kind,path=str(p.relative_to(C)),sha256=digest(p),future_outcomes_read=False)
        if cohort=='source':
            # Predeclared source-state policy diagnostic; never scored against
            # standard animals as though they received this counterfactual.
            cf=C/'artifacts/forecasts/source_policy_swap';cf.mkdir(parents=True,exist_ok=True)
            for kind in MODELS:
                out=simulate(model,prefix,starts,common,initial,persistence,kind,'external',seed)
                p=cf/(subject+'__'+kind+'.npz')
                np.savez_compressed(p,**{k:v for k,v in out.items() if isinstance(v,np.ndarray)},session_start=starts,seed=np.array(seed))
                swapped.append(dict(subject=subject,model=kind,horizon=h,path=str(p.relative_to(ROOT)),sha256=digest(p)))
        print(json.dumps(dict(subject=subject,horizon=h,seconds=time.monotonic()-t)),flush=True)
    manifest=dict(utc=stamp(),cohort=cohort,freeze_sha256=digest(freeze_path),records=records,
                  all_forecasts_saved_before_scored_outcomes=True)
    mp=C/'protocols'/('SOURCE_FORECASTS.json' if cohort=='source' else 'EXTERNAL_FORECASTS.json')
    mp.write_text(json.dumps(manifest,indent=2)+'\n')
    event('all_cohort_forecasts_frozen',cohort=cohort,path=str(mp.relative_to(C)),sha256=digest(mp))
    if cohort=='source':
        cp=C/'protocols/SOURCE_POLICY_SWAP_FORECASTS.json'
        cp.write_text(json.dumps(dict(utc=stamp(),freeze_sha256=digest(freeze_path),records=swapped,
                                    scope='new source prefix states under counterfactual fixed policy; simulation diagnostic only'),indent=2)+'\n')
        event('source_state_policy_swap_forecasts_frozen',sha256=digest(cp),future_outcomes_read=False)
    return manifest

if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser();p.add_argument('--forecasts',action='store_true');p.add_argument('--particles',type=int,default=512)
    a=p.parse_args()
    if a.forecasts: forecast_all(n=a.particles)
