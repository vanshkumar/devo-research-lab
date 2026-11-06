"""Fixed studentizers, paired whole-animal max-T and declared sensitivities."""
import numpy as np
from scipy.stats import t


def resampling_counts(seed,R=20000,stratified=True):
    rng=np.random.default_rng(seed);out=np.zeros((R,64),np.int16)
    groups=[np.arange(40),np.arange(40,64)] if stratified else [np.arange(64)]
    for group in groups:
        choices=rng.choice(group,size=(R,len(group)),replace=True)
        np.add.at(out,(np.arange(R)[:,None],choices),1)
    return out


def se_for(X,stratified=True):
    if stratified:return np.sqrt((40/64)**2*np.var(X[:40],axis=0,ddof=1)/40+
                                 (24/64)**2*np.var(X[40:],axis=0,ddof=1)/24)
    return np.std(X,axis=0,ddof=1)/8


def joint_bands(X,primary_indices,counts,stratified=True):
    assert X.shape[0]==64 and np.isfinite(X).all()
    point=X.mean(0);se=se_for(X,stratified);active=se>1e-14
    assert np.all(np.ptp(X[:,~active],axis=0)<1e-12)
    primary=np.array(primary_indices,int);largest=[];primary_largest=[]
    for start in range(0,len(counts),256):
        centered=counts[start:start+256].astype(float)@X/64-point
        T=np.divide(centered,se[None,:],out=np.zeros_like(centered),where=active[None,:])
        largest.extend(np.max(np.abs(T),axis=1));primary_largest.extend(np.max(np.abs(T[:,primary]),axis=1))
    critical=float(np.quantile(largest,.95));primary_critical=float(np.quantile(primary_largest,.95))
    def band(crit):return dict(critical=crit,lower=(point-crit*se).tolist(),upper=(point+crit*se).tolist())
    return dict(point=point.tolist(),se=se.tolist(),joint=band(critical),primary=band(primary_critical),
                bonferroni_joint=band(float(t.ppf(1-.05/(2*X.shape[1]),23))),
                bonferroni_primary=band(float(t.ppf(1-.05/(2*len(primary)),23))),
                independent_units=64,stratum_counts=[40,24] if stratified else None,
                replicates=len(counts),zero_se_columns=np.flatnonzero(~active).tolist())


def site_sensitivity(X,labs,indices):
    labs=np.asarray(labs);sites=sorted(set(labs));indices=np.array(indices,int);Y=X[:,indices]
    point=Y.mean(0);cluster=[];site_means=[]
    for site in sites:
        use=labs==site
        cluster.append(np.sum(Y[use]-point,axis=0)/64)
        site_means.append(Y[use].mean(0))
    cluster=np.array(cluster);site_means=np.array(site_means);G=len(sites)
    se=np.sqrt(G/(G-1)*np.sum(cluster**2,axis=0))
    signs=np.array([[1 if (i>>j)&1 else -1 for j in range(G)] for i in range(2**G)])
    weights=np.sqrt(G/(G-1))
    values=weights*(signs@cluster)
    T=np.divide(values,se,out=np.zeros_like(values),where=se>1e-14)
    critical=float(np.quantile(np.max(np.abs(T),axis=1),.95))
    equal=site_means.mean(0);sese=site_means.std(0,ddof=1)/np.sqrt(G)
    bon=float(t.ppf(1-.05/(2*len(indices)),G-1))
    strata={}
    for name,values in [('old40',Y[:40]),('later24',Y[40:])]:
        m=values.mean(0);s=values.std(0,ddof=1)/np.sqrt(len(values))
        q=float(t.ppf(1-.05/(2*len(indices)),len(values)-1))
        strata[name]=dict(point=m.tolist(),se=s.tolist(),bonferroni_lower=(m-q*s).tolist(),
                          bonferroni_upper=(m+q*s).tolist(),n=len(values),df=len(values)-1)
    return dict(sites=sites,n_sites=G,animal_weighted_cluster_point=point.tolist(),
         cluster_wild_critical=critical,cluster_se=se.tolist(),cluster_lower=(point-critical*se).tolist(),
         cluster_upper=(point+critical*se).tolist(),sign_patterns=len(signs),
         equal_site_point=equal.tolist(),equal_site_bonferroni_lower=(equal-bon*sese).tolist(),
         equal_site_bonferroni_upper=(equal+bon*sese).tolist(),equal_site_df=G-1,
         per_site={s:site_means[i].tolist() for i,s in enumerate(sites)},
         old40_point=Y[:40].mean(0).tolist(),later24_point=Y[40:].mean(0).tolist(),
         stratum_bonferroni_bands=strata,
         leave_one_site_out={s:Y[labs!=s].mean(0).tolist() for s in sites},
         scope='Observed-site sensitivity only;9sites and singleton sites do not certify arbitrary-new-site equivalence')
