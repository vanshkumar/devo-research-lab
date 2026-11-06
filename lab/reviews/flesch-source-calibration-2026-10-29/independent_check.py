"""Local independent review. Never opens the combined MAT or any target response.

Run with NUMBA_DISABLE_JIT=1 and PYTHONDONTWRITEBYTECODE=1. Reference
enumeration uses rational arithmetic; reference learning uses matrix updates.
"""
import os
os.environ['NUMBA_DISABLE_JIT'] = '1'
os.environ['NUMBA_NUM_THREADS'] = '1'
os.environ['OMP_NUM_THREADS'] = '1'
os.environ['OPENBLAS_NUM_THREADS'] = '1'
from pathlib import Path
from fractions import Fraction as F
import sys, json, hashlib, itertools, math, resource, time
import numpy as np

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
SRC = REPO / 'sources/flesch_source_calibration_2026-10-29'
TASK = REPO / 'lab/tasks/flesch-source-calibration-2026-10-29'
sys.path.insert(0, str(SRC))
import learning as impl

started = time.time()
checks = []
results = {}
def check(name, yes, **detail):
    checks.append({'name': name, 'passed': bool(yes), **detail})
    if not yes:
        raise AssertionError(name)
def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()
before = {str(p.relative_to(REPO)): sha(p) for p in [SRC/'learning.py', SRC/'fit.py', SRC/'forecast.py', TASK/'DESIGN.md', TASK/'MASKS.json']}

# An invented 5-event history. The ignored test boundary still changes last
# action. Late and finite-timeout events count as errors. Three nonboundary
# test opportunities require K>=2 under 20K>11N.
T, end, need = 5, 1, 2
truth = np.array([1, 0, 1, 1, 0], dtype=np.int64)
boundary = np.array([False, False, True, False, False])
q_late, q_miss = F(7,100), F(11,100)
mixw = [F(1,3), F(2,3)]
tables = [
    [[F(15+5*t+9*s+10*j,100) for s in range(3)] for t in range(T)]
    for j in range(2)
]
def enumerate_rational(table, drop_boundary=False):
    out = {}
    for path in itertools.product(range(5), repeat=T):
        prob, prev, correct = F(1), 0, 0
        for t, event in enumerate(path):
            if drop_boundary and t >= end and boundary[t]:
                continue
            if event == 4:
                prob *= q_miss
                prev = 0
            else:
                act = event % 2
                late = event >= 2
                accept = table[t][prev+1]
                prob *= (q_late if late else 1-q_late-q_miss) * (accept if act else 1-accept)
                prev = 2*act-1
                if t >= end and not boundary[t] and not late and act == truth[t]:
                    correct += 1
        out[path] = (prob, correct >= need)
    return out
enum = [enumerate_rational(tab) for tab in tables]
As = [sum((v[0] for v in e.values() if v[1]), F(0)) for e in enum]
for j, e in enumerate(enum):
    mass = sum((v[0] for v in e.values()), F(0))
    got, total = impl.selected_dp(np.array(tables[j], dtype=float), truth, boundary, np.array([float(q_late),float(q_miss)]), end, need)
    check(f'rational history/count mass and DP type {j}', mass == 1 and abs(got-float(As[j])) < 3e-14 and abs(total-1)<3e-14,
          exact_acceptance=str(As[j]), implementation_acceptance=got)
trajectory = (1,0,4,1,0)
Y = [e[trajectory][0] for e in enum]
Abar = sum(w*a for w,a in zip(mixw,As))
right = sum(w*y for w,y in zip(mixw,Y))/Abar
wrong = sum(w*y/a for w,y,a in zip(mixw,Y,As))
selected_mass = sum(sum(mixw[j]*enum[j][path][0] for j in range(2))/Abar for path in enum[0] if enum[0][path][1])
check('ratio-of-integrals selected law normalizes exactly', selected_mass == 1 and abs(float(right-wrong))>1e-5,
      trajectory_probability_correct=float(right), wrong_average_of_truncations=float(wrong),
      preselection_type_weights=list(map(float,mixw)), selected_type_weights=[float(w*a/Abar) for w,a in zip(mixw,As)])
acts = np.array([1,0,-1,1,0]); timing = np.array([0,0,2,0,0])
for j in range(2):
    ll = impl.observed_logp(np.array(tables[j], dtype=float), acts, timing, np.array([float(q_late),float(q_miss)]))
    check(f'complete observed history density type {j}', abs(math.exp(ll)-float(Y[j]))<1e-16)
# The source primary has no silent NaN-correctness class; this arithmetic is
# an independent semantic witness for the declared but unfinished alternative.
check('helper versus omissions-as-errors witness', 20*2 > 11*2 and not 20*2 > 11*5)
results['finite_state_witness'] = {'events': T, 'training_events':end, 'test_nonboundary_events':3,
    'late_probability':float(q_late), 'finite_timeout_probability':float(q_miss),
    'mixture_acceptance':float(Abar), 'correct_selected_trajectory_probability':float(right),
    'wrong_selected_trajectory_probability':float(wrong), 'exact_mass':str(selected_mass)}

# Independent vector algebra for the causal adapter and SGD -> all-input Oja.
# Pinned trainer source computes y=W.T@x after SGD and excludes the .1 hidden
# bias from Oja. No Torch import is needed for this algebraic comparison.
def reference_net(features, ctx, rewards, p, z, W, V, test_ema=False):
    W, V = W.copy(), V.copy()
    bias = 0.; cue = np.eye(2)[ctx[0]].copy(); seen = set(); out=[]
    lr=p[0]*math.exp(p[7]*z)
    for t,(f,c) in enumerate(zip(features,ctx)):
        seen.add(int(c))
        if t<400 or test_ema:
            cue = (1-p[2])*cue + p[2]*np.eye(2)[c]
            current = cue.copy()
        else:
            current = np.eye(2)[c].copy()
        x=np.r_[f,p[3]*(current-(.5 if len(seen)==2 else 0))]
        pre=x@W+.1; hidden=np.maximum(pre,0); value=float(hidden@V+bias)
        out.append(value)
        if t<400:
            sig=1/(1+math.exp(-value)); step=lr*rewards[t]*sig*(1-sig)
            grad=step*V*(pre>0)
            V=V+step*hidden; W=W+np.outer(x,grad); bias+=step
            y=x@W
            W=W+p[1]*y[None,:]*(x[:,None]-y[None,:]*W)
    return np.array(out)
rng=np.random.default_rng(915317)
f=rng.normal(0,.13,(402,25)); coords=rng.normal(0,.1,(402,2))
ctx=np.r_[np.zeros(3,dtype=np.int64), np.ones(198,dtype=np.int64),np.arange(201,dtype=np.int64)%2]
rew=rng.choice([-2.,-1.,0.,1.,2.],402)
W=rng.normal(0,.01,(27,100)); V=rng.normal(0,.01,100)
p=np.array([.087,.0013,.37,2.9,1.8,.17,.8,.42])
got=impl.base_logits(0,f,coords,ctx,rew,p,.61,W,V)
ref=reference_net(f,ctx,rew,p,.61,W,V)
check('pre-feedback full network prescription versus vector reconstruction',np.max(np.abs(got-ref))<2e-12,max_abs_error=float(np.max(np.abs(got-ref))))
changed=rew.copy(); changed[0] = 2 if rew[0]!=2 else -2
got_changed=impl.base_logits(0,f,coords,ctx,changed,p,.61,W,V)
check('first emission hides its feedback; later state receives it',got[0]==got_changed[0] and abs(got[1]-got_changed[1])>1e-7)
changed=rew.copy(); changed[400:]=1e9
check('test feedback hidden throughout',np.array_equal(got,impl.base_logits(0,f,coords,ctx,changed,p,.61,W,V)))
ref_ema=reference_net(f,ctx,rew,p,.61,W,V,True)
got_ema=impl.base_logits(0,f,coords,ctx,rew,p,.61,W,V,True)
check('continued test EMA sensitivity distinct and correctly implemented',np.max(np.abs(ref_ema-got_ema))<2e-12 and np.max(np.abs(got[400:]-got_ema[400:]))>1e-8)

# Only permitted archives are opened. Reconstruct grouping and person split
# without the investigator's mask functions, and raw-source opportunity scores.
inp=np.load(SRC/'inputs_only.npz',allow_pickle=False)
resp=np.load(SRC/'source_responses.npz',allow_pickle=False)
mask=json.loads((TASK/'MASKS.json').read_text())
groups={k:[] for k in ['B2','B20','B200','Interleaved']}
for col in range(176):
    x=inp['expt_contextIDX'][:400,col]
    edges=np.r_[0,np.flatnonzero(np.diff(x)!=0)+1,400]
    runs=np.diff(edges)
    name='B200' if np.array_equal(runs,[200,200]) else 'B20' if np.all(runs==20) else 'B2' if np.all(runs==2) else 'Interleaved'
    groups[name].append(col)
check('independent input-derived groups match frozen masks',groups==mask['groups'])
cols=sorted(groups['B200']+groups['Interleaved'])
check('response archive restricted to 95 source columns',len(cols)==95 and cols==mask['source_columns'] and all(resp[k].shape==(600,95) for k in resp.files))
for group in ['B200','Interleaved']:
    order=sorted(groups[group],key=lambda c:hashlib.sha256(('flesch-source-split-v1:'+str(c)).encode()).hexdigest())
    n=math.floor(.75*len(order))
    check('independent hashed split '+group, order[:n]==mask['split'][group]['fit'] and order[n:]==mask['split'][group]['check'])
cats=inp['expt_catIDX'][:,cols]
actions=resp['resp_category']; rt=resp['resp_reactiontime']; corr=resp['resp_correct']; reward=resp['resp_reward']
timing=np.where(~np.isfinite(actions),2,np.where(rt>5,1,0))
effective=corr.copy();effective[rt>5]=0
keep=cats[400:]!=0
N=np.sum(keep & np.isfinite(effective[400:]),axis=0)
K=np.sum(np.where(keep,np.nan_to_num(effective[400:]),0),axis=0)
check('all source helper eligibility and fixed N=160 primary',np.all(N==160) and np.all(20*K>11*N) and np.all(np.isfinite(corr)) and np.all(np.isfinite(rt)))
valid=np.isfinite(actions)
expected=(actions==(cats>=0)).astype(float)
check('original response correctness reconciles without deletion',np.all(corr[valid]==expected[valid]))
expected_reward=np.where(actions==1,inp['expt_rewardIDX'][:,cols],0)
check('original chosen reward agrees for valid responses',np.all(reward[valid]==expected_reward[valid]))
fitcols=[c for g in ['B200','Interleaved'] for c in mask['split'][g]['fit']]
checkcols=[c for g in ['B200','Interleaved'] for c in mask['split'][g]['check']]
fi=[cols.index(c) for c in fitcols];ci=[cols.index(c) for c in checkcols]
results['source_audit']={'people':95,'fit_people':len(fi),'check_people':len(ci),'groups':{k:len(v) for k,v in groups.items()},
    'timing_all':{str(k):int(np.sum(timing==k)) for k in range(3)},
    'timing_fit':{str(k):int(np.sum(timing[:,fi]==k)) for k in range(3)},
    'timing_check':{str(k):int(np.sum(timing[:,ci]==k)) for k in range(3)},
    'min_test_correct':int(K.min()),'max_test_correct':int(K.max()),'target_response_values_read':0}
obs=np.empty((24,8))
for j,i in enumerate(ci):
    for b in range(8):
        ix=np.arange(50*b,50*b+50);ix=ix[cats[ix,i]!=0]
        obs[j,b]=np.sum((actions[ix,i]==(cats[ix,i]>=0)) & (timing[ix,i]==0))/len(ix)

# Verify saved first-start score logic independently. This is development
# assessment, not a prospective comparison or model-selection calibration.
saved=np.load(SRC/'primary_source_check_forecasts.npz',allow_pickle=False)
assessment=json.loads((TASK/'primary_SOURCE_ASSESSMENT.json').read_text())
check('saved source score columns and raw-observed curves agree',np.array_equal(saved['columns'],checkcols) and np.array_equal(saved['observed'],obs))
score_rows={}; summary={}
for name in ['sgd_oja','context_value','exposure_growth']:
    simulations=saved[name]; n=simulations.shape[1]
    perm=np.random.default_rng(74301).permutation(n//2)
    es=[]
    for s,y in zip(simulations,obs):
        d=np.sqrt(np.sum((s-y)**2,axis=1)).sum()/n
        paired=np.sqrt(np.sum((s[:n//2]-s[n//2:][perm])**2,axis=1)).sum()/(n//2)
        es.append(d-.5*paired)
    score_rows[name]=np.array(es);summary[name]={}
    for group in ['B200','Interleaved']:
        ix=[j for j,c in enumerate(checkcols) if c in groups[group]]
        mae=float(100*np.abs(simulations[ix].mean(axis=(0,1))-obs[ix].mean(axis=0)).mean())
        score=float(np.mean(np.array(es)[ix])); claimed=assessment['models'][name]['groups'][group]
        check('independent saved energy/MAE '+name+' '+group,abs(mae-claimed['population_curve_mae_pp'])<1e-11 and abs(score-claimed['energy_score'])<1e-13)
        summary[name][group]={'energy_score':score,'population_curve_mae_pp':mae}
results['first_start_source_scores']=summary
results['first_start_learner_growth_energy_advantage']=float(np.mean(score_rows['exposure_growth']-score_rows['context_value']))

# Frozen design bytes and input archive remain authoritative through review.
freeze=json.loads((TASK/'PRE_RESPONSE_FREEZE.json').read_text())
for rel in ['lab/tasks/flesch-source-calibration-2026-10-29/DESIGN.md','lab/tasks/flesch-source-calibration-2026-10-29/MASKS.json','sources/flesch_source_calibration_2026-10-29/inputs_only.npz']:
    check('pre-response frozen bytes '+rel,sha(REPO/rel)==freeze['files'][rel])
results['reviewed_hashes_before']=before
results['reviewed_hashes_after']={rel:sha(REPO/rel) for rel in before}
results['checks']=checks
results['passed']=sum(c['passed'] for c in checks)
results['elapsed_seconds']=time.time()-started
results['max_rss_bytes']=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*(1024 if sys.platform!='darwin' else 1)
results['memory_cap_bytes']=512*1024*1024
check('review process remains below 512 MB RSS',results['max_rss_bytes']<results['memory_cap_bytes'])
results['scientific_gate']='not established: no full-pipeline known-effect/null refit or complete sensitivity envelope checked'
(HERE/'independent_results.json').write_text(json.dumps(results,indent=2)+'\n')
print(json.dumps({k:v for k,v in results.items() if k not in ['checks','reviewed_hashes_before','reviewed_hashes_after']},indent=2))
