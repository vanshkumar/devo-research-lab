"""Cache-level reconstruction using augmented least squares, separate from fit engine."""
import os
for k in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','VECLIB_MAXIMUM_THREADS','NUMEXPR_NUM_THREADS'):os.environ[k]='1'
import numpy as np,json,pathlib,datetime,resource,hashlib
r=pathlib.Path(__file__).resolve().parent
cfg=json.loads((r/'config.json').read_text());fit=json.loads((r/'SOURCE_FITS.json').read_text());scores=json.loads((r/'SCORES.json').read_text())
def load(name):
 with np.load(r/name) as z:return {k:z[k] for k in z.files}
s=load('source.npz');e=load('evaluation_scored.npz');p=load('evaluation_predictions.npz')
def primary(d):
 m=(d['trial']>=19)&np.isfinite(d['y'])&np.all(np.isfinite(d['X']),axis=1)
 return {k:v[m] for k,v in d.items()},m
ss,_=primary(s);ee,mask=primary(e);pp={k:v[mask] for k,v in p.items()};ids=np.unique(ee['id'])
w=lambda a:(a+1)%2-1
metric={}
for name,pred in pp.items():
 err=180*w(ee['y']-pred)
 metric[name]={t:np.array([f(err[ee['id']==i],ee['gap'][ee['id']==i]) for i in ids]) for t,f in [('mse',lambda z,g:np.mean(z*z)),('mae',lambda z,g:np.mean(abs(z))),('directed_bias',lambda z,g:np.mean(z*np.sign(g)))]}
max_metric=max(abs(metric[k][t]-scores['person_metrics'][k][t]).max() for k in metric for t in metric[k]);assert max_metric<1e-10
idx=np.random.default_rng(cfg['seed_evaluation']).integers(0,len(ids),(5000,len(ids)))
gains={}
for base in ('B','H'):
 a,b=metric['P']['mse'],metric[base]['mse'];gains[base]={'point':1-float(a.mean()/b.mean()),'interval95':np.percentile(1-a[idx].mean(1)/b[idx].mean(1),[2.5,97.5]).tolist()}
 assert np.max(abs(np.array(gains[base]['interval95'])-scores['primary'][base]['interval95']))<1e-12

def ls(X,y,lam):
 mx=X.mean(0);my=y.mean();sd=np.sqrt(np.mean((X-mx)**2,axis=0));sd[sd<1e-7]=1.
 z=(X-mx)/sd;n=len(y);q=X.shape[1]
 design=np.concatenate((z/np.sqrt(n),np.sqrt(lam)*np.eye(q)),axis=0)
 target=np.concatenate(((y-my)/np.sqrt(n),np.zeros(q)))
 b=np.linalg.lstsq(design,target,rcond=1e-12)[0]/sd
 return b,float(my-np.einsum('i,i->',mx,b))
def pred(model,X):
 b,a=model;return np.clip(np.einsum('ij,j->i',X,b,optimize=False)+a,-1,1)
def independent_fit(y,dim):
 X=ss['X'][:,:dim];people=np.unique(ss['id']);loss=[]
 for lam in cfg['penalties']:
  fold=[]
  for person in people:
   test=ss['id']==person;model=ls(X[~test],y[~test],lam)
   fold.append(np.mean(w(y[test]-pred(model,X[test]))**2))
  loss.append(float(np.mean(fold)))
 best=min(loss);choice=max(j for j,v in enumerate(loss) if v<=best+1e-12)
 return ls(X,y,cfg['penalties'][choice]),cfg['penalties'][choice],np.array(loss)*32400
fits_audit={}
for name,dim in fit['dimensions'].items():
 new,pen,loss=independent_fit(ss['y'],dim);old=fit['models'][name]
 delta=float(np.max(abs(new[0]-old['coef'])));cvdelta=float(np.max(abs(loss-old['cv_mse_degrees2'])))
 assert pen==old['penalty'] and delta<1e-9 and cvdelta<1e-7
 reconstructed=pred(new,e['X'][:,:dim]);valid=np.isfinite(reconstructed)
 forecast_delta=float(np.max(abs(reconstructed[valid]-p[name][valid])))
 assert forecast_delta<1e-10
 fits_audit[name]={'selected_penalty':pen,'max_coefficient_difference':delta,'intercept_difference':abs(new[1]-old['intercept']),'cv_mse_max_difference_degrees2':cvdelta,'max_frozen_prediction_difference_normalized':forecast_delta}
 print('augmented least-squares audit',name,flush=True)

# Two saved full conditional examples, independent refit and prediction reconstruction.
examples={}
for kind in ('signal','null'):
 ex=load('CONTROL_EXAMPLE_'+kind+'.npz');checks={}
 for name,dim in fit['dimensions'].items():
  model,pen,_=independent_fit(ex['source_y'],dim);actual=pred(model,ee['X'][:,:dim]);delta=float(np.max(abs(actual-ex['prediction_'+name])))
  assert delta<1e-9;checks[name]={'penalty':pen,'max_prediction_difference_normalized':delta}
 examples[kind]=checks

linear={}
for name,prediction in pp.items():
 error=180*(ee['y']-prediction)
 linear[name]=float(np.mean([np.mean(error[ee['id']==i]**2) for i in ids]))
su=json.loads((r/'SOURCE_UNCERTAINTY.json').read_text());controls=json.loads((r/'CONTROLS.json').read_text())
stat={'source_point_atleast5percent_vs_H':sum(z['gain_H']>=.05 for z in su['replicates']),
 'source_max_gain_vs_H':max(z['gain_H'] for z in su['replicates']),
 'loo_joint_passes':sum(z['decision']['joint_pass'] for z in scores['leave_one_person_out']),
 'loo_count':len(scores['leave_one_person_out']),
 'control_counts_recounted':{kind:sum(z['kind']==kind and z['decision']['joint_pass'] for z in controls['replicates']) for kind in ('signal','null')}}
pinchecks={}
for name in ('FREEZE.json','FREEZE_v2.json'):
 obj=json.loads((r/name).read_text())
 for path,digest in obj['files'].items():
  # Large data/cache pins were verified in original generation and frozen reader;
  # this final audit rereads only the small model/protocol/code artifacts.
  if path in ('source.npz','original_typed_rows.json'):continue
  assert hashlib.sha256((r/path).read_bytes()).hexdigest()==digest;pinchecks[path]=digest
result={'timestamp_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'equal_person_metric_max_difference':float(max_metric),'gain_reconstruction':gains,
 'augmented_lstsq_source_fits_all360CVfolds':fits_audit,'independent_refit_control_examples':examples,
 'equal_person_linear_revision_MSE_contrary':linear,'stability_counts':stat,'small_freeze_pin_checks':pinchecks,
 'scope':'Within-author cache-level audit, not distinct review or new raw-XLSX reconstruction. Full source fits and all360source selection folds independently recomputed with augmented least squares. Two full conditional control refits;198other independent control refits and100independent source-bootstrap refits UNRUN.',
 'peak_rss_bytes':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss}
(r/'FINAL_AUDIT.json').write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2))
