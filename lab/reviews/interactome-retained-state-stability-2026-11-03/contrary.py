import datetime, resource, signal, time, traceback, warnings
from model import *
from scipy.integrate import solve_ivp

def run(m, y, challenge):
    records = []
    if challenge:
        spans = [(300., 300.3, True, .005), (300.3, 302., False, .01)]
    else:
        spans = [(300., 302., False, .01)]
    ts, ys = [], []
    for a, b, transition, step in spans:
        if transition:
            mask = lambda t: m.background+(m.fwd-m.background)*(.5+.5*np.tanh((t-300.-.15)/.025))
        else:
            fixed = m.fwd if challenge else m.background
            mask = lambda t: fixed
        sol = solve_ivp(lambda t, x: m.rhs(x, mask(t)), (a, b), y, method="BDF", jac=lambda t, x: m.jac(x, mask(t)),
                        rtol=2e-10, atol=2e-11, max_step=step, dense_output=True)
        if not sol.success:
            raise RuntimeError(sol.message)
        tt = 300. + np.arange(int(round((a-300.)*100)), int(round((b-300.)*100))+1)/100
        if ts:
            tt = tt[1:]
        ts.extend(tt.tolist())
        ys.extend(sol.sol(tt).T.tolist())
        y = sol.y[:, -1]
        records.append(dict(span=[a, b], nfev=sol.nfev, nlu=sol.nlu))
    return np.array(ts), np.array(ys), records

def main(result):
    m = Circuit()
    scores = {}
    for seed in (0, 1):
        paths = {}
        replay = {}
        for branch in ("finite", "sham"):
            with np.load(AUTHOR / ("seed%d_%s_challenge.npz" % (seed, branch)), allow_pickle=False) as z:
                y0, original = z["y"][0].copy(), z["y"].copy()
            for challenge in (False, True):
                t, y, statistics = run(m, y0, challenge)
                label = "%s_%s" % (branch, "challenge" if challenge else "no_challenge")
                paths[label] = y
                np.savez_compressed(OUT / ("CONTRARY_seed%d_%s.npz" % (seed, label)), t=t, y=y)
                result["runs"].append(dict(seed=seed, branch=branch, challenge=challenge, statistics=statistics))
                if challenge:
                    replay[branch] = float(np.max(np.abs(y[:, m.motor]-original[:, m.motor])))
                    assert replay[branch] < .001, "independent challenged-path replay gate"
        w = t >= 300.3-1e-9
        absolute = paths["finite_challenge"]-paths["sham_challenge"]
        background = paths["finite_no_challenge"]-paths["sham_no_challenge"]
        interaction = absolute-background
        rms = lambda a: float(np.sqrt(np.mean(a[w][:, m.motor]**2)))
        endpoint = lambda a: dict(motor_rms=float(np.sqrt(np.mean(a[-1, m.motor]**2))), scaled_full_rms=float(np.sqrt(np.mean((a[-1]/D)**2))),
                                  V_maxabs=float(np.max(np.abs(a[-1, :N]))), S_maxabs=float(np.max(np.abs(a[-1, N:]))))
        scores[str(seed)] = dict(absolute_challenged_motor_rms=rms(absolute), matched_no_challenge_motor_rms=rms(background),
                                 evoked_interaction_motor_rms=rms(interaction), passes_unchanged_material_gate=rms(interaction)>SCALE/10,
                                 endpoint_302_challenged=endpoint(absolute), endpoint_302_no_challenge=endpoint(background), challenged_replay_motor_maxabs=replay)
        print("CONTRARY", seed, scores[str(seed)], flush=True)
    result["scores"] = scores
    result["both_evoked_interactions_material"] = all(x["passes_unchanged_material_gate"] for x in scores.values())
    result["interpretation"] = "one fixed matched no-challenge comparison, no altered experimental settings or new post302s horizon"

if __name__ == "__main__":
    signal.alarm(250)
    started = time.perf_counter()
    result = dict(started_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(), runs=[], native_process_exit=1)
    with warnings.catch_warnings(record=True) as ww:
        warnings.simplefilter("always")
        try:
            main(result)
            result["native_process_exit"] = 0
        except BaseException as exc:
            result["exception"] = repr(exc)
            (OUT / "CONTRARY_FAILURE.txt").write_text(traceback.format_exc())
        result["warnings"] = [{"category": w.category.__name__, "message": str(w.message), "filename": w.filename, "lineno": w.lineno} for w in ww]
    result.update(finished_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(), self_elapsed_s=time.perf_counter()-started, rss_bytes_macos=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
    dump("CONTRARY.json", result)
    print("FINISHED", result["native_process_exit"], result["self_elapsed_s"], result["rss_bytes_macos"], flush=True)
    raise SystemExit(result["native_process_exit"])
