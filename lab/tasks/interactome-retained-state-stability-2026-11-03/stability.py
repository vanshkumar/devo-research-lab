"""ONE frozen full-model stability/continuation experiment; no setting search."""
from reference import *
import signal
from scipy import sparse, linalg
from scipy.integrate import solve_ivp
from scipy.optimize import root
from scipy.sparse.linalg import splu

SCALE = 5.638259640019669
CUTOFF = .1*SCALE
D = np.r_[np.full(N,SCALE),np.full(N,.1)]
PROCESS_START = time.monotonic()
REPORT = {'status':'RUNNING','runs':[],'scientific_protocol_revisions':0}

def timed_out(signum, frame):
    raise TimeoutError('1080s single-run process boundary; no automatic extension')

def jacobian(m,y,b):
    """Independent sparse block assembly from exact source coefficients."""
    v,s = y[:N],y[N:]
    q = prior.expit(prior.BETA*(v-m.threshold(b)))
    a = m.gap/prior.CAP-sparse.diags((prior.GC+m.gsum+m.syn.dot(s))/prior.CAP)
    g = m.syn.tocoo()
    coupling = sparse.csr_matrix((g.data*(m.e[g.col]-v[g.row])/prior.CAP,(g.row,g.col)),shape=(N,N))
    c = sparse.diags(prior.RISE*prior.BETA*(1-s)*q*(1-q))
    d = sparse.diags(-prior.DECAY-prior.RISE*q)
    return sparse.bmat([[a,coupling],[c,d]],format='csc')

def solve_constant(m,y,start,end,b,dense=False,events=None,method='Radau',
                   rtol=2e-10,atol=2e-11,maxstep=.05,t_eval=None):
    sol = solve_ivp(lambda t,z:m.rhs(t,z,b),(start,end),y,
                    jac=lambda t,z:jacobian(m,z,b),method=method,
                    rtol=rtol,atol=atol,max_step=maxstep,
                    dense_output=dense,events=events,t_eval=t_eval)
    assert sol.success,sol.message
    assert np.isfinite(sol.y).all()
    REPORT['runs'].append({'method':method,'span':[float(start),float(end)],
                           'nfev':sol.nfev,'njev':sol.njev,'nlu':sol.nlu})
    return sol

def metric_delta(a,b,cols):
    return float(np.sqrt(np.mean(np.square((a-b)[:,cols]))))

def closure_metrics(y0,y1):
    d = y1-y0
    return {'voltage_maxabs':float(np.max(abs(d[:N]))),
            'gate_maxabs':float(np.max(abs(d[N:]))),
            'scaled_rms':float(np.sqrt(np.mean(np.square(d/D))))}

def closure_pass(c):
    return c['voltage_maxabs'] <= 1e-6 and c['gate_maxabs'] <= 1e-8

def scaled_jac(m,y,b):
    j = jacobian(m,y,b).tocoo()
    return sparse.csc_matrix((j.data*D[j.col]/D[j.row],(j.row,j.col)),shape=(2*N,2*N))

def monodromy(m,orbit,period,b,steps,label):
    started = time.monotonic()
    p = np.eye(2*N)
    identity = sparse.eye(2*N,format='csc')
    h = period/steps
    for k in range(steps):
        j = scaled_jac(m,orbit.sol((k+.5)*h),b)
        lu = splu(identity-.5*h*j)
        p = lu.solve((identity+.5*h*j).dot(p))
    assert np.isfinite(p).all()
    values,vectors = linalg.eig(p)
    phase = int(np.argmin(abs(values-1)))
    others = np.delete(np.arange(2*N),phase)
    dominant = int(others[np.argmax(abs(values[others]))])
    f0 = m.rhs(0.,orbit.y[:,0],b)/D
    f1 = m.rhs(period,orbit.y[:,-1],b)/D
    action = np.einsum('ij,j->i',p,f0,optimize=False)
    rec = {'steps':steps,'phase_multiplier':[float(values[phase].real),float(values[phase].imag)],
           'phase_error':float(abs(values[phase]-1)),
           'dominant_nontrivial_multiplier':[float(values[dominant].real),float(values[dominant].imag)],
           'dominant_nontrivial_modulus':float(abs(values[dominant])),
           'tangent_transport_relative':float(np.linalg.norm(action-f1)/np.linalg.norm(f1)),
           'top12_moduli':sorted([float(abs(v)) for v in values],reverse=True)[:12],
           'all_other_count':len(others),'self_elapsed_s':time.monotonic()-started}
    np.savez_compressed(OUT/(label+'.npz'),matrix=p,eigenvalues=values,eigenvectors=vectors,
                        phase_index=np.array(phase),dominant_index=np.array(dominant))
    print('MONODROMY',json.dumps(rec),flush=True)
    return p,values,vectors,phase,dominant,rec

def source_checks(m,y,b):
    m.source_setup(b,b,-1.)
    own = m.rhs(0.,y,b)
    literal = m.source['membrane_voltageRHS'](0.,y)
    scalar = scalar_rhs(m,y,b)
    j = jacobian(m,y,b).toarray()
    return {'source_rhs_maxabs':float(np.max(abs(own-literal))),
            'scalar_rhs_maxabs':float(np.max(abs(own-scalar))),
            'source_jac_maxabs':float(np.max(abs(j-m.source['compute_jacobian'](0.,y)))),
            'inherited_dense_jac_maxabs':float(np.max(abs(j-m.jac(0.,y,b))))}

def main():
    frozen = json.loads((OUT/'FREEZE.json').read_text())
    for name,h in frozen['sha256'].items():
        assert sha(OUT/name) == h,(name,'frozen bytes changed')
    helper = REVIEW/'independent_model.py'
    assert sha(helper) == frozen['reused_helper_sha256']
    m = prior.Model()
    b = background(m)
    section_j = m.names.index('VB01')
    with np.load(OUT/'INPUT_STATES.npz',allow_pickle=False) as z:
        section = float(z['section'])
        initial = {k:z[k].copy() for k in ('seed0_finite','seed0_sham','seed1_finite','seed1_sham')}
        assert np.array_equal(z['background'],b)
    assert section == 43.89687263267149
    def event(t,y):
        return y[section_j]-section
    event.direction = 1
    event.terminal = False
    REPORT.update(initial_native_utc='2026-11-03T07:10:34Z',frozen_at_utc=frozen['frozen_at_utc'],
                  started_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
                  horizon_s=300.,model_neurons=N,model_states=2*N,
                  material_cutoff=CUTOFF,background_common=True)
    ends = {}; windows = {}; challenges = {}; crossing = {}
    times = np.linspace(42.,300.,12901)
    for seed in (0,1):
        for branch in ('finite','sham'):
            key = f'seed{seed}_{branch}'
            sol = solve_constant(m,initial[key],42.,300.,b,
                                 events=event if branch=='sham' else None,t_eval=times)
            y = sol.y.T
            ends[key] = y[-1].copy()
            windows[key] = y[times>=290.-1e-10].copy()
            np.savez_compressed(OUT/(key+'_continuation.npz'),t=times,y=y,
                                event_times=sol.t_events[0] if branch=='sham' else np.array([]),
                                event_states=sol.y_events[0] if branch=='sham' else np.empty((0,2*N)))
            if branch == 'sham':
                et,ey = sol.t_events[0],sol.y_events[0]
                crossing[key] = (et.copy(),ey.copy())
                intervals = np.diff(et)
                errors = np.sqrt(np.mean(np.square(np.diff(ey,axis=0)/D),axis=1))
                REPORT[key+'_returns'] = {'crossing_count':len(et),
                    'last20_periods':intervals[-20:].tolist(),
                    'last20_scaled_return_rms':errors[-20:].tolist(),
                    'last20_max_period_range':float(np.ptp(intervals[-20:])) if len(intervals) else None}
            del sol,y
            # Both histories receive exactly the same source-smoothed challenge.
            tc,yc = m.schedule(ends[key],300.,302.,b,[(300.,m.presets['FWD'])],
                                rtol=2e-10,atol=2e-11)
            np.savez_compressed(OUT/(key+'_challenge.npz'),t=tc,y=yc)
            challenges[key] = yc[tc>=300.3-1e-10].copy()
            write('PROGRESS.json',REPORT)
            print('CONTINUATION_COMPLETE',key,'elapsed',time.monotonic()-PROCESS_START,flush=True)
    REPORT['contrasts'] = {}
    th = m.threshold(b)
    for seed in (0,1):
        f,s = f'seed{seed}_finite',f'seed{seed}_sham'
        late = metric_delta(windows[f],windows[s],m.motor)
        challenge = metric_delta(challenges[f],challenges[s],m.motor)
        vf = 500*np.tanh((windows[f][:,:N]-th)/500)
        vs = 500*np.tanh((windows[s][:,:N]-th)/500)
        REPORT['contrasts'][str(seed)] = {'late_290_300_motor_rms':late,
            'challenge_300_3_302_motor_rms':challenge,
            'late_full_voltage_rms':metric_delta(windows[f],windows[s],np.arange(N)),
            'late_full_gate_rms':metric_delta(windows[f],windows[s],np.arange(N,2*N)),
            'instantaneous_renderer_late_motor_rms':metric_delta(vf,vs,m.motor),
            'finite_late_motor_temporal_rms':float(np.sqrt(np.mean(np.square(windows[f][:,m.motor]-windows[f][:,m.motor].mean(0))))),
            'sham_late_motor_temporal_rms':float(np.sqrt(np.mean(np.square(windows[s][:,m.motor]-windows[s][:,m.motor].mean(0))))),
            'material_late_and_challenge':bool(late>=CUTOFF and challenge>=CUTOFF)}
    REPORT['roots'] = {}
    roots = {}
    for seed in (0,1):
        key = f'seed{seed}_finite'
        answer = root(lambda y:m.rhs(0.,y,b),initial[key],
                      jac=lambda y:jacobian(m,y,b).toarray(),method='hybr',
                      options={'xtol':1e-10,'maxfev':200})
        ev = linalg.eigvals(jacobian(m,answer.x,b).toarray())
        residual = m.rhs(0.,answer.x,b)
        rc = {'solver_success':bool(answer.success),'solver_message':str(answer.message),
            'nfev':int(answer.nfev),'voltage_residual_maxabs':float(np.max(abs(residual[:N]))),
            'gate_residual_maxabs':float(np.max(abs(residual[N:]))),
            'largest_real_eigenvalue_per_s':float(ev.real.max()),
            'gate_min_max':[float(answer.x[N:].min()),float(answer.x[N:].max())],
            'root_to_300s_endpoint':closure_metrics(answer.x,ends[key]),
            'source_checks':source_checks(m,answer.x,b)}
        rc['passes'] = bool(rc['voltage_residual_maxabs']<=1e-6 and rc['gate_residual_maxabs']<=1e-8 and
                            ev.real.max() < -1e-3 and answer.x[N:].min()>=0 and answer.x[N:].max()<=1 and
                            closure_pass(rc['root_to_300s_endpoint']))
        roots[key] = answer.x.copy()
        REPORT['roots'][key] = rc
        np.savez_compressed(OUT/(key+'_equilibrium.npz'),y=answer.x,rhs=residual,eigenvalues=ev)
    et,ey = crossing['seed0_sham']
    REPORT['cycle'] = {'status':'NOT_YET_CLOSED'}
    if len(et) < 21:
        REPORT['cycle']['status'] = 'NO_21_SECTION_CROSSINGS_NO_ALTERNATE_SECTION'
        return
    cycle0 = ey[-1].copy()
    period = float(np.median(np.diff(et)[-5:]))
    shooting = []
    orbit = None
    for iteration in range(4):
        orbit = solve_constant(m,cycle0,0.,period,b,dense=True,rtol=2e-11,atol=2e-12,maxstep=.02)
        c = closure_metrics(cycle0,orbit.y[:,-1])
        shooting.append({'iteration':iteration,'period_s':period,'closure':c,
                         'section_error':float(abs(cycle0[section_j]-section))})
        np.savez_compressed(OUT/f'shooting_{iteration}.npz',t=orbit.t,y=orbit.y.T,
                            initial=cycle0,period=np.array(period))
        if closure_pass(c) and abs(cycle0[section_j]-section)<=1e-8:
            break
        if iteration == 3:
            orbit = None
            break
        p,values,vectors,phase,dominant,rec = monodromy(m,orbit,period,b,512,f'shooting_{iteration}_M512')
        bordered = np.zeros((2*N+1,2*N+1))
        bordered[:-1,:-1] = p-np.eye(2*N)
        bordered[:-1,-1] = m.rhs(period,orbit.y[:,-1],b)/D
        bordered[-1,section_j] = 1.
        residual = np.r_[(orbit.y[:,-1]-cycle0)/D,(cycle0[section_j]-section)/D[section_j]]
        correction = linalg.solve(bordered,-residual)
        shooting[-1]['correction_scaled_maxabs'] = float(np.max(abs(correction)))
        if not np.isfinite(correction).all() or np.max(abs(correction))>.1 or period+correction[-1]<=0:
            shooting[-1]['correction_rejected'] = True
            orbit = None
            break
        cycle0 = cycle0+D*correction[:-1]
        period += float(correction[-1])
    REPORT['cycle']['shooting'] = shooting
    if orbit is None:
        REPORT['cycle']['status'] = 'BOUNDED_SHOOTING_FAILED_NO_RESTART'
        return
    raw_times = np.linspace(0,period,4097)
    raw_states = orbit.sol(raw_times).T
    np.savez_compressed(OUT/'PERIODIC_ORBIT.npz',t=raw_times,y=raw_states,period=np.array(period),section=np.array(section))
    refinements = []
    last = None
    for steps in (512,1024,2048):
        last = monodromy(m,orbit,period,b,steps,f'MONODROMY_{steps}')
        refinements.append(last[-1])
    p,values,vectors,phase,dominant,rec = last
    change = abs(refinements[-1]['dominant_nontrivial_modulus']-refinements[-2]['dominant_nontrivial_modulus'])
    margin = max(.001,10*change)
    tangent_checks = {}
    sine = np.sin(np.arange(2*N)+.5)
    leading = vectors[:,dominant].real
    leading /= np.sqrt(np.mean(leading**2))
    directions = {'fixed_sine':sine,'dominant_nontrivial_real':leading}
    for name,direction in directions.items():
        def tj(t,z):
            return scaled_jac(m,orbit.sol(t),b)
        lin = solve_ivp(lambda t,z:tj(t,z).dot(z),(0.,period),direction,
                        jac=tj,method='BDF',rtol=2e-11,atol=2e-12,max_step=.01)
        assert lin.success,lin.message
        expected = np.einsum('ij,j->i',p,direction,optimize=False)
        relative = float(np.linalg.norm(lin.y[:,-1]-expected)/max(np.linalg.norm(expected),1e-15))
        tangent_checks[name] = {'relative_action_error':relative,'passes':bool(relative<1e-4),
                                'nfev':lin.nfev,'nlu':lin.nlu}
        np.savez_compressed(OUT/('TANGENT_'+name+'.npz'),t=lin.t,z=lin.y.T,direction=direction,
                            midpoint_action=expected)
    eps = 1e-5
    nonlinear = []
    m.source_setup(b,b,-1.)
    for sign in (-1,1):
        zz = solve_ivp(m.source['membrane_voltageRHS'],(0.,period),cycle0+sign*eps*D*leading,
                       jac=m.source['compute_jacobian'],method='BDF',rtol=2e-11,atol=2e-12,max_step=.01)
        assert zz.success,zz.message
        nonlinear.append(zz.y[:,-1])
        np.savez_compressed(OUT/f'NONLINEAR_TANGENT_{sign:+d}.npz',t=zz.t,y=zz.y.T)
    fd = (nonlinear[1]-nonlinear[0])/(2*eps*D)
    expected = np.einsum('ij,j->i',p,leading,optimize=False)
    fd_error = float(np.linalg.norm(fd-expected)/max(np.linalg.norm(expected),1e-15))
    check_states = [source_checks(m,orbit.sol(t),b) for t in (0.,period/3,2*period/3)]
    root0 = roots['seed0_finite']
    motor_dist = np.sqrt(np.mean(np.square(raw_states[:,m.motor]-root0[m.motor]),axis=1))
    init_compat = {
        'seed1_last_section_vs_seed0_periodic_state':closure_metrics(cycle0,crossing['seed1_sham'][1][-1]),
        'finite_seed1_vs_seed0_root':closure_metrics(root0,roots['seed1_finite']),
        'equilibrium_min_motor_distance_over_cycle':float(motor_dist.min()),
        'equilibrium_mean_motor_distance_over_cycle':float(motor_dist.mean())}
    source_ok = all(c['source_rhs_maxabs']<1e-5 and c['scalar_rhs_maxabs']<1e-5 and
                    c['source_jac_maxabs']<1e-8 and c['inherited_dense_jac_maxabs']<1e-8 for c in check_states)
    transverse = bool(rec['phase_error']<1e-4 and rec['tangent_transport_relative']<1e-4 and
                       change<.001 and rec['dominant_nontrivial_modulus']<1-margin)
    returns_ok = all(REPORT[k+'_returns']['crossing_count']>=21 and
                     max(REPORT[k+'_returns']['last20_scaled_return_rms'])<1e-4 and
                     REPORT[k+'_returns']['last20_max_period_range']<1e-4 for k in ('seed0_sham','seed1_sham'))
    compatible = bool(init_compat['seed1_last_section_vs_seed0_periodic_state']['scaled_rms']<1e-4 and
                      init_compat['finite_seed1_vs_seed0_root']['scaled_rms']<1e-4)
    numeric_ok = bool(source_ok and all(c['passes'] for c in tangent_checks.values()) and fd_error<2e-4)
    REPORT['cycle'].update(status='PERIODIC_ORBIT_AND_FULL_VARIATIONAL_CALCULATION_COMPLETE',
        period_s=period,closure=closure_metrics(cycle0,orbit.y[:,-1]),
        monodromy_refinements=refinements,dominant_modulus_1024_2048_change=change,
        required_stability_margin=margin,transverse_stability_passes=transverse,
        last20_return_convergence_passes=returns_ok,tangent_BDF_checks=tangent_checks,
        nonlinear_source_BDF_central_difference_relative_error=fd_error,
        independent_numerical_checks_pass=numeric_ok,source_scalar_jac_checks=check_states,
        initialization_compatibility=init_compat,initialization_compatible=compatible,
        rigorous_computer_assisted_theorem=False)
    REPORT['all_predeclared_claim_gates_pass'] = bool(transverse and returns_ok and compatible and numeric_ok and
        all(v['passes'] for v in REPORT['roots'].values()) and
        all(v['material_late_and_challenge'] for v in REPORT['contrasts'].values()))
    REPORT['status'] = 'FROZEN_STABILITY_EXPERIMENT_COMPLETE'

if __name__ == '__main__':
    signal.signal(signal.SIGALRM,timed_out)
    signal.alarm(1080)
    try:
        main()
    except BaseException as exc:
        REPORT['status'] = 'FAILED_OR_BOUNDARY_STOP_PARTIAL_EVIDENCE_PRESERVED'
        REPORT['exception'] = repr(exc)
        raise
    finally:
        signal.alarm(0)
        REPORT['finished_utc'] = datetime.datetime.now(datetime.timezone.utc).isoformat()
        REPORT['process_self_elapsed_s'] = time.monotonic()-PROCESS_START
        REPORT['rss_bytes_macos'] = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        REPORT['all_raw_summary_auxiliary_outputs_consumed_development'] = True
        REPORT['new_public_ops_ingress_dependencies'] = [0,0,0]
        REPORT['native_mission_completed'] = False
        write('STABILITY_RESULT.json',REPORT)
        print(json.dumps(REPORT,indent=2),flush=True)
