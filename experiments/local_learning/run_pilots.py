"""Reproduce two bounded local-learning pilots. Outputs never include training arrays."""
import argparse
import csv
import json
import platform
import time
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent


def save_csv(path, rows):
    with path.open("w", newline="") as f:
        out = csv.DictWriter(f, fieldnames=list(rows[0]))
        out.writeheader()
        out.writerows(rows)


def rotated_data(rng, n, q, variance, rho):
    y = rng.normal(size=n)
    x = rng.normal(scale=0.1, size=(n, 8))
    x[:, 0] = y + 0.25 * rng.normal(size=n)
    x[:, 1] = np.sqrt(variance) * (rho * y + np.sqrt(1-rho*rho) * rng.normal(size=n))
    return np.einsum("nd,kd->nk", x, q), y


def r2(y, pred):
    return float(1 - np.mean((y-pred)**2) / np.var(y))


def scalar_pred(xcal, ycal, xtest, w):
    z = np.einsum("nd,d->n", xcal, w)
    # Training sample means are retained in the decoder.
    beta = float(np.dot(z-z.mean(), ycal-ycal.mean()) / np.dot(z-z.mean(), z-z.mean()))
    return ycal.mean() + beta * (np.einsum("nd,d->n", xtest, w) - z.mean())


def pilot_a(seeds, ntrain):
    rows = []
    for variance in [0.25, 1.0, 4.0, 16.0]:
        for rho in [0.0, 0.8]:
            streams, rotations, rngs, ws = [], [], [], []
            for seed in seeds:
                rng = np.random.default_rng(seed)
                q, _ = np.linalg.qr(rng.normal(size=(8, 8)))
                x, _ = rotated_data(rng, ntrain, q, variance, rho)
                w = rng.normal(size=8)
                w /= np.linalg.norm(w)
                streams.append(x)
                rotations.append(q)
                rngs.append(rng)
                ws.append(w)
            stream = np.stack(streams, axis=1)
            weights = np.stack(ws)
            eta = 0.01 / (1+variance)
            for x in stream:
                z = np.einsum("sd,sd->s", weights, x)
                weights += eta * z[:, None] * (x - z[:, None] * weights)
            for j, seed in enumerate(seeds):
                q, rng, w, xtrain = rotations[j], rngs[j], weights[j], streams[j]
                # Exact sample PCA and known population covariance are distinct checks.
                _, evec = np.linalg.eigh(np.cov(xtrain, rowvar=False))
                wpca = evec[:, -1]
                cov = np.eye(8) * .01
                cov[0, 0], cov[1, 1] = 1.0625, variance
                cov[0, 1] = cov[1, 0] = np.sqrt(variance) * rho
                _, popvec = np.linalg.eigh(np.einsum("ij,jk,lk->il", q, cov, q))
                xcal, ycal = rotated_data(rng, 4000, q, variance, rho)
                xmatch, ymatch = rotated_data(rng, 6000, q, variance, rho)
                xshift, yshift = rotated_data(rng, 6000, q, variance, 0.0)
                xfull = np.column_stack([xcal, np.ones(len(xcal))])
                beta = np.linalg.lstsq(xfull, ycal, rcond=None)[0]
                for method, axis in [("oja", w), ("pca", wpca), ("oracle_signal_axis", q[:, 0])]:
                    rows.append({"seed":seed,"nuisance_variance":variance,"train_rho":rho,"method":method,
                                 "matched_r2":r2(ymatch, scalar_pred(xcal,ycal,xmatch,axis)),
                                 "shifted_r2":r2(yshift, scalar_pred(xcal,ycal,xshift,axis)),
                                 "sample_pc_alignment_sq":float(np.dot(axis,wpca)**2/np.dot(axis,axis)),
                                 "population_pc_alignment_sq":float(np.dot(axis,popvec[:,-1])**2/np.dot(axis,axis)),
                                 "signal_alignment_sq":float(np.dot(axis,q[:,0])**2/np.dot(axis,axis)),
                                 "weight_norm":float(np.linalg.norm(axis))})
                rows.append({"seed":seed,"nuisance_variance":variance,"train_rho":rho,"method":"full_linear",
                             "matched_r2":r2(ymatch,np.einsum("nd,d->n",np.column_stack([xmatch,np.ones(len(xmatch))]),beta)),
                             "shifted_r2":r2(yshift,np.einsum("nd,d->n",np.column_stack([xshift,np.ones(len(xshift))]),beta)),
                             "sample_pc_alignment_sq":"", "population_pc_alignment_sq":"", "signal_alignment_sq":"", "weight_norm":""})
    return rows


def pilot_b(seeds, npre=20000, npost=4000, eta0=0.0025, angle_deg=90):
    rows, trajectories = [], []
    n = npre+npost
    raw = np.stack([np.random.default_rng(seed+440912).normal(size=(n,4)) for seed in seeds],axis=1)
    raw *= np.sqrt(np.array([4.,1.,.25,.25]))
    initial = np.stack([np.random.default_rng(seed+71000).normal(size=4) for seed in seeds])
    initial /= np.linalg.norm(initial,axis=1)[:,None]
    a = np.deg2rad(angle_deg)
    rot = np.array([[np.cos(a),-np.sin(a),0,0],[np.sin(a),np.cos(a),0,0],[0,0,1,0],[0,0,0,1]])
    for environment in ["stationary","switch"]:
        x = raw.copy()
        target = np.array([1.,0.,0.,0.])
        if environment == "switch":
            x[npre:] = np.einsum("nsd,kd->nsk",x[npre:],rot)
            target = rot[:,0]
        for method in ["constant_oja","annealed_oja","frozen_oja","projected_hebb"]:
            w = initial.copy()
            first = np.full(len(seeds), -1, dtype=int)
            pre_align = np.zeros(len(seeds))
            pre_norm = np.zeros(len(seeds))
            for t in range(n):
                eta = eta0 / (1+t/1000) if method == "annealed_oja" else eta0
                if method == "frozen_oja" and t >= npre:
                    eta = 0.
                z = np.einsum("sd,sd->s",w,x[t])
                if method == "projected_hebb":
                    w += eta*z[:,None]*x[t]
                    w /= np.linalg.norm(w,axis=1)[:,None]
                else:
                    w += eta*z[:,None]*(x[t]-z[:,None]*w)
                if t == npre-1:
                    pre_align = w[:,0]**2 / np.sum(w*w,axis=1)
                    pre_norm = np.linalg.norm(w,axis=1)
                align = np.einsum("sd,d->s",w,target)**2 / np.sum(w*w,axis=1)
                if t >= npre:
                    hit = (align >= .9) & (first < 0)
                    first[hit] = t-npre+1
                if (t+1) % 100 == 0:
                    for j,seed in enumerate(seeds):
                        trajectories.append({"seed":seed,"environment":environment,"method":method,"t":t+1,
                                             "current_pc_alignment_sq":float(np.dot(w[j],(target if t>=npre else np.array([1,0,0,0])))**2 / np.dot(w[j],w[j])),
                                             "weight_norm":float(np.linalg.norm(w[j])),"eta":eta})
            align = np.einsum("sd,d->s",w,target)**2 / np.sum(w*w,axis=1)
            for j,seed in enumerate(seeds):
                rows.append({"seed":seed,"environment":environment,"method":method,"eta0":eta0,"angle_deg":angle_deg,
                             "pre_alignment_sq":float(pre_align[j]),"pre_norm":float(pre_norm[j]),
                             "post_alignment_sq":float(align[j]),"post_norm":float(np.linalg.norm(w[j])),
                             "first_post_alignment_0p9":int(first[j]),"post_horizon":npost})
    return rows, trajectories


def summarize_a(rows):
    result = []
    for v in [.25,1.,4.,16.]:
        for rho in [0.,.8]:
            for method in ["oja","pca","oracle_signal_axis","full_linear"]:
                selected = [r for r in rows if r["nuisance_variance"]==v and r["train_rho"]==rho and r["method"]==method]
                result.append({"v":v,"rho":rho,"method":method,"n":len(selected),
                               "median_matched_r2":float(np.median([r["matched_r2"] for r in selected])),
                               "median_shifted_r2":float(np.median([r["shifted_r2"] for r in selected])),
                               "min_population_pc_alignment_sq":min([r["population_pc_alignment_sq"] for r in selected if r["population_pc_alignment_sq"]!=""],default=None)})
    return result


def summarize_b(rows):
    result=[]
    for env in ["stationary","switch"]:
        for method in ["constant_oja","annealed_oja","frozen_oja","projected_hebb"]:
            selected=[r for r in rows if r["environment"]==env and r["method"]==method]
            hits=[r["first_post_alignment_0p9"] for r in selected if r["first_post_alignment_0p9"]>=0]
            result.append({"environment":env,"method":method,"n":len(selected),"reached_0p9":len(hits),
                           "median_post_alignment_sq":float(np.median([r["post_alignment_sq"] for r in selected])),
                           "median_pre_alignment_sq":float(np.median([r["pre_alignment_sq"] for r in selected])),
                           "median_hit_time_if_reached":float(np.median(hits)) if hits else None,
                           "median_post_norm":float(np.median([r["post_norm"] for r in selected]))})
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--minimal",action="store_true")
    parser.add_argument("--followup",action="store_true")
    args=parser.parse_args()
    start=time.time()
    out=HERE/("minimal" if args.minimal else "followup" if args.followup else "outputs")
    out.mkdir(exist_ok=True)
    seeds=list(range(1)) if args.minimal else list(range(20))
    if args.followup:
        rows=[]
        # Frozen in FOLLOWUP_PLAN.md, never tuned on these holdout seeds.
        for eta0 in [.001,.0025,.005]:
            for angle in [30,60,90]:
                part,_=pilot_b(list(range(100,120)),eta0=eta0,angle_deg=angle)
                rows.extend(part)
        save_csv(out/"pilot_b_sensitivity.csv",rows)
        summary={"sensitivity":[]}
        for eta0 in [.001,.0025,.005]:
            for angle in [30,60,90]:
                part=[r for r in rows if r["eta0"]==eta0 and r["angle_deg"]==angle]
                summary["sensitivity"].append({"eta0":eta0,"angle_deg":angle,"summaries":summarize_b(part)})
    else:
        rows_a=pilot_a(seeds,20000)
        save_csv(out/"pilot_a.csv",rows_a)
        rows_b,trajectories=pilot_b(seeds)
        save_csv(out/"pilot_b.csv",rows_b)
        save_csv(out/"pilot_b_trajectories.csv",trajectories)
        summary={"pilot_a":summarize_a(rows_a),"pilot_b":summarize_b(rows_b)}
    summary["provenance"]={"python":platform.python_version(),"numpy":np.__version__,"wall_seconds":time.time()-start,
                           "seeds":seeds if not args.followup else list(range(100,120)),"data":"synthetic Gaussian, generated by this script"}
    (out/"summary.json").write_text(json.dumps(summary,indent=2))
    print(json.dumps(summary,indent=2))


if __name__=="__main__":
    main()
