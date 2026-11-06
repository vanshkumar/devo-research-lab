import os
os.environ.update(OPENBLAS_NUM_THREADS='1',OMP_NUM_THREADS='1',VECLIB_MAXIMUM_THREADS='1',MKL_NUM_THREADS='1',NUMEXPR_NUM_THREADS='1')
import ast, json, hashlib, sys, zipfile, struct, resource, time, csv
from pathlib import Path
R=Path(__file__).resolve().parent; OLD=R.parent/'dynamic-routing-rule-transfer-2026-10-31'
pin=json.loads((R/'CODEC_PACKAGE_PIN.json').read_bytes())
assert hashlib.sha256((R/'numcodecs.whl').read_bytes()).hexdigest()==pin['digests']['sha256']
with zipfile.ZipFile(R/'numcodecs.whl') as z:
    assert all(not p.startswith('/') and '..' not in Path(p).parts for p in z.namelist())
    z.extractall(R/'deps')
sys.path.insert(0,str(R/'deps'))
import numpy as np, numcodecs
from numcodecs import Blosc, VLenUTF8, VLenBytes
m=json.loads((OLD/'nwb_metadata.json').read_bytes())['metadata']
tree=ast.parse((OLD/'first_data_check.py').read_text());ns={'struct':struct}
exec(compile(ast.Module(body=[x for x in tree.body if isinstance(x,ast.FunctionDef)],type_ignores=[]),str(OLD/'first_data_check.py'),'exec'),ns)
b=(OLD/'reward_time.blosc').read_bytes();ind=Blosc().decode(b);inh=ns['decode_stored_frame'](b)
assert ind==inh
codec=dict(created_utc=time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),package='numcodecs',version=numcodecs.__version__,wheel=pin['filename'],wheel_sha256=pin['digests']['sha256'],frame_bytes=len(b),decoded_bytes=len(ind),byte_exact_equal=True,decoded_sha256=hashlib.sha256(ind).hexdigest(),scope='Independent trusted C-Blosc implementation versus inherited Python Blosc/LZ4 on the complete stored reward frame; all new arrays decoded with trusted numcodecs, not generalized inherited decoder.')
(R/'CODEC_CHECK.json').write_text(json.dumps(codec,indent=2)+'\n')
def decode(p,b):
    s=m[p+'/.zarray'];raw=Blosc().decode(b)
    if s['dtype']=='|O':
        filt=s['filters'][0]['id'];assert filt in ['vlen-utf8','vlen-bytes']
        a=(VLenUTF8() if filt=='vlen-utf8' else VLenBytes()).decode(raw)
        a=np.asarray([x.decode() if isinstance(x,bytes) else x for x in a],dtype=object)
    else:a=np.frombuffer(raw,dtype=s['dtype'])
    assert list(a.shape)==s['shape']
    return a
d={};scalars={}
for f in sorted((R/'raw/742903').glob('*.bin')):
    p=f.stem.replace('__','/');a=decode(p,f.read_bytes())
    if p.startswith('intervals/trials/'):d[p.split('/')[-1]]=a
    else:scalars[p]=a.tolist()
d['reward_time']=np.frombuffer(ind,dtype='<f8')
np.savez(R/'development_arrays.npz',**d)
(R/'DEVELOPMENT_SCALARS.json').write_text(json.dumps(scalars,indent=2)+'\n')
print('CODEC',json.dumps(codec));print('SCALARS',json.dumps(scalars))
for k,a in d.items():
    if a.dtype.kind in 'Obi':print(k,np.unique(a,return_counts=True))
    else:print(k,'finite',int(np.isfinite(a).sum()),'first',a[:6].tolist())
with (R/'development_trials.csv').open('w') as f:
    w=csv.writer(f);w.writerow(d);w.writerows(zip(*d.values()))
print('BLOCKS')
for block in np.unique(d['block_index']):
    ix=np.flatnonzero(d['block_index']==block); print(int(block),'n',len(ix),'start',int(ix[0]),'first',[(int(i),str(d['stim_name'][i]),bool(d['is_response'][i]),float(d['reward_time'][i]),bool(d['is_instruction'][i])) for i in ix[:9]])
print('RSS',resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
