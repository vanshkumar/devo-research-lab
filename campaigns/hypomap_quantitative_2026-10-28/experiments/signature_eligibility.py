"""Account for the frozen conditional signature branch, without fitting a classifier."""
from pathlib import Path
import pandas as pd
import json

r=Path(__file__).resolve().parents[1]
p=pd.read_csv(r/'outputs/abundance/candidate_per_cell.csv')
rows=[]
for d,z in p.groupby('donor_id'):
    rest=p[p.donor_id.ne(d)]
    rows.append(dict(donor_id=d,Dataset=z.Dataset.iloc[0],n=len(z),joint=int(z.joint.sum()),
        minor_median=z['minor'].median(),ratio_median=z.ratio.median(),major_median=z.major.median(),
        primary=int(z.substantial.sum()),lenient_k5_r10=int(((z['minor']>=5)&(z.ratio>=.1)).sum()),
        training_positive=int(rest.substantial.sum()),training_negative=int((~rest.substantial).sum()),
        heldout_positive=int(z.substantial.sum()),heldout_negative=int((~z.substantial).sum()),
        signature_evaluable=bool(z.substantial.nunique()>1 and rest.substantial.nunique()>1)))
pd.DataFrame(rows).to_csv(r/'outputs/abundance/primary_table.csv',index=False)
elig={'decision':'Conditional signature branch not activated: substantial tail does not recur across donors/studies.',
      'positive_cells':int(p.substantial.sum()),'positive_donors':int(p.loc[p.substantial,'donor_id'].nunique()),
      'positive_samples':p.loc[p.substantial,'Sample_ID'].unique().tolist(),'donor_folds':rows,
      'warning':'Every held-out donor either has no positives or leaves no positives in training. A held-out positive-class signature estimate is not identified; no classifier was fitted.'}
(r/'outputs/signature_eligibility.json').write_text(json.dumps(elig,indent=2)+'\n')
print(json.dumps({k:v for k,v in elig.items() if k!='donor_folds'},indent=2))
