"""Frozen eight-teacher order intervention; standard library, one process/thread."""
import hashlib
import importlib.util
import json
import math
from pathlib import Path
import pickle
import random
import resource
import sys
import time
import traceback

from engine import OrderLearner, Learner, Reservoir, ExactCache, forward, pack_input, support_risk, cache_risk

ROOT = Path(__file__).resolve().parent
PREVIOUS = ROOT.parent / 'plasticity-retention-source-benchmark-2026-11-02'
spec = importlib.util.spec_from_file_location('source_feasibility', PREVIOUS / 'feasibility.py')
original = importlib.util.module_from_spec(spec)
spec.loader.exec_module(original)
SEEDS = list(range(240001, 240009))
N = 1_000_000
NAMES = ['cbp_literal', 'cbp_mean', 'cbp_literal_replay', 'cbp_mean_replay',
         'random_literal_replay', 'random_mean_replay', 'sgd_replay', 'cache']
START = None
DEADLINE = 1793676800.  # 2026-11-03T03:33:20Z; asserted below


def log(value):
    line = json.dumps(value, separators=(',', ':'))
    print(line, flush=True)
    with (ROOT / 'RUN.log').open('a') as handle:
        handle.write(line+'\n')


def check_limits():
    rss = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    assert rss <= 1_000_000_000, ('RSS_LIMIT', rss)
    if time.perf_counter()-START > 1680 or time.time() >= DEADLINE:
        raise TimeoutError('Frozen main runtime/deadline limit; preserve partial outputs, no replacement seeds')


def deep_size(obj, seen=None):
    if seen is None:
        seen=set()
    if id(obj) in seen:
        return 0
    seen.add(id(obj))
    result=sys.getsizeof(obj)
    if isinstance(obj, dict):
        return result+sum(deep_size(k,seen)+deep_size(v,seen) for k,v in obj.items())
    if isinstance(obj, (list,tuple)):
        return result+sum(deep_size(v,seen) for v in obj)
    return result


def make_teacher(seed):
    rng = random.Random(seed)
    sign=lambda: 2*rng.randrange(2)-1
    tw=[[sign() for _ in range(20)] for _ in range(100)]
    tb=[sign() for _ in range(100)]
    tv,ob=[sign() for _ in range(100)],sign()
    contexts=[[rng.randrange(2) for _ in range(15)] for _ in range(101)]
    fast=[rng.randrange(32) for _ in range(1_010_000)]
    labels=[]
    for c in contexts:
        table=[]
        for f in range(32):
            x=c+[(f>>k)&1 for k in range(5)]
            value=original.teacher_integer(x,tw,tb,tv,ob)
            assert value==original.teacher_float(x,tw,tb,tv,ob)
            table.append(value)
        labels.append(table)
    theta=[]
    for _ in range(5):
        theta.extend(rng.uniform(-math.sqrt(.3),math.sqrt(.3)) for _ in range(20))
        theta.append(0.)
    theta.extend(rng.uniform(-math.sqrt(.6),math.sqrt(.6)) for _ in range(5)); theta.append(0.)
    result=dict(seed=seed,teacher_weights=tw,teacher_bias=tb,teacher_out_weights=tv,teacher_out_bias=ob,
                contexts=contexts,fast_indices=fast,targets_by_context=labels,initial_learner=theta)
    return result


def summaries(matrix,bins,online_sum):
    initial=[matrix[t][t] for t in range(100)]
    first=[bins[t*10] for t in range(100)]
    ages={}
    for lo,hi in [(1,9),(10,49),(50,99)]:
        entries=[(matrix[k][j],initial[j]) for k in range(100) for j in range(k) if lo<=k-j<=hi]
        ages[str(lo)+'-'+str(hi)]=dict(mean_old_risk=math.fsum(a for a,b in entries)/len(entries),
                                        mean_change_from_initial=math.fsum(a-b for a,b in entries)/len(entries),
                                        cells=len(entries))
    return dict(acquisition_first1000_all_tasks=math.fsum(first)/100,
                acquisition_first1000_tasks10to99=math.fsum(first[10:])/90,
                acquisition_all_examples=online_sum/N,
                time_average_all_old_risk=math.fsum(math.fsum(row[:-1])/len(row[:-1]) for row in matrix[1:])/99,
                final_all_old_risk=math.fsum(matrix[-1][:-1])/99,
                mean_initial_competence=math.fsum(initial)/100,
                final_old_change_from_initial=math.fsum(matrix[-1][j]-initial[j] for j in range(99))/99,
                final_current_risk=matrix[-1][-1],initial_competence_by_task=initial,retention_by_age=ages)


def deployment_storage(arm,reservoir,sampling,insertion,replay):
    state=dict(theta=arm.theta,configuration=dict(method=arm.method,step=arm.step,rate=arm.rate,
                                               decay=arm.decay,maturity=arm.maturity),
               gradient_steps=arm.gradient_steps)
    if isinstance(arm,OrderLearner):
        state.update(util=arm.util,mean=arm.mean,butil=arm.butil,ages=arm.ages,
                     accumulated=arm.accumulated,replacements=arm.replacements,
                     compensate=arm.compensate,renewal_rng=arm.rng.getstate(),event_rng=arm.event_rng.getstate())
    if replay:
        state.update(reservoir=reservoir.items,reservoir_seen=reservoir.seen,
                     sampling_rng=sampling.getstate(),insertion_rng=insertion.getstate())
    payload=pickle.dumps(state,protocol=4)
    return dict(actual_pickle4_state_bytes=len(payload),actual_deep_python_state_bytes=deep_size(state),
                storage_convention='full deployed mutable model/method RNG/replay RNG/reservoir; diagnostic logs/teacher/scorer excluded',
                pickle4_sha256=hashlib.sha256(payload).hexdigest())


def one_teacher(seed):
    begin=time.perf_counter()
    data=make_teacher(seed)
    raw=json.dumps(data,separators=(',', ':')).encode()
    (ROOT/f'REALIZATION_{seed}.json').write_bytes(raw)
    raw_sha=hashlib.sha256(raw).hexdigest()
    raw_bytes=len(raw)
    del raw
    keys=[[pack_input(c,f) for f in range(32)] for c in data['contexts'][:100]]
    labels=data['targets_by_context'][:100]
    arms={}
    for name in NAMES[:-1]:
        if name=='sgd_replay':
            arms[name]=Learner(data['initial_learner'],method='sgd',seed=seed+1000)
        else:
            arms[name]=OrderLearner(data['initial_learner'],method='random' if name.startswith('random') else 'cbp',
                                    seed=seed+1000,compensate='_mean' in name)
    cache=ExactCache(677)
    reservoir=Reservoir(506)
    sampling=random.Random(seed+2000); insertion=random.Random(seed+3000)
    matrices={n:[] for n in NAMES}; snapshots={n:[] for n in arms}
    bins={n:[] for n in NAMES}; bin_sums={n:0. for n in NAMES}; online_sums={n:0. for n in NAMES}
    timers={n:0. for n in NAMES}; timers['scoring']=timers['replay_feed']=0.
    initial_before={n:support_risk(arm.theta,keys[0],labels[0]) for n,arm in arms.items()}
    initial_before['cache']=cache_risk(cache,keys[0],labels[0])
    for i in range(N):
        if i%1000==0:
            check_limits()
        task=i//10000
        f=data['fast_indices'][i]; key,target=keys[task][f],labels[task][f]
        tick=time.perf_counter()
        replay=reservoir.items[sampling.randrange(len(reservoir.items))] if reservoir.items else None
        draw=insertion.randrange(i+1)
        timers['replay_feed']+=time.perf_counter()-tick
        for name,arm in arms.items():
            tick=time.perf_counter()
            loss=arm.learn(key,target)
            if replay is not None and name.endswith('_replay'):
                assert math.isfinite(arm.learn(*replay)),('nonfinite replay',seed,name,i)
            timers[name]+=time.perf_counter()-tick
            assert math.isfinite(loss),('nonfinite current',seed,name,i)
            bin_sums[name]+=loss; online_sums[name]+=loss
        tick=time.perf_counter()
        loss=(cache.predict(key)-target)**2
        cache.observe(key,target)
        timers['cache']+=time.perf_counter()-tick
        bin_sums['cache']+=loss; online_sums['cache']+=loss
        reservoir.insert((key,target),draw)
        if (i+1)%1000==0:
            for name in NAMES:
                bins[name].append(bin_sums[name]/1000); bin_sums[name]=0.
        if (i+1)%10000==0:
            tick=time.perf_counter()
            for name,arm in arms.items():
                assert all(math.isfinite(v) for v in arm.theta)
                snapshots[name].append(arm.theta[:])
                matrices[name].append([support_risk(arm.theta,keys[t],labels[t]) for t in range(task+1)])
            cache_before=(cache.count,cache.total,cache.hits,list(cache.keys),list(cache.labels))
            matrices['cache'].append([cache_risk(cache,keys[t],labels[t]) for t in range(task+1)])
            assert cache_before==(cache.count,cache.total,cache.hits,list(cache.keys),list(cache.labels))
            timers['scoring']+=time.perf_counter()-tick
            if (task+1)%25==0:
                log(dict(seed=seed,task=task,teacher_seconds=time.perf_counter()-begin,
                         main_seconds=time.perf_counter()-START,rss=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss))
    cache_state=dict(keys=cache.keys,labels=cache.labels,count=cache.count,total=cache.total,hits=cache.hits,
                     capacity=cache.capacity)
    storage={name:deployment_storage(arm,reservoir,sampling,insertion,name.endswith('_replay'))
             for name,arm in arms.items()}
    payload=pickle.dumps(cache_state,protocol=4)
    storage['cache']=dict(actual_pickle4_state_bytes=len(payload),actual_deep_python_state_bytes=deep_size(cache_state),
                          packed_array_objects_bytes=sys.getsizeof(cache.keys)+sys.getsizeof(cache.labels),
                          packed_payload_bytes=len(cache.keys)*6,pickle4_sha256=hashlib.sha256(payload).hexdigest(),
                          storage_convention='full mutable cache state, including capacity/counters/fallback; no RNG')
    mean=math.fsum(y for row in labels for y in row)/3200
    variance=math.fsum((y-mean)**2 for row in labels for y in row)/3200
    result=dict(seed=seed,status='PASS',utc=time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),
                source_equations_not_author_torch=True,realization_sha256=raw_sha,realization_bytes=raw_bytes,
                teacher_exact_reference_checks=3232,generated_examples=1_010_000,current_examples=N,
                steps={n:a.gradient_steps for n,a in arms.items()},
                replacements={n:a.replacements for n,a in arms.items() if isinstance(a,OrderLearner)},
                compensation={n:dict(sum=a.compensation_sum,abs_sum=a.compensation_abs_sum,square_sum=a.compensation_square_sum)
                              for n,a in arms.items() if isinstance(a,OrderLearner)},
                sampled_events={n:a.sampled_events for n,a in arms.items() if isinstance(a,OrderLearner)},
                teacher_mean=mean,teacher_variance=variance,initial_before=initial_before,
                summaries={n:summaries(matrices[n],bins[n],online_sums[n]) for n in NAMES},
                risk_matrices=matrices,learner_snapshots=snapshots,online_1000_bins=bins,
                cache_final=dict(keys=list(cache.keys),labels=list(cache.labels),count=cache.count,total=cache.total,hits=cache.hits),
                reservoir_final=reservoir.items,storage=storage,seconds_by_activity=timers,
                total_seconds=time.perf_counter()-begin,max_rss_bytes_macos=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
                exposure='all generated parameter/input/label/unused blocks and all learner/scorer/diagnostic outputs consumed')
    encoded=json.dumps(result,separators=(',',':')).encode()
    (ROOT/f'OUTPUT_{seed}.json').write_bytes(encoded)
    compact={k:v for k,v in result.items() if k not in ['risk_matrices','learner_snapshots','online_1000_bins',
                                                       'cache_final','reservoir_final','sampled_events']}
    compact.update(output_bytes=len(encoded),output_sha256=hashlib.sha256(encoded).hexdigest())
    (ROOT/f'SUMMARY_{seed}.json').write_text(json.dumps(compact,indent=2)+'\n')
    log(dict(completed_seed=seed,teacher_seconds=compact['total_seconds'],main_seconds=time.perf_counter()-START,
             replacements=result['replacements'],cache_hits=cache.hits))
    return {k:v for k,v in compact.items() if k!='summaries'}


def main():
    global START
    START=time.perf_counter()
    assert time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime(DEADLINE))=='2026-11-03T03:33:20Z'
    freeze=(ROOT/'FREEZE.md').read_bytes()
    sources={}
    for path in [ROOT/'run.py',ROOT/'engine.py',ROOT/'reference.py',
                 ROOT.parent/'plasticity-retention-protocol-calibration-2026-11-02'/'engine.py',PREVIOUS/'feasibility.py']:
        content=path.read_bytes(); sources[str(path.relative_to(ROOT.parent))]=dict(sha256=hashlib.sha256(content).hexdigest(),bytes=len(content))
    receipt=dict(utc=time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),seeds=SEEDS,
                 freeze_sha256=hashlib.sha256(freeze).hexdigest(),code=sources,
                 freeze_before_any_new_teacher=True,planned_teachers=8)
    (ROOT/'EXECUTION_RECEIPT.json').write_text(json.dumps(receipt,indent=2)+'\n')
    completed=[]
    for seed in SEEDS:
        check_limits()
        completed.append(one_teacher(seed))
        status=dict(status='RUNNING' if len(completed)<8 else 'PASS',completed=completed,
                    planned_seeds=SEEDS,main_seconds=time.perf_counter()-START,
                    max_rss_bytes_macos=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
                    cpu_seconds=resource.getrusage(resource.RUSAGE_SELF).ru_utime+resource.getrusage(resource.RUSAGE_SELF).ru_stime)
        (ROOT/'RUN_STATUS.json').write_text(json.dumps(status,indent=2)+'\n')
    log(dict(status='PASS',teachers=8,main_seconds=time.perf_counter()-START,
             rss=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss))


if __name__=='__main__':
    try:
        main()
    except BaseException:
        (ROOT/'RUN_FAILURE.txt').write_text(traceback.format_exc())
        log(dict(status='FAILED_OR_PARTIAL',main_seconds=None if START is None else time.perf_counter()-START,
                 rss=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss))
        raise
