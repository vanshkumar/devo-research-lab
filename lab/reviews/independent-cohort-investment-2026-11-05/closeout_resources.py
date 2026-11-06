"""Static closeout accounting, not a monitor or permissions service.

Conservative full-file context charges are retrospective estimates. Computational
receipts retain exact explicit bytes/decoded arrays from each executed version.
Unknown physical, import, provider and helper costs stay unknown.
"""
from datetime import datetime,timezone
from pathlib import Path
import json,resource
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[2]
NEW=ROOT/'lab/tasks/independent-acquisition-cohort-2026-11-05'
OLD=ROOT/'lab/tasks/calibration-frontier-main-2026-11-05'
def j(p):return json.loads(p.read_text())
runs=[]
def add(name,key,cpuk,readk,decodek=None,repetitions=1,accepted=True):
    x=j(HERE/name)[key] if key else j(HERE/name)
    runs.append(dict(receipt=name,repetitions=repetitions,accepted_result=accepted,
       recorded_cpu_seconds=x[cpuk]*repetitions,
       explicit_read_bytes=x[readk]*repetitions,
       decoded_array_bytes=x.get(decodek,0)*repetitions if decodek else 0,
       peak_rss_bytes=x.get('peak_rss_bytes',0),
       first_unrecorded_failure_note='Failed first full identity pass had same inputs; second stored pass duplicated as a conservative read/CPU booking, not measurement of first.' if repetitions>1 else None))
add('INDEPENDENT_CHECK.json','resources','scientific_cpu_seconds','explicit_reads','decoded_saved_array_bytes')
add('LEAN_SENSITIVITY.json','resource','cpu_seconds','explicit_reads','decoded_arrays_bytes')
runs.append(dict(receipt='LEAN initial before additional controls; native execution output retained',
   repetitions=1,accepted_result=True,recorded_cpu_seconds=.543526,
   explicit_read_bytes=621512,decoded_array_bytes=399360,peak_rss_bytes=98533376,
   note='Current file adds controls; initial code/results were not a failed or changed scientific decision. Both runs charged.'))
add('IDENTITY_CHECK.json',None,'cpu_seconds','explicit_read_bytes')
add('SOURCE_CONTRARY.json','resources','cpu_seconds','explicit_read_bytes','decoded_arrays_bytes')
add('FULL_IDENTITY_CHECK_ATTEMPT.json','resources','cpu_seconds','explicit_read_bytes',repetitions=2,accepted=False)
add('FULL_IDENTITY_CHECK.json','resources','cpu_seconds','explicit_read_bytes')

ctx={}
def c(path,count):ctx[str(path)]=max(ctx.get(str(path),0),count)
for fn,n in [('LEARNINGS.md',4),('STATE.md',1),('LAB_WORKFLOW.md',2),('lab/AUTHORIZATION.md',2),('lab/HARD_GATES.md',2),
 ('lab/tasks/research-run-2026-11-05/BRIEF.md',1),('lab/reviews/independent-cohort-investment-2026-11-05/BRIEF.md',1),
 ('lab/tasks/calibration-frontier-main-2026-11-05/RESULT.md',1),('lab/reviews/calibration-frontier-result-2026-11-05/REVIEW.md',1),
 ('lab/reviews/acquisition-rule-investment-2026-11-05/PRIOR_CHECK.md',1),('lab/reviews/acquisition-rule-investment-2026-11-05/PRIOR_RECEIPTS.json',2),
 ('lab/reviews/calibration-frontier-main-design-2026-11-05/REVIEW.md',2),
 ('lab/tasks/acquisition-rule-vs-tracker-2026-11-05/PRIOR.md',1),('lab/tasks/acquisition-rule-vs-tracker-2026-11-05/RESULT.md',1)]:
 c(fn,n)
for fn,n in [('BRIEF.md',1),('FOCUSED_DESIGN.json',6),('DISCRIMINATION.json',2),('CRITERION_SOURCE_FIT.json',5),
 ('AGGREGATE_CHRONOLOGY.json',5),('QUALIFIED_COHORT.json',7),('ORIGINAL_EXCLUSIONS.json',5),('ORIGINAL_SESSION_IDS.json',2),
 ('FOOTER_QUALIFICATION.json',1),('SOURCE_ONLY_ACCESS_PLAN.json',1),('SOURCE_MEASUREMENT_PROBE.json',1),
 ('AGGREGATE_ACCESS_PLAN.json',1),('IDENTITY_PATTERN_CHECK.json',1),('ACCESS_HISTORY.md',1),('LOCAL_FAILURES.md',1),
 ('DESIGN.md',2),('MILESTONE_ASSESSMENT.md',1),('RESULT.md',1),('FINAL_ACCOUNTING.json',2),('GOAL_FINAL.json',1),
 ('CRITERION_COUNT_COUNTEREXAMPLE.json',1),('focused_design.py',1),('plan_discrimination.py',1)]:
 c('lab/tasks/independent-acquisition-cohort-2026-11-05/'+fn,n)
for fn,n in [('MAIN_FAMILY_REFINED.json',3),('MAIN_ANALYSIS.json',3),('MAIN_EXECUTION.json',2),
             ('FINAL_ACCOUNTING.json',1),('MAIN_ACCESS.json',1),('PREP_ACCESS.json',1)]:
 c('lab/tasks/calibration-frontier-main-2026-11-05/'+fn,n)
for f in OLD.glob('*.py'):c(f.relative_to(ROOT),3)
details=[dict(path=p,full_file_pass_booking=n,bytes_each=(ROOT/p).stat().st_size,
             charge_bytes=n*(ROOT/p).stat().st_size) for p,n in ctx.items()]
context_bytes=sum(x['charge_bytes'] for x in details)
# Other saved-array introspections used before the reproducible scientific runs:
array_extra_read=2*(OLD/'REFINED_SCORES.npz').stat().st_size+2*(OLD/'REFINED_CONTRASTS.npz').stat().st_size+(OLD/'MAIN_SCORES.npz').stat().st_size
array_extra_decode=1500000
# Includes bounded metadata displays, own code/result/hash reads, failed helper
# stdout/log reads and post-resource-goal receipts. Physical/import/provider
# accounting is explicitly NOT certified by this booking.
extra_booking=20000000
known_read=sum(r['explicit_read_bytes'] for r in runs)
known_decode=sum(r['decoded_array_bytes'] for r in runs)
recorded_cpu=sum(r['recorded_cpu_seconds'] for r in runs)
uncertain_cpu_booking=60.
total=known_read+known_decode+2*context_bytes+array_extra_read+array_extra_decode+extra_booking
source=j(NEW/'FINAL_ACCOUNTING.json')
account=j(HERE/'ACCOUNT_CHECKPOINT.json')
now=datetime.now(timezone.utc);dispatch=datetime(2026,11,5,17,47,19,tzinfo=timezone.utc)
result=dict(recorded_at=now.isoformat(),review_scope='Bounded independent investment review only',
  limits=dict(elapsed_seconds=5400,scientific_cpu_seconds=600,explicit_read_decode_bytes=200000000,public_ingress_bytes=5000000,reserve_percent=25),
  elapsed_from_conservative_dispatch_seconds=(now-dispatch).total_seconds(),
  deadline_utc='2026-11-05T19:17:19+00:00',
  execution_receipts=runs,recorded_or_conservatively_duplicated_scientific_cpu_seconds=recorded_cpu,
  separate_uninstrumented_helper_import_failed_process_closeout_cpu_booking_seconds=uncertain_cpu_booking,
  recorded_plus_booked_scientific_cpu_seconds=recorded_cpu+uncertain_cpu_booking,
  peak_recorded_scientific_rss_bytes=max(r['peak_rss_bytes'] for r in runs),
  known_scientific_explicit_reads=known_read,known_scientific_decoded_array_bytes=known_decode,
  context_full_file_charges=context_bytes,context_UTF8_decode_nominal_charge=context_bytes,
  context_charge_details=details,extra_saved_array_introspection_read_charge=array_extra_read,
  extra_saved_array_introspection_decoded_array_booking=array_extra_decode,
  uninstrumented_context_metadata_failed_helper_own_artifact_and_closeout_booking_bytes=extra_booking,
  total_recorded_nominal_and_estimated_read_decode_bytes=total,public_ingress_bytes=0,
  actual_usage_file='ACCOUNT_CHECKPOINT.json',ordinary_usage_allowed=True,
  start_weekly_remaining_percent=68,latest_weekly_remaining_percent=66,
  unavailable_windows='secondary and individual missing/null, not zero; no applicable unavailable value invented',
  source_assignment_actuals=dict(recorded_scientific_cpu_seconds=source['recorded_scientific_process_cpu_seconds'],
     conservative_science_cpu_seconds=source['science_CPU_conservative_recorded_plus_booked_seconds'],
     recorded_HTTP_body_bytes=source['HTTP_response_body_bytes'],
     public_recorded_plus_estimated_bytes=source['public_ingress_recorded_plus_estimated_bytes'],
     read_decode_recorded_nominal_plus_estimated_bytes=source['read_decode_recorded_nominal_plus_estimated_bytes'],
     native_goal_completed=True,native_turn_completed=True,source_payloads_opened='NYU-42 only,273rows/eightfields, whole subject excluded'),
  previous_completed_study=dict(author_scientific_cpu_seconds=4932.693987,author_recorded_estimated_read_bytes=723451263,
     distinct_result_review_scientific_cpu_seconds=29.043,distinct_result_review_counted_estimated_read_bytes=405594971,
     earlier_lineage='All earlier costs, failures, uncertainty and exposure retained by reference; no refund.'),
  recommended_new_investigation=dict(future_cpu_minutes=[214.890395390625,344.846553546875],
     future_scientist_elapsed_hours=[6.5,11.5],future_public_body_ceiling_bytes=500000000,
     future_read_decode_bytes=[5000000000,8000000000],future_peak_RSS_bytes=[1000000000,3000000000],
     future_storage_bytes=[2000000000,4000000000],new_source_and_this_review_additional_spent_cpu_minutes=(source['science_CPU_conservative_recorded_plus_booked_seconds']+recorded_cpu+uncertain_cpu_booking)/60,
     scope='Fixed trained prescriptions; no32draw default, repeated neural family or milestone main. Estimates and conservative bookings are not measured future usage.'),
  exposure=dict(new_evaluation_response_or_outcome_payloads=False,old_raw_outcomes_reopened=False,
     allowed_saved64_derived_scores=True,allowed_source_criterion_summaries=True,
     new_response_source_probe_not_reread=True,source_identity_protocol_chronology_auxiliary_metadata=True,
     protected_boundaries_unchanged=True,shared_records_edited=False,PI_goal_or_heartbeat_changed=False),
  failures=['System python missing NumPy before array access; existing .venv used.',
     'Guessed prose/code paths absent; metadata display attempted iterating an integer.',
     'First full-aggregate identity check used all170metadata names instead of154consumed/protected names. Native assertion failed twice; ATTEMPT receipt is not an accepted check. Exact135overlaps were traced solely to metadata-only subjects and corrected by canonical154filter; costs retained.',
     'Initial broad listings/JSON display were truncated; later checks inspect bounded named keys.'],
  job_disposition='All review scientific processes terminal, no main or uncollected review job; source native completion collected once.',
  unknowns=['Physical filesystem I/O','Runtime/import/provider and managed-tool reads/CPU','Exact CPU/RSS of failed/uninstrumented helpers','Per-worker attributable account consumption amid concurrent work'],
  qualification='Explicit scientific bytes/arrays are recorded. Context UTF8/full-file and failure costs are retrospective conservative bookings, not exact measurements or physical-I/O certificates. Some already recorded reads are deliberately overcharged. No cap reset or unrun check is represented as passed.')
assert total<200000000 and recorded_cpu+uncertain_cpu_booking<600
(HERE/'RESOURCES.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({k:result[k] for k in ['elapsed_from_conservative_dispatch_seconds','recorded_plus_booked_scientific_cpu_seconds','total_recorded_nominal_and_estimated_read_decode_bytes','public_ingress_bytes','peak_recorded_scientific_rss_bytes','source_assignment_actuals']},indent=2))
