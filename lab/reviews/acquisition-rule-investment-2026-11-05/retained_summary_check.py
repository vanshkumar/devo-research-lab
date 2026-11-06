"""Independent reduction after recovery of the actual frozen strong growth law."""
import hashlib
import json
import math
from pathlib import Path
import resource
import statistics as st
import time

OUT=Path(__file__).resolve().parent;ROOT=OUT.parents[2]
SRC=ROOT/'lab/tasks/acquisition-rule-vs-tracker-2026-11-05'
start=time.monotonic();cpu=time.process_time();inputs=[]

def read(name):
    b=(SRC/name).read_bytes();inputs.append({'path':str((SRC/name).relative_to(ROOT)),'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest()})
    return json.loads(b)

data=read('RETAINED_GROWTH_SCORES_CORRECTED.json')
labs=read('DEVELOPED_CONDITIONAL.json')['labs']
author=read('RETAINED_REDUCTION.json')
animals=sorted(data['per_animal']);sites=sorted(set(labs.values()))
assert len(animals)==64 and len(sites)==9
results=[];errors=[]
for h in ['200','500','1000','2000']:
    summary={};contrasts={}
    for model in ['frozen_growth','common_hybrid','gru']:
        summary[model]={}
        for metric in ['ratio_crps','equal_side_mae','joint','count','omission_crps']:
            v={s:data['per_animal'][s][model][h][metric] for s in animals}
            bysite={lab:st.mean(v[s] for s in animals if labs[s]==lab) for lab in sites}
            summary[model][metric]={'equal_animal':st.mean(v.values()),'equal_site':st.mean(bysite.values())}
            errors.append(abs(st.mean(bysite.values())-author['summary'][model][h][metric]['equal_site']))
    for model in ['frozen_growth','common_hybrid']:
        contrasts[model]={}
        for metric in ['ratio_crps','equal_side_mae']:
            d={s:data['per_animal'][s][model][h][metric]-data['per_animal'][s]['gru'][h][metric] for s in animals}
            ds={lab:st.mean(d[s] for s in animals if labs[s]==lab) for lab in sites}
            mu=st.mean(ds.values());sd=st.stdev(ds.values());am=st.mean(d.values());asd=st.stdev(d.values())
            margin=.02 if metric=='equal_side_mae' else .1*summary['frozen_growth']['ratio_crps']['equal_site']
            z=st.NormalDist().inv_cdf(.975)+st.NormalDist().inv_cdf(.9)
            contrasts[model][metric]={'sign':'positive favors GRU','equal_animal':am,'equal_site':mu,
                 'animal_t95':[am-1.998340542520741*asd/8,am+1.998340542520741*asd/8],
                 'site_t95':[mu-2.306004135204166*sd/3,mu+2.306004135204166*sd/3],
                 'site_sd':sd,'animal_sd':asd,'site_contrasts':ds,
                 'planning_margin':margin,'normal_sites_for80pct_CI_inside_margin_at_zero':math.ceil((z*sd/margin)**2),
                 'normal_independent_animals_analogue':math.ceil((z*asd/margin)**2)}
            errors.append(abs(mu-author['gru_advantage'][model][h][metric]['equal_site']))
    results.append({'horizon':int(h),'summary':summary,'GRU_advantage':contrasts})
assert max(errors)<1e-12
interaction={}
for metric in ['ratio_crps','equal_side_mae']:
    d={s:(data['per_animal'][s]['frozen_growth']['2000'][metric]-data['per_animal'][s]['gru']['2000'][metric])-(data['per_animal'][s]['frozen_growth']['500'][metric]-data['per_animal'][s]['gru']['500'][metric]) for s in animals}
    ds=[st.mean(d[s] for s in animals if labs[s]==lab) for lab in sites]
    mu=st.mean(ds);se=st.stdev(ds)/3
    interaction[metric]={'definition':'2000-minus500 horizon effect in GRU advantage over recovered frozen growth, same original1000 prefix',
        'equal_site':mu,'site_t95':[mu-2.306004135204166*se,mu+2.306004135204166*se],
        'equal_animal':st.mean(d.values()),'site_sd':st.stdev(ds),'animal_sd':st.stdev(d.values()),
        'information_axis':'unmeasured; not a calibration-by-horizon interaction'}
out={'utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),'status':'independent reduction of actual recovered-reference pilot',
     'results':results,'horizon_planning_sensitivity':interaction,'max_author_reduction_error':max(errors),
     'reference_receipt':data['reference'],'target_correction':data['observation_target_correction'],
     'limitations':['Consumed fixed 64 animals/nine sites; t intervals are descriptive and omit neural source-fit uncertainty.',
       'Frozen growth is an end-to-end original prescription; common_hybrid retains neural prefix cost.',
       'All actors here share original donor omission law; this differs from the earlier warmed-filter experiment.',
       'Default-teacher and future-opportunity information qualifications remain; no additional-calibration test was run.'],
     'resources':{'inputs':inputs,'explicit_read_bytes':sum(x['bytes'] for x in inputs),'cpu_seconds':time.process_time()-cpu,
         'wall_seconds':time.monotonic()-start,'peak_rss_native_bytes_on_Mac':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
         'original_row_reads':0,'physical_io_and_runtime_reads':'unknown'}}
(OUT/'RETAINED_SUMMARY_CHECK.json').write_text(json.dumps(out,indent=2)+'\n')
print(json.dumps({'horizon2000':results[-1],'horizon_sensitivity':interaction,'max_author_reduction_error':max(errors),'resources':out['resources']},indent=2))
