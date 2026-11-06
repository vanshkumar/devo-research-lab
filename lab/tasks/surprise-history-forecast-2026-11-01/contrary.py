from data import ROOT
from model import fit,predict
from evaluate import gains
import datetime,hashlib,json,resource
import numpy as np

assert not (ROOT/'CONTRARY.json').exists()
d=dict(np.load(ROOT/'development_features.npz'));e=dict(np.load(ROOT/'evaluation_features.npz'))
f=dict(np.load(ROOT/'predictions.npz'))
m=fit(d['B'],d['y'],d['keys'][:,0],.1)
hat=predict(m,e['B'])
np.savez(ROOT/'postvalidation_matched_penalty_predictions.npz',keys=e['keys'],B_at_H_penalty=hat)
saved=datetime.datetime.now(datetime.timezone.utc).isoformat()
source=json.loads((ROOT/'DEVELOPMENT.json').read_text())
summary={}
for c in [0,1]:
    vals=[]
    for name in ['small','large']:
        xs=[v['pe_update_slope'] for v in source['descriptive_context_effect'] if v['context']==c and v['error_bin']==name]
        vals.append(float(np.mean(xs)))
    summary[str(c)]=dict(mean_person_small_error_slope=vals[0],mean_person_large_error_slope=vals[1],large_minus_small=vals[1]-vals[0])
out=dict(at=datetime.datetime.now(datetime.timezone.utc).isoformat(),status='Postvalidation consumed-record diagnostic only; no new gate/evaluation',prediction_saved_at=saved,prediction_sha256=hashlib.sha256((ROOT/'postvalidation_matched_penalty_predictions.npz').read_bytes()).hexdigest(),H_vs_B_matched_penalty=gains(e['keys'],e['y'],hat,f['H']),B_matched_penalty_vs_original_B=gains(e['keys'],e['y'],f['B'],hat),development_qualitative_context_check=summary,primary_decision_unchanged='Failed frozen joint5% rule; no model/cohort/criterion repair',peak_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
(ROOT/'CONTRARY.json').write_text(json.dumps(out,indent=2))
print(json.dumps(out,indent=2))
