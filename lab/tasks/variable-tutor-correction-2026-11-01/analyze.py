"""Frozen whole-task finite-generator summaries and inference."""
import os
for key in ("OPENBLAS_NUM_THREADS","OMP_NUM_THREADS","MKL_NUM_THREADS","VECLIB_MAXIMUM_THREADS","NUMEXPR_NUM_THREADS"):
    os.environ[key]="1"
import argparse
import json
import math
from pathlib import Path
import resource
import sys
import numpy as np
import run

ROOT=Path(__file__).resolve().parent

def wilson(k,n,z=1.959963984540054):
    p=k/n;den=1+z*z/n
    center=(p+z*z/(2*n))/den
    half=z*math.sqrt(p*(1-p)/n+z*z/(4*n*n))/den
    return [max(0.,center-half),min(1.,center+half)]

def exact_upper(k,n,alpha=.05):
    if k==n:
        return 1.
    lo,hi=0.,1.
    for _ in range(100):
        p=(lo+hi)/2
        cdf=sum(math.comb(n,j)*p**j*(1-p)**(n-j) for j in range(k+1))
        if cdf>alpha:
            lo=p
        else:
            hi=p
    return hi

def vector(score,n,method,key="acquired"):
    rows=sorted([r for r in score["records"] if r["n"]==n and r["method"]==method],key=lambda r:r["seed"])
    return np.asarray([r[key] for r in rows],dtype=float)

def paired(a,b):
    delta=np.asarray(a)-np.asarray(b)
    rng=np.random.default_rng(50091)
    indices=rng.integers(0,len(delta),size=(10000,len(delta)))
    means=delta[indices].mean(axis=1)
    return dict(point=float(delta.mean()),interval95=np.quantile(means,[.025,.975]).tolist(),
                units=len(delta),bootstrap_replicates=10000,bootstrap_seed=50091)

def summarize(score):
    out={}
    for n in score["budgets"]:
        out[str(n)]={}
        for method in run.METHODS:
            acquired=vector(score,n,method)
            error=vector(score,n,method,"final_true_error")
            removal=vector(score,n,method,"removal")
            k=int(acquired.sum());count=len(acquired)
            out[str(n)][method]=dict(acquired=k,count=count,rate=k/count,wilson95=wilson(k,count),
                mean_error=float(error.mean()),median_error=float(np.median(error)),
                mean_removal=float(removal.mean()),minimum_removal=float(removal.min()))
    return out

if __name__=="__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("--reproduce",action="store_true")
    args=parser.parse_args()
    base=ROOT/"reproduction" if args.reproduce else ROOT
    labels=["main","contrary_decoupled","contrary_noiseless","contrary_resolution"]
    scores={label:json.loads((base/label/"SCORES.json").read_text()) for label in labels}
    tables={label:summarize(score) for label,score in scores.items()}
    main=scores["main"]
    exposure=paired(vector(main,32,"gaussian"),vector(main,3,"gaussian"))
    ball=vector(main,32,"ball");gaussian=vector(main,32,"gaussian")
    superiority=paired(ball,gaussian)
    wins=int(np.sum((ball==1)&(gaussian==0)));losses=int(np.sum((ball==0)&(gaussian==1)))
    upper=exact_upper(wins,len(ball))
    controls=dict(oracle=tables["main"]["32"]["truth"]["rate"]>=.95,
                  absent=tables["main"]["32"]["absent"]["rate"]<=.10,
                  shuffled=tables["main"]["32"]["shuffled"]["rate"]<=.10)
    useful=(tables["main"]["32"]["gaussian"]["rate"]>=.80 and
            tables["main"]["32"]["gaussian"]["wilson95"][0]>=.80 and
            exposure["point"]>=.15 and exposure["interval95"][0]>0 and all(controls.values()))
    gain=superiority["point"]>=.10 and superiority["interval95"][0]>0 and all(controls.values())
    paired_tests=dict(gaussian_exposure32_minus3=exposure,ball_minus_gaussian32=superiority,
        ball_wins=wins,ball_losses=losses,one_sided95_upper_ball_win_probability=upper,
        excludes_10pp_ball_advantage_within_generator=bool(upper<.10),
        decoupling_mean_absolute_error_improvement=paired(vector(main,32,"mean","final_true_error"),
            vector(scores["contrary_decoupled"],32,"mean","final_true_error")),
        noiseless_gaussian3_rate_improvement=paired(vector(scores["contrary_noiseless"],3,"gaussian"),vector(main,3,"gaussian")),
        resolution_gaussian32_rate_change=paired(vector(scores["contrary_resolution"],32,"gaussian"),vector(main,32,"gaussian")))
    audit=json.loads((base/"AUDIT.json").read_text())
    asym=audit["matching"]["asymptotic_mean"]
    limits=dict(mean_infinite_tutors_median_error=float(np.median([r["mean_infinite_tutors_true_error"] for r in asym])),
        mean_infinite_tutors_mean_error=float(np.mean([r["mean_infinite_tutors_true_error"] for r in asym])),
        unconstrained_formula_interior_cases=sum(r["interior"] for r in asym))
    rss=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    output=dict(finished_at=run.stamp(),units=64,unit="whole independently generated task; conditions are paired repeats",
        tables=tables,paired=paired_tests,controls=controls,
        primary1_useful_simple_correction_and_exposure=bool(useful),primary2_disk_investment_gain=bool(gain),
        asymptotic_mean_limit=limits,peak_rss_bytes=int(rss if sys.platform=="darwin" else rss*1024),
        caution="Conditional generator inference. No population equivalence from zero bootstrap width, biological calibration, neural mechanism or novelty. No independent review yet.")
    target=base/"ANALYSIS.json"
    if target.exists():
        raise SystemExit("Refusing to overwrite analysis")
    run.write_json(target,output)
    print(json.dumps(dict(finished_at=output["finished_at"],main_rates={n:{m:f'{r["acquired"]}/{r["count"]}' for m,r in methods.items()} for n,methods in tables["main"].items()},
        paired=paired_tests,controls=controls,primary1=bool(useful),primary2=bool(gain),asymptotic_mean_limit=limits,peak_rss_bytes=output["peak_rss_bytes"]),indent=2))
