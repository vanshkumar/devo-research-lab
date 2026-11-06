import hashlib, io, json, pathlib, resource, zipfile
from scipy.io import loadmat, whosmat
p=pathlib.Path(__file__).resolve().parent
b=(p/'behavior_zip.source').read_bytes()
assert hashlib.md5(b).hexdigest()=='235fad11706c1b93c7a12b55fcde5757'
with zipfile.ZipFile(io.BytesIO(b)) as z:
    for x in z.infolist():
        print('MEMBER',x.filename,x.file_size,x.compress_size)
    choices=sorted(x.filename for x in z.infolist() if x.filename.endswith('.mat') and not x.filename.startswith('__MACOSX'))
    first=choices[0]
    data=z.read(first)
    print('FIRST',first,len(data),'SCHEMA',whosmat(io.BytesIO(data)))
    d=loadmat(io.BytesIO(data),simplify_cells=True)
    for k,v in d.items():
        if not k.startswith('__'):
            print('TOP',k, type(v), list(v.keys()) if isinstance(v,dict) else str(v)[:100])
            if isinstance(v,dict):
                for key,val in v.items():
                    print('FIELD',key, getattr(val,'shape',None),str(val)[:350])
print('RSS_BYTES',resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
