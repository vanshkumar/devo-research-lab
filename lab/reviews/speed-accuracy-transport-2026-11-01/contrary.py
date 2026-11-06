"""The single predeclared source-only affine nondecision-map relaxation."""
from reconstruct import *
from scipy.optimize import minimize, LinearConstraint
import time

def main():
    started=time.monotonic()
    plan=(HERE/'CONTRARY_PLAN.md').read_bytes()
    source=read('SOURCE_FIT.json')
    ps=np.array(source['source_baseline_parameters'])
    d=original()
    targets=[selected(d,p,2) for p in range(1,10)]
    tmin=float(ps[:,2].min())
    deviations=ps[:,2]-tmin
    allowances=np.array([rows['rt'].min()-.005-.03 for rows in targets])

    def transform(p,x):
        a,z,t0,_=physical(p)
        lower=a*z*np.exp(x[0]);upper=a*(1-z)*np.exp(x[1])
        q=np.array(p,float)
        q[0]=np.log(lower+upper);q[1]=np.log(lower/upper)
        q[2]=.03+max(0.,x[3]+x[2]*(t0-tmin))
        return q

    def objective(x,n=192):
        return sum(likelihood(transform(p,x),rows,n) for p,rows in zip(ps,targets))

    pm=np.array(source['P_mapping'])
    original_gain=np.exp(pm[2])
    starts=[np.array([pm[0],pm[1],original_gain,original_gain*(tmin-.03)]),
            np.array([np.log(1.3),np.log(1.3),0.,.5*allowances.min()])]
    # LinearConstraint enforces physical source target delays. Held targets are
    # unavailable to this fitting routine; the held-only branch follows saving.
    matrix=np.c_[np.zeros((9,2)),deviations,np.ones(9)]
    physical_sources=LinearConstraint(matrix,np.full(9,-np.inf),allowances)
    bounds=[(np.log(.5),np.log(3.)),(np.log(.5),np.log(3.)),(0.,2.),(0.,.7)]
    fits=[]
    for k,start in enumerate(starts):
        fit=minimize(objective,start,method='SLSQP',bounds=bounds,constraints=[physical_sources],
                     options={'maxiter':250,'ftol':1e-8})
        feasible=bool((allowances-matrix@fit.x>=-1e-8).all())
        entry={'start':k,'initial':start,'initial_objective':objective(start),
               'parameters':fit.x,'objective':float(fit.fun),'success':bool(fit.success),
               'message':str(fit.message),'iterations':int(fit.nit),
               'evaluations':int(fit.nfev),'feasible':feasible,
               'source_constraint_margins_s':allowances-matrix@fit.x}
        fits.append(entry)
        print(json.dumps(entry,default=lambda v:np.asarray(v).tolist()),flush=True)
    valid=[fit for fit in fits if fit['feasible'] and np.isfinite(fit['objective'])]
    if not valid:
        save('CONTRARY.json',{'at_utc':stamp(),'status':'STOP_no_feasible_optimizer_result','starts':fits})
        return
    chosen=min(valid,key=lambda r:r['objective'])
    fit_stage={'at_utc':stamp(),'postvalidation':True,'plan_sha256':hashlib.sha256(plan).hexdigest(),
               'source_people':list(range(1,10)),'minimum_source_baseline_t0_s':tmin,
               'source_upper_allowances_above_floor_s':allowances,
               'source_baseline_parameters_held_fixed':True,'starts':fits,'selected_start':chosen['start'],
               'selected_parameters':chosen['parameters'],
               'original_map_objective192':objective(starts[0]),
               'changed_map_objective192':chosen['objective'],
               'target_outcomes_used_in_fitting':False}
    # Checkpoint fitted source-only prescription before any held-target summary.
    save('CONTRARY_SOURCE_FIT.json',fit_stage)
    print('Source-only fit checkpoint saved before held scoring',flush=True)

    held=read('PREDICTIONS.json')
    held_ps=np.array(held['baseline_parameters'])
    changed_parameters=np.array([transform(p,chosen['parameters']) for p in held_ps])
    changed=np.array([moments(p,256)[1] for p in changed_parameters])
    refined=np.array([moments(p,384)[1] for p in changed_parameters])
    baseline_p=np.array([moments(original_map(p,source['P_mapping']),256)[1] for p in held_ps])
    obs=np.array([summarize(selected(d,p,2))[0] for p in range(10,18)])
    ref=source['empirical']['reference']
    original_reference=np.array(held['predictions'][ref])
    result=scores({'P':changed,'REFERENCE':original_reference},obs,'REFERENCE')
    original_result=scores({'P':baseline_p,'REFERENCE':original_reference},obs,'REFERENCE')
    per_person=[]
    for i,p in enumerate(held_ps):
        per_person.append({'id':i+10,'baseline_t0_s':p[2],
            'original_target_t0_s':original_map(p,source['P_mapping'])[2],
            'affine_target_t0_s':changed_parameters[i,2],
            'floor_clamp_active':bool(chosen['parameters'][3]+chosen['parameters'][2]*(p[2]-tmin)<0),
            'original_forecast':baseline_p[i], 'affine_forecast':changed[i], 'target_summary':obs[i]})
    x=chosen['parameters']
    source_refined=sum(likelihood(transform(p,x),rows,384) for p,rows in zip(ps,targets))
    source_at256=sum(likelihood(transform(p,x),rows,256) for p,rows in zip(ps,targets))
    out={'at_utc':stamp(),'postvalidation':True,'status':'completed' if chosen['success'] else 'partial_nonconverged',
         'plan_sha256':fit_stage['plan_sha256'],'choice':'ONE source-only affine nondecision map with fixed saved baseline fits; no other alternatives',
         'fit':fit_stage,'source_refined_objective256':source_at256,'source_refined_objective384':source_refined,
         'source_objective_improvement192':fit_stage['original_map_objective192']-chosen['objective'],
         'original_reference':ref,'original':original_result,'affine':result,
         'forecast_quadrature_256_384_max_difference':error(changed,refined),
         'factors':{'lower_distance':np.exp(x[0]),'upper_distance':np.exp(x[1]),'t0_gain':x[2],'t0_intercept_above_minimum_source_floor_s':x[3]},
         'held_per_person':per_person,
         'elapsed_seconds':time.monotonic()-started,
         'largest_measured_process_rss_bytes_macos':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
         'read_decode_hash_charge_bytes':70000000,
         'limitation':'Single changed source prescription scored on consumed evaluation people. No repair of original failure or new validation; no biological decomposition, full baseline/source optimizer refitting uncertainty, power or coverage.'}
    assert out['largest_measured_process_rss_bytes_macos']<800000000
    assert out['forecast_quadrature_256_384_max_difference']<1e-7
    save('CONTRARY.json',out)
    print(json.dumps({'at':out['at_utc'],'status':out['status'], 'source_likelihood_improvement':out['source_objective_improvement192'],
          'parameters':out['factors'],'affine_P':{k:v for k,v in result['models']['P'].items() if k!='per_person_losses'},
          'passes':result['primary_P_rule_passes'],'rss':out['largest_measured_process_rss_bytes_macos'],
          'seconds':out['elapsed_seconds']},default=lambda v:np.asarray(v).tolist()),flush=True)

if __name__=='__main__': main()
