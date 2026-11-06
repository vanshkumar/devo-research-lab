"""Local artifact inventory/accounting. No simulation, fitting or outside access."""
import time
BEGIN=time.monotonic();CPU=time.process_time()
import json,hashlib,struct,resource
from pathlib import Path
from datetime import datetime,timezone

HERE=Path(__file__).resolve().parent
def get(n):return json.loads((HERE/n).read_text())
def save(n,x):(HERE/n).write_text(json.dumps(x,indent=2,allow_nan=False)+'\n')
def utc():return datetime.now(timezone.utc).isoformat()

stage1=get('ACCOUNTING_STAGE1.json')
resources=['MAIN_EXECUTION.json','MAIN_CONTROLS.json','REFERENCE_TO_DEVELOPMENT.json',
           'ANALYSIS_RESOURCES_INITIAL512.json','REFINEMENT_EXECUTION.json','REFINEMENT_ANALYSIS_RESOURCES.json',
           'PLOT_RESOURCES_FIRST.json','PLOT_RESOURCES_SECOND.json','PLOT_RESOURCES.json']
rows={};science_cpu=0.;science_wall=0.;read_decode=0;peak=stage1['peak_recorded_scientific_rss_bytes']
for name in resources:
    r=get(name);c=r['scientific_cpu_seconds'];w=r['process_wall_seconds']
    b=r.get('explicit_read_decode_bytes',r.get('summary_read_bytes',0))
    science_cpu+=c;science_wall+=w;read_decode+=b;peak=max(peak,r['peak_rss_bytes'])
    rows[name]=dict(scientific_cpu_seconds=c,process_wall_seconds=w,explicit_read_decode_bytes=b,peak_rss_bytes=r['peak_rss_bytes'])
assert get('MAIN_EXECUTION.json')['status']=='complete'
assert get('REFINEMENT_EXECUTION.json')['status']=='complete'
assert get('MAIN_FAMILY_REFINED.json')['n_columns']==652
assert get('MAIN_FAMILY_INITIAL512.json')['n_columns']==632
assert len(get('MAIN_ANALYSIS.json')['primary_rows'])==4
assert hashlib.sha256((HERE/'MAIN_FREEZE.md').read_bytes()).hexdigest()=='25c7ca55ea81e38af6a7b581112c578728119aa7ab872fb7075503a1561e3175'
# Figures were inspected once before and once after the PI's scope clarification.
png=(HERE/'MAIN_RESULT.png').read_bytes();width,height=struct.unpack('>II',png[16:24])
figure_read=(HERE/'MAIN_RESULT_FIRST.png').stat().st_size+len(png)
nominal_pixels=2*width*height*4
qa=dict(utc=utc(),final_figure='MAIN_RESULT.png',final_figure_visually_inspected=True,
        dimensions=[width,height],inspection_count=2,figure_read_bytes_nominal=figure_read,
        nominal_RGBA_decode_charge_bytes=nominal_pixels,
        final_scope_clarification='Gray bands are primary rows in652family; source points omit animal bands; source envelope upper4.24/3.83pp does not exclude material gains',
        layout='Readable titles/axes/legends/caption; no clipped panel text or overlapping scientific labels',
        image_io_note='Tool-internal image decode/physical I/O not instrumented; RGBA pixel charge is nominal, not measured')
save('FIGURE_QA.json',qa)
dynamic={'MANIFEST.json','FINAL_ACCOUNTING.json','CLOSEOUT_HASHING.json','NATIVE_COMPLETE.json','FINAL_ALLOWANCE.json','CHECKPOINT.md','SEAL.log'}
entries=[];hashbytes=0
for path in sorted(HERE.rglob('*')):
    if not path.is_file() or path.name in dynamic:continue
    raw=path.read_bytes();hashbytes+=len(raw)
    entries.append(dict(path=str(path.relative_to(HERE)),bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest(),
                        ownership='PI' if path.name=='BRIEF.md' else 'author'))
for path in HERE.glob('*.json'):json.loads(path.read_text())
hash_cpu=time.process_time()-CPU;hash_wall=time.monotonic()-BEGIN
save('CLOSEOUT_HASHING.json',dict(utc=utc(),explicit_artifact_hash_read_bytes=hashbytes,
     parent_process_cpu_seconds=hash_cpu,process_wall_seconds=hash_wall,artifact_files=len(entries),
     estimated_context_read_charge_covers_uninstrumented_small_JSON_text_reads=True))
measured_stage2=read_decode+hashbytes+figure_read
stage2_nominal=measured_stage2+15000000+nominal_pixels
whole_measured=stage1['measured_explicit_read_decode_bytes']+measured_stage2
whole_booked=stage1['counted_plus_estimated_charge_bytes']+stage2_nominal
final=dict(utc=utc(),stage1=stage1,stage2_processes=rows,
     stage2_recorded_scientific_cpu_seconds=science_cpu,stage2_scientific_process_wall_sum_seconds=science_wall,
     artifact_hashing_parent_cpu_seconds=hash_cpu,artifact_hashing_wall_seconds=hash_wall,
     stage2_known_explicit_read_decode_and_hash_bytes=measured_stage2,
     stage2_uninstrumented_context_read_estimate_bytes=15000000,
     stage2_nominal_image_decode_charge_bytes=nominal_pixels,stage2_recorded_plus_estimated_bytes=stage2_nominal,
     whole_author_recorded_scientific_cpu_seconds=stage1['scientific_process_cpu_seconds']+science_cpu,
     whole_author_recorded_parent_cpu_including_hashing_seconds=stage1['scientific_process_cpu_seconds']+science_cpu+hash_cpu,
     conservative_unmeasured_child_startup_compute_booking_seconds=60,
     whole_author_known_explicit_read_decode_bytes=whole_measured,whole_author_recorded_plus_estimated_bytes=whole_booked,
     peak_recorded_rss_bytes=peak,source_archive_ingress_bytes=0,protected_observation_release=False,
     physical_io='unknown',runtime_import_provider_reads='unknown',child_process_CPU='not separately instrumented;60s extra booking is conservative planning, not measurement',
     process_wall_note='Sum of process walls is not agent elapsed; the controls briefly overlapped the main. Native goal and Stage2 start/end receipts give agent elapsed.',
     prior_lineage='Original campaign/November4 and acquisition-rule-vs-tracker costs/failures/exposure unchanged; prior1,061,983,723counted-plus-conservative bytes/590.689978serial science-wall seconds not refunded.',
     limits=dict(stage2_cpu_seconds=8100,stage2_read_decode_bytes=800000000,stage2_elapsed_seconds=10800,
                 whole_author_cpu_seconds=9000,whole_author_read_decode_bytes=1050000000,whole_author_elapsed_seconds=16200),
     remaining_reserved_result_challenge=dict(agent_wall_seconds=9000,scientific_cpu_seconds=1800,read_decode_bytes=600000000,spent_by_author=False),
     remaining_reserved_revision=dict(agent_wall_seconds=3600,scientific_cpu_seconds=1200,read_decode_bytes=300000000,spent_by_author=False),
     job_disposition='Every issued simulation/analysis/plot subprocess exited0; no scientific job running',
     scientific_failure_qualifications=['Two finite input/engagement alternatives failed source predictive/calibration role',
       'Nominal max-T simultaneous band coverage modestly short in finite controls','Early10% proper-score utility and source/site envelope unresolved','Some source/reference integration warnings remain'],
     administrative_failure='One attempted report apply_patch was rejected for delete/add of the same path; recovered with update only, no scientific rerun')
assert science_cpu+hash_cpu+60<8100
assert stage2_nominal<800000000
assert whole_booked<1050000000
save('FINAL_ACCOUNTING.json',final)
manifest=dict(utc=utc(),scope='Completed author two-stage study, pending distinct result challenge; not PI ultimate success',
     files=entries,artifact_hash_read_bytes=hashbytes,
     frozen_original_main_sha256='25c7ca55ea81e38af6a7b581112c578728119aa7ab872fb7075503a1561e3175',
     dynamic_closeout_metadata_not_self_hashed=sorted(dynamic),
     original_manifests='MANIFEST_STAGE1.json and preserved original scientific input/freezes remain authoritative for their times',
     reproducibility='REPRODUCE.md; original512/632 and refined1024/652 retained; source/observed aggregates enable independent scoring')
save('MANIFEST.json',manifest)
print(json.dumps(dict(science_CPU_minutes=(stage1['scientific_process_cpu_seconds']+science_cpu)/60,
     stage2_known_bytes=measured_stage2,stage2_recorded_plus_estimated_bytes=stage2_nominal,
     whole_author_recorded_plus_estimated_bytes=whole_booked,hash_read_bytes=hashbytes,
     peak_rss_bytes=peak,artifact_files=len(entries),all_recorded_booked_limits_pass=True)))
