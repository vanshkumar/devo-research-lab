from data import ROOT,load_people,wrap
from model import block_features,approximate
import datetime,hashlib,json,resource
import numpy as np
people,_,_=load_people('development');f=people[0]
a=block_features(f)
rot={**f,'pred':wrap(f['pred']+.7),'outcome':wrap(f['outcome']+.7)}
b=block_features(rot)
err=abs(a[1]-b[1]);ij=np.unravel_index(np.argmax(err),err.shape)
out=dict(at=datetime.datetime.now(datetime.timezone.utc).isoformat(),person=f['id'],context=f['context'],max_error=float(err[ij]),row=int(ij[0]),column=int(ij[1]),row_key=a[3][ij[0]].tolist(),features_original=a[1][ij[0]].tolist(),features_rotated=b[1][ij[0]].tolist(),raw_outcomes_deg=np.rad2deg(f['outcome'][:int(a[3][ij[0],3])]).tolist(),peak_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
code=(ROOT/'model.py').read_bytes()
(ROOT/'INITIAL_MODEL.py').write_bytes(code)
out['initial_model_sha256']=hashlib.sha256(code).hexdigest()
(ROOT/'INITIAL_DATA.py').write_bytes((ROOT/'data.py').read_bytes())
out['input_dtypes']={'pred':str(f['pred'].dtype),'outcome':str(f['outcome'].dtype)}
(ROOT/'INITIAL_DEVELOPMENT_FAILURE.json').write_text(json.dumps(out,indent=2))
print(json.dumps({k:v for k,v in out.items() if k not in ['raw_outcomes_deg','features_original','features_rotated']},indent=2))
