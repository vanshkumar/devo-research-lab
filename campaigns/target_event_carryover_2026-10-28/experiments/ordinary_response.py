"""Level-based ordinary prior-clamp contrast and ratio denominator."""
from analysis import *
def run_ordinary(part):
 out={};summaries=[]
 for f in FILES:
  pp=[p for p in load(part) if p['file']==f];fits=[]
  for h in range(1,6):
   d=make_design(pp,h,level=True);prep=prepare(d);ft=fit(prep)
   nv=np.zeros(d['NF'].shape[1])
   for cell,w in zip(d['cells'],d['contrast']):
    q=d['cells'].index(cell)
    if q:nv[d['names'].index(f'cell_lag1_{q}')]=w
   base_weights=linalg.lstsq(d['NF'].T,nv,cond=1e-10,lapack_driver='gelsd')[0]
   # alpha = N+ (y-Z beta), index event centered at -2/3 for stationary.
   weights=base_weights-mm(mm(base_weights,d['Z']),prep['W'])-2/3*mm(d['contrast'],prep['W'])
   residual=d['Y']-mm(prep['Q'],mm(prep['Q'].T,d['Y']))-mm(prep['RZ'],ft['beta'])
   G=d['groups'];ng=len(pp);n=len(G);cor=np.sqrt(ng/(ng-1)*(n-1)/(n-prep['p']))
   scores=np.array([mm(weights[G==i],residual[G==i])*cor for i in range(ng)])
   estimate=mm(weights,d['Y']);se=np.sqrt(mm(scores,scores));crit=stats.t.ppf(.975,ng-1)
   fits.append({'contrast':dict(estimate=float(estimate),se=float(se),low=float(estimate-crit*se),high=float(estimate+crit*se),scores=scores)})
  ss=curve_summary(fits);summaries.append(ss);out[f]=dict(summary=ss,lags=fits)
 out['pooled']=pooled_summary(summaries)
 (ROOT/'outputs'/f'{part}_ordinary_response.json').write_text(json.dumps(jsonable(out),indent=2)+'\n');print(part,'ordinary response',out['pooled'])
if __name__=='__main__':
 import sys
 run_ordinary(sys.argv[1] if len(sys.argv)>1 else 'development')
