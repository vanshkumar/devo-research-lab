import os,sys
sys.dont_write_bytecode=True
for k in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','VECLIB_MAXIMUM_THREADS'):os.environ[k]='2'
import importlib.metadata,platform,json
from common import save,now
packages={}
for name in ('numpy','scipy','numba','llvmlite','threadpoolctl'):
    try:packages[name]=importlib.metadata.version(name)
    except importlib.metadata.PackageNotFoundError:packages[name]=None
save('outputs/MODEL_RUNTIME.json',{'utc':now(),'python':sys.version,'executable':sys.executable,'platform':platform.platform(),
                                'packages':packages,'thread_limits':{k:os.environ[k] for k in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','VECLIB_MAXIMUM_THREADS')}})
print(json.dumps(packages),flush=True)
