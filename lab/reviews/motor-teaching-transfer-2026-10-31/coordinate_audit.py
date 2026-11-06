"""Independent coordinate, masks, aggregation and reported source-fit audit."""
import reconstruct as r
import csv
import io
import json
import hashlib
import resource
import warnings
from collections import defaultdict, Counter
import numpy as np
from threadpoolctl import threadpool_limits

def nanmean_prefix(y):
    good=np.isfinite(y)
    sums=np.r_[0.,np.cumsum(np.where(good,y,0.))]
    counts=np.r_[0,np.cumsum(good)]
    def avg(a,b):
        n=counts[b]-counts[a]
        return (sums[b]-sums[a])/n if n else float('nan')
    n=len(y)
    literal=np.array([y[0],avg(0,3)]+[avg(1,i+1) for i in range(2,n-2)]+[avg(n-3,n),y[-1]])
    centered=np.array([y[0],avg(0,3)]+[avg(i-2,i+3) for i in range(2,n-2)]+[avg(n-3,n),y[-1]])
    return literal,centered

def main():
    saved=r.load_json(r.AUTHOR/'SOURCE_ANALYSIS.json')
    endpoint=r.load_json(r.HERE/'RECONSTRUCTION.json')
    measurement=r.load_json(r.AUTHOR/'MEASUREMENT_SENSITIVITY.json')
    masks=[];coefficient_errors=[];loss_errors=[];allcode=[]
    for si,name in enumerate(r.FILES):
        body=r.read(r.SOURCE/name,8)
        reader=csv.DictReader(io.StringIO(body.decode()))
        by=defaultdict(list);coordinates=[]
        tsay=si<2
        for row in reader:
            if tsay:
                v=dict(p=int(row['SN']),t=int(row['TN']),c=r.number(row['clamp_size']),
                       j=r.number(row['tgt_jump_size']),f=0,h=r.number(row['Hand_raw']),bad=False)
            else:
                j=r.number(row['TargetJump'])
                v=dict(p=int(row['Subject']),t=int(row['TrialNum']),c=r.number(row['ClampAngle']),
                       j=0. if j==.01 else j,f=int(j==.01),h=r.number(row['HandError']),
                       bad=r.number(row['FalseStart'])==1)
                if 'HandAngle' in row and 'TgtAngle' in row:
                    coordinates.append([r.number(row['HandAngle']),r.number(row['TgtAngle']),v['h'],v['j'],v['t']])
            by[v['p']].append(v)
        people=[];reasons=Counter();nrows=Counter();perperson=[]
        literal_person=[];center_person=[]
        for p,rr in sorted(by.items()):
            rr.sort(key=lambda v:v['t'])
            for v in rr:
                if not r.core(v,tsay):
                    continue
                nrows['exposure_rows']+=1
                reasons['nonfinite']+=int(not np.isfinite(v['h']))
                reasons['finite_abs_gt90']+=int(np.isfinite(v['h']) and abs(v['h'])>90)
                reasons['FalseStart']+=int(v['bad'])
                reasons['union_rejected']+=int(not r.valid(v))
            tr=r.transitions(rr,tsay)
            X=[];Y=[]
            for a,b in tr:
                c=a['c']/4;j=a['j']/4
                X.append([1.,c,c*bool(a['j'] or a['f']),c*bool(a['c'] and a['j']==a['c']),j,(b['j']-a['j'])/4])
                Y.append(b['h']-a['h'])
            X=np.asarray(X);Y=np.asarray(Y)
            coef,_,rank,_=np.linalg.lstsq(X,Y,rcond=None)
            old=next(v for v in saved['sources'][si]['per_person'] if v['person']==p)
            coefficient_errors.append(float(abs(coef-np.asarray(old['coefficient'])).max()))
            perperson.append(dict(person=p,n=len(Y),rank=int(rank),success_column_all_zero=bool(not np.any(X[:,3])),
                                  coefficient=coef.tolist()))
            people.append((p,X,Y))
            if not tsay:
                core_rows=[v for v in rr if v['t']>103]
                y=np.array([v['h'] for v in core_rows]);literal,centered=nanmean_prefix(y)
                for sm,store in ((literal,literal_person),(centered,center_person)):
                    residual=y-sm;sd=np.nanstd(residual,ddof=1)
                    good=np.isfinite(y)&(abs(residual)<=3*sd)&(abs(y)<=90)&np.array([not v['bad'] for v in core_rows])
                    bins=defaultdict(list)
                    for k in range(len(core_rows)-1):
                        a=core_rows[k];b=core_rows[k+1]
                        if not good[k] or not good[k+1] or a['t']>903 or a['f'] or a['j'] not in (0,a['c']):
                            continue
                        bins[(int(np.sign(a['c'])),a['j']==a['c'])].append(-np.sign(a['c'])*(b['h']-a['h']))
                    store.append([float(np.mean([np.median(bins[(sgn,jump)]) for sgn in (-1,1)])) for jump in (False,True)])
        # Independent equal-person leave-person-out reconstruction with training centering.
        models=[]
        for model,indices in [('success_task_error',[0,1,3,4,5]),('intervention_task_error',[0,1,2,4,5]),
                              ('full_source_diagnostic',[0,1,2,3,4,5])]:
            losses=[]
            for k,(p,X,Y) in enumerate(people):
                trainX=[];trainY=[]
                for j,(q,xx,yy) in enumerate(people):
                    if j==k:
                        continue
                    z=xx[:,indices[1:]]
                    trainX.append((z-z.mean(axis=0))/np.sqrt(len(yy)))
                    trainY.append((yy-yy.mean())/np.sqrt(len(yy)))
                beta=np.linalg.lstsq(np.concatenate(trainX),np.concatenate(trainY),rcond=None)[0]
                z=X[:,indices[1:]]
                prediction=np.einsum('ni,i->n',z-z.mean(axis=0),beta)
                losses.append(float(np.mean((Y-Y.mean()-prediction)**2)))
            old=next(v for v in saved['sources'][si]['model_comparison'] if v['model']==model)
            loss_errors.append(float(np.max(abs(np.array(losses)-np.array(old['per_person_MSE'])))))
            models.append(dict(model=model,per_person_MSE=losses,equal_person_MSE=float(np.mean(losses))))
        coord=None
        if coordinates:
            v=np.array(coordinates);good=np.isfinite(v[:,:3]).all(axis=1);v=v[good]
            candidates={
                'HandAngle_minus_initial_TgtAngle':v[:,0]-v[:,1],
                'initial_TgtAngle_minus_HandAngle':v[:,1]-v[:,0],
                'wrapped_HandAngle_minus_initial_TgtAngle':(v[:,0]-v[:,1]+180)%360-180,
                'wrapped_initial_TgtAngle_minus_HandAngle':(v[:,1]-v[:,0]+180)%360-180,
                'HandAngle_minus_shifted_TgtAngle':v[:,0]-v[:,1]-v[:,3]}
            coord=dict(n_finite=len(v),candidate_errors={k:dict(max_absolute=float(abs(z-v[:,2]).max()),
                              RMS=float(np.sqrt(np.mean((z-v[:,2])**2)))) for k,z in candidates.items()},
                       TgtAngle_values=np.unique(v[:,1]).tolist(),
                       qualification='An export-column identity check; upstream acquisition code remains absent.')
        masks.append(dict(source=name,rows=dict(nrows),rejected_row_reasons=dict(reasons),per_person=perperson,
                          source_models=models,coordinate_identity=coord))
        if not tsay:
            old=next(v for v in measurement['sources'] if v['source']==name)
            masks[-1]['literal_mask']=r.summary(literal_person)
            masks[-1]['centered_mask']=r.summary(center_person)
            masks[-1]['literal_saved_person_error']=float(abs(np.asarray(literal_person)-np.asarray(old['methods']['literal_author_mask_median']['per_person'])).max())
            masks[-1]['centered_saved_person_error']=float(abs(np.asarray(center_person)-np.asarray(old['methods']['centered_author_mask_median']['per_person'])).max())
    groups=[]
    for si in (0,2):
        v=np.array([[p['effects']['current_plus_next'][c] for c in ('No Jump','Jump To')] for p in endpoint['sources'][si]['people']])
        groups.append(v)
    a,f=groups
    shift=f[:,1].mean()/f[:,0].mean()-a[:,1].mean()/a[:,0].mean()
    deletions=[]
    for source,v,other in [('Tsay',a,f),('Figure3',f,a)]:
        for k in range(len(v)):
            new=np.delete(v,k,axis=0).mean(axis=0)
            qo=other[:,1].mean()/other[:,0].mean()
            q=new[1]/new[0]
            deletions.append(dict(source=source,person=endpoint['sources'][0 if source=='Tsay' else 2]['people'][k]['person'],
                                  shift=float(qo-q if source=='Tsay' else q-qo)))
    aggregation=[]
    for label,v in [('Tsay',a),('Figure3',f)]:
        aggregation.append(dict(source=label,ratio_of_means=float(v[:,1].mean()/v[:,0].mean()),
                                ratio_of_medians=float(np.median(v[:,1])/np.median(v[:,0])),
                                median_of_person_ratios=float(np.median(v[:,1]/v[:,0])),
                                person_stationary_nonpositive=int(np.sum(v[:,0]<=0))))
    result=dict(created_utc=r.now(),source_audits=masks,
                max_source_coefficient_error=max(coefficient_errors),max_source_LOO_loss_error=max(loss_errors),
                aggregation_sensitivity=aggregation,single_person_deletions=deletions,
                single_deletion_shift_range=[min(v['shift'] for v in deletions),max(v['shift'] for v in deletions)],
                primary_shift=float(shift))
    r.record('COORDINATE_MASK_AUDIT.json',result)
    r.record('AUDIT_RUN.json',dict(finished_utc=r.now(),read_passes=r.READS,
                                 charged_bytes=sum(v['charged_bytes'] for v in r.READS),
                                 peak_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,jobs_running_at_exit=0))
    print(json.dumps(dict(coefficient_error=result['max_source_coefficient_error'],LOO_error=result['max_source_LOO_loss_error'],
                          aggregation=aggregation,deletion_range=result['single_deletion_shift_range'],
                          source_summary=[dict(source=s['source'],rejected=s['rejected_row_reasons'],coordinates=s['coordinate_identity'],
                                               literal_error=s.get('literal_saved_person_error'),centered_error=s.get('centered_saved_person_error')) for s in masks],
                          charged_bytes=sum(v['charged_bytes'] for v in r.READS),peak_rss=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)),flush=True)

if __name__=='__main__':
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter('always')
        with threadpool_limits(limits=1):main()
        r.record('AUDIT_WARNINGS.json',dict(warnings=[dict(message=str(w.message),file=w.filename,line=w.lineno) for w in caught]))
