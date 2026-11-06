"""Independent endpoint-only reconstruction; no campaign modules executed."""
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

O = Path(__file__).resolve().parent
R = O.parents[2]
C = R / 'campaigns/population_learning_transport_2026-10-28'
V = R / 'lab/reviews/learning-forecast-information-audit-2026-11-01'
H = R / 'experiments/matched_history_diagnostic_2026-10-29'
COMMAND = ('OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 '
           'VECLIB_MAXIMUM_THREADS=1 NUMEXPR_NUM_THREADS=1 PYTHONDONTWRITEBYTECODE=1 '
           'campaigns/learning_rule_transport_2026-10-28/.modelenv/bin/python '
           'lab/tasks/learning-forecast-count-joint-audit-2026-11-01/first_calculation.py')


def main():
    tic = time.monotonic()
    ledger = []
    # Includes the preserved failed start, this context/code/runtime and margin.
    allowance = 12_000_000
    def charged():
        return allowance + sum(x['containing_file_bytes'] + x['decoded_bytes_charged'] for x in ledger)
    def read(path, npz=False, expected=None):
        assert dt.datetime.now(dt.timezone.utc) < dt.datetime(2026,11,1,13,56,15,tzinfo=dt.timezone.utc)
        assert charged() + path.stat().st_size < 200_000_000
        b = path.read_bytes()
        pin = hashlib.sha256(b).hexdigest()
        if expected is not None:
            assert pin == expected, str(path)
        decoded = 0
        if npz:
            with zipfile.ZipFile(io.BytesIO(b)) as z:
                decoded = sum(v.file_size for v in z.infolist())
        ledger.append(dict(path=str(path.relative_to(R)),containing_file_bytes=len(b),
                           decoded_bytes_charged=decoded,sha256=pin))
        assert charged() < 200_000_000
        if npz:
            with np.load(io.BytesIO(b),allow_pickle=False) as z:
                return {k:z[k] for k in z.files}
        return json.loads(b)

    freeze = read(C/'protocols/FREEZE.json')
    manifest = read(C/'protocols/SOURCE_FORECASTS.json')
    assert manifest['freeze_sha256'] == ledger[0]['sha256']
    old = read(H/'CURVES.npz',True)
    verified = read(V/'RECONSTRUCTED_ENDPOINTS.npz',True)
    original = read(C/'artifacts/results/SOURCE_ARRAYS.npz',True)
    subjects = verified['subjects'].tolist()
    labs = verified['labs']
    assert len(subjects) == len(set(subjects)) == 24
    assert subjects == freeze['source_primary_subjects'] == old['subjects'].tolist()
    assert not set(subjects) & {'NYU-21','SWC_007'}
    assert np.array_equal(original['subjects'],verified['subjects'])
    y = verified['observed']
    nobs = verified['observed_counts'][:,:,:2]
    assert y.shape == nobs.shape == (24,6,2)
    assert np.array_equal(y,old['observed_sides'])
    assert np.array_equal(y,original['observed'][:,:,:2])
    assert np.array_equal(nobs,original['counts'][:,:,:2])
    correct_observed = np.rint(y*nobs).astype(np.int64)
    assert np.max(np.abs(y*nobs-correct_observed)) < 1e-10
    arrays = {}
    identities = {}
    records = {(v['subject'],v['model']):v for v in manifest['records'] if v.get('eligible')}
    for method in ('rnn','growth'):
        acc, num, den = [], [], []
        max_rounding = 0.
        for i, subject in enumerate(subjects):
            row = records[(subject,method)]
            x = read(R/row['path'],True,row['sha256'])
            a = x['samples'][:,:,:2]
            n = x['counts'][:,:,:2]
            assert a.shape == n.shape == (512,6,2)
            assert np.isfinite(a).all() and (n>0).all()
            assert (n == np.rint(n)).all() and (n.sum(2)<=500).all()
            k = np.rint(a*n).astype(np.int64)
            max_rounding = max(max_rounding,float(np.max(np.abs(a*n-k))))
            assert max_rounding < 1e-10 and ((0<=k)&(k<=n)).all()
            if method == 'rnn':
                assert np.array_equal(a,verified['autonomous'][i])
                assert np.array_equal(n,verified['autonomous_counts'][i])
            acc.append(a); num.append(k); den.append(n.astype(np.int64))
        arrays[method+'_accuracy'] = np.asarray(acc)
        arrays[method+'_successes'] = np.asarray(num)
        arrays[method+'_opportunities'] = np.asarray(den)
        mean = arrays[method+'_accuracy'].mean(1)
        assert np.max(np.abs(mean-old['autonomous_'+method])) < 1e-12
        identities[method] = dict(shape=list(arrays[method+'_accuracy'].shape),
            max_success_rounding_error_counts=max_rounding,
            min_opportunities=int(arrays[method+'_opportunities'].min()),
            max_opportunities=int(arrays[method+'_opportunities'].max()),
            paired_count_success_cells=int(arrays[method+'_successes'].size))

    def score(p):
        # Independently written scalar sums; all sides/animals/bins equal.
        d = [[math.fsum(float(y[i,t,s]-p[i,t,s]) for s in range(2))/2 for t in range(6)] for i in range(24)]
        pop = [math.fsum(d[i][t] for i in range(24))/24 for t in range(6)]
        return dict(population_mae_pp=100*math.fsum(abs(v) for v in pop)/6,
                    individual_equal_side_mae_pp=100*math.fsum(abs(v) for row in d for v in row)/144,
                    individual_side_mae_pp=100*math.fsum(abs(float(v)) for v in (y-p).flat)/288)
    metrics = {m:score(arrays[m+'_accuracy'].mean(1)) for m in ('rnn','growth')}
    rn = arrays['rnn_opportunities']; rk = arrays['rnn_successes']; ra = arrays['rnn_accuracy']
    pooled = rk.sum(1)/rn.sum(1)
    cov = np.mean((rn-rn.mean(1)[:,None])*(ra-ra.mean(1)[:,None]),axis=1)
    metrics['rnn_count_pooled'] = score(pooled)
    metrics['conditional_sampled'] = score(verified['conditional_sampled'].mean(1))
    assert abs(metrics['rnn']['population_mae_pp']-6.969990523446359)<1e-5
    assert abs(metrics['growth']['population_mae_pp']-2.278105)<1e-5
    assert abs(metrics['rnn_count_pooled']['population_mae_pp']-1.052554)<1e-5
    identity_error = float(np.max(np.abs(pooled-ra.mean(1)-cov/rn.mean(1))))
    assert identity_error < 1e-12
    np.savez_compressed(O/'ENDPOINTS.npz',subjects=np.array(subjects),labs=labs,
                        observed_accuracy=y,observed_opportunities=nobs,
                        observed_successes=correct_observed,**arrays)
    resources = dict(cumulative_read_hash_decode_charge_bytes=charged(),
        context_code_runtime_allowance_bytes=allowance,failed_start_allowance_within_it_bytes=5_000_000,
        peak_process_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
        rss_units='bytes on Darwin',scientific_processes=1,numerical_threads=1,
        public_operations=0,downloads=0,ingress_bytes=0,physical_io_unknown=True,
        elapsed_seconds=time.monotonic()-tic)
    assert resources['peak_process_rss_bytes'] < 800_000_000
    result = dict(utc=dt.datetime.now(dt.timezone.utc).isoformat(),status='executed_independent_endpoint_reconstruction',
        command=COMMAND,owner='01a19734-d25e-7bb3-8e81-85110583eb56',start=21,cycle=13,
        fixed_start_utc='2026-11-01T12:56:15Z',first_numeric_deadline_utc='2026-11-01T13:08:15Z',
        subjects=subjects,labs=labs.tolist(),units='accuracy errors percentage points; integer exact100 opportunities/successes with omissions incorrect',
        admitted_original_rows=96000,new_raw_rows_read=0,observed_opportunities=int(nobs.sum()),
        metrics=metrics,paired_output_identities=identities,
        count_accuracy_covariance_identity_max_error=identity_error,
        negative_rnn_covariance_cells=int((cov<0).sum()),input_manifest=ledger,resources=resources)
    stdout = json.dumps({k:result[k] for k in ('utc','status','observed_opportunities','metrics','paired_output_identities','negative_rnn_covariance_cells','resources')},indent=2)
    result['native_stdout'] = stdout
    (O/'FIRST_CALCULATION.json').write_text(json.dumps(result,indent=2)+'\n')
    (O/'FIRST_CALCULATION.stdout').write_text(stdout+'\n')
    print(stdout,flush=True)


if __name__ == '__main__':
    main()
