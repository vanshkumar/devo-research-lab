"""Same-stage format/measurement audit only; no recoding, models, or forecasts."""
from common import *
sys.path.insert(0,str(ROOT/'sources/longitudinal_learning_feasibility_2026-10-28/tools'))
import duckdb
import struct
FIELDS=['contrastLeft','contrastRight','choice','feedbackType','rewardVolume','probabilityLeft','intervals_0','intervals_1']
WINDOWS={'prefix200':(0,200),'prefix1000':(0,1000),'early_generated201_1000':(200,1000),
    'short1001_1500':(1000,1500),'target1001_3000':(1000,3000),'all3000':(0,3000)}

def append(f,x):
    f.write(json.dumps(x,allow_nan=False,default=serial)+'\n')

def unpack(con,obj):
    p=HERE/'bodies'/obj['local'];assert p.stat().st_size==obj['bytes']
    # Footer hash only, without rereading the whole body in Python.
    with p.open('rb') as f:
        head=f.read(4);f.seek(-8,2);tail=f.read(8);size,magic=struct.unpack('<I4s',tail)
        assert head==magic==b'PAR1' and 0<size<1000000
        f.seek(-8-size,2);foot=f.read(size)
    IO['explicit_footer_bytes']+=len(head)+len(tail)+len(foot)
    assert hashlib.sha256(foot).hexdigest()==obj['footer_sha256'],(obj['subject'],obj['url'],'footer pin')
    cols=','.join('"'+k+'"' for k in obj['decode_fields']);IO['logical_decoder_file_bytes']+=obj['bytes']
    q=con.execute(f"SELECT {cols},file_row_number FROM read_parquet('{p}',file_row_number=true) ORDER BY file_row_number").fetchnumpy()
    rownum=q['file_row_number'];IO['decoded_physical_row_index_bytes']+=rownum.nbytes
    assert np.array_equal(rownum,np.arange(obj['rows']))
    nums=np.column_stack([np.asarray(q[k].astype(float).filled(np.nan) if np.ma.isMaskedArray(q[k]) else q[k],float) for k in FIELDS])
    assert nums.shape==(obj['rows'],8);IO['decoded_numeric_bytes']+=nums.nbytes
    if obj['kind']=='aggregate':
        sid=np.asarray(q['session'],str);IO['decoded_session_identity_utf8_bytes']+=sum(len(s.encode()) for s in sid)
        for z in obj['full_session_row_map']:
            assert z['row_stop']-z['row_start']==z['rows'] and (sid[z['row_start']:z['row_stop']]==z['eid']).all(),(obj['subject'],z['eid'],'physical identity blocks')
    else:sid=None
    return nums,sid

def diagnostics(a):
    l,r,c,f,rw,pl,t0,t1=a.T
    lc=np.isfinite(l)&(l!=0);rc=np.isfinite(r)&(r!=0);single=lc^rc
    cl=np.where(np.isnan(l),0,l);cr=np.where(np.isnan(r),0,r);literal=cr-cl
    valid_choice=np.isin(c,[-1,0,1]);valid_fdb=np.isin(f,[-1,0,1]);respond=np.isin(c,[-1,1]);available=respond&valid_fdb
    side=np.where(lc,-1,1) # meaningful only for single active nonzero field; data unchanged
    reward=f>0;ideal_col=c==-side;ideal_literal=c==-np.sign(literal)
    literal_mismatch=available&(literal!=0)&(ideal_literal!=reward)
    geometry_mismatch=available&single&(ideal_col!=reward)
    negative=(cl<0)|(cr<0);unit_col=np.where(single&(np.maximum(np.abs(cl),np.abs(cr))==1),side,0)
    unit_literal=np.where(np.abs(literal)==1,np.sign(literal),0)
    # Contrast assignment disagreements are counts, not a recoded target or score.
    return dict(negative_contrast_field=negative,negative_left=cl<0,negative_right=cr<0,
        both_nonzero_fields=lc&rc,both_fields_missing=np.isnan(l)&np.isnan(r),contrast_infinite=np.isinf(l)|np.isinf(r),
        literal_unsupported_level=~np.isin(np.abs(literal),[0,.0625,.125,.25,.5,1]),
        column_magnitude_unsupported=single&~np.isin(np.maximum(np.abs(cl),np.abs(cr)),[.0625,.125,.25,.5,1]),
        literal_feedback_mismatch=literal_mismatch,
        literal_mismatch_explained_by_column_polarity=literal_mismatch&single&~geometry_mismatch,
        physical_column_feedback_mismatch=geometry_mismatch,
        physical_column_feedback_mismatch_with_positive_nonzero_fields=geometry_mismatch&~negative,
        physical_column_incorrect_positive_feedback=geometry_mismatch&reward,
        physical_column_correct_nonpositive_feedback=geometry_mismatch&~reward,
        unit_contrast_side_assignment_disagrees=unit_col!=unit_literal,
        invalid_choice_code=~valid_choice,invalid_feedback_code=~valid_fdb,
        omission_positive_feedback=(c==0)&reward,positive_feedback_zero_reward=reward&(rw==0),
        nonpositive_feedback_positive_reward=(f<=0)&(rw>0),
        negative_or_infinite_reward=(rw<0)|np.isinf(rw),missing_reward=np.isnan(rw),
        invalid_probability_left=~np.isfinite(pl)|(pl<0)|(pl>1),
        invalid_within_row_interval=~np.isfinite(t0)|~np.isfinite(t1)|(t1<t0))

def main():
    fp=get(HERE/'ACCESS_FOOTPRINT.json');assert len(fp['primary_units'])==192 and len(fp['objects'])==802
    before=get(HERE/'RESOURCE_CHECKPOINT.json')['conservatively_counted_booked_read_decode_including_http_bytes']
    assert not (HERE/'DIAGNOSIS_COMPLETE.json').exists()
    con=duckdb.connect(':memory:');con.execute('SET threads=1');con.execute('SET preserve_insertion_order=true')
    units=[];cache=[];sessions=[];indices=[];allflags=Counter();objcount=0
    session_anomalies=[];nonchronological_aggregate=0
    with (HERE/'DIAGNOSIS_EXPOSURE.jsonl').open('x') as exposure,(HERE/'DIAGNOSTIC_ANOMALIES.jsonl').open('x') as anomalies:
        for ui,u in enumerate(fp['primary_units']):
            s=u['subject'];objs=[r for r in fp['objects'] if r['subject']==s];seq=u['training_sessions']
            by_session={};aggregate=None
            for o in objs:
                v,ids=unpack(con,o);objcount+=1
                append(exposure,dict(utc=utc(),subject=s,url=o['url'],kind=o['kind'],rows=o['rows'],decoded_fields=o['decode_fields'],
                    whole_auxiliary_rows_decoded=True,previous_whole_bodies_already_acquired=True,new_http_bytes=0,
                    diagnostic_only=True,verified_original_footer_sha256=o['footer_sha256']))
                if o['kind']=='aggregate':aggregate=v
                else:by_session[o['eid']]=v
            if aggregate is not None:
                offsets=[z['aggregate_row_start'] for z in seq];nonchronological_aggregate+=offsets!=sorted(offsets)
            rows=[];rowids=[];physical=[];dates=[];start_flags=[];order_violations=0
            for z in seq:
                lo=z.get('aggregate_row_start',0);hi=z.get('aggregate_row_stop',z['rows']);assert hi-lo==z['rows']
                v=aggregate[lo:hi] if aggregate is not None else by_session[z['eid']]
                assert len(v)==z['rows'] and len(v)>0
                inv=int(np.sum(np.diff(v[:,6])<0));invalid=int(np.sum(~np.isfinite(v[:,6])|~np.isfinite(v[:,7])|(v[:,7]<v[:,6])))
                order_violations+=inv
                if inv or invalid:session_anomalies.append(dict(subject=s,eid=z['eid'],date=z['date'],protocol=z['protocol'],
                    descending_interval_starts=inv,invalid_intervals=invalid,rows_in_complete_session=len(v),physical_range=[lo,hi]))
                rows.append(v);rowids.extend([z['eid']]*len(v));physical.extend(range(lo,hi));dates.extend([z['date']]*len(v));start_flags.extend([1]+[0]*(len(v)-1))
            a=np.concatenate(rows)[:3000];rowids=rowids[:3000];physical=physical[:3000];start_flags=start_flags[:3000]
            assert a.shape==(3000,8) and len(rowids)==3000
            assert np.array_equal(np.asarray(start_flags[1:],bool),np.asarray(rowids[1:])!=np.asarray(rowids[:-1]))
            flags=diagnostics(a);summ={key:{k:int(v[lo:hi].sum()) for k,v in flags.items()} for key,(lo,hi) in WINDOWS.items()}
            allflags.update(summ['all3000']);byid={z['eid']:z for z in seq}
            anybad=np.any(np.stack(list(flags.values())),axis=0)
            for i in np.flatnonzero(anybad):
                eid=rowids[i];z=byid[eid]
                append(anomalies,dict(subject=s,lab=u['lab'],cohort=u['cohort'],eid=eid,date=dates[i],protocol=z['protocol'],
                    opportunity=int(i+1),physical_file_row=physical[i],within_session_row=int(i-z['start']),
                    flags=[k for k,v in flags.items() if v[i]],values={k:(float(a[i,j]) if np.isfinite(a[i,j]) else None) for j,k in enumerate(FIELDS)}))
            units.append(dict(subject=s,lab=u['lab'],cohort=u['cohort'],opportunities=3000,windows=summ,
                interval_start_order_violations=order_violations,first_eid=rowids[0],last_eid=rowids[-1],
                nonchronological_physical_session_order=bool(aggregate is not None and offsets!=sorted(offsets))))
            # Save original values and literal session mapping only, to avoid rereading whole objects.
            cache.append(np.c_[a,np.asarray(start_flags)]);sessions.append(rowids);indices.append(physical)
            if (ui+1)%24==0:print('DIAGNOSED',ui+1,'/192','objects',objcount,'read',sum(IO.values()),flush=True)
            if before+sum(IO.values())>2500000000:raise RuntimeError('diagnosis read safety checkpoint; preserve residual initial allocation')
            if time.time()-get(HERE/'GOAL_START.json')['goalReadback']['goal']['createdAt']>20700:raise RuntimeError('initial stage elapsed safety stop')
    assert objcount==802 and len(units)==192
    npz('DIAGNOSTIC_LITERAL_CHRONOLOGY.npz',values=np.stack(cache),fields=FIELDS+['session_start'],
        session_ids=np.array(sessions),physical_file_rows=np.array(indices),subjects=[u['subject'] for u in units],
        purpose='Literal diagnostic only; original values unchanged; no compatibility release for forecasts.')
    bywindow={}
    for w in WINDOWS:
        bywindow[w]={k:dict(rows=sum(u['windows'][w][k] for u in units),animals=sum(u['windows'][w][k]>0 for u in units)) for k in allflags}
    result=dict(utc=utc(),animals=192,exact_objects_footer_checked=802,whole_decoded_rows=fp['whole_decoded_rows'],
        main_rows=192*3000,nonchronological_aggregate_subjects=nonchronological_aggregate,
        by_window=bywindow,session_interval_anomalies=session_anomalies,units=units,
        literal_data_unchanged=True,no_forecast_or_score_executed=True,new_public_http_bytes=0,
        scope='Deterministic measurement/compatibility audit only; physical-column consistency does not authenticate extractor or deployed feedback law.')
    save('DIAGNOSIS_COMPLETE.json',result);receipt('DIAGNOSIS','complete',all_jobs_terminal=True,public_http_body_bytes=0)
    print(json.dumps({k:v for k,v in result.items() if k not in ['units','session_interval_anomalies']},default=serial),flush=True)

if __name__=='__main__':
    try:main()
    except BaseException as exc:receipt('DIAGNOSIS_FAILURE','failed',error=repr(exc));raise
