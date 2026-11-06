"""Official subject aggregate object/chronology qualification; no trial values."""
from collections import Counter,defaultdict
from datetime import datetime,timezone
import argparse,hashlib,json,re,resource,struct,sys,time
from pathlib import Path
import xml.etree.ElementTree as ET

HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[2]
sys.path.insert(0,str(ROOT/'sources/longitudinal_learning_feasibility_2026-10-28/tools'))
import duckdb
from source_access import request
CACHE={};IO=Counter()
BATCH_PUBLIC_INGRESS=0
MAX_BATCH_PUBLIC_INGRESS=25_000_000


def utc():return datetime.now(timezone.utc).isoformat()
def norm(s):return re.sub('[^a-z0-9]','',s.lower())
def get(n):return json.loads((HERE/n).read_bytes())
def save(n,x):(HERE/n).write_text(json.dumps(x,indent=2,default=str)+'\n')


def cached_request(url,name,limit,byte_range=None,purpose='declared aggregate metadata'):
    global BATCH_PUBLIC_INGRESS
    if not CACHE:
        b=(HERE/'PUBLIC_REQUESTS.jsonl').read_bytes();IO['request_log_read_bytes']+=len(b)
        for r in [json.loads(s) for s in b.splitlines()]:
            if r.get('status') in (200,206) and 'error' not in r and 'sha256' in r:
                CACHE[(r['url'],r.get('requested_range'))]=r
    rec=CACHE.get((url,byte_range))
    if rec and (HERE/rec['local']).is_file():
        b=(HERE/rec['local']).read_bytes();IO['cached_metadata_read_bytes']+=len(b)
        assert hashlib.sha256(b).hexdigest()==rec['sha256']
        assert rec['local']==name
        return rec
    # Network transfer and local read/decode are separate authorized dimensions.
    # Stop BEFORE a request whose full bounded response could cross25MB here;
    # source_access also enforces80MB cumulatively for the whole assignment.
    assert BATCH_PUBLIC_INGRESS+limit<=MAX_BATCH_PUBLIC_INGRESS, 'Public-transfer cap; no request sent'
    rec=request(url,name,limit,byte_range=byte_range,purpose=purpose,metadata_range_only=bool(byte_range),quiet=True)
    BATCH_PUBLIC_INGRESS+=rec['received_bytes']
    if rec.get('status') in (200,206) and 'error' not in rec:CACHE[(url,byte_range)]=rec
    return rec


def plan():
    b=(HERE/'S3_SUBJECT_AGGREGATE_OBJECTS_1.xml').read_bytes();root=ET.fromstring(b)
    ns={'s':'http://s3.amazonaws.com/doc/2006-03-01/'}
    assert root.findtext('s:IsTruncated',namespaces=ns)=='false'
    old=set(get('ORIGINAL_EXCLUSIONS.json')['exclusion_keys']);records=[]
    for c in root.findall('s:Contents',ns):
        key=c.findtext('s:Key',namespaces=ns);parts=key.split('/')
        lab,subject=parts[2:4]
        if norm(subject) in old:continue
        # Pin current unrevisioned tables; historical copies never become animals.
        if len(parts)!=5:continue
        kind='sessions' if '_ibl_subjectSessions.table.' in parts[-1] else 'trials' if '_ibl_subjectTrials.table.' in parts[-1] else None
        if not kind:continue  # Training-status table is outcome-derived and stays closed.
        records.append(dict(lab=lab,subject=subject,kind=kind,key=key,
             url='https://ibl-brain-wide-map-public.s3.amazonaws.com/'+key,
             size=int(c.findtext('s:Size',namespaces=ns)),etag=c.findtext('s:ETag',namespaces=ns),
             last_modified=c.findtext('s:LastModified',namespaces=ns)))
    assert len(records)==len({(r['lab'],r['subject'],r['kind']) for r in records})
    save('AGGREGATE_ACCESS_PLAN.json',dict(utc=utc(),source_listing_sha256=hashlib.sha256(b).hexdigest(),
        scope='Exact unprotected aggregate object IDs below; footer/schema first. No trial-body or training-status acquisition; only separately certified pure metadata session tables may be opened.',
        fields=['Parquet schema','row counts','session IDs','task protocol','dates/times','session numbers','n_trials if present'],
        records=records))
    print('declared',len(records),'objects',len({(r['lab'],r['subject']) for r in records}),'subjects')


def footer(a,con,io):
    name=Path(a['key']).stem
    x=cached_request(a['url'],name+'_tail8.bin',8,'bytes=-8','Declared unprotected aggregate trailer/schema; no trial values')
    assert x.get('status')==206 and 'error' not in x
    b=(HERE/(name+'_tail8.bin')).read_bytes();io['explicit_reads']+=len(b)
    length,magic=struct.unpack('<I4s',b);assert magic==b'PAR1' and 0<length<=1_000_000
    total=int(x['response_headers']['Content-Range'].split('/')[-1]);assert total==a['size']
    assert x['response_headers']['ETag']==a['etag']
    start=total-length-8
    y=cached_request(a['url'],name+'_footer.bin',length,f'bytes={start}-{total-9}','Declared unprotected aggregate footer; schema/row totals only')
    assert y.get('status')==206 and 'error' not in y and y['response_headers']['ETag']==a['etag']
    raw=(HERE/(name+'_footer.bin')).read_bytes();io['explicit_reads']+=len(raw);io['decoded_footer_metadata_bytes']+=len(raw)
    derived=HERE/(name+'_footer_only.pqt')
    with derived.open('wb') as f:f.write(b'PAR1');f.seek(start);f.write(raw);f.write(b)
    io['engine_logical_file_charge']+=total
    n,ng=con.execute(f"SELECT num_rows,num_row_groups FROM parquet_file_metadata('{derived}')").fetchone()
    schema=con.execute(f"SELECT name,type FROM parquet_schema('{derived}')").fetchall()
    return dict(**a,rows=n,row_groups=ng,columns=schema,footer_sha256=hashlib.sha256(raw).hexdigest(),statistics_queried=False,trial_values_acquired=False)


def chronology():
    cpu,wall=time.process_time(),time.monotonic();io=IO
    b=(HERE/'AGGREGATE_ACCESS_PLAN.json').read_bytes();io['explicit_reads']+=len(b)
    records=json.loads(b)['records'];groups=defaultdict(dict)
    for a in records:groups[(a['lab'],a['subject'])][a['kind']]=a
    exclusions=set(get('ORIGINAL_EXCLUSIONS.json')['exclusion_keys'])
    oldeids={r['eid'] for r in get('ORIGINAL_SESSION_IDS.json')['sessions'] if norm(r['subject']) in exclusions}
    c=duckdb.connect(':memory:');out=[]
    allowed={'schema','lab','subject','date','number','task_protocol','projects','id'}
    for (lab,subject),assets in sorted(groups.items()):
        # A conservative full logical-file charge covers footer and identity scans;
        # stop before the assignment's read envelope could be exceeded.
        upper=2*sum(x['size'] for x in assets.values())
        if sum(io.values())+upper>1_700_000_000:
            raise RuntimeError('Aggregate qualification read-charge frontier; retain partial checkpoint')
        s=footer(assets['sessions'],c,io)
        if not {x[0] for x in s['columns']}<=allowed:
            out.append(dict(subject=subject,lab=lab,status='session_table_not_pure_metadata',schema=s));continue
        name=Path(s['key']).stem+'_metadata.pqt'
        r=cached_request(s['url'],name,s['size'],purpose='Schema-certified pure subject/session chronology metadata; no outcomes')
        assert r.get('status')==200 and 'error' not in r and r['response_headers']['ETag']==s['etag']
        p=HERE/name;raw=p.read_bytes();io['explicit_reads']+=len(raw);assert len(raw)==s['size']
        assert hashlib.md5(raw).hexdigest()==s['etag'].strip('"')
        io['engine_logical_file_charge']+=s['size']
        sessions=c.execute(f"SELECT id,lab,subject,date,number,task_protocol,projects FROM read_parquet('{p}') ORDER BY date,number,id").fetchall()
        io['decoded_chronology_utf8_bytes']+=len(json.dumps(sessions,default=str).encode())
        assert len(sessions)==len({x[0] for x in sessions})
        if any(x[0] in oldeids or norm(x[2]) in exclusions for x in sessions):
            out.append(dict(subject=subject,lab=lab,status='known_animal_alias_from_session_metadata'));continue
        assert all(x[1]==lab and x[2]==subject for x in sessions)
        tr=footer(assets['trials'],c,io)
        fields={x[0] for x in tr['columns']}
        required={'session','choice','contrastLeft','contrastRight','feedbackType','probabilityLeft'}
        if not required<=fields:
            out.append(dict(subject=subject,lab=lab,status='trial_fields_missing',schema=tr));continue
        tp=HERE/(Path(tr['key']).stem+'_footer_only.pqt')
        chunks=c.execute(f"SELECT row_group_id,dictionary_page_offset,data_page_offset,total_compressed_size FROM parquet_metadata('{tp}') WHERE path_in_schema='session' ORDER BY row_group_id").fetchall()
        ranges=[]
        for rg,dictionary,data,size in chunks:
            start=min(x for x in (dictionary,data) if x is not None and x>=4)
            chunkname=Path(tr['key']).stem+f'_session_rg{rg}.bin'
            response=cached_request(tr['url'],chunkname,size,f'bytes={start}-{start+size-1}',
                  'Exact declared session-ID column chunk only; no response/stimulus/feedback/status column bytes')
            assert response.get('status')==206 and 'error' not in response and response['response_headers']['ETag']==tr['etag']
            raw=(HERE/chunkname).read_bytes();io['explicit_reads']+=len(raw);assert len(raw)==size
            with tp.open('r+b') as f:f.seek(start);f.write(raw)
            ranges.append(dict(row_group=rg,start=start,stop=start+size,bytes=size,sha256=hashlib.sha256(raw).hexdigest()))
        io['engine_logical_file_charge']+=tr['size']
        # Charge64bytes per decoded identity row, including string/offset overhead.
        io['decoded_identity_row_upper_bytes']+=64*tr['rows']
        counts=c.execute(f"SELECT session,count(*),min(file_row_number),max(file_row_number) FROM read_parquet('{tp}',file_row_number=true) GROUP BY session ORDER BY min(file_row_number)").fetchall()
        assert sum(x[1] for x in counts)==tr['rows']
        byid={str(x[0]):x for x in counts}
        registered={x[0] for x in sessions}
        if not set(byid)<=registered:
            status='aggregate_session_not_in_metadata'
        else:status='pending'
        training=[x for x in sessions if x[5].startswith('_iblrig_tasks_trainingChoiceWorld')]
        first=training[0] if training else None
        offset=0;used=[];missing=[];intervening=[]
        if status=='pending' and not first:status='no_indexed_training_sessions'
        if status=='pending':
            active=False
            for row in sessions:
                if row[0]==first[0]:active=True
                if not active:continue
                if offset>=3000:break
                if not row[5].startswith('_iblrig_tasks_trainingChoiceWorld'):
                    if row[0] in byid:intervening.append(row[0]);status='other_task_before3000';break
                    continue
                if row[0] not in byid:
                    missing.append(row[0]);status='missing_earliest_training_measurement';break
                _,n,lo,hi=byid[row[0]]
                if n!=hi-lo+1:status='noncontiguous_session_rows';break
                used.append(dict(eid=row[0],date=str(row[3]),number=row[4],protocol=row[5],rows=n,
                                  start=offset,stop=offset+n,aggregate_row_start=lo,aggregate_row_stop=hi+1))
                offset+=n
            if status=='pending':status='identity_qualified_3000' if offset>=3000 else 'short_indexed_training_history'
        result=dict(subject=subject,lab=lab,status=status,verified_training_opportunities=offset,
             first_indexed_training=dict(eid=first[0],date=str(first[3]),number=first[4],protocol=first[5]) if first else None,
             first_available_aggregate_session=counts[0] if counts else None,
             total_aggregate_rows=tr['rows'],aggregate_sessions=len(counts),registered_sessions=len(sessions),
             missing_before_target=missing,intervening_other_tasks=intervening,used_sessions=used,
             prior_public_protocols=dict(Counter(x[5] for x in sessions[:sessions.index(first)])) if first else {},
             session_metadata_source=s,trial_metadata_source=tr,identity_byte_ranges=ranges,
             all_trial_identity_counts=[dict(eid=str(x[0]),rows=x[1],row_start=x[2],row_stop=x[3]+1) for x in counts],
             no_behavioral_columns_acquired=True)
        out.append(result);print(subject,status,offset,flush=True)
        save('AGGREGATE_CHRONOLOGY.json',dict(utc=utc(),status='running',subjects=out,io=dict(io),
                    cpu_seconds=time.process_time()-cpu,process_wall_seconds=time.monotonic()-wall))
    summary=dict(utc=utc(),status='complete',subjects=out,counts_by_status=dict(Counter(r['status'] for r in out)),
        qualified_by_lab=dict(Counter(r['lab'] for r in out if r['status']=='identity_qualified_3000')),
        io=dict(io),new_batch_public_ingress_bytes=BATCH_PUBLIC_INGRESS,max_batch_public_ingress_bytes=MAX_BATCH_PUBLIC_INGRESS,
        cpu_seconds=time.process_time()-cpu,process_wall_seconds=time.monotonic()-wall,
        peak_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
    save('AGGREGATE_CHRONOLOGY.json',summary);print(json.dumps({k:v for k,v in summary.items() if k!='subjects'},indent=2))


def main(probe=None):
    cpu,wall=time.process_time(),time.monotonic();io=Counter()
    b=(HERE/'AGGREGATE_ACCESS_PLAN.json').read_bytes();io['explicit_reads']+=len(b)
    records=json.loads(b)['records'];c=duckdb.connect(':memory:');out=[]
    if probe:records=[r for r in records if r['subject']==probe]
    for a in records:
        out.append(footer(a,c,io))
    result=dict(utc=utc(),probe=probe,records=out,io=dict(io),cpu_seconds=time.process_time()-cpu,
                process_wall_seconds=time.monotonic()-wall,peak_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
    save('AGGREGATE_PROBE_SCHEMA.json' if probe else 'AGGREGATE_FOOTERS.json',result)
    print(json.dumps(result,indent=2))


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--plan',action='store_true');p.add_argument('--probe');p.add_argument('--chronology',action='store_true');a=p.parse_args()
    plan() if a.plan else chronology() if a.chronology else main(a.probe)
