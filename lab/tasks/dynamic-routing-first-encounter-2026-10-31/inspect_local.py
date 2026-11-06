import json, importlib.util, ctypes.util, resource
from pathlib import Path
P=Path(__file__).resolve().parent.parent/'dynamic-routing-rule-transfer-2026-10-31'
m=json.loads((P/'nwb_metadata.json').read_bytes())['metadata']
print('CODECS', {x:bool(importlib.util.find_spec(x)) for x in ['numcodecs','blosc','blosc2','lz4','numpy','scipy']},ctypes.util.find_library('blosc'))
for k,v in m.items():
    if k.endswith('/.zarray') and (k.startswith('general/') or '/' not in k[:-8] or k.startswith('intervals/trials/')):
        print(k, {x:v[x] for x in ['shape','dtype','chunks','filters','compressor']})
tree=json.loads((P/'task_tree.json').read_bytes())
print('TASKFILES',[(x['path'],x.get('sha')) for x in tree['tree'] if '/' not in x['path']])
print('RSS',resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
