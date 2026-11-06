"""Numerically decode only the predeclared random-policy source diagnostic people."""
import os
for k in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','VECLIB_MAXIMUM_THREADS'): os.environ[k]='2'
from collections import Counter
import gzip
import json
from pathlib import Path
import numpy as np
import scipy
from choose_cohort import epoch
ROOT=Path('/Users/vanshkumar/Documents/repos/devo-research-lab'); OUT=ROOT/'sources/memory_policy_transfer_2026-10-30'; TASK=ROOT/'lab/tasks/memory-policy-transfer-2026-10-30'
def main():
    co=json.loads((TASK/'COHORT.json').read_text()); users=json.loads((OUT/'selected_users.json').read_text()); meta=json.loads((OUT/'METADATA.json').read_text())
    data=np.load(OUT/'metadata_sorted.npy',allow_pickle=False)
    random_code=next(int(k) for k,v in meta['arms'].items() if v=='random')
    excluded=[]; groups={}
    starts=np.r_[0,1+np.flatnonzero(np.diff(data['uid'])),len(data)]
    for st,en in zip(starts[:-1],starts[1:]):
        a=data[st:en]; uid=int(a['uid'][0]); info=users[uid]
        if info['arms']!=[random_code] or len(info['installations'])!=1 or info['language_set']!=[['de','B']]: continue
        install=info['installations'][0]
        if not epoch('2020-03-01')<=install<epoch('2020-05-11') or a['time'][0]<install: continue
        a=a[(a['time']>=install)&(a['time']<install+21*86400)]
        if len(a)-len(np.unique(a['item']))<20 or np.any(np.diff(a['time'])<=0): continue
        prev={}; bad=0
        for r in a:
            q=int(r['item']); n=prev.get(q,0); bad+=int(int(r['count'])!=n+1); prev[q]=n+1
        if bad: excluded.append((info['hash'],uid,a))
    eligible=co['source_fit']+co['source_validation']
    chosen=[(users[p['uid']]['hash'],p['uid'],data[(data['uid']==p['uid'])&(data['time']>=p['installation'])&(data['time']<p['installation']+21*86400)]) for p in eligible]
    chosen+=sorted(excluded,key=lambda x:x[0])[:10]
    chosen_uids={uid for _,uid,_ in chosen}
    ordinals={int(r['ordinal']) for _,_,a in chosen for r in a}
    # Save exact authorised identities before opening the answer shard.
    (TASK/'SOURCE_FIELD_AUDIT_PEOPLE.json').write_text(json.dumps([{'hash':h,'uid':u,'rows':len(a),'eligible':u in {p['uid'] for p in eligible}} for h,u,a in chosen],indent=2)+'\n')
    y={}; difficulty={}; bytecount=0
    with gzip.open(OUT/('opaque_answers/arm_%02d.tsv.gz'%random_code),'rb') as f:
        for line in f:
            bytecount+=len(line); parts=line.rstrip(b'\n').split(b'\t'); ordinal=int(parts[0])
            if ordinal not in ordinals: continue
            value=float(parts[1])
            if value not in (0,1): raise RuntimeError('Nonbinary source correctness')
            y[ordinal]=int(value)
            try: difficulty[ordinal]=float(parts[2])
            except ValueError: difficulty[ordinal]=None
    if len(y)!=len(ordinals): raise RuntimeError('Missing authorised source rows')
    mode_relation=Counter(); count_increment=Counter(); firstcount=Counter(); seq_relation=Counter(); test_difference=[]; gap_people=Counter(); diff_by_item={}
    for h,uid,a in chosen:
        prev={}; gaps=0
        for r in a:
            ordinal=int(r['ordinal']); correct=y[ordinal]; item=int(r['item']); count=int(r['count']); seq=int(r['sequence'])
            mode=meta['modes'][str(int(r['mode']))]
            try:
                learn=float(mode[1]); mode_relation[(learn,correct)]+=1
                test_difference.append(int(r['time'])-(float(mode[0])+978307200))
            except ValueError: pass
            if item in prev:
                old_count,old_correct,old_seq=prev[item]
                inc=count-old_count; count_increment[(inc,old_correct,correct)]+=1; gaps+=int(inc!=1)
                seq_relation[(seq-old_seq,old_correct,correct)]+=1
            else: firstcount[count]+=1; gaps+=int(count!=1)
            prev[item]=(count,correct,seq)
            value=difficulty[ordinal]
            if value is not None: diff_by_item.setdefault(item,set()).add(value)
        gap_people['eligible' if uid in {p['uid'] for p in eligible} else 'excluded']+=gaps
    result={'source_people':len(chosen),'eligible_source_people':len(eligible),'excluded_semantics_people':len(chosen)-len(eligible),
            'source_correct_values_decoded':len(y),'source_answer_shard_bytes_streamed':bytecount,
            'target_correct_or_reply_values_decoded':0,'source_correct_rate_diagnostic_only':float(np.mean(list(y.values()))),
            'first_item_counts':dict(firstcount),'count_increment_previous_current':[{'increment':k[0],'previous_correct':k[1],'current_correct':k[2],'n':v} for k,v in count_increment.items()],
            'learn_correct_cross_table':[{'learn':k[0],'correct':k[1],'n':v} for k,v in mode_relation.items()],
            'test_timestamp_difference_quantiles_seconds':np.quantile(test_difference,[0,.1,.5,.9,1]).tolist(),
            'items_with_multiple_difficulty_values':sum(len(v)>1 for v in diff_by_item.values()),
            'difficulty_items':len(diff_by_item),'counter_mismatches_by_group':dict(gap_people),'scipy_version':scipy.__version__}
    (TASK/'SOURCE_FIELD_AUDIT.json').write_text(json.dumps(result,indent=2)+'\n')
    np.savez(OUT/'source_field_audit_answers.npz',ordinal=np.array(sorted(y),dtype='u8'),correct=np.array([y[i] for i in sorted(y)],dtype='u1'))
    print(json.dumps(result,indent=2))
if __name__=='__main__': main()
