"""Record incremental bounded diagnosis and cumulative initial-stage charges."""
from common import *
prior=get(HERE/'RESOURCE_CHECKPOINT.json')
stages=[get(HERE/(n+'_RESOURCES.json')) for n in ['DIAGNOSIS','OFFICIAL_SOURCE','MAPPING_CONSEQUENCE']]
seal=get(HERE/'PRE_OUTCOME_SEAL.json')
for p,h in seal['pins'].items():read(ROOT/p,h)
raw=get(HERE/'DIAGNOSIS_COMPLETE.json');s=get(HERE/'OFFICIAL_SOURCE_PINS.json')
assert raw['animals']==192 and raw['exact_objects_footer_checked']==802
assert s['evaluation_plus_text_http_bytes']==458538440
storage=sum(p.stat().st_size for p in HERE.rglob('*') if p.is_file())
rr=receipt('DIAGNOSIS_ACCOUNTING')
actual_cpu=sum(v['cpu_seconds'] for v in stages+[rr]);actual_reads=sum(v['read_decode_bytes'] for v in stages+[rr]);booked_cpu=actual_cpu+2
booked_reads=actual_reads+20000000
totcpu=prior['conservatively_counted_booked_cpu_seconds']+booked_cpu
totreads=prior['conservatively_counted_booked_read_decode_including_http_bytes']+booked_reads
assert booked_reads<=1250000000 and booked_cpu<=600 and totreads<3000000000
data=dict(utc=utc(),status='diagnosis_complete_awaiting_PI_measurement_decision',
    incremental_scientific_cpu_seconds=actual_cpu,incremental_booked_cpu_seconds=booked_cpu,
    incremental_explicit_nominal_decoded_read_bytes=actual_reads,incremental_booked_read_decode_bytes=booked_reads,
    incremental_context_bookings=dict(cpu_seconds=2,read_decode_bytes=20000000),
    incremental_http_body_bytes=s['cumulative_additional_public_body_bytes'],
    cumulative_http_body_bytes=s['evaluation_plus_text_http_bytes'],
    cumulative_booked_initial_science_cpu_seconds=totcpu,cumulative_booked_initial_read_decode_bytes=totreads,
    measured_peak_RSS_bytes=max(prior['peak_measured_RSS_bytes'],max(v['peak_rss_bytes'] for v in stages+[rr])),
    owned_storage_bytes=storage,earliest_dispatch_based_deadline_UTC='2026-11-06T00:27:22Z',
    correction_to_initial_deadline_receipt='Earlier actual dispatch governs; goal creation25s later is not extension.',
    initial_remaining_booked_cpu_seconds=11100-totcpu,initial_remaining_booked_read_decode_bytes=3000000000-totreads,
    remaining_http_body_bytes=500000000-s['evaluation_plus_text_http_bytes'],
    whole_objects_acquired=802,whole_objects_selected_numeric_decoded=802,
    unique_experimental_rows_selected_numeric_decoded=4943360,
    diagnosis_nominal_rows_redo_already_partial=435020,original_partial_and_repeat_charges_preserved=True,
    same_author_native_goal='active',main_forecast_or_score_job_started=False,all_jobs_terminal=True,
    no_raw_value_recode_or_cohort_change=True,source_provenance_pins_all_unchanged=True,
    retained_prior='RESOURCE_CHECKPOINT and all original source/review/old lineage costs remain additional. No reserved stage borrowed.',
    unknown_costs='Physical/provider/import I/O unknown. Bookings are not a certification of total hidden resource use.')
save('DIAGNOSIS_RESOURCE_CHECKPOINT.json',data);print(json.dumps(data,indent=2,default=serial))
