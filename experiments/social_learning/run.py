"""Outcome reconstruction and selection sensitivity for open social-learning trials."""
import csv,json,pathlib,math,collections,hashlib
import numpy as np
import pandas as pd
from scipy.stats import binomtest,fisher_exact,chi2_contingency,norm
D=pathlib.Path(__file__).resolve().parents[2]/'data/social_learning';H=pathlib.Path(__file__).parent

def ac(k,n):
 z=norm.ppf(.975);nn=n+z*z;p=(k+z*z/2)/nn;h=z*math.sqrt(p*(1-p)/nn);return [float(max(0,p-h)),float(min(1,p+h))]
def summary(v,**kwargs):
 v=np.asarray(v,dtype=float);v=v[np.isfinite(v)];k=int(v.sum());n=len(v)
 r=dict(kwargs,n=n,k=k,estimate=k/n if n else None,p_two_sided=float(binomtest(k,n).pvalue) if n else None,agresti_coull95=ac(k,n) if n else None)
 return r

def main():
 b=(D/'data_primacy.csv').read_bytes();assert hashlib.sha256(b).hexdigest()=='0f723df5825865d214e3064c1e16f0e489211f25e45f3eb34e7dfb5c4ebf568b'
 d=pd.read_csv(D/'data_primacy.csv');d['row_id']=np.arange(len(d))
 valid=lambda c:d[c].isin(['p','g'])
 d['mating']=valid('test_color');d['double_court']=valid('color_court_1')&valid('color_court_2');d['eligible']=d.mating&d.double_court
 d['first_single']=d.demo_color_1.where(d.treatment.isin(['T','C1']),d.demo_color_2)
 d['last_single']=d.demo_color_2.where(d.treatment.isin(['T','C2']),d.demo_color_1)
 d['copy_first']=(d.test_color==d.first_single).astype(int);d['copy_last']=(d.test_color==d.last_single).astype(int)
 assert (d.loc[d.double_court,'color_court_1']!=d.loc[d.double_court,'color_court_2']).all()
 assert ((d.loc[d.treatment=='T','demo_color_1']!=d.loc[d.treatment=='T','demo_color_2'])).all()
 counts=[];rates=[]
 for t in ['T','C1','C2']:
  a=d[d.treatment==t];counts.append(dict(treatment=t,total=len(a),matings=int(a.mating.sum()),double_court=int(a.double_court.sum()),eligible=int(a.eligible.sum()),n_dates=a.date.nunique()))
  for incl,label in [(a.eligible,'eligible'),(a.mating,'all_matings')]:
   for score in ['copy_first','copy_last']:
    rates.append(summary(a.loc[incl,score],treatment=t,inclusion=label,score=score,stratum='all'))
   for color in ['g','p']:
    rates.append(summary(a.loc[incl&(a.first_single==color),'copy_first'],treatment=t,inclusion=label,score='copy_first',stratum=color))
  # Worst-case latent choice bounds: not a missing-data adjustment for eligible estimand.
  elig=a[a.eligible]; k=int(elig.copy_first.sum()); n=len(a); miss=n-len(elig)
  counts[-1].update(first_choice_worst_case_lower=k/n,first_choice_worst_case_upper=(k+miss)/n)
 pd.DataFrame(counts).to_csv(H/'inclusion.csv',index=False)
 pd.DataFrame(rates).to_csv(H/'rates.csv',index=False)
 # supplied score mismatch, preserving row IDs and excluding missing supplied annotations
 checks=[]
 for t in ['T','C1','C2']:
  for incl in ['eligible','all']:
   q=d[(d.treatment==t)&(d.eligible if incl=='eligible' else True)&d.copy_dc_bin.notna()]
   checks.append(dict(treatment=t,inclusion=incl,n=len(q),first_mismatch=int((q.copy_dc_bin!=q.copy_first).sum()),last_mismatch=int((q.copy_dc_bin!=q.copy_last).sum())))
 pd.DataFrame(checks).to_csv(H/'annotation_checks.csv',index=False)
 # cluster bootstrap from counts per date, respects simultaneous co-occurring groups.
 dates=sorted(d.date.unique());rng=np.random.default_rng(20261028)
 arr=np.zeros((len(dates),3,2,2)) # date,treatment,color,[k,n]
 for i,dt in enumerate(dates):
  for j,t in enumerate(['T','C1','C2']):
   for c,color in enumerate(['g','p']):
    q=d[(d.date==dt)&(d.treatment==t)&d.eligible&(d.first_single==color)];arr[i,j,c]=[q.copy_first.sum(),len(q)]
 boots=[]
 for _ in range(5000):
  a=arr[rng.integers(len(dates),size=len(dates))].sum(0)
  raw=a[:,:,0].sum(1)/a[:,:,1].sum(1);balanced=(a[:,:,0]/a[:,:,1]).mean(1)
  boots.append([*raw,*balanced,raw[0]-raw[1],raw[0]-raw[2]])
 names=['main_first','C1_single','C2_single','main_balanced','C1_balanced','C2_balanced','main_minus_C1','main_minus_C2']
 boots=np.array(boots);bs={n:dict(ci95=np.quantile(boots[:,i],[.025,.975]).tolist(),bootstrap_mean=float(boots[:,i].mean())) for i,n in enumerate(names)}
 loo=[]
 for dt in dates:
  a=d[d.eligible&(d.date!=dt)];m=a[a.treatment=='T'];c=a[a.treatment=='C1'];loo.append(dict(date_excluded=dt,main_first=float(m.copy_first.mean()),main_minus_C1=float(m.copy_first.mean()-c.copy_first.mean())))
 pd.DataFrame(loo).to_csv(H/'leave_date_out.csv',index=False)
 # Independent standard-library CSV reconstruction and exact binomial enumeration control.
 raw=list(csv.DictReader((D/'data_primacy.csv').open()));ind={}
 for t in ['T','C1','C2']:
  q=[r for r in raw if r['treatment']==t and all(r[c] in ['p','g'] for c in ['color_court_1','color_court_2','test_color'])]
  ind[t]={'n':len(q),'last_k':sum(r['test_color']==r['demo_color_1' if t=='C1' else 'demo_color_2'] for r in q)}
 for t in ind:
  r=next(r for r in rates if r['treatment']==t and r['inclusion']=='eligible' and r['score']=='copy_last' and r['stratum']=='all');assert (r['n'],r['k'])==(ind[t]['n'],ind[t]['last_k'])
 control=[]
 for k,n in [(0,4),(2,4),(40,64),(21,30)]:
  p=math.comb(n,k)/2**n; exact=sum(math.comb(n,j)/2**n for j in range(n+1) if math.comb(n,j)/2**n<=p+1e-16);err=abs(exact-binomtest(k,n).pvalue);assert err<1e-12;control.append(dict(k=k,n=n,enumerated_p=exact,scipy_error=err))
 d.to_csv(H/'reconstructed_trials.csv',index=False)
 (H/'bootstrap.json').write_text(json.dumps(bs,indent=2)+'\n')
 metadata={'seed':20261028,'bootstrap_replicates':5000,'date_clusters':len(dates),'counts':counts,'eligible_rates':[r for r in rates if r['inclusion']=='eligible' and r['stratum']=='all'],'annotation_checks':checks,'independent_counts':ind,'binomial_controls':control,'bootstrap':bs,'untouched_validation':False,'warning':'Exploratory reanalysis of one experiment; eligibility is post-exposure and all-mating sensitivity has a different estimand.'}
 (H/'summary.json').write_text(json.dumps(metadata,indent=2)+'\n')
 print(json.dumps({k:metadata[k] for k in ['counts','eligible_rates','annotation_checks','bootstrap']},indent=2))
if __name__=='__main__':main()
