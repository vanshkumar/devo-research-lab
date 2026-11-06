"""One from-trial-one reliability ablation; only consumed invented inputs."""
from pathlib import Path
import importlib.util, json, hashlib, time, resource
import numpy as np

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
TASK=ROOT/'lab/tasks/noise-context-feasibility-2026-10-29'
spec=importlib.util.spec_from_file_location('frozen_noise_pilot',TASK/'pilot.py')
pilot=importlib.util.module_from_spec(spec);spec.loader.exec_module(pilot)
FAMILIES=('original','relocated','deterministic')
CURRICULA=('blocked','interleaved','early','late')
SEEDS=tuple(range(27001,27021))

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def dump(p,v):p.write_text(json.dumps(v,indent=2,allow_nan=False)+'\n')

class ReliabilityOne(pilot.Learner):
    def weight(self,x):return 1.

def independent_inputs(seed,curr,family,permuted):
    rng=np.random.default_rng(seed)
    tail=rng.integers(0,2,40);branch=rng.integers(0,2,200)
    first={'blocked':[0]*40+[1]*40+[0]*40+[1]*40,
           'interleaved':[0,1]*80,
           'early':[0]*40+[1]*40+[0,1]*40,
           'late':[0,1]*40+[0]*40+[1]*40}[curr]
    ctx=np.r_[first,tail]
    exp=np.zeros((200,5),dtype=int);exp[:,1]=1+ctx
    if family=='original':exp[:,2]=3+branch;exp[:,3]=5+(branch+ctx)%2;exp[:,4]=7+branch;noise=1
    elif family=='relocated':exp[:,2]=3+ctx;exp[:,3]=5+branch;exp[:,4]=7+(branch+ctx)%2;noise=2
    else:exp[:,2]=3+ctx;exp[:,3]=5;exp[:,4]=7+ctx;noise=-1
    pairs=np.array([[1,2],[3,4],[5,6],[7,8]])
    if permuted:
        pm=np.random.default_rng(seed+908172).permutation(9);exp=pm[exp];pairs=pm[pairs]
    return exp,ctx,pairs,noise

def online(seq,ablated=False):
    cls=ReliabilityOne if ablated else pilot.Learner
    l=cls('learned')
    P=np.zeros((200,4,2));W=np.zeros((200,4));E=np.zeros((200,4));Z=np.zeros((200,4),int)
    for s,story in enumerate(seq['exp']):
        l.begin_story()
        for t in range(4):
            x,y=map(int,story[t:t+2])
            # Prediction and both weights use only completed earlier stories.
            P[s,t]=l.predict(x,seq['pairs'][t])
            W[s,t]=l.weight(x)
            E[s,t]=pilot.Learner.weight(l,x)
            Z[s,t]=l.observe(x,y,W[s,t])
        l.end_story()
    assert l.n_updates==800 and l.raw.sum()==800 and l.T.sum()==800
    return P,W,E,Z,l

def metrics(P,W,E,Z,exp,ctx,pairs,noise,l):
    truth=(exp[:,1:,None]==pairs[None,:,:]).argmax(2)
    correct=np.take_along_axis(P,truth[:,:,None],axis=2)[...,0]
    signal=[t for t in (1,2,3) if t!=noise]
    right=0
    for z in np.unique(Z[160:,-1]):
        c=ctx[160:][Z[160:,-1]==z];right+=max((c==0).sum(),(c==1).sum())
    return {'test_signal_probability':float(correct[160:,signal].mean()),
            'test_signal_nll':float(-np.log(correct[160:,signal]).mean()),
            'stories81to85_probability':float(correct[80:85,signal].mean()),
            'stories81to120_probability':float(correct[80:120,signal].mean()),
            'test_probability_each_step':correct[160:].mean(0).tolist(),
            'test_applied_reliability_each_step':W[160:].mean(0).tolist(),
            'test_estimated_reliability_each_step':E[160:].mean(0).tolist(),
            'test_context_purity':float(right/40),
            'n_schemas':int((l.n>0).sum()),'n_updates':l.n_updates,
            'test_signal_modal_accuracy':float(np.where(abs(correct[160:,signal]-.5)<1e-12,.5,correct[160:,signal]>.5).mean())}

def main():
    start=time.monotonic()
    freeze=json.loads((HERE/'FREEZE.json').read_text())
    for n,v in freeze['comparison_files'].items():assert sha(HERE/n)==v
    before={n:sha(TASK/n) for n in freeze['source_task_files']}
    assert before==freeze['source_task_files']
    oldmeta=json.loads((TASK/'scored_metadata.json').read_text())
    with np.load(TASK/'scored_predictions.npz',allow_pickle=False) as archive:
        saved={k:archive[k] for k in ('p','w','z')}
    lookup={(m['family'],m['curriculum'],m['seed'],m['permuted'],m['role']):i for i,m in enumerate(oldmeta)}
    rows=[];pall=[];wall=[];eall=[];zall=[];meta=[];checks=[];partitions=[]
    for family in FAMILIES:
        for curr in CURRICULA:
            for seed in SEEDS:
                prior={}
                for permuted in (False,True):
                    exp,ctx,pairs,noise=independent_inputs(seed,curr,family,permuted)
                    seq=pilot.make_sequence(seed,curr,family,permuted)
                    assert np.array_equal(seq['exp'],exp) and np.array_equal(seq['ctx'],ctx) and np.array_equal(seq['pairs'],pairs) and seq['noise_t']==noise
                    outputs={}
                    for ablated in (False,True):
                        name='reliability_one' if ablated else 'full'
                        P,W,E,Z,l=online(seq,ablated)
                        outputs[name]=(P,W,E,Z,l)
                        m=dict(family=family,curriculum=curr,seed=seed,permuted=permuted,role=name,
                               input_sha256=hashlib.sha256(exp.tobytes()+pairs.tobytes()).hexdigest())
                        rows.append({**m,**metrics(P,W,E,Z,exp,ctx,pairs,noise,l)})
                        meta.append(m);pall.append(P);wall.append(W);eall.append(E);zall.append(Z)
                        if not ablated:
                            i=lookup[(family,curr,seed,permuted,'learned')]
                            assert np.array_equal(P,saved['p'][i]) and np.array_equal(W,saved['w'][i]) and np.array_equal(Z,saved['z'][i])
                        else:assert np.all(W==1)
                        if not permuted:prior[name]=(P,W,E,Z)
                        else:
                            a=prior[name]
                            assert all(np.array_equal(v,q) for v,q in zip(a,(P,W,E,Z)))
                    if not permuted:
                        a,b=outputs['full'],outputs['reliability_one'];za,zb=a[3][:,-1],b[3][:,-1]
                        partitions.append(dict(family=family,curriculum=curr,seed=seed,
                            partition_disagreement=float(np.mean((za[:,None]==za)!=(zb[:,None]==zb))),
                            end_counts_identical=bool(np.array_equal(a[4].raw,b[4].raw)),
                            max_end_count_difference=float(np.max(abs(a[4].raw-b[4].raw))),
                            probability_max_difference=float(np.max(abs(a[0]-b[0])))))
                    assert time.monotonic()-start<240,'Leave time for the independent audit inside the 300s simulation ceiling'
    np.savez_compressed(HERE/'ablation_predictions.npz',p=np.stack(pall),w=np.stack(wall),estimated_w=np.stack(eall),z=np.stack(zall))
    dump(HERE/'ablation_metadata.json',meta);dump(HERE/'ablation_metrics.json',rows);dump(HERE/'state_comparisons.json',partitions)
    rng=np.random.default_rng(77201);ix=rng.integers(0,20,(10000,20))
    def interval(v):return np.percentile(np.asarray(v)[ix].mean(1),[2.5,97.5]).tolist()
    groups=[]
    for family in FAMILIES:
        for curr in CURRICULA:
            rr=[m for m in rows if m['family']==family and m['curriculum']==curr and not m['permuted']]
            aa=[m for m in rr if m['role']=='full'];bb=[m for m in rr if m['role']=='reliability_one']
            group={'family':family,'curriculum':curr,'roles':{}}
            for role,mm in [('full',aa),('reliability_one',bb)]:
                keys=[k for k,v in mm[0].items() if isinstance(v,(int,float,list)) and k not in ('seed','permuted')]
                group['roles'][role]={k:np.mean([m[k] for m in mm],axis=0).tolist() for k in keys}
            for key in ('test_signal_probability','test_signal_nll','stories81to85_probability','stories81to120_probability'):
                v=np.array([a[key]-b[key] for a,b in zip(aa,bb)])
                group['full_minus_reliability_one_'+key]={'mean':float(v.mean()),'ci95':interval(v),'paired_seed_values':v.tolist()}
            group['state_comparison']={k:float(np.mean([r[k] for r in partitions if r['family']==family and r['curriculum']==curr])) for k in ('partition_disagreement','end_counts_identical','max_end_count_difference','probability_max_difference')}
            groups.append(group)
    contrast=[]
    for family in FAMILIES:
        cr={}
        for role in ('full','reliability_one'):
            def get(curr):return np.array([m['test_signal_probability'] for m in rows if m['family']==family and m['curriculum']==curr and m['role']==role and not m['permuted']])
            v=get('early')-get('late');cr[role]={'mean':float(v.mean()),'ci95':interval(v)}
        contrast.append({'family':family,'early_minus_late':cr})
    runtime=time.monotonic()-start
    dump(HERE/'ABLATION.json',{'groups':groups,'mixed_contrast':contrast,
         'uncertainty':'Paired20consumed synthetic seeds;10000bootstrap draws at77201; generator variation only, no human uncertainty or equivalence.',
         'full_runs_match_saved_exactly':True,'all_permutations_exact':True,'all_applied_ablation_weights_one':True,
         'model_runs':len(rows),'unpermuted_inputs':240,'runtime_seconds':runtime,
         'peak_rss_bytes_macos':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
         'source_task_hashes_unchanged':before=={n:sha(TASK/n) for n in before}})
    for g in groups:
        d=g['full_minus_reliability_one_test_signal_probability']
        print(g['family'],g['curriculum'],'full',g['roles']['full']['test_signal_probability'],'one',g['roles']['reliability_one']['test_signal_probability'],'difference',d['mean'],'CI',d['ci95'])
    print('runtime_seconds',runtime,'peak_rss_bytes_macos',resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)

if __name__=='__main__':main()
