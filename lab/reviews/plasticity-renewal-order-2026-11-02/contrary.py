"""ONE frozen, privileged old-mean causal fork; no author imports or training."""
import hashlib
import json
import math
from pathlib import Path
import resource
import time
import traceback

HERE=Path(__file__).resolve().parent
AUTHOR=HERE.parent.parent/'tasks'/'plasticity-renewal-order-consequence-2026-11-02'
SEEDS=list(range(240001,240009))
ARMS=['cbp_literal','cbp_mean','cbp_literal_replay','cbp_mean_replay',
      'random_literal_replay','random_mean_replay']
READS=[]
START=time.perf_counter()


def read(path):
    assert path.stat().st_size<10_000_000
    raw=path.read_bytes()
    READS.append(dict(path=str(path),bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest()))
    return raw


def target(d,x):
    out=d['teacher_out_bias']
    for w,b,v in zip(d['teacher_weights'],d['teacher_bias'],d['teacher_out_weights']):
        if sum(a*z for a,z in zip(w,x))+b>.7*21-(20-sum(w)+b)/2:
            out+=v
    return out


def components(theta,x):
    return [theta[105+j]*max(0.,theta[21*j+20]+sum(theta[21*j+k]*x[k] for k in range(20))) for j in range(5)]


def interval(values):
    if len(values)!=8 or any(x is None for x in values):
        return dict(mean=None,individual=values,status='unearned zero-denominator/missing teacher')
    avg=math.fsum(values)/8
    se=math.sqrt(math.fsum((v-avg)**2 for v in values)/56)
    return dict(mean=avg,lower=avg-2.364624251*se,upper=avg+2.364624251*se,
                individual=values,status='conditional paired-teacher t7; coverage not calibrated')


def means(events):
    names=['risk_before','risk_literal','risk_ema','risk_oracle',
           'disturbance_literal','disturbance_ema','disturbance_oracle']
    result={k:math.fsum(e[k] for e in events)/len(events) for k in names}
    q,d=result['risk_literal'],result['disturbance_literal']
    result.update(ema_risk_gain=(q-result['risk_ema'])/q if q else None,
                  oracle_risk_gain=(q-result['risk_oracle'])/q if q else None,
                  ema_disturbance_reduction=(d-result['disturbance_ema'])/d if d else None,
                  oracle_disturbance_reduction=(d-result['disturbance_oracle'])/d if d else None,
                  eligible_events=len(events),ema_risk_better_events=sum(e['risk_ema']<e['risk_literal'] for e in events),
                  oracle_risk_better_events=sum(e['risk_oracle']<e['risk_literal'] for e in events),
                  ema_disturbance_better_events=sum(e['disturbance_ema']<e['disturbance_literal'] for e in events),
                  oracle_disturbance_better_events=sum(e['disturbance_oracle']<e['disturbance_literal'] for e in events))
    return result


def main():
    assert not (HERE/'CONTRARY.json').exists(),'refuse outcome overwrite'
    freeze=read(HERE/'CONTRARY_FREEZE.md')
    code=read(Path(__file__))
    receipt=dict(utc_before_evaluation=time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),
                 freeze_sha256=hashlib.sha256(freeze).hexdigest(),code_sha256=hashlib.sha256(code).hexdigest(),
                 source='all saved original teacher/input/event states',seeds=SEEDS,arms=ARMS,
                 new_random_draws=0,new_teachers=0,learning_updates=0)
    (HERE/'CONTRARY_EXECUTION_RECEIPT.json').write_text(json.dumps(receipt,indent=2)+'\n')
    all_events=[]; excluded=[]; teacher_rows=[]; actual_gap=0.; oracle_gap=0.; evaluations=0
    for seed in SEEDS:
        data=json.loads(read(AUTHOR/f'REALIZATION_{seed}.json'))
        saved=json.loads(read(AUTHOR/f'OUTPUT_{seed}.json'))
        inputs=[[c+[(f>>k)&1 for k in range(5)] for f in range(32)] for c in data['contexts'][:100]]
        labels=[[target(data,x) for x in xs] for xs in inputs]
        assert labels==data['targets_by_context'][:100]
        for arm in ARMS:
            rows=[]
            for event_number,e in enumerate(saved['sampled_events'][arm]):
                step=e['gradient_step']; replay=arm.endswith('_replay')
                i=step//2 if replay else step-1
                task=i//10000
                assert 0<=task<100
                key=e['key']; slow=tuple((key>>k)&1 for k in range(15))
                replay_gradient=replay and step>1 and step%2==1
                assert any(slow==tuple(c) for c in data['contexts'][:task+1])
                if not replay_gradient: assert slow==tuple(data['contexts'][task])
                if task==0:
                    excluded.append(dict(seed=seed,arm=arm,event=event_number,gradient_step=step,reason='no earlier task'))
                    continue
                before=e['before']; after=e['after']; chosen=e['chosen']
                delta_e=math.fsum(before[105+j]*mu for j,mu in zip(chosen,e['old_means']))
                values=[]
                for j in range(task):
                    for x,y in zip(inputs[j],labels[j]):
                        parts=components(before,x)
                        f=before[110]+math.fsum(parts)
                        removed=math.fsum(parts[u] for u in chosen)
                        actual=after[110]+math.fsum(components(after,x))
                        predicted=f-removed+(delta_e if e['compensate'] else 0.)
                        actual_gap=max(actual_gap,abs(actual-predicted))
                        values.append((f,y,removed))
                count=len(values); evaluations+=count
                delta_o=math.fsum(r for f,y,r in values)/count
                row=dict(seed=seed,arm=arm,event=event_number,gradient_step=step,task=task,
                         current_example_index=i,replay_gradient=replay_gradient,old_support_points=count,
                         chosen=chosen,ema_shift=delta_e,oracle_shift=delta_o,
                         risk_before=math.fsum((f-y)**2 for f,y,r in values)/count,
                         risk_literal=math.fsum((f-y-r)**2 for f,y,r in values)/count,
                         risk_ema=math.fsum((f-y-r+delta_e)**2 for f,y,r in values)/count,
                         risk_oracle=math.fsum((f-y-r+delta_o)**2 for f,y,r in values)/count,
                         disturbance_literal=math.fsum(r*r for f,y,r in values)/count,
                         disturbance_ema=math.fsum((r-delta_e)**2 for f,y,r in values)/count,
                         disturbance_oracle=math.fsum((r-delta_o)**2 for f,y,r in values)/count)
                assert row['disturbance_oracle']<=min(row['disturbance_literal'],row['disturbance_ema'])+1e-11
                # Independent quadratic check at the exact optimum.
                oracle_gap=max(oracle_gap,abs(row['disturbance_literal']-delta_o**2-row['disturbance_oracle']))
                rows.append(row);all_events.append(row)
            assert rows,(seed,arm,'no eligible saved events')
            teacher_rows.append(dict(seed=seed,arm=arm,**means(rows)))
        print(json.dumps(dict(seed=seed,events=sum(e['seed']==seed for e in all_events),status='PASS')),flush=True)
        assert resource.getrusage(resource.RUSAGE_SELF).ru_maxrss<1_000_000_000
        assert time.perf_counter()-START<600
    assert actual_gap<1e-11 and oracle_gap<1e-11,(actual_gap,oracle_gap)
    summaries={}
    for arm in ARMS:
        ts=[r for r in teacher_rows if r['arm']==arm]
        summary={k:interval([r[k] for r in ts]) for k in ['ema_risk_gain','oracle_risk_gain',
                  'ema_disturbance_reduction','oracle_disturbance_reduction']}
        summary['absolute_teacher_means']={k:math.fsum(r[k] for r in ts)/8 for k in
                  ['risk_before','risk_literal','risk_ema','risk_oracle','disturbance_literal','disturbance_ema','disturbance_oracle']}
        summary['event_count']=sum(r['eligible_events'] for r in ts)
        summaries[arm]=summary
    result=dict(status='PASS',utc=time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),
                receipt=receipt,all_events=all_events,excluded_no_old_task=excluded,
                per_teacher_arm=teacher_rows,summaries=summaries,eligible_events=len(all_events),
                total_saved_events=len(all_events)+len(excluded),old_support_event_evaluations=evaluations,
                maximum_saved_after_prediction_gap=actual_gap,maximum_oracle_quadratic_gap=oracle_gap,
                old_mean_uses_privileged_full_old_inputs=True,target_labels_choose_shift=False,
                learning_replay=False,new_teachers=0,new_draws=0,
                reads=READS,explicit_read_bytes=sum(x['bytes'] for x in READS),
                read_hash_decode_conservative_bytes=3*sum(x['bytes'] for x in READS)+1_000_000,
                seconds=time.perf_counter()-START,peak_rss_bytes_macos=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
                scope='postvalidation fixed-state fork, no replacement main outcome or long-term inference')
    (HERE/'CONTRARY.json').write_text(json.dumps(result,indent=2)+'\n')
    for arm in ARMS:
        print(json.dumps(dict(arm=arm,**summaries[arm])),flush=True)
    print(json.dumps({k:result[k] for k in ['status','utc','seconds','eligible_events','total_saved_events',
          'old_support_event_evaluations','maximum_saved_after_prediction_gap','peak_rss_bytes_macos','explicit_read_bytes']}),flush=True)


if __name__=='__main__':
    try:main()
    except BaseException:
        (HERE/'CONTRARY_FAILURE.txt').write_text(traceback.format_exc())
        (HERE/'CONTRARY_FAILURE_RESOURCES.json').write_text(json.dumps(dict(seconds=time.perf_counter()-START,
            reads=READS,peak_rss_bytes_macos=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss),indent=2))
        raise
