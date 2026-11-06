"""Audit metadata and freeze the candidate-person plan before source answers."""
import os
for k in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','VECLIB_MAXIMUM_THREADS'):
    os.environ[k]='2'
from collections import Counter
import datetime as dt
import hashlib
import json
from pathlib import Path
import numpy as np
ROOT=Path('/Users/vanshkumar/Documents/repos/devo-research-lab')
OUT=ROOT/'sources/memory_policy_transfer_2026-10-30'
TASK=ROOT/'lab/tasks/memory-policy-transfer-2026-10-30'

def main():
    meta=json.loads((OUT/'METADATA.json').read_text())
    users=json.loads((OUT/'selected_users.json').read_text())
    data=np.concatenate([np.load(OUT/x['path'],allow_pickle=False) for x in meta['parts']])
    order=np.lexsort((data['ordinal'],data['time'],data['uid']))
    data=data[order]
    starts=np.r_[0,1+np.flatnonzero(np.diff(data['uid'])),len(data)]
    armcounts=Counter()
    firstcounts=Counter()
    offsetcounts=Counter()
    tie_users=set()
    records=[]
    for start,end in zip(starts[:-1],starts[1:]):
        a=data[start:end]
        uid=int(a['uid'][0])
        info=users[uid]
        days=np.unique(a['time']//86400)
        ties=int(np.sum(np.diff(a['time'])==0))
        if ties: tie_users.add(uid)
        prev={}
        offsets=Counter()
        first=Counter()
        gaps=0
        for row in a:
            item=int(row['item'])
            n=prev.get(item,0)
            val=int(row['count'])
            offsets[val-n]+=1
            if n==0: first[val]+=1
            prev[item]=n+1
        firstcounts.update(first)
        offsetcounts.update(offsets)
        armcounts.update(info['arms'])
        records.append({'uid':uid,'hash':info['hash'],'arms':info['arms'],
                        'installations':info['installations'],'language_set':info['language_set'],
                        'rows':len(a),'days':len(days),'first':int(a['time'][0]),'last':int(a['time'][-1]),
                        'repeats':len(a)-len(prev),'ties':ties,
                        'count_offset_top':offsets.most_common(4),'first_count_top':first.most_common(4)})
    dates=sorted(dt.datetime.strptime(Path(x['name']).stem[-8:],'%Y%m%d').date() for x in meta['members'] if x['name'].endswith('.csv'))
    dateset=set(dates)
    missing=[]
    day=dates[0]
    while day<=dates[-1]:
        if day not in dateset: missing.append(day.isoformat())
        day+=dt.timedelta(days=1)
    modecounts=np.bincount(data['mode'])
    topmodes=[{'rows':int(modecounts[i]),'test_string_length':len(meta['modes'][str(i)][0]),
               'learn_string_length':len(meta['modes'][str(i)][1])} for i in np.argsort(modecounts)[-10:][::-1]]
    catcounts=np.bincount(data['category'])
    topcats=[{'code':int(i),'rows':int(catcounts[i]),'value':meta['categories'][str(i)]} for i in np.argsort(catcounts)[-10:][::-1]]
    result={'rows':len(data),'users':len(records),'arms':meta['arms'],'users_by_arm_membership':dict(armcounts),
            'arm_row_counts_all':meta['arm_row_counts_all'],'mode_count':len(meta['modes']),'category_count':len(meta['categories']),
            'top_modes':topmodes,'top_categories':topcats,
            'first_count_hist':dict(firstcounts.most_common(20)),'count_offset_hist':dict(offsetcounts.most_common(20)),
            'missing_daily_files':missing,'ties_users':len(tie_users),
            'cumulative_archive_decoded_bytes':meta['cumulative_archive_decoded_bytes'],
            'stage':'metadata_only_no_answers'}
    (OUT/'PERSON_METADATA.json').write_text(json.dumps(records,separators=(',',':'))+'\n')
    (TASK/'METADATA_AUDIT.json').write_text(json.dumps(result,indent=2)+'\n')
    np.save(OUT/'metadata_sorted.npy',data,allow_pickle=False)
    print(json.dumps(result,indent=2))

if __name__=='__main__': main()
