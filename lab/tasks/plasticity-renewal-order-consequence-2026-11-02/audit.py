"""Independent scalar output/teacher/risk audit and frozen teacher-level inference."""
import hashlib
import json
import math
from pathlib import Path
import resource
import time
import traceback

ROOT=Path(__file__).resolve().parent
T_CRIT=2.364624251
NAMES=['cbp_literal','cbp_mean','cbp_literal_replay','cbp_mean_replay',
       'random_literal_replay','random_mean_replay','sgd_replay','cache']
START=None
PRIOR_SECONDS=0.


def limit():
    if PRIOR_SECONDS+time.perf_counter()-START > 1785:
        raise TimeoutError('Cumulative scientific runtime limit: audit incomplete, no rerun')
    assert resource.getrusage(resource.RUSAGE_SELF).ru_maxrss<1_000_000_000


def prediction(w,key):
    x=[(key//(2**k))%2 for k in range(20)]
    h=[max(0.,math.fsum(w[j*21+k]*x[k] for k in range(20))+w[j*21+20]) for j in range(5)]
    return math.fsum([w[110]]+[w[105+j]*h[j] for j in range(5)])


def teacher(data,key):
    x=[(key//(2**k))%2 for k in range(20)]
    response=data['teacher_out_bias']
    for w,b,v in zip(data['teacher_weights'],data['teacher_bias'],data['teacher_out_weights']):
        threshold=147-5*(20-sum(w)+b)
        if 10*(sum(a*z for a,z in zip(w,x))+b)>threshold:
            response+=v
    return response


def mean(xs):
    return math.fsum(xs)/len(xs)


def interval(xs):
    avg=mean(xs)
    se=math.sqrt(math.fsum((v-avg)**2 for v in xs)/(len(xs)-1)/len(xs))
    return dict(mean=avg,se=se,lower=avg-T_CRIT*se,upper=avg+T_CRIT*se,
                unit='whole teacher/stream',n=len(xs),method='paired teacher t7, model-based small-sample95%; coverage not certified')


def implemented_discrimination():
    from engine import OrderLearner
    observations=[]
    for activity in [0.,1.5]:
        theta=[.1]*111
        theta[84:104]=[0.]*20
        theta[104]=activity
        theta[109]=.2
        theta[110]=.7
        for compensate in [False,True]:
            arm=OrderLearner(theta,method='random',replacement_rate=.2,compensate=compensate)
            arm.ages=[20]*5
            arm.mean=[0.]*4+[activity*(1-.99**20)]
            chosen=arm.renew([0.]*4+[activity],draw=0.,new_incoming={j:[.1]*20 for j in range(5)},
                             random_scores=[5.,4.,3.,2.,1.])
            assert chosen==[4]
            deltas=[prediction(arm.theta,key)-prediction(theta,key) for key in [0,31,(1<<20)-1]]
            expected=0. if compensate else -.2*activity
            assert max(abs(v-expected) for v in deltas)<1e-12
            observations.append(dict(activity=activity,compensate=compensate,
                                     independent_prediction_changes=deltas,expected_change=expected,
                                     squared_change=mean([v*v for v in deltas])))
    return observations


def compare(summaries,base,alt):
    metrics=['time_average_all_old_risk','final_all_old_risk','acquisition_first1000_all_tasks']
    rows=[]
    for seed,summary in summaries.items():
        b,a=summary[base],summary[alt]
        assert all(b[m]>0 for m in metrics)
        rows.append(dict(seed=seed,average_gain=(b[metrics[0]]-a[metrics[0]])/b[metrics[0]],
                         terminal_gain=(b[metrics[1]]-a[metrics[1]])/b[metrics[1]],
                         acquisition_cost=(a[metrics[2]]-b[metrics[2]])/b[metrics[2]]))
    ci={m:interval([r[m] for r in rows]) for m in ['average_gain','terminal_gain','acquisition_cost']}
    successes=sum(r['average_gain']>=.10 and r['terminal_gain']>=.10 and r['acquisition_cost']<=.02 for r in rows)
    passed=ci['average_gain']['lower']>.10 and ci['terminal_gain']['lower']>.10 and ci['acquisition_cost']['upper']<.02
    return dict(baseline=base,alternative=alt,effects_by_teacher=rows,intervals=ci,
                material_joint_gate_pass=passed,teacher_joint_successes=successes,
                exact_one_sided95_upper_success_prevalence_if_zero=(1-.05**(1/len(rows))) if successes==0 else None)


def main():
    global START,PRIOR_SECONDS
    START=time.perf_counter()
    raw=(ROOT/'RUN_STATUS.json').read_bytes(); status=json.loads(raw)
    assert status['status']=='PASS' and len(status['completed'])==8
    reference=json.loads((ROOT/'REFERENCE.json').read_bytes())
    PRIOR_SECONDS=status['main_seconds']+reference['seconds']+5.  # conservative other short process allowance
    receipt=json.loads((ROOT/'EXECUTION_RECEIPT.json').read_bytes())
    assert hashlib.sha256((ROOT/'FREEZE.md').read_bytes()).hexdigest()==receipt['freeze_sha256']
    source_checks=[]
    for relative,expected in receipt['code'].items():
        content=(ROOT.parent/relative).read_bytes()
        assert hashlib.sha256(content).hexdigest()==expected['sha256']
        source_checks.append(relative)
    read_bytes=len(raw)
    checks=[]; summaries={}; matrices={}; stores={}; timers={}; methods={}
    max_risk_gap=0.; prediction_count=0; label_count=0; sampled_events=0; event_gap=0.
    discrimination=implemented_discrimination()
    for seed in range(240001,240009):
        limit()
        paths=[ROOT/f'REALIZATION_{seed}.json',ROOT/f'OUTPUT_{seed}.json',ROOT/f'SUMMARY_{seed}.json']
        raws=[p.read_bytes() for p in paths]
        read_bytes+=sum(len(v) for v in raws)
        data,out,summary=[json.loads(v) for v in raws]
        assert hashlib.sha256(raws[0]).hexdigest()==out['realization_sha256']
        assert hashlib.sha256(raws[1]).hexdigest()==summary['output_sha256']
        supports=[]
        for c in data['contexts']:
            low=sum(bit*2**j for j,bit in enumerate(c))
            supports.append([low+f*2**15 for f in range(32)])
        for row,keys in zip(data['targets_by_context'],supports):
            assert row==[teacher(data,k) for k in keys]
            label_count+=32
        cache=dict(zip(out['cache_final']['keys'],out['cache_final']['labels']))
        fallback=out['cache_final']['total']/out['cache_final']['count']
        independent={}
        for name in NAMES:
            rebuilt=[]
            for t,row in enumerate(out['risk_matrices'][name]):
                limit()
                if name!='cache':
                    weights=out['learner_snapshots'][name][t]
                    values=[]
                    for j in range(t+1):
                        predictions=[prediction(weights,k) for k in supports[j]]
                        prediction_count+=32
                        risk=mean([(p-y)**2 for p,y in zip(predictions,data['targets_by_context'][j])])
                        max_risk_gap=max(max_risk_gap,abs(risk-row[j]))
                        assert abs(risk-row[j])<1e-10,(seed,name,t,j,risk,row[j])
                        values.append(risk)
                    rebuilt.append(values)
                else:
                    # Every cache boundary is not checkpointed: only final predictions independently replayable here.
                    rebuilt.append(row[:])
            if name=='cache':
                for j in range(100):
                    risk=mean([(cache.get(k,fallback)-y)**2 for k,y in zip(supports[j],data['targets_by_context'][j])])
                    assert risk==rebuilt[-1][j]
            initial=[rebuilt[t][t] for t in range(100)]
            pooled_boundary_average=mean([mean(rebuilt[t][:t]) for t in range(1,100)])
            terminal=mean(rebuilt[99][:99])
            acquisition=mean([out['online_1000_bins'][name][10*t] for t in range(100)])
            expected=out['summaries'][name]
            assert abs(pooled_boundary_average-expected['time_average_all_old_risk'])<1e-10
            assert abs(terminal-expected['final_all_old_risk'])<1e-10
            assert abs(acquisition-expected['acquisition_first1000_all_tasks'])<1e-12
            assert abs(mean(initial)-expected['mean_initial_competence'])<1e-10
            for lo,hi in [(1,9),(10,49),(50,99)]:
                risks=[]; changes=[]
                for age in range(lo,hi+1):
                    for old in range(100-age):
                        r=rebuilt[old+age][old]
                        risks.append(r); changes.append(r-initial[old])
                observed=expected['retention_by_age'][str(lo)+'-'+str(hi)]
                assert abs(mean(risks)-observed['mean_old_risk'])<1e-10
                assert abs(mean(changes)-observed['mean_change_from_initial'])<1e-10
                assert len(risks)==observed['cells']
            if name!='cache':
                first=mean([(prediction(data['initial_learner'],k)-y)**2 for k,y in zip(supports[0],data['targets_by_context'][0])])
                assert abs(first-out['initial_before'][name])<1e-10
            independent[name]=dict(time_average_all_old_risk=pooled_boundary_average,
                                   final_all_old_risk=terminal,acquisition_first1000_all_tasks=acquisition)
        for name,events in out['sampled_events'].items():
            for event in events:
                sampled_events+=1
                before,after=event['before'],event['after']
                addition=math.fsum(before[105+j]*m for j,m in zip(event['chosen'],event['old_means'])) if event['compensate'] else 0.
                assert abs(after[110]-before[110]-addition)<1e-12
                for key in [event['key'],0,(1<<20)-1]:
                    if key is None:
                        continue
                    x=[(key>>k)&1 for k in range(20)]
                    removed=math.fsum(before[105+j]*max(0.,math.fsum(before[j*21+k]*x[k] for k in range(20))+before[j*21+20]) for j in event['chosen'])
                    gap=abs(prediction(after,key)-prediction(before,key)-(addition-removed))
                    event_gap=max(event_gap,gap)
                    assert gap<1e-11
        for name,steps in out['steps'].items():
            assert steps==(1_999_999 if name.endswith('_replay') else 1_000_000)
        assert out['cache_final']['count']==1_000_000
        summaries[str(seed)]=out['summaries']; matrices[str(seed)]=independent
        stores[str(seed)]=out['storage']; timers[str(seed)]=out['seconds_by_activity']
        methods[str(seed)]=dict(steps=out['steps'],replacements=out['replacements'],compensation=out['compensation'],cache_hits=out['cache_final']['hits'])
        checks.append(dict(seed=seed,risk_and_age_summaries=True,all_neural_boundaries_rebuilt=True,
                           cache_final_rebuilt=True,cache_earlier_boundaries_inherited=True,
                           distinct_training_contexts=len(set(tuple(c) for c in data['contexts'][:100])),
                           generated_contexts=len(data['contexts']),
                           realization_sha256=out['realization_sha256'],output_sha256=summary['output_sha256']))
        print(json.dumps(dict(audited_seed=seed,seconds=time.perf_counter()-START)),flush=True)
    comparisons={
        'current_only_order':compare(summaries,'cbp_literal','cbp_mean'),
        'replay_order':compare(summaries,'cbp_literal_replay','cbp_mean_replay'),
        'random_order':compare(summaries,'random_literal_replay','random_mean_replay')}
    for baseline in ['sgd_replay','random_literal_replay','random_mean_replay','cache']:
        comparisons['replay_mean_vs_'+baseline]=compare(summaries,baseline,'cbp_mean_replay')
    aggregate={name:{m:interval([s[name][m] for s in summaries.values()]) for m in
                         ['acquisition_first1000_all_tasks','time_average_all_old_risk','final_all_old_risk','mean_initial_competence',
                          'acquisition_first1000_tasks10to99','acquisition_all_examples','final_old_change_from_initial']}
               for name in NAMES}
    result=dict(status='PASS',utc=time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),
                teachers=8,teacher_units=list(summaries),independent_label_checks=label_count,
                independently_rebuilt_neural_predictions=prediction_count,max_risk_gap=max_risk_gap,
                sampled_renewal_events=sampled_events,event_function_identity_max_gap=event_gap,
                implemented_constant_and_dead_feature_discrimination=discrimination,
                checks=checks,code_and_freeze_pins_pass=source_checks,
                cache_scope='final cache predictions reconstructed; previous-boundary cache risks inherited and algebraically checked',
                comparisons=comparisons,aggregate=aggregate,all_teacher_summaries=summaries,
                storage_by_teacher=stores,timers_by_teacher=timers,method_counts_by_teacher=methods,
                actual_explicit_file_read_bytes=read_bytes,
                conservative_read_hash_decode_charge_bytes=3*read_bytes,
                seconds=time.perf_counter()-START,
                cumulative_science_seconds_including_5s_short_process_allowance=PRIOR_SECONDS+time.perf_counter()-START,
                cpu_seconds=resource.getrusage(resource.RUSAGE_SELF).ru_utime+resource.getrusage(resource.RUSAGE_SELF).ru_stime,
                max_rss_bytes_macos=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
                independent_scientific_review=False,
                uncertainty_limit='eight whole teachers/model-based t intervals; no calibration/normality/coverage or biological claim')
    (ROOT/'AUDIT.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k not in ['comparisons','aggregate','all_teacher_summaries','storage_by_teacher','timers_by_teacher','method_counts_by_teacher']}),flush=True)


if __name__=='__main__':
    try:
        main()
    except BaseException:
        (ROOT/'AUDIT_FAILURE.txt').write_text(traceback.format_exc())
        raise
