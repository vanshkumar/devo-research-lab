"""Outcome-blind support and exact-equivalence checks; no outcome field is stored.
Run from repo root: .venv/bin/python campaigns/target_event_carryover_2026-10-28/audits/design_challenge/input_only_challenge.py
"""
import csv
import hashlib
import json
from pathlib import Path
import numpy as np

ROOT = Path(__file__).resolve().parents[4]
OUT = Path(__file__).resolve().parent
SRC = ROOT / 'sources/learning_intervention_feasibility_2026-10-28'
ALLOW = ('SN', 'TN', 'clamp_size', 'tgt_jump_size')
report = {'outcome_access': 'No outcome values stored, computed, or printed. Only SN,TN,clamp_size,tgt_jump_size retained after CSV row parsing.', 'files': [], 'exact_equivalence': []}
all_schedules=[]
for name in ('tsay_TE_SPE.csv', 'tsay_controljump.csv'):
    path=SRC/name
    with path.open() as f:
        reader=csv.DictReader(f)
        rows=[{key:row[key] for key in ALLOW} for row in reader]
    people=sorted({int(row['SN']) for row in rows})
    out={'name':name, 'sha256':hashlib.sha256(path.read_bytes()).hexdigest(), 'horizons':[]}
    counts={h:{'all':0,'readout_nojump':0,'prior_nojump':0,'prior_and_readout_nojump':0,'all_future_nojump':0,'prior_and_all_future_nojump':0,'prior_nojump_by_index_and_clamp':{}} for h in range(1,6)}
    for p in people:
        seq=sorted([r for r in rows if int(r['SN'])==p],key=lambda r:int(r['TN']))
        tn=np.array([int(r['TN']) for r in seq])
        c=np.array([float(r['clamp_size']) for r in seq])
        j=np.array([float(r['tgt_jump_size']) for r in seq])
        assert np.array_equal(tn,np.arange(1,825))
        all_schedules.append((name,p,c,j))
        for t in range(100,824):
            loc=(t-100)%181
            if not 5<=loc<175 or c[t]!=0: continue
            for h,d in counts.items():
                d['all']+=1
                d['readout_nojump']+=int(j[t+h]==0)
                d['prior_nojump']+=int(j[t-1]==0)
                d['prior_and_readout_nojump']+=int(j[t-1]==0 and j[t+h]==0)
                d['all_future_nojump']+=int(np.all(j[t+1:t+h+1]==0))
                d['prior_and_all_future_nojump']+=int(j[t-1]==0 and np.all(j[t+1:t+h+1]==0))
                if j[t-1]==0:
                    key='index_jump=%d,prior_clamp=%g'%(j[t]!=0,c[t-1])
                    d['prior_nojump_by_index_and_clamp'][key]=d['prior_nojump_by_index_and_clamp'].get(key,0)+1
    out['horizons']=[{'horizon':h,**v} for h,v in counts.items()]
    out['main_input_cells']=sorted({(float(r['clamp_size']),float(r['tgt_jump_size'])) for r in rows if int(r['TN'])>100})
    report['files'].append(out)

# For each sign, compare varying retention with fixed storage plus nonnegative
# state-dependent perceived-error correction. Same inputs and readout in both.
# This is an exact model identity, not an empirical fit or recovery assessment.
for name,r0,r1 in [('suppression',.92,.78),('enhancement',.78,.92)]:
    a=.97
    maxdiff=0.
    maxstate=0.
    for source,p,c,j in all_schedules:
        xr=0.
        xp=0.
        for ci,ji in zip(c,j):
            event=int(ji!=0)
            retention=(r0,r1)[event]
            gain=.20
            # Matched flexible current input response; signed jump is included.
            current=gain*ci+.015*ji
            xr=retention*xr+current
            # x' = a*x + gain*(c-lambda[event]*x) + signed-jump term
            lam=(a-retention)/gain
            xp=a*xp+gain*(ci-lam*xp)+.015*ji
            maxdiff=max(maxdiff,abs(xr-xp))
            maxstate=max(maxstate,abs(xr))
    report['exact_equivalence'].append({'effect':name,'retention_nojump':r0,'retention_jump':r1,'fixed_storage_retention':a,'perceived_error_lambda_nojump':(a-r0)/.20,'perceived_error_lambda_jump':(a-r1)/.20,'maximum_absolute_path_difference_degrees':maxdiff,'maximum_absolute_state_degrees':maxstate,'schedules':len(all_schedules),'trials_per_schedule':824,'interpretation':'Same latent path and hence same likelihood under matched readout/noise; no oracle can distinguish these parameterizations on these inputs.'})
(OUT/'input_only_challenge.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({'counts':[{ 'name':x['name'],'horizons':[{k:v for k,v in h.items() if k!='prior_nojump_by_index_and_clamp'} for h in x['horizons']]} for x in report['files']], 'exact_equivalence':report['exact_equivalence']},indent=2))
