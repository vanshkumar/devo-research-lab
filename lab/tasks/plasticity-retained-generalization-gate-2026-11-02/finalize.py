"""Summarize own authorized scientific outputs and pin small reproduction files.

No new science, public request, payload acquisition or model run.
"""
import collections
import hashlib
import json
from pathlib import Path
import resource
import sys
import time

started=time.perf_counter()
here=Path(__file__).resolve().parent
root=here.parents[2]
read_bytes=0
def get(path):
    global read_bytes
    raw=path.read_bytes()
    read_bytes+=len(raw)
    return raw
def load(path): return json.loads(get(path))
f=load(here/'FEASIBILITY.json')
r=load(here/'REFERENCE.json')
head=load(here/'DATA_HEAD.json')
data=load(here/'DATA_GET.json')
inv=load(here/'INVENTORY_39.json')
ops=load(here/'PUBLIC_OPERATIONS.json')
previous_inv=load(root/'lab/tasks/plasticity-retention-source-benchmark-2026-11-02/INVENTORY.json')
assert f['status']=='PASS_EXECUTABLE_FEASIBILITY_ONLY' and r['status']=='PASS_FULL_256_UPDATE_EXPLICIT_REPLAY'
assert f['learning_updates']==256 and len(f['initial_test']['logits'])==64 and f['tasks_completed']==0
assert f['architecture']==[784,2000,2000,2000,10] and f['checks']['parameter_count']==9594010
assert ops['count']==20 and head['public_operations']==4 and data['public_operations']==4
assert data['application_ingress_bytes']==11594722
summary={k:f[k] for k in ('status','utc_finished','implementation','seed','step_size','architecture','learning_updates','tasks_completed','published_updates_per_arm','learning_loop_seconds_for_255_updates','total_seconds_after_imports','max_rss_bytes_macos','checkpoint','numpy_version','threadpools','exposure','main_campaign','long_history_cost')}
summary['initial_test']={k:v for k,v in f['initial_test'].items() if k not in ('logits','probabilities','per_example_loss')}
summary['final_test']={k:v for k,v in f['final_test'].items() if k not in ('logits','probabilities','per_example_loss')}
summary['checks']=f['checks']
summary['original_warning_count']=len(f['warnings'])
summary['original_warning_counts']=dict(collections.Counter(x['message'] for x in f['warnings']))
summary['full_reference']={k:r[k] for k in ('status','initial_64x10_logit_max_gap','final_64x10_logit_max_gap','all_256_online_loss_max_gap','all_9594010_parameters_max_gap','new_warnings','full_reference_learning_seconds','max_rss_bytes_macos','all_60000_train_vs_64_test_exact_image_hash_overlap')}
(here/'FEASIBILITY_SUMMARY.json').write_text(json.dumps(summary,indent=2)+'\n')
license_pin=next(x for x in previous_inv['source_files'] if x['path']=='LICENSE')
manifest={'upstream':{'repository':'shibhansh/loss-of-plasticity','commit':'3138c5556859e0e2918d40f113b40699b6575cfa','root_tree':'803541478812c901d267bd5acd069be20fb824f9','code_license':'MIT; inherited previously verified inventory pin, no new license payload read',
                      'license_pin':license_pin,'license_existing_path':'lab/tasks/plasticity-retention-source-benchmark-2026-11-02/vendor/LICENSE',
                      'provider_reconstructed_files':r['source_manifest'],
                      'prior_bp_source_path':'lab/tasks/plasticity-retention-source-benchmark-2026-11-02/vendor/lop/algos/bp.py',
                      'prior_requirements_path':'lab/tasks/plasticity-retention-protocol-calibration-2026-11-02/vendor/requirements.txt',
                      'source_tree_path':'lab/tasks/plasticity-retention-source-benchmark-2026-11-02/SOURCE_TREE.json'},
          'runtime':{'python':inv['python'],'executable':inv['executable'],'numpy':f['numpy_version'],
                     'numpy_path':f['numpy_path'],'numpy_license':'BSD-style identity from existing package conventions; full bundled license not reverified in this gate',
                     'upstream_numpy_requirement':'1.24.1','actual_numpy':'2.0.2; independent source-equation implementation',
                     'upstream_torch_requirement':'2.1.0','actual_torch':'absent; author execution UNRUN','installations':0,
                     'thread_limits':f['requested_threads'],'runtime_native_thread_count':'UNCERTIFIED; no threadpoolctl enumeration'},
          'data':{'objects':data['objects'],'compressed_bytes':data['application_ingress_bytes'],
                  'license':'UNVERIFIED in bounded gate; code MIT and public mirror do not certify external data license',
                  'provenance':'canonical MNIST IDX objects on public OSSCI mirror; sizes/MD5 match HEAD ETags and declared canonical checksums; original loader selects torchvision MNIST'},
          'large_generated_checkpoint':f['checkpoint'],
          'files':[]}
for path in sorted(here.rglob('*')):
    if not path.is_file() or 'data' in path.relative_to(here).parts or path.name in ('FEASIBILITY_CHECKPOINT.npz','REPRODUCTION_MANIFEST.json','RESOURCES.json','AUDIT.json','STATE.md','TERMINAL_REPORT.md'): continue
    raw=get(path)
    manifest['files'].append({'path':path.relative_to(here).as_posix(),'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()})
(here/'REPRODUCTION_MANIFEST.json').write_text(json.dumps(manifest,indent=2)+'\n')
explicit=f['explicit_input_read_bytes']+r['explicit_file_read_bytes']+inv['source_read_bytes']+read_bytes
resources={
 'status':'CLOSED_SCOPED_GATE_WITH_EXECUTABLE_SHORT_FEASIBILITY',
 'native_anchor_utc':'2026-11-03T03:30:32Z',
 'all_evidence_generating_programs_complete_utc':'2026-11-03T03:38:27Z',
 'scientific_gates_utc':{'prior':'03:50:32Z','original_learning_reference':'04:05:32Z','protocol_or_CLOSE':'04:15:32Z','hard':'04:40:32Z'},
 'public_operations_new':20,'public_operations_cap':20,'screened_programs':2,'public_data_exact_ingress_bytes':11594722,
 'provider_code_pages_queries_headers_failures_allowance_bytes':50000000,'new_ingress_charge_bytes':61594722,
 'new_ingress_cap_bytes':250000000,'actual_ingress_and_cap_compliance':'UNCERTIFIED; provider redirects/internal requests/physical I/O unknown',
 'additional_read_hash_decode':{'explicit_file_read_bytes_recorded_across_owned_programs':explicit,
                               'gzip_decode_bytes_two_passes':f['gzip_inflated_decode_bytes']+r['gzip_inflated_decode_bytes'],
                               'checkpoint_array_decode_bytes_reference':f['checks']['parameter_bytes'],
                               'decoded_image_fingerprint_bytes':r['additional_decoded_image_fingerprint_bytes'],
                               'conservative_separate_charge_bytes':900000000,'cap_bytes':1000000000,
                               'allowance_includes':'all notes/source/report/context reads, provider text handling, imports/native dependencies, hashes/decodes, acquisition in-memory hash passes, failed context reads, generated/checkpoint/output handling and final bookkeeping',
                               'physical_IO':'UNKNOWN; not complete observed physical-byte certification'},
 'local_processes':[{'name':'orient.py','native_exit':0,'script_seconds':inv['seconds'],'max_rss_bytes':inv['max_rss_bytes_macos']},
                    {'name':'acquire_mnist.py head','native_exit':0,'script_seconds':head['seconds'],'max_rss_bytes':head['max_rss_bytes_macos']},
                    {'name':'acquire_mnist.py get','native_exit':0,'native_session':93788,'script_seconds':data['seconds'],'max_rss_bytes':data['max_rss_bytes_macos']},
                    {'name':'feasibility.py','native_exit':0,'native_session':48447,'after_import_seconds':f['total_seconds_after_imports'],'max_rss_bytes':f['max_rss_bytes_macos']},
                    {'name':'verify_reference.py','native_exit':0,'native_session':61254,'after_import_seconds':r['total_seconds_after_imports'],'max_rss_bytes':r['max_rss_bytes_macos']}],
 'actual_local_science_script_seconds_recorded':inv['seconds']+head['seconds']+data['seconds']+f['total_seconds_after_imports']+r['total_seconds_after_imports'],
 'runtime_accounting':'All five evidence-generating programs completed within the 475-second anchor-to-final-output interval, one process at a time. Conservative 500-second charge includes startup/import/final bookkeeping allowance; exact complete process startup wall not separately measured.',
 'conservative_local_scientific_process_seconds_charge':500,'local_scientific_process_seconds_cap':900,
 'max_measured_science_RSS_bytes':max(f['max_rss_bytes_macos'],r['max_rss_bytes_macos'],head['max_rss_bytes_macos'],data['max_rss_bytes_macos'],inv['max_rss_bytes_macos']),
 'RSS_cap_bytes':1000000000,'provider_runtime_toolhost_peaks':'UNKNOWN',
 'processes_at_once':1,'requested_threads':1,'OS_native_thread_count':'UNCERTIFIED; env limits set, enumeration unavailable',
 'failed_scientific_commands':0,'method_revisions':0,
 'closeout_patch_failure':'One combined DELETE+ADD STATE patch was rejected in verification before any mutation; corrected to direct UPDATE, no scientific rerun.',
 'failures_and_limitations':['Broad filename inventory denied for raw/payload browsing roots; no output/no repeated broad inventory.',
                            'Ordinary direct LICENSE cat denied by format guard; use previously verified inventory MIT pin, no bypass/acquisition.',
                            'Ordinary wc of large FEASIBILITY.json denied by context size guard; small derived FEASIBILITY_SUMMARY.json is the PI-facing record.',
                            'PMC recaptcha, guessed arXivv4 404, Nature inaccessible nonretryable redirect.',
                            'Five of six provider-normalized source copies fail Git blob identity; standard BP config passes. No original-byte repair.',
                            '5400 matmul warnings preserved; full explicit 256-update replay agrees without warnings; backend cause unestablished.',
                            'Data and full local dependency licenses not independently reverified; missing Torch is not evidence of compute impossibility.',
                            'No full-history measured cost or qualifying source-linked checkpoint; all main claims UNRUN.'],
 'exposure':f['exposure'],
 'new_training_examples_used':256,'new_heldout_test_examples_scored':64,
 'protected_old_payloads_fits_target_rescores':0,'dependencies_installed':0,'paid_compute':0,'native_goal_edits':0,'shared_record_edits':0,
 'prior_additive':ops['prior_additive'],
 'prior_failures_and_qualifications':'All prior source-copy, beta-default/capacity, method revisions, storage coverage, Torch intent, teacher t7 and runtime/physical-IO unknowns survive; no source/exposure reset.',
 'jobs':0,'scientific_goal':'UNFINISHED; no pause/completion asserted','terminal_report':'saved separately; disposition in STATE'}
(here/'RESOURCES.json').write_text(json.dumps(resources,indent=2)+'\n')
audit={'status':'PASS_SAVED_OUTPUT_AND_PIN_AUDIT','science_rerun':False,'public_operations':20,
       'source_files':len(r['source_manifest']),'source_byte_certified':sum(x['byte_certified'] for x in r['source_manifest']),
       'data_objects':len(data['objects']),'data_ingress_bytes':data['application_ingress_bytes'],
       'checks':{'model_dimensions':True,'parameter_count':True,'short_learning':True,'full_explicit_replay':True,'all_test_images_unseen':True},
       'bookkeeping_read_bytes':read_bytes,'seconds':time.perf_counter()-started,
       'bookkeeping_max_RSS_bytes_macos':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
       'utc_finished':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime())}
(here/'AUDIT.json').write_text(json.dumps(audit,indent=2)+'\n')
print(json.dumps(audit,indent=2))
