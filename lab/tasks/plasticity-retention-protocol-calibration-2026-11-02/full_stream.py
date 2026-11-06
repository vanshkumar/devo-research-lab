"""ONE original full consumed stream: feasibility pair and bounded-cache cost."""
import hashlib
import json
import math
from pathlib import Path
import random
import resource
import sys
import time
import traceback

from engine import ExactCache, Learner, Reservoir, cache_risk, pack_input, support_risk

ROOT=Path(__file__).resolve().parent
PREVIOUS=ROOT.parent/'plasticity-retention-source-benchmark-2026-11-02'
N=1_000_000


def main():
    t0=time.perf_counter()
    raw=(PREVIOUS/'FULL_REALIZATION.json').read_bytes()
    source_sha=hashlib.sha256(raw).hexdigest()
    data=json.loads(raw)
    assert len(data['fast_indices'])>=N
    assert len(data['initial_learner'])==111
    assert data['seed']==1729
    keys=[[pack_input(c,f) for f in range(32)] for c in data['contexts'][:100]]
    labels=data['targets_by_context'][:100]
    mean_y=math.fsum(y for table in labels for y in table)/3200
    variance=math.fsum((y-mean_y)**2 for table in labels for y in table)/3200
    assert variance>0
    arms={name:Learner(data['initial_learner'],method=name,seed=781)
          for name in ('sgd','cbp')}
    cache=ExactCache(677)
    reservoir=Reservoir(506)
    sampling_rng=random.Random(1181)
    insertion_rng=random.Random(1867)
    timers={name:0. for name in ('sgd','cbp','cache','all_support_scoring','replay_feeds')}
    matrices={name:[] for name in ('sgd','cbp','cache')}
    snapshots={name:[] for name in arms}
    bins={name:[] for name in ('sgd','cbp','cache')}
    bin_sum={name:0. for name in bins}
    initial_before={name:support_risk(arm.theta,keys[0],labels[0]) for name,arm in arms.items()}
    for i in range(N):
        task=i//10000
        fast=data['fast_indices'][i]
        key,target=keys[task][fast],labels[task][fast]
        then=time.perf_counter()
        replay=(reservoir.items[sampling_rng.randrange(len(reservoir.items))]
                if reservoir.items else None)
        insertion=insertion_rng.randrange(i+1)
        timers['replay_feeds']+=time.perf_counter()-then
        for name,arm in arms.items():
            then=time.perf_counter()
            current_loss=arm.learn(key,target)
            if replay is not None:
                replay_loss=arm.learn(*replay)
                if not math.isfinite(replay_loss):
                    raise FloatingPointError(('nonfinite replay',name,i))
            timers[name]+=time.perf_counter()-then
            if not math.isfinite(current_loss):
                raise FloatingPointError(('nonfinite current',name,i))
            bin_sum[name]+=current_loss
        then=time.perf_counter()
        cache_prediction=cache.predict(key)
        bin_sum['cache']+=(cache_prediction-target)**2
        cache.observe(key,target)
        timers['cache']+=time.perf_counter()-then
        reservoir.insert((key,target),insertion)
        if (i+1)%1000==0:
            for name in bins:
                bins[name].append(bin_sum[name]/1000)
                bin_sum[name]=0.
        if (i+1)%10000==0:
            then=time.perf_counter()
            for name,arm in arms.items():
                assert all(math.isfinite(v) for v in arm.theta)
                matrices[name].append([support_risk(arm.theta,keys[t],labels[t]) for t in range(task+1)])
                snapshots[name].append(arm.theta[:])
            before_cache=(cache.count,cache.total,cache.hits,list(cache.keys),list(cache.labels))
            matrices['cache'].append([cache_risk(cache,keys[t],labels[t]) for t in range(task+1)])
            assert before_cache==(cache.count,cache.total,cache.hits,list(cache.keys),list(cache.labels))
            timers['all_support_scoring']+=time.perf_counter()-then
            if (task+1)%10==0:
                print(json.dumps(dict(task=task,elapsed=time.perf_counter()-t0,
                                      cbp_replacements=arms['cbp'].replacements,
                                      rss=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)),flush=True)
    summaries={}
    for name,matrix in matrices.items():
        initial=[matrix[t][t] for t in range(100)]
        first_bins=[bins[name][t*10] for t in range(100)]
        last_old=matrix[-1][:-1]
        old_time_risk=math.fsum(math.fsum(row[:-1])/len(row[:-1]) for row in matrix[1:])/99
        by_age={}
        for lo,hi in [(1,9),(10,49),(50,99)]:
            values=[matrix[k][j] for k in range(100) for j in range(k) if lo<=k-j<=hi]
            degradation=[matrix[k][j]-initial[j] for k in range(100) for j in range(k) if lo<=k-j<=hi]
            by_age[str(lo)+'-'+str(hi)]={'mean_old_risk':math.fsum(values)/len(values),
                                        'mean_change_from_initial':math.fsum(degradation)/len(degradation),
                                        'cells':len(values)}
        summaries[name]=dict(acquisition_first1000_all_tasks=math.fsum(first_bins)/100,
                             acquisition_first1000_tasks10to99=math.fsum(first_bins[10:])/90,
                             acquisition_normalized_tasks10to99=math.fsum(first_bins[10:])/90/variance,
                             final_all_old_risk=math.fsum(last_old)/99,
                             time_average_all_old_risk=old_time_risk,
                             normalized_time_average_all_old_risk=old_time_risk/variance,
                             mean_initial_competence=math.fsum(initial)/100,
                             final_current_risk=matrix[-1][-1],
                             final_old_change_from_initial=math.fsum(r-s for r,s in zip(last_old,initial[:-1]))/99,
                             retention_by_age=by_age)
    result=dict(status='PASS',utc=time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),
                input_sha256=source_sha,input_bytes=len(raw),steps_current=N,tasks=100,
                steps_per_neural_arm={n:a.gradient_steps for n,a in arms.items()},
                replacements={n:a.replacements for n,a in arms.items()},
                initial_before_first_task=initial_before,
                teacher_support_mean=mean_y,teacher_support_variance=variance,
                configuration=dict(step=.01,decay=.99,effective_maturity=10,
                                   config_declared_maturity=100,replacement_rate=1e-4,
                                   accumulate=False,utility='adaptable_contribution',
                                   reservoir_capacity=506,cache_capacity=677,cache='packed-arrayLRU',
                                   replay='one pre-insertion observed sample per current example'),
                seconds_by_activity=timers,summaries=summaries,
                risk_matrices=matrices,learner_snapshots=snapshots,
                online_1000_bins=bins,cache_final_keys=list(cache.keys),cache_final_labels=list(cache.labels),
                cache_online_hits=cache.hits,cache_observations=cache.count,
                reservoir_final=reservoir.items,
                cache_packed_payload_bytes=len(cache.keys)*4+len(cache.labels)*2,
                cache_array_objects_bytes=sys.getsizeof(cache.keys)+sys.getsizeof(cache.labels),
                exposed='one consumed teacher/stream; all support risks/model endpoints/cache and reservoir; no holdout claim')
    result['seconds_before_serialization']=time.perf_counter()-t0
    result['max_rss_bytes_macos']=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    payload=json.dumps(result,separators=(',',':')).encode()
    (ROOT/'FULL_STREAM.json').write_bytes(payload)
    summary={k:v for k,v in result.items() if k not in ('risk_matrices','learner_snapshots','online_1000_bins',
                                                      'cache_final_keys','cache_final_labels','reservoir_final')}
    summary['full_output_sha256']=hashlib.sha256(payload).hexdigest()
    summary['full_output_bytes']=len(payload)
    summary['total_seconds']=time.perf_counter()-t0
    summary['max_rss_bytes_macos']=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    (ROOT/'FULL_SUMMARY.json').write_text(json.dumps(summary,indent=2)+'\n')
    print(json.dumps(summary),flush=True)


if __name__=='__main__':
    try:
        main()
    except BaseException:
        (ROOT/'FULL_STREAM_FAILURE.txt').write_text(traceback.format_exc())
        raise
