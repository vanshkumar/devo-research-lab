"""Consumed-source matched-history diagnostic. No new learner fit or rollout."""
from pathlib import Path
import os, sys, socket, json, hashlib, datetime as dt, time
OUT=Path(__file__).resolve().parent
ROOT=OUT.parents[1]
C=ROOT/'campaigns/population_learning_transport_2026-10-28'
OLD=ROOT/'campaigns/learning_rule_transport_2026-10-28'
sys.dont_write_bytecode=True
os.environ['NUMBA_CACHE_DIR']=str(OUT/'numba_cache')
sys.path[:0]=[str(C/'code'),str(OLD/'code')]
import numpy as np
from scipy.special import expit
import mixed_reader as reader
import data_io
from rnn_learning import load_rnn
from baselines import load_bank,draw_initial,omission_at
from learning_models import subject_arrays,features

MODEL=OLD/'artifacts/rnn/rnnglm32_nested_best.npz'
BANK=OLD/'artifacts/baselines/nested_growth_bank.npz'
FOLDER=C/'artifacts/forecasts/source'
FREEZE=C/'protocols/FREEZE.json'
MANIFEST=C/'protocols/SOURCE_FORECASTS.json'
def digest(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def stamp():return dt.datetime.now(dt.timezone.utc).isoformat()
def dump(path,value):Path(path).write_text(json.dumps(value,indent=2)+'\n')
def denied(*a,**kw):raise PermissionError('Network/full-subject/new-RNN-fit access forbidden in matched diagnostic')
socket.create_connection=denied;socket.socket.connect=denied
reader.urlopen=denied;reader.acquire=denied;reader.coverage=denied
data_io.load_subject=denied;data_io.prepare_subject=denied
def log(event):
    with (OUT/'EXPOSURE.jsonl').open('a') as f:
        f.write(json.dumps(dict(utc=stamp(),analysis='postvalidation_consumed_source_only',**event),sort_keys=True)+'\n')
reader.log=log;data_io.exposure=log

def verify_frozen():
    items=json.loads(FREEZE.read_text())['files'];answer={}
    for item in items:
        path=ROOT/item['path'];h=digest(path)
        if h!=item['sha256']:raise RuntimeError('Frozen source changed: '+str(path))
        answer[str(path.relative_to(ROOT))]=h
    return answer

def expected_sides(s,prob_right,omit):
    ans=np.empty((6,2))
    for b in range(6):
        lo=b*500;hi=lo+500
        for j,side in enumerate((-1,1)):
            take=np.isclose(s[lo:hi],side,rtol=0,atol=1e-9)
            pc=prob_right[lo:hi] if side==1 else 1-prob_right[lo:hi]
            ans[b,j]=np.mean(((1-omit[lo:hi])*pc)[take])
    return ans

def observed(s,c):
    out=np.empty((6,4));counts=np.empty((6,4),int)
    for b in range(6):
        ss=s[b*500:(b+1)*500];cc=c[b*500:(b+1)*500]
        for j,side in enumerate((-1,1)):
            take=np.isclose(ss,side,rtol=0,atol=1e-9)
            counts[b,j]=take.sum();out[b,j]=np.mean(cc[take]==-side)
        out[b,2]=np.mean(cc<0);out[b,3]=np.mean(cc==0);counts[b,2:]=500
    return out,counts

def independent_prefix_check(state,s,c,r,day,params,expected,n=32):
    """Direct one-step GRU algebra, separate from the compiled sequence API."""
    w=np.array(state['w']);h=np.array(state['h']);got=[]
    for t in range(n):
        z=np.tanh(5*s[t])/np.tanh(5.)
        x=np.array([max(z,0),min(z,0),1.])
        got.append(float(expit(np.clip(float(w@x),-50,50))))
        if c[t]==0:continue
        inp=np.r_[w,z,1.,float(day[t]),float(c[t]<0),float(r[t]>0),float(z>0)]
        a=params['Wih']@inp+params['bih'];b=params['Whh']@h+params['bhh']
        ar,au,an=np.split(a,3);br,bu,bn=np.split(b,3)
        reset=expit(ar+br);keep=expit(au+bu)
        h=keep*h+(1-keep)*np.tanh(an+reset*bn)
        v=np.maximum(params['A']@h+params['a'],0)
        v=np.maximum(params['B']@v+params['b'],0)
        w=w+params['scale']*(params['C']@v+params['cc'])
    err=float(np.max(np.abs(np.asarray(got)-expected[:n])))
    if err>1e-11:raise AssertionError('Independent pre-update probability mismatch')
    return dict(trials=n,max_probability_difference=err,prediction_before_current_outcome=True)

def mean_nll(prob,c):
    take=c!=0;q=np.clip(prob[take],1e-12,1-1e-12);y=c[take]<0
    loss=-np.where(y,np.log(q),np.log1p(-q))
    return dict(n_responding=int(take.sum()),mean=float(loss.mean()),sum=float(loss.sum()))

def main():
    start=time.monotonic()
    if not (OUT/'PREDECLARATION.md').is_file():raise RuntimeError('Missing predeclaration')
    frozen_before=verify_frozen()
    original=json.loads((C/'artifacts/results/SOURCE_RESULT.json').read_text())
    subjects=original['subjects'];labs=original['labs']
    if len(subjects)!=24 or any(s in subjects for s in ('NYU-21','SWC_007')):raise AssertionError('Wrong cohort')
    original_read=reader._read
    def capped_read(subject,stop):
        if subject not in subjects or int(stop)!=4000:raise PermissionError('Only primary24 first4000 permitted')
        return original_read(subject,4000)
    reader._read=capped_read
    model=load_rnn(MODEL);model.initial_state=denied;bank=load_bank(BANK)
    yy=[];cc=[];aa=[];gg=[];pp=[];rows=[];pins={}
    for subject,lab in zip(subjects,labs):
        t0=time.monotonic();seed=int(hashlib.sha256(subject.encode()).hexdigest()[:8],16)%(2**31-1)
        meta_path=FOLDER/(subject+'__rnn.json');meta=json.loads(meta_path.read_text())
        if meta['model_sha256']!=digest(MODEL) or meta['particles']!=512 or meta['horizon']!=3000:
            raise AssertionError('Frozen RNN metadata mismatch')
        prefix_path=FOLDER/(subject+'__prefix.npz')
        if digest(prefix_path)!=meta['prefix_sha256']:raise AssertionError('Prefix hash mismatch')
        with np.load(prefix_path,allow_pickle=False) as z:
            prefix={k:z[k] for k in z.files if k!='future_session_start'};starts=z['future_session_start']
        full=reader.load_scored(subject,stop=4000,freeze_path=FREEZE,forecast_manifest=MANIFEST,
            purpose='Postvalidation matched actual-history diagnostic; already consumed first4000 only')
        if len(full['choice'])!=4000:raise AssertionError('Wrong raw length')
        checked=[]
        for k,v in prefix.items():
            if isinstance(v,np.ndarray) and v.ndim and len(v)==1000:
                if not np.array_equal(v,full[k][:1000],equal_nan=True):raise AssertionError('Saved/raw prefix mismatch '+k)
                checked.append(k)
        future={k:v[1000:4000] for k,v in full.items() if isinstance(v,np.ndarray) and v.ndim and len(v)==4000}
        if not np.array_equal(starts,future['session_start']):raise AssertionError('Session boundary mismatch')
        s,c,r,day=subject_arrays(future);y,counts=observed(s,c)
        observed_path=FOLDER/(subject+'__observed.npz')
        with np.load(observed_path,allow_pickle=False) as z:
            if not np.array_equal(y,z['observed']) or not np.array_equal(counts,z['counts']):
                raise AssertionError('Original target/count mismatch')
        state=dict(w=np.asarray(meta['calibration']['endpoint']),h=np.asarray(meta['calibration']['hidden_endpoint']))
        probability,weights,end=model.sequence(future,state)
        check=independent_prefix_check(state,s,c,r,day,model.params,probability)
        # Replay the existing fixed prefix-only omission initialization; no RNN fit.
        common=draw_initial(prefix,bank,512,seed+211,exclude=subject,competence='growth')
        omit_by_bin=np.array([omission_at(common,b*500).mean() for b in range(6)])
        omit=np.repeat(omit_by_bin,500)
        conditional=expected_sides(s,probability,omit)
        saved={}
        for kind in ('rnn','growth','persistence'):
            path=FOLDER/(subject+'__'+kind+'.npz')
            with np.load(path,allow_pickle=False) as z:
                saved[kind]=z['samples'].mean(0)[:,:2]
                if kind=='persistence':
                    w=z['weights'];fixed_w=w[:,0,:]
                    if not np.array_equal(w,np.broadcast_to(fixed_w[:,None,:],w.shape)):
                        raise AssertionError('Persistence weights changed')
            pins[str(path.relative_to(ROOT))]=digest(path)
        static_probability=expit(np.einsum('pi,ti->pt',fixed_w,features(s))).mean(0)
        rnn_nll=mean_nll(probability,c);static_nll=mean_nll(static_probability,c)
        row=dict(subject=subject,lab=lab,seed=seed,raw_rows=4000,scored_rows=3000,
            saved_prefix_fields_exact=checked,targets_and_counts_exact=True,session_boundaries_exact=True,
            independent_recurrence=check,conditional_rnn_nll=rnn_nll,frozen_prefix_static_nll=static_nll,
            omission_mean_by_bin=omit_by_bin.tolist(),seconds=time.monotonic()-t0)
        rows.append(row);yy.append(y[:,:2]);cc.append(conditional);aa.append(saved['rnn']);gg.append(saved['growth']);pp.append(saved['persistence'])
        np.savez_compressed(OUT/(subject+'__conditional.npz'),prob_right=probability,p_omit=omit,
            static_prob_right=static_probability,conditional_sides=conditional,observed=y,counts=counts,
            initial_w=state['w'],initial_h=state['h'],final_w=end['w'],final_h=end['h'])
        for path in (prefix_path,meta_path,observed_path):pins[str(path.relative_to(ROOT))]=digest(path)
        print(json.dumps(dict(subject=subject,conditional_rnn_binary_nll=rnn_nll['mean'],seconds=row['seconds'])),flush=True)
    y=np.array(yy);predictions={'conditional_rnn':np.array(cc),'autonomous_rnn':np.array(aa),
        'autonomous_growth':np.array(gg),'autonomous_persistence':np.array(pp)}
    target=y.mean(2);summaries={}
    for name,side in predictions.items():
        curve=side.mean(2);res=target-curve
        summaries[name]=dict(population_curve_mae=float(np.abs(res.mean(0)).mean()),
            individual_curve_mae=float(np.abs(res).mean()),individual_side_curve_mae=float(np.abs(y-side).mean()),
            scalar_bias_observed_minus_prediction=float(res.mean()),forecast_curve=curve.mean(0).tolist(),
            individual_curve_mae_by_animal=np.abs(res).mean(1).tolist(),
            lab_curve_mae={lab:float(np.abs(res[np.array(labs)==lab].mean(0)).mean()) for lab in sorted(set(labs))})
    for name,old_name in [('autonomous_rnn','rnn'),('autonomous_growth','growth'),('autonomous_persistence','persistence')]:
        if abs(summaries[name]['population_curve_mae']-original['models'][old_name]['curve_mae'])>1e-12:
            raise AssertionError('Published primary comparison not reproduced')
    rng=np.random.default_rng(20261029);ix=rng.integers(0,24,(20000,24));comparisons={}
    con=predictions['conditional_rnn'].mean(2)
    for name in ('autonomous_rnn','autonomous_growth','autonomous_persistence'):
        base=predictions[name].mean(2)
        pop=np.abs((target-base)[ix].mean(1)).mean(1)-np.abs((target-con)[ix].mean(1)).mean(1)
        indiv=(np.abs(target-base).mean(1)-np.abs(target-con).mean(1))[ix].mean(1)
        comparisons[name]=dict(positive_means_conditional_better=True,
            population_curve_mae_gain=summaries[name]['population_curve_mae']-summaries['conditional_rnn']['population_curve_mae'],
            population_curve_mae_gain_interval95=np.quantile(pop,[.025,.975]).tolist(),
            individual_curve_mae_gain=summaries[name]['individual_curve_mae']-summaries['conditional_rnn']['individual_curve_mae'],
            individual_curve_mae_gain_interval95=np.quantile(indiv,[.025,.975]).tolist())
    nll={}
    for key in ('conditional_rnn_nll','frozen_prefix_static_nll'):
        nll[key]=dict(equal_animal_mean=float(np.mean([r[key]['mean'] for r in rows])),
            pooled_trial_mean=float(sum(r[key]['sum'] for r in rows)/sum(r[key]['n_responding'] for r in rows)),
            responding_trials=sum(r[key]['n_responding'] for r in rows))
    dif=np.array([r['frozen_prefix_static_nll']['mean']-r['conditional_rnn_nll']['mean'] for r in rows])
    nll['conditional_gain_over_static']=dict(mean=float(dif.mean()),interval95=np.quantile(dif[ix].mean(1),[.025,.975]).tolist())
    if verify_frozen()!=frozen_before:raise RuntimeError('Source hashes changed')
    if any(digest(ROOT/p)!=h for p,h in pins.items()):raise RuntimeError('Reused artifact changed')
    result=dict(utc=stamp(),status='completed_postvalidation_exploratory',subjects=subjects,labs=labs,n=24,
        prefix_trials=1000,future_trials=3000,source_rows_returned=96000,external_access=False,new_learner_fit=False,
        original_omission_prefix_recipe_replayed=True,new_autonomous_rollouts=False,
        information_regime='actual future stimuli and prior choices/feedback/session starts; current response predicted before update',
        endpoint='equal-side exact100 accuracy, omissions as failures; six500-trial bins',
        conditional_curve_method='analytic expected probabilities; 512-particle mean prefix-derived omission probabilities',
        observed_curve=target.mean(0).tolist(),metrics=summaries,comparisons=comparisons,binary_choice_nll=nll,
        bootstrap='20000 paired animal resamples seed20261029; exploratory selected-mixture uncertainty, not lab-general inference',
        checks=dict(all_targets_and_counts_exact=True,all_prefix_values_exact=True,source_frozen_hashes_unchanged=True,
            original_primary_errors_reproduced=True,max_independent_probability_difference=max(r['independent_recurrence']['max_probability_difference'] for r in rows)),
        model_sha256=digest(MODEL),bank_sha256=digest(BANK),predeclaration_sha256=digest(OUT/'PREDECLARATION.md'),
        code_sha256=digest(__file__),records=rows,seconds=time.monotonic()-start)
    dump(OUT/'RESULT.json',result);dump(OUT/'SOURCE_PINS.json',dict(frozen=frozen_before,artifacts=pins))
    np.savez_compressed(OUT/'CURVES.npz',subjects=np.array(subjects),labs=np.array(labs),observed_sides=y,**predictions)
    print(json.dumps({k:result[k] for k in ('metrics','comparisons','binary_choice_nll','checks','seconds')},indent=2),flush=True)

if __name__=='__main__':main()
