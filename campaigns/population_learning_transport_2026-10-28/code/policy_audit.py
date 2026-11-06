"""Independent bounded policy audit, using already-consumed source prefixes.

No external dataset loader is imported. RNN recurrence, fixed trainer, summaries
and probes are reconstructed here; standard trainer is the pinned implementation
and its original-code checks are separately rerun. Frozen files are never edited.
"""
from pathlib import Path
import os, sys, json, hashlib, time, socket, datetime
import ast, types

ROOT = Path(__file__).resolve().parents[3]
C = ROOT / 'campaigns/learning_rule_transport_2026-10-28'
OUT = Path(__file__).resolve().parents[1] / 'artifacts/policy_audit'
OUT.mkdir(parents=True, exist_ok=True)
os.environ['NUMBA_CACHE_DIR'] = str(OUT / 'numba_cache')
sys.dont_write_bytecode = True
sys.path.insert(0, str(C / 'code'))
import numpy as np
from scipy.special import expit
from rnn_learning import load_rnn
from rnn_rollout import calibration_particles
from baselines import load_bank, draw_initial, omission_at, competence_at
from trainer import VectorTrainer, trainer_self_test
from learning_models import subject_arrays, static_fit
from run_forecasts import seed_for

MODEL = C / 'artifacts/rnn/rnnglm32_nested_best.npz'
BANK = C / 'artifacts/baselines/nested_growth_bank.npz'
HORIZON = 3000

def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def denied(*a, **k):
    raise PermissionError('Independent policy audit is offline and source-consumed only')
socket.create_connection = denied
socket.socket.connect = denied

def log(event):
    with (OUT / 'EXPOSURE.jsonl').open('a') as f:
        f.write(json.dumps(dict(utc=datetime.datetime.now(datetime.timezone.utc).isoformat(), **event)) + '\n')

def probability(w, signed):
    z = np.tanh(5 * signed) / np.tanh(5.)
    X = np.stack([np.clip(z, 0, None), np.clip(z, None, 0), np.ones_like(z)], axis=-1)
    return expit(np.einsum('...j,...j->...', w, X))

def update_independent(w, h, s, c, r, day, params, scale=1.):
    """Direct GRU equations, independently read from the exported matrices."""
    z = np.tanh(5 * s) / np.tanh(5.)
    inp = np.column_stack((w, z, np.ones(len(z)), np.broadcast_to(day, len(z)),
                           c < 0, r > 0, z > 0))
    inp_project = inp @ params['Wih'].T + params['bih']
    hid_project = h @ params['Whh'].T + params['bhh']
    ii = np.split(inp_project, 3, axis=1)
    hh = np.split(hid_project, 3, axis=1)
    reset_gate = expit(ii[0] + hh[0])
    keep_gate = expit(ii[1] + hh[1])
    proposal = np.tanh(ii[2] + reset_gate * hh[2])
    memory = keep_gate * h + (1 - keep_gate) * proposal
    rect1 = np.clip(memory @ params['A'].T + params['a'], 0, None)
    rect2 = np.clip(rect1 @ params['B'].T + params['b'], 0, None)
    delta = scale * params['scale'] * (rect2 @ params['C'].T + params['cc'])
    responding = (c != 0)[:, None]
    return np.where(responding, w + delta, w), np.where(responding, memory, h)

class SavedCalibration:
    def __init__(self, model, cal):
        self.model = model
        self.cal = cal
        self.hidden = model.hidden
    def initial_state(self, prefix, method):
        return dict(w=np.array(self.cal['endpoint']), h=np.array(self.cal['hidden_endpoint']), w0=np.array(self.cal['w0']))
    def sequence(self, *a, **k):
        return self.model.sequence(*a, **k)

def load_consumed_prefix(subject, meta, path):
    processed = C / 'data/processed' / meta['split'] / (subject + '.npz')
    log(dict(event='read_consumed_source_prefix', subject=subject, path=str(processed),
             note='Full arrays were already decoded in prior campaign; use first1000only',
             sha256=digest(processed)))
    with np.load(processed, allow_pickle=False) as f:
        prefix = {k:f[k][:1000] for k in f.files
                  if k != 'metadata_json' and f[k].ndim > 0 and len(f[k]) >= 1000}
    # Session starts were saved from metadata opportunities before original scores.
    with np.load(path.with_suffix('.npz'), allow_pickle=False) as f:
        starts = f['session_start'][:HORIZON]
    if len(prefix['choice']) != 1000 or len(starts) != HORIZON:
        raise RuntimeError('Unexpected prefix/horizon')
    return prefix, starts

def recurrence_check(model, prefix, meta):
    s, c, r, day = subject_arrays(prefix)
    w = np.asarray(meta['calibration']['w0'])[None, :]
    h = np.zeros((1, model.hidden))
    probs=[]
    for t in range(1000):
        probs.append(probability(w, s[t:t+1])[0])
        w,h=update_independent(w,h,s[t:t+1],c[t:t+1],r[t:t+1],day[t],model.params)
    oldp,_,oldend=model.sequence(prefix, np.asarray(meta['calibration']['w0']))
    ans=dict(prefix_probability_error=float(np.max(np.abs(np.array(probs)-oldp))),
             saved_weight_endpoint_error=float(np.max(np.abs(w[0]-meta['calibration']['endpoint']))),
             saved_hidden_endpoint_error=float(np.max(np.abs(h[0]-meta['calibration']['hidden_endpoint']))))
    # Omission and current-trial chronology are explicit independent witnesses.
    wo,ho=update_independent(w,h,np.array([1.]),np.array([0]),np.array([-1.]),1.,model.params)
    ans['omission_state_error']=float(max(np.max(np.abs(wo-w)),np.max(np.abs(ho-h))))
    ans['correct_side_signs']=bool(probability(np.array([[3.,3.,0.],[3.,3.,0.]]),np.array([-1.,1.]))[0]<.5<probability(np.array([[3.,3.,0.],[3.,3.,0.]]),np.array([-1.,1.]))[1])
    if max(ans['prefix_probability_error'],ans['saved_weight_endpoint_error'],ans['saved_hidden_endpoint_error'])>1e-11:
        raise AssertionError(ans)
    return ans

def original_correction_check():
    """Exercise original _next_position and _next_contrast branch decisions.

    Inject known normal/uniform variates, avoiding a comparison of two RNGs.
    This check targets the side/correction branch driving the large contrast.
    """
    source=C/'sources/trainer/6.4.2_trial_params.py'
    tree=ast.parse(source.read_text())
    cls=next(node for node in tree.body if isinstance(node,ast.ClassDef) and node.name=='TrialParamHandler')
    methods=[node for node in cls.body if isinstance(node,ast.FunctionDef) and node.name in ['_next_position','_next_contrast']]
    var=dict(normal=0.,uniform=.5)
    def choice(options,p):return options[0 if var['uniform']<p[0] else 1]
    scope=dict(random=types.SimpleNamespace(gauss=lambda mean,sd:mean+sd*var['normal']),
        np=types.SimpleNamespace(random=types.SimpleNamespace(choice=choice)),
        log=types.SimpleNamespace(debug=lambda *a:None))
    exec(compile(ast.Module(body=methods,type_ignores=[]),str(source),'exec'),scope)
    original_pos=scope['_next_position'];original_con=scope['_next_contrast']
    tested=0
    for k in range(11):
        right=k/10
        obj=types.SimpleNamespace(contrast=types.SimpleNamespace(type='RepeatContrast'),response_buffer=[1]*k+[-1]*(10-k),
                                 stim_probability_left=.5,position_set=[-35,35])
        for z in [-3.,-1.,-.2,0.,.2,1.,3.]:
            var['normal']=z
            pos,p=original_pos(obj)
            assert pos==(-35 if right+.5*z<.5 else 35)
            assert p==1-right
            tested+=1
        # Its saved correction probability controls the next adaptive side draw.
        obj.contrast.type='AdaptiveContrast';obj.stim_probability_left=1-right
        for u in [.001,.1,.499,.5,.899,.999]:
            var['uniform']=u
            pos,p=original_pos(obj)
            assert pos==(-35 if u<1-right else 35)
            assert p==.5
            tested+=1
    branches=0
    for correct in [False,True]:
      for repeat in [False,True]:
       for con in [0.,.0625,.125,.25,.5,1.]:
        obj=types.SimpleNamespace(trial_correct=correct,repeat_on_error=repeat,
            repeat_contrasts=[1.,.5],contrast=types.SimpleNamespace(value=con),
            current_contrast=con,ac=types.SimpleNamespace(value=.25,type='AdaptiveContrast'),
            rc=types.SimpleNamespace(value=None,type='RepeatContrast'))
        original_con(obj)
        assert (obj.contrast.type=='RepeatContrast')==(not correct and repeat and con>=.5)
        branches+=1
    return dict(source_sha256=digest(source),position_cases=tested,contrast_branch_cases=branches,
                all_agree=True,scope='Original pinned correction branch, side mapping, and one-trial probability carryover')

def simulate(model, prefix, starts, common, state, n, seed, policy, variant='primary', kind='rnn', independent=True):
    rng=np.random.default_rng(seed+101)
    tr=VectorTrainer.from_prefix(prefix,n,seed+419,'standard' if policy=='standard' else 'external',
        correction=variant!='no_correction',promotion='fast' if variant=='fast' else 'slow' if variant=='slow' else 'source')
    fixed_rng=np.random.default_rng(seed+419)
    w=state['w'].copy();h=state['h'].copy()
    if variant=='hidden_zero':h[:]=0
    if variant=='static_current': w[:]=static_fit(prefix)
    initial_w=w.copy();initial_h=h.copy()
    xx=np.empty((n,HORIZON));cc=np.empty((n,HORIZON),np.int8)
    probes=np.zeros((n,6));weights=np.empty((n,6,3));diagnostic=[]
    max_w=0.;max_h=0.;repeat_count=0;omission_count=0
    contrasts={};scale=.9 if variant=='update_scale.9' else 1.1 if variant=='update_scale1.1' else 1.
    for t in range(HORIZON):
        if starts[t]:
            tr.new_session()
            if variant=='session_retention.8':w*=.8;h*=.8
            elif variant=='session_reset':w=initial_w.copy();h=initial_h.copy()
        if policy=='external' and independent:
            cons=np.array([1.,.25,.125,.0625])
            if variant=='fixed_including50':cons=np.array([1.,.5,.25,.125,.0625])
            elif variant=='fixed_easy':cons=np.array([1.,.5])
            magnitudes=cons[fixed_rng.integers(0,len(cons),n)]
            side=np.where(fixed_rng.random(n)<.5,-1,1)
            x=magnitudes*side
            repeats=np.zeros(n,bool)
        else:
            task=tr.sample();x=task['signed_contrast'];side=task['side'];magnitudes=task['contrast'];repeats=task['is_repeat']
        if kind=='growth':w=competence_at(common,t)
        omit=omission_at(common,t,'persistence' if variant=='fixed_omission' else 'growth')
        if variant=='no_omission':omit=np.zeros(n)
        # Equal-side response probability probes; no training is delivered.
        probes[:,t//500]+=(1-omit)*(.5*(expit(w[:,0]+w[:,2])+1-expit(-w[:,1]+w[:,2])))/500
        p=probability(w,x)
        choice=np.where(rng.random(n)<p,-1,1).astype(np.int8)
        choice[rng.random(n)<omit]=0
        fb=np.where(choice==-side,1,-1)
        if not (policy=='external' and independent):
            old=tr.observe(choice)
            assert np.array_equal(old['feedbackType'],fb)
        before=w.copy()
        if kind=='rnn':
            flag=0. if variant=='session_flags_zero' else float(starts[t])
            if independent:w,h=update_independent(w,h,x,choice,fb,flag,model.params,scale)
            else:
                st=dict(w=w,h=h);model.update(st,x,choice,fb,session_start=bool(flag));w,h=st['w'],st['h']
        if (t+1)%500==0:
            weights[:,t//500]=w
        if t in (0,499,1499,2999):
            diagnostic.append(dict(t=t,mean_w=w.mean(0).tolist(),mean_absolute_delta=np.abs(w-before).mean(0).tolist(),
                mean_sensitivity_wsum=float((w[:,0]+w[:,1]).mean()),mean_bias=float(w[:,2].mean())))
        max_w=max(max_w,float(np.max(np.abs(w))));max_h=max(max_h,float(np.max(np.abs(h))))
        repeat_count+=int(repeats.sum());omission_count+=int((choice==0).sum())
        for value in np.unique(magnitudes):contrasts[str(value)]=contrasts.get(str(value),0)+int((magnitudes==value).sum())
        if not np.isfinite(w).all() or not np.isfinite(h).all():raise FloatingPointError('Nonfinite independent state')
        xx[:,t]=x;cc[:,t]=choice
    exact=np.empty((n,6));official=np.empty((n,6))
    for b in range(6):
        x=xx[:,500*b:500*(b+1)];c=cc[:,500*b:500*(b+1)]
        vals=[];high=[]
        for side in (-1,1):
            mask=np.isclose(x,side)
            den=mask.sum(1)
            vals.append(np.divide((mask&(c==-side)).sum(1),den,out=np.full(n,np.nan),where=den>0))
            mask=(x*side>=.5);den=mask.sum(1)
            high.append(np.divide((mask&(c==-side)).sum(1),den,out=np.full(n,np.nan),where=den>0))
        exact[:,b]=np.mean(vals,axis=0);official[:,b]=np.mean(high,axis=0)
    return dict(exact100=exact,probe100=probes,official_high=official,weights=weights,
                diagnostic=diagnostic,max_abs_weight=max_w,max_abs_hidden=max_h,
                repeat_fraction=repeat_count/(n*HORIZON),omission_fraction=omission_count/(n*HORIZON),
                contrast_fraction={k:v/(n*HORIZON) for k,v in contrasts.items()})

def stats(a):
    scalar=a.mean(2)
    return dict(mean=float(scalar.mean()),curve=a.mean((0,1)).tolist(),prefix_means=scalar.mean(1).tolist(),
        conditional_MC_SE=float(np.sqrt(np.var(scalar,axis=1,ddof=1).sum()/a.shape[1])/a.shape[0]),
        prefix_SD=float(scalar.mean(1).std(ddof=1)))

def main():
    begin=time.monotonic();model=load_rnn(MODEL);bank=load_bank(BANK)
    freeze=json.loads((C/'protocols/RNN_FREEZE.json').read_text())
    pins=[]
    for row in freeze['files']:
        path=C/row['path'];actual=digest(path)
        pins.append(dict(path=str(path),sha256=actual,agrees=actual==row['sha256']))
        assert pins[-1]['agrees']
    assert digest(MODEL)=='c7f675d18f4143891ed7d2c76d91f74be74da9565fbae5407952768e2c146940'
    jobs=[]
    for tag in ['rnn_source_animals','rnn_source_labs']:
        for path in (C/'artifacts/forecasts'/tag).glob('*__rnnglm32.json'):
            meta=json.loads(path.read_text())
            if meta['horizon']>=HORIZON:jobs.append((meta['subject'],meta,path))
    jobs=sorted(jobs,key=lambda j:hashlib.sha256(j[0].encode()).hexdigest())[:8]
    records=[];particles={};comparisons=[]
    with np.load(ROOT/'experiments/population_policy_preflight_2026-10-28/PARTICLES.npz',allow_pickle=False) as zz:
        original={k:zz[k] for k in zz.files}
    # Same64particles with independently written recurrence/fixed trainer reproduce preflight.
    for index,(subject,meta,path) in enumerate(jobs):
        prefix,starts=load_consumed_prefix(subject,meta,path);seed=seed_for(subject);n=64
        recurrence=recurrence_check(model,prefix,meta)
        common=draw_initial(prefix,bank,n,seed+211,exclude=subject,competence='growth')
        state,cal=calibration_particles(SavedCalibration(model,meta['calibration']),prefix,n,seed+313)
        variants=['primary']
        if index<4:variants+=['no_correction','fast','slow','fixed_including50','fixed_easy','hidden_zero','static_current',
                            'update_scale.9','update_scale1.1','fixed_omission','no_omission',
                            'session_retention.8','session_reset','session_flags_zero']
        rec=dict(subject=subject,split=meta['split'],saved_calibration_sha256=digest(path),recurrence=recurrence,variants={})
        for variant in variants:
            rec['variants'][variant]={}
            for policy in ['standard','external']:
                # Changes specific to one trainer leave the paired arm primary.
                effective=variant
                if variant in ['no_correction','fast','slow'] and policy=='external':effective='primary'
                if variant in ['fixed_including50','fixed_easy'] and policy=='standard':effective='primary'
                out=simulate(model,prefix,starts,common,state,n,seed,policy,effective)
                for metric in ['exact100','probe100','official_high']:
                    particles[f'{subject}__{variant}__{policy}__{metric}']=out[metric]
                    key=f'{subject}__rnn__{policy}__{metric}'
                    if variant=='primary' and key in original:
                        error=float(np.max(np.abs(out[metric]-original[key])))
                        comparisons.append(dict(subject=subject,policy=policy,metric=metric,max_error=error))
                        if error>1e-10:raise AssertionError(comparisons[-1])
                rec['variants'][variant][policy]={k:v for k,v in out.items() if k not in ['exact100','probe100','official_high','weights']}
            # Common generated uniforms vary only because policy changes x/reward and state.
        records.append(rec)
        print(json.dumps(dict(subject=subject,variants=len(variants),seconds=time.monotonic()-begin)),flush=True)
    summary={}
    variants=list(records[0]['variants'])
    for variant in variants:
        sj=[r['subject'] for r in records if variant in r['variants']]
        summary[variant]={}
        for metric in ['exact100','probe100','official_high']:
            standard=np.asarray([particles[f'{s}__{variant}__standard__{metric}'] for s in sj])
            external=np.asarray([particles[f'{s}__{variant}__external__{metric}'] for s in sj])
            summary[variant][metric]=dict(n_prefixes=len(sj),standard=stats(standard),external=stats(external),difference=stats(external-standard))
    trainer_tests=trainer_self_test()
    trainer_tests['original_correction']=original_correction_check()
    result=dict(scope='Independent simulation; eight consumed source prefixes; firstfour bounded sensitivities; no new26 or external data',
        n_particles=64,horizon=HORIZON,source_pins=pins,preflight_reconstruction=comparisons,trainer_tests=trainer_tests,
        records=records,summary=summary,seconds=time.monotonic()-begin,
        omissions='Failure for endpoint; skipped model updates, independent development-derived shared process',
        metadata='Physical rewardvolume/wheelgain are absent from actor; their numerical changes cannot affect this actor except via any independently changed stimuli or opportunity counts',
        parameter_sensitivity='Future additive update outputscale multiplied.9/1.1, no refit; not an uncertainty posterior',
        external_code_status='Paper results+first-session input audit supportfourcontrasts; exact customFP acquisitioncode unavailable',
        future_conditioning='Realized opportunity sessionstarts/counts; no calendar/stopping law')
    np.savez_compressed(OUT/'PARTICLES.npz',**particles)
    (OUT/'RESULT.json').write_text(json.dumps(result,indent=2)+'\n')
    (OUT/'PINS.json').write_text(json.dumps(dict(code_sha256=digest(__file__),model_sha256=digest(MODEL),bank_sha256=digest(BANK),result_sha256=digest(OUT/'RESULT.json'),particles_sha256=digest(OUT/'PARTICLES.npz')),indent=2)+'\n')
    print(json.dumps(dict(seconds=result['seconds'],summary={k:{m:v[m]['difference']['mean'] for m in ['exact100','probe100']} for k,v in summary.items()})),flush=True)

if __name__=='__main__':main()
