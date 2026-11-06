"""Independent precision assessment from permitted historical score summaries."""
import csv
import hashlib
import io
import json
import math
from pathlib import Path
import resource
import statistics as st
import time

OUT=Path(__file__).resolve().parent
ROOT=OUT.parents[2]
TAB=ROOT/'campaigns/learning_rule_transport_2026-10-28/tables'
inputs=[]
start=time.monotonic()
cpu=time.process_time()

def read_table(name):
    b=(TAB/name).read_bytes()
    inputs.append({'path':str((TAB/name).relative_to(ROOT)), 'bytes':len(b), 'sha256':hashlib.sha256(b).hexdigest()})
    return list(csv.DictReader(io.StringIO(b.decode())))

rnn=read_table('rnn_challenge_individual.csv')
ordinary=read_table('individual_scores.csv')
sites={r['subject']:r['lab'] for r in read_table('source_disposition.csv')}
z=st.NormalDist().inv_cdf(.975)+st.NormalDist().inv_cdf(.9)
results=[]
for horizon in [1000,3000]:
    a={r['subject']:r for r in rnn if r['arm']=='autonomous' and int(r['horizon'])==horizon and r['full_horizon']=='True'}
    b={r['subject']:r for r in ordinary if r['model']=='growth' and r['arm']=='autonomous' and int(r['horizon'])==horizon and r['full_horizon']=='True'}
    assert set(a)==set(b)
    subjects=sorted(a)
    for metric in ['crps','high_accuracy_mae']:
        growth=st.mean(float(b[s][metric]) for s in subjects)
        neural=st.mean(float(a[s][metric]) for s in subjects)
        d={s:float(b[s][metric])-float(a[s][metric]) for s in subjects}
        sd=st.stdev(d.values())
        n=len(d)
        # Critical values fixed for n=47 and n=40; site n=8 for both.
        critical={47:2.012895598919428,40:2.02269092003676}[n]
        sitevalues={site:st.mean(d[s] for s in subjects if sites[s]==site) for site in sorted({sites[s] for s in subjects})}
        sn=len(sitevalues)
        sitecritical={8:2.364624251592784,9:2.306004135204166}[sn]
        margin=.02 if metric=='high_accuracy_mae' else .1*growth
        site_sd=st.stdev(sitevalues.values())
        results.append({'future_opportunities':horizon,'metric':metric,'animals':n,'sites':sn,
            'growth':growth,'RNN':neural,'gain_growth_minus_RNN':st.mean(d.values()),'paired_animal_sd':sd,
            'animal_t95':[st.mean(d.values())-critical*sd/math.sqrt(n),st.mean(d.values())+critical*sd/math.sqrt(n)],
            'equal_site_mean':st.mean(sitevalues.values()),'paired_site_sd':site_sd,
            'site_t95':[st.mean(sitevalues.values())-sitecritical*site_sd/math.sqrt(sn),st.mean(sitevalues.values())+sitecritical*site_sd/math.sqrt(sn)],
            'precision_margin':margin,
            'normal_independent_animals_for80pct_CI_inside_margin_at_zero':math.ceil((z*sd/margin)**2),
            'normal_independent_sites_analogue':math.ceil((z*site_sd/margin)**2)})

out={'utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),'status':'historical developmental planning sensitivity',
     'results':results,'limitations':['Not a new tracker result or new-horizon power calculation.',
     'Scores preserve original expected-ratio/marginal target; no count-pooled replacement.',
     'Selected site intervals are descriptive; source-fit and shared-training uncertainty are absent.',
     'Historical score tables include other consumed summaries; only declared horizons/arm/full rows enter calculations.'],
     'resources':{'inputs':inputs,'explicit_read_bytes':sum(x['bytes'] for x in inputs),'cpu_seconds':time.process_time()-cpu,
                  'wall_seconds':time.monotonic()-start,'peak_rss_native_bytes_on_Mac':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
                  'original_row_reads':0,'physical_io_and_runtime_reads':'unknown'}}
(OUT/'HISTORICAL_PRECISION.json').write_text(json.dumps(out,indent=2)+'\n')
print(json.dumps(out,indent=2))
