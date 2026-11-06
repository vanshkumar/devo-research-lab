"""Independent 2x2 population calculation against the PCA simulation result."""
import csv
import json
import math
from pathlib import Path

import numpy as np

HERE=Path(__file__).resolve().parent


def prediction(v,rho):
    a,d,b=1.0625,v,rho*math.sqrt(v)
    lam=(a+d+math.sqrt((a-d)**2+4*b*b))/2
    if b==0:
        u0,u1=(1.,0.) if a>d else (0.,1.)
    else:
        norm=math.hypot(b,lam-a)
        u0,u1=b/norm,(lam-a)/norm
    cross=u0+u1*rho*math.sqrt(v)
    var_train=a*u0*u0+2*b*u0*u1+d*u1*u1
    beta=cross/var_train
    return {"nuisance_variance":v,"train_rho":rho,
            "population_pc_signal_alignment_sq":u0*u0,
            "population_matched_r2":cross*cross/var_train,
            "population_shifted_r2":2*beta*u0-beta*beta*(a*u0*u0+d*u1*u1)}


def main():
    data=list(csv.DictReader((HERE/"outputs/pilot_a.csv").open()))
    rows=[]
    for v in [.25,1.,4.,16.]:
        for rho in [0.,.8]:
            row=prediction(v,rho)
            selected=[r for r in data if r["method"]=="pca" and float(r["nuisance_variance"])==v and float(r["train_rho"])==rho]
            row["sample_median_matched_r2"]=float(np.median([float(r["matched_r2"]) for r in selected]))
            row["sample_median_shifted_r2"]=float(np.median([float(r["shifted_r2"]) for r in selected]))
            row["near_degenerate"]=v==1 and rho==0
            rows.append(row)
    result={"rows":rows,
            "max_abs_median_error_excluding_small_eigengap":max(abs(r["population_"+key]-r["sample_median_"+key]) for r in rows if not r["near_degenerate"] for key in ["matched_r2","shifted_r2"]),
            "source":"Closed-form eigenvalue of known 2x2 covariance, no eigensolver or learned Oja weight used."}
    (HERE/"outputs/analytical_check.json").write_text(json.dumps(result,indent=2))
    sensitivity=json.loads((HERE/"followup/summary.json").read_text())
    ode=[]
    for part in sensitivity["sensitivity"]:
        eta0,angle=part["eta0"],part["angle_deg"]
        for method in ["constant_oja","annealed_oja"]:
            total=4000*eta0 if method=="constant_oja" else sum(eta0/(1+t/1000) for t in range(20000,24000))
            # Unit-norm mean Oja flow in the top two axes; exactly orthogonal
            # starts stay orthogonal without stochastic seeding.
            expected=0. if angle==90 else 1/(1+math.tan(math.radians(angle))**2*math.exp(-2*3*total))
            observed=next(r["median_post_alignment_sq"] for r in part["summaries"] if r["environment"]=="switch" and r["method"]==method)
            ode.append({"eta0":eta0,"angle_deg":angle,"method":method,"sum_post_eta":total,
                        "mean_flow_alignment_sq_from_exact_old_pc":expected,"observed_median_alignment_sq":observed})
    (HERE/"followup/ode_check.json").write_text(json.dumps({"rows":ode,
        "limitation":"Mean-flow approximation with exact old principal axis, no stochastic seeding or finite-step jitter; not an exact stochastic theorem."},indent=2))
    print(json.dumps(result,indent=2))


if __name__=="__main__":
    main()
