"""The predeclared273-row NYU-42 source-only measurement probe."""
from datetime import datetime,timezone
from collections import Counter
import hashlib,json,resource,sys,time
from pathlib import Path
import numpy as np

HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[2]
sys.path.insert(0,str(ROOT/'sources/longitudinal_learning_feasibility_2026-10-28/tools'))
import duckdb
from source_access import request

cpu,wall=time.process_time(),time.monotonic();IO=Counter()
pb=(HERE/'SOURCE_ONLY_ACCESS_PLAN.json').read_bytes();IO['explicit_reads']+=len(pb);plan=json.loads(pb)
assert plan['source_only_subject']=='NYU-42' and plan['exclude_entire_subject_from_all_candidate_evaluation']
rec=plan['exact_first_session'];did=rec['dataset_id'];fields=plan['fields'];assert rec['rows']==273
old=set(json.loads((HERE/'ORIGINAL_EXCLUSIONS.json').read_bytes())['exclusion_keys']);assert 'nyu42' not in old
c=duckdb.connect(':memory:');footer=HERE/(did+'_footer_only.pqt');outpath=HERE/(did+'_source_only_probe.pqt')
data=footer.read_bytes();IO['explicit_reads']+=len(data);outpath.write_bytes(data)
rows=c.execute(f"SELECT path_in_schema,dictionary_page_offset,data_page_offset,total_compressed_size FROM parquet_metadata('{footer}')").fetchall()
chunks=[]
for field,dictionary,page,size in rows:
    if field not in fields:continue
    start=min(v for v in (dictionary,page) if v is not None and v>=4)
    chunks.append(dict(field=field,start=start,stop=start+size,bytes=size))
assert {x['field'] for x in chunks}==set(fields)
(HERE/'SOURCE_ONLY_BYTE_RANGES.json').write_text(json.dumps(dict(utc=datetime.now(timezone.utc).isoformat(),
       access_plan_sha256=hashlib.sha256(pb).hexdigest(),subject=plan['source_only_subject'],eid=rec['eid'],
       fields=fields,rows=273,chunks=chunks,declared_before_acquisition=True),indent=2)+'\n')
event=dict(utc=datetime.now(timezone.utc).isoformat(),event='new_source_only_measurement',subject='NYU-42',
           eid=rec['eid'],dataset_id=did,rows=[0,273],fields=fields,entire_animal_excluded_from_evaluation=True)
with (HERE/'EXPOSURE.jsonl').open('a') as f:f.write(json.dumps(event)+'\n')
received=0
for x in chunks:
    name=did+'_probe_'+x['field']+'.bin'
    r=request(rec['source_url'],name,x['bytes'],byte_range=f"bytes={x['start']}-{x['stop']-1}",
           purpose='Predeclared NYU-42 source-only273-row measurement; excluded from evaluation',metadata_range_only=True,quiet=True)
    assert r.get('status')==206 and 'error' not in r and r['response_headers']['ETag'].strip('"')==rec['etag']
    raw=(HERE/name).read_bytes();IO['explicit_reads']+=len(raw);received+=len(raw)
    with outpath.open('r+b') as f:f.seek(x['start']);f.write(raw)
q=','.join('"'+x+'"' for x in fields)
a=np.asarray(c.execute(f"SELECT {q} FROM read_parquet('{outpath}')").fetchall(),dtype=float)
IO['engine_logical_file_charge']+=outpath.stat().st_size;IO['decoded_array_bytes']+=a.nbytes
assert a.shape==(273,len(fields))
d={k:a[:,j] for j,k in enumerate(fields)}
signed=np.nan_to_num(d['contrastRight'])-np.nan_to_num(d['contrastLeft']);nz=(signed!=0)&(d['choice']!=0)
checks=dict(choice_codes_valid=bool(np.isin(d['choice'],[-1,0,1]).all()),
    feedback_codes_valid=bool(np.isin(d['feedbackType'],[-1,0,1]).all()),
    probability_finite_and_bounded=bool((np.isfinite(d['probabilityLeft'])&(d['probabilityLeft']>=0)&(d['probabilityLeft']<=1)).all()),
    contrast_one_side=bool(~((np.nan_to_num(d['contrastLeft'])>0)&(np.nan_to_num(d['contrastRight'])>0)).any()),
    reward_finite_nonnegative=bool((np.isfinite(d['rewardVolume'])&(d['rewardVolume']>=0)).all()),
    finite_ordered_intervals=bool(np.isfinite(d['intervals_0']).all() and np.isfinite(d['intervals_1']).all()
       and (d['intervals_1']>=d['intervals_0']).all() and (np.diff(d['intervals_0'])>=0).all()),
    nonzero_feedback_choice_sign_agreement=bool(np.all((d['feedbackType'][nz]>0)==(d['choice'][nz]==-np.sign(signed[nz])))),
    omissions_not_rewarded=bool(np.all(d['feedbackType'][d['choice']==0]<=0)))
assert all(checks.values())
np.savez_compressed(HERE/'SOURCE_ONLY_ROWS.npz',values=a,fields=fields,subject='NYU-42')
result=dict(utc=datetime.now(timezone.utc).isoformat(),subject='NYU-42',eid=rec['eid'],rows=273,fields=fields,
       checks=checks,all_passed=all(checks.values()),source_ingress_bytes=received,
       no_new_evaluation_outcomes=True,source_only_exposure='All273rows/eightfields consumed; entire NYU-42 remains excluded from candidate evaluation. No later rows or other animals.',
       io=dict(IO),cpu_seconds=time.process_time()-cpu,process_wall_seconds=time.monotonic()-wall,
       peak_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
(HERE/'SOURCE_MEASUREMENT_PROBE.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
