"""Artifact-only closeout; never opens a raw CSV or executes source notebooks."""
import json
import hashlib
import platform
import resource
from datetime import datetime, timezone
from pathlib import Path

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]

def read(name):
    return json.loads((HERE/name).read_text())

def save(name,value):
    (HERE/name).write_text(json.dumps(value,indent=2,allow_nan=False)+'\n')

def utc():
    return datetime.now(timezone.utc).isoformat()

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

recon=read('RECONSTRUCTION.json');contrary=read('CONTRARY.json');later=read('LATER_PROBE.json')
audit=read('COORDINATE_MASK_AUDIT.json');support=read('SUPPORT.json');pins=read('PINS.json')
run=read('RUN.json');lr=read('LATER_RUN.json');ar=read('AUDIT_RUN.json')
base=ROOT/'campaigns/target_event_carryover_2026-10-28/audits/source_measurement'
old=json.loads((base/'audit_results.json').read_text())
code=[]
for pin in old['code_integrity']:
    path=base/pin['local'];body=path.read_bytes()
    blob=hashlib.sha1(b'blob '+str(len(body)).encode()+b'\0'+body).hexdigest()
    check=len(body)==pin['bytes'] and hashlib.sha256(body).hexdigest()==pin['sha256'] and blob==pin['git_blob']
    code.append(dict(path=str(path.relative_to(ROOT)),bytes=len(body),sha256=pin['sha256'],git_blob=blob,
                     pin_pass=check,url=pin['url'],stored_results_decoded=False))
assert all(v['pin_pass'] for v in code)
times={}
for name in ('PLAN.md','CONTRARY_AMENDMENT.md','RECONSTRUCTION.json','CONTRARY.json','LATER_PROBE.json'):
    path=HERE/name
    times[name]=dict(sha256=sha(path),mtime_utc=datetime.fromtimestamp(path.stat().st_mtime,timezone.utc).isoformat())
start=datetime.fromisoformat(run['started_utc'])
first_end=datetime.fromisoformat(run['finished_utc'])
later_end=datetime.fromisoformat(later['created_utc'])
planmtime=datetime.fromtimestamp((HERE/'PLAN.md').stat().st_mtime,timezone.utc)
amendmtime=datetime.fromtimestamp((HERE/'CONTRARY_AMENDMENT.md').stat().st_mtime,timezone.utc)
ordering=dict(plan_mtime_before_initial_run=planmtime<start,
              first_run_before_amendment_mtime=first_end<amendmtime,
              amendment_mtime_before_later_output=amendmtime<later_end,
              plan_hash_matches_run=times['PLAN.md']['sha256']==contrary['frozen_plan_sha256'],
              amendment_hash_matches_run=times['CONTRARY_AMENDMENT.md']['sha256']==later['plan_amendment_sha256'])
assert all(ordering.values())
registry=json.loads((ROOT/'lab/registry.json').read_text())
pi=registry['pi']['thread_id']
sourceold=json.loads((ROOT/'sources/learning_intervention_feasibility_2026-10-28/source_manifest.json').read_text())
used={s['meta']['file'] for s in recon['sources']}|{'task_success_fig4.csv'}
save('SOURCE_DEFINITION_PINS.json',dict(created_utc=utc(),original_code_pins=code,
     files_timing=times,timing_order_checks=ordering,current_registry_PI=pi,
     manual_header_correction='See TIMING.md; frozen 00:18 manual clock label is incorrect.'))
save('SOURCES.json',dict(created_utc=utc(),csvs=[v for v in sourceold['files'] if v['local'] in used],
     raw_csv_hashes=[dict(path='sources/learning_intervention_feasibility_2026-10-28/'+s['meta']['file'],
                         sha256=s['meta']['sha256'],git_blob=s['meta']['git_blob']) for s in recon['sources']]+
                     [dict(path='sources/learning_intervention_feasibility_2026-10-28/task_success_fig4.csv',
                           sha256=support['Figure4_input_sha256'],mode='input-only')],
     original_code=code,
     cached_paper=dict(path=str((base/'Al-Fawakhiri2023_text.txt').relative_to(ROOT)),
                       sha256=sha(base/'Al-Fawakhiri2023_text.txt'),
                       URL='https://doi.org/10.1152/jn.00061.2023'),
     prior_work=['https://elifesciences.org/articles/39882',
                 'https://journals.plos.org/ploscompbiol/article?id=10.1371/journal.pcbi.1010005'],
     terms='Inherited source repository terms; Tsay article CC-BY. No redistribution or publication.'))
save('EXPOSURE.json',dict(created_utc=utc(),reviewer='01a19471-8ed1-7ca3-85c7-810e0e3fa0bb',
     source_people=[dict(source=s['source'],identities=s['meta']['identities'],decoded_rows=s['meta']['n_rows']) for s in recon['sources']],
     all_58_source_people_previously_consumed=True,new_pristine_validation_claim=False,
     Figure4=dict(input_only_ids=support['input_only_ids'],input_rows=42*968,exposures=support['target_exposures'],
                  raw_bytes_hashed=True,CSV_input_tokenization=True,
                  outcome_strings_discarded_before_numeric_conversion_and_analysis_retention=True,
                  retained_fields=support['retained_fields'],discarded_fields=support['discarded_before_conversion'],
                  numeric_outcome_values_converted=0,outcome_statistics=0,target_scores=0,
                  all_42_paper_summaries_previously_exposed=True),
     optional210_raw_geometry_opened=False,
     other_protected_data_opened=False,old_frozen_bytes_changed=False,
     protected='Pan20, Flesch81/B2/B20, laterHABITS, memory targets, four reserved worms and unrelated branch payloads remain closed.',
     exposure_resets=0,source_immutability='All original source/author paths read-only; writes owned review directory only.'))
tracked=run['charged_script_read_decode_hash_bytes']+lr['charged_bytes']+ar['charged_bytes']
codecharge=4*sum(v['bytes'] for v in code)
charged=220_000_000
assert tracked+codecharge<charged<450_000_000
peak=max(run['peak_rss_bytes'],lr['peak_rss_bytes'],ar['peak_rss_bytes'],resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
save('RESOURCES.json',dict(created_utc=utc(),START_utc='2026-11-01T00:10:35.200Z',
     deadline_utc='2026-11-01T00:55:35.200Z',review_allowance_bytes=450000000,
     charged_additional_read_decode_hash_bytes=charged,
     scientific_script_pass_charges=tracked,original_code_hash_charge=codecharge,
     extra_context_artifact_hash_and_closeout_reserve=charged-tracked-codecharge,
     accounting='Conservative file equivalents; includes all raw passes, decode/hash, context reads, output reads and final verification reserve. No new metering service.',
     inherited_author_read_charge=400000000,current_author_plus_review_subtotal=620000000,
     inherited_older_motor_lineage='Preserved separately as recorded in author/campaign resources; subtotal is not a reset or total of earlier motor work.',
     inherited_author_ingress_charge=2000000,inherited_author_logical_public_operations=6,
     review_ingress_bytes=0,review_public_requests=0,
     successful_peak_RSS_bytes=peak,RSS_limit_bytes=1000000000,
     scientific_processes_simultaneous=1,numerical_threads=1,scientific_runs=3,
     scientific_failed_runs=0,jobs_running=0,
     dependency_installations=0,credits_spent_or_reset=False,
     existing_pi_manual_usage='START records51%remaining above20%reserve; no worker usage substitution.',
     numerical_warnings=[read(n) for n in ('NUMERICAL_WARNINGS.json','LATER_WARNINGS.json','AUDIT_WARNINGS.json')]))
save('FAILURES.json',dict(created_utc=utc(),numerical_failed_runs=[],
     version_control_status='Scoped git status returned exit128: this workspace has no recognized .git parent. It was read-only; no commit or version-control mutation attempted.',
     nonexecuted_tool_attempts=[
         dict(action='Initial ordinary rg file discovery with a pipe',reason='Hook blocks shell composition; no payload execution'),
         dict(action='Initial ordinary read lab/STATE.md',reason='Context file is at root STATE.md; missing-path read blocked'),
         dict(action='Saved-artifact summary via python -c',reason='Hook blocks inline shell code; no summary executed')],
     context_scope_error='Initial line-bounded root STATE read included historical sections beyond requested compact CURRENT. No raw science read or stale execution direction followed; current START governed all work.',
     corrected_clock_label='Manual amendment00:18UTC label is inaccurate. Original bytes preserved; actual output/mtime/hash ordering recorded in SOURCE_DEFINITION_PINS.json.',
     scientific_limits=['Common stationary endpoint comparison less precise than primary.',
                        'Later Figure3 stationary denominators unstable; persistent normalized transfer not certified.',
                        'Absolute hand coordinate identity cannot be reconstructed from Figure3 export; HandAngle absent.',
                        'Historical numerical stderr observed by author, not independently replayed.',
                        'Saved nonlinear prescription calibration inherited, not independently refitted.']))
# Immutable scientific/review snapshot; communication and worker STATE remain mutable.
excluded={'MANIFEST.json','VERIFY.json','STATE.md','COMMUNICATION.json'}
files={}
for path in sorted(HERE.iterdir()):
    if path.is_file() and path.name not in excluded:
        files[path.name]=dict(bytes=path.stat().st_size,sha256=sha(path))
save('MANIFEST.json',dict(created_utc=utc(),files=files,
                         exclusions=sorted(excluded),note='Owned __pycache__ directories excluded; original freeze bytes preserved.'))
compact=dict(current_PI=pi,own_pinned_files=len(files),original_code_pins=len(code),
             terminal_report_word_count=len((HERE/'TERMINAL_REPORT.md').read_text().split()),
             timing_order=ordering,script_charged_bytes=tracked,total_charged=charged,peak_RSS=peak,
             retention_all_full_rank=all(p['full_rank'] for row in contrary['retention_sweep'] for g in row['groups'] for p in g['design']),
             common_probe_all_full_rank=all(p['full_rank'] for g in contrary['stationary_next_endpoint_groups'] for p in g['people']),
             common_probe_min_current_cell_n=min(p['min_current_cell_count'] for g in contrary['stationary_next_endpoint_groups'] for p in g['people']),
             prescribed_linear_parameters=read('PRESCRIPTION.json')['independent_linear_fit_at_saved_sigma'],
             warnings=[read(n) for n in ('NUMERICAL_WARNINGS.json','LATER_WARNINGS.json','AUDIT_WARNINGS.json')])
print(json.dumps(compact,indent=2))
