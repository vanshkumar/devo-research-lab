"""Predeclared contrary check: fixed fits, original support, exact contrast strata."""
import os
for key in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','VECLIB_MAXIMUM_THREADS','NUMEXPR_NUM_THREADS'):os.environ[key]='1'
from pathlib import Path
import csv,json,resource,datetime
import numpy as np
HERE=Path(__file__).resolve().parent;AUTHOR=HERE.parents[1]/'tasks'/HERE.name

def bootstrap_weights(ids,meta):
    species=meta[int(ids[0])]['species'];key='schedule' if species=='human' else 'lab'
    labels=sorted({meta[int(u)][key] for u in ids})
    clusters=[np.array([j for j,u in enumerate(ids) if meta[int(u)][key]==g]) for g in labels]
    rng=np.random.default_rng(20261031);W=np.zeros((2000,len(ids)))
    for b in range(2000):
        groups=[clusters[j] for j in rng.integers(len(clusters),size=len(clusters))] if species=='human' else clusters
        draw=np.concatenate([g[rng.integers(len(g),size=len(g))] for g in groups])
        W[b]=np.bincount(draw,minlength=len(ids))/len(draw)
    return W

def main():
    rowpath=AUTHOR/'corrected/scoring_rows.csv';predpath=HERE/'independent_predictions.npz'
    with rowpath.open() as f: rr=list(csv.DictReader(f))
    unit=np.array([int(r['unit']) for r in rr]);choice=np.array([float(r['choice']) for r in rr]);x=np.array([float(r['contrast']) for r in rr])
    support=np.array([r['common_support']=='True' for r in rr]);sp=np.array([r['species'] for r in rr]);condition=np.array([int(r['condition']) for r in rr])
    meta={int(r['unit']):{k:r[k] for k in ('subject','species','schedule','lab','condition')} for r in rr};del rr
    with np.load(predpath,allow_pickle=False) as z: pp={k:z[k] for k in z.files}
    y=pp.pop('y');decoded=sum(a.nbytes for a in pp.values())+y.nbytes
    response=(choice!=0);loss={}
    for k,p in pp.items():
        value=np.full(len(y),np.nan);q=np.clip(p[response],1e-9,1-1e-9)
        value[response]=-(y[response]*np.log(q)+(1-y[response])*np.log1p(-q));loss[k]=value
    cache={};out=[];contributions=[]
    for species in ('human','mouse'):
        primary=response&support&(sp==species);allids=np.unique(unit[primary])
        masks=[('all','all',primary)]+[('absolute_contrast',str(c),primary&(abs(x)==c)) for c in (0.,.25,.5,1.)]
        if species=='human':
            masks.extend(('condition',str(c),primary&(condition==c)) for c in (0,1))
            masks.extend(('schedule',s,primary&np.array([meta[int(u)]['schedule']==s for u in unit])) for s in sorted({meta[int(u)]['schedule'] for u in allids}))
        else:
            masks.extend(('lab',s,primary&np.array([meta[int(u)]['lab']==s for u in unit])) for s in sorted({meta[int(u)]['lab'] for u in allids}))
        for baseline in ('B','S'):
            for a,b in [('human_fixed','B'),('H','B'),('T','H')]:
                delta=loss[baseline+'_'+b]-loss[baseline+'_'+a]
                for kind,label,m in masks:
                    ids=np.unique(unit[m])
                    if not len(ids):continue
                    values=np.array([delta[m&(unit==u)].mean() for u in ids]);counts=np.array([np.sum(m&(unit==u)) for u in ids])
                    ck=tuple(int(u) for u in ids)
                    if ck not in cache:cache[ck]=bootstrap_weights(ids,meta)
                    draws=np.einsum('ij,j->i',cache[ck],values,optimize=False)
                    out.append(dict(species=species,baseline=baseline,comparison=a+'-minus-'+b,stratum=kind,label=label,rows=int(m.sum()),units=len(ids),labs=len({meta[int(u)]['lab'] for u in ids}),schedules=len({meta[int(u)]['schedule'] for u in ids}),gain_nat=float(values.mean()),interval95=np.quantile(draws,[.025,.975]).tolist(),row_weighted_gain=float(np.sum(counts*values)/np.sum(counts)),units_negative=int(np.sum(values<0)),units_materially_negative=int(np.sum(values<=-.005)),unit_gain_range=[float(values.min()),float(values.max())],conditional_exploratory=True))
                for c in (0.,.25,.5,1.):
                    m=primary&(abs(x)==c)
                    v=np.array([np.sum(delta[m&(unit==u)])/np.sum(primary&(unit==u)) for u in allids])
                    contributions.append(dict(species=species,baseline=baseline,comparison=a+'-minus-'+b,absolute_contrast=c,full_unit_denominator=len(allids),rows=int(m.sum()),contribution_to_primary_gain=float(v.mean())))
    summarypath=AUTHOR/'corrected/SUMMARY.json';author=json.loads(summarypath.read_text())
    errors=[]
    for r in out:
        if r['stratum']!='all':continue
        ref=next(a for a in author if a['scope']=='support' and all(a[k]==r[k] for k in ('species','baseline','comparison')))
        errors.append(max(abs(r['gain_nat']-ref['gain_nat']),float(np.max(abs(np.array(r['interval95'])-ref['interval95'])))))
    checks=[]
    for species in ('human','mouse'):
        for baseline in ('B','S'):
            for comp in ('human_fixed-minus-B','H-minus-B','T-minus-H'):
                p=next(r for r in out if r['species']==species and r['baseline']==baseline and r['comparison']==comp and r['stratum']=='all')
                total=sum(r['contribution_to_primary_gain'] for r in contributions if r['species']==species and r['baseline']==baseline and r['comparison']==comp)
                checks.append(dict(species=species,baseline=baseline,comparison=comp,composition_error=abs(total-p['gain_nat'])))
    report=dict(utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),predeclared_check='PLAN.md before detailed stratum outcomes',primary_fixed_fit_interval_max_error=max(errors),rows=out,contrast_contributions=contributions,composition_checks=checks,interpretation='Each stratum averages responding rows within each available unit, then units. Contributions instead retain each unit primary denominator and add exactly to the original primary gain. Intervals condition on fixed fits and observed schedule/lab structure; exploratory postvalidation, no family-wide significance, coverage, equivalence or species causation.',resource=dict(read_file_bytes=rowpath.stat().st_size+predpath.stat().st_size+summarypath.stat().st_size,decoded_array_bytes=decoded,peak_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss))
    (HERE/'CONTRARY.json').write_text(json.dumps(report,indent=2)+'\n')
    with (HERE/'contrast_strata.csv').open('w') as f:
        fields=['species','baseline','comparison','stratum','label','rows','units','gain_nat','interval95','row_weighted_gain','units_negative','units_materially_negative']
        writer=csv.DictWriter(f,fieldnames=fields,extrasaction='ignore');writer.writeheader();writer.writerows(r for r in out if r['stratum']=='absolute_contrast')
    print(json.dumps(dict(interval_max_error=max(errors),resource=report['resource'],human_fixed_contrast_rows=[r for r in out if r['comparison']=='human_fixed-minus-B' and r['stratum']=='absolute_contrast'],human_fixed_S_contexts=[r for r in out if r['comparison']=='human_fixed-minus-B' and r['baseline']=='S' and r['stratum'] in ('condition','lab')]),indent=2))

if __name__=='__main__':main()
