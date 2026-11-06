"""Pin saved sources and prepare the terminal record; no new science/network."""
import datetime, hashlib, json, pathlib, platform, resource, zipfile
P=pathlib.Path(__file__).resolve().parent
stamp=datetime.datetime.now(datetime.timezone.utc).isoformat()
acq=json.loads((P/'ACQUISITION.json').read_text())
listed={x['name']:x for x in json.loads((P/'SOURCE_CANDIDATES.json').read_text())['files']}
pins=[]
for r in acq['requests']:
    if r.get('status')!=200: continue
    b=(P/r['name']).read_bytes()
    digest=hashlib.sha256(b).hexdigest()
    assert digest==r['sha256'] and len(b)==r['bytes']
    if r['name'] in listed:
        assert digest==listed[r['name']]['sha256'] and len(b)==listed[r['name']]['size']
    pins.append({'name':r['name'],'url':r['url'],'retrieved_utc':r['time_utc'],
                 'bytes':len(b),'sha256':digest,'md5':r['md5'],
                 'osf_listing_pin_matches':r['name'] in listed})
code=[x for x in pins if x['name']=='code_v1.1.zip'][0]
assert code['md5']=='40d87e790193d38528b4ba0cecf23e8c'
manifest={'prepared_utc':stamp,'primary_source_families_inspected':1,
 'primary_publication':{'doi':'10.1038/s41586-023-06683-4','url':'https://www.nature.com/articles/s41586-023-06683-4','article_license':'CC-BY-4.0'},
 'data_node':{'id':'e2syt','doi':'10.17605/OSF.IO/E2SYT','public':True,'node_license':None,
              'external_data_license':'not established; article/code license not imputed',
              'raw_folder_id':'671a5286badd54a2128707e3','folder_total_items':678,'first_page_items_inspected':100,
              'osf_objects_current_version':'1 as listed; exact IDs/dates/checksums in cached listings'},
 'code':{'zenodo_record':'8312985','version':'v1.1','license':'GPL-3.0','executed':False},
 'source_pins':pins,'archive_digest_scope':'complete code ZIP; no bulk data archive acquired or hashed'}
(P/'SOURCE_MANIFEST.json').write_text(json.dumps(manifest,indent=2)+'\n')
first=json.loads((P/'FIRST_DATA_CHECK.json').read_text())
meta=json.loads((P/'METADATA_CHECK.json').read_text())
gate={'decision_utc':stamp,'deadline_utc':'2026-11-01T04:30:34.816Z','decision':'STOP_INCOMPLETE_CERTIFICATION',
 'passed':False,'early_real_calculation_executed_utc':first['executed_utc'],
 'event_traces_available':True,'nominal_zero_based_stimulation_frame_and_time_available':True,
 'independent_animal_linkage':'not explicitly certified for these recording paths; publication count/README are suggestive source-level support only',
 'event_pulse_durations':'not exported; protocol default 500 ms for WT and variable AFD series documented, not applied as observed per-event durations',
 'exact_2024_raw_export_preprocessing':'not certified; export writes current Signal.data and settings are not included',
 'artifact_controls':'primary descriptions inspected; matching raw control/event-quality objects not acquired',
 'data_license':'OSF explicit node_license null; external data license unestablished',
 'next_stage':'UNRUN; no evaluation-payload release, model fitting or summary substitution',
 'does_not_establish':['absence of metadata anywhere in full archive','invalid source data','absence or equivalence of state effects','forecast utility','global novelty']}
(P/'GATE.json').write_text(json.dumps(gate,indent=2)+'\n')
body=sum(r['bytes'] for r in acq['requests'])
local_peaks=[r.get('peak_rss_bytes',0) for r in acq['requests']]+[first['peak_rss_bytes'],meta['peak_rss_bytes'],resource.getrusage(resource.RUSAGE_SELF).ru_maxrss]
z=zipfile.ZipFile(P/'code_v1.1.zip')
res={'prepared_utc':stamp,'authorized_start_utc':'2026-11-01T04:10:34.816Z','source_gate_utc':'2026-11-01T04:30:34.816Z','total_deadline_utc':'2026-11-01T05:25:34.816Z',
 'limits':{'logical_public_operations':30,'ingress_bytes':50000000,'additional_scientific_read_decoded_hash_bytes':500000000,'peak_rss_bytes':1000000000,'scientific_processes':1,'numerical_threads':1},
 'public_operations':{'count':len(acq['requests'])+1,'source_search_connector_calls':1,'script_urlopen_attempts_including_failures':len(acq['requests']),
                      'definition':'one initiated public lookup/fetch; automatic redirect hops and provider-internal operations were not separately measured'},
 'ingress':{'measured_application_response_body_bytes':body,'search_connector_unknown_provider_transfer_reserve':1000000,
            'failed_dns_unknown_transfer_reserve':1000000,'failed_identifier_timeout_unknown_transfer_reserve':1000000,
            'charged_total_bytes':body+3000000,'provider_actual_bytes':'unknown; application read caps do not measure remote buffering/transport'},
 'additional_scientific_read_decoded_hash':{'charged_bytes':200000000,
   'basis':'conservative whole-task charge including acquisitions SHA256+MD5, all code ZIP scans/inflation, text/metadata reads, full first-table parsing and decoded values, repeated inspections and closeout hashes; exact cross-pass byte total not instrumented',
   'first_data_pass_known_source_read_bytes':first['this_pass_source_read_bytes'],
   'first_data_pass_known_float64_value_charge':first['this_pass_decoded_values_byte_charge'],
   'closeout_source_hash_read_bytes':sum(x['bytes'] for x in pins),
   'code_zip_total_uncompressed_member_bytes':sum(x.file_size for x in z.infolist())},
 'rss':{'maximum_measured_local_bytes':max(local_peaks),'provider_and_tool_host_peaks':'unknown','failed_local_acquisition_peaks':'recorded in ACQUISITION.json'},
 'execution':{'active_jobs':0,'numerical_models_or_threaded_libraries_used':False,'one_owner':True,
  'note':'standard-library processes were run sequentially; code ZIP and raw100 acquisition calls both yielded, but the retained ledger includes code before raw100, establishing the first acquisition ledger write before the second loaded it; no parallel numerical work',
  'python':platform.python_version(),'os':platform.system()},
 'failures':[{'kind':'DNS denial in sandbox','source':'osf_files.json initial attempt','body_bytes':0,'provider_transfer_unknown':True},
             {'kind':'identifier fetch timeout','source':'2_ds_name.txt first attempt','body_bytes':0,'provider_transfer_unknown':True,'retry':'one same-object retry succeeded'},
             {'kind':'pre-tool hook denial','source':'GitHub codeload URL','public_fetch_executed':False},
             {'kind':'pre-tool hook denials','source':'inline inspection, raw head, symlinked venv path, ordinary read composition/path checks','public_fetch_executed':False}],
 'exposure':{'record0':'entire 4454x114 GCaMP table including unlabeled columns and all five matching metadata vectors consumed/development-exposed',
             'records1_and2':'complete five-field metadata only; no GCaMP acquisition/decoding/scoring',
             'source_context':'whole paper HTML/text, complete v1.1 code ZIP, top-level OSF listing/node/wiki and first100 raw-folder metadata items exposed',
             'new_sealed_protected_data_access':False,'main_evaluation_scoring':False},
 'terminal_report':{'status':'not_yet_attempted; write delivery status in STATE after one send','target':'current registry PI verified 01a1954a-36b7-7191-80de-cc1cba0165c0'},
 'unrun_stages_file':'UNRUN.json'}
(P/'RESOURCES.json').write_text(json.dumps(res,indent=2)+'\n')
print(json.dumps({'gate':gate['decision'],'public_operations':res['public_operations']['count'],
                  'application_body_bytes':body,'charged_ingress':body+3000000,'charged_additional_read':200000000,
                  'measured_peak_rss':max(local_peaks),'source_objects_verified':len(pins),'active_jobs':0,'time':stamp},indent=2))
