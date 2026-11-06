"""Metadata-only final pins/resources/PI check; no scientific rerun."""
import datetime as dt
import hashlib
import json
import pathlib
import resource
import sys

here=pathlib.Path(__file__).resolve().parent
root=here.parents[2]
registry=json.loads((root/'lab/registry.json').read_text())
now=dt.datetime.now(dt.timezone.utc)
assert now<dt.datetime.fromisoformat('2026-11-01T03:21:48.310+00:00')
res=json.loads((here/'RESOURCES.json').read_text())
assert sum(x['bytes'] for x in res['charge_components'])==res['additional_scientific_read_charged_bytes']==120000000
assert res['additional_scientific_read_charged_bytes']<=res['additional_scientific_read_limit_bytes']
assert res['jobs_at_finish']==0
res['closeout_metadata_utc']=now.isoformat()
res['current_registry_pi_at_closeout']=registry['pi']['thread_id']
res['closeout_metadata_peak_rss_bytes']=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
(here/'RESOURCES.json').write_text(json.dumps(res,indent=2)+'\n')
freeze=json.loads((here/'CONTRARY_FREEZE.json').read_text())
assert all(hashlib.sha256((here/n).read_bytes()).hexdigest()==h for n,h in freeze['pins'].items())
names=[p for p in here.iterdir() if p.is_file() and p.name not in ['STATE.md','COMMUNICATION_STATUS.json','OUTPUT_PINS.json']]
pins={p.name:{'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in sorted(names)}
out={'utc':now.isoformat(),'reviewer_thread_id':res['reviewer_thread_id'],
     'current_pi_thread_id':registry['pi']['thread_id'],'jobs':0,'wall_deadline_met':True,
     'python_for_metadata_script':sys.version,'pins':pins,
     'mutable_status_exclusions':['STATE.md','COMMUNICATION_STATUS.json'],
     'resource_charge_bytes':res['additional_scientific_read_charged_bytes']}
(here/'OUTPUT_PINS.json').write_text(json.dumps(out,indent=2)+'\n')
print(json.dumps({k:v for k,v in out.items() if k!='pins'},indent=2))
print('Stable output pins:',len(pins))
