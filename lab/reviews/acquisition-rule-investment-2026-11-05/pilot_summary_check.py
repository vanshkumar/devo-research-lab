"""Postvalidation independent reductions of saved author pilot summaries only."""
import collections
import hashlib
import json
import math
from pathlib import Path
import resource
import statistics as st
import time

OUT=Path(__file__).resolve().parent
ROOT=OUT.parents[2]
SRC=ROOT/'lab/tasks/acquisition-rule-vs-tracker-2026-11-05'
start=time.monotonic()
cpu=time.process_time()
inputs=[]

def read(name):
    data=(SRC/name).read_bytes()
    inputs.append({'path':str((SRC/name).relative_to(ROOT)),'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest()})
    return json.loads(data)

a=read('DEVELOPED_CONDITIONAL.json')
t=read('PREFIX_TEACHER_AUDIT.json')
animals=sorted(a['per_animal'])
assert set(animals)==set(t['evaluation'])
differences={s:a['per_animal'][s]['growth_track']['ternary_loss']-a['per_animal'][s]['gru']['ternary_loss'] for s in animals}
site_diff={lab:st.mean(differences[s] for s in animals if a['labs'][s]==lab) for lab in sorted(set(a['labs'].values()))}
assert abs(st.mean(site_diff.values())-(a['summary']['growth_track']['equal_site_ternary']-a['summary']['gru']['equal_site_ternary']))<1e-12
ns=len(site_diff)
assert ns==9
se=st.stdev(site_diff.values())/math.sqrt(ns)
counts=collections.defaultdict(collections.Counter)
passed=[]
for s,v in t['evaluation'].items():
    c=counts[a['labs'][s]]
    c['animals']+=1
    c['contrast_failures']+=v['outside']
    c['parameter_mismatch']+=v['parameter_mismatch']
    c['animals_any_failure']+=bool(v['outside'] or v['parameter_mismatch'])
    if not(v['outside'] or v['parameter_mismatch']):passed.append(s)
assert len(animals)==64 and len(passed)==53
out={
    'utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),
    'status':'postvalidation independent reduction of actual saved pilot summaries',
    'evaluation_interval':a['evaluation_interval'],
    'equal_site_tracker_minus_GRU_loss':st.mean(site_diff.values()),
    'descriptive_site_t95':[st.mean(site_diff.values())-2.306004135204166*se,st.mean(site_diff.values())+2.306004135204166*se],
    'animal_mean_tracker_minus_GRU_loss':st.mean(differences.values()),
    'animals_favoring_GRU':sum(d>0 for d in differences.values()),
    'sites_favoring_GRU':sum(d>0 for d in site_diff.values()),
    'site_differences':site_diff,
    'observation_diagnostics':{name:a['summary'][name]['blocks'] for name in ['growth_track','gru']},
    'teacher_site_disposition':{k:dict(v) for k,v in counts.items()},
    'teacher_pass_animals':len(passed),
    'teacher_pass_sites':len({a['labs'][s] for s in passed}),
    'teacher_pass_definition':'no observed future contrast-support or probabilityLeft mismatch',
    'limitations':['Fitting/selection window was expanded by PI amendment; this summary reduction does not independently reread its source payloads.',
                   'Teacher-pass filtering uses future inputs, drops one complete site, and is a developmental sensitivity rather than a prospective eligibility rule.',
                   'Conditional residual summaries do not certify long-horizon generated-history calibration.',
                   'Selected-site t interval is descriptive and omits source-fit uncertainty.'],
    'resources':{'inputs':inputs,'explicit_read_bytes':sum(v['bytes'] for v in inputs),
                 'cpu_seconds':time.process_time()-cpu,'wall_seconds':time.monotonic()-start,
                 'peak_rss_native_bytes_on_Mac':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
                 'original_row_reads':0,'physical_io_and_runtime_reads':'unknown'}}
(OUT/'PILOT_SUMMARY_CHECK.json').write_text(json.dumps(out,indent=2)+'\n')
print(json.dumps(out,indent=2))
