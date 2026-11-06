"""Tutor-observable target memories; no motor labels enter teacher learning."""
import os,sys
sys.dont_write_bytecode=True
for k in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','VECLIB_MAXIMUM_THREADS'):os.environ[k]='2'
from common import ROOT,HERE,SOURCE,read,charge,save,check_deadline
os.environ['NUMBA_CACHE_DIR']=str(HERE/'numba_cache')
import types,pickle,io
import numpy as np
shim=types.ModuleType('tqdm');shim.tqdm=lambda iterable,*a,**kw:iterable;sys.modules['tqdm']=shim
sys.path.insert(0,str(ROOT/'sources/sensory_evaluator_feasibility_2026-10-28/upstream/src'))
import models
T=2200;N=100;ON=np.arange(6)*150+50;OFF=ON+100
PERMS=np.array([np.arange(6),np.roll(np.arange(6),1),np.arange(6)[::-1],[1,0,3,2,5,4],np.roll(np.arange(6),3),np.roll(np.arange(6),2)])

def features(shape,basis,bias):
    y=np.maximum(np.einsum('...d,scd->...sc',shape,basis)+bias,0)
    y-=y.mean(axis=-1,keepdims=True)
    return 2*y/np.maximum(y.std(axis=-1,keepdims=True),1e-12)

def waveform(y,stretch=1.,phase=0):
    a=np.zeros((T,N))
    for k,(on,off) in enumerate(zip(ON,OFF)):
        start=100+phase+int(ON[0])+int(round((int(on)-int(ON[0]))*stretch));end=start+int(round((off-on)*stretch))
        assert 0<=start<end<=T,'clipped audio'
        a[start:end]=y[k]
    return a

def load_old(plant):
    p=ROOT/('campaigns/evaluator_optimization_2026-10-28/primary_snapshots/plant_%03d/inputs.npz'%plant)
    with np.load(io.BytesIO(read(p,'consumed_plant_inputs')),allow_pickle=False) as z:d={k:z[k].copy() for k in z.files}
    charge(str(p.relative_to(ROOT)),sum(v.nbytes for v in d.values()),'decoded_arrays')
    net=pickle.loads(read(ROOT/('sources/independent_sprint_2026-10-30/noclock_%03d.pkl'%plant),'consumed_no_clock_circuit'))['net']
    return d,net

def simulate(net,a,h=None,trace=True):
    check_deadline();aud=np.repeat(a,6,axis=1)
    hE,hI=(np.zeros(net.NE),np.zeros(net.NI)) if h is None else h
    out=net.sim(hE,hI,np.zeros((len(a),net.NH)),aud,[],len(a),1,0,no_progress_bar=True)
    return out[0],(out[-2],out[-1])

def quiet(net):
    _,h=simulate(net,np.zeros((1000,N)))
    return h

def moment_features(r):
    z=r/100.
    return np.r_[z.mean(0),(z*z).mean(0)]

def prototype(r):
    z=r/100.;m=moment_features(r)
    variance=np.r_[z.var(0),(z*z).var(0)]+1e-6
    return {'mean':m,'variance':variance}

def population_cost(r,p):return float(np.mean((moment_features(r)-p['mean'])**2/p['variance']))

def onset(a):
    found=np.flatnonzero(np.mean(a*a,axis=1)>1e-8)
    return int(found[0]) if len(found) else None

def learn_state(a):
    """Acquire ordered occurrence states/dwell/gaps from observable input runs."""
    active=np.mean(a*a,axis=1)>1e-8;edges=np.diff(np.r_[False,active,False].astype(int))
    starts=np.flatnonzero(edges==1);ends=np.flatnonzero(edges==-1)
    assert len(starts)>0
    return {'emissions':np.stack([a[s:e].mean(0) for s,e in zip(starts,ends)]),
            'starts':starts-starts[0],'durations':ends-starts,'first_onset':int(starts[0])}

def state_prediction(memory,start):
    # Autonomous learned occurrence/age schedule; no candidate-driven time warp.
    pred=np.zeros((T,N));states=memory['emissions']
    for j in range(len(states)):
        lo=start+int(memory['starts'][j]);hi=lo+int(memory['durations'][j]);lo=max(0,lo);hi=min(T,hi)
        if hi>lo:pred[lo:hi]=states[j]
    return pred

def state_cost(a,m):
    start=onset(a);start=0 if start is None else start
    return float(np.mean((a-state_prediction(m,start))**2))

def template_cost(a,teacher):
    astart=onset(a);tstart=onset(teacher)
    if astart is None:return float(np.mean(teacher*teacher))
    pred=np.zeros_like(a);shift=astart-tstart
    lo=max(0,shift);hi=min(T,T+shift)
    pred[lo:hi]=teacher[lo-shift:hi-shift]
    return float(np.mean((a-pred)**2))

def policies(seed,number=64):
    result=[tuple(int(i) for i in p) for p in PERMS];rng=np.random.default_rng(seed)
    while len(result)<number:
        p=tuple(int(i) for i in rng.permutation(6))
        if p not in result:result.append(p)
    return np.array(result)
