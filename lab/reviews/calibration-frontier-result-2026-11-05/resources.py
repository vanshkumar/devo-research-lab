"""Consolidate actual review receipts and explicitly separate conservative charges."""
import json
from pathlib import Path
from datetime import datetime,timezone

HERE=Path(__file__).resolve().parent


def main():
    early=['FIXED_RESOURCES.json','CONTROL_RESOURCES_V1.json','CONTROL_RESOURCES.json',
           'FIXED_FAMILY_RESOURCES.json','ONE_ACTIVE_BOUNDARY_RESOURCES.json',
           'SOURCE_BATCH_16_RESOURCES.json','SOURCE_BATCH_24_RESOURCES.json']
    final=['SOURCE_FAMILY_RESOURCES.json','SOURCE_FALSIFICATION_RESOURCES.json','REFINED_RESOURCES.json',
           'AUTHOR_REFINED_AGREEMENT_RESOURCES.json','FINAL_RESOURCES.json']
    receipts={n:json.loads((HERE/n).read_text()) for n in early+final}
    failure=json.loads((HERE/'SOURCE_FALSIFICATION_FAILURE.json').read_text())
    def sum_receipts(names):
        return dict(recorded_scientific_cpu_seconds=sum(receipts[n]['scientific_cpu_seconds'] for n in names),
                    recorded_scientific_process_wall_seconds=sum(receipts[n]['scientific_process_wall_seconds'] for n in names),
                    explicit_read_decode_bytes=sum(receipts[n]['explicit_read_decode_bytes'] for n in names))
    a,b=sum_receipts(early),sum_receipts(final)
    b['explicit_failed_summary_read_bytes']=failure['explicit_file_bytes']
    b['explicit_read_decode_bytes']+=failure['explicit_file_bytes']
    a['context_metadata_read_charge_estimate_bytes']=10000000
    b['context_metadata_read_charge_estimate_bytes']=5000000
    b['nominal_two_image_views_read_decode_charge_bytes']=2*2160*1620*4+500000
    for part in [a,b]:
        part['interpreter_and_administrative_cpu_booking_estimate_seconds']=30
        part['counted_plus_estimated_read_decode_bytes']=part['explicit_read_decode_bytes']+part.get('context_metadata_read_charge_estimate_bytes',0)+part.get('nominal_two_image_views_read_decode_charge_bytes',0)
    b['failed_process_cpu_charge_estimate_seconds']=1
    now=datetime.now(timezone.utc)
    conservative_start=datetime(2026,11,5,15,13,30,tzinfo=timezone.utc)
    phase_start=datetime(2026,11,5,15,50,28,tzinfo=timezone.utc)
    out=dict(utc=now.isoformat(),review_thread_id='01a1ac46-1881-7293-9d1a-c2a85c906476',
        conservative_continuous_start_utc=conservative_start.isoformat(),first_observed_clock_utc='2026-11-05T15:14:10Z',
        native_goal_created_utc='2026-11-05T15:14:17Z',continuous_elapsed_seconds=(now-conservative_start).total_seconds(),
        final_phase_start_utc=phase_start.isoformat(),final_phase_elapsed_seconds=(now-phase_start).total_seconds(),
        continuous_hard_endpoint_utc='2026-11-05T17:43:30Z',conservative_final_phase_endpoint_utc='2026-11-05T17:05:28Z',
        early=a,final=b,receipt_files=early+final,
        total_recorded_scientific_cpu_seconds=a['recorded_scientific_cpu_seconds']+b['recorded_scientific_cpu_seconds'],
        total_known_explicit_read_decode_bytes=a['explicit_read_decode_bytes']+b['explicit_read_decode_bytes'],
        total_counted_plus_estimated_read_decode_bytes=a['counted_plus_estimated_read_decode_bytes']+b['counted_plus_estimated_read_decode_bytes'],
        additional_compute_booking_estimate_seconds=61,
        peak_recorded_rss_bytes=max(r['peak_rss_bytes'] for r in receipts.values()),
        limits=dict(total_elapsed_seconds=9000,total_science_cpu_seconds=1800,total_explicit_read_decode_bytes=600000000,
                    early_science_cpu_seconds=900,early_read_decode_bytes=350000000,final_science_cpu_seconds=900,final_read_decode_bytes=250000000),
        source_archive_ingress_bytes=0,original_trial_or_protected_array_reads=0,
        failures=['Fixed science succeeded; external time-l wrapper exit1 from disallowed sysctl, preserved without repeating fixed science',
                  'Additional constant-error stationary-state V1 control had float-only zero-width misses; original and corrected law/costs retained',
                  'Source diagnostic relative-path receipt failed after one owned summary read; corrected and that failed read charged; CPU unknown/1s conservative charge'],
        external_wrapper_cpu_note='Fixed internal2.865596s CPU overlaps external3.18user+.05system; not double counted. Other interpreter/import/physical/provider bytes and CPU are not fully measured.',
        budget_note='Explicit script reads/array bytes are counted; context/image and61s CPU are conservative estimates, not measured physical I/O or certified overhead bounds. Successful outputs do not certify unmeasured resource compliance.',
        inherited_lineage='All prior campaign/November4/development costs, source exposure/failures and uncertainty remain; prior1,061,983,723 counted-plus-conservative bytes/590.689978 serial science-wall seconds are not refunded. Main-author costs are separate in its FINAL_ACCOUNTING.',
        job_disposition='All reviewer scientific subprocesses ended; fixed time wrapper exit1 preserved after successful science. No simulation or scientific subprocess remains active.',
        native_goal_proof='GOAL_START and checkpoints preserve the same objective/createdAt; actual final transition/readback is GOAL_FINAL.json when written. PI ultimate goal and heartbeat unchanged.')
    (HERE/'RESOURCES.json').write_text(json.dumps(out,indent=2)+'\n')
    print(json.dumps(out,indent=2))


if __name__=='__main__': main()
