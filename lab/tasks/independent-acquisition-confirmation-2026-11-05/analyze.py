"""Frozen paired-animal, missing-state and particle-error reductions."""
from common import *
from main_scores import mixed_score,crps
from scipy.stats import t as student
METRICS=['side_mae','proper_V','proper_U','omission_CRPS','count_CRPS','literal_success_CRPS','side_median_mae']
NAMES=['growth','recent100','recent250','gru']

def metric(sample,observed,horizon):
    mae=[];median=[];v=[];u=[];count=[]
    for j in [0,2]:
        n,k=sample[:,j],sample[:,j+1];on,ok=observed[j:j+2];pos=n>0
        a,b=mixed_score(n,k,on,ok);v.append(a);u.append(b)
        if on==0 or not pos.any():mae.append(np.nan);median.append(np.nan)
        else:
            ratio=k[pos]/n[pos];mae.append(abs(ratio.mean()-ok/on));median.append(abs(np.median(ratio)-ok/on))
        count.append(crps(n/horizon,on/horizon))
    return np.array([np.mean(mae),np.mean(v),np.mean(u),crps(sample[:,4]/horizon,observed[4]/horizon),
        np.mean(count),crps(sample[:,6]/horizon,observed[6]/horizon),np.mean(median)])

def band(v,family,df=None):
    v=np.asarray(v,float)
    if not np.isfinite(v).all():return dict(n=len(v),point=None,lower=None,upper=None,undefined=True,reason='Undefined full-cohort accuracy; no animals dropped.')
    n=len(v);df=n-1 if df is None else df;m=float(v.mean());se=float(v.std(ddof=1)/np.sqrt(n));critical=float(student.ppf(1-.05/(2*family),df))
    return dict(n=n,point=m,se=se,lower=m-critical*se,upper=m+critical*se,half_width=critical*se,critical=critical,df=df,family=family)

def mc_record(batch_values,biological):
    v=np.asarray(batch_values,float);m=v.mean(0);means=v.mean(1)
    se=float(np.std(means,ddof=1)/np.sqrt(len(means)));hw=float(student.ppf(.995,len(means)-1)*se)
    result=dict(batch_means=means.tolist(),batch_particles='128neural/main;64ordinary/source',
        unbiased_batch_mean=float(np.mean(means)),mcse=se,mc99_half_width=hw,
        criterion_max_half_width=max(.001,.2*biological['half_width']))
    result['small_against_animal_precision']=hw<=result['criterion_max_half_width']
    result['lower_after_mc']=biological['lower']-hw;result['upper_after_mc']=biological['upper']+hw
    return result

def calibration_record(S,O,horizon):
    rows=[]
    for j in (0,2):
        n,k=S[:,j],S[:,j+1];on,ok=O[j:j+2];pos=n>0;ratios=k[pos]/n[pos]
        row=dict(sign=-1 if j==0 else 1,zero_count_mass=float(np.mean(~pos)),observed_N=int(on),observed_K=int(ok),
            mean_ratio=float(ratios.mean()) if len(ratios) else None,observed_ratio=float(ok/on) if on else None,
            pooled_ratio=float(k.sum()/n.sum()) if n.sum() else None,readouts={})
        for label,vals,y in [('N',n,on),('K',k,ok),('omissions',S[:,4],O[4]),('literal_success',S[:,6],O[6])]:
            q=np.quantile(vals,[.025,.1,.9,.975]);row['readouts'][label]=dict(mean=float(vals.mean()),observed=int(y),
                interval80=q[1:3].tolist(),interval95=q[[0,3]].tolist(),covered80=bool(q[1]<=y<=q[2]),covered95=bool(q[0]<=y<=q[3]),
                mid_PIT=float(np.mean(vals<y)+.5*np.mean(vals==y)))
        if on and len(ratios):
            q=np.quantile(ratios,[.025,.1,.9,.975]);y=ok/on
            row['readouts']['ratio']=dict(mean=float(ratios.mean()),observed=float(y),interval80=q[1:3].tolist(),interval95=q[[0,3]].tolist(),
                covered80=bool(q[1]<=y<=q[2]),covered95=bool(q[0]<=y<=q[3]),mid_PIT=float(np.mean(ratios<y)+.5*np.mean(ratios==y)))
        rows.append(row)
    return rows

def main():
    assert get(HERE/'FORECAST_COMPLETION.json')['all_forecast_jobs_terminal']
    fp=get(HERE/'ACCESS_FOOTPRINT.json');units=fp['primary_units'];ids=[r['subject'] for r in units]
    obs=arrays(HERE/'OBSERVED_COUNTS.npz');O=obs['observed'];assert list(obs['subjects'])==ids
    scores=np.empty((192,2,4,2,7));stream_scores=np.empty((192,2,4,2,2,7));batch_U=np.empty((192,2,4,8))
    source=np.empty((192,2,2,2,2,7));source_batch_U=np.empty((192,2,2,2,8));cal=[]
    for i,s in enumerate(ids):
        sample=arrays(HERE/'main_chunks'/(s+'.npz'))['samples'];assert sample.shape==(2,4,2,512,2,7)
        for ci in range(2):
            for ni in range(4):
                for wi,horizon in enumerate([500,2000]):
                    S=sample[ci,ni,:,:,wi,:].reshape(1024,7);scores[i,ci,ni,wi]=metric(S,O[i,wi],horizon)
                    for stream in range(2):stream_scores[i,ci,ni,stream,wi]=metric(sample[ci,ni,stream,:,wi],O[i,wi],horizon)
                for stream in range(2):
                    for b in range(4):batch_U[i,ci,ni,stream*4+b]=metric(sample[ci,ni,stream,b*128:(b+1)*128,1],O[i,1],2000)[2]
                cal.append(dict(subject=s,lab=units[i]['lab'],cohort=units[i]['cohort'],cutoff=[200,1000][ci],actor=NAMES[ni],
                    signs=calibration_record(sample[ci,ni,:,:,1,:].reshape(1024,7),O[i,1],2000)))
        for ji,j in enumerate([0,14]):
            z=arrays(HERE/'source_chunks'/(str(j)+'_'+s+'.npz'))['samples'];assert z.shape==(2,2,2,256,2,7)
            for ci in range(2):
                for ni in range(2):
                    for wi,horizon in enumerate([500,2000]):source[i,ji,ci,ni,wi]=metric(z[ci,ni,:,:,wi,:].reshape(512,7),O[i,wi],horizon)
                    for stream in range(2):
                        for b in range(4):source_batch_U[i,ji,ci,ni,stream*4+b]=metric(z[ci,ni,stream,b*64:(b+1)*64,1],O[i,1],2000)[2]
        if (i+1)%32==0:print('SCORED',i+1,'/192 CPU',round(time.process_time()-START_CPU,2),flush=True)
    npz('SCORES.npz',scores=scores,stream_scores=stream_scores,batch_U=batch_U,source_scores=source,source_batch_U=source_batch_U,
        subjects=ids,names=NAMES,cutoffs=[200,1000],windows=[500,2000],metrics=METRICS,source_draws=[0,14])
    save('CALIBRATION.json',dict(utc=utc(),records=cal,scope='Per-sign marginals, finite forecast distributions, fixed deposited mixture; mid-PIT for ties.'))
    primary=[];vectors=[];labels=[]
    for ni,name in enumerate(NAMES[:3]):
        D=.9*scores[:,0,ni,1,1]-scores[:,0,3,1,1];b=band(D,3)
        batches=(.9*batch_U[:,0,ni]-batch_U[:,0,3]).T;mc=mc_record(batches,b)
        m=scores[:,0,:,1,1].mean(0);rawgain=1-m[3]/m[ni]
        primary.append(dict(reference=name,cutoff=200,D=b,mc=mc,relative_gain_point=float(rawgain),reference_risk=float(m[ni]),neural_risk=float(m[3]),
            U_contrast_mean=float(np.mean(.9*scores[:,0,ni,1,2]-scores[:,0,3,1,2])),
            V_minus_U_contrast_mean=float(D.mean()-np.mean(.9*scores[:,0,ni,1,2]-scores[:,0,3,1,2])),
            stream_D_means=[float(np.mean(.9*stream_scores[:,0,ni,k,1,1]-stream_scores[:,0,3,k,1,1])) for k in range(2)]))
        vectors.append(D);labels.append(name+'_D200')
    secondary=[]
    for ci,c in enumerate([200,1000]):
        for metricindex,metricname,margin in [(0,'A',.02),(1,'D',0.)]:
            v=scores[:,ci,1,1,0]-scores[:,ci,3,1,0] if metricname=='A' else .9*scores[:,ci,1,1,1]-scores[:,ci,3,1,1]
            secondary.append(dict(reference='recent100',cutoff=c,metric=metricname,margin=margin,band=band(v,4)))
    source_results=[]
    # Exactly8properDcontrasts =2draws*2cutoffs*2ordinaryreferences; sourceMAE remains descriptive.
    for ji,j in enumerate([0,14]):
        for ci,c in enumerate([200,1000]):
            for ni,name in enumerate(NAMES[:2]):
                D=.9*source[:,ji,ci,ni,1,1]-scores[:,ci,3,1,1];b=band(D,8)
                batches=(.9*source_batch_U[:,ji,ci,ni]-batch_U[:,ci,3]).T;mc=mc_record(batches,b)
                source_results.append(dict(draw=j,cutoff=c,reference=name,D=b,mc=mc,
                    relative_gain_point=float(1-scores[:,ci,3,1,1].mean()/source[:,ji,ci,ni,1,1].mean()),
                    descriptive_accuracy_gain=float(np.mean(source[:,ji,ci,ni,1,0]-scores[:,ci,3,1,0]))))
    labs=np.array([r['lab'] for r in units]);cohorts=np.array([r['cohort'] for r in units]);D=np.stack(vectors,axis=1)
    sensitivity=[]
    for ni,name in enumerate(NAMES[:3]):
        v=D[:,ni];sites=sorted(set(labs));means=np.array([v[labs==lab].mean() for lab in sites])
        cluster=student.ppf(1-.05/(2*3),len(sites)-1)*np.sqrt(len(sites)/(len(sites)-1)*sum((v[labs==lab]-v.mean()).sum()**2 for lab in sites))/len(v)
        sensitivity.append(dict(reference=name,by_lab=[dict(lab=lab,n=int(np.sum(labs==lab)),D=float(v[labs==lab].mean())) for lab in sites],
            equal_label_band=band(means,3),animal_weighted_cluster_band=dict(point=float(v.mean()),lower=float(v.mean()-cluster),upper=float(v.mean()+cluster),df=len(sites)-1),
            leave_one_label_out=[dict(excluded=lab,n=int(np.sum(labs!=lab)),D=float(v[labs!=lab].mean())) for lab in sites],
            by_project=[dict(cohort=cohort,band=band(v[cohorts==cohort],3)) for cohort in sorted(set(cohorts))]))
    summary=[]
    for ci,c in enumerate([200,1000]):
        for ni,name in enumerate(NAMES):
            rr=[r for r in cal if r['cutoff']==c and r['actor']==name];side=[s for r in rr for s in r['signs']]
            row=dict(cutoff=c,actor=name,mean_metrics={k:(float(np.mean(scores[:,ci,ni,1,m])) if np.isfinite(scores[:,ci,ni,1,m]).all() else None) for m,k in enumerate(METRICS)},
                mean_zero_N_mass=float(np.mean([r['zero_count_mass'] for r in side])),observed_zero_N_signs=sum(r['observed_N']==0 for r in side),
                mean_ratio_bias=float(np.mean([r['mean_ratio']-r['observed_ratio'] for r in side if r['mean_ratio'] is not None and r['observed_ratio'] is not None])),readouts={})
            for label in ['N','K','ratio','omissions','literal_success']:
                rr=[r['readouts'][label] for r in side if label in r['readouts']]
                row['readouts'][label]=dict(n=len(rr),coverage80=float(np.mean([r['covered80'] for r in rr])),coverage95=float(np.mean([r['covered95'] for r in rr])),
                    mean_prediction=float(np.mean([r['mean'] for r in rr])),mean_observed=float(np.mean([r['observed'] for r in rr])),
                    mean_mid_PIT=float(np.mean([r['mid_PIT'] for r in rr])))
            summary.append(row)
    positive=all(r['D']['lower']>0 and r['mc']['lower_after_mc']>0 and r['mc']['small_against_animal_precision'] for r in primary)
    recent=primary[1];negative=recent['D']['upper']<0 and recent['mc']['upper_after_mc']<0 and recent['mc']['small_against_animal_precision']
    conclusion='material_positive_all_three' if positive else 'selected100_excludes10percent_conditional_fixed_prescription' if negative else 'inconclusive'
    out=dict(utc=utc(),n=192,conclusion=conclusion,primary=primary,secondary_selected_four=secondary,source_contraries=source_results,
        sensitivities=sensitivity,absolute_calibration=summary,primary_positive=positive,primary_selected_negative=negative,
        nominal_inference='Working paired independent-animal Student intervals in fixed deposited mixture, no biological/site/source-family universal guarantee.',
        source_qualification='two finite ordinary donor/anchor sensitivities against unchanged primary neural law; old32/source-tail/retraining uncertainty retained',
        actual_cohort_composition=dict(labs={lab:int(np.sum(labs==lab)) for lab in sorted(set(labs))},cohorts={c:int(np.sum(cohorts==c)) for c in sorted(set(cohorts))}),
        undefined_MAE_cells=int(np.sum(~np.isfinite(scores[:,:,:,:,0]))))
    npz('PRIMARY_CONTRIBUTIONS.npz',D=D,subjects=ids,references=NAMES[:3],labels=labels)
    save('ANALYSIS.json',out);receipt('ANALYSIS','complete',all_jobs_terminal=True)
    print(json.dumps(dict(conclusion=conclusion,primary=primary,secondary=secondary,source=source_results),default=serial),flush=True)
if __name__=='__main__':
    try:main()
    except BaseException as exc:receipt('ANALYSIS_FAILURE','failed',error=repr(exc));raise
