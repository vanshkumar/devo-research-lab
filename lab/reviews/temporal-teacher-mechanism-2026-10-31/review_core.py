"""Independent rendering/integration and bounded input accounting; no training."""
import os,sys
sys.dont_write_bytecode=True
for key in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','VECLIB_MAXIMUM_THREADS'):os.environ[key]='2'
from pathlib import Path
import io,json,hashlib,datetime,zipfile,types
import numpy as np
from scipy.special import erf
from scipy.sparse import csr_matrix,csc_matrix

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
TASK=ROOT/'lab/tasks/temporal-teacher-mechanism-2026-10-31'
SRC=ROOT/'sources/temporal_teacher_mechanism_2026-10-31'
UP=ROOT/'sources/sensory_evaluator_feasibility_2026-10-28/upstream/src'
END=datetime.datetime(2026,10,31,15,22,7,tzinfo=datetime.timezone.utc)
_CACHE={}

def now():return datetime.datetime.now(datetime.timezone.utc).isoformat()
def deadline():assert datetime.datetime.now(datetime.timezone.utc)<END,'Review endpoint reached'
def dump(name,obj):
    def enc(v):
        if isinstance(v,np.ndarray):return v.tolist()
        if isinstance(v,np.generic):return v.item()
        raise TypeError(type(v).__name__)
    (HERE/name).write_text(json.dumps(obj,indent=2,default=enc,allow_nan=False)+'\n')

def charge(path,n,kind,digest=None):
    f=HERE/'READS.json'
    d=json.loads(f.read_text()) if f.exists() else {
        'inherited_actual_bytes':807663431,'additional_cap_bytes':180000000,
        'additional_charged_bytes':2000000,
        'startup_context_note':'Conservative2MBupper charge for repeated ordinary context/source text reads and file metadata before metered loader; exceeds their combined file-size reads.',
        'reads':[],'primary_requests':0,'network_bytes':0}
    assert d['additional_charged_bytes']+int(n)<=180000000,'180MB review ceiling'
    assert d['inherited_actual_bytes']+d['additional_charged_bytes']+int(n)<=1000000000,'1GB lineage ceiling'
    d['additional_charged_bytes']+=int(n)
    d['reads'].append({'path':str(path),'bytes':int(n),'kind':kind,**({'sha256':digest} if digest else {})})
    dump('READS.json',d)

def read(path):
    p=Path(path);charge(p.relative_to(ROOT),p.stat().st_size,'encoded_file_read')
    b=p.read_bytes();h=hashlib.sha256(b).hexdigest()
    d=json.loads((HERE/'READS.json').read_text());d['reads'][-1]['sha256']=h;dump('READS.json',d)
    return b

def loadz(path,keys=None):
    p=Path(path);key=(str(p),None if keys is None else tuple(keys))
    if key in _CACHE:return _CACHE[key]
    b=read(p)
    with zipfile.ZipFile(io.BytesIO(b)) as z:
        members=[i for i in z.infolist() if i.filename.endswith('.npy') and (keys is None or i.filename[:-4] in keys)]
        charge(p.relative_to(ROOT),sum(i.file_size for i in members),'decoded_NPY_members_including_headers')
    with np.load(io.BytesIO(b),allow_pickle=False) as z:
        out={k:z[k].copy() for k in (z.files if keys is None else keys)}
    _CACHE[key]=out
    return out

def emits(shape,env,order):
    # Independent matrix contraction and explicit normalization per occurrence.
    result=[]
    for B,b in zip(env['basis'],env['bias']):
        v=np.maximum(B@np.asarray(shape)+b,0.)
        v=v-v.mean();v=2*v/max(float(np.sqrt(np.mean(v*v))),1e-12);result.append(v)
    return np.asarray(result)[np.asarray(order,dtype=int)]

def schedule(stretch,phase=0,gap=0):
    starts=np.array([150+phase+int(np.rint(150*j*stretch)) for j in range(6)])
    ends=starts+int(np.rint(100*stretch));starts[1]+=gap;ends[1]+=gap
    assert np.all(starts>=0) and np.all(ends<=2200) and np.all(starts[1:]>=ends[:-1])
    return starts,ends

def render(shape,order_index,stretch,env,phase=0,gap=0):
    yy=emits(shape,env,env['orders'][int(order_index)]);ss,ee=schedule(stretch,phase,gap)
    aud=np.zeros((2200,100))
    for j in range(6):aud[ss[j]:ee[j]]=yy[j]
    return aud

def registered(aud,teacher):
    def first(x):
        idx=np.flatnonzero(np.mean(x*x,1)>1e-8)
        return int(idx[0]) if len(idx) else 0
    shift=first(aud)-first(teacher);target=np.zeros_like(teacher)
    lo=max(0,shift);hi=min(2200,2200+shift)
    target[lo:hi]=teacher[lo-shift:hi-shift]
    return float(np.mean((aud-target)**2))

def integrate(aud,pack,trace=False):
    """Direct simultaneous Euler reduction independent of author's batched code."""
    deadline();W=csr_matrix(pack['JT'].T);h=pack['h'].copy()
    def rate(v):return pack['maximum']/2*(1+erf((v-pack['threshold'])/pack['width']))
    r=rate(h);out=[]
    if trace:out.append(r[:600].copy())
    total=r[:600]/100.;square=total*total;total=total.copy()
    for t in range(2199):
        drive=W@r-h;drive[:600]+=np.repeat(aud[t],6)
        h+=pack['inv_tau']*drive;r=rate(h);z=r[:600]/100
        total+=z;square+=z*z
        if trace:out.append(r[:600].copy())
    moments=np.r_[total/2200,square/2200]
    cost=float(np.mean((moments-pack['prototype_mean'])**2/pack['prototype_variance']))
    return cost,moments,(np.asarray(out) if trace else None)

def integrate_batch(waves,pack):
    """Same independent equations; transient state only, no teacher fitting."""
    deadline();b=len(waves);W=csr_matrix(pack['JT'].T);h=np.broadcast_to(pack['h'],(b,750)).copy()
    def rate(v):return pack['maximum']/2*(1+erf((v-pack['threshold'])/pack['width']))
    r=rate(h);total=r[:,:600]/100.;square=total*total;total=total.copy()
    for t in range(2199):
        drive=(W@r.T).T-h;drive[:,:600]+=np.repeat(waves[:,t,:],6,axis=1)
        h+=pack['inv_tau']*drive;r=rate(h);z=r[:,:600]/100;total+=z;square+=z*z
    features=np.c_[total/2200,square/2200]
    return np.mean((features-pack['prototype_mean'])**2/pack['prototype_variance'],axis=1),features

def source_trace(aud,pack):
    # Execute pinned source equations, no import of task common.py/guard/write code.
    shim=types.ModuleType('tqdm');shim.tqdm=lambda v,*args,**kwargs:v;sys.modules['tqdm']=shim
    module=types.ModuleType('independent_review_pinned_source');module.__file__=str(UP/'models.py');sys.modules[module.__name__]=module
    exec(compile(read(UP/'models.py'),str(UP/'models.py'),'exec'),module.__dict__)
    net=module.EINet.__new__(module.EINet);net.NE=600;net.NI=150;net.NH=15;net.w_inh=0
    net.phiE=(100,0,2);net.phiI=(100,0,2);net.tauE=30;net.tauI=10;net.W=csc_matrix((600,15))
    W=pack['JT'].T
    net.JEE=csc_matrix(W[:600,:600]);net.JEI=csc_matrix(-W[:600,600:]);net.JIE=csc_matrix(W[600:,:600]);net.JII=csc_matrix(-W[600:,600:])
    result=net.sim(pack['h'][:600],pack['h'][600:],np.zeros((2200,15)),np.repeat(aud,6,axis=1),[],2200,1,0,no_progress_bar=True)
    return result[0]
