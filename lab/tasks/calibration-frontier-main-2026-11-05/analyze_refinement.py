"""Pool four integration streams; preserve632 and append20refined columns."""
import time,resource
BEGIN=time.monotonic();CPU=time.process_time()
import io,json,hashlib
from pathlib import Path
from datetime import datetime,timezone
from collections import Counter
import numpy as np
from scipy.stats import t
from main_scores import metrics,mixed_score,calibration,METRICS
from main_inference import resampling_counts,joint_bands,site_sensitivity

HERE=Path(__file__).resolve().parent;IO=Counter();PINS={}
def serial(x):
    if isinstance(x,np.ndarray):return x.tolist()
    if isinstance(x,np.generic):return x.item()
    raise TypeError(type(x).__name__)
def save(name,x):(HERE/name).write_text(json.dumps(x,indent=2,allow_nan=False,default=serial)+'\n')
def read(p):
    b=p.read_bytes();IO['explicit_read_bytes']+=len(b);PINS[p.name]=hashlib.sha256(b).hexdigest();return b
def get(name):return json.loads(read(HERE/name))
def arrays(name,keys=None):
    with np.load(io.BytesIO(read(HERE/name)),allow_pickle=False) as z:r={k:z[k] for k in (z.files if keys is None else keys)}
    IO['decoded_array_bytes']+=sum(v.nbytes for v in r.values());return r
def utc():return datetime.now(timezone.utc).isoformat()
def primary_risk(s,o):
    mae=[];score=[]
    for j in (0,2):
        n,k=s[:,j],s[:,j+1];on,ok=o[j:j+2];keep=n>0
        assert keep.any() and on>0
        mae.append(abs(np.mean(k[keep]/n[keep])-ok/on));score.append(mixed_score(n,k,on,ok)[0])
    return np.array([np.mean(mae),np.mean(score)])


def main():
    assert get('REFINEMENT_EXECUTION.json')['status']=='complete'
    base=get('MAIN_ANALYSIS_INITIAL512.json');family=get('MAIN_FAMILY_INITIAL512.json')
    original=arrays('MAIN_COUNTS.npz',['samples','subjects']);added=arrays('REFINED_ADDITIONAL_COUNTS.npz',['samples','subjects'])
    target=arrays('MAIN_OBSERVED.npz');oldmetrics=arrays('MAIN_SCORES.npz',['fixed','streams'])
    oldcon=arrays('MAIN_CONTRASTS.npz')
    assert np.array_equal(original['subjects'],added['subjects'])
    ids=target['subjects'].tolist();labs=target['labs'].tolist();obs=target['observed']
    old=original['samples'][:,0];new=added['samples'];assert new.shape==old.shape
    four=np.concatenate([old,new],axis=3);assert four.shape==(64,2,4,4,256,2,7)
    pooled=four.reshape(64,2,4,1024,2,7)
    scores=np.empty((64,2,4,2,8));extra_scores=np.empty_like(scores);stream_scores=np.empty((64,2,4,4,2,2))
    diag=[];rng=np.random.default_rng(20261105083)
    for i,s in enumerate(ids):
        for ci,c in enumerate((200,1000)):
            for ni,name in enumerate(('growth','recent100','recent250','gru')):
                for hi,h in enumerate((500,2000)):
                    sample=pooled[i,ci,ni,:,hi,:]
                    scores[i,ci,ni,hi]=metrics(sample,obs[i,hi],h)
                    extra_scores[i,ci,ni,hi]=metrics(new[i,ci,ni,:,:,hi,:].reshape(512,7),obs[i,hi],h)
                    diag.append(dict(subject=s,lab=labs[i],condition='primary',cutoff=c,model=name,horizon=h,
                                     signs=calibration(sample,obs[i,hi],h,rng)))
                    for st in range(4):stream_scores[i,ci,ni,st,hi]=primary_risk(four[i,ci,ni,st,:,hi,:],obs[i,hi])
    np.savez_compressed(HERE/'REFINED_SCORES.npz',pooled1024=scores,additional512=extra_scores,
                        streams256=stream_scores,metrics=METRICS,subjects=ids)
    vectors=[];newcols=[]
    refs=[('recent_selected',1),('original',0),('recent100',1),('recent250',2)]
    for ref,ni in refs:
        for ci,c in enumerate((200,1000)):
            o=scores[:,ci,ni,1];g=scores[:,ci,3,1]
            meta=dict(kind='fixed_refined',condition='primary',neural='linear1024',reference=ref,cutoff=c,horizon=2000)
            newcols.append(dict(**meta,metric='A'));vectors.append(o[:,0]-g[:,0])
            newcols.append(dict(**meta,metric='D'));vectors.append(.9*o[:,1]-g[:,1])
    for hi,h in enumerate((500,2000)):
        gap=scores[:,:,1,hi]-scores[:,:,3,hi]
        for mi,label in ((0,'A_interaction'),(1,'raw_score_interaction')):
            newcols.append(dict(kind='interaction_refined',condition='primary',neural='linear1024',reference='recent_selected',horizon=h,metric=label))
            vectors.append(gap[:,0,mi]-gap[:,1,mi])
    X=np.column_stack([oldcon['contributions'],np.stack(vectors,axis=1)]);assert X.shape==(64,652)
    columns=family['columns']+newcols;primary=[632,633,634,635]
    counts=resampling_counts(20261105077);bands=joint_bands(X,primary,counts)
    alternate=joint_bands(X,primary,resampling_counts(20261105078,stratified=False),stratified=False)
    sites=site_sensitivity(X,labs,primary);primaryrows=[]
    for index in primary:
        c=columns[index];margin=.02 if c['metric']=='A' else 0.
        row=dict(index=index,**c,point=bands['point'][index],se=bands['se'][index],margin=margin,
             primary_lower=bands['primary']['lower'][index],primary_upper=bands['primary']['upper'][index],
             joint_lower=bands['joint']['lower'][index],joint_upper=bands['joint']['upper'][index],
             bonferroni_primary_lower=bands['bonferroni_primary']['lower'][index],bonferroni_primary_upper=bands['bonferroni_primary']['upper'][index],
             alternate_primary_lower=alternate['primary']['lower'][index],alternate_primary_upper=alternate['primary']['upper'][index])
        row.update(primary_excludes_material_benefit=row['primary_upper']<margin,
                   primary_establishes_material_benefit=row['primary_lower']>margin,primary_headroom=margin-row['primary_upper'])
        primaryrows.append(row)
    risks=base['absolute_risks']
    for ci,c in enumerate((200,1000)):
        for ni,name in enumerate(('growth','recent100','recent250','gru')):
            row=next(r for r in risks if r['condition']=='primary' and r['cutoff']==c and r['model']==name)
            values=scores[:,ci,ni,1];point=values.mean(0)
            se=np.sqrt((40/64)**2*np.var(values[:40],axis=0,ddof=1)/40+(24/64)**2*np.var(values[40:],axis=0,ddof=1)/24)
            q=float(t.ppf(.975,23));row['particles']=1024
            row['equal_animal']={m:float(point[j]) for j,m in enumerate(METRICS)}
            row['equal_animal_pointwise95']={m:[float(point[j]-q*se[j]),float(point[j]+q*se[j])] for j,m in enumerate(METRICS)}
            row['equal_site']={m:float(np.mean([values[np.array(labs)==lab,j].mean() for lab in sorted(set(labs))])) for j,m in enumerate(METRICS)}
    rowsMC=[]
    for ci,c in enumerate((200,1000)):
        for ref,ni in refs:
            oldO=oldmetrics['fixed'][:,0,ci,ni,1];oldG=oldmetrics['fixed'][:,0,ci,3,1]
            newO=extra_scores[:,ci,ni,1];newG=extra_scores[:,ci,3,1]
            oldA=float(np.mean(oldO[:,0]-oldG[:,0]));newA=float(np.mean(newO[:,0]-newG[:,0]))
            oldD=float(np.mean(.9*oldO[:,1]-oldG[:,1]));newD=float(np.mean(.9*newO[:,1]-newG[:,1]))
            rowsMC.append(dict(cutoff=c,reference=ref,old512_A=oldA,new512_A=newA,old512_D=oldD,new512_D=newD,
                 A_abs_difference=abs(newA-oldA),D_abs_difference=abs(newD-oldD)))
    leaves=[]
    for removed in range(4):
        for ci,c in enumerate((200,1000)):
            contributions=[]
            for i in range(64):
                O=np.delete(four[i,ci,1,:, :,1,:],removed,axis=0).reshape(768,7)
                G=np.delete(four[i,ci,3,:, :,1,:],removed,axis=0).reshape(768,7)
                oo=primary_risk(O,obs[i,1]);gg=primary_risk(G,obs[i,1])
                contributions.append([oo[0]-gg[0],.9*oo[1]-gg[1]])
            leaves.append(dict(removed_stream=removed,cutoff=c,A=float(np.mean(np.array(contributions)[:,0])),D=float(np.mean(np.array(contributions)[:,1]))))
    save('REFINED_MONTE_CARLO.json',dict(utc=utc(),old512_vs_additional512=rowsMC,leave_one_stream_out768=leaves,
         max_A_difference=max(r['A_abs_difference'] for r in rowsMC),max_D_difference=max(r['D_abs_difference'] for r in rowsMC),
         no_new_fit_or_pivot=True,source256_and_failed_stress512_warnings='Preserved in MAIN_MONTE_CARLO_INITIAL512; no broad envelope absence is earned'))
    save('REFINED_CALIBRATION.json',dict(utc=utc(),particles=1024,rows=diag,scope='Primarycondition only; other frozen conditions retain initial512 diagnostics'))
    calrows=[]
    for c in (200,1000):
        for name in ('growth','recent100','recent250','gru'):
            for h in (500,2000):
                selected=[r for r in diag if r['cutoff']==c and r['model']==name and r['horizon']==h]
                for feature in ('N','K','omissions','literal_success','conditional_ratio'):
                    animal=[];pits=[]
                    for r in selected:
                        signs=r['signs'] if feature in ('N','K','conditional_ratio') else r['signs'][:1]
                        vv=[s['readouts'][feature] for s in signs]
                        animal.append([np.mean([v['covered80'] for v in vv]),np.mean([v['covered95'] for v in vv]),np.mean([v['randomized_PIT'] for v in vv])])
                        pits.extend(v['randomized_PIT'] for v in vv)
                    animal=np.array(animal);point=animal.mean(0)
                    se=np.sqrt((40/64)**2*np.var(animal[:40],axis=0,ddof=1)/40+(24/64)**2*np.var(animal[40:],axis=0,ddof=1)/24)
                    q=float(t.ppf(.975,23))
                    calrows.append(dict(cutoff=c,model=name,horizon=h,readout=feature,coverage80=float(point[0]),coverage95=float(point[1]),mean_PIT=float(point[2]),
                         pointwise95_lower=np.maximum(0,point-q*se).tolist(),pointwise95_upper=np.minimum(1,point+q*se).tolist(),
                         PIT_histogram10=np.histogram(pits,bins=np.linspace(0,1,11))[0].tolist(),animal_units=64))
    save('REFINED_CALIBRATION_SUMMARY.json',dict(utc=utc(),rows=calrows,particles=1024,uncertainty='pointwise t23 whole-animal/cohort-weighted diagnostic intervals'))
    initialrows=base['primary_rows'];base.update(utc=utc(),primary_rows=primaryrows,initial_primary_rows_512=initialrows,
         primary_indices=primary,bands=bands,alternate_unstratified=alternate,site_sensitivity=sites,
         primary_particles=1024,joint_column_count=652,original_frozen_joint_632_file='MAIN_ANALYSIS_INITIAL512.json',
         primary_all_four_exclude_material=all(r['primary_excludes_material_benefit'] for r in primaryrows),
         finite_joint_envelope_excludes_material=all(bands['joint']['upper'][i]<(0.02 if col['metric']=='A' else 0.) for i,col in enumerate(columns) if col['metric'] in ('A','D')),
         numerical_refinement='NUMERICAL_REFINEMENT.md; originalresults preserved, only primary integration increased to1024 under measured error trigger')
    save('MAIN_ANALYSIS.json',base)
    save('MAIN_FAMILY_REFINED.json',dict(utc=utc(),columns=columns,primary_indices=primary,n_columns=652,original632_preserved=True))
    np.savez_compressed(HERE/'REFINED_CONTRASTS.npz',contributions=X,primary_indices=primary,subjects=ids,labs=labs)
    save('REFINEMENT_ANALYSIS_RESOURCES.json',dict(utc=utc(),scientific_cpu_seconds=time.process_time()-CPU,
         process_wall_seconds=time.monotonic()-BEGIN,io=dict(IO),explicit_read_decode_bytes=sum(IO.values()),
         peak_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,pins=PINS))
    print('REFINEMENT ANALYSIS COMPLETE',json.dumps(primaryrows),flush=True)

if __name__=='__main__':
    try:main()
    except BaseException as exc:
        save('REFINEMENT_ANALYSIS_FAILURE_'+str(time.time())+'.json',dict(error=repr(exc),scientific_cpu_seconds=time.process_time()-CPU,
             process_wall_seconds=time.monotonic()-BEGIN,io=dict(IO)))
        raise
