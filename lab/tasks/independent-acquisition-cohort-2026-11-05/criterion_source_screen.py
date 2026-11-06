"""Source-only necessary-criterion screen; original74<=6000, no new eval I/O."""
from collections import Counter
from datetime import datetime,timezone
import hashlib,io,json,resource,time
from pathlib import Path
import numpy as np

HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[2]
OLD=HERE.parent/'acquisition-rule-vs-tracker-2026-11-05'
cpu,wall=time.process_time(),time.monotonic();IO=Counter();PINS={}


def read(p):
    b=p.read_bytes();IO['explicit_reads']+=len(b);PINS[p.name]=dict(bytes=len(b),sha256=hashlib.sha256(b).hexdigest());return b


def necessary(blocks):
    n=[len(a) for a in blocks]
    easy=[];zero=False
    for a in blocks:
        x=100*(np.nan_to_num(a[:,1])-np.nan_to_num(a[:,0]));keep=np.abs(x)>=50
        easy.append(float(np.mean(a[keep,3]==1)) if keep.any() else 0.)
        zero|=bool(np.any(x==0))
    return bool(len(blocks)==3 and min(n)>200 and min(easy)>.8 and zero),dict(n=n,easy=easy,zero=zero)


manifest=json.loads(read(OLD/'SOURCE_FIT6000_MANIFEST.json'))
assert manifest['maximum_fit_rows']==6000 and len(manifest['subjects'])==74
event=dict(utc=datetime.now(timezone.utc).isoformat(),event='source_only_established_criterion_screen',
           subjects=manifest['subjects'],maximum_rows=6000,fields=manifest['fields']+['session_start'],
           boundary='Prepared original74 cache only, original prior consumption retained; no evaluation or protected payload')
with (HERE/'EXPOSURE.jsonl').open('a') as f:f.write(json.dumps(event)+'\n')
with np.load(io.BytesIO(read(OLD/'TRAIN6000_ROWS.npz')),allow_pickle=False) as z:raw={k:z[k] for k in z.files}
IO['decoded_array_bytes']+=sum(a.nbytes for a in raw.values())
assert set(raw)==set(manifest['subjects'])
out=[]
for s in manifest['subjects']:
    a=raw[s];assert len(a)<=6000 and a.shape[1]==7
    rs=sorted([r for r in manifest['sessions'] if r['subject']==s],key=lambda r:(r['date'],r['number']))
    complete=[r for r in rs if r['stop']<=len(a)]
    sessions=[];days=[];lastdate=None
    for r in complete:
        part=a[r['start']:r['stop']];sessions.append(part)
        if r['date']==lastdate:days[-1]=np.concatenate([days[-1],part])
        else:days.append(part);lastdate=r['date']
    for grouping,blocks in [('session',sessions),('calendar_day',days)]:
        offset=0;windows=[]
        for j,b in enumerate(blocks):
            offset+=len(b)
            if j<2:continue
            can,details=necessary(blocks[j-2:j+1])
            windows.append(dict(end=offset,necessary_1a_pass=can,details=details))
        for h in [3000,4000,6000]:
            done=[r for r in windows if r['end']<=h]
            good=[r for r in done if r['necessary_1a_pass']]
            out.append(dict(subject=s,grouping=grouping,horizon=h,available_selected_rows=len(a),
                 complete_sessions=len(complete),complete_days=len(days),windows_checked=len(done),
                 necessary_pass_windows=good,can_have_trained1a=bool(good),
                 interpretation='A necessary-condition upper screen ONLY: psychometric bias/threshold/lapse may still fail. Session ends only; capped partial boundary session excluded.'))
summary=[]
for grouping in ['session','calendar_day']:
    for h in [3000,4000,6000]:
        rr=[r for r in out if r['grouping']==grouping and r['horizon']==h]
        summary.append(dict(grouping=grouping,horizon=h,subjects=74,
               source_subjects_with_necessary_pass=sum(r['can_have_trained1a'] for r in rr),
               source_subjects_with_three_complete_units=sum(r['windows_checked']>0 for r in rr),
               source_subjects_with_selected_rows_through_h=sum(r['available_selected_rows']>=h for r in rr)))
result=dict(utc=datetime.now(timezone.utc).isoformat(),summary=summary,rows=out,
       definition_source='IBL_TRAINING_CRITERIA.py criterion_1a and compute_training_info; no RT requirement for1a.1b requires unmodeled RT.',
       no_event_claim='Necessary-pass counts are upper bounds, not actual criterion attainments, first-passage probabilities, power or meaningful negative biological results.',
       io=dict(IO),pins=PINS,cpu_seconds=time.process_time()-cpu,process_wall_seconds=time.monotonic()-wall,
       peak_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
(HERE/'CRITERION_SOURCE_SCREEN.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({k:v for k,v in result.items() if k not in ['rows','pins']},indent=2))
