"""Complete independent source-envelope/family assessment from permitted saved outputs."""
import json
import sys
import time
from collections import Counter
import numpy as np
from independent import (HERE, MAIN, METRICS, Accounting, save, score, bands,
                         bootstrap_weights, cohorts_and_sites)


def assemble(fixed,streams,exact,source=None):
    labels=[];vectors=[]
    conditions=['primary','source_context_input','source_calibrated_engagement']
    def add(label,vector):
        assert vector.shape==(64,) and np.isfinite(vector).all()
        labels.append(label);vectors.append(vector)
    # Keep duplicate selected/100 columns. They do not change the max statistic.
    for k,condition in enumerate(conditions):
        for mode in ['linear512','exact256']:
            for ref,a in [('recent_selected',1),('original',0),('recent100',1),('recent250',2)]:
                for c,cutoff in enumerate([200,1000]):
                    o=fixed[:,k,c,a,1] if mode=='linear512' else streams[:,k,c,a,0,1]
                    g=fixed[:,k,c,3,1] if mode=='linear512' else exact[:,k,c,1]
                    tag=dict(kind='fixed',condition=condition,neural=mode,reference=ref,cutoff=cutoff,horizon=2000)
                    add(dict(**tag,metric='A'),o[:,0]-g[:,0]);add(dict(**tag,metric='D'),.9*o[:,1]-g[:,1])
    if source is not None:
        for draw in range(32):
            for mode in ['linear256','exact256']:
                for a,ref in enumerate(['original','recent_selected']):
                    for c,cutoff in enumerate([200,1000]):
                        o=source[draw,:,c,a,1]
                        g=streams[:,0,c,3,0,1] if mode=='linear256' else exact[:,0,c,1]
                        tag=dict(kind='source',draw=draw,condition='primary',neural=mode,reference=ref,cutoff=cutoff,horizon=2000)
                        add(dict(**tag,metric='A'),o[:,0]-g[:,0]);add(dict(**tag,metric='D'),.9*o[:,1]-g[:,1])
    for k,condition in enumerate(conditions):
        for mode in ['linear512','exact256']:
            for w,horizon in enumerate([500,2000]):
                o=fixed[:,k,:,1,w] if mode=='linear512' else streams[:,k,:,1,0,w]
                g=fixed[:,k,:,3,w] if mode=='linear512' else exact[:,k,:,w]
                for m,name in [(0,'A_interaction'),(1,'raw_score_interaction')]:
                    add(dict(kind='interaction',condition=condition,neural=mode,reference='recent_selected',horizon=horizon,metric=name),
                        (o[:,0,m]-g[:,0,m])-(o[:,1,m]-g[:,1,m]))
    x=np.stack(vectors,axis=1)
    primary=[i for i,label in enumerate(labels) if label['kind']=='fixed' and label['condition']=='primary'
             and label['neural']=='linear512' and label['reference']=='recent_selected']
    assert len(primary)==4 and x.shape==(64,632 if source is not None else 120)
    return labels,x,primary


def collect_highlights(labels,x,primary,intervals):
    highlights=[]
    for i,label in enumerate(labels):
        metric=label['metric']
        if metric not in ['A','D']: continue
        margin=.02 if metric=='A' else 0.
        highlights.append(dict(index=i,**label,point=float(x[:,i].mean()),margin=margin,
                                primary_lower=intervals['primary']['lower'][i] if i in primary else None,
                                primary_upper=intervals['primary']['upper'][i] if i in primary else None,
                                joint_lower=intervals['joint']['lower'][i],joint_upper=intervals['joint']['upper'][i],
                                joint_excludes=bool(intervals['joint']['upper'][i]<margin),
                                joint_establishes=bool(intervals['joint']['lower'][i]>margin)))
    return highlights


def main():
    mode=sys.argv[1] if len(sys.argv)>1 else 'final'
    meter=Accounting('early fixed-family adversarial analysis' if mode=='fixed' else 'final source/cohort/payoff assessment ('+mode+')')
    cache=meter.arrays(HERE/'FIXED_CACHE.npz')
    fixed,streams,exact=cache['fixed'],cache['streams'],cache['exact_gru']
    source=None;records=None;source_mc=None
    if mode in ['source','final']:
        execution=meter.json(MAIN/'MAIN_EXECUTION.json')
        assert execution['status']=='complete', 'author source execution still active/incomplete'
        records=meter.json(MAIN/'MAIN_SOURCE_DRAWS.json')['draws']
        assert [d['draw'] for d in records]==list(range(32))
        # Final RESULT must have superseded its preparatory Stage1 text.
        if mode=='final':
            author_result=meter.read(MAIN/'RESULT.md').decode()
            assert not author_result.startswith('# Stage1 result'), 'final author RESULT not yet available'
        source=np.empty((32,64,2,2,2,8))
        source_mc=np.empty((32,64,2,2,2,2))
        cached_source=(HERE/'SOURCE_SCORE_CACHE.npz').exists()
        if cached_source:
            cached=meter.arrays(HERE/'SOURCE_SCORE_CACHE.npz')
            source=cached['source'];source_mc=cached['source_halves']
        for draw in ([] if cached_source else range(32)):
            independent_cache=HERE/f'source_independent/draw_{draw:02d}.npz'
            if independent_cache.exists():
                completed=meter.arrays(independent_cache)
                assert np.array_equal(completed['subjects'],cache['subjects'])
                source[draw]=completed['metrics'];source_mc[draw]=completed['halves']
                continue
            data=meter.arrays(MAIN/f'source_chunks/draw_{draw:02d}.npz',keys=['samples','subjects','names','cutoffs','windows'])
            assert np.array_equal(data['subjects'],cache['subjects'])
            for i in range(64):
                for c in range(2):
                    for actor in range(2):
                        for w,horizon in enumerate([500,2000]):
                            s=data['samples'][i,c,actor,:,w]
                            source[draw,i,c,actor,w]=score(s,cache['observed'][i,w],horizon)
                        for half in range(2):
                            s=data['samples'][i,c,actor,half*128:(half+1)*128,1]
                            source_mc[draw,i,c,actor,half]=score(s,cache['observed'][i,1],2000)[:2]
        assert np.isfinite(source).all()
    labels,x,primary=assemble(fixed,streams,exact,source)
    intervals=bands(x,cache['bootstrap_weights'],selected=primary)
    alternate=bands(x,bootstrap_weights(20261105078,stratified=False),stratified=False,selected=primary)
    highlights=collect_highlights(labels,x,primary,intervals)
    output=dict(labels=labels,contributions_point=x.mean(0),primary_indices=primary,bands=intervals,
                alternate=alternate,highlights=highlights,cohort_site=cohorts_and_sites(x[:,primary],cache['labs']),
                interpretation='All animals and all frozen conditions retained; failed source stresses are separate from original-prescription primary. Frozen empirical ensembles and weights, consumed/postvalidation outcomes.')
    if mode in ['source','final']:
        output['selection_frequencies']=dict(Counter(str(r['chosen']) for r in records))
        source_points=[]
        for draw in range(32):
            for c,cutoff in enumerate([200,1000]):
                for a,ref in enumerate(['original','recent_selected']):
                    o=source[draw,:,c,a,1];g=streams[:,0,c,3,0,1]
                    source_points.append(dict(draw=draw,chosen=records[draw]['chosen'],cutoff=cutoff,reference=ref,
                         A=float(np.mean(o[:,0]-g[:,0])),D=float(np.mean(.9*o[:,1]-g[:,1])),
                         ordinary_mae=float(o[:,0].mean()),gru_mae=float(g[:,0].mean()),
                         relative_score_gain=float(1-g[:,1].mean()/o[:,1].mean())))
        output['source_points']=source_points
        output['source_mc_half_difference']=(source_mc[:,:,:,:,0]-source_mc[:,:,:,:,1]).mean(axis=1)
        np.savez_compressed(HERE/'SOURCE_SCORE_CACHE.npz',source=source,source_halves=source_mc,metrics=METRICS)
    if mode=='final':
        # Independent scores exist before reading the author's derived values.
        author=meter.arrays(MAIN/'MAIN_SCORES.npz')
        agreement={}
        for label,ours in [('fixed',fixed),('streams',streams),('exact_gru',exact),('source',source)]:
            agreement[label]=float(np.max(np.abs(ours-author[label])))
            assert agreement[label]<1e-12
        saved=meter.arrays(MAIN/'MAIN_CONTRASTS.npz')
        family=meter.json(MAIN/'MAIN_FAMILY.json')
        assert labels==family['columns'] and primary==family['primary_indices']
        agreement['contrast_vectors']=float(np.max(np.abs(x-saved['contributions'])))
        assert agreement['contrast_vectors']<1e-12
        output['author_agreement']=agreement
    np.savez_compressed(HERE/('FULL_CONTRASTS.npz' if mode!='fixed' else 'FIXED_CONTRASTS.npz'),
                        contributions=x,primary_indices=primary,subjects=cache['subjects'],labs=cache['labs'])
    save({'final':'FINAL_CHALLENGE.json','source':'SOURCE_FAMILY_PREAUTHOR.json','fixed':'FIXED_FAMILY.json'}[mode],output)
    save({'final':'FINAL_RESOURCES.json','source':'SOURCE_FAMILY_RESOURCES.json','fixed':'FIXED_FAMILY_RESOURCES.json'}[mode],meter.receipt())
    print(json.dumps(dict(mode=mode,columns=len(labels),primary_upper=intervals['primary']['upper'][primary].tolist(),
        joint_critical=intervals['joint']['critical'],agreement=output.get('author_agreement'),resources=meter.receipt()),default=lambda z:z.tolist()))


if __name__=='__main__':
    cpu=time.process_time()
    try: main()
    except BaseException as exc:
        save('FINAL_CHALLENGE_FAILURE_'+str(time.time_ns())+'.json',dict(error=repr(exc),process_cpu_seconds=time.process_time()-cpu))
        raise
