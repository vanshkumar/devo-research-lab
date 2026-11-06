"""Independent numerical-boundary and generative-state witnesses, local only."""
import os
os.environ['NUMBA_DISABLE_JIT']='1'
os.environ['OPENBLAS_NUM_THREADS']='1'
os.environ['OMP_NUM_THREADS']='1'
from pathlib import Path
import numpy as np, sys, math, json, resource, hashlib
HERE=Path(__file__).resolve().parent;REPO=HERE.parents[2];SRC=REPO/'sources/flesch_source_calibration_2026-10-29'
sys.path.insert(0,str(SRC));import learning as impl
checks=[]
def check(name,yes,**info):
    checks.append({'name':name,'passed':bool(yes),**info});assert yes,name
p=np.array([.1,.001,.4,3.,1.,0.,0.,.2]);q=np.array([.03,.08])
vals=np.array([-1000.,-50.,-2.,0.,2.,50.,1000.])
for acts in [np.zeros(7,dtype=int),np.ones(7,dtype=int),np.arange(7)%2]:
    timing=np.array([0,1,0,0,1,0,0]);tm=np.where(timing==1,q[0],1-q.sum())
    signed=np.where(acts==1,vals,-vals)
    expected=float((np.log(tm)-np.logaddexp(0.,-signed)).sum())
    got=impl.observed_logp_logits(vals,p,0.,acts,timing,q)
    check('stable log emission '+''.join(map(str,acts)),abs(got-expected)<1e-12,expected=expected,actual=got)
check('exact-zero timing mass remains impossible',np.isneginf(impl.observed_logp_logits(np.array([0.]),p,0.,np.array([1]),np.array([1]),np.array([0.,.08]))))
check('missing action resets persistence state',abs(impl.observed_logp_logits(np.array([0.,0.]),np.array([.1,.001,.4,3.,1.,0.,1.,.2]),0.,np.array([-1,1]),np.array([2,0]),q)-(math.log(q[1])+math.log(1-q.sum())-math.log(2)))<1e-13)

truth=np.ones(600,dtype=np.int64);truth[:400]=np.arange(400)%2
boundary=np.zeros(600,dtype=bool);boundary[::5]=True
tables=np.empty((2,600,3));tables[0]=np.array([.45,.5,.6]);tables[1]=np.array([.65,.8,.9]);ww=np.array([.4,.6])
def own_accept(table):
    state={(0,0):1.}
    for t in range(600):
        nxt={}
        for (k,prev),mass in state.items():
            a=table[t,prev+1]
            for act in [0,1]:
                for late,tm in [(False,1-q.sum()),(True,q[0])]:
                    kk=min(89,k+int(t>=400 and not boundary[t] and not late and act==truth[t]))
                    key=(kk,2*act-1);nxt[key]=nxt.get(key,0)+mass*tm*(a if act else 1-a)
            key=(k,0);nxt[key]=nxt.get(key,0)+mass*q[1]
        state=nxt
    return sum(m for (k,prev),m in state.items() if k==89),sum(state.values())
AA=[]
for j in range(2):
    A,mass=own_accept(tables[j]);AA.append(A)
    got,total=impl.selected_dp(tables[j],truth,boundary,q)
    check('600-event independent recursion type '+str(j),abs(A-got)<2e-13 and abs(mass-1)<2e-13 and abs(total-1)<2e-13,acceptance=A)
AA=np.array(AA);expected=ww@AA
curves,ok,acts,times,types=impl.simulate_from_probs(tables,truth,boundary,q,ww,2048,915318)
observed=ok.mean();se=math.sqrt(expected*(1-expected)/2048)
posterior=ww*AA/expected;selected_type=(types[ok]==1).mean();type_se=math.sqrt(posterior[1]*(1-posterior[1])/ok.sum())
check('generative selection rate matches separate recursion',abs(observed-expected)<5*se,expected=expected,observed=observed,mc_se=se)
check('selection reweights sampled person mixture',abs(selected_type-posterior[1])<5*type_se,expected=posterior[1],observed=selected_type,mc_se=type_se)
manual=np.empty((2048,8))
for b in range(8):
    ix=np.arange(50*b,50*b+50);ix=ix[~boundary[ix]]
    manual[:,b]=np.mean((acts[:,ix]==truth[ix])&(times[:,ix]==0),axis=1)
check('generated opportunity curve counts late/missing as errors and drops only boundaries',np.array_equal(curves,manual))
x=np.load(SRC/'inputs_only.npz',allow_pickle=False)
check('actual immutable chronology agrees with hardcoded 400/200 phase boundary',np.all(x['expt_sessIDX'][:400]==1) and np.all(x['expt_sessIDX'][400:]==2) and np.all(np.diff(x['expt_index'],axis=0)==1))
result={'checks':checks,'passed':len(checks),'reviewed_learning_sha256':hashlib.sha256((SRC/'learning.py').read_bytes()).hexdigest(),
    'target_response_values_read':0,'max_rss_bytes':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*(1 if sys.platform=='darwin' else 1024)}
assert result['max_rss_bytes']<512*1024*1024
(HERE/'kernel_boundary_results.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
