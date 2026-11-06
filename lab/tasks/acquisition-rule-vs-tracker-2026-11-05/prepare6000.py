"""PI-amended fit-window read, with explicit prior exposure for boundary decode."""
import time
import json
import hashlib
import importlib.util
import resource
import numpy as np
from prepare import HERE, ROOT, OLD, PREV, read, get, save, COUNTS, PINS, utc

def main():
    begin=time.monotonic()
    freeze=get(OLD/'protocols/FREEZE.json','c0141244ac43d240f858956917e3b2b661c72a01a4bddbccdb3974a818b5741f')
    pin={x['path']:x['sha256'] for x in freeze['files']}
    split=get(OLD/'artifacts/models/DEVELOPMENT_MODEL_SPLIT.json','1ebd21840771d2b101a80ee9912615075f7a99d55520e5cfe35bc4d95fbc6d10')
    roster=split['train']+split['validation']; assert len(set(roster))==74
    idx=get(OLD/'data/INDEX.json',pin['data/INDEX.json'])
    foot={x['eid']:x for x in get(OLD/'data/ROW_COUNTS.json',pin['data/ROW_COUNTS.json'])}
    dl={x['dataset_id']:x for x in map(json.loads,read(OLD/'data/DOWNLOAD_MANIFEST.jsonl').splitlines()) if x.get('verified')}
    ex=list(map(json.loads,read(OLD/'protocols/EXPOSURE.jsonl').splitlines()))
    exceptions=get(OLD/'data/OBJECT_METADATA_EXCEPTIONS.json',pin['data/OBJECT_METADATA_EXCEPTIONS.json'])
    read(HERE/'BRIEF.md')
    spec=importlib.util.spec_from_file_location('fit6000_source',PREV/'source.py')
    source=importlib.util.module_from_spec(spec);spec.loader.exec_module(source);source.HERE=HERE
    sessions=[];proof={};disp={}
    for s in roster:
        prior=[x for x in ex if x.get('subject')==s and x['event']=='open_outcomes' and
               x.get('split')=='dev' and x.get('scope')=='all indexed trials for this subject' and set(source.FIELDS)<=set(x['fields'])]
        assert prior
        rs=sorted([r for r in idx if r['subject']==s and r['kind']=='table'],key=lambda r:(r['date'],r['number']))
        assert len(rs)==len({(r['date'],r['number']) for r in rs})
        off=0; selected=[]
        for r in rs:
            if off>=6000:break
            n=foot[r['eid']]['rows']; keys=('eid','subject','lab','date','number','protocol')
            assert all(foot[r['eid']][k]==r[k] for k in keys) and r['split']=='dev'
            if not n:continue
            d=dl[r['dataset_id']];assert all(d[k]==r[k] for k in (*keys,'path','dataset_id','split'))
            if d.get('source_cache_mismatch'):
                e=exceptions[r['dataset_id']]
                assert d['bytes']==e['object_bytes'] and d['sha256']==e['object_sha256']
                d={k:v for k,v in d.items() if k!='cache_bytes'}
            asset=source.asset(d,OLD/r['path'])
            record=dict(**{k:r[k] for k in keys},start=off,stop=off+n,provenance_utc=prior[0]['utc'],assets={'table':asset})
            sessions.append(record); selected.append(dict(eid=r['eid'],decoded=[off,off+n],fit_selected=[off,min(6000,off+n)]))
            off+=n
        proof[s]=dict(prior_original_full_read=prior[0],selected_exact_sessions=selected,
                      boundary_decode_authority='PI amendment permits already-consumed boundary decode; exact prior full-indexed exposure covers every selected original session')
        disp[s]=dict(role='train' if s in split['train'] else 'selection',lab=rs[0]['lab'],decoded=off,fit_rows=min(off,6000))
    manifest=dict(utc=utc(),subjects=roster,fields=source.FIELDS,maximum_fit_rows=6000,
                  sessions=sessions,exposure_proof=proof,disposition=disp,pins=PINS.copy(),
                  boundary_decode_separately_authorized=True)
    # This proof is saved BEFORE the first amended raw read.
    save('SOURCE_FIT6000_MANIFEST.json',manifest)
    data=source.decode(manifest,roster,'PI_amendment_original74_fit6000_with_certified_boundary_decode')
    data={s:a[:6000].copy() for s,a in data.items()}
    np.savez_compressed(HERE/'TRAIN6000_ROWS.npz',**data)
    save('PREPARATION6000.json',dict(utc=utc(),seconds=time.monotonic()-begin,disposition=disp,
          selected_rows=sum(map(len,data.values())),decoded_rows=sum(d['decoded'] for d in disp.values()),
          io=dict(COUNTS),source_io=dict(source.BYTES),pins=PINS,
          peak_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss))
    print(json.dumps(dict(seconds=time.monotonic()-begin,selected_rows=sum(map(len,data.values())),
                         decoded_rows=sum(d['decoded'] for d in disp.values()))),flush=True)

if __name__=='__main__': main()
