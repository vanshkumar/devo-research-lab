"""Independent scalar-loop comparison with the root's compiled HVC kernel.

Does not import hvc_model.py or its numpy reference implementation.
Equations transcribed from public HVCIter.m; source provenance remains in prior_work.
"""
from pathlib import Path
import ctypes
import hashlib
import json
import random
import numpy as np
from scipy.io import loadmat

HERE = Path(__file__).resolve().parent
BASE = HERE.parents[1]
LIB = BASE / "outputs/hvc/hvc_kernel.dylib"
CPP = BASE / "experiments/hvc_kernel.cpp"
SOURCE = BASE / "inputs/prior_work/mackevicius_code/NIf Paper - code to publish - Sept2020/Sporadic HVC Simulations"


def scalar_model(weights, noise, onsets, parameters):
    w = [row[:] for row in weights]
    n = len(w)
    beta, alpha, eta, epsilon, tau, gamma, wmax, Wmax, k = parameters
    oldx = [0.] * n
    oldy = [0.] * n
    activity = []
    for time in range(len(onsets)):
        y = [oldy[i] + (oldx[i]-oldy[i])/tau for i in range(n)]
        net = []
        for i in range(n):
            stimulus = (10. if onsets[time] else -10.) if i < int(k) else noise[time][i]
            excitatory = sum(w[i][j]*oldx[j] for j in range(n))
            net.append(max(0., excitatory-beta*sum(oldx)-alpha*y[i]+stimulus))
        recurrent = gamma*sum(net)
        x = [float(net[i]-recurrent > 0.) for i in range(n)]
        stdp = [[eta*(x[i]*oldx[j]-oldx[i]*x[j]) for j in range(n)] for i in range(n)]
        tentative = [[w[i][j]+stdp[i][j] for j in range(n)] for i in range(n)]
        pre = [eta*max(0., sum(tentative[i][j] for i in range(n))-Wmax) for j in range(n)]
        post = [eta*max(0., sum(tentative[i])-Wmax) for i in range(n)]
        if eta > 0.:
            w = [[0. if i == j else max(0., min(wmax, tentative[i][j]-epsilon*(pre[j]+post[i])))
                  for j in range(n)] for i in range(n)]
        activity.append(x)
        oldx, oldy = x, y
    return np.array(w), np.array(activity, dtype=np.uint8)


def main():
    function = ctypes.CDLL(str(LIB)).hvc_run
    array = np.ctypeslib.ndpointer
    function.argtypes = [ctypes.c_int, ctypes.c_int, array(dtype=np.float64, flags="C_CONTIGUOUS"),
                         array(dtype=np.uint8, flags="C_CONTIGUOUS"), array(dtype=np.uint8, flags="C_CONTIGUOUS"),
                         array(dtype=np.float64, flags="C_CONTIGUOUS"), array(dtype=np.uint8, flags="C_CONTIGUOUS")]
    function.restype = None
    prng = random.Random(98173)
    cases = []
    for n in (8, 12):
        for eta in (0., .025, .1):
            for style in ("source_parameters", "weak_adaptation", "silent"):
                params = [.115, 30., eta, .2, 12., .01, 1., 5., 1.]
                if style == "weak_adaptation":
                    params[1] = .5
                    params[4] = 4.
                weights = [[prng.random()*.8 for _ in range(n)] for _ in range(n)]
                noise = [[int(prng.random() < .1) for _ in range(n)] for _ in range(80)]
                onsets = [int(t % 7 == 0) for t in range(80)]
                if style == "silent":
                    noise = [[0]*n for _ in range(80)]
                    onsets = [0]*80
                wc = np.asarray(weights, dtype=np.float64).copy()
                nc = np.asarray(noise, dtype=np.uint8)
                oc = np.asarray(onsets, dtype=np.uint8)
                pc = np.asarray(params, dtype=np.float64)
                ac = np.zeros((80, n), dtype=np.uint8)
                function(n, 80, wc, nc, oc, pc, ac)
                ws, activity = scalar_model(weights, noise, onsets, params)
                error = float(np.max(np.abs(wc-ws)))
                exact = bool(np.array_equal(ac, activity))
                assert error < 1e-12 and exact
                cases.append(dict(neurons=n, eta=eta, style=style, max_weight_error=error,
                                  exact_activity=exact, total_spikes=int(ac.sum())))
    times = np.asarray(loadmat(SOURCE / "trialTimes.mat")["trialTimes"]).ravel()
    tt = times.astype(int)-1
    kept = tt[(tt >= 0) & (tt < 360000-100)]
    result = {"comparison": "Independent Python scalar loops vs root compiled C++; no root functions imported",
              "source_files_sha256": {p.name: hashlib.sha256(p.read_bytes()).hexdigest()
                                     for p in (SOURCE/"HVCIter.m", SOURCE/"HVCModel_sporadicSims.m", SOURCE/"findChainLength_v3.m")},
              "kernel_sha256": hashlib.sha256(CPP.read_bytes()).hexdigest(),
              "cases": cases, "max_weight_error": max(c["max_weight_error"] for c in cases),
              "all_activity_exact": all(c["exact_activity"] for c in cases),
              "trial_times": {"count": len(times), "first_matlab_index": int(times[0]),
                              "last_matlab_index": int(times[-1]), "dropped_by_root_filter": len(times)-len(kept),
                              "minimum_gap_steps": int(np.diff(times).min()),
                              "gaps_at_most_30_steps": int(np.sum(np.diff(times) <= 30))},
              "limits": "Validates equation/index translation, not fit to birds or exact MATLAB RNG reproduction."}
    (HERE / "hvc_independent_check.json").write_text(json.dumps(result, indent=2)+"\n")
    print(json.dumps({k: v for k, v in result.items() if k not in ("cases", "source_files_sha256")}, indent=2))


if __name__ == "__main__":
    main()
