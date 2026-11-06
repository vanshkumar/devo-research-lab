"""Summaries of actual review outputs; no additional source-array read."""
import json,math,hashlib,datetime
from pathlib import Path
import numpy as np
P=Path(__file__).resolve().parent
d=json.loads((P/'CROSSED_DIAGNOSTIC.json').read_text())
wrong=[x for x in d['rows'] if x['wrong_corrective_preference']]
geometry=[]
for x in wrong:
    b=x['base_cost'];t=x['positive_temporal_feature_term'];c=x['cross_term']/2
    corr=c/math.sqrt(b*t)
    geometry.append({k:x[k] for k in ('case','critic','alpha','duration_delta','gap_ms','delta_cost','delta_gold','cross_term','positive_temporal_feature_term')})
    geometry[-1].update(cosine=corr,gram_determinant=b*t-c*c,relative_gram_determinant=1-corr*corr)
assert all(x['positive_temporal_feature_term']>0 and x['gram_determinant']>0 for x in geometry)
aud=json.loads((P/'LOG_AUDIT.json').read_text())
rng=np.random.default_rng(700031);ix=rng.integers(0,8,(10000,8))
def values(mode):return np.array([x['improvement'] for x in aud['rows'] if x['mode']==mode])
def effect(a,b):
    v=values(a)-values(b)
    return {'mean_pp':float(v.mean()*100),'case_bootstrap_CI95_pp':(np.percentile(v[ix].mean(1),(2.5,97.5))*100).tolist()}
out={'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'wrong_preferences':geometry,
     'all_wrong_pairs_have_distinct_noncollinear_content_timing_contrasts':True,
     'min_relative_gram_determinant':min(x['relative_gram_determinant'] for x in geometry),
     'paired_population_minus_raw':effect('population','raw'),
     'paired_fixed_minus_population':effect('unplasticized_population','population'),
     'uncertainty_note':'Same8synthetic cases; one common bootstrap index matrix at700031. No new plants or empirical uncertainty.'}
(P/'DERIVED_SUMMARY.json').write_text(json.dumps(out,indent=2)+'\n')
print(json.dumps(out,indent=2))
