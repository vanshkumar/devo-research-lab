"""One bounded frozen-model simulation diagnostic; writes only beside itself."""
from pathlib import Path
import os, sys, json, hashlib, time, socket
OUT=Path(__file__).resolve().parent
C=OUT.parents[1]/'campaigns/learning_rule_transport_2026-10-28'
sys.dont_write_bytecode=True
os.environ['NUMBA_CACHE_DIR']=str(OUT/'numba_cache')
sys.path.insert(0,str(C/'code'))
import numpy as np
from scipy.special import expit
import data_io
from rnn_learning import load_rnn
from rnn_rollout import calibration_particles
from baselines import load_bank, draw_initial, omission_at, competence_at
from trainer import VectorTrainer
from rollout import trajectory_summary
from run_forecasts import seed_for

N=64; H=3000; B=6
MODEL=C/'artifacts/rnn/rnnglm32_nested_best.npz'
BANK=C/'artifacts/baselines/nested_growth_bank.npz'
digest=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
def denied(*a,**k): raise PermissionError('Preflight forbids network and full outcome loading')
socket.create_connection=denied; socket.socket.connect=denied
data_io.load_subject=denied; data_io.prepare_subject=denied
def log(event):
    with (OUT/'EXPOSURE.jsonl').open('a') as f: f.write(json.dumps(event,sort_keys=True)+'\n')
data_io.exposure=log
old_check=data_io.check_access
def check(subject,split,*a,**k):
    if split not in ('animal_holdout','lab_holdout'): raise PermissionError('Source-only preflight')
    return old_check(subject,split,*a,**k)
data_io.check_access=check

class SavedCalibration:
    def __init__(self,model,cal): self.model=model; self.cal=cal; self.hidden=model.hidden
    def initial_state(self,prefix,method):
        return dict(w=np.array(self.cal['endpoint']),h=np.array(self.cal['hidden_endpoint']),w0=np.array(self.cal['w0']))
    def sequence(self,*a,**k): return self.model.sequence(*a,**k)

def summarize_exact(x,c):
    result=np.empty((N,B))
    for b in range(B):
        xx=x[:,b*500:(b+1)*500]; cc=c[:,b*500:(b+1)*500]; sides=[]
        for side in (-1,1):
            mask=np.isclose(xx,side); den=mask.sum(1)
            sides.append(np.divide((mask&(cc==-side)).sum(1),den,out=np.full(N,np.nan),where=den>0))
        result[:,b]=np.mean(sides,axis=0)
    return result

def simulate(model,prefix,starts,common,initial,kind,protocol,seed):
    rng=np.random.default_rng(seed+101)
    state={k:v.copy() for k,v in initial.items()}
    trainer=VectorTrainer.from_prefix(prefix,N,seed+419,protocol)
    xx=np.empty((N,H)); cc=np.empty((N,H),np.int8); probes=np.zeros((N,B))
    for t in range(H):
        if starts[t]: trainer.new_session()
        task=trainer.sample(); x=task['signed_contrast']
        if kind=='growth': state['w']=competence_at(common,t)
        omit=omission_at(common,t)
        # Identical ±100% probes, equal side weighting; no simulated exposure.
        w=state['w']
        probes[:,t//500]+=(1-omit)*((1-expit(-w[:,1]+w[:,2]))+expit(w[:,0]+w[:,2]))/1000
        p=model.probs(state,x)
        choice=np.where(rng.random(N)<p,-1,1).astype(np.int8)
        choice[rng.random(N)<omit]=0
        feedback=trainer.observe(choice)
        if kind=='rnn': model.update(state,x,choice,feedback['feedbackType'],session_start=bool(starts[t]))
        if not np.isfinite(state['w']).all(): raise FloatingPointError('Invalid rollout')
        xx[:,t]=x; cc[:,t]=choice
    official,_=trajectory_summary(xx,cc)
    return dict(exact100=summarize_exact(xx,cc),probe100=probes,official_high=official[:,:,:2].mean(2))

def main():
    start=time.monotonic(); model=load_rnn(MODEL); bank=load_bank(BANK)
    jobs=[]
    for tag in ('rnn_source_animals','rnn_source_labs'):
        for path in (C/'artifacts/forecasts'/tag).glob('*__rnnglm32.json'):
            m=json.loads(path.read_text())
            if m['horizon']>=H: jobs.append((m['subject'],path,m))
    jobs=sorted(jobs,key=lambda j:hashlib.sha256(j[0].encode()).hexdigest())[:4]
    if len(jobs)!=4: raise RuntimeError('Four saved eligible source forecasts required')
    all_results={}; records=[]
    for subject,path,m in jobs:
        now=time.monotonic()
        if m['model_sha256']!=digest(MODEL): raise RuntimeError('Wrong saved model calibration')
        prefix,starts,meta=data_io.load_prefix_and_opportunities(subject,m['split'],1000,H,
            freeze_path=C/'protocols/RNN_FREEZE.json',purpose='Exploratory paired policy simulation; consumed source prefix only')
        seed=seed_for(subject)
        common=draw_initial(prefix,bank,N,seed+211,exclude=subject,competence='growth')
        state,cal=calibration_particles(SavedCalibration(model,m['calibration']),prefix,N,seed+313)
        for kind in ('rnn','growth'):
            for protocol in ('standard','external'):
                ans=simulate(model,prefix,starts,common,state,kind,protocol,seed)
                for metric,value in ans.items(): all_results[f'{subject}__{kind}__{protocol}__{metric}']=value
        rec=dict(subject=subject,split=m['split'],seed=seed,seconds=time.monotonic()-now,
            source_metadata_sha256=digest(path),prefix_n=len(prefix['choice']),future_opportunities=len(starts),
            source_prefix_objects=[r['path'] for r in meta['prefix_outcome_source_records']],
            reused_saved_RNN_calibration=True,new_learner_fit=False,external_access=False)
        records.append(rec); print(json.dumps(rec),flush=True)
    subjects=[j[0] for j in jobs]
    def stack(kind,policy,metric): return np.array([all_results[f'{s}__{kind}__{policy}__{metric}'] for s in subjects])
    def stats(a):
        scalar=np.mean(a,axis=2); individual=scalar.mean(1)
        return dict(mean=float(scalar.mean()),mean_curve=a.mean((0,1)).tolist(),
            conditional_MC_SE=float(np.sqrt(np.var(scalar,axis=1,ddof=1).sum()/N)/len(subjects)),
            prefix_means=individual.tolist(),between_prefix_SD=float(individual.std(ddof=1)))
    result=dict(scope='Input/simulation only; four previously consumed source prefixes; no external access and no new learner fit',
        n_subjects=4,n_particles=N,horizon=H,records=records,model_sha256=digest(MODEL),bank_sha256=digest(BANK),
        full_source_outcomes_read=False,external_prefixes_read=False,external_outcomes_read=False,
        frozen_growth_prefix_nuisance_calibration_replayed=True,metrics={})
    for metric in ('exact100','probe100','official_high'):
        result['metrics'][metric]={}
        for kind in ('rnn','growth'):
            for policy in ('standard','external'):
                result['metrics'][metric][kind+'_'+policy]=stats(stack(kind,policy,metric))
            result['metrics'][metric][kind+'_policy_fixed_minus_adaptive']=stats(stack(kind,'external',metric)-stack(kind,'standard',metric))
        for policy in ('standard','external'):
            result['metrics'][metric]['rnn_minus_growth_'+policy]=stats(stack('rnn',policy,metric)-stack('growth',policy,metric))
    # This precision context was already generated from consumed source outcomes by root.
    precision=json.loads((OUT.parent/'population_precision_preflight_2026-10-28/RESULT.json').read_text())
    result['source_analog_precision_context']=precision['prospective_source_analog'][0]
    gap=result['metrics']['official_high']['rnn_minus_growth_external']['mean']
    threshold=precision['prospective_source_analog'][0]['approximate_effect_for80percent_two_sided_power']
    result['fixed_policy_official_gap_exceeds_optimistic_source_scalar_threshold']=bool(abs(gap)>threshold)
    result['seconds']=time.monotonic()-start
    np.savez_compressed(OUT/'PARTICLES.npz',**all_results)
    (OUT/'RESULT.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(dict(seconds=result['seconds'],fixed_official_gap=gap,threshold=threshold,metrics=result['metrics'])),flush=True)

if __name__=='__main__': main()
