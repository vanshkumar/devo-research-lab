"""Independent scalar model calculation and post-pilot recovery diagnostic."""
import pathlib,csv,json,math
import numpy as np
H=pathlib.Path(__file__).parent

def scalar_curve(endpoint,t,biased):
 # Three-point Lagrange polynomial: no source notebook or numpy polynomial used.
 xp=[0.,.5,.999];yp=[.49/.51,1.,(.49/.51)*.36/.64]
 def pref(i):
  xx=i/1000
  prior=sum(yp[j]*math.prod((xx-xp[k])/(xp[j]-xp[k]) for k in range(3) if k!=j) for j in range(3)) if biased else 1.
  mu=0. if endpoint==645 else .999;w=math.exp(-((i/999-mu)**2)/(2*.2**2))
  return math.log(prior)+t*math.log1p(.01*w)
 target=0 if endpoint==645 else 999;inds=[min(999,int(v*1000)) for v in ([k/8 for k in range(1,9)] if endpoint==645 else [1-k/8 for k in range(1,9)])]
 return np.array([1/(1+math.exp(pref(i)-pref(target))) for i in inds])
rows=list(csv.DictReader((H/'model_curves.csv').open()));errs=[]
for endpoint,group in [(645,'red_long'),(580,'yellow_long')]:
 for name,biased in [('biased',True),('uniform',False)]:
  saved=np.array([float(r['raw']) for r in rows if r['group']==group and r['model']==name]);assert len(saved)==8
  err=float(max(abs(saved-scalar_curve(endpoint,300,biased))));assert err<1e-11;errs.append(dict(group=group,model=name,max_independent_error=err))
# Recovery test held fixed after pilot: when the published biased prior generated choices,
# how reliably can the frozen two-shape MSE comparison recover it at different noise/n?
seeds=range(100);out=[]
for endpoint in [645,580]:
 for t in [100,300]:
  pb=scalar_curve(endpoint,t,True);pu=scalar_curve(endpoint,t,False)
  for n in [14,128]:
   for noise in [.03,.15]:
    dif=[]
    for seed in seeds:
     rng=np.random.default_rng(40000+seed);train=np.clip(.7*pb+rng.normal(0,noise,(n,8)),0,1);test=np.clip(.7*pb+rng.normal(0,noise,(n,8)),0,1)
     def fit(p):
      scale=np.sum(train*p)/np.sum(np.broadcast_to(p,train.shape)**2);scale=np.clip(scale,0,1/max(p));return np.mean((test-scale*p)**2)
     dif.append(float(fit(pb)-fit(pu)))
    out.append(dict(endpoint=endpoint,time_steps=t,n_discovery=n,n_validation=n,noise_sd=noise,n_seeds=100,biased_wins=sum(d<0 for d in dif),mean_biased_minus_uniform_mse=float(np.mean(dif))))
(H/'recovery_controls.json').write_text(json.dumps(dict(independent_model_checks=errs,recovery=out,interpretation='Synthetic positive-control recoverability only. Low recovery at matched small n shows the comparison cannot support an absence-of-prior inference. Noise and clipping are specified, not fitted to biology.'),indent=2)+'\n');print(json.dumps(out,indent=2))
