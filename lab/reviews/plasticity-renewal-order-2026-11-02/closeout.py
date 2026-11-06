"""Final artifact/pin/gate comparison and additive resources; no new experiment."""
import hashlib
import json
import math
from pathlib import Path
import resource
import time
import traceback

HERE=Path(__file__).resolve().parent
AUTHOR=HERE.parent.parent/'tasks'/'plasticity-renewal-order-consequence-2026-11-02'
START=time.perf_counter();READS=[]


def raw(path):
    assert path.stat().st_size<10_000_000
    b=path.read_bytes()
    READS.append(dict(path=str(path),bytes=len(b),sha256=hashlib.sha256(b).hexdigest()))
    return b


def load(path):return json.loads(raw(path))


def main():
    r=load(HERE/'RECONSTRUCTION.json'); c=load(HERE/'CONTRARY.json');v=load(HERE/'VERIFICATION.json')
    f=load(HERE/'RECONSTRUCTION_FAILURE_RESOURCES.json')
    a=load(AUTHOR/'AUDIT.json')
    for k in [r,c,v]:assert k['status']=='PASS'
    assert hashlib.sha256(raw(HERE/'reconstruct.py')).hexdigest()==r['own_code_sha256']
    assert hashlib.sha256(raw(HERE/'contrary.py')).hexdigest()==c['receipt']['code_sha256']
    assert hashlib.sha256(raw(HERE/'CONTRARY_FREEZE.md')).hexdigest()==c['receipt']['freeze_sha256']
    read_pins={p['path']:p for p in r['reads']}
    output_pins=[]
    for seed in range(240001,240009):
        s=load(AUTHOR/f'SUMMARY_{seed}.json')
        o=read_pins[f'lab/tasks/plasticity-renewal-order-consequence-2026-11-02/OUTPUT_{seed}.json']
        assert o['sha256']==s['output_sha256'] and o['bytes']==s['output_bytes']
        output_pins.append(dict(seed=seed,output_sha256=o['sha256'],output_bytes=o['bytes']))
    pairs={
       'current_only_order':('cbp_mean','cbp_literal'),
       'replay_order':('cbp_mean_replay','cbp_literal_replay'),
       'random_order':('random_mean_replay','random_literal_replay'),
       'replay_mean_vs_sgd_replay':('cbp_mean_replay','sgd_replay'),
       'replay_mean_vs_random_literal_replay':('cbp_mean_replay','random_literal_replay'),
       'replay_mean_vs_random_mean_replay':('cbp_mean_replay','random_mean_replay'),
       'replay_mean_vs_cache':('cbp_mean_replay','cache')}
    gap=0.;gates=[]
    for name,(alt,base) in pairs.items():
        own=r['comparisons'][alt+' versus '+base];old=a['comparisons'][name]
        for om,am in [('average','average_gain'),('terminal','terminal_gain'),('acquisition_cost','acquisition_cost')]:
            for stat in ['mean','se','lower','upper']:
                diff=abs(own[om][stat]-old['intervals'][am][stat]);gap=max(gap,diff)
                assert diff<1e-12,(name,om,stat,diff)
        assert own['joint_pass']==old['material_joint_gate_pass']
        assert own['teacher_joint_successes']==old['teacher_joint_successes']
        gates.append(dict(name=name,joint_pass=own['joint_pass'],teacher_successes=own['teacher_joint_successes']))
    names=list(r['per_teacher'][0]['scores'])
    aggregate={n:{key:math.fsum(row['scores'][n][key] for row in r['per_teacher'])/8 for key in
                ['acquisition_first1000_all_tasks','time_average_all_old_risk','final_all_old_risk','mean_initial_competence','final_old_change_from_initial']} for n in names}
    source_excerpt_files=[]
    for name in ['PRIOR_PROVIDER_EXCERPTS.txt','PRIOR_PROVIDER_EXPERIMENTS.txt']:
        p=AUTHOR.parent/'plasticity-retention-protocol-calibration-2026-11-02'/name
        b=raw(p);source_excerpt_files.append(dict(path=str(p),bytes=len(b),sha256=hashlib.sha256(b).hexdigest(),
                                                 exposure='full hash/UTF8 decode; bounded relevant primary excerpts interpreted'))
        b.decode('utf-8')
    main_audit=dict(status='PASS',utc=time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),
                    material_comparison_interval_max_gap=gap,all7_frozen_comparison_gates=gates,
                    author_output_pins=output_pins,all_56_pairwise_gates_computed=True,aggregate=aggregate,
                    source_excerpts=source_excerpt_files,
                    final_scope=['all neural boundary predictions independently reconstructed',
                                 'first task all7 neural arms independently trained, later99 neural histories inherited',
                                 'all eight1M cache streams and all boundary risks/hits independently replayed',
                                 'ONE frozen fixed-state old-input oracle contrary completed',
                                 'original Torch/historical deployment/paper Algorithm1 directly unverified by reviewer',
                                 'total deployed storage matching unearned'],
                    explicit_read_bytes=sum(x['bytes'] for x in READS),reads=READS,
                    seconds=time.perf_counter()-START,peak_rss_bytes_macos=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
    (HERE/'FINAL_AUDIT.json').write_text(json.dumps(main_audit,indent=2)+'\n')
    explicit=(r['explicit_file_read_bytes']+c['explicit_read_bytes']+v['explicit_file_read_bytes']+
              sum(x['bytes'] for x in f['reads'])+main_audit['explicit_read_bytes'])
    science_seconds=r['seconds']+c['seconds']+v['seconds']+f['seconds']+main_audit['seconds']
    rss=max(r['peak_rss_bytes_macos'],c['peak_rss_bytes_macos'],v['peak_rss_bytes_macos'],
            f['peak_rss_bytes_macos'],main_audit['peak_rss_bytes_macos'])
    resources=dict(status='review completed; report-only integration remains',reviewer='01a19f57-57d3-7b13-b2a7-af1c0ccdf243',
        original_start_utc='2026-11-03T02:57:44Z',reference_completed_utc=r['utc'],contrary_completed_utc=c['utc'],
        review_hard_utc='2026-11-03T04:22:44Z',new_public_operations=0,new_ingress_bytes=0,dependency_installs=0,
        protected_old_payload_accesses=0,empirical_payload_accesses=0,new_teacher_draws=0,new_generated_examples=0,
        separate_read_hash_decode_charge_bytes=600_000_000,separate_read_limit_bytes=1_000_000_000,
        explicit_instrumented_file_read_bytes=explicit,
        known_threefold_file_read_hash_decode_plus_20MB_context_bytes=3*explicit+20_000_000,
        science_process_seconds= science_seconds,short_process_allowance_seconds=5,
        conservative_science_process_seconds=science_seconds+5,science_process_limit_seconds=1500,
        maximum_measured_science_rss_bytes=rss,science_rss_limit_bytes=1_000_000_000,
        one_process_one_thread_serial=True,full_neural_boundary_predictions=9_049_600,
        independently_replayed_first_task_neural_gradients=959_960,
        independently_replayed_cache_observations=8_000_000,independently_scored_cache_predictions=1_292_800,
        contrary_old_support_event_evaluations=490_816,contrary_saved_events=334,contrary_eligible_events=286,
        contrary_excluded_no_old_task_events=48,
        local_failures=[
          dict(kind='pre-registration clock tool denial',scientific_process_started=False,payload_bytes=0),
          dict(kind='oversized ordinary registry rg denied',scientific_process_started=False,payload_bytes=0),
          dict(kind='unquoted filename wildcard wc denied',scientific_process_started=False,payload_bytes=0),
          dict(kind='own large-result wc denied',scientific_process_started=False,payload_bytes=0),
          dict(kind='model-capacity systemError',turn='01a19f57-5874-7453-a0a3-6b2243d15693',
               started_utc='2026-11-03T02:57:44Z',ended_utc='2026-11-03T03:01:01Z',
               native_scientific_jobs_started=0,failed_context_runtime_and_host_peaks='unknown; bounded clock not reset',
               continuation='same actual chat/reservation lineage, PI-authorized one recovery'),
          dict(kind='reviewer beta=.75 constructor-default reference mistake; pinned config=.7',exit_code=1,
               seconds=f['seconds'],peak_rss_bytes=f['peak_rss_bytes_macos'],explicit_read_bytes=sum(x['bytes'] for x in f['reads']),
               exact_failed_code='reconstruct_beta075_failed.py',correction='RECONSTRUCTION_CORRECTION.md'),
          dict(kind='combined initial tool output truncated',resolution='bounded overlap reread; context charge preserved')],
        earlier_lineage=dict(public_operations=46,ingress_charge_bytes=168_000_000,ingress_compliance='UNCERTIFIED',
                            separate_read_charge_bytes=700_000_000,generated_examples=9_130_000,prior_revisions=2,
                            author_order_test_revisions=0,source_transcription_failures=3,
                            all_earlier_failed_passes_and_resource_unknowns_preserved=True),
        total_lineage_separate_read_charge_bytes=1_300_000_000,
        physical_io_bytes=None,provider_and_host_peaks=None,wrapper_and_failed_capacity_peak=None,
        resource_qualification='conservative application read/hash/decode bookkeeping, not complete physical-I/O or host certification',
        exposure='all original eight teachers101contexts/fast streams/labels/latent parameters/initial weights/output states/events consumed; all recomputed cache, neural and counterfactual outputs consumed; no protected release',
        remaining_limits=['later99 neural-task full gradient histories not replayed','Torch/source RNG/float32/tie/historical deployment unrun',
                          'smallN t interval coverage not calibrated','oracle changed information/diagnostic only','total storage matching unearned'],
        latest_remaining_percent=18,secondary_usage='unavailable',reserve_remaining_percent=10,reset_or_credit_spend=0,
        jobs=0,shared_record_or_native_goal_mutations=0)
    assert resources['known_threefold_file_read_hash_decode_plus_20MB_context_bytes']<600_000_000
    assert science_seconds+5<1500 and rss<1_000_000_000
    (HERE/'RESOURCES.json').write_text(json.dumps(resources,indent=2)+'\n')
    print(json.dumps(dict(status='PASS',all_frozen_gate_agreement=gates,max_interval_gap=gap,
                         seconds=science_seconds+5,peak_rss_bytes=rss,explicit_read_bytes=explicit,
                         conservative_known_read=resources['known_threefold_file_read_hash_decode_plus_20MB_context_bytes'],aggregate=aggregate)),flush=True)


if __name__=='__main__':
    try:main()
    except BaseException:
        (HERE/'CLOSEOUT_FAILURE.txt').write_text(traceback.format_exc())
        raise
