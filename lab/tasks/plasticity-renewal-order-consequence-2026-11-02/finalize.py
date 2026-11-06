"""Finite read/hash closeout of owned artifacts; no learning or new data."""
import hashlib
import json
from pathlib import Path
import resource
import sys
import time

ROOT=Path(__file__).resolve().parent


def main():
    start=time.perf_counter()
    if '--refresh-report-pins' in sys.argv:
        path=ROOT/'REPRODUCTION_MANIFEST.json'
        manifest=json.loads(path.read_bytes())
        for entry in manifest['files']:
            if entry['path'] in ['STATE.md','TERMINAL_REPORT.md']:
                data=(ROOT/entry['path']).read_bytes()
                entry.update(bytes=len(data),sha256=hashlib.sha256(data).hexdigest())
        manifest['communication_pins_refreshed_utc']=time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime())
        path.write_text(json.dumps(manifest,indent=2)+'\n')
        print(json.dumps(dict(status='PASS',refreshed=['STATE.md','TERMINAL_REPORT.md'],seconds=time.perf_counter()-start)))
        return
    run=json.loads((ROOT/'RUN_STATUS.json').read_bytes())
    audit=json.loads((ROOT/'AUDIT.json').read_bytes())
    reference=json.loads((ROOT/'REFERENCE.json').read_bytes())
    assert run['status']==audit['status']==reference['status']=='PASS'
    if '--summary-only' in sys.argv:
        print(json.dumps(dict(
            means={name:{key:value['mean'] for key,value in row.items()} for name,row in audit['aggregate'].items()},
            comparisons=audit['comparisons'],
            storage={name:{field:[min(v[name][field] for v in audit['storage_by_teacher'].values()),
                                   max(v[name][field] for v in audit['storage_by_teacher'].values())]
                           for field in ['actual_pickle4_state_bytes','actual_deep_python_state_bytes']}
                     for name in audit['aggregate']},
            retention_ages={name:{age:{field:sum(v[name]['retention_by_age'][age][field] for v in audit['all_teacher_summaries'].values())/8
                                       for field in ['mean_old_risk','mean_change_from_initial']}
                                  for age in ['1-9','10-49','50-99']}
                            for name in audit['aggregate']},
            method_counts=audit['method_counts_by_teacher'],
            resource=dict(main_seconds=run['main_seconds'],audit_seconds=audit['seconds'],
                          audit_rss=audit['max_rss_bytes_macos'],cumulative_seconds=audit['cumulative_science_seconds_including_5s_short_process_allowance'])
        )),flush=True)
        return
    files=[p for p in sorted(ROOT.iterdir()) if p.is_file() and p.name not in ['RESOURCES.json','REPRODUCTION_MANIFEST.json']]
    manifests=[]
    for path in files:
        data=path.read_bytes()
        manifests.append(dict(path=path.name,bytes=len(data),sha256=hashlib.sha256(data).hexdigest()))
    bytes_read=sum(v['bytes'] for v in manifests)
    duration=time.perf_counter()-start
    known_read_charge=audit['conservative_read_hash_decode_charge_bytes']+2*bytes_read+3*reference['separate_explicit_read_bytes']+1_000_000
    conservative=max(500_000_000,known_read_charge+100_000_000)
    seconds=audit['cumulative_science_seconds_including_5s_short_process_allowance']+duration
    rss=max(run['max_rss_bytes_macos'],audit['max_rss_bytes_macos'],reference['max_rss_bytes_macos'],resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
    assert conservative<=1_000_000_000 and seconds<1800 and rss<1_000_000_000
    resources=dict(status='completed finite study; interpretation in RESULT.md',
                   investigator='01a19f33-4681-7f83-a498-8727d0520ed2',
                   local_date='2026-11-02',utc_finalized=time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),
                   initial_orientation_utc='2026-11-03T02:18:20Z',
                   new_public_operations=4,new_public_operation_limit=6,new_programs=1,
                   new_ingress_charge_bytes=10_000_000,actual_provider_ingress_bytes=None,ingress_compliance='UNCERTIFIED',
                   separate_new_read_hash_decode_conservative_charge_bytes=conservative,new_read_limit_bytes=1_000_000_000,
                   audit_explicit_file_read_bytes=audit['actual_explicit_file_read_bytes'],
                   audit_conservative_read_hash_decode_bytes=audit['conservative_read_hash_decode_charge_bytes'],
                   closeout_explicit_file_read_bytes=bytes_read,
                   known_read_hash_decode_plus_context_allowance_bytes=known_read_charge,
                   allowance_note='500MB conservative floor includes context/import/hash/parse/failed-read allowances; physical I/O and host/provider peaks are unknown, not full I/O certification',
                   science_runtime_seconds_conservative=seconds,science_runtime_limit_seconds=1800,
                   main_seconds=run['main_seconds'],reference_seconds=reference['seconds'],audit_seconds=audit['seconds'],
                   closeout_seconds=duration,short_process_allowance_seconds=5,
                   maximum_measured_scientific_rss_bytes=rss,rss_limit_bytes=1_000_000_000,one_process_one_thread=True,
                   cpu_seconds_main=run['cpu_seconds'],cpu_seconds_audit=audit['cpu_seconds'],
                   generated_new_whole_teachers=8,generated_new_examples=8_080_000,learned_current_examples_per_teacher=1_000_000,
                   new_sgd_gradient_updates_all_arms=95_999_960,new_full_support_target_labels=25_856,
                   new_realizations_and_all_latents_outputs='fully consumed, including eight extra10,000-example blocks; no pristine replacement teachers',
                   exposure='all eight teacher parameters/contexts/fast draws/target supports/initial weights and all learner/scorer summaries/snapshots/events/cache/reservoir states',
                   empirical_raw_accesses=0,protected_old_payload_reads=0,old_fits_or_target_rescoring=0,
                   public_code_or_dependency_downloads=0,dependency_installs=0,author_torch_executions=0,
                   substantive_preevaluation_revisions=0,postvalidation_rescues=0,
                   local_failures=[dict(kind='pre-tool ordinary tail RUN.log rejected as data payload',observed_bytes=0,science_rerun=False,
                                        resolution='used existing native process output; no override or retry of denied read'),
                                   dict(kind='invalid combined delete/add same STATE path patch rejected before mutation',science_rerun=False,
                                        resolution='ordinary targeted update; no changes to scientific code or evidence')],
                   previous_lineage=dict(public_operations=42,ingress_allowance_bytes=158_000_000,ingress_compliance='UNCERTIFIED',
                                         separate_read_charge_bytes=200_000_000,generated_examples=1_050_000,teacher_seed=1729,
                                         revisions=2,three_transcribed_source_identity_failures_preserved=True,
                                         storage_provider_runtime_physical_io_unknowns_preserved=True),
                   jobs=0,shared_records_or_native_goal_edits=0,independent_scientific_review='UNRUN; this audit is within-investigator reconstruction',
                   reproduction_launcher='saved, not executed; later reproduction needs its own authorized bounded run')
    encoded=json.dumps(resources,indent=2).encode()+b'\n'
    (ROOT/'RESOURCES.json').write_bytes(encoded)
    manifests.append(dict(path='RESOURCES.json',bytes=len(encoded),sha256=hashlib.sha256(encoded).hexdigest()))
    (ROOT/'REPRODUCTION_MANIFEST.json').write_text(json.dumps(dict(
        utc=resources['utc_finalized'],files=manifests,
        note='self excluded; all scientific/frozen source/result bytes pinned; communication-status edits after finalization require targeted manifest update'),indent=2)+'\n')
    print(json.dumps(dict(status='PASS',files=len(manifests),closeout_read_bytes=bytes_read,
                          new_conservative_read_charge=conservative,science_seconds=seconds,max_rss=rss)),flush=True)


if __name__=='__main__':
    main()
