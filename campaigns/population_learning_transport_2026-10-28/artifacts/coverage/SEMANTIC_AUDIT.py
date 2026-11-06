#!/usr/bin/env python3
"""Native-choice, feedback and session chronology audit on already exposed rows.

Read only first4000rows for24primary animals and first3000rows forNYU21.
No mixed_reader imports, external values, SWC_007 values or later rows.
"""
from pathlib import Path
import datetime as dt,hashlib,json,sys
import numpy as np
ROOT=Path(__file__).resolve().parents[4]
C=ROOT/'campaigns/population_learning_transport_2026-10-28'
OUT=C/'artifacts/coverage'
sys.dont_write_bytecode=True
sys.path.insert(0,str(ROOT/'sources/longitudinal_learning_feasibility_2026-10-28/tools'))
import duckdb
FIELDS=('contrastLeft','contrastRight','choice','feedbackType','intervals_0','intervals_1')

def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def log(event):
    with (C/'protocols/EXPOSURE.jsonl').open('a') as f:f.write(json.dumps(dict(utc=dt.datetime.now(dt.timezone.utc).isoformat(),**event),sort_keys=True)+'\n')
def values(record,n,con):
    files=record['files'];a={}
    if record['format']=='parquet':
        rows=con.execute(f"SELECT {','.join(FIELDS)} FROM read_parquet(?) LIMIT {int(n)}",[str(ROOT/files['table'])]).fetchall()
        rows=np.asarray(rows,dtype=float)
        for j,k in enumerate(FIELDS):a[k]=rows[:,j]
    else:
        for k in FIELDS:
            field='intervals' if k.startswith('intervals_') else k
            array=np.load(ROOT/files[field],allow_pickle=False,mmap_mode='r')
            a[k]=np.array(array[:n,int(k[-1])] if field=='intervals' else array[:n],dtype=float).reshape(n)
    assert all(len(v)==n for v in a.values())
    return a

def main():
    gate=json.loads((C/'protocols/SOURCE_GATE.json').read_text())
    if sha(C/'artifacts/results/SOURCE_RESULT.json')!=gate['result_sha256']:raise PermissionError('Source scoring must be complete and pinned')
    manifest=json.loads((OUT/'BYTE_MANIFEST.json').read_text())
    by_path={r['path']:r for r in manifest}
    sessions=json.loads((OUT/'SESSIONS.json').read_text())
    dispositions=json.loads((OUT/'RESULT.json').read_text())['summaries']
    limits={s['subject']:4000 for s in dispositions if s['primary_complete']};limits['NYU-21']=3000
    assert len(limits)==25 and 'SWC_007' not in limits
    con=duckdb.connect();records=[];animals=[];anomalies=[];by_format={}
    for subject,limit in sorted(limits.items()):
        selected=[r for r in sessions if r['subject']==subject]
        keys=[(r['date'],r['number'],r['eid']) for r in selected]
        if len(keys)!=len(set(keys)):raise ValueError('Duplicated session in selected chronology')
        selected.sort(key=lambda r:(r['date'],r['number'],r['eid']))
        log(dict(event='independent_semantic_audit_access',subject=subject,outcome_trial_interval=[0,limit],fields=list(FIELDS),scope='already exposed source rows only'))
        pieces=[];remaining=limit;offset=0;starts=[];resets=[];unique_source=[]
        for r in selected:
            n=min(r['rows'],remaining)
            if n<=0:break
            used_fields=['table'] if r['format']=='parquet' else ['choice','contrastLeft','contrastRight','feedbackType','intervals']
            for key in used_fields:
                path=r['files'][key];pin=by_path[path]
                if sha(ROOT/path)!=pin['sha256']:raise RuntimeError('Original file hash changed')
            a=values(r,n,con)
            signed=np.nan_to_num(a['contrastRight'])-np.nan_to_num(a['contrastLeft'])
            choice=a['choice'];feedback=a['feedbackType'];rewarded=feedback>0
            nonzero=np.isfinite(signed)&(signed!=0)&(choice!=0)
            correct=(choice==-np.sign(signed))
            disagree=nonzero&(correct!=rewarded)
            omitted=(choice==0)
            st,en=a['intervals_0'],a['intervals_1']
            finite_interval=np.isfinite(st)&np.isfinite(en)
            negduration=finite_interval&(en<st)
            startdiff=np.diff(st);enddiff=np.diff(en)
            startdecrease=np.isfinite(startdiff)&(startdiff<0)
            enddecrease=np.isfinite(enddiff)&(enddiff<0)
            duplicate_pairs=int(sum(np.array_equal((st[i],en[i]),(st[i-1],en[i-1])) for i in range(1,n)))
            both_present=np.isfinite(a['contrastLeft'])&np.isfinite(a['contrastRight'])
            if pieces:
                previous=pieces[-1]
                resets.append(dict(previous_eid=unique_source[-1],next_eid=r['eid'],row_boundary=offset,previous_end=float(previous['intervals_1'][-1]),next_start=float(st[0]),timestamp_resets=bool(st[0]<previous['intervals_0'][-1])))
            info=dict(subject=subject,eid=r['eid'],date=r['date'],session_number=r['number'],format=r['format'],rows_read=n,total_rows_from_metadata=r['rows'],concatenated_interval=[offset,offset+n],native_choice_counts={str(v):int((choice==v).sum()) for v in np.unique(choice)},feedback_counts={str(v):int((feedback==v).sum()) for v in np.unique(feedback)},nonzero_responding_trials=int(nonzero.sum()),feedback_correctness_disagreements=int(disagree.sum()),omissions=int(omitted.sum()),rewarded_omissions=int((omitted&rewarded).sum()),nonfinite_choice=int((~np.isfinite(choice)).sum()),nonfinite_feedback=int((~np.isfinite(feedback)).sum()),finite_interval_rows=int(finite_interval.sum()),negative_duration_rows=int(negduration.sum()),start_decreases=int(startdecrease.sum()),end_decreases=int(enddecrease.sum()),duplicate_adjacent_interval_pairs=duplicate_pairs,both_contrast_columns_present=int(both_present.sum()),signed_values=sorted(np.unique(signed).tolist()))
            if info['feedback_correctness_disagreements'] or info['rewarded_omissions'] or info['nonfinite_choice'] or info['nonfinite_feedback'] or info['negative_duration_rows'] or info['start_decreases'] or info['end_decreases'] or duplicate_pairs:
                anomalies.append(info)
            total=by_format.setdefault(r['format'],dict(rows=0,nonzero_responding_trials=0,feedback_correctness_disagreements=0,omissions=0,rewarded_omissions=0,nonfinite_interval_rows=0,negative_duration_rows=0,start_decreases=0,end_decreases=0,duplicate_adjacent_interval_pairs=0,choice_values=set(),feedback_values=set()))
            for k in ('nonzero_responding_trials','feedback_correctness_disagreements','omissions','rewarded_omissions','negative_duration_rows','start_decreases','end_decreases','duplicate_adjacent_interval_pairs'):total[k]+=info[k]
            total['rows']+=n;total['nonfinite_interval_rows']+=n-int(finite_interval.sum());total['choice_values'].update(choice.tolist());total['feedback_values'].update(feedback.tolist())
            records.append(info);pieces.append(a);starts.append(offset);unique_source.append(r['eid']);offset+=n;remaining-=n
        assert remaining==0 and len(unique_source)==len(set(unique_source))
        concatenated={k:np.concatenate([p[k] for p in pieces]) for k in FIELDS}
        actual_starts=np.zeros(limit,dtype=bool);actual_starts[starts]=True
        folder=C/'artifacts/forecasts/source'
        prefix_matches={}
        with np.load(folder/(subject+'__prefix.npz'),allow_pickle=False) as z:
            for k in FIELDS:prefix_matches[k]=bool(np.array_equal(z[k],concatenated[k][:1000],equal_nan=True))
            prefix_matches['session_start']=bool(np.array_equal(z['session_start'],actual_starts[:1000]))
            future_match=bool(np.array_equal(z['future_session_start'],actual_starts[1000:]))
        forecast_boundaries={}
        for kind in ('rnn','growth','persistence'):
            with np.load(folder/(subject+'__'+kind+'.npz'),allow_pickle=False) as z:forecast_boundaries[kind]=bool(np.array_equal(z['session_start'],actual_starts[1000:]))
        if not all(prefix_matches.values()) or not future_match or not all(forecast_boundaries.values()):raise AssertionError('Prefix/future chronology or source field mismatch '+subject)
        animals.append(dict(subject=subject,rows_read=limit,sessions_read=len(pieces),unique_session_ids=True,prefix_fields_exact_match=prefix_matches,prefix_future_starts_match=future_match,forecast_future_starts_match=forecast_boundaries,session_boundaries=starts,between_session_resets=resets))
    for v in by_format.values():
        v['choice_values']=sorted(v['choice_values']);v['feedback_values']=sorted(v['feedback_values'])
    result=dict(utc=dt.datetime.now(dt.timezone.utc).isoformat(),status='passed' if not anomalies else 'anomalies_present',scope='already exposed rows only;24primary×4000 plusNYU21×3000;SWC007/external/later source rows sealed',rows=sum(limits.values()),subjects=25,sessions=len(records),by_format=by_format,anomalies=anomalies,animals=animals,session_records=records,source_code_sha256=sha(__file__),source_result_sha256=gate['result_sha256'],native_choice_rule='choice+1 left,-1 right,0 omission; nonzero correct iffchoice=-sign(contrastRight−contrastLeft); rewards checked independently against feedbackType>0',interval_rule='Within each indexed session starts and ends must not decrease and end≥start; between-session clock resets are expected and preserved',future_boundary_verification='Exact comparison of original-byte session concatenation to saved prefix flags and allforecast session-start vectors; no cross-session timestamp sorting')
    (OUT/'SEMANTIC_AUDIT.json').write_text(json.dumps(result,indent=2)+'\n')
    log(dict(event='independent_semantic_audit_complete',status=result['status'],rows=result['rows'],subjects=25,result_sha256=sha(OUT/'SEMANTIC_AUDIT.json')))
    print(json.dumps({k:v for k,v in result.items() if k not in ('animals','session_records','anomalies')},indent=2))
    if anomalies:print(json.dumps(anomalies,indent=2))

if __name__=='__main__':main()
