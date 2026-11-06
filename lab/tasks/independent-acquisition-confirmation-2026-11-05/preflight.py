"""Source/synthetic fidelity and exact metadata footprint, before evaluation access."""
from common import *
from scipy.stats import t as student
from scipy.spatial.distance import cdist

def main():
    co=get(SOURCE/'QUALIFIED_COHORT.json');agg=get(SOURCE/'AGGREGATE_CHRONOLOGY.json')
    per=get(SOURCE/'FOOTER_QUALIFICATION.json');ex=get(SOURCE/'ORIGINAL_EXCLUSIONS.json');old=get(SOURCE/'ORIGINAL_SESSION_IDS.json')
    primary=[r for r in co['subjects'] if r['role']=='candidate_primary_evaluation']
    norm=lambda s:''.join(x for x in s.lower() if x.isalnum())
    oldkeys=set(ex['exclusion_keys']);oldids={r['eid'] for r in old['sessions'] if norm(r['subject']) in oldkeys}
    assert len(primary)==192 and len(oldids)==6222 and len(ex['subjects'])==154
    ar={r['subject']:r for r in agg['subjects']};pr={r['subject']:r for r in per['subjects']}
    objects=[];seen={};fullseen={};units=[]
    for r in primary:
        s=r['subject'];assert norm(s) not in oldkeys and s not in ('NYU-42','NYU-28')
        sessions=r['training_sessions'];assert sessions[0]['start']==0
        assert sessions==sorted(sessions,key=lambda z:(z['date'],z['number'],z['eid']))
        assert all(a['stop']==b['start'] for a,b in zip(sessions[:-1],sessions[1:])) and sessions[-1]['stop']>=3000
        for z in sessions:
            assert z['eid'] not in oldids and z['eid'] not in seen;seen[z['eid']]=s
        if r['cohort']=='public_subject_aggregate':
            a=ar[s];z=a['trial_metadata_source']
            assert z['rows']==r['full_trial_object_rows'] and z['size']==r['full_trial_object_bytes']
            for row in a['all_trial_identity_counts']:
                assert row['eid'] not in oldids and row['eid'] not in fullseen;fullseen[row['eid']]=s
            objects.append(dict(subject=s,kind='aggregate',url=z['url'],etag=z['etag'].strip('"'),bytes=z['size'],
                rows=z['rows'],all_physically_acquired_fields=[q[0] for q in z['columns'][1:]],
                decode_fields=['contrastLeft','contrastRight','choice','feedbackType','rewardVolume','probabilityLeft','intervals_0','intervals_1','session'],
                full_session_row_map=a['all_trial_identity_counts'],session_metadata_url=r['metadata_url'],
                footer_sha256=z['footer_sha256'],key=z['key'],local=Path(z['key']).name))
        else:
            probes={z['eid']:z for z in pr[s]['probes']}
            for z in sessions:
                p=probes[z['eid']];assert p['rows']==z['rows'] and p['source_url']==z['source_url']
                objects.append(dict(subject=s,kind='session',eid=z['eid'],url=z['source_url'],etag=p['etag'].strip('"'),
                    bytes=p['file_size'],rows=p['rows'],all_physically_acquired_fields=[q[0] for q in p['columns'][1:]],
                    decode_fields=['contrastLeft','contrastRight','choice','feedbackType','rewardVolume','probabilityLeft','intervals_0','intervals_1'],
                    footer_sha256=p['footer_sha256'],local=z['dataset_id']+'.pqt'))
        units.append(r)
    assert len(seen)==1537 and len(fullseen)==6813
    assert len({z['url'] for z in objects})==len(objects)
    assert sum(z['bytes'] for z in objects)==458383178
    assert sum(z['rows'] for z in objects)*48==237281280
    save('ACCESS_FOOTPRINT.json',dict(utc=utc(),primary_units=units,objects=objects,
        primary_animals=192,primary_horizon_sessions=len(seen),whole_aggregate_sessions=len(fullseen),
        consumed_protected_universe_animals=154,consumed_protected_session_ids=6222,
        expected_whole_http_bytes=sum(z['bytes'] for z in objects),http_cumulative_cap=500000000,
        whole_decoded_rows=sum(z['rows'] for z in objects),whole_eight_numeric_decode_bytes=sum(z['rows'] for z in objects)*64,
        auxiliary='All whole-object bytes/fields acquired, all selected eight numeric columns for complete histories decoded. Later training/biased/ephys and boundary rows are exposed auxiliary, not future untouched studies.',
        residual_identity_uncertainty='No animalUUID; undocumented biological aliases not universally excluded.',pins=PINS.copy()))
    ms,e,model,canonical,recent=load_prescriptions()
    selection=get(OLD/'artifacts/rnn/RNN_SELECTION.json');audit=get(OLD/'artifacts/rnn/FITTED_SOURCE_RECURRENCE_AUDIT.json')
    assert selection['best']['epoch']==975 and selection['sha256']==audit['sha256']==PINS[str((OLD/'artifacts/rnn/rnnglm32_nested_best.npz').relative_to(ROOT))]
    original=arrays(OLD/'artifacts/baselines/nested_growth_bank.npz','036f3cfedd56e915b051fb29a80a2622cf5a747366ea31aa46b9249a922eea01')
    assert all(np.array_equal(v,canonical[1000][k]) for k,v in original.items())
    source=get(SOURCE/'SOURCE_MEASUREMENT_PROBE.json');assert source['subject']=='NYU-42' and source['all_passed']
    q=arrays(SOURCE/'SOURCE_ONLY_ROWS.npz');fields=list(q['fields']);v=q['values'];assert v.shape==(273,8)
    f={n:v[:,fields.index(n)] for n in fields}
    x=np.nan_to_num(f['contrastRight'])-np.nan_to_num(f['contrastLeft']);nz=(x!=0)&(f['choice']!=0)
    assert np.isin(f['choice'],[-1,0,1]).all() and np.isin(f['feedbackType'],[-1,0,1]).all()
    assert np.all((f['feedbackType'][nz]>0)==(f['choice'][nz]==-np.sign(x[nz])))
    assert (np.diff(f['intervals_0'])>=0).all() and (f['intervals_1']>=f['intervals_0']).all()
    assert np.isfinite(f['rewardVolume']).all() and (f['rewardVolume']>=0).all()
    assert np.isfinite(f['probabilityLeft']).all() and ((f['probabilityLeft']>=0)&(f['probabilityLeft']<=1)).all()
    # Construct1000 source-derived/synthetic rows. No evaluation animal is touched.
    a=np.zeros((3000,7));part=np.column_stack([f[k] for k in ['contrastLeft','contrastRight','choice','feedbackType','rewardVolume','probabilityLeft']])
    a[:,:6]=part[np.arange(3000)%len(part)];a[:,6]=(np.arange(3000)%273==0)
    # Actual nonchronological physical-block join, using the same helper as acquisition.
    from chronology import join_aggregate
    order=[2,0,3,1];physical=np.concatenate([a[j*750:(j+1)*750,:6] for j in order])
    labels=np.concatenate([np.repeat('session'+str(j),750) for j in order]);ss=[]
    for j in range(4):
        start=order.index(j)*750;ss.append(dict(eid='session'+str(j),rows=750,start=j*750,stop=(j+1)*750,aggregate_row_start=start,aggregate_row_stop=start+750))
    result=join_aggregate(physical,labels,ss)
    expected=a.copy();expected[:,6]=0;expected[::750,6]=1
    assert np.array_equal(result,expected,equal_nan=True) and not np.array_equal(physical,a[:,:6],equal_nan=True)
    replay=[];poison=[]
    for cutoff in (200,1000):
        clean=ms.causal_view(a,cutoff);altered=a.copy()
        for j in range(6):altered[cutoff:,j]=np.arange(3000-cutoff)*((-1)**j)+100000*(j+1)
        dirty=ms.causal_view(altered,cutoff);assert np.array_equal(clean,dirty,equal_nan=True)
        for name,half in [('growth',None),('recent_growth',100),('recent_growth',250),('gru',None)]:
            bank=recent[half][cutoff] if half else None
            out,_=ms.simulate('NYU-42-source-control',clean,cutoff,name,model,canonical[cutoff],bank,half,n=16)
            inherited,_=e.simulate('NYU-42-source-control',a,cutoff,name,model,canonical[cutoff],bank,half,n=16)
            changed,_=ms.simulate('NYU-42-source-control',dirty,cutoff,name,model,canonical[cutoff],bank,half,n=16)
            assert np.array_equal(out,inherited) and np.array_equal(out,changed)
            replay.append(dict(cutoff=cutoff,actor=name,half=half,max_count_difference=0))
            poison.append(dict(cutoff=cutoff,actor=name,half=half,all_six_future_fields_poisoned=True,counts_identical=True))
    # Independently check frozen vector recurrence against sequential original implementation.
    from pilot import subject
    state=dict(w=np.zeros((1,3)),h=np.zeros((1,model.hidden)));qs=[]
    for t in range(200):
        xx=x[t];qs.append(model.probs(state,np.array([xx]))[0]);model.update(state,np.array([xx]),np.array([f['choice'][t]]),np.array([f['feedbackType'][t]]),session_start=t==0)
    qp,_,end=model.sequence(subject(a[:200]),np.zeros(3))
    err=max(np.max(abs(qp-qs)),np.max(abs(end['w']-state['w'][0])),np.max(abs(end['h']-state['h'][0])))
    assert err<1e-10
    draws=get(PREV/'MAIN_SOURCE_DRAWS.json')['draws'];assert len(draws)==32
    selected=[draws[j] for j in [0,14]];assert all(r['chosen']=='100' for r in selected)
    # Preserve exact chosen donor orders including duplicates; no source refits/reselection.
    for r in selected:
        for cutoff in (200,1000):
            npz(f'banks/source{r["draw"]}_canonical_{cutoff}.npz',**reindex_bank(canonical[cutoff],r['donors']))
            npz(f'banks/source{r["draw"]}_recent100_{cutoff}.npz',**reindex_bank(recent[100][cutoff],r['donors']))
    save('SOURCE_SENSITIVITY_PRESCRIPTIONS.json',dict(utc=utc(),draws=selected,
        unchanged_neural='Reuse literal primary GRU forecast including its original omission bank, matching the old source-sensitivity definition. Perturb ordinary donor/anchor laws only; no neural/source-family claim.',
        old_all32=get(ROOT/'lab/reviews/independent-cohort-investment-2026-11-05/SOURCE_CONTRARY.json')))
    from main_scores import mixed_score
    rng=np.random.default_rng(20261105115);scorechecks=[]
    for missing in (False,True):
        n=rng.integers(10,100,50);k=np.array([rng.integers(0,j+1) for j in n]);n[:13]=0;k[:13]=0
        ratios=np.divide(k,n,out=np.zeros(50),where=n>0);z=np.c_[n==0,ratios,np.where(n>0,1-ratios,0)]
        on,ok=(0,0) if missing else (30,19);target=np.array([1,0,0]) if missing else np.array([0,ok/on,1-ok/on])
        literal=(np.linalg.norm(z-target,axis=1).mean()-.5*cdist(z,z).mean())/np.sqrt(2)
        fast,_=mixed_score(n,k,on,ok);assert abs(literal-fast)<1e-12;scorechecks.append(float(abs(literal-fast)))
    crit=float(student.ppf(1-.05/(2*3),191));assert abs(crit-2.41525)<.00001
    # Finite-known-normal checks of the actual three-band decision, not biological coverage.
    control=[]
    for label,mu in [('all_boundary',[0,0,0]),('one_boundary',[0,.04,.04]),('negative',[-.03]*3),('positive',[.03]*3)]:
        means=[];ses=[]
        for batch in range(10):
            common=rng.normal(size=(500,192,1));res=.06*(np.sqrt(.8)*common+np.sqrt(.2)*rng.normal(size=(500,192,3)))+mu
            means.append(res.mean(1));ses.append(res.std(1,ddof=1)/np.sqrt(192))
        m=np.concatenate(means);se=np.concatenate(ses);lo=m-crit*se;hi=m+crit*se
        control.append(dict(label=label,cohorts=5000,any_noncoverage=float(np.mean(np.any((lo>mu)|(hi<mu),axis=1))),
            all_positive=float(np.mean(np.all(lo>0,axis=1))),selected_negative=float(np.mean(hi[:,1]<0))))
    assert control[0]['any_noncoverage']<.07 and control[1]['all_positive']<.04
    save('PREFLIGHT_CONTROLS.json',dict(utc=utc(),all_passed=True,no_evaluation_payload_access=True,
        exact_192_footprint_verified=True,nonchronological_join_reconstructs=True,naive_file_head_fails=True,
        source_semantics_rows=273,reference_replays=replay,poison_controls=poison,
        frozen_recurrence_max_error=float(err),historical_original_source_audit=audit,
        exact_original1000bank=True,checkpoint_epoch=975,missing_score_checks=scorechecks,
        inference_controls=control,primary_critical=crit,pins=PINS.copy()))
    print(json.dumps(dict(all_passed=True,objects=len(objects),http_bytes=sum(z['bytes'] for z in objects),
        numeric_rows=sum(z['rows'] for z in objects),recurrence_error=err,critical=crit,controls=control),default=serial),flush=True)
    receipt('PREFLIGHT')
if __name__=='__main__':
    try:main()
    except BaseException as exc:receipt('PREFLIGHT','failed',error=repr(exc));raise
