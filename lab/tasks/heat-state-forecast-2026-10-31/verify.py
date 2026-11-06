"""Postvalidation numerical/access verification; no model changes or new fits."""
import os
os.environ['OPENBLAS_NUM_THREADS']='1'
os.environ['OMP_NUM_THREADS']='1'
import hashlib,json,numpy as np
import forecast as f
import evaluation as e
def main():
    fr=e.check_freeze();cfg=fr['configuration']
    ps=e.prefixes();full=[]
    for p in ps:
        with np.load(f.SRC/('derived_'+p['uid']+'.npz')) as z:d={k:z[k].copy() for k in z.files}
        d['uid']=p['uid'];full.append(d)
    inv={}
    for mode in ['neural','behavior']:
        a=f.make_bundle(ps,cfg['classes'],mode,False);b=f.make_bundle(full,cfg['classes'],mode,False)
        inv[mode]={k:float(np.nanmax(np.abs(a[k]-b[k]))) for k in ['X','G','R']}
        for k in ['X','G','R']:
            assert np.array_equal(np.isfinite(a[k]),np.isfinite(b[k]))
            assert inv[mode][k]<1e-11
    before=json.loads((f.TASK/'FORECAST_SAVED.json').read_text());access=json.loads((f.TASK/'EVALUATION_OUTCOME_ACCESS.json').read_text())
    assert all(x['at_utc']>before['at_utc'] for x in access)
    assert hashlib.sha256((f.TASK/before['forecast_file']).read_bytes()).hexdigest()==before['sha256']
    result=json.loads((f.TASK/'EVALUATION_RESULT.json').read_text());rng=np.random.default_rng(20261031)
    additional={}
    with np.load(f.TASK/'EVALUATION_FORECASTS.npz') as pp,np.load(f.TASK/'EVALUATION_TRUTH.npz') as yy:
        truth=yy['behavior_truth'];sc=cfg['scales']['behavior']
        losses={m:f.losses(pp['behavior__'+m],truth,sc) for m in ['simple','shared','persistence']}
        additional['behavior_simple_over_shared']=e.summary(losses['shared'],losses['simple'],np.arange(7),rng)
        for k,name in enumerate(['reverse_fraction','pumping']):
            comp={m:np.mean((pp['behavior__'+m][:,k]-truth[:,k])**2,axis=1) for m in ['shared','simple','state','persistence']}
            additional[name+'_simple_over_shared']=e.summary(comp['shared'],comp['simple'],np.arange(7),rng)
            additional[name+'_simple_over_persistence']=e.summary(comp['persistence'],comp['simple'],np.arange(7),rng)
        y=yy['neural_truth'];common=np.isfinite(y[:,:,0]).all(axis=0)
        a=f.losses(pp['neural__simple'][:,common],y[:,common],np.ones(common.sum()))
        b=f.losses(pp['neural__state'][:,common],y[:,common],np.ones(common.sum()))
        additional['postvalidation_common_neuron_class_sensitivity']=dict(classes=np.array(cfg['classes'])[common].tolist(),result=e.summary(a,b,np.arange(7),rng),status='postvalidation label-support diagnostic; no refitting or primary replacement')
        additional['primary_prediction_finite_masks_equal']=bool(np.array_equal(np.isfinite(pp['neural__simple']),np.isfinite(pp['neural__state'])))
    assert additional['primary_prediction_finite_masks_equal']
    # File-size accounting does not decode more numerical input. Conservative
    # reservations in ACCOUNTING remain, including zero-byte failed DNS attempts.
    files={p.name:p.stat().st_size for p in f.SRC.iterdir() if p.is_file()}
    raw=sum(v for k,v in files.items() if k.startswith('atanas_kim_2023-') and k.endswith('.json'))
    assert raw==166063303
    out=dict(at_utc=f.now(),all_frozen_pins_valid=True,forecast_hash_valid=True,all_outcomes_interpreted_after_forecasts_saved=True,max_prefix_feature_difference_from_full_data=inv,raw_payload_bytes=raw,source_file_sizes=files,additional_results=additional,jobs='all invoked numerical/acquisition commands finished; no background jobs launched',limits='Code used single serial process and BLAS/OMP thread cap1. Full-process memory not OS-profiled; largest JSON<10MB, measured array sizes and implementation keep expected peak well below4GB. No complete OS-process audit claimed.')
    f.save('VERIFICATION.json',out)
    print(json.dumps({k:v for k,v in out.items() if k!='source_file_sizes'},indent=2))
if __name__=='__main__':main()
