"""Frozen donor-resolved descriptive abundance analysis. Run from any directory."""
from pathlib import Path
import json, hashlib, sys, warnings
import numpy as np
import pandas as pd
from scipy import sparse, stats
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT/'outputs'/'abundance'
OUT.mkdir(parents=True, exist_ok=True)
SEED = 28102026
rng = np.random.default_rng(SEED)
prefix = sys.argv[1] if len(sys.argv)>1 else 'selected'
manifest=json.loads((ROOT/'inputs'/f'{prefix}_extraction_manifest.json').read_text())
for name in [f'{prefix}_obs.csv',f'{prefix}_counts.npz','raw_var.csv']:
    assert hashlib.sha256((ROOT/'inputs'/name).read_bytes()).hexdigest()==manifest[name]['sha256'], f'Changed input: {name}'
obs = pd.read_csv(ROOT/'inputs'/f'{prefix}_obs.csv', keep_default_na=False)
var = pd.read_csv(ROOT/'inputs'/'raw_var.csv', keep_default_na=False)
X = sparse.load_npz(ROOT/'inputs'/f'{prefix}_counts.npz').tocsr()
assert X.shape == (len(obs),len(var))
assert obs.row_index.is_unique
genes={g:int(var.loc[var.feature_name.eq(g),'column_index'].iloc[0]) for g in ['OXT','AVP']}
for g,j in genes.items(): obs[g]=X[:,j].toarray().ravel()
obs['T'] = np.asarray(X.sum(axis=1, dtype=np.float64)).ravel()
obs['B'] = obs['T']-obs.OXT-obs.AVP
obs['nFeature_actual'] = np.asarray((X>0).sum(axis=1)).ravel()
mt_cols=var.loc[var.feature_name.str.startswith('MT-'),'column_index'].to_numpy(dtype=int)
obs['mt_counts']=np.asarray(X[:,mt_cols].sum(axis=1,dtype=np.float64)).ravel()
obs['mt_fraction_actual']=obs.mt_counts/obs['T'].clip(lower=1)
obs['minor'] = obs[['OXT','AVP']].min(axis=1)
obs['major'] = obs[['OXT','AVP']].max(axis=1)
obs['ratio'] = obs['minor']/obs['major'].clip(lower=1)
obs['minor_depth'] = obs['minor']/obs['T'].clip(lower=1)
obs['minor_peptide_fraction'] = obs['minor']/(obs.OXT+obs.AVP).clip(lower=1)
obs['cluster'] = obs.C4_named.str.split().str[0]
obs['substantial'] = (obs['minor']>=10)&(obs.ratio>=.1)
obs['substantial_depth'] = obs.substantial&(obs.minor_depth>=.001)
obs['joint'] = (obs.OXT>0)&(obs.AVP>0)
obs.to_csv(OUT/'per_cell.csv.gz', index=False)
peptide=obs[obs.cluster.isin(['C4-296','C4-312','C4-313','C4-315'])].copy()
target=peptide[peptide.cluster.eq('C4-313')].copy()
target.to_csv(OUT/'candidate_per_cell.csv', index=False)
peptide.to_csv(OUT/'peptide_per_cell.csv', index=False)

def ci_binary(v):
    # Equivalent to individual-cell nonparametric bootstrap for binary mean.
    z=rng.binomial(len(v),float(np.mean(v)),size=2000)/len(v)
    return np.quantile(z,[.025,.975])

def summarize(z,scope,key):
    out={'scope':scope,'group':str(key),'cluster':z.cluster.iloc[0] if z.cluster.nunique()==1 else 'pooled',
         'Dataset':z.Dataset.iloc[0] if z.Dataset.nunique()==1 else 'pooled',
         'donor_id':z.donor_id.iloc[0] if z.donor_id.nunique()==1 else 'pooled','n':len(z),
         'OXT_positive':int((z.OXT>0).sum()),'AVP_positive':int((z.AVP>0).sum()),
         'joint_positive':int(z.joint.sum()),'substantial_n':int(z.substantial.sum()),
         'substantial_fraction':float(z.substantial.mean()),
         'substantial_depth_n':int(z.substantial_depth.sum()),
         'k20_r10_n':int(((z['minor']>=20)&(z.ratio>=.1)).sum())}
    lo,hi=ci_binary(z.substantial)
    out.update(substantial_cell_bootstrap_lo=lo,substantial_cell_bootstrap_hi=hi)
    for v in ['OXT','AVP','minor','major','ratio','minor_depth','minor_peptide_fraction','T','B','nFeature_RNA','percent_mt']:
        for q in [0,.1,.25,.5,.75,.9,.95,.99,1]: out[f'{v}_q{int(q*100):02}']=float(z[v].quantile(q))
    return out

summaries=[]
for cluster,z in peptide.groupby('cluster',sort=True):
    summaries.append(summarize(z,'cluster',cluster))
    for d,y in z.groupby('donor_id',sort=True): summaries.append(summarize(y,'donor',d))
    for d,y in z.groupby('Dataset',sort=True): summaries.append(summarize(y,'study',d))
pd.DataFrame(summaries).to_csv(OUT/'donor_abundance.csv', index=False)

grid=[]
curves=[]
for (cluster,d),z in peptide.groupby(['cluster','donor_id'],sort=True):
    for k in [1,2,5,10,20,50,100]:
        for r in [0,.01,.05,.10,.25,.50]:
            for f in [0,.0001,.0005,.001,.005,.01]:
                hit=(z['minor']>=k)&(z.ratio>=r)&(z.minor_depth>=f)
                grid.append(dict(cluster=cluster,donor_id=d,Dataset=z.Dataset.iloc[0],n=len(z),k=k,ratio_min=r,depth_fraction_min=f,positive=int(hit.sum()),fraction=float(hit.mean())))
    for k in np.unique(np.r_[0,1,2,3,5,10,20,50,100,200,500,1000,z['minor'].values]):
        curves.append(dict(cluster=cluster,donor_id=d,n=len(z),minor_min=k,fraction=float((z['minor']>=k).mean())))
pd.DataFrame(grid).to_csv(OUT/'threshold_grid.csv',index=False)
pd.DataFrame(curves).to_csv(OUT/'minor_survival.csv',index=False)

corr=[]
qc=[]
for d,z in target.groupby('donor_id',sort=True):
    for a in ['minor','ratio','minor_depth','substantial']:
        for b in ['B','T','nFeature_RNA','percent_mt']:
            r=float(stats.spearmanr(z[a],z[b]).statistic) if len(z)>2 and z[a].nunique()>1 and z[b].nunique()>1 else np.nan
            corr.append(dict(donor_id=d,Dataset=z.Dataset.iloc[0],n=len(z),outcome=a,covariate=b,spearman=r))
    # Selected matrix may be case/control enriched. QC reference uses whole-atlas metadata,
    # not the sampling distribution, except the explicitly target-relative sensitivity.
allobs=pd.read_csv(ROOT/'inputs'/'obs.csv',keep_default_na=False)
for d,z in target.groupby('donor_id',sort=True):
    context=allobs[allobs.donor_id.eq(d)&allobs.C4_named.str.startswith('C4-')]
    ref={v:context[v].quantile(.95) for v in ['nCount_RNA','nFeature_RNA','percent_mt']}
    # T threshold uses nCount metadata whose exact agreement is separately checked below.
    masks={'all':np.ones(len(z),bool),'no_top5_metadata_depth':z.nCount_RNA<=ref['nCount_RNA'],
           'no_top5_features':z.nFeature_RNA<=ref['nFeature_RNA'],
           'no_top5_mt':z.percent_mt<=ref['percent_mt'],
           'no_target_top10_depth':z['T']<=z['T'].quantile(.9)}
    masks['all_three_metadata_qc']=masks['no_top5_metadata_depth']&masks['no_top5_features']&masks['no_top5_mt']
    if prefix=='selected':
        near=obs[obs.donor_id.eq(d)&obs.C4_named.str.contains('Mid-3')]
        masks['no_top5_actual_depth_mid3']=z['T']<=near['T'].quantile(.95)
        masks['no_top5_actual_features_mid3']=z.nFeature_actual<=near.nFeature_actual.quantile(.95)
        masks['no_top5_actual_mt_mid3']=z.mt_fraction_actual<=near.mt_fraction_actual.quantile(.95)
        masks['all_three_actual_mid3_qc']=masks['no_top5_actual_depth_mid3']&masks['no_top5_actual_features_mid3']&masks['no_top5_actual_mt_mid3']
    for name,m in masks.items():
        y=z[m]
        qc.append(dict(donor_id=d,Dataset=z.Dataset.iloc[0],filter=name,n=len(y),substantial_n=int(y.substantial.sum()),fraction=float(y.substantial.mean()) if len(y) else np.nan,depth_fraction=float(y.substantial_depth.mean()) if len(y) else np.nan,median_minor=float(y['minor'].median()) if len(y) else np.nan))
    for binid,y in z.groupby(pd.qcut(z['B'].rank(method='first'),q=min(4,len(z)),labels=False)):
        qc.append(dict(donor_id=d,Dataset=z.Dataset.iloc[0],filter=f'depth_quartile_{binid+1}',n=len(y),substantial_n=int(y.substantial.sum()),fraction=float(y.substantial.mean()),depth_fraction=float(y.substantial_depth.mean()),median_minor=float(y['minor'].median())))
pd.DataFrame(corr).to_csv(OUT/'within_donor_correlations.csv',index=False)
pd.DataFrame(qc).to_csv(OUT/'quality_depth_sensitivity.csv',index=False)

is_integer=bool(np.all(X.data==np.floor(X.data)))
thin=[]
if is_integer:
    # Choose common target total from all target counts, a prespecified descriptive
    # depth sensitivity (not used in labels/classifier).
    for depth in [1000,3000, float(target['T'].quantile(.1))]:
        for d,z in target.groupby('donor_id',sort=True):
            p=np.minimum(1,depth/z['T'].clip(lower=1).values)
            O=rng.binomial(z.OXT.to_numpy(dtype=np.int64)[None,:],p[None,:],size=(100,len(z)))
            A=rng.binomial(z.AVP.to_numpy(dtype=np.int64)[None,:],p[None,:],size=(100,len(z)))
            m=np.minimum(O,A); M=np.maximum(O,A)
            f=((m>=10)&(m>=.1*M)).mean(axis=1)
            thin.append(dict(donor_id=d,Dataset=z.Dataset.iloc[0],n=len(z),target_expected_T=depth,mean_fraction=f.mean(),lo=np.quantile(f,.025),hi=np.quantile(f,.975)))
pd.DataFrame(thin).to_csv(OUT/'thinning.csv',index=False)

audit=[]
for d,z in obs.groupby('donor_id'):
    if len(z)==0: continue
    audit.append(dict(donor_id=d,Dataset=z.Dataset.iloc[0],n=len(z),count_deficit_median=float((z.nCount_RNA-z['T']).median()),count_deficit_fraction_median=float(((z.nCount_RNA-z['T'])/z.nCount_RNA).median()),features_deficit_median=float((z.nFeature_RNA-z.nFeature_actual).median()),median_exported_mt=float(z.percent_mt.median()),median_actual_mt_fraction=float(z.mt_fraction_actual.median()),median_exported_to_actual_mt=float((z.percent_mt/z.mt_fraction_actual.replace(0,np.nan)).median())))
pd.DataFrame(audit).to_csv(OUT/'measurement_audit.csv',index=False)

donors=target.groupby('donor_id',sort=True).size().sort_values(ascending=False).index.tolist()
colors=plt.cm.tab10(np.arange(len(donors)))
plt.rcParams.update({'font.size':10,'axes.spines.top':False,'axes.spines.right':False})
fig,axs=plt.subplots(2,3,figsize=(13,8),layout='constrained')
for ax,d,c in zip(axs.flat,donors,colors):
    z=target[target.donor_id.eq(d)]
    ax.scatter(z.OXT+1,z.AVP+1,c=np.where(z.substantial,'#d55e00','#0072b2'),s=22,alpha=.7,linewidths=0)
    ax.set(xscale='log',yscale='log',xlabel='OXT count + 1',ylabel='AVP count + 1',title=f'{d} ({z.Dataset.iloc[0]})\nn={len(z)}, substantial={int(z.substantial.sum())}')
    mx=max(100,(target[['OXT','AVP']].max().max()+1)*1.3)
    ax.plot([1,mx],[1,mx],c='gray',lw=.7,ls='--')
    ax.axvline(11,c='gray',lw=.6); ax.axhline(11,c='gray',lw=.6)
    ax.set_xlim(.8,mx); ax.set_ylim(.8,mx)
fig.suptitle('C4-313: actual joint peptide counts by donor\nOrange: minor ≥10 and minor/major ≥0.10; blue: other observations',fontsize=13)
fig.savefig(OUT/'joint_counts.png',dpi=180); fig.savefig(OUT/'joint_counts.pdf'); plt.close(fig)
fig,axs=plt.subplots(1,3,figsize=(14,4),layout='constrained')
for d,c in zip(donors,colors):
    z=target[target.donor_id.eq(d)]
    ks=np.unique(np.r_[1,z['minor'].values[z['minor'].values>=1]])
    axs[0].step(ks,[(z['minor']>=k).mean() for k in ks],where='post',label=f'{d} (n={len(z)})',color=c)
    rs=np.sort(z.ratio.values); axs[1].step(rs,np.arange(1,len(rs)+1)/len(rs),where='post',color=c)
    fs=np.sort(z.minor_depth.values); axs[2].step(fs,np.arange(1,len(fs)+1)/len(fs),where='post',color=c)
axs[0].set(xscale='log',xlabel='Minimum minor-gene count',ylabel='Fraction of all donor target cells',ylim=(0,1.03)); axs[0].axvline(10,c='gray',ls=':')
axs[1].set(xlabel='Minor / major peptide count',ylabel='Cumulative fraction',xlim=(0,1),ylim=(0,1.03)); axs[1].axvline(.1,c='gray',ls=':')
axs[2].set(xscale='symlog',xlabel='Minor count / total counts',ylabel='Cumulative fraction',ylim=(0,1.03)); axs[2].set_xscale('symlog',linthresh=.00001); axs[2].axvline(.001,c='gray',ls=':')
axs[0].legend(fontsize=7,loc='upper right')
fig.savefig(OUT/'abundance_curves.png',dpi=180);fig.savefig(OUT/'abundance_curves.pdf');plt.close(fig)

summary={'input_prefix':prefix,'shape':list(X.shape),'nnz':X.nnz,'nonnegative_finite':bool(np.all(np.isfinite(X.data)) and np.all(X.data>=0)),
         'all_stored_values_integer':is_integer,'metadata_count_max_abs_difference':float(np.max(np.abs(obs['T']-obs.nCount_RNA))),
         'metadata_features_max_abs_difference':float(np.max(np.abs(obs.nFeature_actual-obs.nFeature_RNA))),
         'target_n':len(target),'target_joint':int(target.joint.sum()),'target_substantial':int(target.substantial.sum()),'target_substantial_depth':int(target.substantial_depth.sum()),
         'target_substantial_using_metadata_depth':int((target.substantial&(target['minor']/target.nCount_RNA>=.001)).sum()),
         'target_donors':donors,'target_median_minor':float(target['minor'].median()),'target_median_ratio':float(target.ratio.median()),
         'target_minor_ge20':int((target['minor']>=20).sum()),'target_k20_r10':int(((target['minor']>=20)&(target.ratio>=.1)).sum()),
         'source_file_hashes':{f'{prefix}_{kind}'+ext:hashlib.sha256((ROOT/'inputs'/(f'{prefix}_{kind}'+ext)).read_bytes()).hexdigest() for kind,ext in [('obs','.csv'),('counts','.npz')]}}
(OUT/'summary.json').write_text(json.dumps(summary,indent=2)+'\n')
print(json.dumps(summary,indent=2))
print(pd.DataFrame(summaries).query('cluster == "C4-313"')[['scope','donor_id','Dataset','n','joint_positive','substantial_n','substantial_depth_n','minor_q50','ratio_q50']].to_string(index=False))
