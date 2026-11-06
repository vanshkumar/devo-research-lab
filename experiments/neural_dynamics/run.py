"""Transparent forecast baselines and dimension-surrogate pilots; see PLAN.md."""
import argparse,csv,json,pathlib,hashlib,warnings
import numpy as np
from scipy import linalg, signal
ROOT=pathlib.Path(__file__).resolve().parents[2]; HERE=pathlib.Path(__file__).parent

def mm(a,b): return np.einsum('ij,jk->ik',a,b,optimize=False)
def standardize(x,idx):
 mu=x[idx].mean(0); sd=x[idx].std(0); good=np.isfinite(x).all(0)&(sd>1e-10)
 return (x[:,good]-mu[good])/sd[good],int((~good).sum())
def mse(a,b): return float(np.mean((a-b)**2))
def records(part):
 m=json.loads((HERE/'selection.json').read_text())
 for item in m[part]:
  p=ROOT/'data/public'/pathlib.Path(item['path']).name; d=json.loads(p.read_text())
  x=np.asarray(d['trace_array'],dtype=float).T
  t=np.asarray(d['timestamp_confocal']); dt=float(np.median(np.diff(t)))
  yield d['uid'],x,dt,d

def forecasts(x,dt,uid,part):
 n=len(x); cut1=int(n*.60);cut2=int(n*.75);gap=int(np.ceil(30/dt))
 x,dropped=standardize(x,np.arange(cut1)); n,p=x.shape
 out=[]
 for seconds in [.6,3,12,30]:
  h=max(1,int(round(seconds/dt)))
  tr=np.arange(0,cut1-h-gap); va=np.arange(cut1+gap,cut2-h-gap);te=np.arange(cut2+gap,n-h)
  assert len(va)>5 and tr[-1]+h<va[0] and va[-1]+h<te[0]
  X=x[tr]; Y=x[tr+h]
  xm=X.mean(0);ym=Y.mean(0);A=X-xm;B=Y-ym
  diag=(A*B).sum(0)/np.maximum((A*A).sum(0),1e-12)
  pred={'mean':np.tile(ym,(len(te),1)),'persistence':x[te], 'diag_ar1':(x[te]-xm)*diag+ym}
  for name,pc in [('population_ridge',None),('pca5_ridge',5)]:
   if pc:
    ev,v=linalg.eigh(mm(A.T,A)); proj=v[:,-min(pc,p):]
   else: proj=np.eye(p)
   Z=mm(A,proj); zv=mm(x[va]-xm,proj); zt=mm(x[te]-xm,proj)
   g=mm(Z.T,Z); q=mm(Z.T,B)
   candidates=[]
   for lam in [.01,.1,1,10,100,1000]:
    coef=linalg.solve(g+np.eye(g.shape[0])*len(tr)*lam,q,assume_a='pos')
    candidates.append((mse(x[va+h],mm(zv,coef)+ym),lam,coef))
   _,lam,coef=min(candidates,key=lambda a:a[0]);pred[name]=mm(zt,coef)+ym
   out.append(dict(uid=uid,part=part,seconds=seconds,h=h,dt=dt,method=name,mse=mse(x[te+h],pred[name]),lambda_=lam,n_train=len(tr),n_test=len(te),n_neurons=p,dropped=dropped))
  for name in ['mean','persistence','diag_ar1']:
   out.append(dict(uid=uid,part=part,seconds=seconds,h=h,dt=dt,method=name,mse=mse(x[te+h],pred[name]),lambda_='',n_train=len(tr),n_test=len(te),n_neurons=p,dropped=dropped))
 return out

def dimension(x):
 z=(x-x.mean(0))/np.maximum(x.std(0),1e-12)
 c=mm(z.T,z)/len(z); e=np.maximum(linalg.eigvalsh(c),0)
 return dict(pr=float(e.sum()**2/np.sum(e**2)),top3=float(e[-3:].sum()/e.sum()))
def surrogate(x,rng,kind):
 if kind=='shift': return np.stack([np.roll(x[:,j],int(rng.integers(len(x)))) for j in range(x.shape[1])],1)
 if kind=='frame_shuffle': return x[rng.permutation(len(x))]
 f=np.fft.rfft(x,axis=0);phase=rng.uniform(0,2*np.pi,f.shape);phase[0]=0
 if len(x)%2==0:phase[-1]=0
 return np.fft.irfft(f*np.exp(1j*phase),n=len(x),axis=0)

def nulls(x,uid,part,count=39,transforms=('raw','difference')):
 out=[]
 for transform in transforms:
  z=x if transform=='raw' else np.diff(x,axis=0)
  real=dimension(z)
  for kind in ['phase','shift']:
   rng=np.random.default_rng(15297)
   vals=[dimension(surrogate(z,rng,kind)) for _ in range(count)]
   out.append(dict(uid=uid,part=part,transform=transform,null=kind,count=count,real_pr=real['pr'],real_top3=real['top3'],null_pr_median=float(np.median([v['pr'] for v in vals])),null_top3_median=float(np.median([v['top3'] for v in vals])),p_pr=(1+sum(v['pr']<=real['pr'] for v in vals))/(count+1),p_top3=(1+sum(v['top3']>=real['top3'] for v in vals))/(count+1)))
 return out

def synthetic(seed,kind,n=1600,p=40):
 rng=np.random.default_rng(seed)
 if kind=='independent_ar':
  x=rng.normal(size=(n,p))
  for i in range(1,n):x[i]=.95*x[i-1]+.3*x[i]
  return x
 if kind=='pure_sine':
  t=np.arange(n)*2*np.pi*12/n
  a=rng.normal(size=(2,p));return mm(np.stack([np.cos(t),np.sin(t)],1),a)
 if kind=='shared_broadband':
  z=rng.normal(size=(n,2))
  for i in range(1,n):z[i]=.95*z[i-1]+.3*z[i]
 else:
  z=np.zeros((n,2));r=np.array([[np.cos(.12),-np.sin(.12)],[np.sin(.12),np.cos(.12)]])*.98
  for i in range(1,n):z[i]=np.einsum('ij,j->i',r,z[i-1])+.12*rng.normal(size=2)
 return mm(z,rng.normal(size=(2,p)))+.20*rng.normal(size=(n,p))

def save_csv(name,rows):
 with (HERE/name).open('w') as f:
  w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)

def controls():
 rows=[]; ns=[]
 for kind in ['rotation','independent_ar']:
  for seed in range(10): rows+=forecasts(synthetic(seed,kind),.6,kind+'_'+str(seed),'control')
 for kind in ['pure_sine','rotation','shared_broadband','independent_ar']:
  x=synthetic(10,kind);ns+=nulls(x,kind,'control')
 x=synthetic(10,'rotation');s=surrogate(x,np.random.default_rng(5),'phase')
 inv={'frame_shuffle_top3_error':abs(dimension(x)['top3']-dimension(surrogate(x,np.random.default_rng(4),'frame_shuffle'))['top3']), 'phase_spectral_max_error':float(np.max(np.abs(np.abs(np.fft.rfft(x,axis=0))-np.abs(np.fft.rfft(s,axis=0)))))}
 assert inv['frame_shuffle_top3_error']<1e-10 and inv['phase_spectral_max_error']<1e-9
 save_csv('control_forecasts.csv',rows);save_csv('control_nulls.csv',ns);(HERE/'control_invariants.json').write_text(json.dumps(inv,indent=2)+'\n')
 print(json.dumps(inv))

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--part',choices=['controls','discovery','validation'],default='controls');ap.add_argument('--null-count',type=int,default=39);args=ap.parse_args()
 if args.part=='controls':controls();return
 rows=[];ns=[];quality=[]
 for uid,x,dt,d in records(args.part):
  print('analyzing',uid,x.shape,'dt',dt,flush=True)
  rows+=forecasts(x,dt,uid,args.part);ns+=nulls(x,uid,args.part,args.null_count)
  quality.append(dict(uid=uid,shape=list(x.shape),dt=dt,dt_min=float(np.min(np.diff(d['timestamp_confocal']))),dt_max=float(np.max(np.diff(d['timestamp_confocal']))),finite_fraction=float(np.isfinite(x).mean()),labels_used=False,behavior_keys=[k for k in ['velocity','pumping','head_curvature'] if k in d]))
 save_csv(args.part+'_forecasts.csv',rows);save_csv(args.part+'_nulls.csv',ns)
 (HERE/(args.part+'_quality.json')).write_text(json.dumps(quality,indent=2)+'\n')
 print('saved',len(rows),'forecasts;',len(ns),'null summaries')
if __name__=='__main__': main()
