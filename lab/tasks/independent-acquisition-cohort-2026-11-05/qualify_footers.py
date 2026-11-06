"""One-off footer/schema qualification, with proposed outcomes unopened.

No table body is acquired. Parquet statistics are neither queried nor exposed;
only total rows and column names/types are returned from derived footer files.
"""
import argparse
from collections import Counter,defaultdict
from datetime import datetime,timezone
import hashlib
import json
from pathlib import Path
import resource
import struct
import sys
import time

HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[2]
sys.path.insert(0,str(ROOT/'sources/longitudinal_learning_feasibility_2026-10-28/tools'))
import duckdb
import source_access
from source_access import request


def utc():return datetime.now(timezone.utc).isoformat()
def save(n,x):(HERE/n).write_text(json.dumps(x,indent=2,default=str)+'\n')


def plan():
    b=(HERE/'CANDIDATE_OBJECTS.json').read_bytes();obj=json.loads(b)['records']
    # Declare every exact eligible EID and dataset before metadata access.
    records=[r for r in obj if r['selected_objects'].get('table')]
    save('FOOTER_ACCESS_PLAN.json',dict(utc=utc(),source_sha256=hashlib.sha256(b).hexdigest(),
        scope='Only exact listed unprotected table IDs; sequential sessions per subject until3000 opportunities. No trial body, outcome values, learning summaries, QC or Parquet column statistics queried.',
        fields=['Parquet magic/format','num_rows','num_row_groups','column_names','column_types'],
        proposed_evaluation_outcomes='remain unopened',records=records))
    print('Declared',len(records),'session objects for',len({r['subject'] for r in records}),'candidate subjects; only required prefix coverage will be probed')


def main(resume=False):
    cpu,wall=time.process_time(),time.monotonic();io=Counter()
    prior_cpu=prior_wall=0.;out=[]
    if resume:
        previous=json.loads((HERE/'FOOTER_QUALIFICATION.json').read_bytes())
        assert previous['status']=='running'
        out=previous['subjects'];io.update(previous['io'])
        prior_cpu=previous['cpu_seconds'];prior_wall=previous['process_wall_seconds']
    completed={r['subject'] for r in out}
    logbytes=(HERE/'PUBLIC_REQUESTS.jsonl').read_bytes();io['explicit_read_bytes']+=len(logbytes)
    cached={}
    for rec in [json.loads(s) for s in logbytes.splitlines()]:
        if rec.get('status')==206 and 'error' not in rec and 'sha256' in rec:
            cached[(rec['url'],rec['requested_range'])]=rec
    def getrange(url,name,limit,byte_range,purpose):
        rec=cached.get((url,byte_range))
        if rec and (HERE/rec['local']).is_file():
            b=(HERE/rec['local']).read_bytes();io['explicit_cached_metadata_reads']+=len(b)
            assert hashlib.sha256(b).hexdigest()==rec['sha256'] and rec['local']==name
            return rec
        rec=request(url,name,limit,byte_range=byte_range,purpose=purpose,metadata_range_only=True,quiet=True)
        if rec.get('status')==206 and 'error' not in rec:cached[(url,byte_range)]=rec
        return rec
    pb=(HERE/'FOOTER_ACCESS_PLAN.json').read_bytes();io['explicit_read_bytes']+=len(pb)
    plan=json.loads(pb)
    rb=(HERE/'CANDIDATE_ROSTER.json').read_bytes();io['explicit_read_bytes']+=len(rb)
    roster={r['subject']:r for r in json.loads(rb)['subjects']}
    groups=defaultdict(list)
    for r in plan['records']:groups[r['subject']].append(r)
    allrows=json.loads((HERE/'CANDIDATE_OBJECTS.json').read_bytes())['records']
    io['explicit_read_bytes']+=(HERE/'CANDIDATE_OBJECTS.json').stat().st_size
    con=duckdb.connect(':memory:')
    for sub,rr in sorted(groups.items()):
        if sub in completed:continue
        rr=sorted([r for r in allrows if r['subject']==sub],key=lambda r:(r['date'],r['number']))
        offset=0;status='short_indexed_history';probes=[]
        for row in rr:
            if offset>=3000:status='footer_qualified_3000';break
            a=row['selected_objects'].get('table')
            if not a:status='missing_table_before_target';break
            did=a['dataset_id'];url=a['url']
            tailname=did+'_tail8.bin';footname=did+'_footer.bin'
            x=getrange(url,tailname,8,'bytes=-8','Declared exact eligible object: Parquet trailer only')
            if x.get('status')!=206 or 'error' in x:status='trailer_access_failure';probes.append(dict(eid=row['eid'],request=x));break
            t=(HERE/tailname).read_bytes();io['explicit_read_bytes']+=len(t)
            length,magic=struct.unpack('<I4s',t)
            if magic!=b'PAR1' or not 0<length<=1_000_000:
                status='invalid_or_large_footer';break
            total=int(x['response_headers']['Content-Range'].split('/')[-1])
            if total!=a['file_size']:
                status='catalogue_object_size_discrepancy';break
            etag=x['response_headers'].get('ETag','').strip('"')
            if '-' not in etag and etag!=a['md5']:
                status='catalogue_object_etag_discrepancy';break
            start=total-8-length
            y=getrange(url,footname,length,f'bytes={start}-{total-9}','Declared exact eligible object: footer/schema only; no statistics queried')
            if y.get('status')!=206 or 'error' in y:status='footer_access_failure';break
            assert x['response_headers']['ETag']==y['response_headers']['ETag']
            raw=(HERE/footname).read_bytes();io['explicit_read_bytes']+=len(raw)
            assert len(raw)==length
            # Reconstitute a footer-only logical file, with zeros replacing data.
            derived=HERE/(did+'_footer_only.pqt')
            with derived.open('wb') as f:
                f.write(b'PAR1');f.seek(start);f.write(raw);f.write(t)
            io['engine_footer_logical_file_charge']+=total
            n,ng=con.execute(f"SELECT num_rows,num_row_groups FROM parquet_file_metadata('{derived}')").fetchone()
            schema=con.execute(f"SELECT name,type FROM parquet_schema('{derived}')").fetchall()
            io['decoded_footer_metadata_bytes']+=length
            fields={z[0] for z in schema};required={'choice','contrastLeft','contrastRight','feedbackType','probabilityLeft'}
            probe=dict(**{k:row[k] for k in ('eid','subject','lab','date','number','protocol')},dataset_id=did,
                 source_url=url,file_size=total,etag=etag,footer_sha256=hashlib.sha256(raw).hexdigest(),
                 rows=n,row_groups=ng,columns=schema,required_fields_present=required<=fields,
                 start=offset,stop=offset+n,statistics_queried=False,trial_values_acquired=False)
            probes.append(probe)
            if not required<=fields:status='required_fields_missing';break
            offset+=n
        if offset>=3000:status='footer_qualified_3000'
        out.append(dict(subject=sub,cohort=roster[sub]['cohort'],lab=roster[sub]['lab'],status=status,
                        verified_opportunities=offset,probes=probes,chronology=roster[sub]))
        print(sub,status,offset,flush=True)
        # Save recoverable same-assignment progress without a new access request.
        save('FOOTER_QUALIFICATION.json',dict(utc=utc(),status='running',subjects=out,io=dict(io),
             cpu_seconds=prior_cpu+time.process_time()-cpu,process_wall_seconds=prior_wall+time.monotonic()-wall))
    io['request_log_initial_read_bytes']+=source_access.REQUEST_LOG_BYTES_READ
    summary=dict(utc=utc(),status='complete',subjects=out,
        counts_by_status=dict(Counter(r['status'] for r in out)),
        qualified_by_cohort=dict(Counter(r['cohort'] for r in out if r['status']=='footer_qualified_3000')),
        scope='Accessible fields and >=3000 deposited opportunities only; no biological-first-exposure guarantee, genotype/subject-UUID certification or outcome validation.',
        io=dict(io),cpu_seconds=prior_cpu+time.process_time()-cpu,process_wall_seconds=prior_wall+time.monotonic()-wall,
        peak_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
        input_plan_sha256=hashlib.sha256(pb).hexdigest())
    save('FOOTER_QUALIFICATION.json',summary)
    print(json.dumps({k:v for k,v in summary.items() if k!='subjects'},indent=2))


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--plan',action='store_true');p.add_argument('--resume',action='store_true');a=p.parse_args()
    plan() if a.plan else main(a.resume)
