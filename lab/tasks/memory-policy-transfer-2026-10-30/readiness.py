"""Outcome-blind support and cohort-size diagnostics; no answers opened."""
import os
for k in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','VECLIB_MAXIMUM_THREADS'): os.environ[k]='2'
from collections import Counter
import datetime as dt
import json
from pathlib import Path
import numpy as np
ROOT=Path('/Users/vanshkumar/Documents/repos/devo-research-lab'); OUT=ROOT/'sources/memory_policy_transfer_2026-10-30'; TASK=ROOT/'lab/tasks/memory-policy-transfer-2026-10-30'
def epoch(s): return int(dt.datetime.fromisoformat(s).replace(tzinfo=dt.timezone.utc).timestamp())
def features(a):
    prev={}; result=[]
    for k,r in enumerate(a):
        item=int(r['item']); when=int(r['time'])
        if item in prev:
            j,t,n=prev[item]
            delta=(when-t)/86400; other=k-j-1
            cell=(int(np.searchsorted([1/1440,1/24,1,7],delta)),int(np.searchsorted([1,2,4],n,side='left')),int(np.searchsorted([0,9,99],other,side='left')))
            result.append((delta,n,other,cell))
            prev[item]=(k,when,n+1)
        else: prev[item]=(k,when,1)
    return result

def main():
    meta=json.loads((OUT/'METADATA.json').read_text()); users=json.loads((OUT/'selected_users.json').read_text()); co=json.loads((TASK/'COHORT.json').read_text())
    data=np.load(OUT/'metadata_sorted.npy',allow_pickle=False)
    selected=co['source_fit']+co['source_validation']+co['targets']['smart']+co['targets']['spaced']
    support={}; counts=Counter(); perarm={}
    for group,people in [('source_fit',co['source_fit']),('source_validation',co['source_validation']),('smart',co['targets']['smart']),('spaced',co['targets']['spaced'])]:
        rows=[]; pc=[]
        for p in people:
            a=data[data['uid']==p['uid']]; a=a[(a['time']>=p['installation'])&(a['time']<p['installation']+21*86400)]
            f=features(a); rows.extend(f); pc.append(len(f))
        arr=np.array([x[:3] for x in rows],float) if rows else np.empty((0,3))
        c=Counter(x[3] for x in rows); support[group]=c
        perarm[group]={'people':len(people),'repeat_rows':len(rows),'per_person_repeats':pc,
                       'feature_quantiles':{name:np.quantile(arr[:,i],[0,.1,.5,.9,1]).tolist() if len(arr) else [] for i,name in enumerate(('delta_days','prior_seen','intervening_other'))},
                       'joint_cells':len(c)}
    source=support['source_fit']; supported={c for c,n in source.items() if n>=10}
    overlap={}
    for g in ('source_validation','smart','spaced'):
        count=sum(n for c,n in support[g].items() if c in supported)
        overlap[g]={'source_cell_minimum':10,'supported_repeat_rows':count,'fraction':count/max(1,perarm[g]['repeat_rows'])}
    # Diagnose whether the conservative window is causing the small cohort; do not change it.
    starts=np.r_[0,1+np.flatnonzero(np.diff(data['uid'])),len(data)]
    early=Counter(); stage=Counter(); repeats_by_stage={}
    for st,en in zip(starts[:-1],starts[1:]):
        a=data[st:en]; info=users[int(a['uid'][0])]
        if len(info['arms'])!=1 or len(info['installations'])!=1 or len(info['language_set'])!=1: continue
        arm=meta['arms'][str(info['arms'][0])]
        if arm not in ('random','smart','spaced') or tuple(info['language_set'][0])!=('de','B'): continue
        install=info['installations'][0]
        period='late' if epoch('2020-03-01')<=install<epoch('2020-05-11') else ('early' if epoch('2019-12-21')<=install<epoch('2020-01-24') else None)
        if not period or a['time'][0]<install: continue
        a=a[(a['time']>=install)&(a['time']<install+21*86400)]
        if not len(a): continue
        stage[(period,arm,'stable_window')]+=1
        n=len(a)-len(np.unique(a['item'])); repeats_by_stage.setdefault((period,arm),[]).append(n)
        if np.any(np.diff(a['time'])<=0): continue
        prev={}; bad=0
        for r in a:
            item=int(r['item']); k=prev.get(item,0)
            bad+=int(int(r['count'])!=k+1); prev[item]=k+1
        if bad: continue
        stage[(period,arm,'counter_complete')]+=1
        if n>=20 and len(np.unique(a['time']//86400))>=2: stage[(period,arm,'qualified')]+=1
    result={'outcome_blind':True,'global_item_ids_in_sample':len(meta['items_hashed']), 'cohort':perarm,'joint_support':overlap,
            'metadata_sensitivity_not_a_cohort_amendment':[{'period':k[0],'arm':k[1],'stage':k[2],'people':v} for k,v in stage.items()],
            'repeat_count_quantiles_stable_window':[{'period':k[0],'arm':k[1],'n':len(v),'quantiles':np.quantile(v,[0,.5,.9,1]).tolist()} for k,v in repeats_by_stage.items()]}
    (TASK/'READINESS.json').write_text(json.dumps(result,indent=2)+'\n'); print(json.dumps(result,indent=2))
if __name__=='__main__': main()
