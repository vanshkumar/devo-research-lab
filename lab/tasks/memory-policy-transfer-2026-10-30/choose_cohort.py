"""Select coherent fixed-window learners using metadata only."""
import os
for k in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','VECLIB_MAXIMUM_THREADS'): os.environ[k]='2'
from collections import Counter
import datetime as dt
import hashlib
import json
from pathlib import Path
import numpy as np
ROOT=Path('/Users/vanshkumar/Documents/repos/devo-research-lab')
OUT=ROOT/'sources/memory_policy_transfer_2026-10-30'
TASK=ROOT/'lab/tasks/memory-policy-transfer-2026-10-30'

def epoch(date): return int(dt.datetime.fromisoformat(date).replace(tzinfo=dt.timezone.utc).timestamp())
def main():
    if (TASK/'COHORT.json').exists(): raise RuntimeError('Cohort already frozen')
    users=json.loads((OUT/'selected_users.json').read_text())
    meta=json.loads((OUT/'METADATA.json').read_text())
    data=np.load(OUT/'metadata_sorted.npy',allow_pickle=False)
    starts=np.r_[0,1+np.flatnonzero(np.diff(data['uid'])),len(data)]
    exclusions=Counter(); candidates=[]; context_counts=Counter(); state_counts=Counter()
    for st,en in zip(starts[:-1],starts[1:]):
        a=data[st:en]; uid=int(a['uid'][0]); info=users[uid]
        if len(info['arms'])!=1: exclusions['multiple_arms']+=1; continue
        arm=meta['arms'][str(info['arms'][0])]
        if arm not in ('random','smart','spaced'): exclusions['unrecognised_policy']+=1; continue
        if len(info['installations'])!=1: exclusions['multiple_installations']+=1; continue
        install=info['installations'][0]
        if not epoch('2020-03-01')<=install<epoch('2020-05-11'): exclusions['installation_outside_gap_free_window']+=1; continue
        if len(info['language_set'])!=1: exclusions['multiple_language_or_set']+=1; continue
        if a['time'][0]<install: exclusions['preinstallation_records']+=1; continue
        a=a[(a['time']>=install)&(a['time']<install+21*86400)]
        if not len(a): exclusions['no_window_rows']+=1; continue
        if np.any(np.diff(a['time'])<=0): exclusions['timestamp_ties']+=1; continue
        prev={}; mismatches=0; repeats=0
        for r in a:
            item=int(r['item']); n=prev.get(item,0)
            if int(r['count']) != n+1: mismatches+=1
            repeats+=int(n>0); prev[item]=n+1
        state_counts[(arm,'checked')]+=1
        if mismatches: exclusions['item_counter_gap_or_left_truncation']+=1; continue
        if repeats<20 or len(np.unique(a['time']//86400))<2:
            exclusions['fewer_than_20_repeats_or_two_days']+=1; continue
        context=tuple(info['language_set'][0]); context_counts[(arm,context)]+=1
        candidates.append({'uid':uid,'hash':info['hash'],'arm':arm,'context':list(context),'installation':install,
                           'rows':len(a),'repeats':repeats,'first':int(a['time'][0]),'last':int(a['time'][-1]),
                           'days':len(np.unique(a['time']//86400))})
    random_context=Counter(tuple(x['context']) for x in candidates if x['arm']=='random')
    if not random_context:
        raise RuntimeError('No random-policy candidates satisfy complete-window rules')
    context=random_context.most_common(1)[0][0]
    pools={a:sorted([x for x in candidates if x['arm']==a and tuple(x['context'])==context],key=lambda x:x['hash']) for a in ('random','smart','spaced')}
    fit=[]; validation=[]
    for x in pools['random']:
        if int(x['hash'][8:16],16)%4==0: validation.append(x)
        else: fit.append(x)
    fit=fit[:600]; validation=validation[:250]
    targets={a:pools[a][:600] for a in ('smart','spaced')}
    result={'frozen_before_any_answer_analysis':True,'selection':'SHA256 bucket 0 mod 8; stable arm/install/context; install March 1 through May 10; first 21 days; strictly increasing times; every item count equals local exposure number starting at 1; >=20 repeat events on >=2 UTC days',
            'source_context':list(context),'source_fit':fit,'source_validation':validation,'targets':targets,
            'exclusions':dict(exclusions),'all_candidate_counts':{a:len(pools[a]) for a in pools},
            'context_counts':[{'arm':k[0],'context':list(k[1]),'people':v} for k,v in context_counts.items()],
            'source_split':'hash digits 8:16 mod 4 = 0 validation, otherwise fit; sorted hash caps 600/250; target caps 600 each',
            'observation_end':'2020-05-31','horizon_days':21,'answer_values_analysed':0}
    (TASK/'COHORT.json').write_text(json.dumps(result,indent=2)+'\n')
    summary={k:result[k] for k in ('selection','source_context','exclusions','all_candidate_counts','context_counts')}
    summary['selected']={'source_fit':len(fit),'source_validation':len(validation),**{a:len(v) for a,v in targets.items()}}
    summary['repeat_events']={'source_fit':sum(x['repeats'] for x in fit),'source_validation':sum(x['repeats'] for x in validation),**{a:sum(x['repeats'] for x in v) for a,v in targets.items()}}
    (TASK/'COHORT_SUMMARY.json').write_text(json.dumps(summary,indent=2)+'\n')
    print(json.dumps(summary,indent=2))

if __name__=='__main__': main()
