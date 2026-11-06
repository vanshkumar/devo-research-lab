"""Direct paired information/lead-time contrast on the same future observations."""
import time
import numpy as np
from scipy.stats import t as student_t
from scipy.spatial.distance import cdist
from pilot import HERE,PREV,IO,get,save,arrays,utc
from early import score_window,WINDOWS
from reduce import interval
from generate import crps

METRICS=('mixed_ratio_score','equal_side_mae','joint','count','omission_crps','all_correct_crps')

def inference(values,labs):
    v=np.asarray(values);n=len(v);mean=float(v.mean());se=float(v.std(ddof=1)/np.sqrt(n));width=student_t.ppf(.975,n-1)*se
    site=interval(v,labs)
    return dict(equal_animal=mean,animal_t95=[mean-width,mean+width],animal_sd=float(v.std(ddof=1)),
                equal_site=site['equal_site'],site_t95=site['site_t95'],site=site['site'],
                site_sd=float(np.std(list(site['site'].values()),ddof=1)))

def main():
    began=time.monotonic();sc=get(HERE/'EARLY_SCORES.json');z=arrays(HERE/'EARLY_COUNTS.npz')
    ids=list(z['subjects']);names=list(z['names']);labs0=get(HERE/'DEVELOPED_CONDITIONAL.json')['labs'];labs=[labs0[s] for s in ids]
    risks={};gains={};interaction={};calibration={};relative={};splits={}
    rng=np.random.default_rng(202611054);draw=rng.integers(0,len(ids),(6000,len(ids)))
    for name in names:
        risks[name]={};calibration[name]={}
        for cutoff in ('200','1000'):
            risks[name][cutoff]={}
            for h in WINDOWS:
                risks[name][cutoff][str(h)]={m:inference([sc['per_animal'][s][cutoff][name][str(h)][m] for s in ids],labs) for m in METRICS}
        for h in WINDOWS:
            calibration[name][str(h)]={m:inference([sc['per_animal'][s]['200'][name][str(h)][m]-sc['per_animal'][s]['1000'][name][str(h)][m] for s in ids],labs) for m in METRICS}
        if name=='gru':continue
        gains[name]={};interaction[name]={};relative[name]={};splits[name]={}
        for cutoff in ('200','1000'):
            gains[name][cutoff]={};relative[name][cutoff]={}
            for h in WINDOWS:
                gains[name][cutoff][str(h)]={m:inference([sc['per_animal'][s][cutoff][name][str(h)][m]-sc['per_animal'][s][cutoff]['gru'][str(h)][m] for s in ids],labs) for m in METRICS}
                b=np.array([sc['per_animal'][s][cutoff][name][str(h)]['mixed_ratio_score'] for s in ids]);g=np.array([sc['per_animal'][s][cutoff]['gru'][str(h)]['mixed_ratio_score'] for s in ids])
                boot=(b[draw].mean(1)-g[draw].mean(1))/b[draw].mean(1)
                relative[name][cutoff][str(h)]=dict(animal_relative_gru_gain=float((b-g).mean()/b.mean()),
                               paired_animal_bootstrap95=np.quantile(boot,[.025,.975]).tolist())
        for h in WINDOWS:
            interaction[name][str(h)]={}
            for m in METRICS:
                v=[]
                for s in ids:
                    a=sc['per_animal'][s]
                    v.append((a['200'][name][str(h)][m]-a['200']['gru'][str(h)][m])-
                             (a['1000'][name][str(h)][m]-a['1000']['gru'][str(h)][m]))
                interaction[name][str(h)][m]=inference(v,labs)
            parts=[]
            for part in (slice(0,128),slice(128,None)):
                v={m:[] for m in ('mixed_ratio_score','equal_side_mae')}
                for i,s in enumerate(ids):
                    for m in v:
                        scores=[]
                        for j,cutoff in enumerate((200,1000)):
                            ordinary=score_window(z['samples'][i,j,names.index(name),part,WINDOWS.index(h)],z['observed'][i,WINDOWS.index(h)],h)
                            neural=score_window(z['samples'][i,j,names.index('gru'),part,WINDOWS.index(h)],z['observed'][i,WINDOWS.index(h)],h)
                            scores.append(ordinary[m]-neural[m])
                        v[m].append(scores[0]-scores[1])
                parts.append({m:inference(vals,labs) for m,vals in v.items()})
            splits[name][str(h)]=parts
    teacher={}
    for cutoff in ('200','1000'):
        teacher[cutoff]={k:int(sum(sc['teacher'][s][cutoff][k] for s in ids)) for k in ('n','contrast_support_failures','parameter_failures')}
        teacher[cutoff]['animals_with_any_failure']=sum(sc['teacher'][s][cutoff]['contrast_support_failures']>0 or sc['teacher'][s][cutoff]['parameter_failures']>0 for s in ids)
    precision={}
    for name in interaction:
        precision[name]={}
        for h in WINDOWS:
            precision[name][str(h)]={}
            for metric,margin in (('mixed_ratio_score',.01),('equal_side_mae',.02)):
                v=interaction[name][str(h)][metric]
                precision[name][str(h)][metric]=dict(
                   normal_sites_for95_halfwidth_margin=int(np.ceil((1.96*v['site_sd']/margin)**2)),
                   normal_animals_for95_halfwidth_margin=int(np.ceil((1.96*v['animal_sd']/margin)**2)),
                   margin=margin,
                   interpretation='Observed-dispersion planning analogy only; independent same-design units and no extra source/teacher uncertainty assumed. Not a cohort authorization or power guarantee.')
    # Proper mixed-score identity and no-opportunity boundary.
    sample=z['samples'][0,1,0,:,1];on=z['observed'][0,1];errors=[]
    for j in (0,2):
        n,k=sample[:,j],sample[:,j+1];assert (n>0).all()
        ratios=k/n;v=np.column_stack([np.zeros(len(n)),ratios,1-ratios]);target=np.array([0,on[j+1]/on[j],1-on[j+1]/on[j]])
        energy=(np.linalg.norm(v-target,axis=1).mean()-.5*cdist(v,v).mean())/np.sqrt(2)
        errors.append(abs(energy-crps(ratios,on[j+1]/on[j])))
    allmissing=np.zeros((16,7),int);missing_obs=np.zeros(7,int)
    boundary=score_window(allmissing,missing_obs,500)['mixed_ratio_score']
    assert max(errors)<1e-14 and boundary==0
    save('EARLY_REDUCTION.json',dict(utc=utc(),risks=risks,gru_advantage=gains,
           paired_information_contrast=interaction,model_calibration_benefit=calibration,
           relative_gru_gain=relative,split_half_interaction=splits,teacher=teacher,
           precision_analogies=precision,mixed_score_checks=dict(positive_count_crps_error=float(max(errors)),all_missing_self_score=boundary),
           io=dict(IO),seconds=time.monotonic()-began,
           uncertainty='Paired animal t/bootstrap under independent-mouse working assumptions and observed-site t sensitivity. Consumed fixed/source sites, not calibrated arbitrary-lab or neural-family equivalence. Source bank/recency selection uncertainty not resampled here.'))
    for name in names:
        for cutoff in ('200','1000'):
            print(name,cutoff,{str(h):{m:risks[name][cutoff][str(h)][m]['equal_animal'] for m in ('mixed_ratio_score','equal_side_mae')} for h in WINDOWS})
    for name in interaction:
        print('PAIRED CONTRAST',name,{str(h):{m:interaction[name][str(h)][m] for m in ('mixed_ratio_score','equal_side_mae')} for h in WINDOWS})
    print('teacher',teacher,'precision',precision,flush=True)

if __name__=='__main__':main()
