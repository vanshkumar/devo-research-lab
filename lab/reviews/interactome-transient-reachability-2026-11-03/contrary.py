"""Execute ONE frozen maintained-background contrary; no condition search."""
from independent_model import *
import datetime
import time
import resource
from scipy.optimize import minimize_scalar, root
start=time.monotonic()
frozen=json.loads((OUT/'CONTRARY_FREEZE.json').read_text())
for name,h in frozen['sha256'].items(): assert sha(OUT/name)==h,(name,'freeze changed')
m=Model()
background=m.presets['PLM'].copy()
for name in ('ASKL','ASKR'): background[m.names.index(name)]=.24
fwd=m.presets['FWD']
normalization=5.638259640019669; cut=.1*normalization
def maskidx(t,a,b):return (t>=a-1e-10)&(t<=b+1e-10)
def metrics(t,ys):
    f,s,d=(ys[k] for k in ('finite','sham','drive'))
    delta=f-s; late=maskidx(t,40,42);challenge=maskidx(t,42.3,44)
    r={'late_motor_rms':rms(delta[late][:,m.motor]),
       'challenge_motor_rms':rms(delta[challenge][:,m.motor]),
       'drive_vs_sham_late_motor_rms':rms((d-s)[late][:,m.motor]),
       'late_full_voltage_rms':rms(delta[late,:N]),'late_full_gate_rms':rms(delta[late,N:]),
       'preceding_second_motor_rms':rms(delta[maskidx(t,40,41)][:,m.motor]),
       'last_second_motor_rms':rms(delta[maskidx(t,41,42)][:,m.motor])}
    r['last_over_preceding_second']=r['last_second_motor_rms']/r['preceding_second_motor_rms'] if r['preceding_second_motor_rms'] else None
    r['material_candidate']=r['late_motor_rms']>=cut and r['challenge_motor_rms']>=cut
    r['late_states']={}
    for label,y in ys.items():
        at42=y[np.argmin(abs(t-42))]
        common=background if label!='drive' else fwd
        rhs=m.rhs(42,at42,common)
        eig=linalg.eigvals(m.jac(42,at42,common))
        st={'motor_temporal_rms':rms(y[late][:,m.motor]-y[late][:,m.motor].mean(0)),
            'voltage_derivative_maxabs':float(np.max(abs(rhs[:N]))),
            'gate_derivative_maxabs':float(np.max(abs(rhs[N:]))),
            'local_largest_eigenvalue_real':float(np.max(eig.real))}
        st['nearsteady']=(st['motor_temporal_rms']<=.01*normalization and
                          st['voltage_derivative_maxabs']<=.01*normalization and
                          st['gate_derivative_maxabs']<=1e-4)
        r['late_states'][label]=st
    if r['late_motor_rms']>=cut:
        qt=t[late]; target=f[late][:,m.motor]
        def align(tau,allstates=False):
            cols=np.arange(2*N) if allstates else m.motor
            return np.column_stack([np.interp(qt+tau,t,s[:,i]) for i in cols])
        def loss(tau):return rms(target-align(tau))
        shifts=np.linspace(-10,0,1001); losses=np.array([loss(tau) for tau in shifts])
        ix=int(np.argmin(losses)); lo=shifts[max(0,ix-1)]; hi=shifts[min(1000,ix+1)]
        opt=minimize_scalar(loss,bounds=(lo,hi),method='bounded',options={'xatol':1e-10})
        tau=float(opt.x) if opt.fun<losses[ix] else float(shifts[ix])
        resid=loss(tau); aligned=align(tau,True); full=f[late]-aligned
        r['single_time_shift']={'lag_s':tau,'motor_rms_residual':resid,
            'fraction_raw_separation_removed':1-resid/r['late_motor_rms'],
            'full_voltage_rms_residual':rms(full[:,:N]),'full_gate_rms_residual':rms(full[:,N:]),
            'sufficient_at_declared_resolution':bool(resid<.01*normalization and resid<.1*r['late_motor_rms'])}
    if r['late_motor_rms']>=cut and all(r['late_states'][k]['nearsteady'] for k in ('finite','sham')):
        roots={}
        for label in ('finite','sham'):
            x=ys[label][np.argmin(abs(t-42))]
            sol=root(lambda z:m.rhs(42,z,background),x,jac=lambda z:m.jac(42,z,background),method='hybr')
            ev=linalg.eigvals(m.jac(42,sol.x,background))
            roots[label]={'success':bool(sol.success),'message':str(sol.message),
                'rhs_maxabs':float(np.max(abs(sol.fun))),'max_eigenvalue_real':float(np.max(ev.real))}
            np.savez_compressed(OUT/('contrary_root_'+label+'.npz'),x=sol.x)
        r['one_root_per_actual_state']=roots
    return r

results={};rules={'finite':[(20.,fwd),(22.,background),(42.,fwd)],
                 'sham':[(42.,fwd)],'drive':[(20.,fwd)]}
for seed in (0,1):
    init=1e-4*np.random.RandomState(seed).normal(0,.94,2*N)
    tb,b=m.schedule(init,0,20,m.zero,[(0.,background)])
    np.savez_compressed(OUT/f'contrary_seed{seed}_baseline.npz',t=tb,y=b)
    ys={}
    for label,switches in rules.items():
        t,y=m.schedule(b[-1],20,44,background,switches)
        ys[label]=y
        np.savez_compressed(OUT/f'contrary_seed{seed}_{label}.npz',t=t,y=y)
    results[str(seed)]=metrics(t,ys)
    if seed==0: baseline0=b.copy();primary0={k:ys[k].copy() for k in ('finite','sham')}
    del ys

# Predeclared different-integrator replay, no experimental choices altered.
tb,b=m.schedule(1e-4*np.random.RandomState(0).normal(0,.94,2*N),0,20,m.zero,[(0.,background)],rtol=5e-11,atol=5e-12,method='BDF')
checks={'baseline_full_maxabs':float(np.max(abs(b-baseline0)))}
for label in ('finite','sham'):
    t,y=m.schedule(b[-1],20,44,background,rules[label],rtol=5e-11,atol=5e-12,method='BDF')
    checks[label]={'motor_maxabs':float(np.max(abs(y[:,m.motor]-primary0[label][:,m.motor]))),
                   'full_maxabs':float(np.max(abs(y-primary0[label])))}
    # Static new-trajectory source expression comparisons, including transition.
    errors=[]
    for tm in (20.15,21.,22.15,23.,41.,42.15,43.):
        ix=int(np.argmin(abs(t-tm)));z=y[ix]
        if tm<22:old,new,when=background,fwd,20.
        elif tm<42:old,new,when=fwd,background,22.
        else:old,new,when=background,fwd,42.
        m.source_setup(old,new,when)
        actual=m.input(tm,old,new,when)
        errors.append(float(np.max(abs(m.rhs(tm,z,actual)-m.source['membrane_voltageRHS'](tm,z)))))
    checks[label]['literal_source_rhs_maxabs']=max(errors)
    np.savez_compressed(OUT/f'contrary_BDF0_{label}.npz',t=t,y=y)

report={'status':'ONE_FROZEN_MAINTAINED_BACKGROUND_CONTRARY_COMPLETE',
    'finished_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
    'background_nonzero_masks':{n:float(background[i]) for i,n in enumerate(m.names) if background[i]},
    'changed_model_parameters':False,'new_postvalidation_experiment':True,
    'background_bistability_in_2019_assumed':False,'material_scale_rms':normalization,
    'material_cutoff_rms':cut,'seeds':results,'numerical_BDF_Radau':checks,
    'both_initializations_material_candidate':all(x['material_candidate'] for x in results.values()),
    'input_threshold_restoration':'bitwise identical common background mask after22.3; same linear threshold law; identical challenge',
    'process_elapsed_s':time.monotonic()-start,'rss_bytes_macos':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
    'independent_units':'one deterministic connectome, two initialization controls',
    'new_conditions_searched':0,'scientific_protocol_revisions':0,
    'all_new_trajectories':'consumed development forever; no empirical/protected data',
    'asymptotic_behavior_biological_memory_priority':'UNESTABLISHED'}
write('CONTRARY.json',report)
print(json.dumps(report,indent=2))
