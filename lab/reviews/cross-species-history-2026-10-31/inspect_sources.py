import os
for key in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','VECLIB_MAXIMUM_THREADS','NUMEXPR_NUM_THREADS'):os.environ[key]='1'
from pathlib import Path
import json
HERE=Path(__file__).resolve().parent;AUTHOR=HERE.parents[1]/'tasks'/HERE.name
m=json.loads((AUTHOR/'ALLOWED_MANIFEST.json').read_text())
out=dict(authority_pins=m['authority_pins'],human_samples=[r for r in m['subjects'] if r['species']=='human'][:2],mouse_sample=next(r for r in m['subjects'] if r['species']=='mouse'))
(HERE/'SOURCE_SELECTION.json').write_text(json.dumps(out,indent=2)+'\n')
print(json.dumps(out,indent=2))
