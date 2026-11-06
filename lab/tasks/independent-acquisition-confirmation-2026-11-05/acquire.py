"""Exact bounded802 anonymous public bodies; eight-field decode and chronology."""
from common import *
import urllib.request,urllib.error
sys.path.insert(0,str(ROOT/'sources/longitudinal_learning_feasibility_2026-10-28/tools'))
import duckdb
from chronology import join_aggregate

NUMERIC=['contrastLeft','contrastRight','choice','feedbackType','rewardVolume','probabilityLeft','intervals_0','intervals_1']

def append(name,v):
    with (HERE/name).open('a') as f:f.write(json.dumps(v,default=serial,sort_keys=True)+'\n')

def main():
    seal=get(HERE/'PRE_OUTCOME_SEAL.json')
    for path,h in seal['pins'].items():read(ROOT/path,h)
    assert get(HERE/'PREFLIGHT_CONTROLS.json')['all_passed']
    fp=get(HERE/'ACCESS_FOOTPRINT.json');objects=fp['objects']
    logpath=HERE/'PUBLIC_REQUESTS.jsonl'
    old=[json.loads(line) for line in read(logpath).splitlines()] if logpath.exists() else []
    ingress=sum(r['received_bytes'] for r in old);done={r['url']:r for r in old if r.get('success')}
    (HERE/'bodies').mkdir(exist_ok=True)
    for i,obj in enumerate(objects):
        path=HERE/'bodies'/obj['local']
        if obj['url'] in done:
            assert path.stat().st_size==obj['bytes'];continue
        assert obj['url'].startswith('https://ibl-brain-wide-map-public.s3.amazonaws.com/')
        assert ingress+obj['bytes']<=500000000
        rec=dict(utc=utc(),url=obj['url'],subject=obj['subject'],kind=obj['kind'],local=str(path.relative_to(HERE)),
            expected_etag=obj['etag'],expected_bytes=obj['bytes'],received_bytes=0,success=False,
            all_acquired_fields=obj['all_physically_acquired_fields'],rows=obj['rows'],method='GET',anonymous=True)
        body=bytearray();c=time.process_time();w=time.monotonic()
        try:
            req=urllib.request.Request(obj['url'],headers={'User-Agent':'independent-acquisition-confirmation/1.0','If-Match':'"'+obj['etag']+'"'})
            with urllib.request.urlopen(req,timeout=35) as resp:
                rec.update(http_status=resp.status,response_headers=dict(resp.headers),resolved_url=resp.url)
                assert resp.status==200 and resp.url==obj['url']
                assert resp.headers.get('ETag','').strip('"')==obj['etag']
                assert int(resp.headers['Content-Length'])==obj['bytes']
                remaining=obj['bytes']
                while remaining:
                    block=resp.read(min(262144,remaining))
                    if not block:raise RuntimeError('short exact body')
                    body.extend(block);remaining-=len(block)
                # Exact Content-Length is already pinned; do not read beyond it.
            assert len(body)==obj['bytes'];path.write_bytes(body)
            rec.update(success=True,sha256=hashlib.sha256(body).hexdigest())
        except BaseException as exc:
            rec['error']=repr(exc)
            if body:(HERE/'bodies'/(obj['local']+'.failed'+str(len(old)))).write_bytes(body)
            raise
        finally:
            rec.update(received_bytes=len(body),cpu_seconds=time.process_time()-c,wall_seconds=time.monotonic()-w)
            ingress+=len(body);old.append(rec);append('PUBLIC_REQUESTS.jsonl',rec)
        if (i+1)%20==0 or i+1==len(objects):
            print('ACQUIRED',i+1,'/',len(objects),'bytes',ingress,'CPU',round(time.process_time()-START_CPU,2),flush=True)
            receipt('ACQUISITION_LIVE','running',public_http_body_bytes=ingress,objects_completed=i+1)
    assert ingress<=500000000
    # Purely local decode after all exact objects have acquired-body receipts.
    con=duckdb.connect(':memory:');con.execute('SET threads=1');con.execute('SET preserve_insertion_order=true')
    by_subject={r['subject']:[z for z in objects if z['subject']==r['subject']] for r in fp['primary_units']}
    values=[];allintervals=[];ids=[];sid=[];checks=[];observed=[]
    import main_simulator
    from source_models import inherited as e
    for u in fp['primary_units']:
        s=u['subject'];arrs=[];identities=[];intervals=[]
        for obj in by_subject[s]:
            path=HERE/'bodies'/obj['local'];IO['logical_decoder_file_bytes']+=path.stat().st_size
            data=read(path)
            footer=int.from_bytes(data[-8:-4],'little');h=hashlib.sha256(data[-8-footer:-8]).hexdigest()
            assert data[:4]==data[-4:]==b'PAR1' and h==obj['footer_sha256'],(s,'footer',h,obj['footer_sha256'])
            fields=obj['decode_fields'];query=','.join('"'+k+'"' for k in fields)
            q=con.execute(f"SELECT {query},file_row_number FROM read_parquet('{path}',file_row_number=true) ORDER BY file_row_number").fetchnumpy()
            assert len(q[NUMERIC[0]])==obj['rows'] and np.array_equal(q['file_row_number'],np.arange(obj['rows']))
            def column(k):
                v=q[k]
                return np.asarray(v.filled(np.nan) if np.ma.isMaskedArray(v) else v,dtype=float)
            nums=np.column_stack([column(k) for k in NUMERIC]);IO['decoded_numeric_bytes']+=nums.nbytes
            IO['decoded_row_index_bytes']+=q['file_row_number'].nbytes
            if obj['kind']=='aggregate':
                ident=np.asarray(q['session'],str);IO['decoded_session_identity_utf8_bytes']+=sum(len(z.encode()) for z in ident)
                assert len(ident)==obj['rows']
                for row in obj['full_session_row_map']:
                    assert row['row_stop']-row['row_start']==row['rows']
                    assert np.all(ident[row['row_start']:row['row_stop']]==row['eid'])
                main=join_aggregate(nums,ident,u['training_sessions'])
                ix=np.concatenate([np.arange(z['aggregate_row_start'],z['aggregate_row_stop']) for z in u['training_sessions']])
                ints=nums[ix,6:8];session_ids=ident[ix]
                for z in u['training_sessions']:
                    iv=nums[z['aggregate_row_start']:z['aggregate_row_stop'],6:8]
                    assert np.isfinite(iv).all() and (iv[:,1]>=iv[:,0]).all() and (np.diff(iv[:,0])>=0).all(),(s,z['eid'],'intervals')
                intervals=[ints[:3000]];identities=[session_ids[:3000]];arrs=[main]
            else:
                iv=nums[:,6:8]
                assert np.isfinite(iv).all() and (iv[:,1]>=iv[:,0]).all() and (np.diff(iv[:,0])>=0).all(),(s,obj['eid'],'intervals')
                a=np.zeros((len(nums),7));a[:,:6]=nums[:,:6];a[0,6]=1
                arrs.append(a);intervals.append(iv);identities.append(np.repeat(obj['eid'],len(nums)))
            append('EXPOSURE.jsonl',dict(utc=utc(),event='whole_exact_object_selected_column_decode',subject=s,
                object=obj['url'],acquired_rows=obj['rows'],all_acquired_fields=obj['all_physically_acquired_fields'],
                decoded_fields=fields,decoded_rows=obj['rows'],auxiliary_included=True,
                only_main_first3000_used_for_forecast_score=True))
        a=np.concatenate(arrs)[:3000];iv=np.concatenate(intervals)[:3000];ss=np.concatenate(identities)[:3000]
        assert a.shape==(3000,7) and iv.shape==(3000,2) and len(ss)==3000
        assert np.isin(a[:,2],[-1,0,1]).all() and np.isin(a[:,3],[-1,0,1]).all(),(s,'codes')
        xx=np.nan_to_num(a[:,1])-np.nan_to_num(a[:,0]);nz=(xx!=0)&(a[:,2]!=0)
        assert np.all((a[nz,3]>0)==(a[nz,2]==-np.sign(xx[nz]))),(s,'nonzero sign feedback')
        assert np.all(a[a[:,2]==0,3]<=0),(s,'rewarded omission')
        assert np.isfinite(a[:,4:6]).all() and (a[:,4]>=0).all() and ((a[:,5]>=0)&(a[:,5]<=1)).all(),(s,'reward/probability')
        assert np.isin(np.abs(xx),[0,.0625,.125,.25,.5,1]).all(),(s,'contrast support')
        assert not ((np.nan_to_num(a[:,0])>0)&(np.nan_to_num(a[:,1])>0)).any(),(s,'two active contrasts')
        assert a[0,6]==1 and np.array_equal(a[1:,6].astype(bool),ss[1:]!=ss[:-1])
        values.append(a);allintervals.append(iv);sid.append(ss);ids.append(s);observed.append(e.observed(a))
        checks.append(dict(subject=s,rows=3000,first_eid=str(ss[0]),last_eid=str(ss[-1]),sessions=len(set(ss)),
            all_measurement_checks_pass=True,observed_zero_N_signs=int((e.observed(a)[1,[0,2]]==0).sum())))
        if len(ids)%16==0:print('DECODED',len(ids),'/192','CPU',round(time.process_time()-START_CPU,2),flush=True)
    assert len(ids)==192
    npz('CHRONOLOGICAL_MAIN.npz',values=np.stack(values),intervals=np.stack(allintervals),session_ids=np.stack(sid),subjects=ids,
        labs=[u['lab'] for u in fp['primary_units']],cohorts=[u['cohort'] for u in fp['primary_units']])
    npz('OBSERVED_COUNTS.npz',observed=np.stack(observed),subjects=ids,windows=[500,2000],
        columns=['N_left','K_left','N_right','K_right','omissions','choice_negative','literal_feedback_success'])
    save('CHRONOLOGY_CHECKS.json',dict(utc=utc(),all_passed=True,animals=checks,source_rows_decoded=fp['whole_decoded_rows'],
        main_rows=192*3000,auxiliary_numeric_rows=fp['whole_decoded_rows']-192*3000,
        no_eligibility_or_performance_filters=True,public_http_body_bytes=ingress))
    receipt('ACQUISITION','complete',public_http_body_bytes=ingress,objects=len(objects),all_jobs_terminal=True)
    print('ACQUISITION_AND_CHRONOLOGY_COMPLETE',utc(),'bytes',ingress,flush=True)

if __name__=='__main__':
    try:main()
    except BaseException as exc:
        n=len(list(HERE.glob('ACQUISITION_FAILURE_*.json')))
        receipt('ACQUISITION_FAILURE_'+str(n),'failed',error=repr(exc));raise
