"""Proper curve scores, independent-animal comparisons and calibration."""
import numpy as np
from scipy.spatial.distance import pdist


def marginal_crps(samples,observed):
    """Unbiased Monte Carlo estimate E|X-y| - .5 E|X-X'| per cell."""
    a=np.asarray(samples,float);y=np.asarray(observed,float)
    if a.shape[1:]!=y.shape:raise ValueError((a.shape,y.shape))
    n=a.shape[0];z=np.sort(a,axis=0)
    coeff=(2*np.arange(n)-n+1).reshape((n,)+(1,)*(a.ndim-1))
    return np.mean(np.abs(a-y),axis=0)-np.sum(coeff*z,axis=0)/(n*(n-1))


def score(samples,observed,mask=None):
    a=np.asarray(samples,float);y=np.asarray(observed,float)
    valid=np.isfinite(y)
    if mask is not None:valid &=np.asarray(mask,bool)
    if not np.isfinite(a[:,valid]).all():
        raise FloatingPointError('Nonfinite forecast on an observed target; forecast failures cannot drop scored cells')
    cell=marginal_crps(a,y)
    # Equal weight per recorded metric, then equal weight per available bin.
    # Missing high-side cells never reduce the omission/right-choice weights.
    bymetric=np.array([np.mean(cell[:,j][valid[:,j]]) if valid[:,j].any() else np.nan for j in range(y.shape[-1])])
    mean=np.mean(a,axis=0);err=np.abs(mean-y)
    maes=np.array([np.mean(err[:,j][valid[:,j]]) if valid[:,j].any() else np.nan for j in range(y.shape[-1])])
    cv={};width={}
    for level in [.5,.8,.95]:
        lo,hi=np.quantile(a,[(1-level)/2,(1+level)/2],axis=0)
        cv[str(level)]=float(np.mean(((y>=lo)&(y<=hi))[valid]))
        width[str(level)]=float(np.mean((hi-lo)[valid]))
    # Joint trajectory score as a prespecified sensitivity. Scale every
    # observed coordinate equally; source unit remains one animal.
    aa=a[:,valid];yy=y[valid]
    energy=float(np.mean(np.linalg.norm(aa-yy,axis=1))-np.mean(pdist(aa))/2) if valid.any() else np.nan
    return dict(crps=float(np.nanmean(bymetric)),crps_by_metric=bymetric.tolist(),
                mae=float(np.nanmean(maes)),mae_by_metric=maes.tolist(),
                high_accuracy_mae=float(np.nanmean(maes[:2])),coverage=cv,width=width,
                energy=energy,n_cells=int(valid.sum()))


def paired_interval(differences,seed=891,replicates=10000):
    d=np.asarray(differences,float);d=d[np.isfinite(d)]
    if not len(d):return dict(n=0,mean=None,lo=None,hi=None)
    rng=np.random.default_rng(seed)
    bs=d[rng.integers(0,len(d),(replicates,len(d)))].mean(axis=1)
    return dict(n=len(d),mean=float(d.mean()),lo=float(np.quantile(bs,.025)),hi=float(np.quantile(bs,.975)))


def apply_discrepancy(samples,residual_bank,seed=0,scale=1.):
    """Frozen, zero-mean development residual uncertainty, never mean rescue.

    Each independent donor supplies a full correlated curve error. Centering
    is across development animals, not validation outcomes. Both raw and
    widened forecasts must be reported; broad intervals alone earn no gate.
    """
    a=np.asarray(samples,float);r=np.asarray(residual_bank,float)
    r=r[:,:a.shape[1],:]
    center=np.nanmean(r,axis=0);r=np.nan_to_num(r-center)
    rng=np.random.default_rng(seed)
    delta=r[rng.integers(len(r),size=len(a))]
    return np.clip(a+scale*delta,0,1)
