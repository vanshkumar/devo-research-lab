#!/usr/bin/env python3
"""Empirical nuisance and known-effect controls. Inputs are immutable sparse subsets."""
from pathlib import Path
import argparse,json,hashlib,sys,warnings,time
import numpy as np
import pandas as pd
from scipy import sparse,optimize,special,stats

ROOT=Path(__file__).resolve().parents[2]; OUT=ROOT/'outputs'/'technical'; OUT.mkdir(parents=True,exist_ok=True)
SEED=28102026
POOLS=['near_mid3','broad_neuronal','non_neuronal']

def load():
    x=sparse.load_npz(ROOT/'inputs'/'selected_counts.npz').astype(np.float64)
    o=pd.read_csv(ROOT/'inputs'/'selected_obs.csv'); f=pd.read_csv(ROOT/'inputs'/'raw_var.csv')
    ji=[int(f.index[f.feature_name.eq(g)][0]) for g in ['OXT','AVP']]
    o['OXT']=x[:,ji[0]].toarray().ravel();o['AVP']=x[:,ji[1]].toarray().ravel()
    o['T']=np.asarray(x.sum(1)).ravel();o['B']=o['T']-o.OXT-o.AVP
    o['m']=np.minimum(o.OXT,o.AVP);o['M']=np.maximum(o.OXT,o.AVP)
    o['minor_gene']=np.where(o.OXT>=o.AVP,'AVP','OXT')
    o['ratio']=o.m/np.maximum(o.M,1)
    o['sub']=(o.m>=10)&(o.ratio>=.1)
    o['np_features']=np.diff(x.indptr)-(o.OXT>0).astype(int)-(o.AVP>0).astype(int)
    assert np.all(x.data==np.floor(x.data)) and np.all(np.isfinite(x.data))
    return x,o,f,ji

def shape_mom(c,b,q):
    mu=q*b
    alpha=max(np.sum((c-mu)**2-c)/max(np.sum(mu**2),1e-12),.001)
    return float(np.clip(1/alpha,.05,1000))

def background(x,o,f,ji):
    target=o[o.pool.eq('candidate')]; rows=[]; individual=[]; rates=[]
    for pool in POOLS:
        co=o[o.pool.eq(pool)]
        for donor,t in target.groupby('donor_id',sort=True):
            c=co[co.donor_id.eq(donor)]
            if len(c)==0:continue
            for gene in ['OXT','AVP']:
                q=(c[gene].sum()+.5)/(c.B.sum()+1); k=shape_mom(c[gene].values,c.B.values,q)
                rates.append(dict(pool=pool,donor=donor,study=t.Dataset.iloc[0],gene=gene,n=len(c),counts=c[gene].sum(),exposure=c.B.sum(),rate=q,shape=k,rate_q90=np.quantile(c[gene]/np.maximum(c.B,1),.9),rate_q99=np.quantile(c[gene]/np.maximum(c.B,1),.99)))
            donor_predictions={}
            for i,r in t.iterrows():
                dist=np.abs(np.log1p(c.B)-np.log1p(r.B)); match=c.loc[dist.nsmallest(min(100,len(c))).index]
                gene=r.minor_gene; vals=match[gene].values;b=match.B.values
                q=(vals.sum()+.5)/(b.sum()+1);k=shape_mom(vals,b,q)
                q90=float(np.quantile(vals/np.maximum(b,1),.9));q99=float(np.quantile(vals/np.maximum(b,1),.99))
                rec=dict(row_index=int(r.row_index),donor=donor,study=r.Dataset,pool=pool,gene=gene,observed_minor=r.m,major=r.M,B=r.B,matched_n=len(match),matched_logdepth_max=float(dist.loc[match.index].max()),q_mean=q,q90=q90,q99=q99,shape=k,observed_to_expected=r.m/max(q*r.B,1e-12))
                for mult in [1,2,5,10,20]:
                    mu=max(q*r.B*mult,1e-12);p=k/(k+mu)
                    low=max(10,int(np.ceil(.1*r.M-1e-10)))
                    rec['mean_'+str(mult)]=mu
                    rec['nb_primary_'+str(mult)]=0 if r.M<low else max(0,float((stats.nbinom.cdf(r.M,k,p)-stats.nbinom.cdf(low-1,k,p))/max(stats.nbinom.cdf(r.M,k,p),1e-300)))
                    rec['poisson_primary_'+str(mult)]=0 if r.M<low else max(0,float((stats.poisson.cdf(r.M,mu)-stats.poisson.cdf(low-1,mu))/max(stats.poisson.cdf(r.M,mu),1e-300)))
                    rec['nb_minor10_'+str(mult)]=float(stats.nbinom.sf(9,k,p))
                for lab,rate in [('q90',q90),('q99',q99)]:
                    mu=max(rate*r.B,1e-12)
                    rec['poisson_primary_'+lab]=0 if r.M<low else max(0,float((stats.poisson.cdf(r.M,mu)-stats.poisson.cdf(low-1,mu))/max(stats.poisson.cdf(r.M,mu),1e-300)))
                individual.append(rec)
            z=pd.DataFrame(individual); z=z[(z.pool==pool)&(z.donor==donor)]
            for mult in [1,2,5,10,20]:
                rows.append(dict(pool=pool,donor=donor,study=t.Dataset.iloc[0],n=len(t),observed_primary=int(t['sub'].sum()),observed_minor10=int((t.m>=10).sum()),multiplier=mult,expected_primary_nb=z['nb_primary_'+str(mult)].sum(),expected_primary_poisson=z['poisson_primary_'+str(mult)].sum(),expected_minor10_nb=z['nb_minor10_'+str(mult)].sum(),median_minor_multiplier=z.observed_to_expected.median(),q90_expected_primary=z.poisson_primary_q90.sum(),q99_expected_primary=z.poisson_primary_q99.sum()))
    pd.DataFrame(rows).to_csv(OUT/'background_sensitivity.csv',index=False)
    pd.DataFrame(individual).to_csv(OUT/'background_per_cell.csv',index=False)
    pd.DataFrame(rates).to_csv(OUT/'background_rates.csv',index=False)
    # The two retained substantial observations and their library-local empirical backgrounds.
    samples=[]
    for _,r in target[target['sub']].iterrows():
        for pool in POOLS:
            c=o[(o.pool==pool)&(o.Sample_ID==r.Sample_ID)]
            if not len(c):continue
            for gene in ['OXT','AVP']:
                q=(c[gene].sum()+.5)/(c.B.sum()+1)
                samples.append(dict(row_index=int(r.row_index),sample=r.Sample_ID,pool=pool,gene=gene,n=len(c),background_counts=c[gene].sum(),exposure=c.B.sum(),rate=q,expected_count_at_target=q*r.B,target_count=r[gene],ratio_to_background=r[gene]/max(q*r.B,1e-12)))
    pd.DataFrame(samples).to_csv(OUT/'rare_cases_sample_background.csv',index=False)
    print('background complete',flush=True)

def nb_logp(y,M,mu,k,truncated=True):
    mu=np.maximum(mu,1e-10);p=k/(k+mu)
    lp=stats.nbinom.logpmf(y,k,p)
    if truncated:lp=lp-stats.nbinom.logcdf(M,k,p)
    return lp

def predict(theta,y,M,B,q,kref,alt,truncated=True):
    alpha=np.exp(theta[0]); beta=.01*theta[1]; k=np.exp(theta[2]);mu=alpha*q*B+beta*M
    l0=nb_logp(y,M,mu,k,truncated)
    if not alt:return l0
    mixbeta=np.exp(theta[3]);w=special.expit(theta[4]);l1=nb_logp(y,M,alpha*q*B+mixbeta*M,k,truncated)
    return np.logaddexp(np.log1p(-w)+l0,np.log(w)+l1)

def fit(y,M,B,q,kref,alt,truncated=True):
    logk=np.log(np.clip(kref,.05,1000))
    bounds=[(np.log(.1),np.log(20)),(0.,1.),(np.log(.05),np.log(1000))]
    starts=[[0.,.1,logk],[np.log(2),.5,0.]]
    if alt:
        bounds+= [(np.log(.1),0.),(-10.,3.)]
        starts=[v+[np.log(.2),-3.] for v in starts]+[[0.,0.,logk,np.log(.1),-1.]]
    def objective(v):
        lp=predict(v,y,M,B,q,kref,alt,truncated)
        pen=.5*(v[0]/np.log(5))**2+.5*((v[2]-logk)/2)**2
        if alt:pen+=3*np.logaddexp(0,v[4])
        val=-np.sum(lp)+pen
        return val if np.isfinite(val) else 1e100
    results=[optimize.minimize(objective,v,method='L-BFGS-B',bounds=bounds,options={'maxiter':200,'ftol':1e-9}) for v in starts]
    best=min(results,key=lambda r:r.fun)
    return best.x,dict(success=bool(best.success),objective=float(best.fun),message=str(best.message),iterations=int(best.nit))

def prepare_model(o,pool='near_mid3',fixed_avp=False):
    t=o[o.pool.eq('candidate') & (o.M>0)].copy()
    if fixed_avp:t=t[t.OXT>=t.AVP].copy()
    donors=[d for d,n in t.donor_id.value_counts().items() if n>=20]
    t=t[t.donor_id.isin(donors)].copy().reset_index(drop=True)
    co=o[o.pool.eq(pool)]
    folds=[]
    for donor in sorted(donors):
        train=t.donor_id.ne(donor).values;test=~train
        q=np.empty(len(t));klist=[];source_rates={}
        for study in t.Dataset.unique():
            sc=co[(co.Dataset==study)&(co.donor_id!=donor)&(co.donor_id.isin(donors))]
            for gene in ['OXT','AVP']:
                # Equal-donor weighting prevents one control-rich donor dominating rates.
                dr=[(z[gene].sum()+.5)/(z.B.sum()+1) for _,z in sc.groupby('donor_id')]
                rate=float(np.mean(dr));source_rates[study+'_'+gene]=rate
                klist.append(shape_mom(sc[gene].values,sc.B.values,rate))
                q[(t.Dataset==study)&(t.minor_gene==gene)]=rate
        kref=float(np.exp(np.mean(np.log(klist))))
        folds.append(dict(donor=donor,train=train,test=test,q=q,kref=kref,rates=source_rates))
    return t,folds

def model_cv(t,folds,y=None,truncated=True):
    if y is None:y=t.m.values
    M=t.M.values;B=t.B.values;results=[];parameters=[]
    for fo in folds:
        tr=fo['train'];te=fo['test'];q=fo['q'];kr=fo['kref']; fits=[]
        for alt in [False,True]:
            par,meta=fit(y[tr],M[tr],B[tr],q[tr],kr,alt,truncated)
            lp=predict(par,y[te],M[te],B[te],q[te],kr,alt,truncated)
            fits.append((par,lp,meta))
            parameters.append(dict(donor=fo['donor'],model='mixed' if alt else 'trace',alpha=float(np.exp(par[0])),beta_trace=float(.01*par[1]),shape=float(np.exp(par[2])),beta_mixed=float(np.exp(par[3])) if alt else None,mixed_weight=float(special.expit(par[4])) if alt else 0,control_shape_ref=kr,**meta,**fo['rates']))
        delta=fits[1][1]-fits[0][1]
        results.append(dict(donor=fo['donor'],study=t.loc[te,'Dataset'].iloc[0],n=int(te.sum()),trace_logscore=float(fits[0][1].sum()),mixed_logscore=float(fits[1][1].sum()),delta_logscore=float(delta.sum()),delta_per_cell=float(delta.mean()),n_better=int((delta>0).sum()),min_delta=float(delta.min()),max_delta=float(delta.max()),trace_success=fits[0][2]['success'],mixed_success=fits[1][2]['success']))
    return pd.DataFrame(results),pd.DataFrame(parameters)

def models(o):
    allres=[];allpar=[];cellresults=[]
    for pool in POOLS:
        for fixed in [False,True]:
            t,folds=prepare_model(o,pool,fixed)
            r,p=model_cv(t,folds,truncated=True)
            r['pool']=pool;r['conditioning']='AVP_given_OXT_dominant_truncated' if fixed else 'minor_given_major_truncated'
            p['pool']=pool;p['conditioning']=r.conditioning.iloc[0]
            allres.append(r);allpar.append(p)
            for fo in folds:
                te=fo['test']; vals=[]
                for alt in [False,True]:
                    pr=p[(p.donor==fo['donor'])&(p.model==('mixed' if alt else 'trace'))].iloc[0]
                    par=[np.log(pr.alpha),pr.beta_trace/.01,np.log(pr['shape'])]
                    if alt:par += [np.log(pr.beta_mixed),special.logit(pr.mixed_weight)]
                    vals.append(predict(par,t.m.values[te],t.M.values[te],t.B.values[te],fo['q'][te],fo['kref'],alt,True))
                for j,(_,cell) in enumerate(t.loc[te].iterrows()):
                    cellresults.append(dict(row_index=int(cell.row_index),donor=fo['donor'],pool=pool,conditioning=r.conditioning.iloc[0],minor=cell.m,major=cell.M,primary=bool(cell['sub']),delta_logscore=float(vals[1][j]-vals[0][j])))
            print('model',pool,fixed,'deltas',r.delta_logscore.round(3).tolist(),flush=True)
    pd.concat(allres).to_csv(OUT/'model_heldout_scores.csv',index=False)
    pd.concat(allpar).to_csv(OUT/'model_parameters.csv',index=False)
    pd.DataFrame(cellresults).to_csv(OUT/'model_per_cell_scores.csv',index=False)

def simulate(o,reps):
    t,folds=prepare_model(o); rng=np.random.default_rng(SEED+10);M=t.M.values;B=t.B.values
    # Design calibrated from controls only; no fitting of target minor outcomes.
    co=o[o.pool.eq('near_mid3')]; q=np.empty(len(t));kr=[]
    for (donor,gene),idx in t.groupby(['donor_id','minor_gene']).groups.items():
        c=co[co.donor_id.eq(donor)];rate=(c[gene].sum()+.5)/(c.B.sum()+1)
        q[list(idx)]=rate;kr.append(shape_mom(c[gene].values,c.B.values,rate))
    kref=float(np.exp(np.mean(np.log(kr))));shapes=[kref,1.]
    rows=[]; threshold_rows=[]
    scenarios=[('null_control',0.,.1,kref),('null_overdispersed',0.,.1,.5),('mixed10pct_ratio10',.1,.1,kref),('mixed30pct_ratio10',.3,.1,kref),('mixed30pct_ratio25',.3,.25,kref),('mixed50pct_ratio25',.5,.25,kref)]
    for name,w,beta,k in scenarios:
        for rep in range(reps):
            ismix=rng.random(len(t))<w
            mu=q*B+np.where(ismix,beta,.001)*M
            p=k/(k+mu);F=stats.nbinom.cdf(M,k,p)
            y=stats.nbinom.ppf(rng.random(len(t))*F,k,p).astype(int)
            r,_=model_cv(t,folds,y=y,truncated=True)
            for _,a in r.iterrows():rows.append(dict(scenario=name,replicate=rep,injected_fraction=w,injected_ratio=beta,injected_shape=k,**a.to_dict()))
            for donor,g in t.groupby('donor_id'):
                idx=g.index.values;hit=(y[idx]>=10)&(y[idx]/M[idx]>=.1)
                threshold_rows.append(dict(scenario=name,replicate=rep,donor=donor,n=len(idx),injected_n=int(ismix[idx].sum()),observed_primary_n=int(hit.sum()),realized_positive_recovery=float(hit[ismix[idx]].mean()) if ismix[idx].any() else np.nan,false_positive_fraction=float(hit[~ismix[idx]].mean()) if (~ismix[idx]).any() else np.nan))
        print('simulation',name,'complete',flush=True)
    pd.DataFrame(rows).to_csv(OUT/'model_simulation_scores.csv',index=False)
    pd.DataFrame(threshold_rows).to_csv(OUT/'model_simulation_thresholds.csv',index=False)
    # Independent direct Poisson signal addition to actual minority counts. No truncated-model generator.
    # Include peptide-zero cells in detectability denominators, unlike the conditional count model.
    t=o[o.pool.eq('candidate')].copy()
    t=t[t.donor_id.map(t.donor_id.value_counts())>=20].reset_index(drop=True)
    M=t.M.values
    rows=[]
    for frac in [.1,.25,.5]:
        for rep in range(200):
            # mean added minor component ratio to measured dominant abundance; keep original counts.
            y=t.m.values+rng.poisson(frac*M)
            mm=np.minimum(M,y);MM=np.maximum(M,y)
            hit=(mm>=10)&(mm/np.maximum(MM,1)>=.1)
            for donor,g in t.groupby('donor_id'):
                idx=g.index.values;rows.append(dict(injected_ratio=frac,replicate=rep,donor=donor,n=len(idx),detected=int(hit[idx].sum()),fraction=float(hit[idx].mean())))
    pd.DataFrame(rows).to_csv(OUT/'direct_injection_recovery.csv',index=False)

def doublets(x,o,f,ji):
    rng=np.random.default_rng(SEED+20);pep=o[o.pool.isin(['candidate','peptide_comparison'])]
    po=pep[(pep.OXT>=10)&(pep.AVP/pep.OXT<=.01)];pa=pep[(pep.AVP>=10)&(pep.OXT/pep.AVP<=.01)]
    target=o[o.pool.eq('candidate')];rows=[];details=[]
    # Actual sparse-profile support and Poisson occupancy expectations are computed without densifying atlas.
    for donor,t in target.groupby('donor_id'):
        a=po[po.donor_id.eq(donor)];b=pa[pa.donor_id.eq(donor)]
        if not len(a) or not len(b):
            rows.append(dict(donor=donor,study=t.Dataset.iloc[0],weight_O=np.nan,n_synthetic=0,n_Oparents=len(a),n_Aparents=len(b),reason='no opposite parents'))
            continue
        for w in [.25,.5,.75]:
            nr=500; hit=[];hit_sum=[];features=[];depths=[];ratios=[]
            for rep in range(nr):
                ia=int(rng.choice(a.index.values));ib=int(rng.choice(b.index.values));rt=t.iloc[int(rng.integers(len(t)))];T=float(rt['T'])
                u=x.getrow(ia);v=x.getrow(ib);profile=u*(w/o.loc[ia,'T'])+v*((1-w)/o.loc[ib,'T']);profile=profile.tocsr()
                counts=rng.poisson(profile.data*T);ix=profile.indices
                O=float(counts[ix==ji[0]].sum());A=float(counts[ix==ji[1]].sum());m=min(O,A);M=max(O,A);ratio=m/max(M,1);yes=(m>=10 and ratio>=.1)
                # Summed parent libraries correspond to the actual technical co-encapsulation comparison.
                Os=o.loc[ia,'OXT']+o.loc[ib,'OXT'];As=o.loc[ia,'AVP']+o.loc[ib,'AVP'];ys=min(Os,As)>=10 and min(Os,As)/max(Os,As)>=.1
                nfeat=int(((counts>0)&(~np.isin(ix,ji))).sum());hit.append(yes);hit_sum.append(ys);features.append(nfeat);depths.append(counts.sum());ratios.append(ratio)
                if rep<100:details.append(dict(donor=donor,weight_O=w,parent_O_row=int(o.loc[ia,'row_index']),parent_A_row=int(o.loc[ib,'row_index']),target_depth_row=int(rt.row_index),target_T=T,sim_T=int(counts.sum()),OXT=O,AVP=A,minor=m,ratio=ratio,primary=bool(yes),nonpeptide_features=nfeat))
            rows.append(dict(donor=donor,study=t.Dataset.iloc[0],weight_O=w,n_synthetic=nr,n_Oparents=len(a),n_Aparents=len(b),primary_fraction=np.mean(hit),summed_parent_primary_fraction=np.mean(hit_sum),nonpeptide_features_median=np.median(features),sim_depth_median=np.median(depths),ratio_median=np.median(ratios),reason=''))
    pd.DataFrame(rows).to_csv(OUT/'synthetic_doublet_summary.csv',index=False)
    pd.DataFrame(details).to_csv(OUT/'synthetic_doublet_examples.csv',index=False)
    # Inspect rare cases against same-donor target-depth matched real parent and control complexity.
    rare=[]
    for _,r in target[target['sub']].iterrows():
        for pool in ['candidate','peptide_comparison']+POOLS:
            c=o[(o.pool==pool)&(o.donor_id==r.donor_id)&(o.row_index!=r.row_index)]
            match=c.loc[(np.abs(np.log1p(c.B)-np.log1p(r.B))).nsmallest(min(100,len(c))).index]
            if len(match):rare.append(dict(row_index=int(r.row_index),donor=r.donor_id,pool=pool,matched_n=len(match),observed_nonpeptide_features=int(r.np_features),matched_features_median=match.np_features.median(),feature_percentile=float((match.np_features<=r.np_features).mean()),max_logdepth_difference=float(np.abs(np.log1p(match.B)-np.log1p(r.B)).max())))
    pd.DataFrame(rare).to_csv(OUT/'rare_case_complexity.csv',index=False)
    print('doublet controls complete',flush=True)

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--stage',choices=['background','models','simulate','doublets','all'],default='all');ap.add_argument('--reps',type=int,default=10);args=ap.parse_args();x,o,f,ji=load()
    for stage,fun in [('background',lambda:background(x,o,f,ji)),('models',lambda:models(o)),('simulate',lambda:simulate(o,args.reps)),('doublets',lambda:doublets(x,o,f,ji))]:
        if args.stage in [stage,'all']:fun()
    (OUT/'run_environment.json').write_text(json.dumps(dict(seed=SEED,python=sys.version,numpy=np.__version__,pandas=pd.__version__,stage=args.stage,simulation_replicates=args.reps),indent=2))
if __name__=='__main__':main()
