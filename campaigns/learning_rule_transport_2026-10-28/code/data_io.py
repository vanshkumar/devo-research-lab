#!/usr/bin/env python3
"""Outcome-access boundary for the frozen learning-rule transport campaign.

No future holdout choices/rewards are loaded unless the caller supplies the
predeclared freeze file. External outcome access needs a separate gate file.
All trial rows, including omissions, remain in task-exposure chronology.
"""
from __future__ import annotations
import argparse, datetime as dt, hashlib, json, sys
from pathlib import Path
import numpy as np

CAMPAIGN=Path(__file__).resolve().parents[1]
ROOT=Path(__file__).resolve().parents[3]
SOURCE=ROOT/'sources/longitudinal_learning_feasibility_2026-10-28'
sys.path.insert(0,str(SOURCE/'tools'))

def _duckdb():
    # Only Parquet conversion needs the bundled CPython3.12 DuckDB extension.
    # Prepared NPZ loading remains available in the campaign's NumPy runtime.
    import duckdb
    return duckdb

FIELDS=['contrastLeft','contrastRight','choice','feedbackType','rewardVolume','probabilityLeft',
        'intervals_0','intervals_1','goCue_times','stimOn_times','firstMovement_times','response_times','feedback_times']

def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def exposure(event):
    with open(CAMPAIGN/'protocols/EXPOSURE.jsonl','a') as f:
        f.write(json.dumps({'utc':dt.datetime.now(dt.timezone.utc).isoformat(),**event},sort_keys=True)+'\n')

def split_info(subject):
    s=json.loads((CAMPAIGN/'protocols/SPLIT.json').read_text())
    for r in s['standard']:
        if r['subject']==subject:return r
    if subject in s['external_strict_prefix']:
        return dict(subject=subject,split='external',lab='wittenlab')
    raise ValueError('Not an eligible frozen subject: '+subject)

def subjects(split='dev'):
    x=json.loads((CAMPAIGN/'protocols/SPLIT.json').read_text())
    return x['external_strict_prefix'] if split=='external' else [r['subject'] for r in x['standard'] if r['split']==split]

def check_access(subject, split, freeze_path=None, external_gate_path=None):
    info=split_info(subject)
    if info['split']!=split:raise PermissionError(f'{subject} belongs to {info["split"]}, not {split}')
    if split in ['lab_holdout','animal_holdout']:
        if not freeze_path or not Path(freeze_path).is_file():
            raise PermissionError('Source validation requires explicit existing model/method freeze artifact')
    if split=='external':
        if not external_gate_path or not Path(external_gate_path).is_file():
            raise PermissionError('External outcomes sealed until source-performance gate artifact exists')
    return info

def subject_records(subject):
    rs=json.loads((CAMPAIGN/'data/INDEX.json').read_text())
    return sorted([r for r in rs if r['subject']==subject and r['kind']=='table'],key=lambda r:(r['date'],r['number']))

def prepare_subject(subject, split='dev', purpose='development preprocessing',freeze_path=None,external_gate_path=None):
    info=check_access(subject,split,freeze_path,external_gate_path)
    rs=subject_records(subject)
    if not rs:raise ValueError('No tables for '+subject)
    for r in rs:
        if not (CAMPAIGN/r['path']).is_file():raise FileNotFoundError(CAMPAIGN/r['path'])
    # Values are opened only after the access decision and logged before read.
    exposure(dict(event='open_outcomes',subject=subject,split=split,purpose=purpose,
                  scope='all indexed trials for this subject',fields=FIELDS,
                  freeze_sha256=sha256(freeze_path) if freeze_path else None,
                  external_gate_sha256=sha256(external_gate_path) if external_gate_path else None))
    con=_duckdb().connect()
    arrays={k:[] for k in FIELDS};session=[];starts=[];ends=[];day=[];rep=[];offsets=[0]
    meta=[]
    all_index=json.loads((CAMPAIGN/'data/INDEX.json').read_text())
    rep_map={r['eid']:r for r in all_index if r['kind']=='repNum'}
    for i,r in enumerate(rs):
        p=CAMPAIGN/r['path']
        columns=[v[0] for v in con.execute(f"DESCRIBE SELECT * FROM read_parquet('{p}')").fetchall()]
        select=','.join('"'+k+'"' if k in columns else 'NULL AS "'+k+'"' for k in FIELDS)
        rows=con.execute(f"SELECT {select} FROM read_parquet('{p}')").fetchall()
        a=np.asarray(rows,dtype=float)
        n=len(a)
        if n==0:continue
        for j,k in enumerate(FIELDS):arrays[k].append(a[:,j])
        session.append(np.full(n,i,dtype=np.int32))
        ss=np.zeros(n,dtype=bool);ss[0]=True; starts.append(ss)
        se=np.zeros(n,dtype=bool);se[-1]=True; ends.append(se)
        day.append(np.full(n,r['author_day'] if r['author_day'] is not None else i+1,dtype=np.int32))
        rp=rep_map.get(r['eid'])
        if rp and (CAMPAIGN/rp['path']).exists():
            rr=np.load(CAMPAIGN/rp['path'],allow_pickle=False).reshape(-1)
            if len(rr)!=n:raise ValueError('repNum/table mismatch '+r['eid'])
            rep.append(rr.astype(float))
        else:rep.append(np.full(n,np.nan))
        offsets.append(offsets[-1]+n)
        meta.append({k:r[k] for k in ['subject','lab','date','number','protocol','eid','dataset_id','path','author_day']})
    out={k:np.concatenate(v) for k,v in arrays.items()}
    for k in ['choice','feedbackType']:
        if not np.isfinite(out[k]).all():raise ValueError('Nonfinite categorical observations '+subject+' '+k)
        out[k]=out[k].astype(np.int8)
    if not np.isin(out['choice'],[-1,0,1]).all():raise ValueError('Unexpected choice code '+subject)
    out.update(session=np.concatenate(session),session_index=np.concatenate(session),
               session_start=np.concatenate(starts),session_end=np.concatenate(ends),
               start_of_session=np.concatenate(starts),day=np.concatenate(day),repNum=np.concatenate(rep),
               session_offsets=np.asarray(offsets,dtype=np.int64))
    # Metadata contains only chronology/provenance, not behavioral summaries.
    out['metadata_json']=np.array(json.dumps(dict(**info,sessions=meta),sort_keys=True))
    dest=CAMPAIGN/'data/processed'/split/(subject+'.npz');dest.parent.mkdir(parents=True,exist_ok=True)
    np.savez_compressed(dest,**out)
    return dest

def load_subject(subject,split='dev',permit_validation=False,purpose='development modeling',
                 freeze_path=None,external_gate_path=None):
    # Boolean alone deliberately does not grant validation outcome access.
    check_access(subject,split,freeze_path,external_gate_path)
    p=CAMPAIGN/'data/processed'/split/(subject+'.npz')
    if not p.exists():p=prepare_subject(subject,split,purpose,freeze_path,external_gate_path)
    exposure(dict(event='load_processed_outcomes',subject=subject,split=split,purpose=purpose,
                  path=str(p.relative_to(CAMPAIGN)),sha256=sha256(p)))
    with np.load(p,allow_pickle=False) as f:
        out={k:f[k] for k in f.files if k!='metadata_json'}
        out['metadata']=json.loads(str(f['metadata_json']))
    return out

def load_prefix_and_opportunities(subject,split,prefix_n=1000,horizon=5000,
                                  freeze_path=None,external_gate_path=None,
                                  purpose='prospective prefix calibration and opportunity conditioning'):
    """Read only permitted prefix outcomes and future opportunity boundaries.

    Future row counts come from the pinned Parquet footer audit. No future
    contrast, choice, feedback, reward, repeat number or probability is loaded
    into the returned forecast inputs. Source validation and external access
    retain their explicit method-freeze/transfer-gate requirements.

    Returns ``(prefix, future_session_start, metadata)``. For short histories,
    metadata declares the available prefix/future lengths; no animal is
    selected on future competence. Future boundaries are realized exposure,
    so resulting forecasts are conditional on opportunities, not calendar time.
    """
    info=check_access(subject,split,freeze_path,external_gate_path)
    rs=subject_records(subject)
    if not rs:raise ValueError('No tables for '+subject)
    row_path=CAMPAIGN/'data/ROW_COUNTS.json'
    if not row_path.exists():raise FileNotFoundError('Run footer-only coverage first: '+str(row_path))
    row_meta={r['eid']:int(r['rows']) for r in json.loads(row_path.read_text())}
    if any(r['eid'] not in row_meta for r in rs):raise ValueError('Missing pinned footer counts for '+subject)
    sizes=[row_meta[r['eid']] for r in rs]
    total=sum(sizes);take=min(int(prefix_n),total)
    future_length=min(int(horizon),max(0,total-int(prefix_n)))
    future_starts=np.zeros(future_length,dtype=bool)
    offset=0
    for n in sizes:
        if int(prefix_n)<=offset<int(prefix_n)+future_length:
            future_starts[offset-int(prefix_n)]=True
        offset+=n
    exposure(dict(event='open_prefix_only_outcomes',subject=subject,split=split,purpose=purpose,
                  outcome_trial_interval=[0,take],outcome_fields=FIELDS,
                  future_inputs='session starts from pinned footer row counts only',
                  future_outcomes_read=False,requested_prefix=int(prefix_n),future_opportunities=future_length,
                  freeze_sha256=sha256(freeze_path) if freeze_path else None,
                  external_gate_sha256=sha256(external_gate_path) if external_gate_path else None))
    con=_duckdb().connect();arrays={k:[] for k in FIELDS}
    sessions=[];starts=[];ends=[];days=[];rep=[];offsets=[0];read_meta=[]
    all_index=json.loads((CAMPAIGN/'data/INDEX.json').read_text())
    rep_map={r['eid']:r for r in all_index if r['kind']=='repNum'}
    remaining=take
    for i,(r,full_n) in enumerate(zip(rs,sizes)):
        if remaining<=0:break
        n=min(remaining,full_n);remaining-=n
        if n==0:continue
        p=CAMPAIGN/r['path']
        columns=[v[0] for v in con.execute(f"DESCRIBE SELECT * FROM read_parquet('{p}')").fetchall()]
        select=','.join('"'+k+'"' if k in columns else 'NULL AS "'+k+'"' for k in FIELDS)
        rows=con.execute(f"SELECT {select} FROM read_parquet('{p}') LIMIT {n}").fetchall()
        a=np.asarray(rows,dtype=float)
        if len(a)!=n:raise ValueError('Footer/prefix row count discrepancy '+r['eid'])
        for j,k in enumerate(FIELDS):arrays[k].append(a[:,j])
        sessions.append(np.full(n,i,dtype=np.int32))
        ss=np.zeros(n,dtype=bool);ss[0]=True;starts.append(ss)
        se=np.zeros(n,dtype=bool);se[-1]=n==full_n;ends.append(se)
        days.append(np.full(n,r['author_day'] if r['author_day'] is not None else i+1,dtype=np.int32))
        rr=rep_map.get(r['eid'])
        if rr and (CAMPAIGN/rr['path']).exists():
            # Header and selected prefix elements only; no future repeat flags.
            mm=np.load(CAMPAIGN/rr['path'],allow_pickle=False,mmap_mode='r').reshape(-1)
            if len(mm)!=full_n:raise ValueError('repNum/footer mismatch '+r['eid'])
            rep.append(np.asarray(mm[:n],dtype=float).copy())
        else:rep.append(np.full(n,np.nan))
        offsets.append(offsets[-1]+n)
        read_meta.append({**{k:r[k] for k in ['date','number','protocol','eid','dataset_id','path','author_day']},
                          'prefix_rows_read':n,'total_rows_from_footer':full_n})
    if take==0:raise ValueError('Empty prefix '+subject)
    prefix={k:np.concatenate(v) for k,v in arrays.items()}
    for k in ['choice','feedbackType']:
        if not np.isfinite(prefix[k]).all():raise ValueError('Nonfinite prefix categorical observation '+subject)
        prefix[k]=prefix[k].astype(np.int8)
    if not np.isin(prefix['choice'],[-1,0,1]).all():raise ValueError('Unexpected prefix choice code '+subject)
    prefix.update(session=np.concatenate(sessions),session_index=np.concatenate(sessions),
                  session_start=np.concatenate(starts),start_of_session=np.concatenate(starts),
                  session_end=np.concatenate(ends),day=np.concatenate(days),repNum=np.concatenate(rep),
                  session_offsets=np.asarray(offsets,dtype=np.int64))
    metadata=dict(**info,prefix_n_requested=int(prefix_n),prefix_n_available=take,
                  future_horizon_requested=int(horizon),future_opportunities_available=future_length,
                  indexed_total_trials=total,prefix_complete=total>=prefix_n,
                  horizon_complete=total>=prefix_n+horizon,
                  session_sizes_from_footer=sizes,session_dates=[r['date'] for r in rs],
                  prefix_outcome_source_records=read_meta,future_outcomes_read=False,
                  conditioned_on_realized_opportunities=True,row_counts_sha256=sha256(row_path))
    prefix['metadata']=metadata
    return prefix,future_starts,metadata

def coverage():
    """Read Parquet row-count metadata only, with no column values."""
    index=json.loads((CAMPAIGN/'data/INDEX.json').read_text())
    con=_duckdb().connect();rows=[]
    for r in index:
        if r['kind']!='table':continue
        p=CAMPAIGN/r['path']
        if not p.exists():continue
        n=int(con.execute(f"SELECT sum(num_rows) FROM parquet_file_metadata('{p}')").fetchone()[0])
        rows.append({**{k:r[k] for k in ['subject','split','lab','date','number','protocol','eid','author_day']},'rows':n})
    (CAMPAIGN/'data/ROW_COUNTS.json').write_text(json.dumps(rows,indent=2)+'\n')
    summary=[]
    for subject in sorted(set(r['subject'] for r in rows)):
        rr=[r for r in rows if r['subject']==subject]
        summary.append(dict(subject=subject,split=rr[0]['split'],lab=rr[0]['lab'],sessions=len(rr),
                            trials=sum(r['rows'] for r in rr),session_trials=[r['rows'] for r in rr],
                            protocols=sorted(set(r['protocol'] for r in rr))))
    (CAMPAIGN/'data/COVERAGE.json').write_text(json.dumps(summary,indent=2)+'\n')
    exposure(dict(event='footer_rowcount_coverage',files=len(rows),outcomes_read=False))
    return summary

def main():
    parser=argparse.ArgumentParser(); parser.add_argument('--prepare-dev',action='store_true');parser.add_argument('--coverage',action='store_true');parser.add_argument('--subject')
    args=parser.parse_args()
    if args.coverage:
        rr=coverage();print('metadata coverage',len(rr),'animals',sum(r['trials'] for r in rr),'task trials')
    if args.prepare_dev:
        for subject in subjects('dev'):
            try:
                p=prepare_subject(subject);print(subject,str(p),flush=True)
            except FileNotFoundError as e:print('pending',subject,flush=True)
    if args.subject:print(prepare_subject(args.subject))

if __name__=='__main__':main()
