"""Finite integrity checks and source-coefficient accounting; no fitting."""
import os
for key in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','VECLIB_MAXIMUM_THREADS','NUMEXPR_NUM_THREADS'):os.environ[key]='1'
from pathlib import Path
import json,hashlib,resource,datetime
import numpy as np
HERE=Path(__file__).resolve().parent;AUTHOR=HERE.parents[1]/'tasks'/HERE.name;ROOT=HERE.parents[2]

def main():
    charge=0;pins=[]
    def pin(path,expected=None):
        nonlocal charge
        h=hashlib.sha256()
        with path.open('rb') as f:
            for b in iter(lambda:f.read(1024*1024),b''):h.update(b);charge+=len(b)
        r=dict(path=str(path.relative_to(ROOT)),bytes=path.stat().st_size,sha256=h.hexdigest())
        if expected is not None:r['expected_sha256']=expected;r['matches_expected']=h.hexdigest()==expected;assert r['matches_expected'],r
        pins.append(r);return r
    freeze_path=AUTHOR/'FREEZE.json';freeze=json.loads(freeze_path.read_text());charge+=freeze_path.stat().st_size
    for name,expected in freeze['sha256'].items():pin(AUTHOR/name,expected)
    manifest_path=AUTHOR/'ALLOWED_MANIFEST.json';manifest=json.loads(manifest_path.read_text());charge+=manifest_path.stat().st_size
    for r in manifest['authority_pins']:pin(ROOT/r['path'],r['sha256'])
    # Stable author scientific products and all current review code. Avoid
    # duplicate hashing of source objects already verified by source_sample.py.
    stable=['FREEZE.json','NUMERICAL_AMENDMENT.json','LOGGING_AMENDMENT.md','CONTROLS_AMENDMENT.md','RESOURCES.json','analysis_explicit.py','audit.py','consumed_inputs.npz','corrected/FITS.json','corrected/FEATURES.json','corrected/predictions.npz','corrected/scoring_rows.csv','corrected/unit_scores_B.csv','corrected/unit_scores_S.csv','corrected/SUMMARY.json','corrected/DIAGNOSTICS.json','corrected/NUMERICAL_AUDIT.json','corrected/CONTROLS.json','corrected/CONTROL_FITS.json','corrected/CONTROL_RUN.json','RESULT.md','README.md','STATE.md']
    for name in stable:pin(AUTHOR/name)
    for p in sorted(HERE.glob('*.py')):pin(p)
    path1=AUTHOR/'corrected/predictions.npz';path2=HERE/'independent_predictions.npz'
    charge+=path1.stat().st_size+path2.stat().st_size
    with np.load(path1,allow_pickle=False) as a,np.load(path2,allow_pickle=False) as b:
        assert set(a.files)==set(b.files)
        all_entries=finite=nan=decoded=0;errors=[]
        for key in a.files:
            aa=a[key];bb=b[key];decoded+=aa.nbytes+bb.nbytes
            assert np.array_equal(np.isnan(aa),np.isnan(bb))
            good=np.isfinite(aa);assert np.array_equal(aa[good],bb[good])
            if key!='y':all_entries+=aa.size;finite+=int(good.sum());nan+=int(np.isnan(aa).sum())
    fit_path=AUTHOR/'corrected/FITS.json';fits=json.loads(fit_path.read_text());charge+=fit_path.stat().st_size
    theta=[]
    for source in ('human','mouse'):
        for baseline,aug in [('B',False),('S',True)]:
            rr=sorted([r for r in fits if r['model']==source+'_fixed' and r['augmented']==aug],key=lambda r:r['fold'])
            values=np.array([r['source_history'] for r in rr])
            theta.append(dict(source=source,baseline=baseline,fold_coefficients=values.tolist(),coefficient_mean=values.mean(axis=0).tolist(),mean_l2_norm=float(np.mean(np.sqrt(np.sum(values**2,axis=1)))),source_gradient_max_recorded=max(r['source_diagnostics']['gradient_max'] for r in rr)))
    registry=ROOT/'lab/registry.json';record=json.loads(registry.read_text());charge+=registry.stat().st_size
    report=dict(utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),frozen_author_pins_passed=len(freeze['sha256']),authority_pins_passed=len(manifest['authority_pins']),current_artifact_pins=pins,prediction_equality=dict(total_entries=all_entries,finite_entries=finite,omission_NaNs=nan,y_entries=65732,all_bit_exact=True),source_history_accounting=theta,coefficient_interpretation='The human-fixed vector is source-frozen separately within each baseline. S refits source history coefficients with physical history present; it does not apply the original B source vector unchanged. No independent source optimizer refit.',current_pi=record['pi']['thread_id'],resource=dict(read_hash_bytes=charge,decoded_array_bytes=decoded,peak_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss))
    (HERE/'PINS.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({k:report[k] for k in ('frozen_author_pins_passed','authority_pins_passed','prediction_equality','source_history_accounting','current_pi','resource')},indent=2))

if __name__=='__main__':main()
