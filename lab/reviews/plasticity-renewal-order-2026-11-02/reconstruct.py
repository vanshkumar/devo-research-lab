"""Distinct review; independent standard-library scalar equations, no author imports."""
import hashlib
import json
import math
from pathlib import Path
import random
import resource
import sys
import time
import traceback

HERE = Path(__file__).resolve().parent
TASKS = HERE.parent.parent / 'tasks'
AUTHOR = TASKS / 'plasticity-renewal-order-consequence-2026-11-02'
SOURCE = TASKS / 'plasticity-retention-source-benchmark-2026-11-02'
NAMES = ['cbp_literal','cbp_mean','cbp_literal_replay','cbp_mean_replay',
         'random_literal_replay','random_mean_replay','sgd_replay','cache']
SEEDS = list(range(240001,240009))
READS = []
START = time.perf_counter()
T7 = 2.364624251


def read(path):
    assert path.stat().st_size < 10_000_000
    raw = path.read_bytes()
    READS.append(dict(path=str(path.relative_to(HERE.parent.parent.parent)),
                      bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest()))
    return raw


def load(path):
    return json.loads(read(path))


def predict(t,x):
    # Independent dense input representation; no packed-input/helper imports.
    answer=t[110]
    for unit in range(5):
        base=21*unit
        z=t[base+20]+sum(t[base+k]*x[k] for k in range(20))
        if z>0:
            answer+=t[105+unit]*z
    return answer


def target(d,x):
    # FixLTUNet strict LTU; pinned prob.json beta=.7 overrides constructor .75.
    answer=d['teacher_out_bias']
    for w,b,v in zip(d['teacher_weights'],d['teacher_bias'],d['teacher_out_weights']):
        tau=.7*21-(20-sum(w)+b)/2
        if sum(w[k]*x[k] for k in range(20))+b>tau:
            answer+=v
    return answer


def risk(t,inputs,labels):
    return math.fsum((predict(t,x)-y)**2 for x,y in zip(inputs,labels))/32


def check_close(x,y,label,tol=5e-11):
    gap=abs(x-y)
    assert gap<=tol,(label,x,y,gap)
    return gap


def interval(vals):
    n=len(vals); mean=math.fsum(vals)/n
    se=math.sqrt(math.fsum((x-mean)**2 for x in vals)/(n-1)/n)
    return dict(mean=mean,se=se,lower=mean-T7*se,upper=mean+T7*se,
                individual=vals,model='paired eight-teacher t7; coverage unvalidated')


def summary(matrix,bins):
    competence=[matrix[j][j] for j in range(100)]
    first=[bins[10*j] for j in range(100)]
    ages={}
    for lo,hi in [(1,9),(10,49),(50,99)]:
        cells=[(matrix[k][j],competence[j]) for k in range(100) for j in range(k) if lo<=k-j<=hi]
        ages[f'{lo}-{hi}']=dict(mean_old_risk=math.fsum(a for a,b in cells)/len(cells),
                               mean_change_from_initial=math.fsum(a-b for a,b in cells)/len(cells),
                               cells=len(cells))
    return dict(acquisition_first1000_all_tasks=math.fsum(first)/100,
                acquisition_first1000_tasks10to99=math.fsum(first[10:])/90,
                acquisition_all_examples=math.fsum(bins)/1000,
                time_average_all_old_risk=math.fsum(math.fsum(matrix[k][:k])/k for k in range(1,100))/99,
                final_all_old_risk=math.fsum(matrix[99][:99])/99,
                mean_initial_competence=math.fsum(competence)/100,
                final_old_change_from_initial=math.fsum(matrix[99][j]-competence[j] for j in range(99))/99,
                final_current_risk=matrix[99][99],initial_competence_by_task=competence,
                retention_by_age=ages)


def compare_tree(a,b,where):
    gaps=[]
    if isinstance(a,dict):
        for k in a: gaps.extend(compare_tree(a[k],b[k],where+'.'+k))
    elif isinstance(a,list):
        assert len(a)==len(b),(where,'length')
        for k,(x,y) in enumerate(zip(a,b)): gaps.extend(compare_tree(x,y,where+f'[{k}]'))
    elif isinstance(a,(int,float)):
        gaps.append(check_close(a,b,where))
    return gaps


def data_rng_check(d,seed):
    r=random.Random(seed)
    signs=lambda:2*r.randrange(2)-1
    assert d['teacher_weights']==[[signs() for _ in range(20)] for _ in range(100)]
    assert d['teacher_bias']==[signs() for _ in range(100)]
    assert d['teacher_out_weights']==[signs() for _ in range(100)]
    assert d['teacher_out_bias']==signs()
    assert d['contexts']==[[r.randrange(2) for _ in range(15)] for _ in range(101)]
    for i,v in enumerate(d['fast_indices']):
        assert v==r.randrange(32),(seed,'fast',i)
    t=[]
    for j in range(5):
        t.extend(r.uniform(-math.sqrt(.3),math.sqrt(.3)) for _ in range(20)); t.append(0.)
    t.extend(r.uniform(-math.sqrt(.6),math.sqrt(.6)) for _ in range(5)); t.append(0.)
    assert t==d['initial_learner']
    return True


def main():
    pins=[]
    sm=load(SOURCE/'SOURCE_MANIFEST.json')
    for row in sm['files']:
        raw=read(SOURCE/'vendor'/row['path'])
        actual=hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest()
        assert actual==row['blob_sha1'],row['path']
        pins.append(dict(path=row['path'],git_blob=actual,bytes=len(raw)))
    receipt=load(AUTHOR/'EXECUTION_RECEIPT.json')
    freeze=read(AUTHOR/'FREEZE.md')
    assert hashlib.sha256(freeze).hexdigest()==receipt['freeze_sha256']
    for rel,pin in receipt['code'].items():
        raw=read(TASKS/rel)
        assert hashlib.sha256(raw).hexdigest()==pin['sha256'],rel
    assert receipt['seeds']==SEEDS and receipt['planned_teachers']==8
    # Exact rational positive/negative identities, distinct from old-task risks.
    from fractions import Fraction as F
    v,h=F(3,10),F(1)
    rational=dict(constant_literal_squared_change=str((v*h)**2),
                  constant_retained_squared_change=str((v*h-v*h)**2),
                  dead_both_squared_change=str((v*F(0))**2))
    per_teacher=[]; prediction_count=0; max_gap=0.; event_max=0.; event_count=0
    for seed in SEEDS:
        tick=time.perf_counter()
        d=load(AUTHOR/f'REALIZATION_{seed}.json')
        o=load(AUTHOR/f'OUTPUT_{seed}.json')
        assert o['realization_sha256']==READS[-2]['sha256']
        assert d['seed']==o['seed']==seed
        assert len(d['fast_indices'])==1_010_000 and len(d['contexts'])==101
        data_rng_check(d,seed)
        inputs=[[c+[(f>>k)&1 for k in range(5)] for f in range(32)] for c in d['contexts']]
        labels=[[target(d,x) for x in row] for row in inputs]
        assert labels==d['targets_by_context']
        support_counts=[len(set(d['fast_indices'][10000*j:10000*(j+1)])) for j in range(101)]
        scores={}; initial={}; gaps=[]
        for name in NAMES:
            bins=o['online_1000_bins'][name]
            assert len(bins)==1000 and all(math.isfinite(x) for x in bins)
            if name=='cache':
                matrix=o['risk_matrices'][name] # Earlier cache states absent: inherited.
                saved=o['cache_final']
                mapping=dict(zip(saved['keys'],saved['labels']))
                fallback=saved['total']/saved['count']
                for j in range(100):
                    losses=[]
                    for x,y in zip(inputs[j],labels[j]):
                        key=sum(value<<k for k,value in enumerate(x))
                        losses.append((mapping.get(key,fallback)-y)**2)
                    gaps.append(check_close(math.fsum(losses)/32,matrix[99][j],f'{seed} cache final{j}'))
            else:
                assert len(o['learner_snapshots'][name])==100
                matrix=[]
                for k,t in enumerate(o['learner_snapshots'][name]):
                    assert len(t)==111 and all(math.isfinite(z) for z in t)
                    row=[risk(t,inputs[j],labels[j]) for j in range(k+1)]
                    prediction_count+=32*(k+1)
                    for j,value in enumerate(row):
                        gaps.append(check_close(value,o['risk_matrices'][name][k][j],f'{seed} {name} {k} {j}'))
                    matrix.append(row)
                initial[name]=risk(d['initial_learner'],inputs[0],labels[0])
                check_close(initial[name],o['initial_before'][name],f'{seed} {name} initial')
            scores[name]=summary(matrix,bins)
            gaps.extend(compare_tree(scores[name],o['summaries'][name],f'{seed} {name} summary'))
        # Only the saved intervention identity is checked here; no contrary costs computed.
        for name,events in o['sampled_events'].items():
            for e in events:
                before,after=e['before'],e['after']; chosen=e['chosen']
                shift=math.fsum(before[105+j]*mu for j,mu in zip(chosen,e['old_means'])) if e['compensate'] else 0.
                event_max=max(event_max,check_close(before[110]+shift,after[110],f'{seed} {name} bias',1e-12))
                for j in chosen:
                    assert after[105+j]==0 and after[21*j+20]==0
                x=[(e['key']>>k)&1 for k in range(20)]
                removed=math.fsum(before[105+j]*max(0.,before[21*j+20]+sum(before[21*j+k]*x[k] for k in range(20))) for j in chosen)
                event_max=max(event_max,check_close(predict(before,x)-removed+shift,predict(after,x),f'{seed} {name} identity',1e-11))
                event_count+=1
        for a,b in [('cbp_literal','cbp_mean'),('cbp_literal_replay','cbp_mean_replay'),('random_literal_replay','random_mean_replay')]:
            assert o['steps'][a]==o['steps'][b]
        max_gap=max(max_gap,max(gaps))
        per_teacher.append(dict(seed=seed,scores=scores,initial_before=initial,
                                unique_current_contexts=len({tuple(c) for c in d['contexts'][:100]}),
                                fast_support_counts=support_counts,steps=o['steps'],replacements=o['replacements'],
                                compensation=o['compensation'],storage=o['storage'],
                                cache_hits_inherited=o['cache_final']['hits'],max_scalar_gap=max(gaps)))
        print(json.dumps(dict(seed=seed,status='PASS',seconds=time.perf_counter()-tick,max_gap=max(gaps))),flush=True)
        assert resource.getrusage(resource.RUSAGE_SELF).ru_maxrss<1_000_000_000
        assert time.perf_counter()-START<1000
    comparisons={}
    for alt in NAMES:
        for base in NAMES:
            if alt==base:continue
            avg=[];terminal=[];cost=[]
            for row in per_teacher:
                a,b=row['scores'][alt],row['scores'][base]
                avg.append((b['time_average_all_old_risk']-a['time_average_all_old_risk'])/b['time_average_all_old_risk'])
                terminal.append((b['final_all_old_risk']-a['final_all_old_risk'])/b['final_all_old_risk'])
                cost.append((a['acquisition_first1000_all_tasks']-b['acquisition_first1000_all_tasks'])/b['acquisition_first1000_all_tasks'])
            ai,ti,ci=interval(avg),interval(terminal),interval(cost)
            comparisons[alt+' versus '+base]=dict(average=ai,terminal=ti,acquisition_cost=ci,
                joint_pass=ai['lower']>.10 and ti['lower']>.10 and ci['upper']<.02,
                teacher_joint_successes=sum(x>=.10 and y>=.10 and z<=.02 for x,y,z in zip(avg,terminal,cost)))
    output=dict(status='PASS',utc=time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),
                source_git_pins=pins,receipt_code_freeze_pins='PASS; saved chronology consistent, not independently timestamp-certified',
                rational_controls=rational,neural_predictions_reconstructed=prediction_count,
                teacher_labels_reconstructed=8*101*32,full_saved_rng_regeneration='PASS',
                maximum_risk_summary_gap=max_gap,sampled_events=event_count,maximum_event_identity_gap=event_max,
                independent_units=8,t7=T7,zero_of_eight_exact_onesided95_upper=1-.05**(1/8),
                per_teacher=per_teacher,comparisons=comparisons,
                inherited=['online training/bin errors (arithmetic only, full gradients not replayed)',
                           'earlier cache boundary states/hit counts','original Torch execution unrun',
                           'deployment/historical author intent','total process-memory storage matching'],
                reads=READS,explicit_file_read_bytes=sum(x['bytes'] for x in READS),
                read_hash_decode_conservative_bytes=3*sum(x['bytes'] for x in READS)+3_000_000,
                seconds=time.perf_counter()-START,peak_rss_bytes_macos=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
                own_code_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest())
    (HERE/'RECONSTRUCTION.json').write_text(json.dumps(output,indent=2)+'\n')
    for k in ['cbp_mean versus cbp_literal','cbp_mean_replay versus cbp_literal_replay','random_mean_replay versus random_literal_replay']:
        print(json.dumps(dict(comparison=k,**comparisons[k])),flush=True)
    print(json.dumps({k:output[k] for k in ['status','utc','seconds','neural_predictions_reconstructed','maximum_risk_summary_gap','peak_rss_bytes_macos','explicit_file_read_bytes']}),flush=True)


if __name__=='__main__':
    try: main()
    except BaseException:
        (HERE/'RECONSTRUCTION_FAILURE.txt').write_text(traceback.format_exc())
        (HERE/'RECONSTRUCTION_FAILURE_RESOURCES.json').write_text(json.dumps(dict(seconds=time.perf_counter()-START,reads=READS,peak_rss_bytes_macos=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss),indent=2))
        raise
