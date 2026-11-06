"""Record-only hashes and native-failure receipts. NEVER parse participant rows."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import resource
import sys

R = Path(__file__).resolve().parent
def pin(path):
    b = path.read_bytes()
    return {'file':path.name,'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest(),
            'git_blob_sha1':hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest()}

sources = ['gureckis-cv.pdf','papers.html','Crossact_data.csv','source_README.md',
           'Crossact_codebook.csv','crossact_v1.html','crossact_v4.html',
           'source_LICENSE','crossact-test-v4.js','selection-learning-v4.js','SOURCE_TREE.json']
pins = {name:pin(R/name) for name in sources}
data_pin = pins['Crossact_data.csv']
assert data_pin['bytes'] == 4015641
assert data_pin['git_blob_sha1'] == '622d0e34305f7208ef0ec77a0dc6951add1a161c'

source_record = {'recorded_at_utc':datetime.now(timezone.utc).isoformat(),
    'original_data_blob_verified_from_downloaded_bytes':True,
    'crossact_tree_sha':'d390ff3a9716c7fb0a277f3d3a65ff821afa943c',
    'tree_is_not_claimed_to_be_a_commit_sha':True,
    'source_text_copy_qualification':'GitHub source text copied with normalized line endings and trailing blank lines; local SHA256 pins are not claims of byte identity to listed source Git blobs.',
    'pins':pins,
    'public_urls': ['https://gureckislab.org/publications/MarkantGureckisJEPGEN2013.pdf',
        'https://www.gureckislab.org/papers','https://todd.gureckislab.org/gureckis-cv.pdf',
        'https://github.com/mzettersten/crossAct','https://osf.io/udmvh/'],
    'osf_was_not_fetched':True,'paper_provider_bytes_and_original_pdf_hash':'unknown; web views only'}
(R/'SOURCE_PINS.json').write_text(json.dumps(source_record,indent=2)+'\n')

first = {'status':'CLOSED_PARTIAL_NATIVE_FAILURES_NO_QUALIFYING_MEASUREMENT',
    'qualifying_first_measurement_milestone':False,
    'successful_assignment_acquisition_common_probe_calculation':'UNRUN',
    'recorded_at_utc':datetime.now(timezone.utc).isoformat(),
    'actual_command':'.venv/bin/python lab/tasks/assigned-teacher-common-probe-2026-11-01/first_data_check.py',
    'runs':[{'native_exit_code':1,'tool_chunk_id':'95ad4b','failure':'AssertionError: 9 at assert len(learning) == 24, len(learning)',
             'raw_records_touched':'same first development person; no score saved','peak_rss_bytes':None,'read_charge_bytes':5000000},
            {'native_exit_code':1,'tool_chunk_id':'b99545','failure':"assert metadata['version'] == 'kids2B', metadata",
             'native_stdout':"DEVELOPMENT_METADATA_AND_COUNTS {'subject': 'Crossact1_p101', 'experiment_name': 'Experiment 2', 'version': 'kids2A', 'age_group': 'kids', 'ambiguity_condition': 'ambiguous'} {'fam-learning': 4, 'fam-selection': 2, 'fam-test': 4, 'learning': 9, 'selection': 4, 'test': 6}",
             'peak_rss_bytes':None,'read_charge_bytes':5000000}],
    'original_csv_pin':data_pin,
    'original_development_metadata':{'subject':'Crossact1_p101','experiment_name':'Experiment 2','version':'kids2A','age_group':'kids','ambiguity_condition':'ambiguous'},
    'original_development_phase_counts':{'fam-learning':4,'fam-selection':2,'fam-test':4,'learning':9,'selection':4,'test':6},
    'original_development_total_rows':29,
    'probe_correct_count':None,'assignment_independence':'UNCERTIFIED',
    'v3_actual_protocol':'listed in source tree, unacquired',
    'native_exit_zero_record_closeout_is_not_a_scientific_milestone':True,
    'exposure':{'whole_original_csv_acquired_and_hashed_bytes':4015641,
       'same_development_person_rows_csv_tokenized_each_failed_pass':29,
       'following_person_first_row_csv_tokenized_each_failed_pass':1,
       'following_response_values':'not interpreted/rendered/scored; exact identifier not reported by failed runs',
       'development_response_and_auxiliary_values':'encountered in CSV tokenization; development-exposed, no response score computed',
       'other_response_scores_aggregates_or_whole_csv_tokenization':'UNRUN'},
    'unrun':['assignment-acquisition-probe join','independent teacher allocation certification','source/evaluation split','main freeze','model fit','forecast score','calibration controls','independent scientific review'],
    'native_failed_run_times':'exact times not saved; first before14:27:23Z clock, second after that clock; record-only closeout time is separate'}
(R/'FIRST_DATA_CHECK.json').write_text(json.dumps(first,indent=2)+'\n')

ops = json.loads((R/'PUBLIC_OPERATIONS.json').read_text())
known_native_ingress = 263726+1279920+4015641
known_connector_small_bodies = 3163+20124+12275+20488+1068+12350+11138
tree_body_bytes = 115559
known_body_bytes = known_native_ingress+known_connector_small_bodies+tree_body_bytes
resources = {'recorded_at_utc':datetime.now(timezone.utc).isoformat(),
    'caps':{'public_operations':25,'ingress_bytes':25000000,'additional_read_hash_decode_bytes':250000000,'peak_rss_bytes':800000000,'scientific_processes':1,'numerical_threads':1},
    'public_attempt_slots':ops['attempt_slots'],'conservative_operation_charge':ops['conservative_public_operation_charge'],
    'operation_compliance':ops['compliance'],
    'known_native_download_body_bytes':known_native_ingress,
    'known_small_connector_body_bytes':known_connector_small_bodies,
    'known_tree_body_bytes':tree_body_bytes,'known_body_bytes_total':known_body_bytes,
    'additional_discovery_provider_failure_ingress_allowance_bytes':15000000,
    'charged_ingress_allowance_bytes':known_body_bytes+15000000,
    'exact_provider_network_ingress':'unknown; allowance is a conservative charge, not a measured upper bound or traffic certificate',
    'read_hash_decode_charge_bytes':80000000,
    'read_charge_components':{'context_runtime_final_hash_record_work_allowance':40000000,'two_failed_original_data_passes':10000000,'source_inspection_and_other_reads_margin':30000000},
    'exact_failed_prefix_read_and_physical_io_bytes':'unknown',
    'largest_measured_source_link_script_peak_rss_bytes':11550720,
    'record_only_peak_rss_bytes':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
    'failed_original_check_peaks_and_curl_web_connector_peaks':'unknown; do not substitute the record-only peak for science/acquisition peak',
    'overall_memory_cap_compliance':'uncertified for unmeasured passes',
    'science_process_concurrency':1,'numerical_threads':1,'new_dependencies':0,'active_jobs':0,
    'fixed_start_utc':'2026-11-01T14:14:00Z','first_data_deadline_utc':'2026-11-01T14:34:00Z',
    'source_design_deadline_utc':'2026-11-01T14:44:00Z','hard_stop_utc':'2026-11-01T15:14:00Z',
    'stop_reason':'conservative public-operation exhaustion/overage; no qualified original assignment-acquisition-common-probe join',
    'scientific_work_stopped_at_source_limit':True,
    'python':sys.version,'native_failed_science_exits':[1,1],
    'record_only_exit_zero_not_a_passed_measurement':True}
(R/'RESOURCES.json').write_text(json.dumps(resources,indent=2)+'\n')
artifact_names = ['DESIGN.md','RESULT.md','STATE.md','README.md','PROPOSED_LEARNING.md','FAILURES.md',
    'PUBLIC_OPERATIONS.json','FIRST_DATA_CHECK.json','SOURCE_PINS.json','RESOURCES.json','first_data_check.py','inspect_source_link.py','record_closeout.py']
artifacts={name:pin(R/name) for name in artifact_names}
audit={'recorded_at_utc':datetime.now(timezone.utc).isoformat(),'kind':'RECORD_ONLY_CLOSED_SOURCE_GATE',
    'actual_source_data_blob_match':True,'qualifying_measurement_pass':False,
    'main_forecast_executed':False,'active_jobs':0,'artifact_pins':artifacts}
(R/'FINAL_AUDIT.json').write_text(json.dumps(audit,indent=2)+'\n')
print(json.dumps({'record_only':True,'original_csv_pin':data_pin,'native_science_exits':[1,1],
    'qualifying_measurement_pass':False,'public_charge':resources['conservative_operation_charge'],
    'ingress_allowance':resources['charged_ingress_allowance_bytes'],'read_charge':80000000,
    'record_only_peak_rss':resources['record_only_peak_rss_bytes'],'active_jobs':0,
    'recorded_at_utc':audit['recorded_at_utc']},indent=2))
