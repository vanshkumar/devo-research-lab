"""Source-data reproduction and a controlled limit on causal interpretation."""
import json,pathlib,csv,math
import numpy as np
from scipy import linalg
H=pathlib.Path(__file__).resolve().parent;C=H.parents[1];D=C/'data/song_learning'
def vals(rows):return np.array([v for row in rows for v in row.values()],dtype=float)
def mm(a,b):return np.einsum('ij,jk->ik',a,b,optimize=False)
def arr(rows):return np.array([list(r.values()) for r in rows],dtype=float)
def save(name,rows):
 with (H/name).open('w') as f:w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
def source_analysis():
 m=json.loads((D/'fig3_extracted.json').read_text());x=arr(m['e.syllable_traces']);mean=vals(m['f.population_mean']);s=vals(m['f.shuffle_mean']);upper=vals(m['f.shuffle_pvalue_upper']);lower=vals(m['f.shuffle_pvalue_lower'])
 assert x.shape==(25,600) and len(mean)==600 and np.isfinite(x).all()
 err=float(np.max(abs(x.mean(0)-mean)));assert err<1e-12
 leave=(x.sum(0)[None,:]-x)/24
 rows=[dict(syllable_row=i+1,at_source_column_150=float(v[149]),at_source_column_300=float(v[299]),at_source_column_600=float(v[599])) for i,v in enumerate(x)]
 save('source_syllable_endpoints.csv',rows)
 q=json.loads((D/'fig4_extracted.json').read_text());coef=vals(q['d.regression_coeff']);hist=vals(q['d.history_step']);se=vals(q['d.error_positive']);model_ppe=vals(q['b.model_PPE']);model_me=vals(q['b.model_ME'])
 assert len(coef)==12 and hist[-1]==0 and max(abs(model_me[:-1]))<1e-12
 save('source_history_kernel.csv',[dict(history=int(a),observed_mean_coefficient=float(b),reported_error=float(c),model_ppe=float(e),model_me=float(f)) for a,b,c,e,f in zip(hist,coef,se,model_ppe,model_me)])
 result=dict(source_mean_reproduction_max_error=err,n_syllable_rows=25,n_source_columns=600,all_endpoints_positive=bool((x[:,-1]>0).all()),endpoint_mean=float(mean[-1]),endpoint_median=float(np.median(x[:,-1])),endpoint_min=float(x[:,-1].min()),endpoint_max=float(x[:,-1].max()),endpoint_shuffle_mean=float(s[-1]),endpoint_shuffle_envelope=[float(lower[-1]),float(upper[-1])],endpoint_leave_one_syllable_out_mean_range=[float(leave[:,-1].min()),float(leave[:,-1].max())],number_source_columns_above_upper_envelope=int((mean>upper).sum()),history_current_coefficient=float(coef[-1]),history_negative_count=int((coef[:-1]<0).sum()),history_count=11,source_ppe_negative_history_count=int((model_ppe[:-1]<0).sum()),limit='descriptive published aggregates; no bird IDs or per-rendition values in Fig3 e/f; no independent-bird uncertainty or raw-pipeline reproduction')
 return result

def simulate(seed,kind,clamp=False):
 rng=np.random.default_rng(seed);n=150;dim=23;sigma=.25;eta=.10;steps=35
 target=rng.normal(size=dim);target/=np.linalg.norm(target);mu=np.zeros(dim);align=[];errors=[];control_align=[]
 for t in range(steps):
  eps=rng.normal(0,sigma,size=(n,dim));xx=mu+eps
  quality=-np.sum((xx-target)**2,axis=1)+rng.normal(0,.2,size=n)
  if kind=='independent_signal':quality=rng.normal(size=n)
  xc=xx-xx.mean(0);yc=np.zeros(n) if clamp else quality-quality.mean()
  cov=np.einsum('ij,i->j',xc,yc,optimize=False)/n
  reg=linalg.solve(mm(xc.T,xc)+np.eye(dim)*1e-6,np.einsum('ij,i->j',xc,yc,optimize=False),assume_a='pos');v=reg/max(np.linalg.norm(reg),1e-12)
  yy=yc[rng.permutation(n)];nullreg=linalg.solve(mm(xc.T,xc)+np.eye(dim)*1e-6,np.einsum('ij,i->j',xc,yy,optimize=False),assume_a='pos');nullv=nullreg/max(np.linalg.norm(nullreg),1e-12)
  if kind=='causal':delta=eta*(np.zeros(dim) if clamp else cov)/(2*sigma*sigma)
  else:delta=eta*(target-mu) # no dopamine input in this structural equation
  align.append(float(np.sum(delta*v)));control_align.append(float(np.sum(delta*nullv)));mu+=delta;errors.append(float(np.sum((mu-target)**2)))
 return dict(seed=seed,model=kind,clamp=clamp,mean_future_alignment=float(np.mean(align)),mean_shuffled_alignment=float(np.mean(control_align)),final_squared_target_error=errors[-1]),mu

def controlled():
 rows=[];max_pathchange=0
 for seed in range(50):
  for kind in ['common_teacher','causal','independent_signal']:
   normal,mu=simulate(seed,kind,False);rows.append(normal)
   if kind in ['common_teacher','causal']:
    clamped,muc=simulate(seed,kind,True);rows.append(clamped)
    if kind=='common_teacher':max_pathchange=max(max_pathchange,float(np.max(abs(mu-muc))))
 assert max_pathchange==0
 save('controlled_runs.csv',rows)
 summaries=[]
 for model in ['common_teacher','causal','independent_signal']:
  for clamp in [False,True]:
   q=[x for x in rows if x['model']==model and x['clamp']==clamp]
   if q:summaries.append(dict(model=model,clamp=clamp,n=len(q),alignment_median=float(np.median([x['mean_future_alignment'] for x in q])),shuffle_alignment_median=float(np.median([x['mean_shuffled_alignment'] for x in q])),final_error_median=float(np.median([x['final_squared_target_error'] for x in q]))))
 # Independent known-answer population covariance check, no fitted neural model.
 rng=np.random.default_rng(999);eps=rng.normal(0,.25,size=(200000,3));target=np.array([.3,-.4,.2]);quality=-np.sum((eps-target)**2,axis=1);got=np.mean(eps*(quality-quality.mean())[:,None],axis=0);want=2*.25**2*target
 analytic_error=float(np.max(abs(got-want)));assert analytic_error<.001
 return dict(summaries=summaries,common_teacher_clamp_max_path_change=max_pathchange,known_covariance_estimate=got.tolist(),known_covariance_exact=want.tolist(),known_covariance_max_error=analytic_error,claim='A latent target-driven updater without dopamine input can produce the future-alignment signature. These model distributions are not asserted identical; causal intervention predictions differ.',config=dict(seeds=list(range(50)),dimension=23,renditions_per_block=150,steps=35,sigma=.25,eta=.1))
if __name__=='__main__':
 result=dict(source=source_analysis(),control=controlled());(H/'summary.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
