import json, resource
from pathlib import Path
p=Path(__file__).resolve().parent
b=(p/'remote_tutorial.ipynb').read_bytes(); n=json.loads(b)
for i,c in enumerate(n['cells']):
    src=''.join(c.get('source',[]))
    if 'trials' not in src and 'remote_paths' not in src: continue
    print('CELL',i,src[:300])
    for o in c.get('outputs',[]):
        for k,v in o.get('data',{}).items():
            if k in ('text/plain','text/html','application/vnd.vegalite.v5+json'):
                print(k,(''.join(v) if isinstance(v,list) else str(v))[:23000])
            else: print(k,'len',len(str(v)))
        if 'text' in o: print(''.join(o['text'])[:3000])
print('READ_CHARGE',len(b)*3,'RSS',resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
