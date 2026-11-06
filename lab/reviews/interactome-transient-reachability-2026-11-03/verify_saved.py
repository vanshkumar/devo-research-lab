"""Record-only closeout validation/pins; no numerical library or ODE import."""
from pathlib import Path
import hashlib
import json
import datetime
import ast
import time
import resource
p=Path(__file__).resolve().parent
root=p.parents[2]
author=root/'lab/tasks/interactome-transient-reachability-2026-11-03'
start=time.monotonic()
def digest(path):
    h=hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda:f.read(1024*1024),b''):h.update(chunk)
    return h.hexdigest()
def read(name):return json.loads((p/name).read_text())
for name in ('BRIEF.md','REVIEW.md','README.md','STATE.md','RESOURCES.json','NATIVE_EXECUTION.json','FAILURES.md','EXPOSURE.md','PROPOSED_LEARNINGS.md','COMMUNICATION_REPORT.md'):
    assert (p/name).is_file(),name
freeze=read('CONTRARY_FREEZE.json')
assert all(digest(p/name)==h for name,h in freeze['sha256'].items())
for name,h in json.loads((author/'FREEZE.json').read_text())['sha256'].items():assert digest(author/name)==h
ref=read('REFERENCE.json');audit=read('AUDIT.json');contrary=read('CONTRARY.json');obs=read('CONTRARY_OBSERVATIONS.json');num=read('NUMERICAL_AUDIT.json');res=read('RESOURCES.json')
assert ref['full_states']==558 and ref['full_neurons']==279
assert ref['finished_utc']<'2026-11-03T06:56:22Z'
assert freeze['frozen_at_utc']<contrary['finished_utc'] and freeze['frozen_at_utc']<'2026-11-03T07:06:22Z'
assert audit['frozen_hashes_match'] and all(not x['material_retention'] and not x['material_challenge'] for x in audit['saved_raw_independent_scores'].values())
assert contrary['both_initializations_material_candidate'] and contrary['scientific_protocol_revisions']==0
assert obs['new_ODE_executions']==0 and obs['frozen_bytes_unchanged']
assert num['finite_all'] and num['matrix_relative_maxabs']<1e-8
assert res['process']['largest_successful_measured_rss_bytes_macos']<res['process']['rss_cap_bytes']
assert res['process']['conservative_local_process_booking_seconds']<res['process']['cap_actual_scientific_seconds']
assert res['public_operations']['new']==res['ingress']['new_bytes']==res['new_dependencies']==0
report_words=len((p/'COMMUNICATION_REPORT.md').read_text().split())
assert report_words<=400,report_words
for script in p.glob('*.py'):ast.parse(script.read_text(),filename=str(script))
names=['independent_model.py','reference.py','inspect_inputs.py','audit.py','freeze_contrary.py','contrary.py','numerical_audit.py','contrary_observations.py','verify_saved.py',
       'REFERENCE.json','INPUT_INSPECTION.json','AUDIT.json','CONTRARY_PLAN.md','CONTRARY_FREEZE.json','CONTRARY.json','CONTRARY_OBSERVATIONS.json','NUMERICAL_AUDIT.json','REVIEW.md','README.md','EXPOSURE.md','PROPOSED_LEARNINGS.md']
names+=sorted(x.name for x in p.glob('*.npz'))
inventory={name:{'bytes':(p/name).stat().st_size,'sha256':digest(p/name)} for name in names}
pins=p/'SCIENTIFIC_PINS.json'
if pins.exists():assert json.loads(pins.read_text())==inventory,'Existing scientific pins changed'
else:pins.write_text(json.dumps(inventory,indent=2)+'\n')
receipt={'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
         'checks_passed':True,'new_ODE_or_library_imports':0,'files_pinned':len(inventory),
         'raw_npz_files_pinned':len(list(p.glob('*.npz'))),'scientific_pin_file_bytes_sum':sum(x['bytes'] for x in inventory.values()),
         'contrary_and_author_frozen_bytes_match':True,'terminal_report_words':report_words,
         'native_science_exits':'all0; verified earlier actual tool returns, not inferred from this check',
         'jobs_remaining':0,'elapsed_s':time.monotonic()-start,'rss_bytes_macos':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss}
(p/'FINAL_VERIFICATION.json').write_text(json.dumps(receipt,indent=2)+'\n')
print(json.dumps(receipt,indent=2))
