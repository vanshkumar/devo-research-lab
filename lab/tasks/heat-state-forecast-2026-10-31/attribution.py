"""Two prespecified postvalidation feature knockouts, no alpha/recipe selection."""
import os
os.environ['OPENBLAS_NUM_THREADS']='1'
os.environ['OMP_NUM_THREADS']='1'
import numpy as np
import forecast as f
import evaluation as e
def main():
    fr=e.check_freeze();cfg=fr['configuration'];ds=f.load_development();ps=e.prefixes()
    tr=f.make_bundle(ds,cfg['classes'],'neural');te=f.make_bundle(ps,cfg['classes'],'neural',False)
    gt,ge=f.global_features(tr,te);alpha=cfg['primary']['neural']['configs']['state']['alpha']
    with np.load(f.TASK/'EVALUATION_TRUTH.npz') as z:y=z['neural_truth'].copy()
    rows={};preds={};rng=np.random.default_rng(20261031)
    with np.load(f.TASK/'EVALUATION_FORECASTS.npz') as z:local=z['neural__simple'].copy();full=z['neural__state'].copy()
    local_loss=f.losses(local,y,np.ones(len(cfg['classes'])))
    # Necessary matched-penalty control: the frozen local baseline selected alpha10,
    # whereas the frozen augmented family selected alpha1. Keep the initial
    # attribution output intact and report the matched control in a new artifact.
    matched=f.predict(tr,te,'local',alpha)
    matched_loss=f.losses(matched,y,np.ones(len(cfg['classes'])))
    rows['matched_alpha_local_only']=dict(fixed_alpha=alpha,mean_mse=float(matched_loss.mean()),per_worm_losses=matched_loss.tolist())
    for name,which in [('behavior_only',[0,1]),('neural_pcs_only',[2,3])]:
        out=np.full_like(local,np.nan)
        for c in range(y.shape[1]):
            ok=np.isfinite(tr['X'][:,c]).all(1)&np.isfinite(tr['Y'][:,c]).all(1)
            use=np.isfinite(te['X'][:,c]).all(1)
            x=np.concatenate([tr['X'][ok,c],gt[ok][:,which]],axis=1)
            zz=np.concatenate([te['X'][use,c],ge[use][:,which]],axis=1)
            out[use,c]=f.ridge(x,tr['Y'][ok,c],zz,alpha)
        losses=f.losses(out,y,np.ones(len(cfg['classes'])))
        rows[name]=dict(fixed_alpha=alpha,mean_mse=float(losses.mean()),per_worm_losses=losses.tolist(),comparison_with_frozen_local=e.summary(local_loss,losses,np.arange(7),rng),comparison_with_matched_alpha_local=e.summary(matched_loss,losses,np.arange(7),rng))
        preds[name]=out
    preds['matched_alpha_local_only']=matched
    np.savez_compressed(f.TASK/'POSTVALIDATION_MATCHED_FORECASTS.npz',**preds)
    out=dict(at_utc=f.now(),status='postvalidation consumed-data attribution with matched-penalty control; original attribution artifact retained; no model promotion',frozen_full_state_mse=float(f.losses(full,y,np.ones(len(cfg['classes']))).mean()),frozen_local_mse=float(local_loss.mean()),full_vs_matched_alpha_local=e.summary(matched_loss,f.losses(full,y,np.ones(len(cfg['classes']))),np.arange(7),rng),knockouts=rows)
    f.save('POSTVALIDATION_ATTRIBUTION_MATCHED.json',out);print(__import__('json').dumps(out,indent=2))
if __name__=='__main__':main()
