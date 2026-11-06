"""Replay every saved forecast and primary MSE from cached inputs, no network."""
import argparse,copy,json,pathlib,numpy as np
import forecast as f
import evaluation as e
def main(output):
    fr=e.check_freeze();cfg=fr['configuration'];ds=f.load_development();ps=e.prefixes();pred={}
    for mode in ['neural','behavior']:
        tr=f.make_bundle(ds,cfg['classes'],mode);te=f.make_bundle(ps,cfg['classes'],mode,False)
        for name in f.SIMPLE+['local','state']:
            pred[mode+'__'+name]=f.predict(tr,te,name,cfg['primary'][mode]['configs'][name]['alpha'])
        pred[mode+'__simple']=e.baseline(tr,te,cfg)
        pred[mode+'__simple_delay120']=e.delay(pred[mode+'__simple'],te)
        pred[mode+'__state_delay120']=e.delay(pred[mode+'__state'],te)
        pred[mode+'__no_stimulus_relax120']=f.simple_base(te['X'],'relax120')
    dd=copy.deepcopy(ds);pp=copy.deepcopy(ps)
    for d in dd+pp:d['neural']=d['ratio']-1.
    tr=f.make_bundle(dd,cfg['classes'],'neural');te=f.make_bundle(pp,cfg['classes'],'neural',False)
    for name in ['shared','local','state']:pred['fractional__'+name]=f.predict(tr,te,name,cfg['fractional'][name]['alpha'])
    differences={}
    with np.load(f.TASK/'EVALUATION_FORECASTS.npz') as z:
        for name,a in pred.items():
            assert np.array_equal(np.isfinite(a),np.isfinite(z[name]))
            differences[name]=float(np.nanmax(np.abs(a-z[name])))
            assert differences[name]<1e-12
    r=json.loads((f.TASK/'EVALUATION_RESULT.json').read_text());errs={}
    with np.load(f.TASK/'EVALUATION_TRUTH.npz') as z:
        for mode in ['neural','behavior']:
            y=z[mode+'_truth'];scale=np.asarray(cfg['scales'][mode]);errs[mode]={}
            for name in ['simple','state','shared']:
                a=pred[mode+'__'+name];ls=[]
                # Scalar loop formulation, deliberately separate from losses().
                for i in range(7):
                    ss=0.;count=0
                    for c in range(y.shape[1]):
                        for b in range(7):
                            if np.isfinite(a[i,c,b]) and np.isfinite(y[i,c,b]):
                                ss+=((a[i,c,b]-y[i,c,b])/scale[c])**2;count+=1
                    ls.append(ss/count)
                ref=r['modalities'][mode]['per_worm_losses'][name]
                err=float(np.max(np.abs(np.asarray(ls)-ref)));assert err<1e-12
                errs[mode][name]=dict(mean_mse=float(np.mean(ls)),max_saved_difference=err)
    out=dict(at_utc=f.now(),frozen_hashes_valid=True,replayed_forecast_arrays=len(pred),forecast_max_abs_difference=max(differences.values()),forecast_differences=differences,independent_scalar_mse_formulation=errs,network_requests=0,new_biological_observations=0,independent_scientific_review=False)
    pathlib.Path(output).write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out,indent=2))
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--output',default=str(f.TASK/'REPRODUCTION.json'));a=p.parse_args();main(a.output)
