"""Verify cached source bytes, fixed forecasts and the expected no-score gate.

Writes only OFFLINE_REPLAY.json; does not overwrite frozen evidence or score.
"""
import os
os.environ.update(OPENBLAS_NUM_THREADS='1',OMP_NUM_THREADS='1',VECLIB_MAXIMUM_THREADS='1',MKL_NUM_THREADS='1')
import sys,json,hashlib,zipfile,resource,time
from pathlib import Path
R=Path(__file__).resolve().parent
pin=json.loads((R/'CODEC_PACKAGE_PIN.json').read_bytes());wheel=(R/'numcodecs.whl').read_bytes();assert hashlib.sha256(wheel).hexdigest()==pin['digests']['sha256']
if not (R/'deps/numcodecs').exists():
    with zipfile.ZipFile(R/'numcodecs.whl') as z:
        assert all(not p.startswith('/') and '..' not in Path(p).parts for p in z.namelist());z.extractall(R/'deps')
sys.path.insert(0,str(R/'deps'))
import numpy as np,scipy,numcodecs
import analysis as A, evaluate as E
f=E.check_freeze();acq=[json.loads(x) for x in (R/'ACQUISITIONS.jsonl').read_text().splitlines()];source_ok=0
for x in acq:
    assert hashlib.sha256((R/x['path']).read_bytes()).hexdigest()==x['sha256'];source_ok+=1
models=json.loads((R/'DEVELOPMENT_MODELS.json').read_bytes());pins=json.loads((R/'FORECAST_PINS.json').read_bytes());arrays=0;probabilities=0;maxerr=0;data_checks={}
for sid in A.EVAL:
    d=E.decode(sid);saved=dict(np.load(R/(sid+'_evaluation_arrays.npz'),allow_pickle=True));pred=dict(np.load(R/(sid+'_FORECASTS.npz'),allow_pickle=True))
    for k,a in d.items():
        assert np.array_equal(a,saved[k]) if a.dtype.kind=='O' else np.array_equal(a,saved[k],equal_nan=True)
        arrays+=1
    for ablate in [False,True]:
        X,n,c=A.features(d,ablate=ablate)
        for fam in A.FAMILIES:
            got=A.predict(X[:,:c[fam]],models[fam]);target=pred[('ablation_' if ablate else '')+fam];err=float(np.max(np.abs(got-target)));maxerr=max(maxerr,err);assert err<1e-14;probabilities+=len(got)
    assert hashlib.sha256((R/(sid+'_FORECASTS.npz')).read_bytes()).hexdigest()==pins['paths'][sid+'_FORECASTS.npz']
    data_checks[sid]=E.checks(d)
assert not all(all(x.values()) for x in data_checks.values())
assert not (R/'PRIMARY_SCORES.json').exists() and not (R/'SCORED_TRIALS.json').exists()
full={}
if len(sys.argv)>1 and sys.argv[1]=='full':
    dest=R/'reproduction';dest.mkdir(exist_ok=True)
    def replay_save(name,x):(dest/name).write_text(json.dumps(x,indent=2,allow_nan=False)+'\n')
    A.save=replay_save;A.development();A.controls()
    rebuilt=json.loads((dest/'DEVELOPMENT_MODELS.json').read_bytes())
    err=max(float(np.max(np.abs(np.array(rebuilt[k]['beta'])-np.array(models[k]['beta'])))) for k in A.FAMILIES);assert err<1e-10
    original_control=json.loads((R/'CONTROL_FORECASTS.json').read_bytes());replayed_control=json.loads((dest/'CONTROL_FORECASTS.json').read_bytes());assert original_control==replayed_control
    full=dict(development_model_max_coefficient_error=err,all_100_development_fits_reexecuted=True,conditional_control_replicates_reexecuted=64,conditional_control_forecast_rows_exactly_equal=len(original_control),writes='reproduction/ only; original frozen bytes retained')
out=dict(created_utc=A.stamp(),source_response_pins_verified=source_ok,frozen_files_verified=len(f['paths']),raw_arrays_redecoded_verified=arrays,forecast_probabilities_replayed=probabilities,max_probability_error=maxerr,forecasts_pins_verified=len(pins['paths']),frozen_source_gate_failure_reproduced=True,primary_scores_exist=False,full_replay=full,note='Author self-replay, not independent scientific review. No evaluation losses computed.',versions=dict(python=sys.version,numpy=np.__version__,scipy=scipy.__version__,numcodecs=numcodecs.__version__),rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
(R/'OFFLINE_REPLAY.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out,indent=2))
