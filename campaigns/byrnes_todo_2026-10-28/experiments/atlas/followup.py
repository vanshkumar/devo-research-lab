"""Integer/rounding/donor-capacity bounds for observed OXT/AVP co-detection.
Not cell-level validation, contamination estimation, peptide or species inference.
"""
import pathlib,json,csv,math,itertools,hashlib
from decimal import Decimal,ROUND_CEILING,ROUND_FLOOR
import numpy as np,pandas as pd
from scipy.optimize import milp,LinearConstraint,Bounds
BASE=pathlib.Path(__file__).resolve().parents[2];D=BASE/'data/atlas';H=pathlib.Path(__file__).parent
IDS=['C4-296','C4-312','C4-313','C4-315']

def interval(n,text,decimals,scale=1):
 value=Decimal(str(text))/Decimal(scale);half=Decimal(5)*(Decimal(10)**(-decimals-1))/Decimal(scale)
 lo=int((max(Decimal(0),value-half)*n).to_integral_value(rounding=ROUND_CEILING));hi=int((min(Decimal(1),value+half)*n).to_integral_value(rounding=ROUND_FLOOR))
 assert lo<=hi,(n,text,lo,hi)
 return lo,hi

def solve(n,caplo,caphi,al,ah,bl,bh,objective='total',largest=None,target_donor=None,donor_subset=None):
 d=len(caplo);binary=objective=='contributors';k=4*d+(d if binary else 0)
 # donor categories: neither, A-only, B-only, both
 rows=[];lower=[];upper=[]
 def add(coeff,lo,hi):rows.append(coeff);lower.append(lo);upper.append(hi)
 for j in range(d):
  v=np.zeros(k);v[4*j:4*j+4]=1;add(v,caplo[j],caphi[j])
 v=np.zeros(k);v[:4*d]=1;add(v,n,n)
 v=np.zeros(k);v[1:4*d:4]=1;v[3:4*d:4]=1;add(v,al,ah)
 v=np.zeros(k);v[2:4*d:4]=1;v[3:4*d:4]=1;add(v,bl,bh)
 c=np.zeros(k)
 if objective=='total':c[3:4*d:4]=1
 elif objective=='outside_largest':
  c[3:4*d:4]=1;c[4*largest+3]=0
 elif objective=='donor':c[4*target_donor+3]=1
 elif objective=='subset':
  for j in donor_subset:c[4*j+3]=1
 elif binary:
  for j in range(d):
   v=np.zeros(k);v[4*j+3]=1;v[4*d+j]=-caphi[j];add(v,-np.inf,0)
  c[4*d:]=1
 else:raise ValueError(objective)
 ub=np.full(k,float(n))
 if binary:ub[4*d:]=1
 result=milp(c,integrality=np.ones(k),bounds=Bounds(np.zeros(k),ub),constraints=LinearConstraint(np.array(rows),lower,upper),options={'time_limit':10})
 assert result.success,(objective,result.message)
 x=np.rint(result.x).astype(int);assert np.max(np.abs(result.x-x))<1e-5
 return int(round(result.fun)),x[:4*d].reshape(d,4)

def exhaustive_controls():
 out=[]
 # enumerate labelled binary pairs for every A,B count in every3/5-cell universe
 for capacities in [(1,2),(2,3)]:
  n=sum(capacities);subsets=[set(i for i in range(n) if mask>>i&1) for mask in range(1<<n)]
  donor=[0]*capacities[0]+[1]*capacities[1]
  for a in range(n+1):
   for b in range(n+1):
    vals=[]
    for A in subsets:
     if len(A)!=a:continue
     for B in subsets:
      if len(B)!=b:continue
      common=A&B;vals.append((len(common),sum(donor[i]!=int(np.argmax(capacities)) for i in common),len(set(donor[i] for i in common))))
    L=max(0,a+b-n);sortedcaps=sorted(capacities,reverse=True);need=next((j for j in range(3) if sum(sortedcaps[:j])>=L),None)
    expected=(L,max(0,L-max(capacities)),need);observed=tuple(min(v[j] for v in vals) for j in range(3));assert observed==expected,(capacities,a,b,expected,observed)
    out.append(dict(capacities=capacities,A=a,B=b,expected=expected,exhaustive=observed))
 return out

def main():
 for f in json.loads((D/'manifest.json').read_text())['files']:assert hashlib.sha256((BASE/f['file']).read_bytes()).hexdigest()==f['sha256']
 annotation=list(csv.DictReader((D/'cluster_annotations_and_statistics.txt').open(),delimiter='\t'));marker=list(csv.DictReader((D/'marker_genes_all.txt').open(),delimiter='\t'));sample=list(csv.DictReader((D/'sup_sample_statistics.txt').open(),delimiter='\t'))
 donors=list(dict.fromkeys(r['Donor_ID'] for r in sample));results=[];witness=[];perdonor=[];sensitivity=[];dataset_bounds=[]
 donor_dataset={r['Donor_ID']:r['Dataset'] for r in sample}
 assert all(len({r['Dataset'] for r in sample if r['Donor_ID']==donor})==1 for donor in donors)
 controls=exhaustive_controls()
 for cid in IDS:
  row=next(r for r in annotation if r['cluster_id']==cid);n=int(row['ncells']);m={r['gene']:r for r in marker if r['cluster']==cid and r['gene'] in ['OXT','AVP']};assert len(m)==2
  al,ah=interval(n,m['OXT']['pct.1'],3);bl,bh=interval(n,m['AVP']['pct.1'],3)
  caps=[interval(n,row[donor],2,100) for donor in donors];cl=[x[0] for x in caps];ch=[x[1] for x in caps];assert sum(cl)<=n<=sum(ch)
  L=max(0,al+bl-n);U=min(ah,bh);largest=int(np.argmax(ch));outside=max(0,L-ch[largest]);sortedcaps=sorted(ch,reverse=True);need=next(j for j in range(len(donors)+1) if sum(sortedcaps[:j])>=L)
  il,x=solve(n,cl,ch,al,ah,bl,bh);io,y=solve(n,cl,ch,al,ah,bl,bh,'outside_largest',largest=largest);ik,z=solve(n,cl,ch,al,ah,bl,bh,'contributors')
  assert (il,io,ik)==(L,outside,need),(cid,il,io,ik,L,outside,need)
  result=dict(cluster=cid,n=n,OXT_count_min=al,OXT_count_max=ah,AVP_count_min=bl,AVP_count_max=bh,joint_min=L,joint_max=U,joint_min_fraction=L/n,largest_donor=donors[largest],largest_donor_capacity_max=ch[largest],min_joint_outside_largest=outside,min_contributing_donors=need,integer_capacity_intervals_unique=all(a==b for a,b in caps),milp_min_total=il,milp_min_outside_largest=io,milp_min_contributing_donors=ik,spurious_positive_calls_needed_for_zero_true_overlap=L,spurious_calls_per_observation_min=L/n,artifact_barcode_fraction_to_zero_bound=L/n)
  results.append(result)
  for name,xx in [('min_total',x),('min_outside_largest',y),('min_donors',z)]:
   assert xx.sum()==n and al<=sum(xx[:,1]+xx[:,3])<=ah and bl<=sum(xx[:,2]+xx[:,3])<=bh
   for j,donor in enumerate(donors):witness.append(dict(cluster=cid,objective=name,donor=donor,neither=int(xx[j,0]),OXT_only=int(xx[j,1]),AVP_only=int(xx[j,2]),both=int(xx[j,3]),capacity_min=cl[j],capacity_max=ch[j]))
  for j,donor in enumerate(donors):
   minj=max(0,L-sum(ch[t] for t in range(len(donors)) if t!=j));mj,_=solve(n,cl,ch,al,ah,bl,bh,'donor',target_donor=j);assert mj==minj
   perdonor.append(dict(cluster=cid,donor=donor,capacity_min=cl[j],capacity_max=ch[j],joint_min_this_donor=minj,joint_max_this_donor=min(ch[j],U),milp_joint_min_this_donor=mj))
  for fraction in [0,.01,.05,.1,.2,.3,.5]:
   c=math.floor(n*fraction);sensitivity.append(dict(cluster=cid,assumed_max_artifactual_barcodes_or_spurious_binary_calls=c,fraction_of_original_n=c/n,remaining_joint_count_min=max(0,L-c),remaining_joint_over_original_n=max(0,L-c)/n))
  # Exploratory robustness extension: same capacity logic across source studies,
  # not an untouched replication or direct observation of per-study expression.
  for dataset in sorted(set(donor_dataset.values())):
   subset=[j for j,donor in enumerate(donors) if donor_dataset[donor]==dataset]
   bound=max(0,L-sum(ch[j] for j in range(len(donors)) if j not in subset))
   exact,_=solve(n,cl,ch,al,ah,bl,bh,'subset',donor_subset=subset);assert exact==bound
   dataset_bounds.append(dict(cluster=cid,source_dataset=dataset,n_capacity_min=sum(cl[j] for j in subset),n_capacity_max=sum(ch[j] for j in subset),joint_min_in_source=bound,milp_joint_min_in_source=exact))
 # Independent approximate-float derivation must be weaker than integer lower bound.
 for r in results:
  p=float(next(x for x in marker if x['cluster']==r['cluster'] and x['gene']=='OXT')['pct.1']);q=float(next(x for x in marker if x['cluster']==r['cluster'] and x['gene']=='AVP')['pct.1']);assert r['joint_min_fraction']+1e-12>=max(0,p+q-1-.001)
 pd.DataFrame(results).to_csv(H/'integer_bounds.csv',index=False);pd.DataFrame(perdonor).to_csv(H/'donor_bounds.csv',index=False);pd.DataFrame(witness).to_csv(H/'allocation_witnesses.csv',index=False);pd.DataFrame(sensitivity).to_csv(H/'contamination_sensitivity.csv',index=False);pd.DataFrame(dataset_bounds).to_csv(H/'dataset_bounds.csv',index=False)
 out=dict(results=results,exploratory_source_dataset_bounds=dataset_bounds,n_exact_exhaustive_controls=len(controls),control_details=controls,rounding='inclusive±0.0005 for3decimal gene fractions;±0.005 percentage points for2decimal donor percentages',assumptions=['marker percentages and cluster annotationN describe identical barcode universe','donor percentages are fractions of that sameN rounded to2decimal percentage points','integer count/category allocations are observations, not ground-truth genuine neurons','adversarial contamination model counts false positive binary gene calls or wholly artifactual barcodes; not ambientRNA read fraction'],untouched_donor_validation=False,new_raw_data=False)
 (H/'followup_summary.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps({k:out[k] for k in ['results','n_exact_exhaustive_controls','assumptions']},indent=2))
if __name__=='__main__':main()
