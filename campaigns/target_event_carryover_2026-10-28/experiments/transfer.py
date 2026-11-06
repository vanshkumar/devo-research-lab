"""Frozen Fig3 transfer of prior-input interaction, not an exact zero-clamp replication."""
from analysis import *

def load_external(inputs_only=False):
 if not inputs_only:verify_release('TRANSFER')
 rows={}
 with (SOURCE/'task_success_fig3.csv').open() as h:
  for r in csv.DictReader(h):
   sn=r['Subject'];d=dict(tn=int(r['TrialNum']),c=num(r['ClampAngle']),j=num(r['TargetJump']))
   if not inputs_only:d['y']=-num(r['HandError'])
   rows.setdefault(sn,[]).append(d)
 out=[]
 for sn,rr in sorted(rows.items(),key=lambda kv:int(kv[0])):
  rr.sort(key=lambda x:x['tn']);assert [r['tn'] for r in rr]==list(range(1,905))
  p={k:np.array([r[k] for r in rr]) for k in rr[0]};p.update(key='external3:'+sn,sn=sn)
  if inputs_only:p['y']=np.zeros(904)
  out.append(p)
 return out

def make_external_design(people,h,readout='all',level=False):
 cells=sorted(set(zip(people[0]['c'][103:903],people[0]['j'][103:903])));assert len(cells)==8
 names=['intercept']+[f'epoch{b}' for b in range(1,4)]+[f'time_epoch{b}' for b in range(4)]
 names += [f'cell_lag{k}_{q}' for k in range(1,6) for q in range(1,8)]
 names += [f'tail_{a}_{q}' for a in [.8,.95] for q in range(1,8)]
 names += [f'future{k}_cell{q}' for k in range(1,h+1) for q in range(1,8)]
 names += ['index_clamp','index_clamp_event']+[f'priorcell{q}_signedindex' for q in range(1,8)]
 names += [f'older{k}_event' for k in range(2,6)]
 N=[];Z=[];Y=[];G=[];meta=[]
 for ip,p in enumerate(people):
  c,j,y=p['c'],p['j'],p['y'];cell=np.array([cells.index((cc,jj)) if (cc,jj) in cells else 0 for cc,jj in zip(c,j)])
  for t in range(123,898):
   if not (j[t]==0 or j[t]==c[t]):continue
   if readout=='stationary' and j[t+h]!=0:continue
   pre=y[t-5:t]
   if not np.all(np.isfinite(y[t+1:t+6])) or np.any(np.abs(y[t+1:t+6])>90):continue
   if not np.all(np.isfinite(pre)) or np.any(np.abs(pre)>90):continue
   event=float(j[t]!=0);ec=event-.5;sign=c[t]/4; b=(t-103)//200;loc=(t-103)%200
   x=[1.]+[float(b==q) for q in range(1,4)]+[(loc-100)/100*float(b==q) for q in range(4)]
   x.extend(float(cell[t-k]==q) for k in range(1,6) for q in range(1,8))
   for a in [.8,.95]:
    w=a**np.arange(15);w/=w.sum();x.extend(sum(w[k-6]*float(cell[t-k]==q) for k in range(6,21)) for q in range(1,8))
   x.extend(float(cell[t+k]==q) for k in range(1,h+1) for q in range(1,8))
   x.extend([sign,sign*ec]+[sign*ec*float(cell[t-1]==q) for q in range(1,8)])
   x.extend(ec*c[t-k]/4 for k in range(2,6))
   N.append(x);Z.append([ec*float(cell[t-1]==q) for q in range(8)]);Y.append(y[t+h] if level else y[t+h]-pre.mean());G.append(ip);meta.append((p['key'],int(p['tn'][t]),b,loc))
 N=np.array(N);Z=np.array(Z);G=np.array(G);extra=[];blocks=np.array([m[2] for m in meta]);time=np.array([(m[3]-100)/100 for m in meta])
 for ip in range(1,len(people)):
  code=(G==ip).astype(float)-(G==0).astype(float)
  extra.extend([code*(blocks==b) for b in range(4)]);extra.extend([code*(blocks==b)*time for b in range(4)])
 NF=np.column_stack([N,*extra]);v=np.zeros(8);v[cells.index((4.,0.))]=.5;v[cells.index((-4.,0.))]=-.5
 return dict(N=N,NF=NF,Z=Z,Y=np.array(Y),groups=G,meta=meta,names=names,cells=cells,contrast=v,marginal=v,people=[p['key'] for p in people],h=h,readout=readout,level=level)

def prep_external(d):
 Q,rank=residualizer(d['NF']);RZ=d['Z']-mm(Q,mm(Q.T,d['Z']));W=mm(linalg.solve(mm(RZ.T,RZ),np.eye(8),assume_a='sym'),RZ.T)
 return dict(Q=Q,rank=rank,W=W,RZ=RZ,d=d,p=rank+8)

def run_transfer():
 pp=load_external();out={}
 frozen=json.loads((ROOT/'protocol/TRANSFER_PREDICTION.json').read_text())
 for readout in ['all','stationary']:
  fits=[fit(prep_external(make_external_design(pp,h,readout))) for h in range(1,6)];ss=curve_summary(fits)
  expected=frozen['predictions'][readout];delta=ss['estimate']-expected['estimate'];se=np.sqrt(ss['se']**2+expected['se']**2)
  # Compatibility uses independent participant uncertainty in both laboratories.
  df=(ss['se']**2+expected['se']**2)**2/(ss['se']**4/(ss['people']-1)+expected['se']**4/(expected['people']-1))
  comp={'external_minus_prediction':delta,'se':se,'df':df,'low':delta-stats.t.ppf(.975,df)*se,'high':delta+stats.t.ppf(.975,df)*se,'external95_contains_point_prediction':ss['low']<=expected['estimate']<=ss['high']}
  out[readout]={'summary':ss,'lags':fits,'prediction':expected,'compatibility':comp}
 (ROOT/'outputs/transfer_fig3.json').write_text(json.dumps(jsonable(out),indent=2)+'\n')
 print(json.dumps({k:{'summary':v['summary'],'compatibility':v['compatibility']} for k,v in out.items()},indent=2))
if __name__=='__main__':
 import sys
 if '--inputs-only' in sys.argv:
  pp=load_external(True);info={r:[{'h':h,'n':len(make_external_design(pp,h,r)['Y'])} for h in range(1,6)] for r in ['all','stationary']};(ROOT/'outputs/transfer_input_support.json').write_text(json.dumps(info,indent=2));print(info)
 else:run_transfer()
