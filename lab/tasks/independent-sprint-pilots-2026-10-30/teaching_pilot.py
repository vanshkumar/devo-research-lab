"""Onset tolerance, temporal errors and matched scalar-feedback motor searches.

Uses only locally generated, admitted old synthetic pickles. No external pickle,
new biological observations, target-fitted motor basis or target gradient is used.
"""
import os,sys
sys.dont_write_bytecode=True
from pathlib import Path
HERE=Path(__file__).resolve().parent
os.environ['NUMBA_CACHE_DIR']=str(HERE/'numba_cache')
for k in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','VECLIB_MAXIMUM_THREADS'):os.environ[k]='2'
import argparse,copy,hashlib,importlib.util,json,pickle,time
from io import BytesIO
import numpy as np
from common import ROOT,SOURCE,read,load_json,save,now
spec=importlib.util.spec_from_file_location('sprint_source_helper',ROOT/'experiments/sensory_evaluator_preflight_2026-10-28/preflight.py')
helper=importlib.util.module_from_spec(spec);sys.modules[spec.name]=helper;spec.loader.exec_module(helper)
PERMS=np.array([np.arange(6),np.roll(np.arange(6),1),np.arange(6)[::-1],[1,0,3,2,5,4],np.roll(np.arange(6),3),np.roll(np.arange(6),2)])
MODES=('clocked','unregistered','onset_reset','no_clock')
PAD=100;LENGTH=helper.T_SONG+helper.T_POST+2*PAD

def features(action,basis,bias):
    y=np.maximum(np.einsum('d,scd->sc',action,basis)+bias,0.)
    y-=y.mean(axis=-1,keepdims=True)
    return 2*y/np.maximum(y.std(axis=-1,keepdims=True),1e-12)
def auditory(y,phase=0,stretch=1.,pad=PAD,length=LENGTH):
    aud=np.zeros((length,helper.NE));projected=np.repeat(y,helper.NE//helper.NC,axis=1)
    first=helper.ON[0]
    for k,(on,off) in enumerate(zip(helper.ON,helper.OFF)):
        lo=pad+phase+first+int(round((on-first)*stretch));hi=lo+int(round((off-on)*stretch))
        if lo<0 or hi>length:raise ValueError('Stimulus clipping would invalidate onset nuisance')
        aud[lo:hi]=projected[k]
    return aud
def clock(rh,phase=0):
    out=np.zeros((LENGTH,helper.NH));lo=PAD+phase
    out[lo:lo+len(rh)]=rh
    return out
def means():
    c=.5
    return np.array([1/np.sqrt(helper.NE*c),1.7/np.sqrt(helper.NI*c),1/np.sqrt(helper.NE*c),1.5/np.sqrt(helper.NI*c)])/10

def load(plant):
    path=ROOT/('campaigns/evaluator_optimization_2026-10-28/primary_snapshots/plant_%03d/state.pkl'%plant)
    data=pickle.loads(read(path,'admitted_synthetic_state'))
    # Pin every original numerical source, without decoding other input assets.
    for name,digest in data['source_hashes'].items():
        if hashlib.sha256(read(ROOT/name,'source_pin_check')).hexdigest()!=digest:raise RuntimeError('Original source pin changed')
    return data
def train_no_clock(state,plant):
    cached=SOURCE/('noclock_%03d.pkl'%plant)
    if cached.exists():return pickle.loads(read(cached,'derived_synthetic_state'))
    net=copy.deepcopy(state['nets']['untutored']);aud_one=auditory(state['target_features'],pad=0,length=1100)
    aud_train=np.concatenate([np.zeros((helper.T_BURN,helper.NE)),np.tile(aud_one,(35,1))]);rh=np.zeros((len(aud_train),helper.NH));m=means();t=time.monotonic()
    res=net.sim(state['initial_hE'],state['initial_hI'],rh,aud_train,[],len(aud_train),1,0,
                plasticity={'JEI':helper.bilin_hebb_EI,'JIE':helper.bilin_hebb_IE},lr={'JEI':5e-2,'JIE':6e-3},tauW=1e5,
                JEI0_mean=m[1],JIE0_mean=m[2],asyn_E=10,asyn_I=0,rE_th=1.5,rI_th=5,no_progress_bar=True)
    del res,aud_train,rh
    result={'net':net,'seconds':time.monotonic()-t,'source_clock':'zero throughout tutoring and testing','renditions':35}
    with cached.open('wb') as f:pickle.dump(result,f,pickle.HIGHEST_PROTOCOL)
    print(json.dumps({'plant':plant,'stage':'no_clock_trained','seconds':result['seconds']}),flush=True)
    return result
def evaluator(state,no_clock,mode):
    net=no_clock['net'] if mode=='no_clock' else state['nets']['learned35']
    # Shared quiet reset, independent of tutor/action/phase; test requires fixed states.
    z=net.sim(state['initial_hE'],state['initial_hI'],np.zeros((1000,helper.NH)),np.zeros((1000,helper.NE)),[],1000,1,0,no_progress_bar=True)
    hE,hI=z[-2:];del z
    calls={'logical_feedback_slots':0,'source_simulations':0,'cache_hits':0};cache={}
    def cost_shape(y,phase,stretch=1.):
        aud=auditory(y,phase=phase,stretch=stretch)
        if mode=='no_clock':rh=np.zeros((LENGTH,helper.NH))
        else:
            align=0
            if mode=='onset_reset':
                active=np.flatnonzero(np.max(np.abs(aud),axis=1)>1e-8)
                align=int(active[0])-(PAD+int(helper.ON[0])) if len(active) else 0
            rh=clock(state['rh'],phase=align)
        result=net.sim(hE,hI,rh,aud,[],LENGTH,1,0,no_progress_bar=True)
        value=float(np.mean(result[0]));calls['source_simulations']+=1
        if not np.isfinite(value):raise FloatingPointError('Nonfinite circuit cost')
        return value
    def callback(action):
        action=np.asarray(action);key=action.tobytes();calls['logical_feedback_slots']+=1
        if key in cache:calls['cache_hits']+=1;return cache[key]
        y=features(action[:4],state['basis'],state['bias'])[PERMS[int(action[4])]]
        phases=(0,0) if mode=='clocked' else (-60,60)
        value=float(np.mean([cost_shape(y,p) for p in phases]));cache[key]=value;return value
    return callback,cost_shape,calls
def true_loss(action,state):
    y=features(np.asarray(action)[:4],state['basis'],state['bias'])[PERMS[int(action[4])]]
    return float(np.mean((y-state['target_features'])**2))

def search(callback,initial,seed,rounds):
    x=np.asarray(initial,dtype=float).copy();value=callback(x);step=.4;rng=np.random.default_rng(seed)
    actions=[x.copy()];costs=[value];trajectory=[x.copy()];tcosts=[value]
    for r in range(rounds):
        proposals=[]
        for j in range(4):
            for sign in (1.,-1.):
                a=x.copy();a[j]=np.clip(a[j]+sign*step,-2,2);proposals.append(a)
        for p in range(6):
            if p!=int(x[4]):a=x.copy();a[4]=p;proposals.append(a)
        for k in range(3):
            a=np.r_[rng.uniform(-2,2,4),int(x[4]) if k<2 else int(rng.integers(6))];proposals.append(a)
        assert len(proposals)==16
        values=[callback(a) for a in proposals]
        actions.extend(proposals);costs.extend(values);best=int(np.argmin(values))
        if values[best]<value:x=proposals[best].copy();value=values[best]
        else:step=max(.00625,step/2)
        trajectory.append(x.copy());tcosts.append(value)
    return {'query_actions':np.array(actions),'query_costs':np.array(costs),'actions':np.array(trajectory),'costs':np.array(tcosts),'step':step}

def search_per_order(callback,initial,seed,rounds):
    """Six target-blind, fixed-order starts prevent greedy order/shape trapping."""
    rng=np.random.default_rng(seed);states=[];actions=[];costs=[]
    for p in range(6):
        x=np.r_[np.asarray(initial)[:4],float(p)];value=callback(x)
        states.append({'x':x,'value':value,'step':.4});actions.append(x.copy());costs.append(value)
    trajectory=[np.asarray(initial).copy()];tcosts=[float(costs[int(initial[4])])]
    best=min(states,key=lambda s:s['value']);trajectory.append(best['x'].copy());tcosts.append(best['value'])
    for r in range(rounds):
        broad=rng.uniform(-2,2,(2,4))
        for p,s in enumerate(states):
            proposals=[]
            for j in range(4):
                for sign in (1.,-1.):
                    a=s['x'].copy();a[j]=np.clip(a[j]+sign*s['step'],-2,2);proposals.append(a)
            proposals.extend(np.r_[b,float(p)] for b in broad)
            assert len(proposals)==10
            values=[callback(a) for a in proposals];actions.extend(proposals);costs.extend(values);k=int(np.argmin(values))
            if values[k]<s['value']:s['x']=proposals[k].copy();s['value']=values[k]
            else:s['step']=max(.00625,s['step']/2)
        best=min(states,key=lambda s:s['value']);trajectory.append(best['x'].copy());tcosts.append(best['value'])
    return {'query_actions':np.array(actions),'query_costs':np.array(costs),'actions':np.array(trajectory),'costs':np.array(tcosts),'step':np.array([s['step'] for s in states])}

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--plant',type=int,choices=[100,101,102],required=True);ap.add_argument('--stage',choices=['diagnostics','learning'],required=True);ap.add_argument('--rounds',type=int,default=20);ap.add_argument('--search',choices=['coupled','per_order'],default='per_order');ap.add_argument('--only-oracle',action='store_true');args=ap.parse_args();t0=time.monotonic();state=load(args.plant);no_clock=None if args.only_oracle else train_no_clock(state,args.plant)
    saved=load_json(ROOT/('campaigns/evaluator_optimization_2026-10-28/primary_snapshots/plant_%03d/preparation.json'%args.plant))
    aud=auditory(state['target_features'],pad=0,length=1100);h=state['probe_states']['learned35']
    reference,_=helper.run_frozen(state['nets']['learned35'],aud,h['hE'],h['hI'],state['rh'])
    assert abs(float(reference.mean())-saved['target_costs']['learned35']['mean'])<1e-10
    if args.stage=='diagnostics':
        rows=[]
        for mode in MODES:
            _,score,calls=evaluator(state,no_clock,mode)
            for phase in (-60,0,60):
                for condition,perm,stretch in [('correct',0,1.),('rotate',1,1.),('reverse',2,1.),('short_duration',0,.8),('long_duration',0,1.2)]:
                    y=state['target_features'][PERMS[perm]];value=score(y,phase,stretch)
                    rows.append({'mode':mode,'phase_ms':phase,'condition':condition,'cost':value})
        result={'plant':args.plant,'reference_score_reproduced':float(reference.mean()),'rows':rows,'seconds':time.monotonic()-t0,'scope':'full-cycle mean-rate score; no noise, fixed unit gain; onset reset retains known six-context timing template; no-clock retrained/tested with HVC zero'}
        save('outputs/teaching_diagnostics_%03d.json'%args.plant,result);print(json.dumps(result,indent=2));return
    initial=np.r_[state['initial'],1.];results=[]
    modes=('oracle',) if args.only_oracle else ('oracle',)+MODES
    expected=1+16*args.rounds if args.search=='coupled' else 6*(1+10*args.rounds)
    for mode in modes:
        if mode=='oracle':callback=lambda a:true_loss(a,state);calls={'logical_feedback_slots':expected,'source_simulations':0}
        else:callback,_,calls=evaluator(state,no_clock,mode)
        actor=(search if args.search=='coupled' else search_per_order)(callback,initial,80000+args.plant,args.rounds)
        # Gold scoring is offline, after the actor has finished consuming scalar feedback.
        losses=np.array([true_loss(a,state) for a in actor['actions']]);qloss=np.array([true_loss(a,state) for a in actor['query_actions']])
        assert len(actor['query_actions'])==expected
        out={'plant':args.plant,'mode':mode,'search':args.search,'rounds':args.rounds,'queries':len(actor['query_actions']),'initial_loss':float(losses[0]),'final_loss':float(losses[-1]),'improvement':float(1-losses[-1]/losses[0]),'final_order':int(actor['actions'][-1,4]),'final_cost':float(actor['costs'][-1]),'feedback':calls}
        np.savez(HERE/('outputs/teaching_%03d_%s_%s_%d.npz'%(args.plant,mode,args.search,args.rounds)),**actor,true_losses=losses,query_true_losses=qloss)
        results.append(out);save('outputs/teaching_learning_%03d_%s_%d.json'%(args.plant,args.search,args.rounds),{'results':results,'seconds':time.monotonic()-t0,'reference':float(reference.mean())})
        print(json.dumps(out),flush=True)
        if mode=='oracle' and out['improvement']<.8 and not args.only_oracle:
            print(json.dumps({'oracle_gate':'failed','teacher_searches':'not_run'}),flush=True)
            break
if __name__=='__main__':main()
