"""Bounded exploratory likelihood and design checks; see FOLLOWUP_PLAN.md."""
import json,pathlib,math
import numpy as np,pandas as pd
from scipy import optimize,special,linalg,stats
from numpy.polynomial.hermite import hermgauss
H=pathlib.Path(__file__).parent

def linear(x,b):return np.einsum('ij,j->i',x,b,optimize=False)
def logistic_nll(b,x,y):
 eta=linear(x,b);return float(np.sum(np.logaddexp(0,eta)-y*eta))
def hessian(f,b,h=2e-4):
 k=len(b);e=np.eye(k)*h;out=np.zeros((k,k))
 for i in range(k):
  for j in range(k):out[i,j]=(f(b+e[i]+e[j])-f(b+e[i]-e[j])-f(b-e[i]+e[j])+f(b-e[i]-e[j]))/(4*h*h)
 return out

def glmm(x,y,group,nodes=40):
 z,w=hermgauss(nodes);lw=np.log(w)-.5*np.log(np.pi);idx=[np.flatnonzero(group==g) for g in np.unique(group)]
 def f(b):
  eta=linear(x,b[:-1]);sd=np.exp(b[-1]);ans=0.
  for ix in idx:
   v=eta[ix][None,:]+np.sqrt(2)*sd*z[:,None];ll=(y[ix][None,:]*v-np.logaddexp(0,v)).sum(1);ans-=special.logsumexp(lw+ll)
  return float(ans)
 initial=optimize.minimize(logistic_nll,np.zeros(x.shape[1]),args=(x,y),method='BFGS').x
 fits=[optimize.minimize(f,np.r_[initial,s],method='L-BFGS-B',bounds=[(None,None)]*len(initial)+[(-7,1.5)],options={'ftol':1e-12,'gtol':1e-6}) for s in [-3.,-1.,0.]]
 best=min(fits,key=lambda r:r.fun);b=best.x;hh=hessian(f,b)
 try:
  cov=linalg.inv(hh);diag=np.diag(cov)[:-1]
  if np.any(diag<=0):raise ValueError('invalid Hessian diagonal')
  se=np.sqrt(diag)
 except (ValueError,linalg.LinAlgError):
  p=special.expit(linear(x,b[:-1]));info=np.einsum('ni,n,nj->ij',x,p*(1-p),x,optimize=False);se=np.sqrt(np.diag(linalg.inv(info)))
 return dict(beta=b[:-1].tolist(),se=se.tolist(),wald_p_approx=(2*stats.norm.sf(np.abs(b[:-1]/se))).tolist(),date_sd=float(np.exp(b[-1])),nll=float(best.fun),converged=bool(best.success),nodes=nodes),f

def main():
 d=pd.read_csv(H/'reconstructed_trials.csv');g=pd.factorize(d.date)[0];X=np.c_[np.ones(len(d)),(d.treatment=='C1').astype(float),(d.treatment=='C2').astype(float)]
 designs=[('archived_script_all',d.copy_dc_bin.notna().values,d.copy_dc_bin.values),('eligible_first_single',d.eligible.values,d.copy_first.values),('eligible_last_single',d.eligible.values,d.copy_last.values)]
 fits={}
 for name,ix,y in designs:
  a,f=glmm(X[ix],y[ix],g[ix],40);b,_=glmm(X[ix],y[ix],g[ix],80)
  a.update(n=int(ix.sum()),nodes80_beta=b['beta'],quadrature_max_beta_difference=float(np.max(np.abs(np.array(a['beta'])-b['beta']))),quadrature_nll_difference=float(abs(a['nll']-b['nll'])))
  fits[name]=a
 ix=d.eligible.values;y=d.copy_first.values[ix];x=X[ix];grp=g[ix];fit,f=glmm(x,y,grp)
 b=np.array([.3,-.2,.1]);zero_error=abs(f(np.r_[b,-25.])-logistic_nll(b,x,y));assert zero_error<1e-10
 rng=np.random.default_rng(1509);gr=np.repeat(np.arange(100),30);xs=np.c_[np.ones(len(gr)),rng.normal(size=len(gr))];bs=np.array([-.3,.8]);effects=rng.normal(0,.6,100)
 ys=(rng.random(len(gr))<special.expit(linear(xs,bs)+effects[gr])).astype(float);control,_=glmm(xs,ys,gr,40)
 assert max(abs(np.array(control['beta'])-bs))<.15 and abs(control['date_sd']-.6)<.20
 q=d[d.eligible].copy();y=q.copy_first.values;c=np.where(q.first_single=='p',1.,-1.);is_t=(q.treatment=='T').values;profiles=[]
 for r in np.linspace(0,2,201):
  x=np.c_[np.where(is_t,1-r,1),c];rr=optimize.minimize(logistic_nll,np.array([.5,0.]),args=(x,y),method='L-BFGS-B',bounds=[(0,4),(None,None)],options={'ftol':1e-13})
  profiles.append(dict(relative_second_weight=float(r),g=float(rr.x[0]),color_bias=float(rr.x[1]),log_likelihood=float(-rr.fun)))
 prof=pd.DataFrame(profiles);best=prof.iloc[prof.log_likelihood.argmax()];prof['relative_likelihood']=np.exp(prof.log_likelihood-best.log_likelihood);prof.to_csv(H/'weight_profile.csv',index=False)
 powers=[]
 for gg in [.2,float(best.g),.8]:
  pa=float(special.expit(gg));pb=1-pa
  for n in [32,64,100,150,200,300,500]:
   critical=next((k for k in range(n+1) if stats.binom.sf(k-1,n,pb)<=.05),n+1)
   powers.append(dict(g=gg,n_eligible=n,p_gate_A=pa,p_accumulator_A=pb,critical_gate_count=critical,test_size=float(stats.binom.sf(critical-1,n,pb)),power=float(stats.binom.sf(critical-1,n,pa))))
 pd.DataFrame(powers).to_csv(H/'design_power.csv',index=False)
 p=.35;n=8;k=5;tail=sum(math.comb(n,j)*p**j*(1-p)**(n-j) for j in range(k,n+1));tail_error=abs(tail-stats.binom.sf(k-1,n,p));assert tail_error<1e-13
 diagnostics=[]
 for t in ['T','C1','C2']:
  for inclusion in ['eligible','mating']:
   a=d[(d.treatment==t)&d[inclusion]];diagnostics.append(dict(treatment=t,inclusion=inclusion,n=len(a),choice_matches_first_courter=float((a.test_color==a.color_court_1).mean()),first_courter_matches_demo=float((a.color_court_1==a.first_single).mean()),copy_first=float(a.copy_first.mean())))
 pd.DataFrame(diagnostics).to_csv(H/'courtship_diagnostics.csv',index=False)
 m=d[(d.treatment=='T')&d.mating];table=[[int(((m.copy_first==choice)&(m.eligible==elig)).sum()) for elig in [True,False]] for choice in [1,0]];odds,pf=stats.fisher_exact(table)
 result=dict(regressions=fits,controls=dict(zero_sd_nll_error=zero_error,known_beta=bs.tolist(),known_date_sd=.6,fit=control,binomial_tail_error=tail_error),weight_family=dict(best=best.to_dict(),fixed_models={name:prof.iloc[idx].to_dict() for name,idx in [('gate',0),('equal_evidence',100),('recency',200)]},assumption='common single-demonstration gain and stable color bias; no direct measurement of memory or update rule'),selection=dict(main_choice_by_eligibility_table=table,rows=['first_demo_choice','second_demo_choice'],cols=['eligible','not_eligible'],fisher_oddsratio=float(odds),fisher_p=float(pf)),design_note='ABB predictions and power condition on gate vs symmetric equal-weight accumulation, known gain and independent eligible trials. They do not identify all mechanisms or correct post-treatment selection.')
 (H/'followup_summary.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
if __name__=='__main__':main()
