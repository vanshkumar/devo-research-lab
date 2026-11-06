"""Adversarial development checks; own checks are not independent review."""
import os
os.environ['OPENBLAS_NUM_THREADS']='1'
os.environ['OMP_NUM_THREADS']='1'
import copy,json,pathlib,datetime
import numpy as np
import forecast as f
def main():
    ds=f.load_development();res=json.loads((f.TASK/'DEVELOPMENT_RESULT.json').read_text())
    classes=res['classes'];out=dict(at_utc=f.now(),independent_review=False)
    # Actual prefix/feature invariance to completely replaced future outcomes.
    altered=copy.deepcopy(ds)
    for d in altered:
        future=d['t']>=-5
        d['neural'][:,future]=1e90;d['ratio'][:,future]=-1e90;d['behavior'][:,future]=np.nan
    inv={}
    for mode in ['neural','behavior']:
        b=f.make_bundle(ds,classes,mode,False);a=f.make_bundle(altered,classes,mode,False)
        inv[mode]={k:bool(np.array_equal(b[k],a[k],equal_nan=True)) for k in ['X','G','R']}
        assert all(inv[mode].values())
    out['future_response_invariance']=inv
    # Separate behavior channels; prevent large average pumping suppression being
    # presented as an individual reversal prediction.
    with np.load(f.TASK/'DEVELOPMENT_CV.npz') as z:
        y=z['behavior_truth'];entries={}
        for model in ['shared','local','state']:
            key=res['modalities']['behavior']['configs'][model]['key']
            p=z['behavior__'+key]
            err=np.mean((p-y)**2,axis=(0,2))
            entries[model]=dict(reverse_fraction_mse=float(err[0]),pumping_mse=float(err[1]))
        out['behavior_components']=entries
        out['neural_class_coverage_per_worm']=np.isfinite(z['neural_truth'][:,:,0]).sum(axis=1).tolist()
    # A completely different sensible fluorescence scale: fractional change about
    # own pre-heat mean. Same classes/endpoints/feature family, no new search.
    frac=copy.deepcopy(ds)
    for d in frac:d['neural']=d['ratio']-1.
    b=f.make_bundle(frac,classes,'neural')
    ff={}
    for model in ['shared','local','state']:
        aa=f.ALPHAS if model in ['local','state'] else [None]
        results=[]
        for a in aa:
            pred=f.cv_predict(b,model,a)
            ls=f.losses(pred,b['Y'],np.ones(len(classes)))
            results.append(dict(alpha=a,mse=float(np.mean(ls)),per_worm=ls.tolist()))
        ff[model]=min(results,key=lambda x:x['mse'])
    ff['state_gain_over_local']=1-ff['state']['mse']/ff['local']['mse']
    ff['state_gain_over_shared']=1-ff['state']['mse']/ff['shared']['mse']
    out['fractional_fluorescence_sensitivity']=ff
    # Timing/heterogeneity diagnostics: pre-heat spontaneous changes versus actual
    # post-heat persistent means. These are observational, not causal no-heat controls.
    pre=[];post=[];sham=[]
    for d in ds:
        t=d['t'];b=d['behavior'][1:3]
        first=(t>=-450)&(t<-240);last=(t>=-215)&(t<-5);after=(t>=30)&(t<240)
        p=np.mean(b[:,last],axis=1);pre.append(p)
        post.append(np.mean(b[:,after],axis=1)-p)
        sham.append(p-np.mean(b[:,first],axis=1))
    pre=np.asarray(pre);post=np.asarray(post);sham=np.asarray(sham)
    out['persistent_behavior_diagnostic']=dict(uids=[d['uid'] for d in ds],channels=['reverse_fraction','pumping'],pre_mean=pre.tolist(),post_minus_pre=post.tolist(),pre_spontaneous_change=sham.tolist(),mean_post_change=post.mean(axis=0).tolist(),sd_post_change=post.std(axis=0,ddof=1).tolist(),mean_pre_change=sham.mean(axis=0).tolist())
    # Independent algebraic numerical formulation for one nonconstant ridge fit.
    rng=np.random.default_rng(20261031)
    x=rng.normal(size=(11,9));y=rng.normal(size=(11,7));z=rng.normal(size=(2,9));a=.1
    p=f.ridge(x,y,z,a)
    mu=x.mean(0);sd=x.std(0);xx=(x-mu)/sd;zz=(z-mu)/sd;ym=y.mean(0)
    u,sv,vh=np.linalg.svd(xx,full_matrices=False)
    coef=np.einsum('ij,j,jk->ik',vh.T,sv/(sv**2+a*len(x)),np.einsum('ij,ik->jk',u,y-ym))
    ref=ym+np.einsum('ij,jk->ik',zz,coef)
    err=float(np.max(np.abs(ref-p)));assert err<1e-12
    out['ridge_svd_max_difference']=err
    f.save('ADVERSARIAL_DEVELOPMENT.json',out)
    print(json.dumps(out,indent=2))
if __name__=='__main__':main()
