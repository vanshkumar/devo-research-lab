"""Animal/site reductions and declared-functional/Monte Carlo development checks."""
import time
import numpy as np
from scipy.stats import t as student_t
from pilot import HERE,IO,get,save,arrays,utc
from generate import score_counts,HORIZONS,NAMES

METRICS=('joint','count','ratio_crps','equal_side_mae','omission_crps','all_correct_crps')

def interval(vals,labs):
    site={l:float(np.mean([v for v,k in zip(vals,labs) if k==l])) for l in sorted(set(labs))}
    x=np.array(list(site.values()));se=float(x.std(ddof=1)/np.sqrt(len(x)))
    d=student_t.ppf(.975,len(x)-1)*se
    return dict(equal_animal=float(np.mean(vals)),equal_site=float(x.mean()),site_t95=[float(x.mean()-d),float(x.mean()+d)],site=site)

def main():
    began=time.monotonic();z=arrays(HERE/'GENERATED_COUNTS.npz');sc=get(HERE/'GENERATED_SCORES.json')
    con=get(HERE/'DEVELOPED_CONDITIONAL.json');ta=get(HERE/'TEACHER_AUDIT.json')
    ids=list(z['subjects']);names=list(z['names']);labs=[con['labs'][s] for s in ids]
    samples=z['samples'];obs=z['observed'];summary={};contrasts={};cohort={};mc={};functional_error=0.
    for k,name in enumerate(names):
        summary[name]={};cohort[name]={}
        for j,h in enumerate(HORIZONS):
            rows=[sc['per_animal'][s][name][str(h)] for s in ids]
            summary[name][str(h)]={m:interval([r[m] for r in rows],labs) for m in METRICS}
            er=np.array([r['expected_ratio'] for r in rows]);po=np.array([r['count_pooled'] for r in rows])
            observed=np.stack((obs[:,j,1]/obs[:,j,0],obs[:,j,3]/obs[:,j,2]),axis=1)
            cohort[name][str(h)]=dict(observed=float(observed.mean()),expected_ratio=float(er.mean()),
                count_pooled=float(po.mean()),expected_ratio_cohort_mae=float(abs(er.mean()-observed.mean())),
                count_pooled_cohort_mae=float(abs(po.mean()-observed.mean())),
                positive_count_mass_min=float(min(min(r['positive_count_mass']) for r in rows)),
                ratio_80_coverage=float(np.mean([r['ratio_80_coverage'] for r in rows])),
                observed_omission=float(obs[:,j,4].mean()/h),
                expected_omission=float(np.mean([r['expected_omission'] for r in rows])))
            for side in (0,2):
                n=samples[:,k,:,j,side]
                # A ratio is undefined at zero count. Identity applies only to
                # cells whose entire predictive count support is positive.
                if not (n>0).all():continue
                rat=samples[:,k,:,j,side+1]/n
                cov=np.mean((n-n.mean(1)[:,None])*(rat-rat.mean(1)[:,None]),axis=1)
                functional_error=max(functional_error,float(np.max(np.abs(po[:,side//2]-er[:,side//2]-cov/n.mean(1)))))
    for name in names:
        if name=='gru':continue
        contrasts[name]={};mc[name]={}
        for j,h in enumerate(HORIZONS):
            contrasts[name][str(h)]={}
            for metric in METRICS:
                v=[sc['per_animal'][s][name][str(h)][metric]-sc['per_animal'][s]['gru'][str(h)][metric] for s in ids]
                contrasts[name][str(h)][metric]=interval(v,labs)
            splits=[]
            for half in (slice(0,len(samples[0,0])//2),slice(len(samples[0,0])//2,None)):
                v=[]
                for i,s in enumerate(ids):
                    baseline=score_counts(samples[i,names.index(name),half,j],obs[i,j],h)
                    neural=score_counts(samples[i,names.index('gru'),half,j],obs[i,j],h)
                    v.append({m:baseline[m]-neural[m] for m in METRICS})
                splits.append({m:interval([r[m] for r in v],labs)['equal_site'] for m in METRICS})
            mc[name][str(h)]=splits
    conditional={}
    for name in ('history_track','growth_track'):
        v=[con['per_animal'][s][name]['ternary_loss']-con['per_animal'][s]['gru']['ternary_loss'] for s in ids]
        conditional[name]=interval(v,labs)
    good=[i for i,s in enumerate(ids) if ta['per_animal'][s]['contrast_support_failures']==ta['per_animal'][s]['probabilityLeft_mismatches']==0]
    teacher_sensitivity={}
    for name in ('growth','history_track','growth_track'):
        teacher_sensitivity[name]={}
        for h in HORIZONS:
            teacher_sensitivity[name][str(h)]={m:interval([sc['per_animal'][ids[i]][name][str(h)][m]-sc['per_animal'][ids[i]]['gru'][str(h)][m] for i in good],[labs[i] for i in good]) for m in METRICS}
    save('REDUCTION.json',dict(utc=utc(),summary=summary,gru_advantage=contrasts,cohort=cohort,
          conditional_gru_advantage=conditional,split_half_mc=mc,functional_identity_max_error=functional_error,
          deterministic_teacher_pass_n=len(good),teacher_pass_sensitivity=teacher_sensitivity,
          uncertainty='paired finite observed-site Student t sensitivity; nine observed sites are not arbitrary new environments. Teacher-pass subset selected on consumed future inputs; no pristine confirmation.',
          simulation_coupling='Same initial per-animal seeds, but GRU Fisher draws advance the action/trainer stream. Samples are not pathwise paired across model families. Split-half differences are integration diagnostics, not independent biological replication.',
          seconds=time.monotonic()-began,io=dict(IO)))
    for h in HORIZONS:
        print('HORIZON',h)
        for name in names:
            row=summary[name][str(h)]
            print(name,{m:round(row[m]['equal_site'],6) for m in ('joint','ratio_crps','equal_side_mae')},cohort[name][str(h)])
    print('Conditional',conditional,'identity',functional_error,'seconds',time.monotonic()-began,flush=True)

if __name__=='__main__': main()
