#!/usr/bin/env python3
"""Separate original-byte mixed Parquet/NPY reader; acquisition is metadata-only.

--coverage downloads/verifies opaque bytes and inspects only NPY headers and
Parquet schema/footer row counts. All value-reading APIs require a prospective
freeze and log access before decoding. Prefix NPZs never contain future rows.
"""
from __future__ import annotations
import argparse, concurrent.futures, datetime as dt, hashlib, json, sys, time
from pathlib import Path
from urllib.request import Request, urlopen
import numpy as np
ROOT=Path(__file__).resolve().parents[3]
CAMPAIGN=Path(__file__).resolve().parents[1]
OUT=CAMPAIGN/'artifacts/coverage'
SOURCE=ROOT/'sources/longitudinal_learning_feasibility_2026-10-28'
FEAS=ROOT/'sources/prospective_acquisition_feasibility_2026-10-28'
sys.path.insert(0,str(SOURCE/'tools'))
CORE=['contrastLeft','contrastRight','choice','feedbackType','probabilityLeft','intervals']
FIELDS=['contrastLeft','contrastRight','choice','feedbackType','rewardVolume','probabilityLeft',
        'intervals_0','intervals_1','goCue_times','stimOn_times','firstMovement_times','response_times','feedback_times']

def db():
    import duckdb
    return duckdb.connect()
def sha(path,algorithm='sha256'):
    h=hashlib.new(algorithm)
    with open(path,'rb') as f:
        for b in iter(lambda:f.read(1<<20),b''):h.update(b)
    return h.hexdigest()
def dump(path,value):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(value,indent=2,default=str)+'\n')
def log(event):
    p=CAMPAIGN/'protocols/EXPOSURE.jsonl';p.parent.mkdir(exist_ok=True)
    with p.open('a') as f:f.write(json.dumps({'utc':dt.datetime.now(dt.timezone.utc).isoformat(),**event},sort_keys=True)+'\n')
def header(path):
    with open(path,'rb') as f:
        version=np.lib.format.read_magic(f)
        if version==(1,0):shape,fort,dtype=np.lib.format.read_array_header_1_0(f)
        elif version==(2,0):shape,fort,dtype=np.lib.format.read_array_header_2_0(f)
        else:raise ValueError('Unsupported NPY header version '+str(version))
        offset=f.tell()
    expected=offset+int(np.prod(shape))*dtype.itemsize
    if dtype.hasobject:raise ValueError('Object arrays not allowed '+str(path))
    if expected!=Path(path).stat().st_size:raise ValueError('NPY body byte count mismatch '+str(path))
    return dict(shape=list(shape),fortran_order=fort,dtype=dtype.str,header_bytes=offset,expected_bytes=expected)
def records():
    con=db();inventory=json.loads((FEAS/'excluded26_inventory.json').read_text())
    subjects=sorted(r['subject'] for r in inventory['summary'])
    expected={r[2]:(r[0],r[1],r[3],int(r[4]),r[5]) for r in inventory['rows']}
    inventory_dataset_ids={did for r in inventory['rows'] for did in r[8]}
    rows=con.execute(f"SELECT s.subject,s.lab,s.date,s.number,s.task_protocol,s.id,d.session_path,d.rel_path,d.id,d.file_size,d.hash,d.exists_aws,d.default_revision FROM read_parquet('{SOURCE/'standard_cache/sessions.pqt'}') s JOIN read_parquet('{SOURCE/'standard_cache/datasets.pqt'}') d ON s.id=d.eid WHERE s.task_protocol LIKE '%trainingChoiceWorld%' ORDER BY s.subject,s.date,s.number,d.rel_path,d.default_revision DESC,d.id").fetchall()
    keep=set(CORE+['repNum','feedback_times','goCue_times','response_times','stimOn_times','firstMovement_times','rewardVolume'])
    result=[];seen=set()
    for subject,lab,date,number,protocol,eid,session_path,rel,did,size,md5,aws,default in rows:
        if subject not in subjects:continue
        assert eid in expected and expected[eid]==(subject,lab,str(date),int(number),protocol)
        name=Path(rel).name
        field='table' if name=='_ibl_trials.table.pqt' else name.removeprefix('_ibl_trials.').removesuffix('.npy')
        if field!='table' and field not in keep:continue
        key=(eid,field)
        if key in seen:continue
        if did not in inventory_dataset_ids:raise ValueError('Dataset differs from prospective inventory '+did)
        seen.add(key);rp=Path(rel)
        remote=str(rp.with_name(rp.stem+'.'+did+rp.suffix))
        path=OUT/'raw'/subject/(str(date)+'_'+str(number).zfill(3)+'_'+eid+'_'+field+rp.suffix)
        result.append(dict(subject=subject,lab=lab,date=str(date),number=int(number),protocol=protocol,eid=eid,field=field,dataset_id=did,bytes=size,md5=md5,exists_aws=aws,default_revision=default,session_path=session_path,rel_path=rel,url='https://ibl-brain-wide-map-public.s3.amazonaws.com/data/'+session_path+'/'+remote,path=str(path.relative_to(ROOT))))
    # For table sessions only retain table and repNum: no silent competing arrays.
    table_sessions={r['eid'] for r in result if r['field']=='table'}
    result=[r for r in result if r['eid'] not in table_sessions or r['field'] in ['table','repNum']]
    assert {r['eid'] for r in result}==set(expected)
    return result

def acquire(r):
    p=ROOT/r['path']
    for attempt in range(3):
        try:
            if not (p.exists() and p.stat().st_size==r['bytes'] and sha(p,'md5')==r['md5']):
                p.parent.mkdir(parents=True,exist_ok=True);temp=p.with_suffix(p.suffix+'.partial')
                with urlopen(Request(r['url'],headers={'User-Agent':'research-lab-open-data/1.0'}),timeout=40) as response,open(temp,'wb') as f:
                    while True:
                        b=response.read(1<<18)
                        if not b:break
                        f.write(b)
                if temp.stat().st_size!=r['bytes'] or sha(temp,'md5')!=r['md5']:raise ValueError('Pinned cache size/MD5 mismatch')
                temp.replace(p)
            return {**r,'sha256':sha(p),'verified':True}
        except Exception as e:
            if attempt==2:return {**r,'verified':False,'error':repr(e)}
            time.sleep(1+attempt)

def coverage(workers=12):
    OUT.mkdir(parents=True,exist_ok=True)
    # Freeze inventory by reference; header/schema inspection has no trial values.
    rs=records();dump(OUT/'INDEX.json',rs)
    print('requested',len(rs),'opaque files',sum(r['bytes'] for r in rs),'bytes',flush=True)
    completed=[]
    with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as pool:
        for i,r in enumerate(pool.map(acquire,rs)):
            completed.append(r)
            if (i+1)%100==0:print('verified',i+1,'failures',sum(not q['verified'] for q in completed),flush=True)
    dump(OUT/'BYTE_MANIFEST.json',completed)
    failed=[r for r in completed if not r['verified']]
    if failed:raise RuntimeError('Opaque byte acquisition failures '+str(len(failed)))
    con=db();files=[]
    for r in completed:
        p=ROOT/r['path']
        if r['field']=='table':
            n=int(con.execute('SELECT num_rows FROM parquet_file_metadata(?)',[str(p)]).fetchone()[0])
            schema=con.execute('DESCRIBE SELECT * FROM read_parquet(?)',[str(p)]).fetchall()
            cols=[x[0] for x in schema]
            needed=['choice','contrastLeft','contrastRight','feedbackType','probabilityLeft','intervals_0','intervals_1']
            if not set(needed)<=set(cols):raise ValueError('Missing table core fields '+str(p))
            meta={'rows':n,'columns':cols,'schema':[list(x[:2]) for x in schema]}
        else:
            meta=header(p);n=meta['shape'][0]
            if r['field']=='intervals' and meta['shape']!=[n,2]:raise ValueError('Unexpected intervals shape '+str(p))
            if r['field']!='intervals' and meta['shape'] not in [[n],[n,1]]:raise ValueError('Unexpected scalar shape '+str(p))
            meta['rows']=n
        files.append({**r,**meta})
    dump(OUT/'FILE_METADATA.json',files)
    sessions=[]
    for eid in sorted({r['eid'] for r in files}):
        rr=[r for r in files if r['eid']==eid];one=rr[0];sizes={r['rows'] for r in rr}
        if len(sizes)!=1:raise ValueError('Core/aux row-length mismatch '+eid+' '+str(sizes))
        n=sizes.pop();by={r['field']:r for r in rr};is_table='table' in by
        if not is_table and not set(CORE)<=set(by):raise ValueError('Legacy missing core '+eid)
        sessions.append({**{k:one[k] for k in ['subject','lab','date','number','protocol','eid']},'format':'parquet' if is_table else 'legacy_npy','rows':n,'files':{k:v['path'] for k,v in by.items()},'rewardVolume_measured':('rewardVolume' in by['table']['columns']) if is_table else 'rewardVolume' in by})
    sessions.sort(key=lambda r:(r['subject'],r['date'],r['number'],r['eid']))
    # No duplicate date/number session keys: order unambiguous by original index.
    keys=[(r['subject'],r['date'],r['number']) for r in sessions]
    if len(set(keys))!=len(keys):raise ValueError('Ambiguous subject/date/number chronology')
    dump(OUT/'SESSIONS.json',sessions)
    summary=[]
    for subject in sorted({r['subject'] for r in sessions}):
        rr=[r for r in sessions if r['subject']==subject];total=sum(r['rows'] for r in rr)
        summary.append(dict(subject=subject,lab=rr[0]['lab'],sessions=len(rr),legacy_sessions=sum(r['format']=='legacy_npy' for r in rr),total_opportunities=total,prefix_complete=total>=1000,primary_complete=total>=4000,full_future_bins=min(6,max(0,total-1000)//500),future_opportunities=max(0,total-1000),session_sizes=[r['rows'] for r in rr],dates=[r['date'] for r in rr],session_numbers=[r['number'] for r in rr],missing_rewardVolume_sessions=sum(not r['rewardVolume_measured'] for r in rr)))
    out=dict(utc=dt.datetime.now(dt.timezone.utc).isoformat(),scope='opaque hash verification; Parquet footer/schema and NPY headers only; no trial array values or prefixes decoded',source_inventory_sha256=sha(FEAS/'excluded26_inventory.json'),source_cache_hashes={str(p.relative_to(ROOT)):sha(p) for p in [SOURCE/'standard_cache/datasets.pqt',SOURCE/'standard_cache/sessions.pqt']},files=len(files),verified_bytes=sum(r['bytes'] for r in files),sessions=len(sessions),animals=len(summary),primary_animals=sum(r['primary_complete'] for r in summary),summaries=summary)
    dump(OUT/'RESULT.json',out);log(dict(event='new_source_metadata_only_coverage',outcomes_read=False,animals=len(summary),sessions=len(sessions),files=len(files),verified_bytes=out['verified_bytes'],result_sha256=sha(OUT/'RESULT.json')))
    print(json.dumps({k:v for k,v in out.items() if k!='summaries'},indent=2),flush=True)
    print(json.dumps(summary,indent=2),flush=True)
    return out

def _sessions(subject):
    rs=json.loads((OUT/'SESSIONS.json').read_text());rs=[r for r in rs if r['subject']==subject]
    if not rs:raise ValueError('Not in original excluded26 coverage: '+subject)
    return rs

def _permit(subject,freeze_path,scored=False,forecast_manifest=None):
    if not freeze_path or not Path(freeze_path).is_file():raise PermissionError('New source values require existing prospective freeze')
    if scored and (not forecast_manifest or not Path(forecast_manifest).is_file()):raise PermissionError('Scored future values require existing saved-forecast manifest')
    return dict(freeze_path=str(freeze_path),freeze_sha256=sha(freeze_path),forecast_manifest=str(forecast_manifest) if forecast_manifest else None,forecast_manifest_sha256=sha(forecast_manifest) if forecast_manifest else None)

def _decode_session(r,n):
    """Decode selected first n rows; no future values returned or summarized."""
    n=int(n);paths=r['files'];values={k:np.full(n,np.nan) for k in FIELDS}
    if 'table' in paths:
        con=db();p=str(ROOT/paths['table'])
        cols=[row[0] for row in con.execute('DESCRIBE SELECT * FROM read_parquet(?)',[p]).fetchall()]
        names=[k for k in FIELDS if k in cols]
        select=','.join('"'+k+'"' for k in names)
        a=np.asarray(con.execute(f'SELECT {select} FROM read_parquet(?) LIMIT {n}',[p]).fetchall(),dtype=float)
        if len(a)!=n:raise ValueError('Prefix/footer length mismatch')
        for j,k in enumerate(names):values[k]=a[:,j]
    else:
        for field,path in paths.items():
            if field not in set(CORE+FIELDS+['repNum']):continue
            # Memory mapping selects only requested prefix rows; no whole-array
            # np.asarray operation or full-array load takes place.
            a=np.load(ROOT/path,mmap_mode='r',allow_pickle=False)
            if len(a)!=r['rows']:raise ValueError('NPY/header length mismatch')
            if field=='intervals':values['intervals_0']=np.array(a[:n,0],dtype=float);values['intervals_1']=np.array(a[:n,1],dtype=float)
            elif field in FIELDS:values[field]=np.array(a[:n],dtype=float).reshape(n)
    if 'repNum' in paths:
        rep=np.load(ROOT/paths['repNum'],mmap_mode='r',allow_pickle=False)
        values['repNum']=np.array(rep[:n],dtype=float).reshape(n)
    else:values['repNum']=np.full(n,np.nan)
    values['rewardVolume_available']=np.full(n,r['rewardVolume_measured'],dtype=bool)
    return values

def _read(subject,stop):
    sessions=_sessions(subject);parts=[];offsets=[0];remaining=int(stop)
    for i,r in enumerate(sessions):
        if remaining<=0:break
        n=min(remaining,r['rows']);remaining-=n
        if not n:continue
        values=_decode_session(r,n)
        values['session']=np.full(n,i,dtype=np.int32);values['session_index']=values['session'].copy()
        values['session_start']=np.zeros(n,dtype=bool);values['session_start'][0]=True
        values['start_of_session']=values['session_start'].copy()
        values['session_end']=np.zeros(n,dtype=bool);values['session_end'][-1]=n==r['rows']
        values['day']=np.full(n,i+1,dtype=np.int32)
        parts.append(values);offsets.append(offsets[-1]+n)
    if not parts:raise ValueError('Empty indexed prefix')
    values={k:np.concatenate([p[k] for p in parts]) for k in parts[0]}
    for k in ['choice','feedbackType']:
        if not np.isfinite(values[k]).all():raise ValueError('Nonfinite '+k+' '+subject)
        values[k]=values[k].astype(np.int8)
    if not np.isin(values['choice'],[-1,0,1]).all():raise ValueError('Invalid choice code '+subject)
    if not np.isin(values['feedbackType'],[-1,0,1]).all():raise ValueError('Invalid feedback code '+subject)
    values['session_offsets']=np.asarray(offsets,dtype=np.int64)
    return values

def load_prefix_and_opportunities(subject,prefix_n=1000,horizon=3000,freeze_path=None,purpose='prospective prefix calibration'):
    permit=_permit(subject,freeze_path);sessions=_sessions(subject)
    sizes=[r['rows'] for r in sessions];total=sum(sizes);take=min(prefix_n,total);future=min(horizon,max(0,total-prefix_n))
    starts=np.zeros(future,dtype=bool);offset=0
    for n in sizes:
        if prefix_n<=offset<prefix_n+future:starts[offset-prefix_n]=True
        offset+=n
    meta=dict(subject=subject,lab=sessions[0]['lab'],split='prospective_new_source',prefix_n_requested=prefix_n,prefix_n_available=take,future_horizon_requested=horizon,future_opportunities_available=future,indexed_total_trials=total,prefix_complete=total>=prefix_n,horizon_complete=total>=prefix_n+horizon,session_sizes_from_footer=sizes,session_dates=[r['date'] for r in sessions],future_outcomes_read=False,conditioned_on_realized_opportunities=True,row_counts_sha256=sha(OUT/'SESSIONS.json'),rewardVolume_policy='missing legacy values remain NaN, never measured/imputed')
    log(dict(event='open_new_source_prefix_only',subject=subject,purpose=purpose,outcome_trial_interval=[0,take],future_outcomes_read=False,fields=FIELDS,**permit))
    prefix=_read(subject,take);prefix['metadata']=meta
    return prefix,starts,meta

def load_scored(subject,stop=4000,freeze_path=None,forecast_manifest=None,purpose='one prospective source score'):
    permit=_permit(subject,freeze_path,True,forecast_manifest);sessions=_sessions(subject);take=min(stop,sum(r['rows'] for r in sessions))
    log(dict(event='open_new_source_scored_outcomes',subject=subject,purpose=purpose,outcome_trial_interval=[0,take],full_indexed_history_decoded=False,**permit))
    values=_read(subject,take);values['metadata']=dict(subject=subject,lab=sessions[0]['lab'],rows_read=take,stop_requested=stop)
    return values

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--coverage',action='store_true');p.add_argument('--workers',type=int,default=12)
    a=p.parse_args()
    if a.coverage:coverage(a.workers)
