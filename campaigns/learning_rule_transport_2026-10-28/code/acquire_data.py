#!/usr/bin/env python3
"""Pinned metadata-only allocation and verified public IBL byte acquisition.

Downloading bytes does not analyze outcomes. Trial Parquet footers are used only
for row counts; they are not scanned before development allocation is frozen.
"""
from __future__ import annotations
import argparse, concurrent.futures, datetime as dt, hashlib, json, os, sys, time
from collections import Counter
from pathlib import Path
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[3]
CAMPAIGN = Path(__file__).resolve().parents[1]
SOURCE = ROOT / 'sources/longitudinal_learning_feasibility_2026-10-28'
sys.path.insert(0, str(SOURCE / 'tools'))
import duckdb

def digest(path, kind='sha256'):
    h=hashlib.new(kind)
    with open(path,'rb') as f:
        for b in iter(lambda:f.read(1<<20),b''): h.update(b)
    return h.hexdigest()

def dump(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value,indent=2,default=str)+'\n')

def exposure(event):
    event={'utc':dt.datetime.now(dt.timezone.utc).isoformat(),**event}
    with open(CAMPAIGN/'protocols/EXPOSURE.jsonl','a') as f:
        f.write(json.dumps(event,sort_keys=True)+'\n')

def freeze():
    """Use no trial outcome columns, plots, values, or performance criteria."""
    path=CAMPAIGN/'protocols/SPLIT.json'
    if path.exists(): return json.loads(path.read_text())
    meta=json.loads((SOURCE/'cohort_metadata.json').read_text())
    assignments=[]
    for subject,lab,n,t,first,last in meta['standard_subject_metadata']:
        eligible=n==t and t>0
        bucket=int(hashlib.sha256(('learning_rule_transport_2026-10-28:'+subject).encode()).hexdigest(),16)%5
        split=('lab_holdout' if lab in ['hoferlab','wittenlab'] else
               'animal_holdout' if bucket==0 else 'dev') if eligible else 'excluded_incomplete_tables'
        assignments.append(dict(subject=subject,lab=lab,indexed_sessions=n,table_sessions=t,
                                first_indexed_date=first,last_indexed_date=last,split=split,hash_mod_5=bucket))
    x=dict(campaign='learning_rule_transport_2026-10-28',date='2026-10-28',
           frozen_before_outcome_reads=True,source_manifest_sha256=digest(SOURCE/'MANIFEST.json'),
           allocation='All indexed training sessions must have trial tables; hold out hoferlab and wittenlab entirely; SHA256(campaign+colon+subject) modulo5=0 hold out animals in other labs; no outcome selection.',
           standard=assignments,external_strict_prefix=meta['pan_complete_days_1_5'],
           external_prefix_gap_excluded=['fip_16','fip_38'],external_status='sealed; only metadata and prior sample schema/rowcount known',
           prior_exposure=[dict(subject='CSHL034',date='2019-10-01',session=1,role='source feasibility',scope='schema,rowcount,bytes,hash only; no outcomes'),
                           dict(subject='fip_13',date='2021-03-05',session=1,role='external feasibility',scope='schema,rowcount,bytes,hash only; no outcomes')],
           limitation='Complete indexed tables do not certify biological first exposure; short and discontinued histories are included with prespecified exposure/censoring treatment.')
    dump(path,x)
    exposure(dict(event='split_frozen',split_sha256=digest(path),counts=dict(Counter(a['split'] for a in assignments)),outcomes_read=False))
    return x

def records():
    split=freeze()
    amap={x['subject']:x for x in split['standard']}
    conn=duckdb.connect()
    out=[]
    for cohort in ['standard','pan']:
        conn.execute(f"CREATE OR REPLACE TEMP VIEW s AS SELECT * FROM read_parquet('{SOURCE / (cohort+'_cache/sessions.pqt')}')")
        conn.execute(f"CREATE OR REPLACE TEMP VIEW d AS SELECT * FROM read_parquet('{SOURCE / (cohort+'_cache/datasets.pqt')}')")
        if cohort=='pan':
            conn.execute(f"CREATE OR REPLACE TEMP VIEW days AS SELECT * FROM read_parquet('{SOURCE/'pan_training_day.pqt'}')")
        rows=conn.execute("SELECT s.subject,s.lab,s.date,s.number,s.task_protocol,s.id,d.session_path,d.rel_path,d.id,d.file_size,d.hash,d.exists_aws,d.default_revision FROM s JOIN d ON s.id=d.eid WHERE "+
            ("s.task_protocol LIKE '%trainingChoiceWorld%'" if cohort=='standard' else "s.task_protocol = '_iblrig_tasks_FPChoiceWorld6.4.2'")+" AND (d.rel_path LIKE '%_ibl_trials.table.pqt' OR d.rel_path LIKE '%_ibl_trials.repNum.npy') ORDER BY s.subject,s.date,s.number,d.rel_path,d.default_revision DESC").fetchall()
        seen=set()
        for subject,lab,date,number,protocol,eid,session_path,rel,did,size,md5,aws,default in rows:
            if cohort=='standard':
                a=amap.get(subject)
                if not a or a['split']=='excluded_incomplete_tables': continue
                label=a['split']
            else:
                if subject not in split['external_strict_prefix']: continue
                label='external'
            key=(eid,rel)
            if key in seen: continue
            seen.add(key)
            # S3 inserts the dataset UUID immediately before the suffix.
            rp=Path(rel)
            remote=str(rp.with_name(rp.stem+'.'+did+rp.suffix))
            url='https://ibl-brain-wide-map-public.s3.amazonaws.com/data/'+session_path+'/'+remote
            kind='table' if rel.endswith('.pqt') else 'repNum'
            base='data/raw/dev' if label=='dev' else 'data/sealed/'+label
            local=CAMPAIGN/base/subject/(str(date)+'_'+str(number).zfill(3)+'_'+eid+'_'+kind+rp.suffix)
            day=conn.execute('SELECT training_day FROM days WHERE eid=?',[eid]).fetchone()[0] if cohort=='pan' else None
            out.append(dict(cohort=cohort,split=label,subject=subject,lab=lab,date=str(date),number=number,protocol=protocol,eid=eid,
                            session_path=session_path,rel_path=rel,dataset_id=did,kind=kind,bytes=size,md5=md5,exists_aws=aws,
                            default_revision=default,url=url,path=str(local.relative_to(CAMPAIGN)),author_day=day))
    dump(CAMPAIGN/'data/INDEX.json',out)
    return out

def fetch_one(rec):
    override_path=CAMPAIGN/'data/OBJECT_METADATA_EXCEPTIONS.json'
    overrides=json.loads(override_path.read_text()) if override_path.exists() else {}
    if rec['dataset_id'] in overrides:
        o=overrides[rec['dataset_id']]
        rec={**rec,'cache_bytes':rec['bytes'],'cache_md5':rec['md5'],
             'bytes':o['object_bytes'],'md5':o['object_etag_md5'],
             'source_cache_mismatch':True,'object_metadata_evidence':o['evidence']}
    p=CAMPAIGN/rec['path']
    for attempt in range(5):
        try:
            if p.exists() and p.stat().st_size==rec['bytes'] and digest(p,'md5')==rec['md5']:
                return dict(**rec,sha256=digest(p),verified=True,reused=True)
            p.parent.mkdir(parents=True,exist_ok=True)
            temp=p.with_suffix(p.suffix+'.partial')
            req=Request(rec['url'],headers={'User-Agent':'research-lab-open-data/1.0'})
            with urlopen(req,timeout=60) as response,open(temp,'wb') as f:
                for b in iter(lambda:response.read(1<<18),b''): f.write(b)
            if temp.stat().st_size!=rec['bytes'] or digest(temp,'md5')!=rec['md5']:
                raise ValueError('public index byte/hash mismatch '+str(temp))
            temp.replace(p)
            return dict(**rec,sha256=digest(p),verified=True,reused=False)
        except Exception as e:
            if attempt==4: return dict(**rec,verified=False,error=repr(e))
            time.sleep(min(1+attempt*2,7))

def main():
    p=argparse.ArgumentParser()
    p.add_argument('--freeze-only',action='store_true')
    p.add_argument('--splits',default='dev,animal_holdout,lab_holdout,external')
    p.add_argument('--workers',type=int,default=12)
    p.add_argument('--limit',type=int,default=0)
    p.add_argument('--tables-only',action='store_true')
    args=p.parse_args()
    split=freeze(); rs=records()
    print('allocation',dict(Counter(a['split'] for a in split['standard'])),flush=True)
    print('indexed files',len(rs),'bytes',sum(r['bytes'] for r in rs),flush=True)
    if args.freeze_only: return
    selected=[r for r in rs if r['split'] in args.splits.split(',') and (not args.tables_only or r['kind']=='table')]
    # Visit early sessions in every animal before the later sessions.
    selected.sort(key=lambda r:(r['date'],r['subject'],r['number'],r['kind']))
    if args.limit: selected=selected[:args.limit]
    manifest=CAMPAIGN/'data/DOWNLOAD_MANIFEST.jsonl'
    start=time.time(); done=0; failed=0; count=0
    with concurrent.futures.ThreadPoolExecutor(max_workers=args.workers) as pool,open(manifest,'a') as f:
        for rec in pool.map(fetch_one,selected):
            f.write(json.dumps(rec,sort_keys=True)+'\n'); f.flush()
            count+=1; done+=rec['bytes'] if rec['verified'] else 0; failed+=not rec['verified']
            if count%100==0 or count==len(selected): print(dict(files=count,total=len(selected),bytes=done,failed=failed,seconds=round(time.time()-start,1)),flush=True)
    exposure(dict(event='byte_acquisition',splits=args.splits,files=count,failed=failed,verified_bytes=done,outcomes_read=False))

if __name__=='__main__': main()
