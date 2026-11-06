"""Independent reductions of the actual common-prefix-state pilot summaries."""
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
start=time.monotonic();cpu=time.process_time();inputs=[]

def read(name):
    b=(SRC/name).read_bytes()
    inputs.append({'path':str((SRC/name).relative_to(ROOT)),'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest()})
    return json.loads(b)

data=read('COMMON_GENERATED_SCORES.json')
labs=read('DEVELOPED_CONDITIONAL.json')['labs']
results=[]
for h in ['200','500','1000','2000']:
    summary={}
    for model in ['common_growth','common_hybrid','gru']:
        summary[model]={}
        for metric in ['ratio_crps','equal_side_mae','joint']:
            values={s:v[model][h][metric] for s,v in data['per_animal'].items()}
            site={lab:st.mean(v for s,v in values.items() if labs[s]==lab) for lab in sorted(set(labs.values()))}
            summary[model][metric]={'equal_animal':st.mean(values.values()),'equal_site':st.mean(site.values())}
    comparisons={}
    for model in ['common_growth','common_hybrid']:
        comparisons[model]={}
        for metric in ['ratio_crps','equal_side_mae']:
            dv={s:v[model][h][metric]-v['gru'][h][metric] for s,v in data['per_animal'].items()}
            ds={lab:st.mean(v for s,v in dv.items() if labs[s]==lab) for lab in sorted(set(labs.values()))}
            assert len(ds)==9
            mean=st.mean(ds.values());sd=st.stdev(ds.values());se=sd/3
            am=st.mean(dv.values());asd=st.stdev(dv.values());ase=asd/8
            margin=.02 if metric=='equal_side_mae' else .1*summary['common_growth']['ratio_crps']['equal_site']
            z=st.NormalDist().inv_cdf(.975)+st.NormalDist().inv_cdf(.9)
            comparisons[model][metric]={'sign':'positive favors GRU','equal_animal':am,'equal_site':mean,
               'animal_t95':[am-1.998340542520741*ase,am+1.998340542520741*ase],
               'site_t95':[mean-2.306004135204166*se,mean+2.306004135204166*se],
               'site_sd':sd,'site_contrasts':ds,
               'material_margin_for_planning':margin,
               'normal_sites_for80pct_CI_inside_symmetric_margin_at_zero':math.ceil((z*sd/margin)**2),
               'normal_independent_animals_analogue':math.ceil((z*asd/margin)**2)}
    results.append({'horizon':int(h),'summary':summary,'GRU_advantage':comparisons})
checks=data['checks']
errors=[v[m]['first_policy_error'] for v in checks.values() for m in ['common_growth','common_hybrid','gru']]
assert max(errors)==0.
interaction={}
for metric,margin in [('ratio_crps',.01),('equal_side_mae',.02)]:
    dv={s:(v['common_growth']['2000'][metric]-v['gru']['2000'][metric])-(v['common_growth']['500'][metric]-v['gru']['500'][metric]) for s,v in data['per_animal'].items()}
    ds={lab:st.mean(v for s,v in dv.items() if labs[s]==lab) for lab in sorted(set(labs.values()))}
    mu=st.mean(ds.values());sd=st.stdev(ds.values());se=sd/3
    am=st.mean(dv.values());asd=st.stdev(dv.values());ase=asd/8
    z=st.NormalDist().inv_cdf(.975)+st.NormalDist().inv_cdf(.9)
    interaction[metric]={'definition':'GRU advantage over common_growth at cumulative2000 minus cumulative500, same original1000 prefix',
        'equal_site':mu,'site_t95':[mu-2.306004135204166*se,mu+2.306004135204166*se],
        'equal_animal':am,'animal_t95':[am-1.998340542520741*ase,am+1.998340542520741*ase],
        'site_sd':sd,'animal_sd':asd,'planning_margin':margin,
        'normal_sites_for80pct_CI_inside_symmetric_margin_at_zero':math.ceil((z*sd/margin)**2),
        'normal_independent_animals_analogue':math.ceil((z*asd/margin)**2),
        'limitation':'Existing one-prefix horizon contrast only; it supplies no evidence about an additional-calibration interaction.'}
out={'utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),'status':'postvalidation independent actual-pilot summary reduction',
     'results':results,'max_saved_first_policy_error':max(errors),
     'horizon_interaction_planning_sensitivity':interaction,
     'interpretation':'Common growth and hybrid use the same neural prefix estimator; this is incremental future-updater utility, not an end-to-end cheap ordinary-model comparison.',
     'limitations':['No independent reconstruction of actor updates or source fits in this investment review.',
         'Observed-site/animal t intervals omit shared source-fit uncertainty and are not arbitrary-new-lab inference.',
         'Default teacher support failures and conditional future opportunity boundaries remain.',
         'Normal zero-effect precision analogies are not a funded main study or new power guarantee.'],
     'resources':{'inputs':inputs,'explicit_read_bytes':sum(x['bytes'] for x in inputs),'cpu_seconds':time.process_time()-cpu,
                  'wall_seconds':time.monotonic()-start,'peak_rss_native_bytes_on_Mac':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
                  'original_row_reads':0,'physical_io_and_runtime_reads':'unknown'}}
(OUT/'COMMON_SUMMARY_CHECK.json').write_text(json.dumps(out,indent=2)+'\n')
print(json.dumps({'utc':out['utc'],'horizon_interaction_planning_sensitivity':interaction,'resources':out['resources']},indent=2))
