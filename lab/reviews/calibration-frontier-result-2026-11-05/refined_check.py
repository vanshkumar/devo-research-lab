"""Independent pooling of the fixed1024-particle refinement; no author imports."""
import time
import numpy as np
from independent import HERE, MAIN, Accounting, save, score, bands, primary_vectors, cohorts_and_sites


def main():
    meter=Accounting('final independent1024-particle refinement')
    status=meter.json(MAIN/'REFINEMENT_EXECUTION.json')
    assert status['status']=='complete' and status['completed_animals']==64
    plan=meter.read(MAIN/'NUMERICAL_REFINEMENT.md').decode()
    cache=meter.arrays(HERE/'FIXED_CACHE.npz')
    base=meter.arrays(HERE/'FULL_CONTRASTS.npz')
    original_family=meter.json(HERE/'SOURCE_FAMILY_PREAUTHOR.json')
    old=meter.arrays(MAIN/'MAIN_COUNTS.npz',keys=['samples','subjects','stream_offsets'])
    new=meter.arrays(MAIN/'REFINED_ADDITIONAL_COUNTS.npz')
    assert np.array_equal(new['subjects'],cache['subjects']) and np.array_equal(old['subjects'],cache['subjects'])
    assert new['stream_offsets'].tolist()==[20000038,30000057]
    assert old['stream_offsets'].tolist()==[0,10000019]
    # Pool actual count draws. Averaging old/new MAEs or energy scores would be wrong.
    # This one new raw-count read is needed because the first-stage cache kept scores,
    # not particles. It is fully charged; no old fixed reconstruction is repeated.
    old_primary=old['samples'][:,0]
    draws=np.concatenate([old_primary,new['samples']],axis=3)
    assert draws.shape==(64,2,4,4,256,2,7)
    full=np.empty((64,2,4,2,8));fresh=np.empty_like(full)
    leave=np.empty((4,64,2,2))
    for i in range(64):
        for c in range(2):
            for actor in range(4):
                for w,horizon in enumerate([500,2000]):
                    full[i,c,actor,w]=score(draws[i,c,actor,:,:,w].reshape(1024,7),cache['observed'][i,w],horizon)
                    fresh[i,c,actor,w]=score(new['samples'][i,c,actor,:,:,w].reshape(512,7),cache['observed'][i,w],horizon)
            for dropped in range(4):
                m=[]
                for actor in [1,3]:
                    x=np.delete(draws[i,c,actor,:,:,1],dropped,axis=0).reshape(768,7)
                    m.append(score(x,cache['observed'][i,1],2000))
                leave[dropped,i,c]=[m[0][0]-m[1][0],.9*m[0][1]-m[1][1]]
    assert np.isfinite(full).all() and np.isfinite(fresh).all()
    xprimary=primary_vectors(full[:,None])
    labels=list(original_family['labels']);vectors=[v for v in base['contributions'].T]
    refined_primary=[]
    for ref,actor in [('recent_selected',1),('original',0),('recent100',1),('recent250',2)]:
        for c,cutoff in enumerate([200,1000]):
            o=full[:,c,actor,1];g=full[:,c,3,1]
            for metric,v in [('A',o[:,0]-g[:,0]),('D',.9*o[:,1]-g[:,1])]:
                if ref=='recent_selected': refined_primary.append(len(labels))
                labels.append(dict(kind='refined',condition='primary',neural='linear1024',reference=ref,cutoff=cutoff,horizon=2000,metric=metric))
                vectors.append(v)
    for w,horizon in enumerate([500,2000]):
        gap=full[:,:,1,w]-full[:,:,3,w]
        for m,metric in [(0,'A_interaction'),(1,'raw_score_interaction')]:
            labels.append(dict(kind='refined_interaction',condition='primary',neural='linear1024',reference='recent_selected',horizon=horizon,metric=metric))
            vectors.append(gap[:,0,m]-gap[:,1,m])
    x=np.stack(vectors,axis=1)
    assert x.shape==(64,652) and refined_primary==[632,633,634,635]
    assert np.array_equal(x[:,:632],base['contributions'])
    joint=bands(x,cache['bootstrap_weights'],selected=refined_primary)
    primary=bands(xprimary,cache['bootstrap_weights'])
    oldx=primary_vectors(cache['fixed']);newx=primary_vectors(fresh[:,None])
    leave_mean=leave.mean(axis=1).reshape(4,4)
    numerical=dict(old512_point=oldx.mean(0),new512_point=newx.mean(0),
                   new512_minus_old512_point=newx.mean(0)-oldx.mean(0),
                   leave_one_stream_out_points=leave_mean,
                   leave_one_stream_out_max_abs_shift=np.max(np.abs(leave_mean-xprimary.mean(0)),axis=0),
                   warning_thresholds=[.0025,.001,.0025,.001],
                   interpretation='Finite integration diagnostics only; no added biological units or uncertainty-tail certification')
    save('REFINED_CHECK.json',dict(primary_columns=['A200','D200','A1000','D1000'],primary=primary,
        original_primary512=original_family['bands']['primary'],augmented=joint,refined_primary_indices=refined_primary,
        original632_unchanged=True,numerical=numerical,absolute_risks=full[:,:,:,1].mean(0),
        cohort_site=cohorts_and_sites(xprimary,cache['labs']),labels=labels))
    np.savez_compressed(HERE/'REFINED_SCORE_CACHE.npz',metrics=full,new512_metrics=fresh,
                        contributions=x,leave_stream=leave,subjects=cache['subjects'])
    save('REFINED_RESOURCES.json',meter.receipt())
    print(dict(primary_point=xprimary.mean(0).tolist(),primary_upper=primary['primary']['upper'].tolist(),
               bonferroni_upper=primary['bonferroni_primary']['upper'].tolist(),
               augmented_joint_primary_upper=joint['joint']['upper'][refined_primary].tolist(),
               numerical=numerical,resources=meter.receipt()))


if __name__=='__main__':
    cpu=time.process_time()
    try: main()
    except BaseException as exc:
        save('REFINED_CHECK_FAILURE_'+str(time.time_ns())+'.json',dict(error=repr(exc),process_cpu_seconds=time.process_time()-cpu))
        raise
