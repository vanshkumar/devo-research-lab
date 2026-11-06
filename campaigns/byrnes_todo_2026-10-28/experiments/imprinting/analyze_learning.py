import pathlib,json,zipfile
import pandas as pd,numpy as np
R=pathlib.Path(__file__).resolve().parents[2];D=R/'data/imprinting';H=pathlib.Path(__file__).parent
rng=np.random.default_rng(20261029);z=zipfile.ZipFile(D/'Experiment4.zip');allrows=[];curves=[];results=[]
x=np.linspace(0,1,1000);prior_x=np.arange(0,1,.001);rp=.49/.51;yp=rp*.36/.64
coeff=np.polynomial.polynomial.polyfit([0,.5,.999],[rp,1,yp],2);prior=np.polynomial.polynomial.polyval(prior_x,coeff)
assert np.all(prior>0)

def model(train_end,biased=True,t=300):
 p=prior.copy() if biased else np.ones(len(x));mu=0 if train_end==645 else .999;w=np.exp(-((x-mu)**2)/(2*.2**2))
 initial=p.copy()
 for _ in range(t):p*=1+.01*w;p/=p.max()
 closed=initial*np.exp(t*np.log1p(.01*w));closed/=closed.max();err=float(np.max(abs(p-closed)));assert err<1e-12
 target=0 if train_end==645 else 999
 coords=np.arange(1,9)/8 if train_end==645 else 1-np.arange(1,9)/8
 idx=np.clip((coords*1000).astype(int),0,999)
 return p[target]/(p[target]+p[idx]),err
for name,target,label in [('Exp 4a_Zenodo.xlsx',645,'red_long'),('Exp 4b_Zenodo.xlsx',580,'yellow_long')]:
 d=pd.read_excel(z.open(name));d=d.rename(columns={'Sex':'sex'})
 d=d[(d.left_stimulus>0)&(d.right_stimulus>0)].copy();assert np.all((d.left_stimulus==target)|(d.right_stimulus==target))
 d['novel_color']=np.where(d.left_stimulus==target,d.right_stimulus,d.left_stimulus);colors=sorted(d.novel_color.unique(),reverse=(target==645));rank={c:i+1 for i,c in enumerate(colors)};d['distance_rank']=d.novel_color.map(rank)
 s=d.groupby(['ID_exp','distance_rank']).prop_fam.mean().unstack();assert s.notna().all().all() and s.shape[1]==8
 train=s.loc[s.index%2==1].to_numpy();test=s.loc[s.index%2==0].to_numpy()
 constant=float(train.mean());baseline_mse=float(np.mean((test-constant)**2))
 models={}
 for which,biased in [('biased',True),('uniform',False)]:
  pred,err=model(target,biased);scale=float(np.sum(train*pred)/np.sum(np.broadcast_to(pred,train.shape)**2));scale=np.clip(scale,0,1/max(pred));prediction=pred*scale
  subjerr=np.mean((test-prediction)**2,axis=1);models[which]=dict(scale=float(scale),mse=float(subjerr.mean()),raw_curve=pred.tolist(),scaled_curve=prediction.tolist(),closed_form_max_error=err,subject_errors=subjerr.tolist())
  for k in range(8):curves.append(dict(group=label,model=which,rank=k+1,raw=pred[k],calibrated=prediction[k]))
 dif=np.array(models['biased']['subject_errors'])-models['uniform']['subject_errors'];boots=dif[rng.integers(len(dif),size=(5000,len(dif)))].mean(1)
 for sid,row in s.iterrows():
  for k,value in row.items():allrows.append(dict(group=label,ID_exp=int(sid),split='discovery' if sid%2 else 'validation',distance_rank=int(k),preference=float(value)))
 means=s.mean(0);bootmean=s.to_numpy()[rng.integers(len(s),size=(5000,len(s)))].mean(1)
 results.append(dict(group=label,total_subjects=len(s),discovery_subjects=len(train),validation_subjects=len(test),dual_trials=len(d),observed_means=means.tolist(),mean_ci95=np.quantile(bootmean,[.025,.975],axis=0).T.tolist(),constant_discovery_prediction=constant,constant_validation_mse=baseline_mse,models=models,biased_minus_uniform_mse=dict(estimate=float(dif.mean()),ci95=np.quantile(boots,[.025,.975]).tolist())))
pd.DataFrame(allrows).to_csv(H/'learning_subjects.csv',index=False);pd.DataFrame(curves).to_csv(H/'model_curves.csv',index=False)
(H/'learning_summary.json').write_text(json.dumps(dict(results=results,seed=20261029,model_parameters=dict(alpha=.01,sigma=.2,t=300),validation='Even subject IDs reserved before outcome computation; model params frozen; scale calibrated on odd IDs.',missing_condition='Short red-yellow data cannot be recovered from mislabeled Exp1 archive; no fast-vs-slow empirical test claimed.'),indent=2)+'\n');print(json.dumps(results,indent=2))
