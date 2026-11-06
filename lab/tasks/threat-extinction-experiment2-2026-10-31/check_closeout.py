import datetime as dt
import json
import pathlib
import resource

ROOT=pathlib.Path(__file__).resolve().parent
resources=json.loads((ROOT/'RESOURCES.json').read_text())
manifest=json.loads((ROOT/'SOURCE_MANIFEST.json').read_text())
ops=manifest['five_public_operations']
assert len(ops)==resources['public_operations_charged']==5
assert sum(o['body_bytes'] for o in ops)==resources['ingress_charged_bytes']==128448
assert sum(c['bytes'] for c in resources['scientific_read_charge_components'])==resources['additional_scientific_read_charged_bytes']==97000000
assert resources['additional_scientific_read_charged_bytes']<=resources['additional_scientific_read_limit_bytes']
assert resources['largest_measured_local_peak_rss_bytes']<=resources['local_peak_rss_limit_bytes']
for name in ['RESULT.md','README.md','STATE.md','RESOURCES.json','SOURCE_CERTIFICATION.json',
             'FREEZE.json','EVALUATION.json','CONTROLS.json','CONTRARY.json','FINAL_VERIFICATION.json',
             'PROPOSED_LEARNING.md','TERMINAL_REPORT.md']:
    assert (ROOT/name).is_file(),name
report=(ROOT/'TERMINAL_REPORT.md').read_text()
assert len(report.split())<=400
registry=json.loads((ROOT.parent.parent/'registry.json').read_text())
current_pi=registry['pi']['thread_id']
assert current_pi=='01a194d5-b47a-7780-a5b9-d32abf3183f2'
now=dt.datetime.now(dt.timezone.utc)
assert now<dt.datetime.fromisoformat(resources['hard_deadline_utc'].replace('Z','+00:00'))
out={'utc':now.isoformat(),'current_registry_pi':current_pi,'terminal_report_words_space_delimited':len(report.split()),
     'resource_totals_consistent':True,'required_artifacts_present':True,'within_deadline':True,
     'jobs_remaining':0,'peak_rss_this_metadata_check_bytes':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss}
(ROOT/'CLOSEOUT_CHECK.json').write_text(json.dumps(out,indent=2)+'\n')
print(json.dumps(out,indent=2))
