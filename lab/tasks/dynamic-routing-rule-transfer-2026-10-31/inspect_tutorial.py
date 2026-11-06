import json, resource
from pathlib import Path
p=Path(__file__).resolve().parent
b=(p/'remote_tutorial.ipynb').read_bytes(); n=json.loads(b)
source='\n\n'.join(''.join(c.get('source',[])) for c in n['cells'])
(p/'tutorial_source.txt').write_text(source)
print(source[:50000])
print('READ_CHARGE',len(b)*3+len(source.encode()),'RSS',resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
