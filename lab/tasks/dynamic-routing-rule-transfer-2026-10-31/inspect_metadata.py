import json, resource
from pathlib import Path
p=Path(__file__).resolve().parent
b=(p/'nwb_metadata.json').read_bytes(); n=json.loads(b)['metadata']
out={k:v for k,v in n.items() if k.startswith('intervals/trials/') or k in ('.zattrs','general/subject/.zattrs')}
(p/'TRIAL_SCHEMA.json').write_text(json.dumps(out,indent=2))
print(json.dumps(out,indent=2))
print('READ_CHARGE',len(b)*3,'RSS',resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
