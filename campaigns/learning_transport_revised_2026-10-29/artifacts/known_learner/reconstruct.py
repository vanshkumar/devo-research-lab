"""Independent scalar aggregation of saved synthetic control curves only."""
from pathlib import Path
import hashlib
import json
import numpy as np

OUT=Path(__file__).resolve().parent
ROOT=OUT.parents[3]
result=json.loads((OUT/'RESULT.json').read_text())
freeze=json.loads((OUT/'FREEZE.json').read_text())
subjects=[r['subject'] for r in freeze['selected_prefixes']]


def curves(path):
    with np.load(path,allow_pickle=False) as z:
        a=z['samples']
    return [sum((float(a[p,b,0])+float(a[p,b,1]))/2 for p in range(len(a)))/len(a) for b in range(6)]


truth={s:curves(OUT/(s+'__standard__truth_rho0.8.npz')) for s in subjects}
losses=[]
for rho in (.5,.6,.7,.8,.9,1.):
    errors=[]
    for s in subjects:
        pred=curves(OUT.parent/'transition_fit'/f'rho_{rho:.1f}'/(s+'.npz'))
        errors.extend(abs(truth[s][b]-pred[b]) for b in range(6))
    losses.append(sum(errors)/len(errors))
checks=[abs(a-result['grid_results'][i]['equal_lab_curve_mae']) for i,a in enumerate(losses)]
chosen=max(rho for rho,loss in zip((.5,.6,.7,.8,.9,1.),losses) if loss<=min(losses)+.001)
assert chosen==result['selected_control_rho']
for policy in ('standard','external'):
    tc=[curves(OUT/(s+'__'+policy+'__truth_rho0.8.npz')) for s in subjects]
    pc=[curves(OUT/(s+'__'+policy+'__selected_forecast.npz')) for s in subjects]
    errors=[sum(tc[i][b]-pc[i][b] for i in range(len(subjects)))/len(subjects) for b in range(6)]
    loss=sum(abs(e) for e in errors)/6
    checks.append(abs(loss-result['policies'][policy]['population_curve_mae']))
    if policy=='external':
        gc=[curves(OUT/(s+'__'+policy+'__growth_forecast.npz')) for s in subjects]
        ge=[sum(tc[i][b]-gc[i][b] for i in range(len(subjects)))/len(subjects) for b in range(6)]
        gloss=sum(abs(e) for e in ge)/6
        checks.append(abs((gloss-loss)-result['policies'][policy]['population_curve_mae_advantage_over_growth']))
assert max(checks)<1e-12
for row in result['manifest']:
    assert hashlib.sha256((ROOT/row['path']).read_bytes()).hexdigest()==row['sha256']
out=dict(saved_generated_curves_only=True,actual_outcomes_read=False,
    numeric_comparisons=len(checks),max_abs_difference=max(checks),
    selected_rho=chosen,forecast_hashes_verified=len(result['manifest']))
(OUT/'INDEPENDENT_SUMMARY_CHECK.json').write_text(json.dumps(out,indent=2)+'\n')
print(json.dumps(out))
