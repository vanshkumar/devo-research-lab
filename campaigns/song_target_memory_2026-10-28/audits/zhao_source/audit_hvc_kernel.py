"""Independent scalar implementation of published HVCIter arithmetic.

Does not import root hvc_model.py or its reference. Reads root's compiled C++
function only as subject under test. Units and schedule are audited separately.
"""
from pathlib import Path
import random,ctypes,json,hashlib
import numpy as np
P=Path(__file__).resolve().parents[2]
A=Path(__file__).resolve().parent
lib=P/'outputs/hvc/hvc_kernel.dylib'
f=ctypes.CDLL(str(lib)).hvc_run
arr=np.ctypeslib.ndpointer
f.argtypes=[ctypes.c_int,ctypes.c_int,arr(dtype=np.float64,flags='C_CONTIGUOUS'),arr(dtype=np.uint8,flags='C_CONTIGUOUS'),arr(dtype=np.uint8,flags='C_CONTIGUOUS'),arr(dtype=np.float64,flags='C_CONTIGUOUS'),arr(dtype=np.uint8,flags='C_CONTIGUOUS')]
f.restype=None

def scalar(weights,noise,onsets,par):
 beta,alpha,eta,epsilon,tau,gamma,cap,budget,k=par;k=int(k)
 n=len(weights);w=[r[:] for r in weights];old=[0.]*n;adapt=[0.]*n;states=[]
 for t in range(len(noise)):
  oldsum=sum(old)
  for i in range(n):adapt[i]+=(old[i]-adapt[i])/tau
  activation=[]
  for i in range(n):
   drive=(10. if onsets[t] else -10.) if i<k else noise[t][i]
   a=sum(w[i][j]*old[j] for j in range(n))-beta*oldsum-alpha*adapt[i]+drive
   activation.append(max(0.,a))
  inhibition=gamma*sum(activation)
  now=[float(a>inhibition) for a in activation]
  if eta>0:
   proposed=[[w[i][j]+eta*(now[i]*old[j]-old[i]*now[j]) for j in range(n)] for i in range(n)]
   ppre=[eta*max(0.,sum(proposed[i][j] for i in range(n))-budget) for j in range(n)]
   ppost=[eta*max(0.,sum(proposed[i])-budget) for i in range(n)]
   w=[[0. if i==j else min(cap,max(0.,proposed[i][j]-epsilon*(ppre[j]+ppost[i]))) for j in range(n)] for i in range(n)]
  states.append(now);old=now
 return np.array(w),np.array(states,dtype=np.uint8)

results=[]
for n,seed,eta,gamma in [(12,3,0.,.01),(12,7,.025,.01),(20,11,.05,.02),(20,23,.0125,0.),(9,37,.1,.1)]:
 r=random.Random(seed);steps=350
 par=np.array([.115,30,eta,.2,12,.01 if gamma is None else gamma,1,5,3.],dtype=float)
 weights=[[r.random() for _ in range(n)] for __ in range(n)]
 noise=[[int(r.random()<.08) for _ in range(n)] for __ in range(steps)]
 onsets=[int(t%17 in [0,3,6]) for t in range(steps)]
 expectw,expectx=scalar(weights,noise,onsets,par)
 gotw=np.array(weights,dtype=float);gotx=np.zeros((steps,n),dtype=np.uint8)
 f(n,steps,gotw,np.array(noise,dtype=np.uint8),np.array(onsets,dtype=np.uint8),par,gotx)
 err=float(np.abs(gotw-expectw).max());agree=bool(np.array_equal(gotx,expectx))
 assert err<1e-12 and agree,(n,seed,err,agree)
 results.append({'n':n,'seed':seed,'eta':eta,'gamma':gamma,'steps':steps,'weight_max_abs_error':err,'activity_exact':agree})
report={'independent_scalar_cases':results,'verdict':'PASS for kernel arithmetic; not biological model validation','source_cpp_sha256':hashlib.sha256((P/'experiments/hvc_kernel.cpp').read_bytes()).hexdigest(),'limitations':['Independent Python scalar source implementation; no MATLAB runtime/PRNG replay.','Core uses10ms impulse irrespective of50/300ms biological light width.','Sequence length is not vocal element duration; no acoustic decoder validated.','Frozen-weight probes differ from original online training readout, both legitimately reported separately.']}
(A/'hvc_independent_kernel_audit.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2))
