"""Record-only closeout: own-path pins, resource/exposure/failure accounting."""
import datetime, hashlib, json, pathlib, resource
p=pathlib.Path(__file__).resolve().parent
acq=json.loads((p/'ACQUISITION.json').read_text())
known=sum(x.get('bytes_read',0) for x in acq)
provider_allowance=14000000
failed_http_allowance=750000
redirect_allowance=1000000
inputs={}
for x in acq:
    if x.get('saved'):
        inputs[x['name']]={'bytes':x['bytes_read'],'sha256':x['sha256'],'url':x['url'],'final_url':x.get('final_url'),'range':x.get('range')}
pin={}
for f in sorted(p.glob('*.py')):
    raw=f.read_bytes();pin[f.name]={'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()}
peak=max([x.get('process_peak_rss_bytes_macos',0) for x in acq]+[
 json.loads((p/n).read_text()).get('process_peak_rss_bytes_macos',0) for n in ('FIRST_DATA_CHECK.json','SOCIAL_TABLE_TYPED.json')])
resources={'recorded_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
 'hard_bounds':{'initial_native_turn_utc':'2026-11-02T22:36:28Z','first_original_due':'2026-11-02T23:01:28Z','source_gate_due':'2026-11-02T23:16:28Z','freeze_or_close_due':'2026-11-02T23:31:28Z','hard_deadline':'2026-11-03T00:36:28Z','ingress_bytes':50000000,'read_hash_decode_bytes':600000000,'peak_rss_bytes':800000000,'public_operations':40,'empirical_families':2,'total_primary_families':3,'scientific_processes':1,'numerical_threads':1},
 'public_operations':{'top_level_calls':22,'counting_queries_separately':23,'conservative_charged_operations':26,
 'extra_allowance':'Three operations for observed/uncertified redirects or provider routing. Exact provider subrequests unavailable; this is a conservative booking, not complete network metering.'},
 'ingress':{'known_local_application_response_bytes':known,'provider_allowance_bytes':provider_allowance,'failed_http_allowance_bytes':failed_http_allowance,'redirect_allowance_bytes':redirect_allowance,'conservative_charged_bytes':known+provider_allowance+failed_http_allowance+redirect_allowance,'note':'Includes failed DNS250KB and failed404500KB budgets. Web/GitHub actual traffic and HTTP-error bodies are unavailable. No whole49.9MBarchive acquisition.'},
 'separate_additional_read_hash_decode':{'conservative_charged_bytes':350000000,
 'components_allowance':{'original_CSV_acquisition_hash_decode_and_three_first_check_runs_plus_source_audits':110000000,'OOXML_acquisition_typed_parse_failed_and_successful_ratio_checks':10000000,'source_context_metadata_scripts_logs_pins_closeout':30000000,'stdlib_imports_runtime_toolhost_and_failed_pass_reserve':200000000},
 'note':'Booking allowance for repeated reads/hash/decode, not measured physicalIO. Unknown imports/runtime/provider/kernel work is not certified by this allowance.'},
 'largest_measured_scientific_process_peak_rss_bytes_macos':peak,
 'unmeasured_peaks':['initial first_data_check assertion failure before resource serialization','initial social_gate assertion failure','provider/toolhost/wrapper process internals'],
 'physical_io_and_runtime':'Unmetered provider/toolhost/kernel IO and internal peaks remain unknown. No total-IO or all-process-memory compliance certification.',
 'parallelism':'All source/scientific subprocesses run sequentially; only stdlib code, no numerical library threads/GPU/new dependencies.',
 'jobs_remaining':0,'purchases_contacts_publication_new_human_experiments':0,
 'source_responses':inputs,'code_pins':pin}
(p/'RESOURCES.json').write_text(json.dumps(resources,indent=2)+'\n')
print(json.dumps({k:resources[k] for k in ('public_operations','ingress','largest_measured_scientific_process_peak_rss_bytes_macos','jobs_remaining')},indent=2))
