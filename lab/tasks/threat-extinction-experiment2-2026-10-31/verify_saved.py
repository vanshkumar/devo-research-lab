"""Read-only reconstruction of saved forecast losses and source/freeze pins."""
import collections
import datetime as dt
import hashlib
import json
import pathlib
import resource
import sys
import numpy as np

ROOT=pathlib.Path(__file__).resolve().parent
read_bytes=0
def read(name):
    global read_bytes
    b=(ROOT/name).read_bytes()
    read_bytes+=len(b)
    return b
def obj(name):
    return json.loads(read(name))

out={'utc':dt.datetime.now(dt.timezone.utc).isoformat(),'source_pins':{},'main_freeze':{},'contrary_freeze':{}}
listing=obj('sources/files.json')
archive=next(f for f in listing['data'] if f['attributes']['name'].endswith('.zip'))
b=read('sources/experiment2.zip')
assert hashlib.sha256(b).hexdigest()==archive['attributes']['extra']['hashes']['sha256']
assert hashlib.md5(b).hexdigest()==archive['attributes']['extra']['hashes']['md5']
assert len(b)==archive['attributes']['size']
out['source_pins']={'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest(),'md5':hashlib.md5(b).hexdigest(),'source_version':archive['attributes']['current_version']}
for filename,key in [('FREEZE.json','main_freeze'),('CONTRARY_FREEZE.json','contrary_freeze')]:
    frozen=obj(filename)
    for name,h in frozen['pins'].items():
        out[key][name]=hashlib.sha256(read(name)).hexdigest()==h
    assert all(out[key].values())
evaluation=obj('EVALUATION.json')['results']
rows=obj('FORECASTS.json')
grouped=collections.defaultdict(list)
for row in rows:
    grouped[(row['comparison'],row['id'])].append(row)
max_error=0.
losses=0
for (key,participant),records in grouped.items():
    original=next(v for v in evaluation[key]['per_participant_losses'] if v['id']==participant)
    models=[k for k in original if k!='id']
    for model in models:
        reconstructed=sum((r['observed']-r[model])**2 for r in records)/len(records)
        error=abs(reconstructed-original[model])
        max_error=max(max_error,error)
        assert error<1e-12
        losses+=1
out['main_reconstructed_individual_losses']=losses
out['main_forecast_rows']=len(rows)
out['main_loss_max_abs_error']=max_error
contrary=obj('CONTRARY.json')['results']
crows=obj('CONTRARY_FORECASTS.json')
cg=collections.defaultdict(list)
for r in crows:
    cg[(r['comparison'],r['id'])].append(r)
cmax=0.
for (key,participant),records in cg.items():
    original=next(v for v in contrary[key]['per_participant'] if v['id']==participant)
    for model in ['static','common']:
        reconstructed=sum((r['observed']-r[model])**2 for r in records)/len(records)
        cmax=max(cmax,abs(reconstructed-original[model+'_loss']))
        assert abs(reconstructed-original[model+'_loss'])<1e-12
out['contrary_reconstructed_individual_losses']=len(cg)*2
out['contrary_forecast_rows']=len(crows)
out['contrary_loss_max_abs_error']=cmax
inclusion=obj('DEVELOPMENT_INCLUSION.json')+obj('EVALUATION_INCLUSION.json')
out['excluded']= [r for r in inclusion if not r['included']]
out['all_zero_extinction_units']=[{'id':r['id'],'channel':r['channel']} for r in inclusion if r.get('zero_extinction_features')==18]
out['environment']={'python':sys.version,'numpy':np.__version__,'platform':sys.platform}
out['measured_scientific_bytes_this_command']=read_bytes
out['read_charge_bytes']=5000000
out['peak_rss_bytes']=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
out['owned_scientific_jobs_remaining']=0
(ROOT/'FINAL_VERIFICATION.json').write_text(json.dumps(out,indent=2)+'\n')
print(json.dumps(out,indent=2))
