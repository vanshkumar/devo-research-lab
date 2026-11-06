"""Summarize existing development/synthetic results and verify frozen forecasts.

Never loads reserved/external outcomes. No additional model fitting.
"""
import csv, hashlib, json, sys
from pathlib import Path
import numpy as np
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parents[1]/'experiments'))
import state_models as s

def wilson(count,n):
    z=1.959963984540054;p=count/n;den=1+z*z/n
    mid=(p+z*z/(2*n))/den
    half=z*np.sqrt(p*(1-p)/n+z*z/(4*n*n))/den
    return [float(mid-half),float(mid+half)]

records=json.loads((s.OUT/'state_models_fgls_recovery_core.json').read_text())['records']
summary=[]
for target in [0.,.2,-.2]:
    rows=[r for r in records if r['target']==target];n=len(rows)
    est=np.array([r['theta'] for r in rows]);true=np.array([r['truth'] for r in rows])
    count=sum(r['false_equivalence'] for r in rows)
    summary.append({'scenario':rows[0]['scenario'],'truth':target,'n':n,
        'mean_estimate':float(est.mean()),'bias':float((est-true).mean()),
        'rmse':float(np.sqrt(np.mean((est-true)**2))),
        'mean_se':float(np.mean([r['se'] for r in rows])),
        'coverage':sum(r['coverage'] for r in rows),
        'detect_zero_exclusion':sum(r['detect_zero_exclusion'] for r in rows),
        'interval_inside_margin':sum(r['interval_inside_margin'] for r in rows),
        'false_equivalence':count,'false_equivalence_wilson95':wilson(count,n),
        'coverage_wilson95':wilson(sum(r['coverage'] for r in rows),n),
        'mean_phi':float(np.mean([r['phi'] for r in rows])),
        'diagnostic_only':sum(r['diagnostic_only'] for r in rows),
        'slow_at_upper_bound':sum(r['slow_at_upper_bound'] for r in rows),
        'unflagged_n':sum(not r['diagnostic_only'] for r in rows),
        'unflagged_false_equivalence':sum(r['false_equivalence'] and not r['diagnostic_only'] for r in rows),
        'failed_alternative_starts':sum(not q['success'] for r in rows for q in r['starts'])})
(s.OUT/'state_models_fgls_recovery_summary.json').write_text(json.dumps(summary,indent=2)+'\n')
with (s.OUT/'state_models_fgls_recovery_summary.csv').open('w') as f:
    w=csv.DictWriter(f,fieldnames=list(summary[0]));w.writeheader();w.writerows(summary)

ps=s.load('development','Hand_raw');rng=np.random.default_rng(283117)
invariance=[]
for filename in ['state_models_frozen_predictions.json','state_models_fgls_frozen_predictions.json']:
    frozen=json.loads((s.OUT/filename).read_text())
    for model in ['restricted','alternative']:
        changes=[];shift_errors=[]
        for p in ps:
            before=s.predicted_full(p,frozen[model])
            changed=dict(p);changed['y']=p['y'].copy()
            changed['y'][100:]=rng.normal(100,500,724)
            changed['y'][100::17]=np.nan
            after=s.predicted_full(changed,frozen[model])
            changes.append(float(np.nanmax(abs(after-before))))
            shifted=dict(p);shifted['y']=p['y'].copy();shifted['y'][:100]+=1
            shifted_pred=s.predicted_full(shifted,frozen[model])
            shift_errors.append(float(np.nanmax(abs(shifted_pred-before-1))))
        invariance.append({'frozen_file':filename,'model':model,
            'max_forecast_change_under_arbitrary_main_outcomes':max(changes),
            'max_error_from_one_degree_baseline_shift':max(shift_errors)})
assert all(r['max_forecast_change_under_arbitrary_main_outcomes']==0 for r in invariance)
(s.OUT/'state_models_prediction_invariance.json').write_text(json.dumps(invariance,indent=2)+'\n')

# Mathematical check of fixed-source forecast scoring, with fabricated gains.
rows=[{'file':f,'set':f,'mse_gain':float(x)} for f,offset in [('A',-20),('B',20)] for x in np.arange(10)+offset]
score=s.prediction_score_summary(rows)
expected_se=np.sqrt(2*np.var(np.arange(10),ddof=1)/10)/2
assert np.isclose(score['mean_person_mse_gain'],4.5)
assert np.isclose(score['se'],expected_se) and np.isclose(score['df'],18)

refresh=[]
for name in ['state_models_development.json','state_models_fgls_development.json']:
    new=json.loads((s.OUT/name).read_text())
    old=json.loads((s.OUT/name.replace('.json','_before_provenance_refresh.json')).read_text())
    for key in ['restricted','alternative']:
        assert new[key]['parameters']==old[key]['parameters']
        assert new[key]['actual_schedule_curve']==old[key]['actual_schedule_curve']
    refresh.append({'file':name,'parameter_and_curve_change':0.})
files=[Path(s.__file__),HERE/'gls_repair.py',s.OUT/'state_models_frozen_predictions.json',
       s.OUT/'state_models_fgls_frozen_predictions.json',s.ROOT/'protocol/split.json']
hashes={str(p.relative_to(s.ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in files}
ols=json.loads((s.OUT/'state_models_frozen_predictions.json').read_text())
fgls=json.loads((s.OUT/'state_models_fgls_frozen_predictions.json').read_text())
assert ols['script_sha256']==hashes['experiments/state_models.py']
assert fgls['script_sha256']==hashes['audits/state_models/gls_repair.py']
assert fgls['state_models_dependency_sha256']==hashes['experiments/state_models.py']
out={'development_only':True,'reserved_and_external_outcomes_accessed':False,
     'invariance':invariance,'fabricated_equal_set_scoring_check':score,
     'provenance_refresh_unchanged_fit':refresh,'sha256':hashes,
     'post_release_commands':[
         '.venv/bin/python campaigns/target_event_carryover_2026-10-28/experiments/state_models.py evaluate',
         '.venv/bin/python campaigns/target_event_carryover_2026-10-28/audits/state_models/gls_repair.py evaluate']}
(s.OUT/'state_models_freeze_readiness.json').write_text(json.dumps(out,indent=2)+'\n')
print(json.dumps({'recovery_summary':summary,'freeze_readiness':out},indent=2))
