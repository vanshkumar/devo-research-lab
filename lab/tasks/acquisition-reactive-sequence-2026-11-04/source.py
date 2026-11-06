"""Metadata-first source projection. Never opens a session intersecting row 4001."""
from collections import Counter
import hashlib
import importlib.util
import json
from pathlib import Path
import resource
import sys
import time

import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
OLD = ROOT / 'campaigns/learning_rule_transport_2026-10-28'
POP = ROOT / 'campaigns/population_learning_transport_2026-10-28'
REV = ROOT / 'campaigns/learning_transport_revised_2026-10-29'
FIELDS = ('contrastLeft', 'contrastRight', 'choice', 'feedbackType', 'rewardVolume', 'probabilityLeft')
CAP = 4000
BYTES = Counter()
META_PINS = {}


def utc():
    from datetime import datetime, timezone
    return datetime.now(timezone.utc).isoformat()


def blob(path, pin=None, record=True):
    data = path.read_bytes()
    BYTES['explicit_file_reads'] += len(data)
    sha = hashlib.sha256(data).hexdigest()
    if pin is not None and sha != pin:
        raise ValueError(f'Pin mismatch {path}')
    if record:
        META_PINS[str(path.relative_to(ROOT))] = sha
    return data


def get(path, pin=None):
    return json.loads(blob(path, pin))


def save(name, data):
    (HERE/name).write_text(json.dumps(data, indent=2, allow_nan=False)+'\n')


def lines(path):
    return [json.loads(line) for line in blob(path).splitlines()]


def check(test, label):
    if not test:
        raise ValueError(label)


def reference():
    p = HERE.parent/'acquisition-probe-design-2026-11-04/pilot.py'
    blob(p, 'febcc48d80ee5163ce58d1735e470a597382f4931e627e4664feb5cb32e94c02')
    spec = importlib.util.spec_from_file_location('pilot_ref', p)
    pilot = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(pilot)
    ref, summary, result = pilot.reference()
    models = pilot.model_load()
    subject = str(summary['subjects'][0])
    pins = {x['path']:x['sha256'] for x in ref['forecast_records']}
    late = {}
    for name in ('existing', 'session'):
        path = pilot.COMP/subject/(name+'.npz')
        a = pilot.arrays(path, ('weights', 'hidden_final'), pins[str(path.relative_to(ROOT))])
        late[name] = dict(w=a['weights'][:1,5], h=a['hidden_final'][:1])
    manifest = {x['path']:x['sha256'] for x in pilot.js(OLD/'MANIFEST.json')['artifacts']}
    path, = [OLD/'artifacts/forecasts'/f/(subject+'__reinforce.npz')
             for f in ('source_animals','source_labs')
             if (OLD/'artifacts/forecasts'/f/(subject+'__reinforce.npz')).is_file()]
    late['reinforce'] = dict(w=pilot.arrays(path, ['weights'], manifest[str(path.relative_to(OLD))])['weights'][:1,5])
    result['scalar_step_error'] = pilot.reference_step(models, late)
    result['input_hashes'] = pilot.PINS
    result['counted_io'] = dict(pilot.D)
    result['utc'] = utc()
    save('REFERENCE.json', result)
    return result


def asset(rec, path):
    p = path.resolve(strict=True)
    check(p == path and p.is_relative_to(ROOT), f'Unexpected resolved path {path}')
    n = rec.get('cache_bytes', rec['bytes'])
    check(rec['verified'] and p.stat().st_size == n, f'Unverified asset {path}')
    return dict(path=str(p.relative_to(ROOT)), size=n, sha=rec['sha256'], dataset_id=rec['dataset_id'])


def manifest(ref):
    pfreeze = POP/'protocols/FREEZE.json'
    freeze_sha = '625535ac5c20fe7301b7dcdec22549fd0a708271cc51dd79df8dee6f5c37a64c'
    pop = get(pfreeze, freeze_sha)
    pin = {ROOT/x['path']:x['sha256'] for x in pop['files']}
    ofreeze = OLD/'protocols/FREEZE.json'
    old = get(ofreeze, pin[ofreeze])
    op = {OLD/x['path']:x['sha256'] for x in old['files']}
    of = lambda p: get(OLD/p, op[OLD/p])
    pf = lambda p: get(POP/p, pin[POP/p])
    ids40 = get(OLD/'artifacts/results/SUBJECT_ORDER.json',
                '2f57d860a20b9f73ef1aba9d9e9135075897b78f7fa40ac3a67b02f8ad7313b0')
    ids24 = pop['source_primary_subjects']
    ids = ids40+ids24
    check(len(ids40)==40 and len(ids24)==24 and len(set(ids))==64 and ids==ref['roster'], 'Roster')
    check(not set(ids) & set(pop['external_subjects']+['SWC_007','NYU-21','SWC007','NYU21']), 'Protected roster')
    orig_exposure = lines(OLD/'protocols/EXPOSURE.jsonl')
    pop_exposure = lines(POP/'protocols/EXPOSURE.jsonl')
    old_ids = {
        r['subject']:r for r in get(OLD/'protocols/SPLIT.json', pin[OLD/'protocols/SPLIT.json'])['standard']}
    counts = {x['eid']:x for x in of('data/ROW_COUNTS.json')}
    download = {x['dataset_id']:x for x in lines(OLD/'data/DOWNLOAD_MANIFEST.jsonl')}
    tables = [x for x in of('data/INDEX.json') if x['subject'] in ids40 and x['kind']=='table']
    mixed = [x for x in pf('artifacts/coverage/SESSIONS.json') if x['subject'] in ids24]
    filemeta = {x['path']:x for x in pf('artifacts/coverage/FILE_METADATA.json') if x['subject'] in ids24}
    # The original score exposure cites the saved forecast manifest and scope.
    scorepin = '256e0d3e595626a074acc28228cebf3eb56acf6d24ea4d5340339f77e98dc9d8'
    blob(POP/'protocols/SOURCE_FORECASTS.json', scorepin)
    sessions = []
    for j, (subject, lab) in enumerate(zip(ids, ref['labs'])):
        earlier = j < 40
        if earlier:
            split = old_ids[subject]['split']
            check(split in ('lab_holdout','animal_holdout') and old_ids[subject]['lab']==lab, subject)
            exposures = [x for x in orig_exposure if x.get('subject')==subject and
                         x.get('event')=='open_outcomes' and x.get('scope')=='all indexed trials for this subject'
                         and x['split']==split and x['freeze_sha256']==pin[ofreeze] and set(FIELDS)<=set(x['fields'])]
            rs = [x for x in tables if x['subject']==subject]
        else:
            exposures = [x for x in pop_exposure if x.get('subject')==subject and
                         x.get('event')=='open_new_source_scored_outcomes' and
                         x['outcome_trial_interval']==[0,CAP] and x['freeze_sha256']==freeze_sha and
                         x['forecast_manifest_sha256']==scorepin]
            rs = [x for x in mixed if x['subject']==subject]
        check(bool(exposures), f'No matching prior exposure {subject}')
        rs.sort(key=lambda x:(x['date'],x['number']))
        check(len(rs)==len({(x['date'],x['number']) for x in rs}), f'Ambiguous chronology {subject}')
        offset = 0
        for r in rs:
            footer = counts[r['eid']] if earlier else r
            n = footer['rows']
            keys = ('eid','subject','lab','date','number','protocol')
            check(all(r[k]==footer[k] for k in keys) and r['lab']==lab and 'trainingChoiceWorld' in r['protocol'],
                  f'Chronology mismatch {r["eid"]}')
            if offset+n>CAP:
                break
            if n==0:
                continue
            if earlier:
                d = download[r['dataset_id']]
                check(all(r[k]==d[k] for k in (*keys,'path','dataset_id','split')) and r['split']==split,
                      f'Asset mismatch {r["eid"]}')
                assets = {'table': asset(d, OLD/r['path'])}
            else:
                names = ['table'] if 'table' in r['files'] else [f for f in FIELDS if f in r['files']]
                check(names==['table'] or set(FIELDS)-{'rewardVolume'}<=set(names), 'Required legacy fields')
                assets = {}
                for field in names:
                    d = filemeta[r['files'][field]]
                    check(all(r[k]==d[k] for k in keys) and d['rows']==n and d['field']==field, 'Asset metadata mismatch')
                    assets[field] = asset(d, ROOT/r['files'][field])
            sessions.append(dict(**{k:r[k] for k in keys}, start=offset, stop=offset+n,
                                 provenance_utc=exposures[0]['utc'], assets=assets))
            offset += n
        check(offset>=2200, f'Insufficient wholly allowed chronology {subject} {offset}')
    out = dict(utc=utc(), purpose='new development, previous exposure retained', subjects=ids, labs=ref['labs'],
               fields=FIELDS, maximum_rows_per_animal=CAP, sessions=sessions, metadata_sha256=META_PINS.copy(),
               counted_io=dict(BYTES))
    save('SOURCE_MANIFEST.json', out)
    return out


def decode(m, subjects, label):
    import duckdb
    con = duckdb.connect(config={'threads':1,'preserve_insertion_order':'true'})
    # Preflight every selected asset with opaque checksum, footer count and schema
    # before any projected trial column is decoded in this invocation.
    specs = []
    for s in m['sessions']:
        if s['subject'] not in subjects:
            continue
        n = s['stop']-s['start']
        for f,a in s['assets'].items():
            path = ROOT/a['path']
            blob(path,a['sha'],record=False)
            if f=='table':
                rows, = con.execute('SELECT num_rows FROM parquet_file_metadata(?)',[str(path)]).fetchone()
                cols = [x[0] for x in con.execute('DESCRIBE SELECT * FROM read_parquet(?)',[str(path)]).fetchall()]
                check(rows==n and set(FIELDS)-{'rewardVolume'}<=set(cols), f'Bad footer/schema {path}')
                BYTES['duckdb_nominal_whole_file_per_query'] += 3*a['size']
            else:
                with path.open('rb') as stream:
                    v = np.lib.format.read_magic(stream)
                    reader = {(1,0):np.lib.format.read_array_header_1_0,(2,0):np.lib.format.read_array_header_2_0}[v]
                    shape, _, dtype = reader(stream)
                    check(shape in ((n,),(n,1)) and not dtype.hasobject and stream.tell()+n*dtype.itemsize==a['size'],
                          f'Bad NPY header {path}')
                BYTES['numpy_nominal_read_including_header'] += a['size']
        specs.append(s)
    out = {subject:[] for subject in subjects}
    with (HERE/'EXPOSURE.jsonl').open('a') as log:
        for s in specs:
            n = s['stop']-s['start']
            paths = {f:str(ROOT/a['path']) for f,a in s['assets'].items()}
            event = dict(utc=utc(), action='open_previously_consumed_session_projection', subject=s['subject'],
                         eid=s['eid'], zero_based_half_open=[s['start'],s['stop']], fields=FIELDS,
                         sha256={k:a['sha'] for k,a in s['assets'].items()}, stage=label)
            log.write(json.dumps(event)+'\n')
            log.flush()
            if 'table' in paths:
                cols = [x[0] for x in con.execute('DESCRIBE SELECT * FROM read_parquet(?)',[paths['table']]).fetchall()]
                q = ','.join(f'"{f}"' if f in cols else f'NULL AS "{f}"' for f in FIELDS)
                a = np.asarray(con.execute(f'SELECT {q}, file_row_number FROM read_parquet(?, file_row_number=true) '
                                           'ORDER BY file_row_number LIMIT ?', [paths['table'],n]).fetchall(),dtype=float)
                check(np.array_equal(a[:,-1],np.arange(n)), f'Physical row order {s["eid"]}')
                a = a[:,:-1]
                BYTES['duckdb_nominal_whole_file_per_query'] += s['assets']['table']['size']
            else:
                cols = [np.load(paths[f],allow_pickle=False).reshape(n) if f in paths else np.full(n,np.nan) for f in FIELDS]
                a = np.column_stack(cols).astype(float)
            check(a.shape==(n,len(FIELDS)), f'Row count {s["eid"]}')
            check(np.isin(a[:,2],[-1,0,1]).all() and np.isin(a[:,3],[-1,0,1]).all(), f'Codes {s["eid"]}')
            check(not ((np.nan_to_num(a[:,0])>0)&(np.nan_to_num(a[:,1])>0)).any(), f'Bilateral {s["eid"]}')
            BYTES['projected_array_bytes'] += a.nbytes
            start = np.arange(n)==0
            out[s['subject']].append(np.column_stack([a,start]))
    return {k:np.concatenate(v) for k,v in out.items()}


def crosscheck(data, manifest):
    # Independently reproduce signed high-contrast numerator/denominator bins
    # whose entire 500 opportunities were within the newly read cap.
    pin = '8263da4c9f615d1040cd7b39d3bb327200bb727d2612c318564f5b5d393d0661'
    from io import BytesIO
    with np.load(BytesIO(blob(REV/'artifacts/source_comparison/COMPARISON_ARRAYS.npz',pin)),allow_pickle=False) as z:
        obs, counts, ids = z['observed'], z['counts'], list(z['subjects'])
    cells = 0
    for subject,a in data.items():
        i = ids.index(subject)
        for b,t in enumerate(range(1000,len(a)-499,500)):
            x = a[t:t+500]
            signed = np.nan_to_num(x[:,1])-np.nan_to_num(x[:,0])
            for j,c in enumerate((-1,1)):
                keep = signed==c
                n = int(keep.sum())
                check(n==counts[i,b,j] and np.isclose((x[keep,2]==-c).mean(),obs[i,b,j],atol=1e-15,rtol=0),
                      f'Reference bin mismatch {subject} {t} {c}')
                cells += 1
    return cells


def main(mode):
    begin = time.monotonic()
    ref = reference() if mode=='plan' else get(HERE/'REFERENCE.json')
    if mode=='plan':
        m = manifest(ref)
        print('Metadata verified',len(m['sessions']), 'sessions',
              sum(s['stop']-s['start'] for s in m['sessions']), 'rows', flush=True)
    else:
        m = get(HERE/'SOURCE_MANIFEST.json')
        check(m['subjects']==ref['roster'] and m['maximum_rows_per_animal']==CAP and
              tuple(m['fields'])==FIELDS, 'Manifest boundary')
        subjects = m['subjects'][:1]+m['subjects'][40:41] if mode=='pilot' else m['subjects']
        data = decode(m, subjects, mode)
        n = crosscheck(data,m)
        if mode=='all':
            np.savez_compressed(HERE/'CAPPED_ROWS.npz',**data)
        print('Scored reference exact100 cells',n, 'rows',sum(map(len,data.values())), flush=True)
        save(f'SOURCE_{mode.upper()}_EXECUTION.json',
             dict(utc=utc(), seconds=time.monotonic()-begin, rows={k:len(v) for k,v in data.items()}, exact100_cells=n,
                  counted_io=dict(BYTES), peak_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss))


if __name__=='__main__':
    main(sys.argv[1])
