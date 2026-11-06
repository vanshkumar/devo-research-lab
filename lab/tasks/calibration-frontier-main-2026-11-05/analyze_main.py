"""Frozen saved-count scoring, primary4 and complete joint-family inference."""
import time,resource
BEGIN=time.monotonic();CPU=time.process_time()
import io,json,hashlib
from pathlib import Path
from datetime import datetime,timezone
from collections import Counter
import numpy as np
from scipy.stats import t as student_t
from main_scores import metrics,calibration,METRICS
from main_inference import resampling_counts,joint_bands,site_sensitivity

HERE=Path(__file__).resolve().parent;IO=Counter();PINS={}

def serial(x):
    if isinstance(x,np.ndarray):return x.tolist()
    if isinstance(x,np.generic):return x.item()
    raise TypeError(type(x).__name__)
def save(name,x):(HERE/name).write_text(json.dumps(x,indent=2,allow_nan=False,default=serial)+'\n')
def read(p):
    b=p.read_bytes();IO['explicit_read_bytes']+=len(b);PINS[p.name]=hashlib.sha256(b).hexdigest();return b
def arrays(name):
    with np.load(io.BytesIO(read(HERE/name)),allow_pickle=False) as z:r={k:z[k] for k in z.files}
    IO['decoded_array_bytes']+=sum(v.nbytes for v in r.values());return r
def get(name):return json.loads(read(HERE/name))
def utc():return datetime.now(timezone.utc).isoformat()


def main():
    source=arrays('MAIN_SOURCE_COUNTS.npz');fixed=arrays('MAIN_COUNTS.npz');target=arrays('MAIN_OBSERVED.npz')
    execution=get('MAIN_EXECUTION.json');assert execution['status']=='complete'
    observed=target['observed'];ids=target['subjects'].tolist();labs=target['labs'].tolist()
    assert ids==fixed['subjects'].tolist()==source['subjects'].tolist()
    S=fixed['samples'];E=fixed['exact_samples'];B=source['samples']
    assert S.shape==(64,3,2,4,2,256,2,7) and E.shape==(64,3,2,256,2,7)
    assert B.shape==(32,64,2,2,256,2,7)
    allmetrics=np.empty((64,3,2,4,2,8));streammetrics=np.empty((64,3,2,4,2,2,8))
    exactmetrics=np.empty((64,3,2,2,8));source_metrics=np.empty((32,64,2,2,2,8))
    source_halves=np.empty((32,64,2,2,2,2));neural_halves=np.empty((64,2,2,2,2))
    rng=np.random.default_rng(20261105083);diagnostics=[]
    for i,s in enumerate(ids):
        for k,condition in enumerate(fixed['conditions']):
            for ci,c in enumerate((200,1000)):
                for ni,name in enumerate(fixed['names']):
                    for hi,h in enumerate((500,2000)):
                        combined=S[i,k,ci,ni,:,:,hi,:].reshape(512,7)
                        allmetrics[i,k,ci,ni,hi]=metrics(combined,observed[i,hi],h)
                        for st in (0,1):streammetrics[i,k,ci,ni,st,hi]=metrics(S[i,k,ci,ni,st,:,hi,:],observed[i,hi],h)
                        diagnostics.append(dict(subject=s,lab=labs[i],cohort='old40' if i<40 else 'later24',
                             condition=str(condition),cutoff=c,model=str(name),horizon=h,
                             signs=calibration(combined,observed[i,hi],h,rng)))
                for hi,h in enumerate((500,2000)):
                    exactmetrics[i,k,ci,hi]=metrics(E[i,k,ci,:,hi,:],observed[i,hi],h)
                if k==0:
                    for mode in (0,1):
                        ensemble=S[i,0,ci,3,0,:,1,:] if mode==0 else E[i,0,ci,:,1,:]
                        for half in (0,1):neural_halves[i,ci,mode,half]=metrics(ensemble[half*128:(half+1)*128],observed[i,1],2000)[:2]
        if (i+1)%16==0:print('SCORED FIXED',i+1,'CPU',round(time.process_time()-CPU,2),flush=True)
    for j in range(32):
        for i in range(64):
            for ci in (0,1):
                for ni in (0,1):
                    for hi,h in enumerate((500,2000)):source_metrics[j,i,ci,ni,hi]=metrics(B[j,i,ci,ni,:,hi,:],observed[i,hi],h)
                    for half in (0,1):source_halves[j,i,ci,ni,half]=metrics(B[j,i,ci,ni,half*128:(half+1)*128,1,:],observed[i,1],2000)[:2]
        if (j+1)%4==0:print('SCORED SOURCE',j+1,'CPU',round(time.process_time()-CPU,2),flush=True)
    assert np.isfinite(allmetrics).all() and np.isfinite(source_metrics).all() and np.isfinite(exactmetrics).all()
    np.savez_compressed(HERE/'MAIN_SCORES.npz',fixed=allmetrics,streams=streammetrics,exact_gru=exactmetrics,
         source=source_metrics,source_halves=source_halves,neural_halves=neural_halves,metrics=METRICS,subjects=ids)
    save('MAIN_CALIBRATION.json',dict(utc=utc(),particle_count=512,rows=diagnostics,
         missingness='Positive-count conditional ratio intervals and explicit positive mass; no zero imputation',
         coverage_scope='Descriptive predictive coverage/PIT; future boundaries supplied; no claim of latent competence calibration'))
    calibration_summary=[]
    for condition in fixed['conditions']:
        for c in (200,1000):
            for name in fixed['names']:
                for h in (500,2000):
                    selected=[r for r in diagnostics if r['condition']==condition and r['cutoff']==c and r['model']==name and r['horizon']==h]
                    assert len(selected)==64
                    for readout in ('N','K','omissions','literal_success','conditional_ratio'):
                        animal=[];pits=[]
                        for row in selected:
                            signs=row['signs'] if readout in ('N','K','conditional_ratio') else row['signs'][:1]
                            values=[sign['readouts'][readout] for sign in signs if readout in sign['readouts']]
                            assert values
                            animal.append([np.mean([v['covered80'] for v in values]),np.mean([v['covered95'] for v in values]),np.mean([v['randomized_PIT'] for v in values])])
                            pits.extend(v['randomized_PIT'] for v in values)
                        animal=np.array(animal);point=animal.mean(0)
                        se=np.sqrt((40/64)**2*np.var(animal[:40],axis=0,ddof=1)/40+(24/64)**2*np.var(animal[40:],axis=0,ddof=1)/24)
                        q=float(student_t.ppf(.975,23));low=point-q*se;high=point+q*se
                        hist=np.histogram(pits,bins=np.linspace(0,1,11))[0]
                        calibration_summary.append(dict(condition=str(condition),cutoff=c,model=str(name),horizon=h,readout=readout,
                             coverage80=float(point[0]),coverage95=float(point[1]),mean_randomized_PIT=float(point[2]),
                             pointwise95_lower=np.maximum(0,low).tolist(),pointwise95_upper=np.minimum(1,high).tolist(),
                             interval_columns=['coverage80','coverage95','mean_PIT'],PIT_histogram10=hist.tolist(),
                             animal_units=64,readout_entries=len(pits)))
    save('MAIN_CALIBRATION_SUMMARY.json',dict(utc=utc(),rows=calibration_summary,
         uncertainty='Pointwise t23 working intervals on whole-animal averages, fixed40/24cohort weights; diagnostic, not multiplicity-adjusted primary tests',
         two_signs='Signs average within each animal; omissions/literal successes counted once per animal, not twice'))
    # Same paired contribution matrix supports both explicitly frozen families.
    columns=[];vectors=[]
    def add(label,vector):
        assert vector.shape==(64,) and np.isfinite(vector).all();columns.append(label);vectors.append(vector)
    refnames=[('recent_selected',1),('original',0),('recent100',1),('recent250',2)]
    for k,condition in enumerate(fixed['conditions']):
        for mode in ('linear512','exact256'):
            for ref,ni in refnames:
                for ci,c in enumerate((200,1000)):
                    ordinary=allmetrics[:,k,ci,ni,1] if mode=='linear512' else streammetrics[:,k,ci,ni,0,1]
                    gru=allmetrics[:,k,ci,3,1] if mode=='linear512' else exactmetrics[:,k,ci,1]
                    base=dict(kind='fixed',condition=str(condition),neural=mode,reference=ref,cutoff=c,horizon=2000)
                    add(dict(**base,metric='A'),ordinary[:,0]-gru[:,0])
                    add(dict(**base,metric='D'),.9*ordinary[:,1]-gru[:,1])
    for j in range(32):
        for mode in ('linear256','exact256'):
            for ni,ref in enumerate(('original','recent_selected')):
                for ci,c in enumerate((200,1000)):
                    ordinary=source_metrics[j,:,ci,ni,1]
                    gru=streammetrics[:,0,ci,3,0,1] if mode=='linear256' else exactmetrics[:,0,ci,1]
                    base=dict(kind='source',draw=j,condition='primary',neural=mode,reference=ref,cutoff=c,horizon=2000)
                    add(dict(**base,metric='A'),ordinary[:,0]-gru[:,0])
                    add(dict(**base,metric='D'),.9*ordinary[:,1]-gru[:,1])
    for k,condition in enumerate(fixed['conditions']):
        for mode in ('linear512','exact256'):
            for hi,h in enumerate((500,2000)):
                if mode=='linear512':
                    o=allmetrics[:,k,:,1,hi];g=allmetrics[:,k,:,3,hi]
                else:o=streammetrics[:,k,:,1,0,hi];g=exactmetrics[:,k,:,hi]
                gap=o-g
                for mi,label in ((0,'A_interaction'),(1,'raw_score_interaction')):
                    add(dict(kind='interaction',condition=str(condition),neural=mode,reference='recent_selected',horizon=h,metric=label),gap[:,0,mi]-gap[:,1,mi])
    X=np.stack(vectors,axis=1);assert X.shape==(64,632)
    primary=[i for i,c in enumerate(columns) if c['kind']=='fixed' and c['condition']=='primary' and c['neural']=='linear512' and c['reference']=='recent_selected']
    assert len(primary)==4
    counts=resampling_counts(20261105077)
    bands=joint_bands(X,primary,counts,stratified=True)
    alternate=joint_bands(X,primary,resampling_counts(20261105078,stratified=False),stratified=False)
    sites=site_sensitivity(X,labs,primary)
    np.savez_compressed(HERE/'MAIN_CONTRASTS.npz',contributions=X,primary_indices=primary,subjects=ids,labs=labs)
    np.savez_compressed(HERE/'BOOTSTRAP_COUNTS.npz',counts=counts,seed=np.array(20261105077))
    save('MAIN_FAMILY.json',dict(utc=utc(),columns=columns,primary_indices=primary,n_columns=len(columns),
         amended_primary='four long-window selected-recent vsGRU, original primary environment/linear initialization',
         original_joint='all632 frozen fixed/source/numerical/interaction columns, including duplicates'))
    primary_rows=[]
    for index in primary:
        col=columns[index];margin=.02 if col['metric']=='A' else 0.
        row=dict(index=index,**col,point=bands['point'][index],se=bands['se'][index],margin=margin,
             primary_lower=bands['primary']['lower'][index],primary_upper=bands['primary']['upper'][index],
             joint_lower=bands['joint']['lower'][index],joint_upper=bands['joint']['upper'][index],
             bonferroni_primary_lower=bands['bonferroni_primary']['lower'][index],
             bonferroni_primary_upper=bands['bonferroni_primary']['upper'][index],
             alternate_primary_lower=alternate['primary']['lower'][index],alternate_primary_upper=alternate['primary']['upper'][index])
        row['primary_excludes_material_benefit']=row['primary_upper']<margin
        row['primary_establishes_material_benefit']=row['primary_lower']>margin
        row['primary_headroom']=margin-row['primary_upper'];primary_rows.append(row)
    envelope=[i for i,c in enumerate(columns) if c['metric'] in ('A','D')]
    all_absent=all(bands['joint']['upper'][i]<(0.02 if columns[i]['metric']=='A' else 0.) for i in envelope)
    summary=[]
    for k,condition in enumerate(fixed['conditions']):
        for ci,c in enumerate((200,1000)):
            for ni,name in enumerate(fixed['names']):
                row=dict(condition=str(condition),cutoff=c,model=str(name),
                         equal_animal={m:float(allmetrics[:,k,ci,ni,1,j].mean()) for j,m in enumerate(METRICS)})
                values=allmetrics[:,k,ci,ni,1];point=values.mean(0)
                sese=np.sqrt((40/64)**2*np.var(values[:40],axis=0,ddof=1)/40+(24/64)**2*np.var(values[40:],axis=0,ddof=1)/24)
                q=float(student_t.ppf(.975,23))
                row['equal_animal_pointwise95']={m:[float(point[j]-q*sese[j]),float(point[j]+q*sese[j])] for j,m in enumerate(METRICS)}
                unique=sorted(set(labs));row['equal_site']={m:float(np.mean([allmetrics[np.array(labs)==lab,k,ci,ni,1,j].mean() for lab in unique])) for j,m in enumerate(METRICS)}
                summary.append(row)
    source_records=get('MAIN_SOURCE_DRAWS.json')['draws']
    frequencies=Counter(r['chosen'] for r in source_records)
    source_points=[]
    for j in range(32):
        for ci,c in enumerate((200,1000)):
            for ni,ref in enumerate(('original','recent_selected')):
                ordinary=source_metrics[j,:,ci,ni,1];gru=streammetrics[:,0,ci,3,0,1]
                source_points.append(dict(draw=j,chosen=source_records[j]['chosen'],cutoff=c,reference=ref,
                     A=float(np.mean(ordinary[:,0]-gru[:,0])),D=float(np.mean(.9*ordinary[:,1]-gru[:,1]))))
    mc=[]
    for k,condition in enumerate(fixed['conditions']):
        for ci,c in enumerate((200,1000)):
            for ref,ni in refnames:
                om=streammetrics[:,k,ci,ni,:,1];gm=streammetrics[:,k,ci,3,:,1]
                A=np.mean(om[:,:,0]-gm[:,:,0],axis=0);D=np.mean(.9*om[:,:,1]-gm[:,:,1],axis=0)
                mc.append(dict(kind='fixed_streams',condition=str(condition),reference=ref,cutoff=c,
                     A_streams=A.tolist(),D_streams=D.tolist(),A_abs_difference=float(abs(A[1]-A[0])),D_abs_difference=float(abs(D[1]-D[0]))))
    source_mc=[]
    for j in range(32):
        for ci,c in enumerate((200,1000)):
            for ni,ref in enumerate(('original','recent_selected')):
                for mode in (0,1):
                    om=source_halves[j,:,ci,ni];gm=neural_halves[:,ci,mode]
                    A=(om[:,:,0]-gm[:,:,0]).mean(0);D=(.9*om[:,:,1]-gm[:,:,1]).mean(0)
                    source_mc.append(dict(kind='source_halves',draw=j,reference=ref,cutoff=c,neural='linear256' if mode==0 else 'exact256',
                         A_halves=A.tolist(),D_halves=D.tolist(),A_abs_difference=float(abs(A[1]-A[0])),D_abs_difference=float(abs(D[1]-D[0]))))
    nonlinear=[]
    for k,condition in enumerate(fixed['conditions']):
        for ci,c in enumerate((200,1000)):
            old=streammetrics[:,k,ci,3,0,1];new=exactmetrics[:,k,ci,1]
            nonlinear.append(dict(condition=str(condition),cutoff=c,
                  A_gain_shift=float(np.mean(old[:,0]-new[:,0])),D_gain_shift=float(np.mean(old[:,1]-new[:,1]))))
    save('MAIN_MONTE_CARLO.json',dict(utc=utc(),fixed_streams=mc,source_halves=source_mc,nonlinear=nonlinear,
         warning_thresholds=dict(A=.0025,D=.001),max_fixed_A_difference=max(x['A_abs_difference'] for x in mc),
         max_fixed_D_difference=max(x['D_abs_difference'] for x in mc),
         max_source_A_difference=max(x['A_abs_difference'] for x in source_mc),max_source_D_difference=max(x['D_abs_difference'] for x in source_mc),
         scope='Numerical split/stream checks, separate from conditional animal bands and finite source envelope; not biological confidence'))
    save('MAIN_ANALYSIS.json',dict(utc=utc(),primary_rows=primary_rows,primary_all_four_exclude_material=all(r['primary_excludes_material_benefit'] for r in primary_rows),
         finite_joint_envelope_excludes_material=all_absent,primary_indices=primary,bands=bands,alternate_unstratified=alternate,
         site_sensitivity=sites,absolute_risks=summary,source_selection_frequencies=dict(frequencies),source_points=source_points,
         data_scope='Consumed postvalidation, fixed neural weights and supplied future session/opportunity boundaries',
         failed_stresses='Source-context input and source-calibrated engagement remain failed algorithm stresses, not validated environments'))
    save('ANALYSIS_RESOURCES.json',dict(utc=utc(),scientific_cpu_seconds=time.process_time()-CPU,
         process_wall_seconds=time.monotonic()-BEGIN,io=dict(IO),explicit_read_decode_bytes=sum(IO.values()),
         peak_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,pins=PINS,
         raw_trial_reads=0,physical_io='unknown',import_provider_runtime_reads='unknown'))
    print('ANALYSIS COMPLETE',json.dumps(primary_rows),flush=True)


if __name__=='__main__':
    try:main()
    except BaseException as exc:
        save('ANALYSIS_FAILURE_'+utc().replace(':','-')+'.json',dict(utc=utc(),error=repr(exc),
             scientific_cpu_seconds=time.process_time()-CPU,process_wall_seconds=time.monotonic()-BEGIN,io=dict(IO)))
        raise
