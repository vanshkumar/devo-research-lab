"""Explicit metadata/source orientation for admitted inputs, no new outcomes."""
from independent_model import *
import re
import time
import resource
start=time.monotonic()
metadata={}
for name in ('seed0_baseline.npz','seed0_finite.npz','seed0_sham.npz','seed0_drive.npz',
             'seed0_literal_finite.npz','FWD_20s_reference.npz'):
    with np.load(AUTHOR/name,allow_pickle=False) as z:
        metadata[name]={k:{'shape':list(z[k].shape),'dtype':str(z[k].dtype)} for k in z.files}
def strings(obj):
    if isinstance(obj,dict):
        for key,value in obj.items():
            if key=='text' and isinstance(value,str): yield value
            else: yield from strings(value)
    elif isinstance(obj,list):
        for v in obj: yield from strings(v)
source={}
for file,ranges in [('interactome-results.json',[(346,360),(437,441)]),
                    ('article-results.json',[(318,319),(328,332),(357,359)])]:
    parts=[]
    for string in strings(json.loads((ORIGINAL/file).read_text())):
        for line in string.splitlines():
            match=re.match(r'L(\d+):',line)
            if match and any(lo<=int(match[1])<=hi for lo,hi in ranges):parts.append(line)
    source[file]=parts
report={'metadata':metadata,'cached_primary_excerpts':source,
        'elapsed_s':time.monotonic()-start,'rss_bytes_macos':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
        'exposure':'Complete named NPZ members decoded for metadata; already consumed author trajectories; no empirical or saved_dynamics inputs.'}
write('INPUT_INSPECTION.json',report)
print(json.dumps(report,indent=2))
