import datetime, hashlib, resource, signal, time, traceback, warnings
from model import *
from scipy.integrate import solve_ivp

def utc():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()

def solve(m, y, a, b, old, new=None, step=.03, tight=False, dense=False):
    if new is None:
        mask = lambda t: old
    else:
        mask = lambda t: old + (new-old) * (.5 + .5*np.tanh((t-a-.15)/.025))
    sol = solve_ivp(lambda t, x: m.rhs(x, mask(t)), (a, b), y, method="BDF",
                    jac=lambda t, x: m.jac(x, mask(t)), rtol=2e-11 if tight else 2e-10,
                    atol=2e-12 if tight else 2e-11, max_step=step, dense_output=dense)
    if not sol.success:
        raise RuntimeError(sol.message)
    return sol

def maxerr(a, b):
    return {"V_maxabs": float(np.max(np.abs(a[:N]-b[:N]))), "S_maxabs": float(np.max(np.abs(a[N:]-b[N:]))),
            "scaled_rms": float(np.sqrt(np.mean(((a-b)/D)**2)))}

def spectrum(matrix):
    eig = linalg.eigvals(matrix, check_finite=True)
    pi = int(np.argmin(np.abs(eig-1)))
    other = np.delete(eig, pi)
    return eig, pi, float(np.max(np.abs(other)))

def main(result):
    m = Circuit()
    result["independence"] = "own edge-list RHS, sparse balance, analytic Jacobian, BDF orbit and endpoint-Jacobian trapezoidal full variational flow; zero lab helper imports"
    source = m.source_comparator()
    source.update(t_Switch=-1., transit_End=-.7, oldMask=m.background, newMask=m.background,
                  Vth_Static=source["EffVth_rhs"](CURRENT, m.background))
    z = np.load(AUTHOR / "SOURCE_REFERENCE.npz", allow_pickle=False)
    ref = solve(m, z["literal"][0], float(z["t"][0]), float(z["t"][-1]), m.fwd, step=.005, tight=True, dense=True)
    ref_y = ref.sol(z["t"]).T
    referr = float(np.max(np.abs(ref_y[:, m.motor] - z["literal"][:, m.motor])))
    np.savez_compressed(OUT / "FWD_SOURCE_REFERENCE.npz", t=z["t"], y=ref_y)
    result["original_54step_FWD_motor_maxabs"] = referr
    assert referr <= 5e-5, "original FWD reference gate"
    print("ORIGINAL_REFERENCE", referr, utc(), flush=True)

    with np.load(AUTHOR / "PERIODIC_ORBIT.npz", allow_pickle=False) as z:
        y0, period = z["y"][0].copy(), float(z["period"])
        author_orbit_closure = maxerr(z["y"][-1], y0)
    result["author_raw_orbit_closure"] = author_orbit_closure
    orbit = solve(m, y0, 0., period, m.background, step=.01, tight=True, dense=True)
    closure = maxerr(orbit.y[:, -1], y0)
    result["own_BDF_orbit"] = dict(period_s=period, closure=closure, nfev=orbit.nfev, nlu=orbit.nlu)
    assert closure["V_maxabs"] <= 1e-6 and closure["S_maxabs"] <= 1e-8, "independent periodic closure gate"
    np.savez_compressed(OUT / "INDEPENDENT_ORBIT.npz", t=np.linspace(0, period, 2049), y=orbit.sol(np.linspace(0, period, 2049)).T, period=period)
    source_checks = []
    for phase in (0., period/3, 2*period/3):
        y = orbit.sol(phase)
        rhs = m.rhs(y, m.background)
        j = m.jac(y, m.background)
        direction = D * np.sin(np.arange(2*N)+.25)
        eps = 1e-5
        fd = (m.rhs(y+eps*direction, m.background)-m.rhs(y-eps*direction, m.background))/(2*eps)
        jd = j @ direction
        item = dict(phase_s=phase, rhs_maxabs=float(np.max(np.abs(rhs-source["membrane_voltageRHS"](1., y)))),
                    jac_maxabs=float(np.max(np.abs(j.toarray()-source["compute_jacobian"](1., y)))),
                    directional_jac_relative=float(linalg.norm(fd-jd)/linalg.norm(jd)))
        source_checks.append(item)
        assert item["rhs_maxabs"] < 1e-6 and item["jac_maxabs"] < 1e-7 and item["directional_jac_relative"] < 1e-6, "source expression gate"
    result["source_checks_on_independent_cycle"] = source_checks
    roots = {}
    for seed in (0, 1):
        z = np.load(AUTHOR / ("seed%d_finite_equilibrium.npz" % seed), allow_pickle=False)
        y = z["y"]
        f = m.rhs(y, m.background)
        eig = linalg.eigvals(m.jac(y, m.background).toarray())
        roots[str(seed)] = dict(V_residual_max=float(np.max(np.abs(f[:N]))), S_residual_max=float(np.max(np.abs(f[N:]))),
                                max_real_eigenvalue=float(np.max(eig.real)), gate_min=float(np.min(y[N:])), gate_max=float(np.max(y[N:])),
                                source_rhs_maxabs=float(np.max(np.abs(f-source["membrane_voltageRHS"](1., y)))))
        np.savez_compressed(OUT / ("EQUILIBRIUM_AUDIT_seed%d.npz" % seed), y=y, rhs=f, eigenvalues=eig)
        assert roots[str(seed)]["V_residual_max"] < 1e-6 and roots[str(seed)]["S_residual_max"] < 1e-8 and np.max(eig.real) < -.001, "equilibrium stability gate"
    result["roots"] = roots
    print("ROOTS_ORBIT_SOURCE", roots, closure, utc(), flush=True)

    all_mon = []
    for steps in (1024, 2048):
        times = np.linspace(0., period, steps+1)
        states = orbit.sol(times)
        h = period/steps
        def sj(y):
            return m.jac(y, m.background).multiply(D[None, :]).multiply((1/D)[:, None]).tocsc()
        ident = sparse.eye(2*N, format="csc")
        p = np.eye(2*N)
        jp = sj(states[:, 0])
        for k in range(steps):
            jn = sj(states[:, k+1])
            p = splu(ident - .5*h*jn).solve(p + .5*h*(jp @ p))
            jp = jn
        eig, phase_index, largest = spectrum(p)
        tangent = m.rhs(y0, m.background)/D
        tangent_error = float(linalg.norm(np.einsum("ij,j->i", p, tangent)-tangent)/linalg.norm(tangent))
        item = dict(steps=steps, phase_real=float(eig[phase_index].real), phase_imag=float(eig[phase_index].imag),
                    phase_error=float(abs(eig[phase_index]-1)), largest_557_transverse_modulus=largest, tangent_relative_error=tangent_error,
                    top12_moduli=sorted(np.abs(eig).tolist(), reverse=True)[:12])
        np.savez_compressed(OUT / ("OWN_MONODROMY_%d.npz" % steps), matrix=p, eigenvalues=eig, phase_index=phase_index)
        all_mon.append(item)
        print("FULL_VARIATIONAL", item, utc(), flush=True)
    result["full_variational_trapezoid"] = all_mon
    final = all_mon[-1]
    result["dominant_modulus_refinement_change"] = abs(all_mon[-1]["largest_557_transverse_modulus"]-all_mon[0]["largest_557_transverse_modulus"])
    assert final["phase_error"] < 2e-4 and final["tangent_relative_error"] < 2e-4 and final["largest_557_transverse_modulus"] < .999 and result["dominant_modulus_refinement_change"] < .001, "full cycle stability gate"
    auth_mon = []
    for steps in (512, 1024, 2048):
        with np.load(AUTHOR / ("MONODROMY_%d.npz" % steps), allow_pickle=False) as z:
            e, pi, largest = spectrum(z["matrix"])
            auth_mon.append(dict(steps=steps, phase_error=float(abs(e[pi]-1)), largest_557_transverse_modulus=largest,
                                 stored_spectrum_nearest_maxabs=float(np.max(np.min(np.abs(e[:, None]-z["eigenvalues"][None, :]), axis=1)))))
    result["author_raw_full_monodromy_recomputed_spectra"] = auth_mon

    with np.load(AUTHOR / "INPUT_STATES.npz", allow_pickle=False) as z:
        cached = {k: z[k].copy() for k in z.files}
    assert np.array_equal(cached["background"], m.background)
    access = {}
    for seed in (0, 1):
        init = 1e-4*np.random.RandomState(seed).normal(0., .94, 2*N)
        base = solve(m, init, 0., 20., m.background, dense=True)
        np.savez_compressed(OUT / ("ACCESS_seed%d_baseline.npz" % seed), t=np.linspace(0, 20, 1001), y=base.sol(np.linspace(0, 20, 1001)).T)
        sham = solve(m, base.y[:, -1], 20., 42., m.background, dense=True)
        np.savez_compressed(OUT / ("ACCESS_seed%d_sham.npz" % seed), t=np.linspace(20, 42, 1101), y=sham.sol(np.linspace(20, 42, 1101)).T)
        history = []
        y = base.y[:, -1]
        segments = [(20., 20.3, m.background, m.fwd, .005), (20.3, 22., m.fwd, None, .03),
                    (22., 22.3, m.fwd, m.background, .005), (22.3, 42., m.background, None, .03)]
        for k, (a, b, old, new, step) in enumerate(segments):
            sol = solve(m, y, a, b, old, new, step=step, dense=True)
            tt = np.linspace(a, b, max(2, int(round((b-a)*100))+1))
            yy = sol.sol(tt).T
            np.savez_compressed(OUT / ("ACCESS_seed%d_finite_segment%d.npz" % (seed, k)), t=tt, y=yy)
            history.append(dict(span=[a, b], nfev=sol.nfev, nlu=sol.nlu))
            y = sol.y[:, -1]
        access[str(seed)] = dict(finite=maxerr(y, cached["seed%d_finite" % seed]), sham=maxerr(sham.y[:, -1], cached["seed%d_sham" % seed]),
                                finite_motor_maxabs=float(np.max(np.abs(y[m.motor]-cached["seed%d_finite" % seed][m.motor]))),
                                sham_motor_maxabs=float(np.max(np.abs(sham.y[m.motor, -1]-cached["seed%d_sham" % seed][m.motor]))), segments=history)
        assert access[str(seed)]["finite_motor_maxabs"] < .001 and access[str(seed)]["sham_motor_maxabs"] < .001, "finite source-input accessibility reproduction gate"
        print("ACCESSIBILITY", seed, access[str(seed)], utc(), flush=True)
    result["source_initialization_to_42s_accessibility"] = access

    raw = {}
    for seed in (0, 1):
        finite = np.load(AUTHOR / ("seed%d_finite_continuation.npz" % seed), allow_pickle=False)
        sham = np.load(AUTHOR / ("seed%d_sham_continuation.npz" % seed), allow_pickle=False)
        t, fy, sy = finite["t"], finite["y"], sham["y"]
        assert np.array_equal(t, sham["t"]) and np.array_equal(fy[0], cached["seed%d_finite" % seed]) and np.array_equal(sy[0], cached["seed%d_sham" % seed])
        late = t >= 290.-1e-9
        d = fy[late][:, m.motor] - sy[late][:, m.motor]
        events = sham["event_times"]
        es = sham["event_states"]
        row = dict(late_motor_rms=float(np.sqrt(np.mean(d*d))), sham_crossing_count=len(events),
                   last20_period_range=float(np.ptp(np.diff(events)[-20:])),
                   last20_scaled_return_rms_max=float(np.max(np.sqrt(np.mean(((es[-20:]-es[-21:-1])/D)**2, axis=1)))),
                   finite_gate_min=float(np.min(fy[:, N:])), finite_gate_max=float(np.max(fy[:, N:])),
                   sham_gate_min=float(np.min(sy[:, N:])), sham_gate_max=float(np.max(sy[:, N:])), forks_bitwise=True)
        for branch, yy in (("finite", fy), ("sham", sy)):
            z = np.load(AUTHOR / ("seed%d_%s_challenge.npz" % (seed, branch)), allow_pickle=False)
            assert np.array_equal(yy[-1], z["y"][0]), "300s challenge fork gate"
        zf = np.load(AUTHOR / ("seed%d_finite_challenge.npz" % seed), allow_pickle=False)
        zs = np.load(AUTHOR / ("seed%d_sham_challenge.npz" % seed), allow_pickle=False)
        w = zf["t"] >= 300.3-1e-9
        delta = zf["y"][w][:, m.motor]-zs["y"][w][:, m.motor]
        row["challenge_motor_rms"] = float(np.sqrt(np.mean(delta*delta)))
        assert row["late_motor_rms"] > SCALE/10 and row["challenge_motor_rms"] > SCALE/10
        raw[str(seed)] = row
        del fy, sy
    result["author_raw_scores_crossings_gates_and_forks"] = raw
    freeze = json.loads((AUTHOR / "FREEZE.json").read_text())
    verified = {}
    for name, expected in freeze["sha256"].items():
        actual = hashlib.sha256((AUTHOR / name).read_bytes()).hexdigest()
        verified[name] = actual == expected
        assert actual == expected, "author frozen hash gate"
    result["author_frozen_bytes_verified"] = verified
    result["author_freeze_before_main"] = freeze["frozen_at_utc"] < json.loads((AUTHOR / "STABILITY_RESULT.json").read_text())["started_utc"]
    result["all_independent_reconstruction_gates_pass"] = True

if __name__ == "__main__":
    signal.alarm(800)
    started = time.perf_counter()
    result = {"started_utc": utc(), "all_independent_reconstruction_gates_pass": False}
    with warnings.catch_warnings(record=True) as ww:
        warnings.simplefilter("always")
        try:
            main(result)
            result["native_process_exit"] = 0
        except BaseException as exc:
            result["native_process_exit"] = 1
            result["exception"] = repr(exc)
            (OUT / "RECONSTRUCTION_FAILURE.txt").write_text(traceback.format_exc())
        result["warnings"] = [{"category": w.category.__name__, "message": str(w.message), "filename": w.filename, "lineno": w.lineno} for w in ww]
    result.update(finished_utc=utc(), self_elapsed_s=time.perf_counter()-started, rss_bytes_macos=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
    dump("RECONSTRUCTION.json", result)
    print("FINISHED", result["native_process_exit"], result["self_elapsed_s"], result["rss_bytes_macos"], flush=True)
    raise SystemExit(result["native_process_exit"])
