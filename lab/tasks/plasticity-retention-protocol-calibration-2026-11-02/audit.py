"""Saved-output reconstruction, no neural full-stream learning rerun."""
import hashlib
import json
import math
from pathlib import Path
import pickle
import resource
import time
import traceback

from engine import Learner, pack_input
from references import scalar_prediction

ROOT=Path(__file__).resolve().parent
PREVIOUS=ROOT.parent/'plasticity-retention-source-benchmark-2026-11-02'


def main():
    started=time.perf_counter()
    raw=(PREVIOUS/'FULL_REALIZATION.json').read_bytes()
    data=json.loads(raw)
    saved_bytes=(ROOT/'FULL_STREAM.json').read_bytes()
    result=json.loads(saved_bytes)
    summary=json.loads((ROOT/'FULL_SUMMARY.json').read_text())
    assert hashlib.sha256(raw).hexdigest()==result['input_sha256']
    assert hashlib.sha256(saved_bytes).hexdigest()==summary['full_output_sha256']
    maximum=0.
    predictions=0
    for name in ('sgd','cbp'):
        for last,theta in enumerate(result['learner_snapshots'][name]):
            for old in range(last+1):
                terms=[]
                for fast in range(32):
                    key=pack_input(data['contexts'][old],fast)
                    pred=scalar_prediction(theta,key)[0]
                    terms.append((pred-data['targets_by_context'][old][fast])**2)
                    predictions+=1
                independent=math.fsum(terms)/32
                gap=abs(independent-result['risk_matrices'][name][last][old])
                maximum=max(maximum,gap)
                assert gap<1e-11,(name,last,old,gap)
    metrics={}
    for name in ('sgd','cbp','cache'):
        matrix=result['risk_matrices'][name]
        acquisition=math.fsum(result['online_1000_bins'][name][::10])/100
        average=math.fsum(math.fsum(row[:-1])/(len(row)-1) for row in matrix[1:])/99
        final=math.fsum(matrix[-1][:-1])/99
        assert abs(acquisition-result['summaries'][name]['acquisition_first1000_all_tasks'])<1e-13
        assert abs(average-result['summaries'][name]['time_average_all_old_risk'])<1e-13
        assert abs(final-result['summaries'][name]['final_all_old_risk'])<1e-13
        metrics[name]=dict(acquisition=acquisition,average_all_old=average,final_all_old=final)
    # Final cache scorer independently reconstructed from exact saved keys and
    # the actually observed, not uniform-support, global fallback mean.
    total=math.fsum(data['targets_by_context'][i//10000][f]
                    for i,f in enumerate(data['fast_indices'][:1_000_000]))
    fallback=total/1_000_000
    cache=dict(zip(result['cache_final_keys'],result['cache_final_labels']))
    cache_maximum=0.
    for task in range(100):
        independent=math.fsum((cache.get(pack_input(data['contexts'][task],f),fallback)
                               -data['targets_by_context'][task][f])**2 for f in range(32))/32
        gap=abs(independent-result['risk_matrices']['cache'][-1][task])
        cache_maximum=max(cache_maximum,gap)
        assert gap<1e-12
    unique_keys={pack_input(data['contexts'][i],f) for i in range(100) for f in range(32)}
    assert len(unique_keys)==3200
    assert result['cache_online_hits']==1_000_000-len(unique_keys)
    # An unresolved cost: source-style Gaussian perturbation of all111params.
    # Time ONLY20,000gradient steps on the already consumed first10kexamples;
    # no new rate/seed/full-stream campaign and no effect selection.
    timing=Learner(data['initial_learner'],method='snp',weight_decay=.01,perturb=1e-4)
    then=time.perf_counter()
    for i in range(10000):
        f=data['fast_indices'][i]
        key=pack_input(data['contexts'][0],f)
        y=data['targets_by_context'][0][f]
        a=timing.learn(key,y)
        b=timing.learn(key,y)  # same input: timing only, not a replay effect
        assert math.isfinite(a) and math.isfinite(b)
    snp_seconds=time.perf_counter()-then
    # MT state is real method storage, outside the declared random-tape/core
    # state comparison. Do not disguise pickle size as minimal physical state.
    rng_serialized={name:len(pickle.dumps(getattr(timing,name).getstate(),protocol=4))
                    for name in ('rng','event_rng')}
    output=dict(status='PASS',utc=time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),
                independent_full_neural_predictions=predictions,
                maximum_full_risk_gap=maximum,cache_final_risk_maximum_gap=cache_maximum,
                reconstructed_metrics=metrics,unique_original_training_support_keys=len(unique_keys),
                exact_cache_misses=1_000_000-result['cache_online_hits'],
                snp_prefix_gradient_steps=timing.gradient_steps,snp_prefix_seconds=snp_seconds,
                snp_linear_2M_step_price_seconds=snp_seconds*100,
                snp_price_status='EXTRAPOLATION of measured20ksteps, not measured fullSNP',
                serialized_rng_states_bytes=rng_serialized,
                random_tape_core_budget_is_not_total_method_or_process_memory=True,
                explicit_read_hash_decode_allowance_bytes=3*(len(raw)+len(saved_bytes)),
                seconds=time.perf_counter()-started,
                max_rss_bytes_macos=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
                new_science_exposure='consumed seed1729only; all saved risks reconstructed; no main holdout')
    (ROOT/'AUDIT.json').write_text(json.dumps(output,indent=2)+'\n')
    print(json.dumps(output))


if __name__=='__main__':
    try:
        main()
    except BaseException:
        (ROOT/'AUDIT_FAILURE.txt').write_text(traceback.format_exc())
        raise
