"""Input/support diagnostics, not prediction scoring."""
import os
for k in ['OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','VECLIB_MAXIMUM_THREADS','NUMEXPR_NUM_THREADS']:os.environ[k]='1'
from pathlib import Path
import json, resource
import numpy as np
OUT=Path(__file__).resolve().parent

def load():
    with np.load(OUT/'consumed_inputs.npz',allow_pickle=False) as z:
        n=len([k for k in z.files if k.endswith('__subject')])
        return [{k.split('__',1)[1]:z[k] for k in z.files if k.startswith(str(i)+'__')} for i in range(n)]

def main():
    data=load();out={}
    for species in ['human','mouse']:
        ds=[d for d in data if str(d['species'])==species]
        stats={}
        for window,lo,hi in [('early',200,600),('full',200,6000)]:
            stats[window]={}
            for mode in ['all','within_session32','first_session','repNum_equals_1']:
                counts={};nr=0;nu=0;zero=0;changes=[];hs=[];xs=[]
                for d in ds:
                    t=d['trial'];m=(t>=lo)&(t<hi)
                    if mode=='within_session32':m &= d['session_trial']>=32
                    if mode=='first_session':m &= d['session']==0
                    if mode=='repNum_equals_1':m &= d['repNum']==1 if species=='mouse' else np.ones(len(t),bool)
                    nu+=int(m.any());nr+=int(m.sum());zero+=int(np.sum(m&(d['contrast']==0)))
                    for c in np.unique(np.abs(d['contrast'][m])):counts[str(c)]=counts.get(str(c),0)+int(np.sum(m&(np.abs(d['contrast'])==c)))
                    hs.append(np.column_stack([d['h2'][m],d['h8'][m],d['h32'][m]]));xs.append(d['contrast'][m])
                h=np.concatenate(hs);x=np.concatenate(xs)
                stats[window][mode]=dict(units=nu,rows=nr,zero=zero,contrasts=counts,
                       history_quantiles=np.quantile(h,[0,.05,.25,.5,.75,.95,1],axis=0).tolist() if len(h) else [],
                       history_sensory_correlations=[float(np.corrcoef(h[:,j],x)[0,1]) for j in range(3)] if len(h) else [])
        out[species]=stats
    (OUT/'INPUT_SUPPORT.json').write_text(json.dumps(out,indent=2)+'\n')
    print(json.dumps(out,indent=2))

if __name__=='__main__':main()
