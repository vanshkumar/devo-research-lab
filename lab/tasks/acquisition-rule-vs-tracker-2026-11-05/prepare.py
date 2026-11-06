"""Eligible consumed periods only; own-directory projection and exposure log."""
from collections import Counter
import hashlib
import importlib.util
import json
from pathlib import Path
import resource
import time
import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
OLD = ROOT/'campaigns/learning_rule_transport_2026-10-28'
PREV = HERE.parent/'acquisition-reactive-sequence-2026-11-04'
COUNTS = Counter()
PINS = {}

def utc():
    from datetime import datetime, timezone
    return datetime.now(timezone.utc).isoformat()

def read(p, pin=None):
    b=p.read_bytes(); COUNTS['explicit_read_bytes']+=len(b)
    h=hashlib.sha256(b).hexdigest()
    if pin is not None: assert h==pin, str(p)
    PINS[str(p.relative_to(ROOT))]=h
    return b

def get(p, pin=None): return json.loads(read(p,pin))
def save(p,x): (HERE/p).write_text(json.dumps(x,indent=2,allow_nan=False)+'\n')

def main():
    start=time.monotonic()
    freeze=get(OLD/'protocols/FREEZE.json','c0141244ac43d240f858956917e3b2b661c72a01a4bddbccdb3974a818b5741f')
    frozen={x['path']:x['sha256'] for x in freeze['files']}
    split=get(OLD/'artifacts/models/DEVELOPMENT_MODEL_SPLIT.json','1ebd21840771d2b101a80ee9912615075f7a99d55520e5cfe35bc4d95fbc6d10')
    roster=split['train']+split['validation']
    assert len(set(roster))==74
    index=get(OLD/'data/INDEX.json',frozen['data/INDEX.json'])
    row=get(OLD/'data/ROW_COUNTS.json',frozen['data/ROW_COUNTS.json'])
    foot={x['eid']:x for x in row}
    downloads=[json.loads(x) for x in read(OLD/'data/DOWNLOAD_MANIFEST.jsonl').splitlines()]
    downloads={x['dataset_id']:x for x in downloads if x.get('verified')}
    exceptions=get(OLD/'data/OBJECT_METADATA_EXCEPTIONS.json',frozen['data/OBJECT_METADATA_EXCEPTIONS.json'])
    exposure=[json.loads(x) for x in read(OLD/'protocols/EXPOSURE.jsonl').splitlines()]
    spec=importlib.util.spec_from_file_location('consumed_source',PREV/'source.py')
    read(PREV/'source.py')
    source=importlib.util.module_from_spec(spec); spec.loader.exec_module(source)
    source.HERE=HERE
    fields=source.FIELDS
    sessions=[]; disposition={}
    for s in roster:
        es=[x for x in exposure if x.get('subject')==s and x['event']=='open_outcomes'
            and x.get('scope')=='all indexed trials for this subject' and x.get('split')=='dev'
            and set(fields)<=set(x['fields'])]
        assert es, ('No prior original exposure',s)
        rs=sorted([r for r in index if r['subject']==s and r['kind']=='table'],key=lambda r:(r['date'],r['number']))
        assert len(rs)==len({(r['date'],r['number']) for r in rs})
        offset=0; used=[]
        for r in rs:
            f=foot[r['eid']]; n=f['rows']
            keys=('eid','subject','lab','date','number','protocol')
            assert all(r[k]==f[k] for k in keys)
            assert r['split']=='dev' and 'trainingChoiceWorld' in r['protocol']
            if offset+n>4000: break
            if not n: continue
            d=downloads[r['dataset_id']]
            assert all(r[k]==d[k] for k in (*keys,'dataset_id','path','split'))
            if d.get('source_cache_mismatch'):
                e=exceptions[r['dataset_id']]
                assert d['bytes']==e['object_bytes'] and d['sha256']==e['object_sha256']
                assert d['md5']==e['object_etag_md5']
                # The old source.asset helper prioritizes stale cache_bytes.
                # This certified exception is the original public object.
                d={k:v for k,v in d.items() if k!='cache_bytes'}
            a=source.asset(d,OLD/r['path'])
            sessions.append(dict(**{k:r[k] for k in keys},start=offset,stop=offset+n,
                                 provenance_utc=es[0]['utc'],assets={'table':a}))
            offset+=n; used.append(r['eid'])
        disposition[s]=dict(role='train' if s in split['train'] else 'selection',
                            lab=rs[0]['lab'],rows=offset,sessions=len(used),
                            prefix_eligible=offset>=1000,shared_fit_eligible=offset>1000,
                            prior_full_read_utc=es[0]['utc'])
    eval_manifest=get(PREV/'SOURCE_MANIFEST.json','19c68735e1fd721ad86a5c05debedf98f8782e8d4461799efe3d3d0925958210')
    eval_run=get(PREV/'SOURCE_ALL_EXECUTION.json')
    read(PREV/'EXPOSURE.jsonl')
    assert not set(roster)&set(eval_manifest['subjects'])
    assert len(eval_manifest['subjects'])==64 and tuple(eval_manifest['fields'])==fields
    assert eval_manifest['maximum_rows_per_animal']==4000
    manifest=dict(utc=utc(),subjects=roster,fields=fields,maximum_rows_per_animal=4000,
                  sessions=sessions,disposition=disposition,split=split,pins=PINS.copy(),
                  purpose='consumed-data rule-versus-tracker development; no new outcomes')
    save('SOURCE_MANIFEST.json',manifest)
    data=source.decode(manifest,roster,'original74_consumed_complete_sessions')
    assert all(len(data[s])==disposition[s]['rows'] for s in roster)
    np.savez_compressed(HERE/'TRAIN_ROWS.npz',**data)
    cache=PREV/'CAPPED_ROWS.npz'
    read(cache)
    with (HERE/'EXPOSURE.jsonl').open('a') as log:
        log.write(json.dumps(dict(utc=utc(),action='reuse_consumed_64_projection',
             path=str(cache.relative_to(ROOT)),sha256=PINS[str(cache.relative_to(ROOT))],
             fields=fields,subjects=eval_manifest['subjects'],rows=eval_run['rows'],
             source_manifest_sha256=PINS[str((PREV/'SOURCE_MANIFEST.json').relative_to(ROOT))]))+'\n')
    with np.load(cache,allow_pickle=False) as z:
        assert z.files==eval_manifest['subjects']
        ev={s:z[s] for s in z.files}
    assert {s:len(a) for s,a in ev.items()}==eval_run['rows']
    assert all(a.shape[1]==7 for a in ev.values())
    COUNTS['decoded_eval_array_bytes']+=sum(a.nbytes for a in ev.values())
    source.crosscheck(ev,eval_manifest)
    save('PREPARATION.json',dict(utc=utc(),seconds=time.monotonic()-start,
        disposition=disposition,train_rows=sum(map(len,data.values())),eval_rows=sum(map(len,ev.values())),
        eval_source_manifest=eval_manifest,io=dict(COUNTS),source_io=dict(source.BYTES),pins=PINS,
        source_pins=source.META_PINS,peak_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
        physical_io='unknown; explicit and nominal query/read charges only'))
    print(json.dumps(dict(train_rows=sum(map(len,data.values())),eval_rows=sum(map(len,ev.values())),
                         seconds=time.monotonic()-start,disposition={k:sum(d[k] for d in disposition.values())
                           for k in ('prefix_eligible','shared_fit_eligible')})),flush=True)

if __name__=='__main__': main()
