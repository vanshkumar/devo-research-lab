"""Reserved contrasts and forecasts with frozen development coefficients."""
from analysis import *
from ordinary_response import run_ordinary

def prediction_evaluation(part='validation',readout='all'):
 frozen=json.loads((ROOT/'protocol'/f'PREDICTORS_{readout}.json').read_text());people=load(part);personloss={}
 for f in FILES:
  pp=[p for p in people if p['file']==f]
  for h in range(1,6):
   d=make_design(pp,h,readout);model=frozen[f+':'+str(h)];N=d['N'];Z=d['Z'];y=d['Y'];keep=model['restricted_keep']
   pr=mm(np.column_stack([N[:,keep],Z.sum(axis=1)]),np.array(model['restricted']))
   pf=mm(np.column_stack([N,Z]),np.array(model['full']))
   for ip,p in enumerate(pp):
    mask=d['groups']==ip;v=personloss.setdefault(p['key'],{'restricted':[],'full':[],'zero':[],'n':[]})
    v['zero'].append(float(np.mean(y[mask]**2)));v['restricted'].append(float(np.mean((y[mask]-pr[mask])**2)));v['full'].append(float(np.mean((y[mask]-pf[mask])**2)));v['n'].append(int(mask.sum()))
 rows=[]
 for key,v in personloss.items():rows.append({'person':key,'restricted_mse':np.mean(v['restricted']),'full_mse':np.mean(v['full']),'zero_change_mse':np.mean(v['zero']),'gain':np.mean(v['restricted'])-np.mean(v['full']),'events_by_horizon':v['n']})
 sets={}
 for f in FILES:
  vals=np.array([r['gain'] for r in rows if r['person'].startswith(f+':')]);sets[f]={'estimate':float(vals.mean()),'se':float(vals.std(ddof=1)/np.sqrt(len(vals))),'people':len(vals)}
 est=np.mean([s['estimate'] for s in sets.values()]);v=np.array([s['se']**2 for s in sets.values()]);se=np.sqrt(v.sum())/2;df=v.sum()**2/np.sum(v*v/np.array([s['people']-1 for s in sets.values()]));crit=stats.t.ppf(.975,df)
 out=dict(part=part,readout=readout,interpretation='Positive means lower squared prediction error for development-fitted full propagation model; no reserved coefficient calibration.',set_summaries=sets,df=float(df),gain=float(est),se=float(se),low=float(est-crit*se),high=float(est+crit*se),restricted_mse=float(np.mean([r['restricted_mse'] for r in rows])),full_mse=float(np.mean([r['full_mse'] for r in rows])),zero_change_mse=float(np.mean([r['zero_change_mse'] for r in rows])),people=rows)
 (ROOT/'outputs'/f'{part}_prediction_{readout}.json').write_text(json.dumps(jsonable(out),indent=2)+'\n');print('prediction',readout,{k:v for k,v in out.items() if k!='people'})
 return out

def relative(part):
 a=json.loads((ROOT/'outputs'/f'{part}_Hand_raw_change_all.json').read_text());b=json.loads((ROOT/'outputs'/f'{part}_ordinary_response.json').read_text())
 th=a['pooled']['estimate'];nu=b['pooled']['estimate'];va=a['pooled']['se']**2;vb=b['pooled']['se']**2;cov=0
 for f in FILES:
  sa=np.mean([z['contrast']['scores'] for z in a[f]['lags']],axis=0)
  sb=np.mean([z['contrast']['scores'] for z in b[f]['lags']],axis=0);cov+=float(mm(sa,sb))/4
 df=min([a[f]['summary']['people']-1 for f in FILES]);t=stats.t.ppf(.975,df);A=nu**2-t*t*vb;B=-2*th*nu+2*t*t*cov;C=th**2-t*t*va;disc=B*B-4*A*C
 bounds=sorted([(-B-np.sqrt(disc))/(2*A),(-B+np.sqrt(disc))/(2*A)]) if A>0 and disc>=0 else None
 out={'ratio':th/nu,'fieller95':bounds,'numerator':th,'denominator':nu,'covariance':cov,'df':df,'note':'Approximate clustered Fieller interval with conservative minimum set cluster df; ratio of signed half-contrasts, unbounded if denominator uncertainty precludes bounded interval.'}
 (ROOT/'outputs'/f'{part}_relative_effect.json').write_text(json.dumps(out,indent=2)+'\n');print('relative',out)
 return out

if __name__=='__main__':
 ap=argparse.ArgumentParser();ap.add_argument('--part',default='validation');args=ap.parse_args();part=args.part
 for endpoint,level,readout in [('Hand_raw',False,'all'),('Hand_raw',True,'all'),('Hand_raw',False,'stationary'),('Hand',False,'all'),('Hand_dt',False,'all')]:run(part,endpoint,level,readout,save_predictions=False)
 run_ordinary(part);relative(part)
 if part=='validation':
  for readout in ['all','stationary']:prediction_evaluation(part,readout)
