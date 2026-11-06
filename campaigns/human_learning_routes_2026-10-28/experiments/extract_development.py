"""Release only the locked development participants' numeric response data."""
from pathlib import Path
import csv,json,hashlib
import pandas as pd
ROOT=Path(__file__).resolve().parents[1]
split=pd.read_csv(ROOT/'protocol/split_manifest.csv',dtype={'subject':str})
subjects=set(split.loc[split.partition=='development','subject'])
out=ROOT/'inputs/development_numeric.csv'
fields=['subject','session','trial','probabilityLeft','contrastLeft','contrastRight','choice','firstMovement_times_from_stim','response_times_from_stim','feedbackType','stimContrast','sideContrast','stimSide','instructions','dot.started']
count=0
with (ROOT/'inputs/processed_data_2026.csv').open(newline='') as inp,out.open('w',newline='') as dest:
    reader=csv.DictReader(inp); writer=csv.DictWriter(dest,fieldnames=fields);writer.writeheader()
    for row in reader:
        if row['subject'] in subjects:
            writer.writerow({k:row[k] for k in fields});count+=1
assert count==600*len(subjects)
(ROOT/'protocol/DEVELOPMENT_RELEASE.json').write_text(json.dumps(dict(date='2026-10-28',participants=len(subjects),rows=count,sha256=hashlib.sha256(out.read_bytes()).hexdigest(),note='Only development numeric responses extracted. Validation strings were skipped without parsing or analysis.'),indent=2)+'\n')
print('Development released:',len(subjects),'participants,',count,'rows')
