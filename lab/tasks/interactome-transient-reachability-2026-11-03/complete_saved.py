"""Collect immutable primary trajectories; finish the originally planned numeric check.

No primary branch is rerun. The literal VODE reference respects one-sided
segment limits at the source's known .3s clipping discontinuities. This changes
only numerical extension outside an integration segment, not the ODE on its
open interval, source parameters, frozen inputs, readouts or decision rule.
"""
import os
for key in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','VECLIB_MAXIMUM_THREADS','NUMEXPR_NUM_THREADS'):
    os.environ[key]='1'
import hashlib
import json
import resource
import shutil
import time
import warnings
from datetime import datetime,timezone

T0=time.monotonic()
import pilot as p
np=p.np
root=p.ROOT

def literal_piece(env,y,start,end,method):
    assert method=='literal'
    times=p.output_times(start,end)
    def bounded_time(t):
        # End of a smooth transition: internal solver stages must not see the
        # later clipped law while integrating the preceding open interval.
        if abs(end-env['transit_End'])<1e-10:
            t=min(t,end)
        # Interval immediately after clipping: use the right-hand limit at its
        # first derivative evaluation; state/output remains exactly continuous.
        if abs(start-env['transit_End'])<1e-10 and t<=start:
            t=np.nextafter(start,np.inf)
        return t
    rhs=lambda t,y:env['membrane_voltageRHS'](bounded_time(t),y)
    jac=lambda t,y:env['compute_jacobian'](bounded_time(t),y)
    solver=p.integrate.ode(rhs,jac).set_integrator('vode',
        atol=p.CONFIG['literal_reference_atol'],rtol=p.CONFIG['literal_reference_rtol'],
        min_step=1e-8,max_step=.01,method='bdf',nsteps=10000)
    solver.set_initial_value(y,start)
    rows=[y.copy()]
    for t in times[1:]:
        rows.append(solver.integrate(float(t)).copy())
        assert solver.successful(),'One-sided literal VODE still failed; do not hunt settings'
    return times,np.asarray(rows)

def main():
    assert not (root/'PILOT_RESULT.json').exists()
    assert (root/'GRID_FIX_CONTINUATION.json').exists()
    history=root/'history'
    dst=history/'CLIPPING_FAILURE_pilot.py'
    assert not dst.exists()
    shutil.copyfile(root/'pilot.py',dst)
    (history/'CLIPPING_FAILURE.json').write_text(json.dumps(dict(
        utc=datetime.now(timezone.utc).isoformat(),native_session=8087,native_exit_code=1,
        native_chunk='8b583d',
        failure='VODE error test at22.29999999258/minimum step1e-8, near source clipping at22.3',
        all_six_primary_branches_saved=True,primary_trajectories_will_not_be_rerun=True,
        code_sha256=hashlib.sha256(dst.read_bytes()).hexdigest(),
        numerical_driver_correction='one-sided segment extension, maxstep10ms, identical declared tolerances/source RHS',
        frozen_scientific_choices_changed=False),indent=2)+'\n')
    with warnings.catch_warnings(record=True) as wr:
        warnings.simplefilter('default')
        names,manifest,env,constants=p.build_source()
        preset=json.loads((p.SOURCES/'FWD.json').read_text())
        fwd=np.array([preset[n]['inputCurrent'] for n in names])
        results=[p.summarize_seed(env,names,seed,fwd) for seed in p.CONFIG['seeds']]
        # Preserve earned scores BEFORE the independent reference can fail.
        (root/'PRIMARY_RESULT.json').write_text(json.dumps(dict(
            utc=datetime.now(timezone.utc).isoformat(),results=results,
            numerical_validation='pending planned original-source tighter VODE reference'),indent=2)+'\n')
        print('PRIMARY_RESULTS_SAVED',[(r['seed'],r['retained_fraction'],r['challenge_fraction']) for r in results],flush=True)
        # Use already saved tighter literal baseline from the interrupted run.
        with np.load(root/'seed0_literal_baseline.npz',allow_pickle=False) as saved:
            literal_y0=saved['y'][-1].copy()
            literal_baseline=saved['y']
        with np.load(root/'seed0_baseline.npz',allow_pickle=False) as saved:
            baseline_error=float(np.max(np.abs(literal_baseline-saved['y'])))
            baseline0=saved['y'][-1].copy()
        with np.load(root/'seed1_baseline.npz',allow_pickle=False) as saved:
            baseline1=saved['y'][-1].copy()
        p.piece=literal_piece
        motor=np.array([i for i,n in enumerate(names) if n.startswith(('DB','VB','DD','VD'))])
        numerical={}
        for kind in ['finite','sham']:
            tb,yb=p.branch(env,literal_y0,fwd,kind,method='literal')
            np.savez_compressed(root/f'seed0_literal_{kind}.npz',t=tb,y=yb)
            with np.load(root/f'seed0_{kind}.npz',allow_pickle=False) as saved:
                error=yb-saved['y']
            numerical[kind]=dict(max_absolute_all_state_error=float(np.max(np.abs(error))),
                max_absolute_motor_voltage_error=float(np.max(np.abs(error[:,:p.N][:,motor]))),
                late_motor_rms_error=p.rms(error[p.window(tb,40.,42.),:p.N][:,motor]),
                challenge_motor_rms_error=p.rms(error[p.window(tb,42.3,44.),:p.N][:,motor]))
            print('TIGHT_LITERAL_REFERENCE_SAVED',kind,numerical[kind],flush=True)
        with np.load(root/'seed0_literal_finite.npz',allow_pickle=False) as a,np.load(root/'seed0_literal_sham.npz',allow_pickle=False) as b:
            delta=(a['y']-b['y'])[:,:p.N][:,motor]
            literal_metrics=dict(retained_motor_rms=p.rms(delta[p.window(tb,40.,42.)]),
                challenge_motor_rms=p.rms(delta[p.window(tb,42.3,44.)]))
        gg,gs=env['Gg_Dynamic'],env['Gs_Dynamic'];s_eq=constants['threshold_gate_rounded']
        gap_off=gg-np.diag(np.diag(gg));syn_off=gs-np.diag(np.diag(gs))
        matrix=-env['Gc']*np.eye(p.N)-np.diag(gap_off.sum(axis=1))+gap_off-np.diag(s_eq*syn_off.sum(axis=1))
        bb=-env['Gc']*env['Ec']*np.ones(p.N)-gs.dot(s_eq*env['E'].reshape(p.N))
        threshold_check={}
        for label,mask in [('zero',np.zeros(p.N)),('FWD',fwd)]:
            direct=p.linalg.solve(matrix,bb-env['Iext']*mask)
            source=env['EffVth_rhs'](env['Iext'],mask)
            err=float(np.max(np.abs(direct-source)))
            threshold_check[label]=dict(max_absolute_difference=err,
                source_linear_residual=float(np.max(np.abs(matrix.dot(source)-(bb-env['Iext']*mask)))))
            assert err<1e-6
        numeric_ok=all(r['max_absolute_motor_voltage_error']<.01*p.CONFIG['reference_motor_rms'] for r in numerical.values())
        report=dict(status='ONE_FROZEN_PILOT_COMPLETED',utc=datetime.now(timezone.utc).isoformat(),
            frozen_at=p.FREEZE['frozen_at_utc'],results=results,
            seed0_literal_numerical_reference=numerical,seed0_literal_primary_metrics=literal_metrics,
            baseline_literal_max_error=baseline_error,
            seed0_to_seed1_baseline_all_state_max_difference=float(np.max(np.abs(baseline0-baseline1))),
            independent_threshold_reference=threshold_check,
            numerical_control_passed=numeric_ok,
            current_collection_and_reference_elapsed_s=time.monotonic()-T0,
            current_collection_and_reference_max_rss_bytes_macos=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
            interrupted_process_times_and_peaks='not fully measured; preserve conservative containing bookings',
            warnings=[dict(message=str(w.message),category=w.category.__name__,file=w.filename,line=w.lineno) for w in wr],
            scientific_protocol_revisions=0,
            implementation_amendments=['output-grid binary endpoint equality','one-sided literal numerical reference at source clipping'],
            recommendation=('CLOSE_FIXED_ONE_CYCLE_PULSE_RECIPE' if not numeric_ok or not all(r['preliminary_material_gate'] for r in results) else 'MATERIAL_GATE_PASSED_REQUIRES_FULL_ALTERNATIVE_ASSESSMENT'),
            independent_units=1,no_empirical_or_protected_inputs=True)
    (root/'PILOT_RESULT.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2),flush=True)

if __name__=='__main__':
    main()
