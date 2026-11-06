"""Checksum acquisition and inspect inputs only; never read choices/feedback/RT."""
from pathlib import Path
import hashlib, json, sys
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / 'inputs/processed_data_2026.csv'
EXPECTED = '5bc8ccf8bdca2e89fc21d20ffb7c1695'
raw_md5 = hashlib.md5(RAW.read_bytes()).hexdigest()
assert raw_md5 == EXPECTED, (raw_md5, EXPECTED)
cols = ['subject', 'session', 'trial', 'probabilityLeft', 'contrastLeft', 'contrastRight', 'stimContrast', 'sideContrast', 'stimSide', 'instructions']
d = pd.read_csv(RAW, usecols=cols, dtype={'subject':str, 'session':str}).sort_values(['subject','trial'])
assert not d.duplicated(['subject','trial']).any()
metadata_path=ROOT/'inputs/participant_design_metadata.csv'
if not metadata_path.exists():metadata_path=ROOT.parents[1] / 'sources/human_learning_feasibility_2026-10-28/participants_info.csv'
meta = pd.read_csv(metadata_path, usecols=['subject','instructions','session_start'],dtype={'subject':str})
signatures = {}
rows = []
for subject,s in d.groupby('subject',sort=True):
    assert len(s)==600 and np.array_equal(s.trial.values,np.arange(600))
    assert s.session.nunique()==s.instructions.nunique()==1
    arr=s[['probabilityLeft','contrastLeft','contrastRight','stimSide']].to_numpy(dtype='<f8')
    key=hashlib.sha256(arr.tobytes()).hexdigest()
    if key not in signatures: signatures[key]=f'S{len(signatures)+1:02d}'
    sch=signatures[key]
    p=s.probabilityLeft.to_numpy()
    switches=np.where((p[1:]!=p[:-1]) & (p[1:]!=.5) & (p[:-1]!=.5))[0]+1
    mask=np.zeros(600,bool)
    for t in switches: mask[t:min(t+30,600)] = True
    primary=mask & (s.trial.to_numpy()>=200) & (s.stimContrast.to_numpy()<=.1)
    rows.append(dict(subject=subject,session=s.session.iloc[0],condition=int(s.instructions.iloc[0]),schedule=sch,schedule_sha256=key,n_trials=len(s),n_switches_late=int(np.sum(switches>=200)),n_primary_stimuli=int(primary.sum()),switch_trials_zero_based=';'.join(map(str,switches)),first_biased=int(np.where(p!=.5)[0][0])))
    d.loc[s.index,'schedule']=sch
summary=pd.DataFrame(rows).merge(meta.drop(columns='instructions'),on='subject',validate='one_to_one')
assert (summary.condition.to_numpy()==meta.set_index('subject').loc[summary.subject].instructions.to_numpy()).all()
(ROOT/'outputs/input_only').mkdir(parents=True,exist_ok=True)
d.to_csv(ROOT/'outputs/input_only/trial_inputs.csv',index=False)
summary.to_csv(ROOT/'outputs/input_only/participants.csv',index=False)
manifest=dict(raw_file=str(RAW.relative_to(ROOT)),bytes=RAW.stat().st_size,md5=raw_md5,sha256=hashlib.sha256(RAW.read_bytes()).hexdigest(),url='https://zenodo.org/api/records/23072548/files/processed_data_2026.csv/content',input_only_columns=cols,rows=len(d),participants=len(summary),schedules=len(signatures),inspection='No choices, feedback, response or movement times read by this script. Stimulus inputs and schedule counts only. Historical prefix subject 006 belongs in development.')
(ROOT/'acquisition/MANIFEST.json').write_text(json.dumps(manifest,indent=2)+'\n')
print(json.dumps(manifest,indent=2))
print(summary.groupby(['schedule','condition']).agg(n=('subject','size'),primary_stimuli=('n_primary_stimuli','sum')).to_string())
print('Contrast values', sorted(d.stimContrast.unique()))
print('First biased trials', sorted(summary.first_biased.unique()))
