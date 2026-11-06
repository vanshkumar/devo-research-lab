"""Independent scalar endpoint reconstruction. No author-module imports."""
from pathlib import Path
import datetime as dt
import hashlib
import io
import json
import math
import resource
import time
import zipfile
import numpy as np

OUT = Path(__file__).resolve().parent
ROOT = OUT.parents[2]
AUTHOR = ROOT / 'lab/tasks/learning-forecast-information-audit-2026-11-01'
HISTORY = ROOT / 'experiments/matched_history_diagnostic_2026-10-29'
CMD = ('OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 '
       'VECLIB_MAXIMUM_THREADS=1 NUMEXPR_NUM_THREADS=1 PYTHONDONTWRITEBYTECODE=1 '
       'campaigns/learning_rule_transport_2026-10-28/.modelenv/bin/python '
       'lab/reviews/learning-forecast-information-audit-2026-11-01/first_calculation.py')

def main():
    tic = time.monotonic()
    ledger = []
    def read_npz(path):
        b = path.read_bytes()
        with zipfile.ZipFile(io.BytesIO(b)) as z:
            decoded = sum(x.file_size for x in z.infolist())
        ledger.append(dict(path=str(path.relative_to(ROOT)), file_bytes=len(b),
                           full_decoded_bytes=decoded, sha256=hashlib.sha256(b).hexdigest()))
        with np.load(io.BytesIO(b), allow_pickle=False) as z:
            return {k:z[k] for k in z.files}

    x = read_npz(AUTHOR/'MATCHED_PREDICTIONS.npz')
    old = read_npz(HISTORY/'CURVES.npz')
    print('MATCHED_KEYS', {k:list(v.shape) for k,v in x.items()}, flush=True)
    subjects = x['subjects'].tolist()
    assert len(subjects) == len(set(subjects)) == 24
    assert not set(subjects) & {'NYU-21','SWC_007'}
    assert subjects == old['subjects'].tolist()
    target = x['observed_sides']
    assert target.shape == (24,6,2)
    assert np.array_equal(target,old['observed_sides'])
    predictions = {}
    for k in ('saved_autonomous_particles','conditional_sampled_particles','conditional_analytic_particles'):
        a = x[k]
        assert a.shape == (24,512,6,2) and np.isfinite(a).all()
        # Scalar fsum is independent of the author's vector aggregation.
        predictions[k] = np.array([math.fsum(float(v) for v in a[i,:,t,s])/512
                                  for i in range(24) for t in range(6) for s in range(2)]).reshape(24,6,2)
    predictions['saved_central'] = old['conditional_rnn']
    counts = []
    for i,subject in enumerate(subjects):
        row = read_npz(HISTORY/(subject+'__conditional.npz'))
        assert np.array_equal(row['observed'][:,:2],target[i])
        n = row['counts'][:,:2]
        assert n.shape == (6,2) and (n>0).all()
        assert np.max(np.abs(target[i]*n-np.rint(target[i]*n))) < 1e-10
        counts.append(n)
    def score(p):
        residual = [[math.fsum(float(target[i,t,s]-p[i,t,s]) for s in range(2))/2
                     for t in range(6)] for i in range(24)]
        pop = [math.fsum(residual[i][t] for i in range(24))/24 for t in range(6)]
        return dict(population_curve_mae_pp=100*math.fsum(abs(v) for v in pop)/6,
                    individual_equal_side_mae_pp=100*math.fsum(abs(v) for a in residual for v in a)/144,
                    individual_side_mae_pp=100*math.fsum(abs(float(v)) for v in (target-p).flat)/288,
                    signed_population_residual_pp=[100*v for v in pop])
    metrics = {k:score(p) for k,p in predictions.items()}
    auto = metrics['saved_autonomous_particles']['population_curve_mae_pp']
    cond = metrics['conditional_sampled_particles']['population_curve_mae_pp']
    charge = sum(a['file_bytes']+a['full_decoded_bytes'] for a in ledger)+5_000_000
    result = dict(utc=dt.datetime.now(dt.timezone.utc).isoformat(), command=CMD,
                  status='independent_scalar_array_reconstruction_executed',
                  units='percentage points; denominator counts are exact100 opportunities, including omissions',
                  subjects=subjects,labs=x['labs'].tolist(),count_shape=list(np.asarray(counts).shape),
                  counts=np.asarray(counts).tolist(),exact100_opportunities=int(np.sum(counts)),
                  metrics=metrics,population_gap_pp=auto-cond,
                  input_manifest=ledger,
                  matched_prediction_member_shapes={k:list(v.shape) for k,v in x.items()},
                  resources=dict(conservative_cumulative_read_charge_bytes=charge,
                                 context_runtime_code_allowance_bytes=5_000_000,
                                 peak_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
                                 physical_io_unknown=True,public_operations=0,ingress_bytes=0,
                                 scientific_processes=1,numerical_threads=1,elapsed_seconds=time.monotonic()-tic))
    (OUT/'FIRST_CALCULATION.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:result[k] for k in ('utc','status','exact100_opportunities','metrics','population_gap_pp','resources')},indent=2),flush=True)

if __name__ == '__main__':
    main()
