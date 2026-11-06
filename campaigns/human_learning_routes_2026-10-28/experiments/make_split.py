"""Lock split using only stimulus inputs and metadata; no behavioral reads."""
from pathlib import Path
import json, hashlib
import numpy as np
import pandas as pd
ROOT=Path(__file__).resolve().parents[1]
p=pd.read_csv(ROOT/'outputs/input_only/participants.csv',dtype={'subject':str,'session':str})
rng=np.random.default_rng(20261028)
prefix_schedule=p.loc[p.subject=='006','schedule'].iloc[0]
hold=sorted(rng.choice(sorted(set(p.schedule)-{prefix_schedule}),3,replace=False).tolist())
p['partition']='development'
p.loc[p.schedule.isin(hold),'partition']='validation_unseen_schedule'
for sch,s in p.loc[~p.schedule.isin(hold)].groupby('schedule',sort=True):
    for g in [0,1]:
        candidates=sorted(s.loc[(s.condition==g)&(s.subject!='006'),'subject'])
        chosen=rng.choice(candidates)
        p.loc[p.subject==chosen,'partition']='validation_seen_schedule'
assert p.loc[p.subject=='006','partition'].iloc[0]=='development'
assert p.loc[p.partition=='development'].groupby('schedule').condition.nunique().eq(2).all()
out=ROOT/'protocol/split_manifest.csv'
assert not out.exists(), 'Do not overwrite an existing frozen split'
p.to_csv(out,index=False)
manifest=dict(date='2026-10-28',seed=20261028,bit_generator='PCG64',unseen_schedules=hold,historical_prefix_subject='006',historical_prefix_forced_development=True,selection='Uniformly sample three complete schedules excluding prefix subject schedule; on each remaining schedule uniformly select one participant per condition excluding 006.',source_inputs_sha256=hashlib.sha256((ROOT/'outputs/input_only/trial_inputs.csv').read_bytes()).hexdigest(),split_sha256=hashlib.sha256(out.read_bytes()).hexdigest(),outcomes_inspected=False)
(ROOT/'protocol/SPLIT_LOCK.json').write_text(json.dumps(manifest,indent=2)+'\n')
print(json.dumps(manifest,indent=2))
print(p.groupby(['partition','condition']).size().to_string())
