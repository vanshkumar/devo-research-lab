"""One frozen source-prior comparison. No human data or fitted objects are read."""
import os
for _thread_option in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "VECLIB_MAXIMUM_THREADS", "NUMEXPR_NUM_THREADS"):
    os.environ[_thread_option] = "1"

from datetime import datetime, timezone
from pathlib import Path
import hashlib
import json
import math
import resource
import sys
import time
import numpy as np

HERE = Path(__file__).resolve().parent
SEED = 2026110201
BATCH = 1024
N = 131072
T = 125
K = 1000
SIGMA = .025
LAWS = ["source_bank", "fresh_iid", "Gaussian_common_mean"]
Z99 = 2.5758293035489004


def stamp():
    return datetime.now(timezone.utc).isoformat()


def write_json(name, value):
    (HERE / name).write_text(json.dumps(value, indent=2) + "\n")


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def reflect(x):
    # Literal two source statements, with no repeated-reflection substitution.
    y = np.minimum(x, np.maximum(1.5 - x, .25))
    return np.maximum(y, np.minimum(.5 - y, .75))


def reflect_scalar(x):
    if x > .75:
        return max(.25, 1.5-x)
    if x < .25:
        return min(.75, .5-x)
    return x


def logistic(x):
    return 1 / (1 + np.exp(-x))


def truncated(rng, name, args, size, low, high):
    x = getattr(rng, name)(*args, size=size)
    bad = (x < low) | (x > high)
    while np.any(bad):
        x[bad] = getattr(rng, name)(*args, size=int(bad.sum()))
        bad = (x < low) | (x > high)
    return x


def inputs(batch_id, size=BATCH):
    streams = [np.random.default_rng(s) for s in np.random.SeedSequence([SEED, batch_id]).spawn(7)]
    rprior, rinit, rbank, rindex, rfresh, rcommon, raction = streams
    params = np.column_stack([
        truncated(rprior, "gamma", (4.82, .88), size, 0, 20),
        rprior.uniform(0, 1, (size, 3)),
        truncated(rprior, "normal", (.15, 1.42), size, -20, 20),
        truncated(rprior, "normal", (.15, 1.42), size, -20, 20),
    ])
    # Eight equiprobable arrangements exactly implement the source's three coins.
    p0 = np.tile(np.array([[.6, .4], [.25, .75]]), (size, 1, 1))
    order = rinit.integers(0, 2, (size, 3))
    for i in range(size):
        if order[i, 0]:
            p0[i] = p0[i, ::-1]
        for j in range(2):
            if order[i, j+1]:
                p0[i, j] = p0[i, j, ::-1]
    bank = rbank.normal(0, SIGMA, (size, K))
    indices = rindex.integers(0, K, (size, (T-1)*4))
    rows = np.arange(size)
    increments = np.empty((3, size, (T-1)*4))
    increments[0] = bank[rows[:, None], indices]
    increments[1] = rfresh.normal(0, SIGMA, (size, (T-1)*4))
    seen = np.zeros((size, K), dtype=bool)
    for event in range((T-1)*4):
        idx = indices[:, event]
        fresh = ~seen[rows, idx]
        increments[1, fresh, event] = increments[0, fresh, event]
        seen[rows, idx] = True
    bank_mean = bank.mean(axis=1)
    increments[2] = bank_mean[:, None] + rcommon.normal(0, SIGMA*math.sqrt(1-1/K), (size, (T-1)*4))
    increments = increments.reshape(3, size, T-1, 2, 2)
    uniforms = raction.random((T, size, 5))
    return params, p0, increments, uniforms, bank_mean


def simulate(params, p0, increments, uniforms, record=False):
    size = len(params)
    b, lr, trace, w, st, respst = [params[:, i][None, :] for i in range(6)]
    q = np.zeros((3, size, 3, 2))
    p = np.broadcast_to(p0, (3, size, 2, 2)).copy()
    orient = np.zeros((3, size), dtype=int)
    prev = np.zeros((3, size), dtype=int)
    prev_left = np.zeros((3, size), dtype=bool)
    totals = np.zeros((3, size, 2), dtype=np.int16)
    expected = np.zeros((3, size, 2))
    uniform_condvar = np.zeros((3, size))
    rows = np.arange(size)[None, :]
    laws = np.arange(3)[:, None]
    prob_record, action_record = [], []
    for t in range(T):
        if t:
            p = reflect(p + increments[:, :, t-1])
        maxq = np.max(q[:, :, 1:, :], axis=-1)
        diag = np.where(orient > 0, .7, np.where(orient < 0, .3, .5))
        mb0 = diag*maxq[:, :, 0] + (1-diag)*maxq[:, :, 1]
        mb1 = (1-diag)*maxq[:, :, 0] + diag*maxq[:, :, 1]
        logit = w*(mb1-mb0) + (1-w)*(q[:, :, 0, 1]-q[:, :, 0, 0])
        leftstim = (uniforms[t, :, 4] < .5).astype(int)[None, :]
        if t:
            response_for_one = np.where(prev_left, leftstim == 1, leftstim != 1)
            logit += st*(2*prev-1) + respst*(2*response_for_one.astype(int)-1)
        first_prob = logistic(b*logit)
        second_probs = logistic(b[:, :, None]*(q[:, :, 1:, 1]-q[:, :, 1:, 0]))
        conditional_reward = (1-second_probs)*p[:, :, :, 0] + second_probs*p[:, :, :, 1]
        state0_prob = (1-first_prob)*.7 + first_prob*.3
        expected[:, :, 0] += state0_prob*conditional_reward[:, :, 0] + (1-state0_prob)*conditional_reward[:, :, 1]
        a1 = (uniforms[t, :, 0][None, :] < first_prob).astype(int)
        common = uniforms[t, :, 2][None, :] < .7
        state = np.where(common, a1, 1-a1)
        second_prob = second_probs[laws, rows, state]
        a2 = (uniforms[t, :, 1][None, :] < second_prob).astype(int)
        win = uniforms[t, :, 3][None, :] < p[laws, rows, state, a2]
        old_first = q[laws, rows, 0, a1].copy()
        old_second = q[laws, rows, state+1, a2].copy()
        q[laws, rows, 0, a1] = old_first + lr*(old_second-old_first) + trace*lr*(win-old_second)
        q[laws, rows, state+1, a2] = old_second + lr*(win-old_second)
        orient += np.where(common, 1, -1)
        prev = a1
        prev_left = a1 == leftstim
        totals[:, :, 0] += win
        pm = p.mean(axis=(2, 3))
        expected[:, :, 1] += pm
        uniform_condvar += pm*(1-pm)
        totals[:, :, 1] += uniforms[t, :, 3][None, :] < pm
        if record:
            prob_record.append(np.stack([first_prob, second_prob], axis=-1))
            action_record.append(np.stack([a1, state, a2, win.astype(int)], axis=-1))
    result = {"totals": totals.transpose(1, 0, 2), "expected": expected.transpose(1, 0, 2), "uniform_condvar": uniform_condvar.T,
              "q": q, "orientation": orient}
    if record:
        result["probabilities"] = np.array(prob_record)
        result["actions"] = np.array(action_record)
    return result


def scalar_reference(params, p0, increments, uniforms):
    # Independently written list/scalar implementation of the original MATLAB rule.
    size = len(params)
    probabilities = np.zeros((T, 3, size, 2))
    actions = np.zeros((T, 3, size, 4), dtype=int)
    final_q = np.zeros((3, size, 3, 2))
    totals = np.zeros((size, 3, 2), dtype=int)
    expected = np.zeros((size, 3, 2))
    for i in range(size):
        beta, alpha, lam, weight, sticky, response_sticky = params[i]
        for law in range(3):
            Q = [[0., 0.], [0., 0.], [0., 0.]]
            counts = [[0, 0], [0, 0]]
            M, R = [0, 0], [0, 0]
            P = p0[i].tolist()
            TM = [[.5, .5], [.5, .5]]
            for t in range(T):
                if t:
                    P = [[reflect_scalar(P[s][a]+float(increments[law, i, t-1, s, a])) for a in range(2)] for s in range(2)]
                left = int(uniforms[t, i, 4] < .5)
                current_R = R if left == 0 else R[::-1]
                maxima = [max(Q[1]), max(Q[2])]
                mb = [sum(TM[s][a]*maxima[s] for s in range(2)) for a in range(2)]
                mixed = [weight*mb[a]+(1-weight)*Q[0][a]+sticky*M[a]+response_sticky*current_R[a] for a in range(2)]
                pr1 = 1/(1+math.exp(beta*(mixed[0]-mixed[1])))
                pr2all = [1/(1+math.exp(beta*(Q[s+1][0]-Q[s+1][1]))) for s in range(2)]
                ep = [(1-pr2all[s])*P[s][0]+pr2all[s]*P[s][1] for s in range(2)]
                pstate0 = (1-pr1)*.7+pr1*.3
                expected[i, law, 0] += pstate0*ep[0]+(1-pstate0)*ep[1]
                a1 = int(uniforms[t, i, 0] < pr1)
                state = a1 if uniforms[t, i, 2] < .7 else 1-a1
                pr2 = pr2all[state]
                a2 = int(uniforms[t, i, 1] < pr2)
                win = int(uniforms[t, i, 3] < P[state][a2])
                M = [int(a1 == 0), int(a1 == 1)]
                R = [int(a1 == left), int(a1 != left)]
                pe1 = Q[state+1][a2]-Q[0][a1]
                pe2 = win-Q[state+1][a2]
                Q[0][a1] += alpha*pe1
                Q[state+1][a2] += alpha*pe2
                Q[0][a1] += lam*alpha*pe2
                counts[state][a1] += 1
                diagonal = counts[0][0]+counts[1][1]
                off = counts[0][1]+counts[1][0]
                diagonal_probability = .7 if diagonal > off else .3 if diagonal < off else .5
                TM = [[diagonal_probability, 1-diagonal_probability], [1-diagonal_probability, diagonal_probability]]
                pm = sum(sum(row) for row in P)/4
                expected[i, law, 1] += pm
                totals[i, law, 0] += win
                totals[i, law, 1] += int(uniforms[t, i, 3] < pm)
                probabilities[t, law, i] = [pr1, pr2]
                actions[t, law, i] = [a1, state, a2, win]
            final_q[law, i] = Q
    return {"probabilities": probabilities, "actions": actions, "q": final_q, "totals": totals, "expected": expected}


def sources():
    raw = (HERE / "PUBLIC_RECEIPTS.json").read_bytes()
    receipts = json.loads(raw)
    tree = json.loads(receipts["responses"][2]["structuredContent"]["content"])
    by_path = {x["path"]:x for x in tree["tree"]}
    checks = {}
    for operation, path in [(4, "utils/twostep_environment.py"), (5, "Online_evaluator.py"), (6, "models.py"), (7, "utils/twostep_support.py"), (8, "MLE.py")]:
        item = receipts["responses"][operation-1]["structuredContent"]
        data = item["content"].encode()
        git_blob = hashlib.sha1(b"blob "+str(len(data)).encode()+b"\0"+data).hexdigest()
        assert git_blob == by_path[path]["sha"], path
        checks[path] = {"bytes":len(data), "sha256":hashlib.sha256(data).hexdigest(), "git_blob":git_blob, "url":item["url"]}
    return {"tree_commit":tree["sha"], "files":checks, "receipts_bytes":len(raw)}


def checks():
    src = sources()
    x = np.linspace(-2, 3, 20001)
    reflection_error = float(np.max(np.abs(reflect(x)-np.array([reflect_scalar(float(z)) for z in x]))))
    assert reflection_error == 0
    params, p0, inc, u, mean = inputs(100000, 16)
    vector = simulate(params, p0, inc, u, record=True)
    reference = scalar_reference(params, p0, inc, u)
    errors = {key:float(np.max(np.abs(vector[key]-reference[key]))) for key in reference}
    assert errors["actions"] == errors["totals"] == 0
    assert max(errors.values()) < 1e-11, errors
    zero = simulate(params, p0, np.zeros_like(inc), u)
    for law in (1, 2):
        assert np.array_equal(zero["totals"][:, 0], zero["totals"][:, law])
        assert np.array_equal(zero["expected"][:, 0], zero["expected"][:, law])
    assert np.max(np.abs(zero["expected"][:, :, 1]-T*.5)) == 0
    assert np.max(np.abs(zero["uniform_condvar"]-T*.25)) == 0
    result = {"utc":stamp(), "sources":src, "reference_experiments":16, "all_laws":LAWS,
              "reference_scalar_max_errors":errors, "reflection_grid_max_error":reflection_error,
              "zero_drift_identical_all_laws":True, "uniform_zero_drift_exact_mean":T*.5,
              "uniform_zero_drift_exact_variance":T*.25, "numpy":np.__version__,
              "maxrss_bytes_darwin":resource.getrusage(resource.RUSAGE_SELF).ru_maxrss, "exit_code":0}
    write_json("REFERENCE_CHECKS.json", result)
    print(json.dumps(result, indent=2))


def freeze():
    assert (HERE / "REFERENCE_CHECKS.json").exists()
    result = {"utc":stamp(), "configuration":{"seed":SEED, "N":N, "forecast_N":N//2, "evaluation_N":N//2,
              "batch":BATCH, "T":T, "K":K, "sigma":SIGMA, "laws":LAWS},
              "files":{name:sha(HERE/name) for name in ["PROTOCOL.md", "forecast.py", "REFERENCE_CHECKS.json", "FIRST_CALCULATION.json", "PUBLIC_RECEIPTS.json"]},
              "main_run_started":False, "premain_revisions":0}
    write_json("FREEZE.json", result)
    print(json.dumps(result, indent=2))


def main():
    frozen = json.loads((HERE / "FREEZE.json").read_text())
    for name, value in frozen["files"].items():
        assert sha(HERE/name) == value, name
    assert not (HERE / "EXPERIMENTS.npz").exists(), "No automatic rerun/overwrite"
    started = stamp()
    start_time = time.monotonic()
    totals, expected, condvar, allparams, bankmeans = [], [], [], [], []
    for batch_id in range(N//BATCH):
        p, p0, inc, u, bankmean = inputs(batch_id)
        out = simulate(p, p0, inc, u)
        totals.append(out["totals"])
        expected.append(out["expected"])
        condvar.append(out["uniform_condvar"])
        allparams.append(p)
        bankmeans.append(bankmean)
        if (batch_id+1) % 16 == 0:
            print(json.dumps({"completed_experiments":(batch_id+1)*BATCH, "seconds":time.monotonic()-start_time}), flush=True)
    np.savez_compressed(HERE/"EXPERIMENTS.npz", totals=np.concatenate(totals), expected=np.concatenate(expected),
                        uniform_condvar=np.concatenate(condvar), params=np.concatenate(allparams), bank_mean=np.concatenate(bankmeans))
    result = {"started_utc":started, "finished_utc":stamp(), "seconds":time.monotonic()-start_time,
              "N":N, "filename":"EXPERIMENTS.npz", "bytes":(HERE/"EXPERIMENTS.npz").stat().st_size,
              "maxrss_bytes_darwin":resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
              "input_file_bytes":sum((HERE/name).stat().st_size for name in frozen["files"])+ (HERE/"FREEZE.json").stat().st_size,
              "output_sha256":sha(HERE/"EXPERIMENTS.npz"), "numerical_threads":1, "jobs_after_exit":0, "exit_code":0}
    write_json("MAIN_RUN.json", result)
    print(json.dumps(result, indent=2))


def estimate(v, influence=None):
    v = np.asarray(v)
    m = float(np.mean(v))
    centered = v-m if influence is None else influence
    se = float(np.std(centered, ddof=1)/math.sqrt(len(v)))
    return {"estimate":m, "MCSE":se, "MC99":[m-Z99*se, m+Z99*se]}


def sd_difference(a, b):
    va, vb = float(np.var(a)), float(np.var(b))
    sa, sb = math.sqrt(va), math.sqrt(vb)
    influence = ((a-np.mean(a))**2-va)/(2*sa) - ((b-np.mean(b))**2-vb)/(2*sb)
    se = float(np.std(influence, ddof=1)/math.sqrt(len(a)))
    point = sa-sb
    ratio = va/vb
    ratio_influence = ((a-np.mean(a))**2-va)/vb - va*((b-np.mean(b))**2-vb)/vb**2
    ratio_se = float(np.std(ratio_influence, ddof=1)/math.sqrt(len(a)))
    return {"sd_difference":{"estimate":point, "MCSE":se, "MC99":[point-Z99*se, point+Z99*se]},
            "variance_ratio":{"estimate":ratio, "MCSE":ratio_se, "MC99":[ratio-Z99*ratio_se, ratio+Z99*ratio_se]}}


def summarize():
    with np.load(HERE/"EXPERIMENTS.npz", allow_pickle=False) as f:
        totals, expected, condvar, bankmeans = f["totals"].astype(float), f["expected"], f["uniform_condvar"], f["bank_mean"]
    split = N//2
    results = {"utc":stamp(), "forecast_N":split, "evaluation_N":split, "learners":{}, "scope":"source-prior predictive simulation, not human validation"}
    for learner, label in enumerate(["hybrid_source_prior", "uniform_choice"]):
        forecast = totals[:split, :, learner]
        evaluation = totals[split:, :, learner]
        interval = np.quantile(forecast[:, 1], [.05, .95], method="inverted_cdf").astype(int)
        within = ((evaluation >= interval[0]) & (evaluation <= interval[1])).astype(float)
        entry = {"iid_90pct_integer_interval":interval.tolist(), "laws":{}}
        for law, lawname in enumerate(LAWS):
            entry["laws"][lawname] = {"mean_total":estimate(forecast[:, law]), "sd_total":float(np.std(forecast[:, law])),
                "variance_total":float(np.var(forecast[:, law])), "coverage_of_iid_interval":estimate(within[:, law]),
                "Rao_Blackwell_mean_total":estimate(expected[:split, law, learner])}
        entry["bank_minus_iid_mean"] = estimate(forecast[:, 0]-forecast[:, 1])
        entry["bank_minus_iid_RB_mean"] = estimate(expected[:split, 0, learner]-expected[:split, 1, learner])
        entry["bank_minus_iid_coverage"] = estimate(within[:, 0]-within[:, 1])
        entry["bank_minus_common_mean_coverage"] = estimate(within[:, 0]-within[:, 2])
        entry["bank_minus_common_mean_mean"] = estimate(forecast[:, 0]-forecast[:, 2])
        entry["bank_vs_iid_spread"] = sd_difference(forecast[:, 0], forecast[:, 1])
        entry["bank_vs_common_mean_spread"] = sd_difference(forecast[:, 0], forecast[:, 2])
        if learner == 1:
            entry["analytic_conditional_total_variance"] = {law:float(np.var(expected[:split, j, 1])+np.mean(condvar[:split, j])) for j, law in enumerate(LAWS)}
        results["learners"][label] = entry
    hyb = results["learners"]["hybrid_source_prior"]
    mean_interval = hyb["bank_minus_iid_mean"]["MC99"]
    cover_interval = hyb["bank_minus_iid_coverage"]["MC99"]
    results["practical_gate"] = {"mean_boundary_one_reward":1, "coverage_boundary_absolute":.05,
        "mean_change_resolved_below_boundary":max(abs(x) for x in mean_interval) < 1,
        "coverage_change_resolved_below_boundary":max(abs(x) for x in cover_interval) < .05}
    results["bank_mean"] = {"empirical_sd":float(np.std(bankmeans)), "known_sd":SIGMA/math.sqrt(K)}
    results["maxrss_bytes_darwin"] = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    results["explicit_npz_read_bytes"] = (HERE/"EXPERIMENTS.npz").stat().st_size
    results["npz_uncompressed_array_bytes_used"] = totals.nbytes+expected.nbytes+condvar.nbytes+bankmeans.nbytes
    results["exit_code"] = 0
    write_json("SUMMARY.json", results)
    print(json.dumps(results, indent=2))


if __name__ == "__main__":
    {"check":checks, "freeze":freeze, "main":main, "summarize":summarize}[sys.argv[1]]()
