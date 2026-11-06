"""Small aligned-feature, finite-support teaching experiment. Python3 + NumPy."""
import os
for _key in ("OPENBLAS_NUM_THREADS", "OMP_NUM_THREADS", "MKL_NUM_THREADS", "VECLIB_MAXIMUM_THREADS", "NUMEXPR_NUM_THREADS"):
    os.environ[_key] = "1"
import argparse
import hashlib
import json
import platform
import resource
import sys
import time
from pathlib import Path
import numpy as np

ROOT = Path(__file__).resolve().parent
OUTPUT_ROOT = ROOT
D, RANK, K = 6, 2, 4
METHODS = ["first", "mean", "gaussian", "tangent", "ball", "hull", "nearest", "absent", "shuffled", "truth"]

def stamp():
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

def write_json(path, value):
    path.write_text(json.dumps(value, indent=2, allow_nan=False) + "\n")

def dot(a, b):
    return np.einsum("...i,i->...", a, b)

def mm(a, b):
    return np.einsum("...i,ij->...j", a, b)

def square(x):
    return np.einsum("...i,...i->...", x, x)

def make_case(seed, nmax=128, sigma=.08, radius=2., feasible_fraction=.85, coupled=True):
    # Fixed draw length keeps nested tutor prefixes invariant across conditions.
    # nmax controls accessible prefixes in experiment(), never RNG scheduling.
    nmax = 128
    rng = np.random.default_rng(seed)
    basis, _ = np.linalg.qr(rng.normal(size=(D, D)))
    u, v = basis[:, :RANK], basis[:, RANK:]
    q, _ = np.linalg.qr(rng.normal(size=(K, K)))
    c = rng.normal(size=(RANK, K)) * .8
    plant = np.einsum("ij,jk->ik", v, q)
    if coupled:
        plant += np.einsum("ij,jk->ik", u, c)
    mu = rng.normal(size=D)
    goal = rng.uniform(-.6, .6, size=K)
    direction = rng.normal(size=RANK)
    direction /= np.sqrt(square(direction))
    zstar = direction * feasible_fraction * radius
    offset = mu + mm(zstar, u.T) - mm(goal, plant.T)
    theta = rng.uniform(0, 2*np.pi, nmax)
    radii = radius * np.sqrt(rng.uniform(size=nmax))
    latent = np.stack([np.cos(theta)*radii, np.sin(theta)*radii], axis=1)
    noise = rng.normal(size=(nmax, D))
    tutors = mu + mm(latent, u.T) + sigma * noise
    return dict(seed=seed, mu=mu, u=u, plant=plant, offset=offset, goal=goal,
                zstar=zstar, latent=latent, noise=noise, tutors=tutors,
                sigma=sigma, radius=radius, coupled=coupled, coupling=c, complement=v, motor_rotation=q)

def true_error(case, x):
    d = x - case["mu"]
    z = mm(d, case["u"])
    residual = d - mm(z, case["u"].T)
    excess = np.maximum(np.sqrt(square(z)) - case["radius"], 0.)
    return (square(residual) + excess**2)/(D-RANK)

def convex_hull(points):
    unique = sorted(set(map(tuple, points.tolist())))
    if len(unique) < 3:
        return np.asarray(unique)
    def cross(o, a, b):
        return (a[0]-o[0])*(b[1]-o[1]) - (a[1]-o[1])*(b[0]-o[0])
    lower, upper = [], []
    for p in unique:
        while len(lower)>1 and cross(lower[-2], lower[-1], p)<=0:
            lower.pop()
        lower.append(p)
    for p in reversed(unique):
        while len(upper)>1 and cross(upper[-2], upper[-1], p)<=0:
            upper.pop()
        upper.append(p)
    return np.asarray(lower[:-1] + upper[:-1])

def fit(tutors, sigma):
    mean = tutors.mean(axis=0)
    centered = tutors-mean
    cov = np.einsum("ni,nj->ij", centered, centered)/(len(tutors)-1)
    lam, vectors = np.linalg.eigh(cov)
    idx = np.argsort(lam)[::-1]
    lam, vectors = lam[idx], vectors[:, idx]
    u = vectors[:, :RANK]
    radius = np.sqrt(max((RANK+2)/RANK * (lam[:RANK].sum()-RANK*sigma**2), 0.))
    effective = np.full(D, max(sigma**2, 1e-8))
    effective[:RANK] = np.maximum(lam[:RANK], effective[:RANK])
    precision = np.einsum("ij,j,kj->ik", vectors, 1/effective, vectors)
    precision *= D/np.trace(precision)
    hull = convex_hull(mm(centered, u))
    return dict(mean=mean, u=u, radius=radius, precision=precision,
                hull=hull, tutors=tutors, eigenvalues=lam)

def polygon_distance(z, hull):
    start, end = hull, np.roll(hull, -1, axis=0)
    edges = end-start
    diff = z[:, None, :] - start[None, :, :]
    cross = edges[None, :, 0]*diff[:, :, 1] - edges[None, :, 1]*diff[:, :, 0]
    inside = np.all(cross >= -1e-12, axis=1)
    denom = np.maximum(square(edges), 1e-30)
    alpha = np.clip(np.einsum("nhi,hi->nh", diff, edges)/denom, 0., 1.)
    dist = np.min(square(diff-alpha[:, :, None]*edges[None, :, :]), axis=1)
    return np.where(inside, 0., dist)

def evaluate(method, model, case, x):
    if method == "truth":
        return true_error(case, x)
    if method == "absent":
        return np.zeros(len(x))
    if method == "first":
        return square(x-model["tutors"][0])/D
    if method == "mean":
        return square(x-model["mean"])/D
    if method == "nearest":
        return np.min(square(x[:, None, :]-model["tutors"][None, :, :]), axis=1)/D
    d = x-model["mean"]
    if method == "gaussian":
        return np.einsum("ni,ij,nj->n", d, model["precision"], d)/D
    z = mm(d, model["u"])
    residual = d-mm(z, model["u"].T)
    loss = square(residual)
    if method in ("ball", "shuffled"):
        loss += np.maximum(np.sqrt(square(z))-model["radius"], 0.)**2
    elif method == "hull":
        loss += polygon_distance(z, model["hull"])
    return loss/(D-RANK)

def actor(case, model, method, rounds=80, resolution=0.):
    a = np.zeros(K)
    step = .5
    directions = np.concatenate([np.eye(K), -np.eye(K)])
    def query(actions):
        x = case["offset"] + mm(actions, case["plant"].T)
        cost = evaluate(method, model, case, x)
        if resolution:
            cost = np.round(cost/resolution)*resolution
        return cost
    current = float(query(a[None, :])[0])
    actions, costs = [a.copy()], [current]
    path = [a.copy()]
    for _ in range(rounds):
        candidates = np.clip(a[None, :] + step*directions, -1., 1.)
        feedback = query(candidates)
        actions.extend(candidates.copy())
        costs.extend(feedback.tolist())
        best = int(np.argmin(feedback))
        if feedback[best] < current - 1e-12:
            a, current = candidates[best].copy(), float(feedback[best])
        else:
            step *= .5
        path.append(a.copy())
    return np.asarray(actions), np.asarray(costs), np.asarray(path)

def case_arrays(case):
    return {key: value for key,value in case.items() if isinstance(value,np.ndarray)}

def experiment(label, seeds, budgets, sigma=.08, radius=2., rounds=80, resolution=0., coupled=True):
    started = stamp()
    outputs = OUTPUT_ROOT/label
    if (outputs/"SCORES.json").exists():
        raise SystemExit("Refusing to overwrite saved experiment: "+str(outputs))
    outputs.mkdir(exist_ok=True)
    all_actions, all_feedback, all_paths, records, observations = [], [], [], [], {}
    for seed in seeds:
        case = make_case(seed, max(budgets), sigma, radius, coupled=coupled)
        for key,value in case_arrays(case).items():
            observations[f"s{seed}_{key}"] = value
        wrong = make_case(seed+1000000, max(budgets), sigma, radius, coupled=coupled)
        for key,value in case_arrays(wrong).items():
            observations[f"s{seed}_shuffled_{key}"] = value
        for n in budgets:
            model = fit(case["tutors"][:n], sigma)
            shuffled = fit(wrong["tutors"][:n], sigma)
            observations[f"s{seed}_n{n}_eigenvalues"] = model["eigenvalues"]
            observations[f"s{seed}_n{n}_estimated_u"] = model["u"]
            observations[f"s{seed}_n{n}_estimated_radius"] = np.asarray(model["radius"])
            for method in METHODS:
                actions, feedback, path = actor(case, shuffled if method=="shuffled" else model, method, rounds, resolution)
                all_actions.append(actions)
                all_feedback.append(feedback)
                all_paths.append(path)
                records.append(dict(seed=seed, n=n, method=method, resolution=resolution))
    # Save predictions and observations BEFORE any non-oracle endpoint gold scoring.
    np.savez_compressed(outputs/"observations.npz", **observations)
    np.savez_compressed(outputs/"predictions.npz", actions=np.asarray(all_actions), feedback=np.asarray(all_feedback), paths=np.asarray(all_paths))
    write_json(outputs/"PREDICTION_INDEX.json", dict(saved_at=stamp(), records=records))
    predictions_pin = hashlib.sha256((outputs/"predictions.npz").read_bytes()).hexdigest()
    for index, rec in enumerate(records):
        case = make_case(rec["seed"], max(budgets), sigma, radius, coupled=coupled)
        end = case["offset"] + mm(all_paths[index][-1], case["plant"].T)
        initial = float(true_error(case, case["offset"][None, :])[0])
        final = float(true_error(case, end[None, :])[0])
        rec.update(initial_true_error=initial, final_true_error=final,
                   removal=1-final/initial, acquired=bool(final <= .05*initial),
                   endpoint_action=all_paths[index][-1].tolist())
    summary = {}
    for n in budgets:
        summary[str(n)] = {}
        for method in METHODS:
            rows = [r for r in records if r["n"]==n and r["method"]==method]
            summary[str(n)][method] = dict(count=len(rows), acquired=sum(r["acquired"] for r in rows),
                mean_removal=float(np.mean([r["removal"] for r in rows])),
                median_final_error=float(np.median([r["final_true_error"] for r in rows])))
    rss = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    peak_bytes = int(rss if sys.platform=="darwin" else rss*1024)
    result = dict(label=label, started_at=started, finished_at=stamp(), seeds=list(seeds), budgets=budgets,
                  sigma=sigma, radius=radius, coupled=coupled, resolution=resolution,
                  rounds=rounds, queries=1+2*K*rounds,
                  prediction_sha256=predictions_pin, prediction_before_gold=True,
                  summary=summary, records=records, peak_rss_bytes=peak_bytes,
                  python=sys.version, numpy=np.__version__, platform=platform.platform(),
                  numerical_threads={key:os.environ.get(key) for key in ("OPENBLAS_NUM_THREADS","OMP_NUM_THREADS","VECLIB_MAXIMUM_THREADS")})
    write_json(outputs/"SCORES.json", result)
    if label=="first":
        sample = make_case(list(seeds)[0], max(budgets), sigma, radius)
        write_json(OUTPUT_ROOT/"FIRST_CALCULATION.json", dict(result=result, first_case={k:(v.tolist() if isinstance(v,np.ndarray) else v) for k,v in sample.items()},
            provenance="New synthetic observations; three whole independent development tasks. All10methods use actual641scalar queries; generated feedback/actions saved before gold scoring. Peak is this measured process only; search-provider peak/transfer unknown."))
    print(json.dumps(dict(label=label, started_at=started, finished_at=result["finished_at"], summary=summary, peak_rss_bytes=peak_bytes), indent=2))

if __name__=="__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("mode", choices=["first","dev","dev-contrary","main"])
    parser.add_argument("--reproduce", action="store_true")
    args=parser.parse_args()
    if args.reproduce:
        OUTPUT_ROOT = ROOT/"reproduction"
        OUTPUT_ROOT.mkdir(exist_ok=True)
    if args.mode=="first":
        experiment("first", range(1100,1103), [16])
    elif args.mode=="dev":
        experiment("development", range(1200,1212), [3,8,32,128])
    elif args.mode=="dev-contrary":
        experiment("development_decoupled_matched", range(1200,1212), [32], coupled=False)
        experiment("development_noiseless_matched", range(1200,1212), [3,32], sigma=0.)
    else:
        freeze = json.loads((ROOT/"FREEZE.json").read_text())
        for name,pin in freeze["sha256"].items():
            if hashlib.sha256((ROOT/name).read_bytes()).hexdigest()!=pin:
                raise SystemExit("Frozen artifact changed: "+name)
        experiment("main", range(2000,2064), [3,8,32,128])
        experiment("contrary_decoupled", range(2000,2064), [32], coupled=False)
        experiment("contrary_noiseless", range(2000,2064), [3,32], sigma=0.)
        experiment("contrary_resolution", range(2000,2064), [32], resolution=.001)
