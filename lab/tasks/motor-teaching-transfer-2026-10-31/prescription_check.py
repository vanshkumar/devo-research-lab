"""Fit one published prescription on consumed sources; no target outcomes."""
import os
for k in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','VECLIB_MAXIMUM_THREADS','NUMEXPR_NUM_THREADS'):
    os.environ[k]='1'
import json,resource,hashlib
from datetime import datetime,timezone
from pathlib import Path
import numpy as np
from scipy.optimize import least_squares,lsq_linear
from threadpoolctl import threadpool_limits

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]

def dot(a,b):return np.einsum('...i,i->...',np.asarray(a),np.asarray(b))

def rows(source,channel='current_plus_next',indices=None):
    cells=[tuple(c) for c in source['input_cells']];idx={c:i for i,c in enumerate(cells)}
    people=source['people'] if indices is None else [source['people'][i] for i in indices]
    vals=np.asarray([p[channel] for p in people]);m=vals.mean(axis=0)
    baseline=-.5*(m[idx[(4.,0.,0)]]-m[idx[(-4.,0.,0)]])
    cc=[]
    for c,j,f in cells:
        if f or c<0 or (c==0 and j<=0) or j==0:continue
        neg=(-c,-j,f)
        if neg not in idx:continue
        signed=.5*(m[idx[(c,j,f)]]-m[idx[neg]])
        cc.append([c,j,baseline,signed])
    return np.array(cc),baseline

def predict(par,table):
    sigma,g,t=par;c,j,A=table[:,:3].T
    val=-(g*A-c*t)*np.exp(-j*j/(2*sigma*sigma))+t*(j-c)
    val=np.where(c==0,t*j,val)
    assert np.isfinite(val).all()
    return val

def fit(table):
    result=[]
    for sigma in (2.,8.,32.):
        r=least_squares(lambda p:predict(p,table)-table[:,3], [sigma,.7,.01],
                        bounds=([1e-5,1e-5,1e-5],[100.,1.,40.]),xtol=1e-12,ftol=1e-12,gtol=1e-12,max_nfev=300)
        result.append(r)
    r=min(result,key=lambda r:float(np.sum(r.fun*r.fun)))
    return dict(parameters=r.x.tolist(),SSE=float(np.sum(r.fun*r.fun)),
                jacobian_singular_values=np.linalg.svd(r.jac,compute_uv=False).tolist(),
                multistart_SSE=[float(np.sum(x.fun*x.fun)) for x in result],success=bool(r.success))

def main():
    data=json.loads((HERE/'ENDPOINT_CONTROL.json').read_text());aa=data['sources'][:2];ff=data['sources'][2]
    tables=[rows(s)[0] for s in aa];table=np.vstack(tables);cal=fit(table)
    rng=np.random.default_rng(3152026);forecasts=[];boot=[]
    for _ in range(500):
        parts=[rows(s,indices=rng.integers(len(s['people']),size=len(s['people'])))[0] for s in aa]
        tab=np.vstack(parts);f=fit(tab);boot.append(f['parameters'])
        sigma,g,t=f['parameters']
        # Predict ratio at exactly source-supported target-to c4, with Figure3 stationary amplitude supplied as a declared nuisance calibration.
        F,base=rows(ff,indices=rng.integers(len(ff['people']),size=len(ff['people'])))
        target=np.array([[4.,4.,base,0.]])
        forecasts.append(-predict(f['parameters'],target)[0]/base)
    boot=np.asarray(boot)
    profiles=[]
    c,j,A=table[:,:3].T
    for sig in np.geomspace(.3,100,160):
        e=np.exp(-j*j/(2*sig*sig))
        x=np.c_[-A*e,c*e+j-c]
        x[c==0,0]=0;x[c==0,1]=j[c==0]
        r=lsq_linear(x,table[:,3],bounds=([1e-5,1e-5],[1.,40.]),tol=1e-12)
        pred=dot(x,r.x)
        profiles.append(dict(sigma=float(sig),g=float(r.x[0]),slope=float(r.x[1]),SSE=float(np.sum((pred-table[:,3])**2))))
    cal['parameters_bootstrap95']=np.quantile(boot,[.025,.975],axis=0).tolist()
    pred=predict(cal['parameters'],table)
    F,base=rows(ff);target=np.array([[4.,4.,base,0.]])
    predicted_jump=-float(predict(cal['parameters'],target)[0]);obs=ff['summary']['Jump To']['current_plus_next']['estimate']
    exact=ROOT/'campaigns/target_event_carryover_2026-10-28/audits/source_measurement/code/TargetJumpModels.R'
    body=exact.read_bytes()
    out=dict(created_utc=datetime.now(timezone.utc).isoformat(),
      prescription='Tsay2022 SPEdisruptTElinear; one account, no model tournament',
      code=dict(path=str(exact.relative_to(ROOT)),bytes=len(body),sha256=hashlib.sha256(body).hexdigest()),
      formula='signed dH=-(g*A4-c*t)*exp(-j^2/(2*sigma^2))+t*(j-c); c=0 gives t*j; stationary nonzero clamp gives -A4',
      source_scope='TsayA/B40, additive endpoint-expression diagnostic; Figure3_18 is consumed comparison, not a new validation cohort',
      model_limit='Original function takes empirical my_spe_adapt independently at every clamp; it contains no target-size input. This subset does not identify my_spe_adapt at any of Figure4 six new magnitudes.',
      fit=cal,source_rows=[dict(clamp=float(r[0]),jump=float(r[1]),A4=float(r[2]),observed_signed=float(r[3]),fitted_signed=float(p)) for r,p in zip(table,pred)],
      profile=profiles,
      figure3_stationary_calibrated_comparison=dict(stationary_amplitude=base,predicted_jump_to=predicted_jump,
            observed_jump_to=obs,predicted_ratio=predicted_jump/base,observed_ratio=obs/base,
            predicted_ratio_source_and_F3_stationary_bootstrap95=np.quantile(forecasts,[.025,.975]).tolist()),
      bootstrap_replicates=500,peak_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
      charged_read_decode_hash_bytes=4*((HERE/'ENDPOINT_CONTROL.json').stat().st_size+len(body)))
    (HERE/'PRESCRIPTION_CHECK.json').write_text(json.dumps(out,indent=2)+'\n')
    print(json.dumps({k:v for k,v in out.items() if k not in ('profile','source_rows')},indent=2))

if __name__=='__main__':
    with threadpool_limits(limits=1):main()
