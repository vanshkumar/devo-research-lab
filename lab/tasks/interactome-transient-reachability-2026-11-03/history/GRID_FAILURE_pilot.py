"""Execute only the immutable one-pulse declaration in PROTOCOL.md/CONFIG.json."""
import os
for key in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','VECLIB_MAXIMUM_THREADS','NUMEXPR_NUM_THREADS'):
    os.environ[key]='1'
import hashlib
import json
import resource
import time
import warnings
from datetime import datetime, timezone
from pathlib import Path

START=time.monotonic()
from reference import (np, integrate, linalg, N, ROOT, SOURCES,
    build_source, set_source_mask, efficient_system, scalar_rhs)
from scipy import optimize

CONFIG=json.loads((ROOT/'CONFIG.json').read_text())
FREEZE=json.loads((ROOT/'FREEZE.json').read_text())
for name,expected in FREEZE['sha256'].items():
    assert hashlib.sha256((ROOT/name).read_bytes()).hexdigest()==expected,'Frozen bytes changed'

def output_times(start,end):
    a,b=round(start/CONFIG['dt']),round(end/CONFIG['dt'])
    return np.arange(a,b+1)*CONFIG['dt']

def piece(env,y,start,end,method):
    times=output_times(start,end)
    if method=='literal':
        solver=integrate.ode(env['membrane_voltageRHS'],env['compute_jacobian']).set_integrator(
            'vode',atol=CONFIG['literal_reference_atol'],rtol=CONFIG['literal_reference_rtol'],
            min_step=1e-8,method='bdf',nsteps=10000)
        solver.set_initial_value(y,start)
        rows=[y.copy()]
        for t in times[1:]:
            rows.append(solver.integrate(float(t)).copy())
            assert solver.successful(),'Literal original VODE failed'
        return times,np.asarray(rows)
    rhs,jac=efficient_system(env)
    solved=integrate.solve_ivp(rhs,[start,end],y,method='BDF',jac=jac,t_eval=times,
        atol=CONFIG['primary_atol'],rtol=CONFIG['primary_rtol'])
    assert solved.success,solved.message
    assert np.isfinite(solved.y).all()
    return times,solved.y.T

def event_segment(env,y,start,end,old,new,method):
    set_source_mask(env,new,old=old,switch=start)
    # Source's .3s transition cutoff is an explicit solver segment boundary.
    times,rows=piece(env,y,start,start+.3,method)
    t2,y2=piece(env,rows[-1],start+.3,end,method)
    return np.r_[times,t2[1:]],np.vstack([rows,y2[1:]])

def baseline(env,seed,method='primary'):
    y0=1e-4*np.random.RandomState(seed).normal(0,.94,2*N)
    zero=np.zeros(N)
    return event_segment(env,y0,0.,20.,zero,zero,method)

def branch(env,y0,fwd,kind,method='primary'):
    zero=np.zeros(N)
    schedules={'finite':[fwd,zero,fwd], 'sham':[zero,zero,fwd], 'drive':[fwd,fwd,fwd]}
    old=zero
    times,rows=[],[]
    for start,end,new in zip([20.,22.,42.],[22.,42.,44.],schedules[kind]):
        t,y=event_segment(env,y0,start,end,old,new,method)
        if len(times):
            times.extend(t[1:]);rows.extend(y[1:])
        else:
            times.extend(t);rows.extend(y)
        y0=y[-1].copy()
        old=new
    return np.asarray(times),np.asarray(rows)

def window(t,a,b):
    return (t>=a-1e-9)&(t<=b+1e-9)

def rms(a):
    return float(np.sqrt(np.mean(np.square(a))))

def source_mask(t,kind,fwd):
    zero=np.zeros(N)
    if kind=='finite':
        events=[(20.,fwd),(22.,zero),(42.,fwd)]
    elif kind=='sham':
        events=[(20.,zero),(22.,zero),(42.,fwd)]
    else:
        events=[(20.,fwd),(22.,fwd),(42.,fwd)]
    old=zero
    for i,(switch,new) in enumerate(events):
        end=events[i+1][0] if i+1<len(events) else np.inf
        if switch<=t<end or i==len(events)-1:
            if t<=switch+.3:
                w=.5+.5*np.tanh((t-switch-.15)/.025)
                return old*(1-w)+new*w
            return new
        old=new
    return zero

def summarize_seed(env,names,seed,fwd):
    data={}
    for kind in ['finite','sham','drive']:
        with np.load(ROOT/f'seed{seed}_{kind}.npz',allow_pickle=False) as saved:
            data[kind]=saved['y']
            t=saved['t']
    motor=np.array([i for i,n in enumerate(names) if n.startswith(('DB','VB','DD','VD'))])
    scale=CONFIG['reference_motor_rms']
    late=window(t,*CONFIG['late_window'])
    challenge=window(t,*CONFIG['challenge_window'])
    delta=data['finite']-data['sham']
    raw_motor_delta=delta[:,:N][:,motor]
    retained=rms(raw_motor_delta[late])
    predicted=rms(raw_motor_delta[challenge])
    previous=rms(raw_motor_delta[window(t,40.,41.)])
    last=rms(raw_motor_delta[window(t,41.,42.)])
    maintained=rms((data['drive']-data['sham'])[late,:N][:,motor])
    index=lambda time_:int(round((time_-20)/CONFIG['dt']))
    set_source_mask(env,np.zeros(N),switch=22.)
    rhs,_=efficient_system(env)
    origin=index(CONFIG['linear_origin'])
    j=env['compute_jacobian'](23.,data['sham'][origin])
    max_eig=float(np.max(np.real(linalg.eigvals(j))))
    linear=[]
    for absolute_time in CONFIG['linear_times']:
        pred=linalg.expm(j*(absolute_time-23.)).dot(delta[origin])
        observed=delta[index(absolute_time)]
        linear.append(dict(t=absolute_time,motor_predicted_rms=rms(pred[:N][motor]),
            motor_observed_rms=rms(observed[:N][motor]),
            relative_motor_vector_error=(rms((pred-observed)[:N][motor])/max(rms(observed[:N][motor]),1e-300)),
            absolute_motor_vector_error=rms((pred-observed)[:N][motor])))
    endpoints={}
    for kind in ['finite','sham']:
        y=data[kind][index(42.)]
        derivative=rhs(42.,y)
        endpoints[kind]=dict(motor_last2s_temporal_sd_rms=rms(np.std(data[kind][late,:N][:,motor],axis=0)),
            all_voltage_max_abs_derivative=float(np.max(np.abs(derivative[:N]))),
            all_gate_max_abs_derivative=float(np.max(np.abs(derivative[N:]))),
            terminal_motor_mean=float(np.mean(y[:N][motor])),
            terminal_gate_min=float(y[N:].min()),terminal_gate_max=float(y[N:].max()))
    conditions=dict(material_retained=retained>=.1*scale,material_future_response=predicted>=.1*scale,
        late_not_strongly_decaying=last>=.8*previous,
        continuing_drive_positive=maintained>=.1*scale)
    root_info={'attempted':False,'reason':'Prespecified prerequisite retention/readout gates did not both pass'}
    if conditions['material_retained'] and conditions['material_future_response']:
        roots={}
        root_arrays={}
        for kind in ['finite','sham']:
            y=data[kind][index(42.)]
            root=optimize.root(lambda state:rhs(42.,state),y,
                jac=lambda state:env['compute_jacobian'](42.,state),method='hybr',
                options={'xtol':1e-9,'maxfev':2000})
            root_arrays[kind]=root.x
            roots[kind]=dict(success=bool(root.success),residual=float(np.max(np.abs(root.fun))),
                max_real_eigenvalue=float(np.max(np.real(linalg.eigvals(env['compute_jacobian'](42.,root.x))))),
                reached_motor_distance=rms((root.x-y)[:N][motor]))
        root_info=dict(attempted=True,roots=roots,
            motor_root_separation=rms((root_arrays['finite']-root_arrays['sham'])[:N][motor]))
        np.savez_compressed(ROOT/f'seed{seed}_root_check.npz',**root_arrays)
    # Independent literal source/scalar/efficient expressions on noninitial states.
    expression_checks=[]
    for tm in [23.,41.,44.]:
        mask=source_mask(tm,'finite',fwd)
        set_source_mask(env,mask,switch=tm-1.)
        y=data['finite'][index(tm)]
        scalar=scalar_rhs(env,tm,y)
        source=env['membrane_voltageRHS'](tm,y)
        fast=efficient_system(env)[0](tm,y)
        error=float(np.max(np.abs(scalar-source)))
        fast_error=float(np.max(np.abs(fast-source)))
        assert np.allclose(scalar,source,rtol=1e-10,atol=1e-7)
        assert np.allclose(fast,source,rtol=1e-10,atol=1e-7)
        expression_checks.append(dict(t=tm,scalar_max_absolute_error=error,
            independent_sparse_max_absolute_error=fast_error))
    # Renderer uses the shared source thresholds and contains no hidden filter.
    rendered={}
    for label,selector in [('late',late),('challenge',challenge)]:
        for kind in ['finite','sham']:
            ys=data[kind][selector,:N]
            ts=t[selector]
            threshold=np.array([env['EffVth_rhs'](env['Iext'],source_mask(float(tm),kind,fwd)) for tm in ts])
            rendered[kind]=500*np.tanh((ys-threshold)/500)
        if label=='late':rendered_late=rms((rendered['finite']-rendered['sham'])[:,motor])
        else:rendered_probe=rms((rendered['finite']-rendered['sham'])[:,motor])
    np.savez_compressed(ROOT/f'seed{seed}_primary_differences.npz',t=t,
        motor_indices=motor,motor_voltage_delta=raw_motor_delta,
        full_terminal_state_delta=delta[index(42.)])
    return dict(seed=seed,independent_unit='SAME fixed connectome; numerical initialization only',
        motor_names=[names[i] for i in motor],normalization=scale,
        retained_motor_rms=retained,retained_fraction=retained/scale,
        late_previous_second_rms=previous,late_last_second_rms=last,
        late_last_to_previous_ratio=(last/max(previous,1e-300)),
        challenge_motor_rms=predicted,challenge_fraction=predicted/scale,
        maintained_drive_motor_rms=maintained,maintained_drive_fraction=maintained/scale,
        rendered_late_motor_rms=rendered_late,rendered_challenge_motor_rms=rendered_probe,
        complete_terminal_voltage_delta_rms=rms(delta[index(42.),:N]),
        complete_terminal_gate_delta_rms=rms(delta[index(42.),N:]),
        conditions=conditions,preliminary_material_gate=all(conditions.values()),
        baseline_linearization_max_real_eigenvalue=max_eig,linear_relaxation=linear,
        endpoints=endpoints,root_check=root_info,expression_checks=expression_checks)

def main():
    assert not (ROOT/'PILOT_STARTED.json').exists(),'Consumed pilot: never overwrite or rerun automatically'
    (ROOT/'PILOT_STARTED.json').write_text(json.dumps(dict(
        started_at_utc=datetime.now(timezone.utc).isoformat(),freeze=FREEZE,
        fixed_config=CONFIG),indent=2)+'\n')
    with warnings.catch_warnings(record=True) as warning_records:
        warnings.simplefilter('default')
        names,manifest,env,constants=build_source()
        preset=json.loads((SOURCES/'FWD.json').read_text())
        fwd=np.array([preset[name]['inputCurrent'] for name in names])
        motor=np.array([i for i,n in enumerate(names) if n.startswith(('DB','VB','DD','VD'))])
        baseline_states={}
        for seed in CONFIG['seeds']:
            t,y=baseline(env,seed)
            np.savez_compressed(ROOT/f'seed{seed}_baseline.npz',t=t,y=y)
            baseline_states[seed]=y[-1].copy()
            for kind in ['finite','sham','drive']:
                tb,yb=branch(env,baseline_states[seed],fwd,kind)
                np.savez_compressed(ROOT/f'seed{seed}_{kind}.npz',t=tb,y=yb)
                print('PILOT_RAW_SAVED',seed,kind,len(tb),flush=True)
        results=[summarize_seed(env,names,seed,fwd) for seed in CONFIG['seeds']]
        # Predetermined independent original-source tighter integration, seed0 only.
        t,y=baseline(env,0,method='literal')
        np.savez_compressed(ROOT/'seed0_literal_baseline.npz',t=t,y=y)
        literal_y0=y[-1].copy()
        with np.load(ROOT/'seed0_baseline.npz',allow_pickle=False) as saved:
            baseline_error=float(np.max(np.abs(y-saved['y'])))
        numerical={}
        for kind in ['finite','sham']:
            tb,yb=branch(env,literal_y0,fwd,kind,method='literal')
            np.savez_compressed(ROOT/f'seed0_literal_{kind}.npz',t=tb,y=yb)
            with np.load(ROOT/f'seed0_{kind}.npz',allow_pickle=False) as saved:
                discrepancy=yb-saved['y']
            numerical[kind]=dict(max_absolute_all_state_error=float(np.max(np.abs(discrepancy))),
                max_absolute_motor_voltage_error=float(np.max(np.abs(discrepancy[:,:N][:,motor]))),
                late_motor_rms_error=rms(discrepancy[window(tb,40.,42.),:N][:,motor]),
                challenge_motor_rms_error=rms(discrepancy[window(tb,42.3,44.),:N][:,motor]))
            print('TIGHT_LITERAL_REFERENCE_SAVED',kind,numerical[kind],flush=True)
        with np.load(ROOT/'seed0_literal_finite.npz',allow_pickle=False) as a,np.load(ROOT/'seed0_literal_sham.npz',allow_pickle=False) as b:
            literal_delta=(a['y']-b['y'])[:,:N][:,motor]
            literal_metrics=dict(retained_motor_rms=rms(literal_delta[window(tb,40.,42.)]),
                challenge_motor_rms=rms(literal_delta[window(tb,42.3,44.)]))
        # Check threshold LU semantics against an independently assembled dense solve.
        gg=env['Gg_Dynamic'];gs=env['Gs_Dynamic'];s_eq=constants['threshold_gate_rounded']
        gap_off=gg-np.diag(np.diag(gg))
        syn_off=gs-np.diag(np.diag(gs))
        matrix=-env['Gc']*np.eye(N)-np.diag(gap_off.sum(axis=1))+gap_off-np.diag(s_eq*syn_off.sum(axis=1))
        bb=-env['Gc']*env['Ec']*np.ones(N)-gs.dot(s_eq*env['E'].reshape(N))
        threshold_check={}
        for label,mask in [('zero',np.zeros(N)),('FWD',fwd)]:
            direct=linalg.solve(matrix,bb-env['Iext']*mask)
            source=env['EffVth_rhs'](env['Iext'],mask)
            error=float(np.max(np.abs(direct-source)))
            threshold_check[label]=dict(max_absolute_difference=error,source_linear_residual=float(np.max(np.abs(matrix.dot(source)-(bb-env['Iext']*mask)))))
            assert error<1e-6
        report=dict(status='ONE_FROZEN_PILOT_COMPLETED',utc=datetime.now(timezone.utc).isoformat(),
            frozen_at=FREEZE['frozen_at_utc'],results=results,
            seed0_literal_numerical_reference=numerical,
            seed0_literal_primary_metrics=literal_metrics,
            baseline_literal_max_error=baseline_error,
            seed0_to_seed1_baseline_all_state_max_difference=float(np.max(np.abs(baseline_states[0]-baseline_states[1]))),
            independent_threshold_reference=threshold_check,
            elapsed_s=time.monotonic()-START,max_rss_bytes_macos=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
            warnings=[dict(message=str(w.message),category=w.category.__name__,file=w.filename,line=w.lineno) for w in warning_records],
            scientific_protocol_revisions=0,
            recommendation=('CLOSE_FIXED_ONE_CYCLE_PULSE_RECIPE' if not all(r['preliminary_material_gate'] for r in results) else 'MATERIAL_GATE_PASSED_REQUIRES_FULL_ALTERNATIVE_ASSESSMENT'),
            independent_units=1,no_empirical_or_protected_inputs=True)
    (ROOT/'PILOT_RESULT.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2),flush=True)

if __name__=='__main__':
    main()
