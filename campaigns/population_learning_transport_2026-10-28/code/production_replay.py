"""Independent production simulation replay from already-saved allowed prefixes.

Requires a complete cohort forecast manifest before reading even saved prefixes.
Reads no raw new animal or external files and no scored future outcomes. The
separate policy audit supplies an independently coded matrix-level recurrence;
this file reconstructs prefix Fisher propagation and production summaries.
"""
from pathlib import Path
import sys, os, json, hashlib, datetime, argparse
import numpy as np
from scipy.special import expit, logit

C=Path(__file__).resolve().parents[1]
ROOT=C.parents[1]
OUT=C/'artifacts/policy_audit/production_replay'
OUT.mkdir(parents=True,exist_ok=True)
os.environ['NUMBA_CACHE_DIR']=str(OUT/'numba_cache')
sys.path.insert(0,str(C/'code'))
from policy_audit import update_independent, probability, digest, load_rnn, load_bank, draw_initial, omission_at, competence_at, VectorTrainer, MODEL, BANK
from baselines import fit_competence
from learning_models import subject_arrays

def log(event):
    with (OUT/'EXPOSURE.jsonl').open('a') as f:
        f.write(json.dumps(dict(utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),**event))+'\n')

def prefix_uncertainty(model,prefix,meta,n,seed):
    w0=np.asarray(meta['calibration']['w0']);eps=1e-3
    initial=np.vstack([w0]+[w0+v for v in eps*np.eye(3)]+[w0-v for v in eps*np.eye(3)])
    w=initial.copy();h=np.zeros((7,model.hidden));s,c,r,d=subject_arrays(prefix)
    probability_path=np.empty((1000,7))
    for t in range(1000):
        x=np.full(7,s[t]);choice=np.full(7,c[t]);reward=np.full(7,r[t])
        probability_path[t]=probability(w,x)
        w,h=update_independent(w,h,x,choice,reward,d[t],model.params)
    D=(logit(np.clip(probability_path[:,1:4],1e-7,1-1e-7))-logit(np.clip(probability_path[:,4:7],1e-7,1-1e-7)))/(2*eps)
    Jw=((w[1:4]-w[4:7])/(2*eps)).T
    Jh=((h[1:4]-h[4:7])/(2*eps)).T
    responding=c!=0;p=probability_path[:,0]
    fisher=np.einsum('ni,n,nj->ij',D[responding],p[responding]*(1-p[responding]),D[responding])+.5*np.eye(3)
    cov=np.linalg.inv(fisher);values,vectors=np.linalg.eigh((cov+cov.T)/2)
    cov=(vectors*np.clip(values,1e-7,4.))@vectors.T
    wcov=Jw@cov@Jw.T;ev=float(np.max(np.linalg.eigvalsh((wcov+wcov.T)/2)))
    factor=min(1.,np.sqrt(4./ev)) if ev>0 else 1.
    # Verify the reconstruction, then pin the saved covariance for identical
    # finite Monte Carlo orientation if an SVD axis has arbitrary sign. This
    # avoids labelling equivalent random-number transforms simulation errors.
    saved_cov=np.asarray(meta['calibration']['initial_covariance'])
    saved_factor=float(meta['calibration']['endpoint_sd_cap_factor'])
    if np.max(np.abs(cov-saved_cov))>1e-8 or abs(factor-saved_factor)>1e-8:
        raise AssertionError('Independent prefix Fisher propagation disagrees')
    delta=np.random.default_rng(seed+313).multivariate_normal(np.zeros(3),saved_cov,size=n)*saved_factor
    state=dict(w=w[0]+delta@Jw.T,h=np.clip(h[0]+delta@Jh.T,-1,1))
    check=dict(weight_endpoint_error=float(np.max(np.abs(w[0]-meta['calibration']['endpoint']))),
               hidden_endpoint_error=float(np.max(np.abs(h[0]-meta['calibration']['hidden_endpoint']))),
               covariance_error=float(np.max(np.abs(cov-meta['calibration']['initial_covariance']))),
               factor_error=abs(factor-meta['calibration']['endpoint_sd_cap_factor']))
    return state,check

def own_summary(x,c):
    n,T=x.shape;B=T//500;y=np.empty((n,B,4));counts=np.zeros((n,B,4),int)
    for b in range(B):
        xx=x[:,b*500:(b+1)*500];cc=c[:,b*500:(b+1)*500]
        for j,sgn in enumerate([-1,1]):
            mask=np.isclose(xx,sgn,atol=1e-9,rtol=0)
            den=np.sum(mask,axis=1);num=np.sum(mask&(cc==-sgn),axis=1)
            y[:,b,j]=num/den;counts[:,b,j]=den
        y[:,b,2]=np.count_nonzero(cc<0,axis=1)/500
        y[:,b,3]=np.count_nonzero(cc==0,axis=1)/500
        counts[:,b,2:]=500
    return y,counts

def replay(model,prefix,starts,common,state,persistence,kind,policy,seed):
    n=len(state['w']);T=len(starts);B=T//500
    w=state['w'].copy();h=state['h'].copy()
    if kind=='persistence':w=persistence.copy()
    rng=np.random.default_rng(seed+101)
    trainer=VectorTrainer.from_prefix(prefix,n,seed+419,policy)
    fixed=np.random.default_rng(seed+419)
    X=np.empty((n,T));choices=np.empty((n,T),np.int8)
    weights=np.empty((n,B,3));probes=np.zeros((n,B));pool=[]
    for t in range(T):
        if starts[t]:trainer.new_session()
        if policy=='external':
            con=np.array([1.,.25,.125,.0625])[fixed.integers(0,4,n)]
            side=np.where(fixed.random(n)<.5,-1,1);x=side*con
        else:
            task=trainer.sample();x=task['signed_contrast'];side=task['side']
        if kind=='growth':w=competence_at(common,t)
        omit=omission_at(common,t)
        probes[:,t//500]+=(1-omit)*(.5*(expit(w[:,0]+w[:,2])+1-expit(-w[:,1]+w[:,2])))/500
        p=probability(w,x)
        choice=np.where(rng.random(n)<p,-1,1).astype(np.int8)
        choice[rng.random(n)<omit]=0
        reward=np.where(choice==-side,1,-1)
        if policy!='external':
            tr=trainer.observe(choice)
            assert np.array_equal(reward,tr['feedbackType'])
        if kind=='rnn':w,h=update_independent(w,h,x,choice,reward,float(starts[t]),model.params)
        X[:,t]=x;choices[:,t]=choice
        if (t+1)%500==0:
            weights[:,t//500]=w;pool.append(trainer.pool.mean(0))
    samples,counts=own_summary(X,choices)
    return dict(samples=samples,counts=counts,weights=weights,hidden_final=h,probe100=probes,pool_fraction=np.array(pool))

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--cohort',choices=['source','external'],default='source')
    parser.add_argument('--limit',type=int,default=6);args=parser.parse_args()
    mp=C/'protocols'/('SOURCE_FORECASTS.json' if args.cohort=='source' else 'EXTERNAL_FORECASTS.json')
    manifest=json.loads(mp.read_text())
    assert manifest['all_forecasts_saved_before_scored_outcomes']
    records=[r for r in manifest['records'] if r.get('eligible')]
    ids=sorted(set(r['subject'] for r in records),key=lambda s:hashlib.sha256(s.encode()).hexdigest())[:args.limit]
    model=load_rnn(MODEL);bank=load_bank(BANK);result=[]
    for subject in ids:
        sr=[r for r in records if r['subject']==subject]
        assert set(r['model'] for r in sr)=={'rnn','growth','persistence'}
        root=C/'artifacts/forecasts'/args.cohort
        metadata=json.loads((root/(subject+'__rnn.json')).read_text())
        pp=root/(subject+'__prefix.npz');assert digest(pp)==metadata['prefix_sha256']
        log(dict(event='replay_saved_permitted_prefix_only',cohort=args.cohort,subject=subject,path=str(pp),sha256=digest(pp),
                 manifest_sha256=digest(mp),raw_new_or_external_access=False,future_outcomes_accessed=False))
        with np.load(pp,allow_pickle=False) as z:
            prefix={k:z[k] for k in z.files if k!='future_session_start'};starts=z['future_session_start']
        n=int(metadata['particles'])
        with np.load(root/(subject+'__rnn.npz'),allow_pickle=False) as z:seed=int(z['seed'])
        state,initial_check=prefix_uncertainty(model,prefix,metadata,n,seed)
        common=draw_initial(prefix,bank,n,seed+211,exclude=subject,competence='growth')
        w,cov,_=fit_competence(prefix,ridge=.5)
        persistence=np.random.default_rng(seed+313).multivariate_normal(w,cov,size=n)
        row=dict(subject=subject,seed=seed,particles=n,initial_check=initial_check,models={})
        for record in sr:
            kind=record['model'];path=ROOT/record['path'];assert digest(path)==record['sha256']
            simulated=replay(model,prefix,starts,common,state,persistence,kind,metadata['policy'],seed)
            with np.load(path,allow_pickle=False) as old:
                errors={key:float(np.max(np.abs(old[key]-value))) for key,value in simulated.items()}
            if errors['samples']>1e-11 or errors['counts']>0 or max(errors.values())>1e-8:
                raise AssertionError((subject,kind,errors))
            row['models'][kind]=dict(forecast_sha256=digest(path),errors=errors)
            np.savez_compressed(OUT/(args.cohort+'__'+subject+'__'+kind+'.npz'),**simulated)
        result.append(row);print(json.dumps(row),flush=True)
    report=dict(cohort=args.cohort,scope='Independent recurrence, prefix Fisher propagation, fixed sampler and production summaries; no scored outcomes',
                manifest_sha256=digest(mp),subjects=ids,records=result,passed=True,
                code_sha256=digest(__file__),independent_recurrence_sha256=digest(C/'code/policy_audit.py'))
    (OUT/(args.cohort.upper()+'_RESULT.json')).write_text(json.dumps(report,indent=2)+'\n')

if __name__=='__main__':main()
