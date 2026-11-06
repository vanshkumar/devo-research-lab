"""Reduce the faithful strong reference and check finite-law discrimination."""
import time
import numpy as np
from scipy.spatial.distance import cdist
from pilot import HERE,PREV,IO,get,save,arrays,utc
from generate import score_counts,HORIZONS,crps
from reduce import interval,METRICS

def proper_difference_law(first,second,truth,horizon):
    # Exact fixed empirical-forecast energy difference at every truth atom.
    out=np.zeros(len(truth))
    for j in (0,2):
        def categories(a):
            n,k=a[:,j],a[:,j+1]
            return np.column_stack([k,n-k,horizon-n])/horizon
        f,g,y=map(categories,(first,second,truth))
        sf=cdist(y,f).mean(1)-.5*cdist(f,f).mean()
        sg=cdist(y,g).mean(1)-.5*cdist(g,g).mean()
        out+=(sf-sg)/2
    return out

def main():
    begin=time.monotonic();z=arrays(HERE/'RETAINED_GROWTH_COUNTS.npz');sc=get(HERE/'RETAINED_GROWTH_SCORES.json')
    ids=list(z['subjects']);names=list(z['names']);m=z['samples'];obs=z['observed']
    target=get(HERE/'OBSERVATION_TARGET_CORRECTION.json')
    for i,s in enumerate(ids):
        for j,h in enumerate(HORIZONS):obs[i,j,6]=target['all_feedback_success'][s][str(h)]
    sc=get(HERE/'RETAINED_GROWTH_SCORES_CORRECTED.json')
    labs0=get(HERE/'DEVELOPED_CONDITIONAL.json')['labs'];labs=[labs0[s] for s in ids]
    summary={};gain={};split={};cohort={}
    for name in names:
        summary[name]={};cohort[name]={}
        for j,h in enumerate(HORIZONS):
            rows=[sc['per_animal'][s][name][str(h)] for s in ids]
            summary[name][str(h)]={metric:interval([r[metric] for r in rows],labs) for metric in METRICS}
            cohort[name][str(h)]=dict(expected_ratio=float(np.mean([r['expected_ratio'] for r in rows])),
                count_pooled=float(np.mean([r['count_pooled'] for r in rows])),
                observed=float(np.mean(obs[:,j,[1,3]]/obs[:,j,[0,2]])),
                coverage=float(np.mean([r['ratio_80_coverage'] for r in rows])),
                positive_mass_min=float(min(min(r['positive_count_mass']) for r in rows)),
                predicted_omission=float(np.mean([r['expected_omission'] for r in rows])),
                observed_omission=float(obs[:,j,4].mean()/h))
        if name=='gru':continue
        gain[name]={};split[name]={}
        for j,h in enumerate(HORIZONS):
            gain[name][str(h)]={metric:interval([sc['per_animal'][s][name][str(h)][metric]-sc['per_animal'][s]['gru'][str(h)][metric] for s in ids],labs) for metric in METRICS}
            half=[]
            for block in (slice(0,m.shape[2]//2),slice(m.shape[2]//2,None)):
                d=[]
                for i,s in enumerate(ids):
                    f=score_counts(m[i,names.index(name),block,j],obs[i,j],h)
                    g=score_counts(m[i,names.index('gru'),block,j],obs[i,j],h)
                    d.append({k:f[k]-g[k] for k in ('joint','ratio_crps','equal_side_mae')})
                half.append({k:interval([v[k] for v in d],labs)['equal_site'] for k in d[0]})
            split[name][str(h)]=half
    con=get(HERE/'COMMON_CONDITIONAL.json');conditional=interval([con['per_animal'][s]['common_hybrid']['ternary_loss']-con['per_animal'][s]['gru']['ternary_loss'] for s in ids],labs)
    # Independent scalar numerical checks on a selected exact100 cell.
    a=m[0,0,:9,-1];y=obs[0,-1];N,K=a[:,0],a[:,1];on,ok=y[:2]
    vec=np.column_stack([K,N-K,2000-N])/2000;target=np.array([ok,on-ok,2000-on])/2000
    explicit=sum(sum(np.sqrt(sum((u-v)**2)) for v in vec) for u in vec)/(2*len(vec)**2)
    scalar=sum(np.sqrt(sum((u-target)**2)) for u in vec)/len(vec)-explicit
    vector=np.linalg.norm(vec-target,axis=1).mean()-.5*cdist(vec,vec).mean()
    ratio=K/N;truth=ok/on
    scalar_crps=sum(abs(float(v)-truth) for v in ratio)/len(ratio)-sum(abs(float(u-v)) for u in ratio for v in ratio)/(2*len(ratio)**2)
    checks=dict(scalar_joint_error=float(abs(scalar-vector)),scalar_crps_error=float(abs(scalar_crps-crps(ratio,truth))),
                identical_forecast_law_error=float(np.max(np.abs(proper_difference_law(m[0,0,:,-1],m[0,0,:,-1],m[0,2,:,-1],2000)))))
    assert max(checks.values())<1e-14
    # Known finite laws and a large, supported count-level planted difference.
    # No biological or fitted-rule recovery is claimed by these controls.
    rng=np.random.default_rng(202611053);rep=4000;controls={};h=2000;j=-1
    site_index={l:np.array([i for i,k in enumerate(labs) if k==l]) for l in sorted(set(labs))}
    for truth_name in ('frozen_growth','gru','planted_null','planted10pp'):
        losses=[]
        for i in range(len(ids)):
            baseline=m[i,0,:,j];neural=m[i,2,:,j]
            if truth_name in ('planted_null','planted10pp'):
                baseline=baseline.copy();neural=baseline.copy()
                for col in (0,2):neural[:,col+1]=np.minimum(neural[:,col],neural[:,col+1]+np.rint(.1*neural[:,col]).astype(int))
                truth=baseline if truth_name=='planted_null' else neural
            else:truth=m[i,names.index(truth_name),:,j]
            losses.append(proper_difference_law(baseline,neural,truth,h))
        losses=np.stack(losses)
        draws=rng.integers(0,m.shape[2],size=(rep,len(ids)))
        vals=losses[np.arange(len(ids))[None,:],draws]
        site=np.column_stack([vals[:,ix].mean(1) for ix in site_index.values()])
        # A fixed-known-law decision uses independently simulated null quantiles,
        # not an asserted biological t-test calibration.
        controls[truth_name]=dict(mean_expected_gru_gain=float(np.mean([losses[ix].mean() for ix in site_index.values()])),
              equal_site_statistic=site.mean(1).tolist(),atom_count=m.shape[2],replicates=rep)
    null=np.array(controls['frozen_growth'].pop('equal_site_statistic'))
    crit=float(np.quantile(null,.95))
    planted_null=np.array(controls['planted_null'].pop('equal_site_statistic'))
    planted_crit=float(np.quantile(planted_null,.95))
    for n,v in controls.items():
        stat=null if n=='frozen_growth' else planted_null if n=='planted_null' else np.array(v.pop('equal_site_statistic'))
        threshold=planted_crit if n.startswith('planted') else crit
        v['fraction_over_pair_null_95']=float(np.mean(stat>threshold))
        v['decision_threshold']=threshold
    # False distinction when forecasts are identical is exact, no random test.
    controls['identical_forecasts']=dict(gain_exactly_zero=True)
    save('RETAINED_REDUCTION.json',dict(utc=utc(),summary=summary,gru_advantage=gain,cohort=cohort,
          common_conditional_gru_advantage=conditional,split_half_mc=split,checks=checks,
          known_finite_law_controls=controls,io=dict(IO),seconds=time.monotonic()-begin,
          limitations='Nine observed sites, consumed outcomes, fixed actor and empirical source uncertainty only; input-law violations remain. Finite-law controls hold prefix/site contexts fixed, do not fit a neural model and are not biological power.'))
    for name in names:
        print(name,summary[name]['2000'],cohort[name]['2000'])
    print('gain over strongest growth',gain['frozen_growth']['2000'],'conditional',conditional,'controls',controls,flush=True)

if __name__=='__main__':main()
