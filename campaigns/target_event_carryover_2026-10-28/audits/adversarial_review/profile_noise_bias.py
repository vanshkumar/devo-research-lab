"""Exact expected profiled SSE under known colored noise; INPUTS ONLY.

This diagnoses a possible incidental-parameter bias without any fitted human
outcomes and without Monte Carlo. Noise covariance is stipulated, not inferred.
"""
from pathlib import Path
import sys,json,time
import numpy as np
from scipy import linalg
from scipy.linalg.blas import dgemm
R=Path(__file__).resolve().parents[2];sys.path.insert(0,str(R/'experiments'))
from analysis import load,mm,jsonable
from state_models import cell_design,state_design,profile,curves,counts_for_truth,calibrated_delta
from generators import generate
ps=load('development',inputs_only=True);counts=[counts_for_truth(p) for p in ps]
delta,true=calibrated_delta(.2,.65,1.,np.ones(20),counts);truthpars=[.65,.97,.65+delta]
for p in ps:p['y']=generate(p['c'],p['j'],kind='retention',effect=delta*np.mean(.65**np.arange(5)),gains=(1.,.2),noise_sd=0,drift_scale=0)['clean']
ds=[cell_design(p) for p in ps]
ids=ds[0]['indices'];lag=np.abs(ids[:,None]-ids[None,:]);colored=6.25*(.35*.7**lag+.65*.25**lag)
white=np.eye(720)*6.25;trace=float(np.trace(colored));records=[]
candidates=[truthpars]+[[a,s,e] for a in [.65,.70,.75] for s in [.97,.995] for e in [.90,.95,1.0]]
for pars in candidates:
 signal=0.;capcolor=0.;capwhite=0.;ranktotal=0
 for d in ds:
  X=np.column_stack([d['N'],state_design(d,pars)])
  Q,RR,piv=linalg.qr(X,mode='economic',pivoting=True,check_finite=False);rank=int(np.sum(np.abs(np.diag(RR))>abs(RR[0,0])*1e-10));Q=Q[:,:rank]
  residual=d['y']-mm(Q,mm(Q.T,d['y']));signal+=float(mm(residual,residual))
  CQ=dgemm(1.,colored,Q);capcolor+=float(np.sum(Q*CQ));capwhite+=6.25*rank;ranktotal+=rank
 sse,rows=profile(ds,pars,True);theta=float(curves(ds,{'parameters':pars,'people':rows}).mean())
 records.append(dict(parameters=pars,profiled_theta=theta,noiseless_signal_SSE=signal,
  expected_colored_noise_SSE=20*trace-capcolor,expected_colored_profile_SSE=signal+20*trace-capcolor,
  expected_white_noise_SSE=20*trace-capwhite,expected_white_profile_SSE=signal+20*trace-capwhite,
  total_rank=ranktotal))
base=records[0]
for r in records:
 r['colored_total_minus_true']=r['expected_colored_profile_SSE']-base['expected_colored_profile_SSE']
 r['white_total_minus_true']=r['expected_white_profile_SSE']-base['expected_white_profile_SSE']
 r['colored_noise_minus_true']=r['expected_colored_noise_SSE']-base['expected_colored_noise_SSE']
out=dict(scope='Development INPUT schedules only; exact expected profiled loss for stipulated mean/covariance.',true_theta=true,true_parameters=truthpars,
 noise_sd=2.5,noise_covariance='6.25*(.35*.7**distance+.65*.25**distance)',
 formula='E[min_beta ||y-X_lambda beta||^2]=||(I-P_lambda)mu||^2+tr((I-P_lambda)Sigma)',
 implication='If a wrong lambda has smaller expected profile SSE, many-person OLS profiling with fixed trials can prefer it even though the mean model family contains truth. This is not an optimizer artifact.',records=records)
(R/'audits/adversarial_review/profile_noise_bias.json').write_text(json.dumps(jsonable(out),indent=2)+'\n')
for r in sorted(records,key=lambda r:r['expected_colored_profile_SSE'])[:5]:print(r)
