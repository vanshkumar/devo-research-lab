"""Reconstruct saved losses/searches without running another circuit search.

This is an implementation-author check, not independent scientific review.
The supplied query costs are replayed; their numerical source is not re-certified
by this replay. Source dynamics have a separate zero-noise reconstruction check.
"""
import os, sys
sys.dont_write_bytecode = True
for key in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','VECLIB_MAXIMUM_THREADS'):
    os.environ[key] = '2'
import csv, json, resource, time
from io import BytesIO
import numpy as np
from common import ROOT, HERE, SOURCE, read, save, now

PERMS = np.array([[0,1,2,3,4,5],[5,0,1,2,3,4],[5,4,3,2,1,0],
                  [1,0,3,2,5,4],[3,4,5,0,1,2],[4,5,0,1,2,3]])

def get_arrays(path, kind):
    with np.load(BytesIO(read(path, kind)), allow_pickle=False) as z:
        return {key:z[key].copy() for key in z.files}

def sensory(shape, basis, bias):
    # Explicit contraction written separately from the actor's einsum helper.
    values = (basis * np.asarray(shape)[None,None,:]).sum(axis=2) + bias
    values = np.where(values > 0, values, 0)
    centered = values - values.mean(axis=1)[:,None]
    scale = np.sqrt((centered * centered).mean(axis=1))
    return centered * (2 / np.maximum(scale, 1e-12))[:,None]

def losses(actions, inp):
    desired = sensory(inp['target'], inp['basis'], inp['bias'])
    return np.array([((sensory(a[:4],inp['basis'],inp['bias'])[PERMS[int(a[4])]]-desired)**2).mean()
                     for a in actions])

def replay_actor(saved, initial, plant):
    qa,qc=saved['query_actions'],saved['query_costs'];cursor=0;error=0.;seen={}
    def observe(proposal):
        nonlocal cursor,error
        assert cursor < len(qa)
        error=max(error,float(np.max(np.abs(qa[cursor]-proposal))))
        assert np.allclose(qa[cursor],proposal,rtol=0,atol=1e-14)
        value=float(qc[cursor]);key=qa[cursor].tobytes()
        if key in seen: assert abs(value-seen[key])<1e-12
        seen[key]=value;cursor+=1
        return value
    states=[]
    for order in range(6):
        action=np.r_[initial,float(order)]
        states.append([action,observe(action),.4])
    actions=[np.r_[initial,1.]];costs=[states[1][1]]
    best=min(states,key=lambda v:v[1]);actions.append(best[0].copy());costs.append(best[1])
    rng=np.random.default_rng(80000+plant)
    for iteration in range(20):
        broad=rng.uniform(-2,2,(2,4))
        for order,entry in enumerate(states):
            action,value,step=entry;proposals=[]
            for coordinate in range(4):
                for sign in (1.,-1.):
                    candidate=action.copy();candidate[coordinate]=np.clip(candidate[coordinate]+sign*step,-2,2)
                    proposals.append(candidate)
            proposals += [np.r_[candidate,float(order)] for candidate in broad]
            values=[observe(a) for a in proposals];pick=int(np.argmin(values))
            if values[pick]<value: entry[:2]=[proposals[pick].copy(),values[pick]]
            else: entry[2]=max(.00625,step/2)
        best=min(states,key=lambda v:v[1]);actions.append(best[0].copy());costs.append(best[1])
    assert cursor==1206==len(qa)
    assert np.allclose(actions,saved['actions'],rtol=0,atol=1e-14)
    assert np.allclose(costs,saved['costs'],rtol=0,atol=1e-14)
    assert np.all(np.diff(costs)<=1e-12)
    assert np.all(np.abs(qa[:,:4])<=2)
    assert np.all((qa[:,4]>=0)&(qa[:,4]<6)&(qa[:,4]==qa[:,4].astype(int)))
    return {'query_count':cursor,'trajectory_points':len(actions),
            'query_action_max_error':error,'distinct_queries':len(seen)}

def main():
    start=time.monotonic();checks=[]
    for plant in (100,101,102):
        inp=get_arrays(ROOT/('campaigns/evaluator_optimization_2026-10-28/primary_snapshots/plant_%03d/inputs.npz'%plant),'admitted_synthetic_inputs')
        modes=('oracle','clocked','unregistered','onset_reset','no_clock')
        if (HERE/('outputs/teaching_%03d_untutored_no_clock_per_order_20.npz'%plant)).exists():modes+=('untutored_no_clock',)
        for mode in modes:
            path=HERE/('outputs/teaching_%03d_%s_per_order_20.npz'%(plant,mode))
            if not path.exists():
                checks.append({'plant':plant,'mode':mode,'status':'unrun'});continue
            saved=get_arrays(path,'derived_actor');errors=[]
            for actions,name in ((saved['actions'],'true_losses'),(saved['query_actions'],'query_true_losses')):
                error=float(np.max(np.abs(losses(actions,inp)-saved[name])))
                assert error<1e-11;errors.append(error)
            replay=replay_actor(saved,inp['initial'],plant)
            canonical=saved['actions'][[-1]].copy();canonical[:,4]=0
            checks.append({'plant':plant,'mode':mode,'gold_max_error':max(errors),
                           'chosen_order':int(saved['actions'][-1,4]),
                           'offline_canonical_order_content_mse':float(losses(canonical,inp)[0]),**replay})
    # Re-run the corrected current-only reference using its admitted cached trace.
    import worm_pilot as w
    worm=get_arrays(SOURCE/'worm_0.npz','consumed_derived_worm')
    ref=w.forecasts(worm['x'],float(worm['dt']),str(worm['uid']),maxlag=0,pc=False)
    assert {r['method'] for r in ref}=={'persistence','local_current','population_current'}
    old=list(csv.DictReader(read(ROOT/'experiments/causal_identification/neural_audit_check.csv','consumed_reference').decode().splitlines()))
    ref_errors=[]
    for row in ref:
        if row['method']=='persistence':continue
        method={'local_current':'anchored_diagonal','population_current':'anchored_population'}[row['method']]
        expected=next(float(v['test_mse']) for v in old if float(v['seconds'])==row['seconds'] and v['method']==method)
        ref_errors.append(abs(row['mse']-expected))
    assert max(ref_errors)<1e-8
    for path,count in (('worm_main.csv',144),('worm_shifts.csv',108),('worm_controls.csv',90)):
        rows=list(csv.DictReader(read(HERE/'outputs'/path,'derived_result').decode().splitlines()))
        assert len(rows)==count
    ledger=json.loads((HERE/'READS.json').read_text())
    raw={r['path'] for r in ledger['reads'] if r['kind']=='consumed_worm'}
    selection=json.loads(read(ROOT/'experiments/neural_dynamics/selection.json','source_selection'))
    allowed={'data/public/'+r['path'].split('/')[-1] for r in selection['discovery']}
    assert raw==allowed and len(raw)==6
    assert all(not any(token in r['path'].lower() for token in ('pan_vazquez','habits','memory_policy_transfer'))
               for r in ledger['reads'] if r['kind']!='context')
    original_noise=HERE/'outputs/teaching_source_noise_100_failed_serialization.npz'
    rerun_noise_max_error=None
    if original_noise.exists():
        a=get_arrays(original_noise,'derived_noise_control');b=get_arrays(HERE/'outputs/teaching_source_noise_100.npz','derived_noise_control')
        assert set(a)==set(b)
        rerun_noise_max_error=max(float(np.max(np.abs(a[key]-b[key]))) for key in a)
        assert rerun_noise_max_error<1e-12
    out={'time':now(),'teaching_checks':checks,'corrected_worm_reference_max_error':max(ref_errors),
         'raw_worms_only_admitted_six':True,'decoded_read_bytes_before_final_record':ledger['total_bytes'],
         'export_repair_seeded_noise_max_error':rerun_noise_max_error,
         'seconds':time.monotonic()-start,'peak_rss_bytes_macOS':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
         'scope':'author verification; deterministic actor replay consumes recorded scalar costs; no independent-review signoff'}
    save('outputs/VERIFICATION.json',out)
    print(json.dumps(out,indent=2))

if __name__=='__main__':main()
