import os
os.environ.update(OPENBLAS_NUM_THREADS='1',OMP_NUM_THREADS='1',VECLIB_MAXIMUM_THREADS='1',MKL_NUM_THREADS='1')
import json, platform, sysconfig, sys, base64, hashlib
from pathlib import Path
R=Path(__file__).resolve().parent
j=json.loads((R/'codec_pypi.json').read_bytes())
print('PLATFORM',platform.machine(),sysconfig.get_platform(),sys.version)
print('MAC_WHEELS',[(x['filename'],x['size'],x['url']) for x in j['urls'] if 'cp39' in x['filename'] and 'macosx' in x['filename']])
v=[x for x in j['urls'] if 'cp39' in x['filename'] and 'macosx' in x['filename'] and ('universal2' in x['filename'] or platform.machine() in x['filename'])]
if v:
    x=v[0]
    (R/'codec_wheel.json').write_text(json.dumps([(x['url'],'numcodecs.whl',x['size'])]))
    (R/'CODEC_PACKAGE_PIN.json').write_text(json.dumps(x,indent=2)+'\n')
blob=json.loads((R/'task_blob.json').read_bytes());data=base64.b64decode(blob['content'])
assert hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest()==blob['sha']
(R/'DynamicRouting1.py.txt').write_bytes(data)
