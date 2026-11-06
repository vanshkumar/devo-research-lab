"""Independent numerical checks; authorized DEVELOPMENT outcomes only."""
from pathlib import Path
import sys,json,hashlib
import numpy as np
from scipy import optimize
R=Path(__file__).resolve().parents[2];sys.path.insert(0,str(R/'experiments'))
from analysis import load,jsonable
from state_models import cell_design,filtered,uncertainty,profile,curves
saved=json.loads((R/'outputs/state_models_development.json').read_text());model=saved['alternative']
for k in ['parameters']:model[k]=np.array(model[k])
for row in model['people']:
 for k in ['coef','nuisance']:row[k]=np.array(row[k])
ds=[cell_design(p) for p in load('development','Hand_raw')]
result={'exposure':'Development-only numerical audit; reserved and external outcomes not accessed.',
 'script_sha256':hashlib.sha256((R/'experiments/state_models.py').read_bytes()).hexdigest(),
 'derivative_steps':{},'fixed_slow_profiles':[]}
for step in [.00025,.0005,.001,.002]:
 u=uncertainty(ds,model,step=step)
 result['derivative_steps'][str(step)]={k:u[k] for k in ['theta','cluster_profile_se','cluster_profile_ci95','profile_hessian_eigenvalues','diagnostic_only']}
 print('step',step,'SE',u['cluster_profile_se'],flush=True)
# Explicit recurrence independent of cumprod/cumsum implementation.
rng=np.random.default_rng(812);u=rng.normal(size=(180,8));a=np.where(rng.uniform(size=180)<.23,1.15,.65)
h,initial=filtered(u,a);reference=np.zeros_like(h);initref=np.ones(180)
for r in range(1,180):reference[r]=a[r-1]*reference[r-1]+u[r-1];initref[r]=a[r-1]*initref[r-1]
assert np.max(np.abs(h-reference))<1e-12
result['filter_check']={'max_history_difference':float(np.max(np.abs(h-reference))),'max_initial_difference':float(np.max(np.abs(initial-initref)))}
pars=model['parameters'];SE=np.sqrt(np.diag(np.array(model['profile_uncertainty']['parameter_covariance'])))
result['boundary_distance_in_profile_SE']={'a_fast_to_upper':float((.85-pars[0])/SE[0]),'a_slow_to_upper':float((.995-pars[1])/SE[1]),'a_event_to_upper':float((1.35-pars[2])/SE[2])}
for slow in [.98,.985,.99,.995]:
 fun=lambda v:profile(ds,[v[0],slow,v[1]])[0].sum()
 opt=optimize.minimize(fun,[pars[0],pars[2]],method='L-BFGS-B',bounds=[(.1,.85),(.01,1.35)],options={'ftol':1e-10,'maxiter':80})
 q=[opt.x[0],slow,opt.x[1]];sse,rows=profile(ds,q,True)
 theta=float(curves(ds,{'parameters':q,'people':rows}).mean())
 result['fixed_slow_profiles'].append(dict(a_slow=slow,parameters=q,sse=float(sse.sum()),theta=theta,success=bool(opt.success)))
 print('fixed slow',slow,'theta',theta,flush=True)
(R/'audits/adversarial_review/state_numeric_audit.json').write_text(json.dumps(jsonable(result),indent=2)+'\n')
