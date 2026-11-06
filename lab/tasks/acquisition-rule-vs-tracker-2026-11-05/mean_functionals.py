import time
import numpy as np
from pilot import HERE,IO,get,save,arrays,utc

begin=time.monotonic();z=arrays(HERE/'EARLY_COUNTS.npz');s=get(HERE/'EARLY_SCORES.json');out={}
ids=list(z['subjects'])
for name in z['names']:
    out[str(name)]={}
    for c in z['cutoffs']:
        out[str(name)][str(c)]={}
        for j,h in enumerate(z['windows']):
            rows=[s['per_animal'][i][str(c)][str(name)][str(h)] for i in ids]
            er=np.array([r['expected_ratio'] for r in rows]);po=np.array([r['count_pooled'] for r in rows])
            actual=z['observed'][:,j,[1,3]]/z['observed'][:,j,[0,2]]
            out[str(name)][str(c)][str(h)]=dict(individual_side_specific_mae=float(abs(er-actual).mean()),
                individual_balanced_mean_mae=float(abs(er.mean(1)-actual.mean(1)).mean()),
                cohort_observed=float(actual.mean()),cohort_expected_ratio=float(er.mean()),cohort_count_pooled=float(po.mean()),
                predicted_positive_count_mass_min=float(min(min(r['positive_mass']) for r in rows)))
save('MEAN_FUNCTIONALS.json',dict(utc=utc(),summary=out,seconds=time.monotonic()-begin,io=dict(IO),
      label='Descriptive postvalidation auxiliary; not replacement primary or an independently earned interval.'))
print({name:{c:row['2000'] for c,row in data.items()} for name,data in out.items()},flush=True)
