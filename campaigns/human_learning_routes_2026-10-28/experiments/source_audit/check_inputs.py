"""Independent stimulus-only reconstruction. Never reads choice, feedback or RT."""
from pathlib import Path
import pandas as pd,numpy as np,json,hashlib
ROOT=Path(__file__).resolve().parent
CAMP=ROOT.parents[1]
d=pd.read_csv(CAMP/'outputs/input_only/trial_inputs.csv',dtype={'subject':str})
cols=['probabilityLeft','contrastLeft','contrastRight','stimSide']
schedules={}
source_records=[]
for i in range(10):
 p=ROOT/f'sources/pregen_sequence_{i}.xlsx'
 x=pd.read_excel(p).iloc[:600]
 side=np.where(x.eccentricity<0,1,-1)
 contrast=np.round(x.contrastDelta/.2,2).to_numpy()
 arr=np.column_stack([x.bias.to_numpy(),np.where(side==1,contrast,0),np.where(side==-1,contrast,0),side])
 schedules[i]=arr
 source_records.append(dict(task_sequence=i,bytes=p.stat().st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest(),first_biased_zero_index=int(np.flatnonzero(x.bias.to_numpy()!=.5)[0]),switches_zero_index=np.flatnonzero(x.bias.to_numpy()[1:]!=x.bias.to_numpy()[:-1]).astype(int).__add__(1).tolist()))
rows=[]
for sid,g in d.groupby('subject'):
 arr=g.sort_values('trial')[cols].to_numpy()
 matches=[i for i,s in schedules.items() if np.allclose(arr,s)]
 rows.append(dict(subject=sid,condition=int(g.instructions.iloc[0]),input_schedule=g.schedule.iloc[0],matched_task_sequence=matches[0] if len(matches)==1 else None,matches=len(matches),id_digit=int(sid[-1]),digit_match=len(matches)==1 and matches[0]==int(sid[-1])))
res=pd.DataFrame(rows);res.to_csv(ROOT/'schedule_mapping.csv',index=False)
(ROOT/'schedule_sources.json').write_text(json.dumps(source_records,indent=2))
metadata_path=CAMP/'inputs/participant_design_metadata.csv'
if not metadata_path.exists():
 metadata_path=CAMP.parents[1]/'sources/human_learning_feasibility_2026-10-28/participants_info.csv'
meta=pd.read_csv(metadata_path,usecols=['subject','instructions','session_start'],dtype={'subject':str})
meta['date']=meta.session_start.str[:10]
meta['expected_rule']=meta.subject.astype(int).mod(4).isin([1,2]).astype(int)
summary={'all80_exactly_match_one_source_sequence':bool((res.matches==1).all()),'digit_mismatches':res[~res.digit_match].to_dict('records'),'chronology':meta.groupby('instructions').date.agg(['min','max','count']).reset_index().to_dict('records'),'rule_exceptions':meta[meta.instructions!=meta.expected_rule][['subject','instructions','date']].to_dict('records'),'date_condition_counts':meta.groupby(['date','instructions']).size().reset_index(name='n').to_dict('records')}
(ROOT/'input_audit_summary.json').write_text(json.dumps(summary,indent=2))
print(json.dumps({k:v for k,v in summary.items() if k!='date_condition_counts'},indent=2))
