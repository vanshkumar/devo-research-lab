"""Closeout of existing outputs only; no scientific/source/evaluation execution."""
from datetime import datetime,timezone
import hashlib,json,resource,time
from pathlib import Path

HERE=Path(__file__).resolve().parent
cpu,wall=time.process_time(),time.monotonic();own_reads=0
stages=[('SAVED_QUALIFICATION.json','io'),('CATALOGUE_EXTRACTION.json',None),
 ('CATALOGUE_QUALIFICATION_INITIAL.json','io'),('CATALOGUE_QUALIFICATION.json','io'),
 ('FOOTER_QUALIFICATION.json','io'),('AGGREGATE_PROBE_SCHEMA.json','io'),
 ('AGGREGATE_CHRONOLOGY.json','io'),('SOURCE_MEASUREMENT_PROBE.json','io'),
 ('CRITERION_SOURCE_SCREEN.json','io'),('CRITERION_SOURCE_FIT_INITIAL.json','io'),
 ('CRITERION_COUNT_COUNTEREXAMPLE.json',None),('QUALIFIED_COHORT.json','io'),
 ('DISCRIMINATION.json','io'),('FOCUSED_DESIGN_INITIAL.json','io'),('FOCUSED_DESIGN.json','io'),
 ('CRITERION_SOURCE_CHRONOLOGY.json','io')]
records=[];science_cpu=0.;read_charge=0
for name,key in stages:
    b=(HERE/name).read_bytes();own_reads+=len(b);j=json.loads(b)
    charge=sum(j[key].values()) if key else sum(j.get(a,0) for a in ['explicit_read_bytes','decoded_metadata_bytes','input_read_charge_bytes'])
    c=j.get('cpu_seconds',0.);science_cpu+=c;read_charge+=charge
    records.append(dict(file=name,read_decode_charge_bytes=charge,recorded_cpu_seconds=c,
                        process_wall_seconds=j.get('process_wall_seconds'),
                        basis='Contains explicit reads, actual decoded arrays and clearly named conservative engine/logical/identity-row charges; not measured physical I/O.'))
b=(HERE/'PUBLIC_REQUESTS.jsonl').read_bytes();own_reads+=len(b);requests=[json.loads(s) for s in b.splitlines()]
received=sum(r['received_bytes'] for r in requests);request_cpu=sum(r['cpu_seconds'] for r in requests)
files=[p for p in HERE.iterdir() if p.is_file() and p.suffix in ['.json','.jsonl','.py','.md']
       and p.name not in ['BRIEF.md','MANIFEST.json','FINAL_ACCOUNTING.json','GOAL_FINAL.json']]
manifest=[];hash_bytes=0
for p in sorted(files):
    b=p.read_bytes();hash_bytes+=len(b);manifest.append(dict(path=p.name,bytes=len(b),sha256=hashlib.sha256(b).hexdigest()))
close_cpu=time.process_time()-cpu
extra_read_booking=250_000_000
extra_cpu_booking=120.
total_read=read_charge+own_reads+hash_bytes+extra_read_booking
cpu_charge=science_cpu+request_cpu+close_cpu+extra_cpu_booking
assert received+1_000_000<80_000_000 and total_read<2_000_000_000 and cpu_charge<2700
result=dict(utc=datetime.now(timezone.utc).isoformat(),status='bounded source/design closeout; all native processes terminal',
    limits=dict(elapsed_seconds=14400,science_cpu_seconds=2700,new_public_ingress_bytes=80_000_000,explicit_read_decode_bytes=2_000_000_000,account_reserve_percent=25,token_budget=None),
    scientific_processes=records,recorded_scientific_process_cpu_seconds=science_cpu,
    HTTP_request_count=len(requests),HTTP_response_body_bytes=received,
    web_tool_result_ingress_estimated_booking_bytes=1_000_000,
    public_ingress_recorded_plus_estimated_bytes=received+1_000_000,
    HTTP_request_cpu_seconds=request_cpu,HTTP_CPU_note='Embedded request times overlap scientific processes; summing again is a conservative double charge, not another actual process.',
    read_decode_counted_and_nominal_bytes=read_charge,closeout_json_read_bytes=own_reads,
    closeout_hash_read_bytes=hash_bytes,
    uninstrumented_context_inline_check_failed_process_and_request_log_read_booking_bytes=extra_read_booking,
    read_decode_recorded_nominal_plus_estimated_bytes=total_read,
    closeout_recorded_parent_cpu_seconds=close_cpu,
    unmeasured_import_failed_process_inline_reduction_and_closeout_CPU_booking_seconds=extra_cpu_booking,
    science_CPU_conservative_recorded_plus_booked_seconds=cpu_charge,
    peak_recorded_scientific_rss_bytes=max(json.loads((HERE/n).read_bytes()).get('peak_rss_bytes',0) for n,k in stages),
    native_elapsed='Actual final native goal readback in GOAL_FINAL; no context/budget reset. Native model/token accounting is distinct from local scientific CPU.',
    prior_lineage=dict(author_science_CPU_seconds=4932.693987,author_recorded_estimated_read_bytes=723451263,
      distinct_result_reviewer_science_CPU_seconds=29.043,reviewer_recorded_estimated_read_MB=405.59,
      review_totals_basis='Rounded whole-review totals carried in the current PI handoff; FINAL_RESOURCES.json alone is only its last0.2772CPU-second stage, not the whole reviewer.',
      authoritative_paths=['../calibration-frontier-main-2026-11-05/FINAL_ACCOUNTING.json','../../reviews/calibration-frontier-result-2026-11-05/REVIEW.md','../../reviews/calibration-frontier-result-2026-11-05/RESOURCES_FINAL.log'],
      preservation='All earlier lineage, failures, caps and unknown physical/provider/runtime/import/child costs remain. No refunded budget or fresh holdout follows from this task.'),
    exposure=dict(new_source_only=dict(subject='NYU-42',eid='63cbe4a9-e50d-4045-ad46-3c68eb40aa81',rows=273,fields=8,whole_animal_excluded_from_evaluation=True),
      prior_source_sample='NYU-28 opaque/schema sample retained and excluded from primary',
      proposed_primary_evaluation_response_values_opened=False,
      aggregate_identity_protocol_and_future_availability_auxiliary_exposed=True,
      footer_statistics_not_queried=True,training_status_tables_not_acquired=True,
      source74_rows='Existing prepared consumed source<=6000 only, original exposure retained',
      original64_evaluation='No new payload read; only saved consumed contribution/summary arrays used',
      protected_payload_release=False),
    failures='ACCESS_HISTORY, FOOTER_INTERRUPT, LOCAL_FAILURES, INITIAL/EXECUTED outputs and PUBLIC_REQUESTS preserve failures/recoveries; old completed science was not restarted.',
    unknowns=['Physical filesystem I/O','TLS/header/provider/network transport beyond recorded response bodies','Web-provider upstream ingress','Runtime/library/import reads and managed tool execution overhead','Exact failed-process CPU/RSS/partial-interruption work beyond saved checkpoints','Account use attributable to this worker amid concurrent PI/reviewer activity'],
    qualification='Nominal engine whole-file/identity64byte charges and extra bookings are conservative accounting bases, not instrumentation or certificates for unknown costs.',
    no_new_main_or_shared_goal_heartbeat_change=True)
(HERE/'FINAL_ACCOUNTING.json').write_text(json.dumps(result,indent=2)+'\n')
(HERE/'MANIFEST.json').write_text(json.dumps(dict(utc=result['utc'],scope='Owned primary evidence/prose/code/request receipts; PI-owned BRIEF and self/circular/future native completion artifacts omitted. Raw response binaries are already individually pinned in PUBLIC_REQUESTS; huge footer-only sparse derivatives are not outcome datasets and are not rehashed.',files=manifest),indent=2)+'\n')
print(json.dumps({k:result[k] for k in ['recorded_scientific_process_cpu_seconds','HTTP_request_count','HTTP_response_body_bytes','public_ingress_recorded_plus_estimated_bytes','read_decode_counted_and_nominal_bytes','closeout_json_read_bytes','closeout_hash_read_bytes','read_decode_recorded_nominal_plus_estimated_bytes','science_CPU_conservative_recorded_plus_booked_seconds','peak_recorded_scientific_rss_bytes']},indent=2))
