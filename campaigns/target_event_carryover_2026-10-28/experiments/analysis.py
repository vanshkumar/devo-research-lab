"""Stimulus-anchored participant-clustered carryover analysis. No validation read without release file."""
from pathlib import Path
import os
os.environ.setdefault('MPLCONFIGDIR','/tmp/target_event_matplotlib')
os.environ.setdefault('OPENBLAS_NUM_THREADS','1')
import csv,json,hashlib,argparse
import numpy as np
from scipy import linalg,stats
from threadpoolctl import threadpool_limits
threadpool_limits(1)
ROOT=Path(__file__).resolve().parents[1]
SOURCE=ROOT.parents[1]/'sources/learning_intervention_feasibility_2026-10-28'
FILES=['tsay_TE_SPE.csv','tsay_controljump.csv']
SPLIT=json.loads((ROOT/'protocol/split.json').read_text())['split']

def mm(a,b):
 """Explicit contractions avoid documented spurious NumPy matmul warnings on this host."""
 a=np.asarray(a);b=np.asarray(b)
 expr={(1,1):'i,i->',(2,1):'ij,j->i',(1,2):'i,ij->j',(2,2):'ij,jk->ik'}[(a.ndim,b.ndim)]
 return np.einsum(expr,a,b,optimize=False)

def num(v):
 try:return float(v)
 except:return np.nan

def verify_release(kind='VALIDATION'):
 record_path=ROOT/'protocol'/f'{kind}_RELEASE.json'
 assert record_path.exists(),'Outcomes sealed'
 record=json.loads(record_path.read_text());fp=ROOT/'protocol/FINAL_FREEZE.json'
 assert hashlib.sha256(fp.read_bytes()).hexdigest()==record['freeze_sha256'],'Freeze record changed'
 frozen=json.loads(fp.read_text())
 for path,h in frozen['files_sha256'].items():
  assert hashlib.sha256((ROOT/path).read_bytes()).hexdigest()==h,'Frozen artifact changed: '+path

def load(part='development',endpoint='Hand_raw',inputs_only=False):
 if part=='all_inputs': assert inputs_only,'all_inputs must never open outcomes'
 if part=='validation' and not inputs_only:
  verify_release('VALIDATION')
 people=[]
 for f in FILES:
  ids=SPLIT[f][part] if part!='all_inputs' else sum(SPLIT[f].values(),[])
  rr={p:[] for p in ids}
  with (SOURCE/f).open() as h:
   for r in csv.DictReader(h):
    if r['SN'] not in rr:continue
    d={'tn':int(r['TN']),'c':num(r['clamp_size']),'j':num(r['tgt_jump_size'])}
    # Outcome values are accessed only for authorized person rows.
    if not inputs_only:d['y']=-num(r[endpoint])
    rr[r['SN']].append(d)
  for sn,rows in rr.items():
   rows.sort(key=lambda x:x['tn']);assert [r['tn'] for r in rows]==list(range(1,825))
   p={k:np.array([r[k] for r in rows]) for k in rows[0]}
   p.update(key=f+':'+sn,file=f,sn=sn,set='A' if f==FILES[0] else 'B')
   if inputs_only:p['y']=np.full(824,np.nan)
   people.append(p)
 return people

def cells_for(p):
 return sorted(set(zip(p['c'][100:280],p['j'][100:280])))

def make_design(people,h,readout='all',level=False,short=False):
 """Design uses all previous cells, zero-clamp indices, full chronology. No response selection except finite/90° mask."""
 cells=cells_for(people[0]); ncell=len(cells); assert ncell==9
 records=[]; Y=[]; groups=[];meta=[]
 # common N basis plus cluster/block nuisance; columns constant across partitions.
 names=['intercept']+[f'block{b}' for b in range(1,4)]+[f'time_block{b}' for b in range(4)]
 names += [f'cell_lag{k}_{q}' for k in range(1,6) for q in range(1,9)]
 names += [f'tail_{a}_{q}' for a in [.8,.95] for q in range(1,9)]
 names += [f'future{k}_cell{q}' for k in range(1,h+1) for q in range(1,9)]
 names += ['index_signedjump']+[f'priorcell{q}_signedindex' for q in range(1,9)]
 names += [f'older{k}_event' for k in range(2,6)]
 # Z is the complete nine prior-cell x (jump -2/3) basis.
 for ip,p in enumerate(people):
  assert cells_for(p)==cells
  c,j,y=p['c'],p['j'],p['y']; cell=np.array([cells.index((cc,jj)) if (cc,jj) in cells else 0 for cc,jj in zip(c,j)])
  for b in range(4):
   start=100+181*b
   for loc in range(20,175):
    t=start+loc
    if c[t]!=0:continue
    if readout=='stationary' and j[t+h]!=0:continue
    yy=y[t+h]; pre=y[t-5:t]
    # The same future validity set for all main horizons enables joint curve inference.
    if not np.all(np.isfinite(y[t+1:t+6])) or np.any(np.abs(y[t+1:t+6])>90):continue
    if not np.all(np.isfinite(pre)) or np.any(np.abs(pre)>90):continue
    event=float(j[t]!=0); sign=np.sign(j[t]); ec=event-2/3
    x=[1.]+[float(b==q) for q in range(1,4)]+[(loc-97)/77*float(b==q) for q in range(4)]
    x.extend(float(cell[t-k]==q) for k in range(1,6) for q in range(1,9))
    for a in [.8,.95]:
     weights=a**np.arange(15);weights/=weights.sum()
     x.extend(sum(weights[k-6]*float(cell[t-k]==q) for k in range(6,21)) for q in range(1,9))
    x.extend(float(cell[t+k]==q) for k in range(1,h+1) for q in range(1,9))
    x.extend([sign]+[sign*float(cell[t-1]==q) for q in range(1,9)])
    x.extend(ec*c[t-k]/4 for k in range(2,6))
    z=[ec*float(cell[t-1]==q) for q in range(9)]
    records.append(x+z);Y.append(yy if level else yy-pre.mean());groups.append(ip)
    meta.append((p['key'],int(p['tn'][t]),b,loc))
 X=np.asarray(records); nn=len(names); N=X[:,:nn];Z=X[:,nn:]; G=np.asarray(groups)
 # Each participant gets intercept and linear slope in each block, centered across people.
 extra=[]
 for ip in range(1,len(people)):
  code=(G==ip).astype(float)-(G==0).astype(float)
  blocks=np.array([m[2] for m in meta]);time=np.array([(m[3]-97)/77 for m in meta])
  extra.extend([code*(blocks==b) for b in range(4)])
  extra.extend([code*(blocks==b)*time for b in range(4)])
 NF=np.column_stack([N,*extra]) if extra else N
 qplus=cells.index((4.,0.));qminus=cells.index((-4.,0.))
 contrast=np.zeros(9);contrast[qplus]=.5;contrast[qminus]=-.5
 marginal=np.array([float(cc)/4/6 for cc,jj in cells]) # uniform within signed old-clamp cells; ± each has 3
 return dict(N=N,NF=NF,Z=Z,Y=np.asarray(Y),groups=G,meta=meta,names=names,cells=cells,contrast=contrast,marginal=marginal,people=[p['key'] for p in people],h=h,readout=readout,level=level)

def residualizer(N):
 Q,R,piv=linalg.qr(N,mode='economic',pivoting=True,check_finite=False)
 diag=np.abs(np.diag(R)); rank=int(np.sum(diag>diag[0]*1e-10));Q=Q[:,:rank]
 return Q,rank

def prepare(d):
 Q,rank=residualizer(d['NF']);Z=d['Z'];RZ=Z-mm(Q,mm(Q.T,Z))
 zz=mm(RZ.T,RZ)
 inv=linalg.solve(zz,np.eye(9),assume_a="sym");W=mm(inv,RZ.T)
 return dict(Q=Q,rank=rank,W=W,RZ=RZ,d=d,p=rank+np.linalg.matrix_rank(RZ))

def fit(prep,y=None):
 d=prep['d']; y=d['Y'] if y is None else y; Q,W=prep['Q'],prep['W'];Z=d['Z']
 beta=mm(W,y);res=y-mm(Q,mm(Q.T,y))-mm(prep["RZ"],beta)
 g=d['groups'];ng=len(d['people']);n=len(y);p=prep['p']
 score=np.array([mm(W[:,g==i],res[g==i]) for i in range(ng)])
 correction=ng/(ng-1)*(n-1)/max(1,n-p)
 score*=np.sqrt(correction)
 cov=mm(score.T,score)
 out={'beta':beta,'cov':cov,'scores':score,'residual_sd':np.sqrt(np.mean(res**2)),'n':n,'p':p,'rankZ':int(np.linalg.matrix_rank(prep['RZ']))}
 for key in ['contrast','marginal']:
  v=d[key];est=float(mm(v,beta));se=float(np.sqrt(mm(mm(v,cov),v)));crit=stats.t.ppf(.975,ng-1)
  out[key]={'estimate':est,'se':se,'low':est-crit*se,'high':est+crit*se,'scores':mm(score,v)}
 return out

def predict_fit(d):
 # Fit common stimulus/time coefficients only. Reserved endpoints never calibrate coefficients.
 N,Z,y=d['N'],d['Z'],d['Y']; A=np.column_stack([N,Z])
 keep=[i for i,n in enumerate(d['names']) if not n.startswith('older') and not (n.startswith('priorcell') and n.endswith('signedindex'))]
 restricted=np.column_stack([N[:,keep],Z.sum(axis=1)])
 return {'restricted':linalg.lstsq(restricted,y,cond=1e-9,lapack_driver='gelsd')[0], 'restricted_keep':keep, 'full':linalg.lstsq(A,y,cond=1e-9,lapack_driver='gelsd')[0]}

def curve_summary(fits,key='contrast'):
 G=len(fits[0][key]['scores']);S=np.array([f[key]['scores'] for f in fits]).T
 curve=np.array([f[key]['estimate'] for f in fits]);cov=mm(S.T,S)
 est=curve.mean();se=np.sqrt(cov.mean());crit=stats.t.ppf(.975,G-1)
 return dict(estimate=float(est),se=float(se),low=float(est-crit*se),high=float(est+crit*se),curve=curve.tolist(),cov=cov.tolist(),people=G)

def pooled_summary(summaries):
 est=np.mean([s['estimate'] for s in summaries]);se=np.sqrt(sum(s['se']**2 for s in summaries))/len(summaries)
 variances=np.array([s['se']**2 for s in summaries]); dfs=np.array([s['people']-1 for s in summaries])
 df=float(variances.sum()**2/np.sum(variances**2/dfs));crit=stats.t.ppf(.975,df)
 return dict(estimate=float(est),se=float(se),low=float(est-crit*se),high=float(est+crit*se),people=sum(s['people'] for s in summaries),df=df,curve=np.mean([s['curve'] for s in summaries],axis=0).tolist())

def jsonable(x):
 if isinstance(x,np.ndarray):return x.tolist()
 if isinstance(x,np.generic):return x.item()
 if isinstance(x,dict):return {k:jsonable(v) for k,v in x.items()}
 if isinstance(x,list):return [jsonable(v) for v in x]
 return x

def run(part,endpoint='Hand_raw',level=False,readout='all',save_predictions=True):
 if part=='validation': save_predictions=False
 people=load(part,endpoint);out={};summaries=[];marginals=[]; pred={}
 for f in FILES:
  pp=[p for p in people if p['file']==f];fits=[]
  for h in range(1,6):
   d=make_design(pp,h,readout,level);prep=prepare(d);ft=fit(prep);fits.append(ft)
   if save_predictions:pred[f+':'+str(h)]=jsonable(predict_fit(d))
  ss=curve_summary(fits);ms=curve_summary(fits,'marginal');summaries.append(ss);marginals.append(ms)
  out[f]={'summary':ss,'marginal_summary':ms,'lags':fits}
 out['pooled']=pooled_summary(summaries);out['pooled_marginal']=pooled_summary(marginals)
 out['settings']=dict(part=part,endpoint=endpoint,level=level,readout=readout)
 stem=f'{part}_{endpoint}_{"level" if level else "change"}_{readout}'
 (ROOT/'outputs'/f'{stem}.json').write_text(json.dumps(jsonable(out),indent=2)+'\n')
 if save_predictions:(ROOT/'outputs'/f'{stem}_predictions.json').write_text(json.dumps(pred,indent=2)+'\n')
 print(stem,json.dumps(out['pooled']),flush=True)
 return out

if __name__=='__main__':
 ap=argparse.ArgumentParser();ap.add_argument('--part',default='development',choices=['development','validation']);ap.add_argument('--endpoint',default='Hand_raw');ap.add_argument('--level',action='store_true');ap.add_argument('--readout',default='all');args=ap.parse_args()
 run(args.part,args.endpoint,args.level,args.readout)
