"""Author numerical audit; independent science review still required."""
import os
for key in ("OPENBLAS_NUM_THREADS","OMP_NUM_THREADS","MKL_NUM_THREADS","VECLIB_MAXIMUM_THREADS","NUMEXPR_NUM_THREADS"):
    os.environ[key]="1"
import argparse
import hashlib
import itertools
import json
from pathlib import Path
import resource
import sys
import time
import numpy as np
import run

ROOT=Path(__file__).resolve().parent

def true_reference(case, x):
    delta=x-case["mu"]
    # Independent projector form, distinct from the generator's residual subtraction.
    projection=np.eye(6)-np.einsum("ik,jk->ij",case["u"],case["u"])
    perpendicular=np.einsum("...i,ij,...j->...",delta,projection,delta)
    latent=np.einsum("...i,ij->...j",delta,case["u"])
    radial=np.maximum(np.linalg.norm(latent,axis=-1)-2.,0.)**2
    return (np.maximum(perpendicular,0.)+radial)/4

def box_optimum(a_matrix, offset, center, weight, denominator):
    h=np.einsum("ij,ik,kl->jl",a_matrix,weight,a_matrix)
    rhs=np.einsum("ij,ik,k->j",a_matrix,weight,center-offset)
    best=(float("inf"),None)
    for statuses in itertools.product((-1,0,1),repeat=4):
        a=np.asarray(statuses,dtype=float)
        free=np.flatnonzero(a==0.)
        active=np.flatnonzero(a!=0.)
        if len(free):
            r=rhs[free].copy()
            if len(active):
                r-=np.einsum("ij,j->i",h[np.ix_(free,active)],a[active])
            try:
                a[free]=np.linalg.solve(h[np.ix_(free,free)],r)
            except np.linalg.LinAlgError:
                continue
            if np.any(np.abs(a[free])>1.+1e-10):
                continue
        delta=offset+np.einsum("ij,j->i",a_matrix,a)-center
        cost=float(np.einsum("i,ij,j->",delta,weight,delta)/denominator)
        if cost<best[0]:
            best=(cost,a.copy())
    if best[1] is None:
        raise AssertionError("No finite box optimum")
    return best

def weights(y,sigma):
    center=np.sum(y,axis=0)/len(y)
    differences=y-center
    s=np.einsum("ni,nj->ij",differences,differences)/(len(y)-1)
    eig,vec=np.linalg.eigh(s)
    nuisance=vec[:,-2:]
    tangent=np.eye(6)-np.einsum("ik,jk->ij",nuisance,nuisance)
    noise=max(sigma*sigma,1e-8)
    variances=np.full(6,noise)
    variances[-2:]=np.maximum(eig[-2:],noise)
    gaussian=np.einsum("ij,j,kj->ik",vec,1/variances,vec)
    gaussian*=6/np.trace(gaussian)
    return center,{"mean":(np.eye(6),6),"gaussian":(gaussian,6),"tangent":(tangent,4)}

def audit_label(label,base):
    directory=base/label
    scores=json.loads((directory/"SCORES.json").read_text())
    observations=np.load(directory/"observations.npz",allow_pickle=False)
    predictions=np.load(directory/"predictions.npz",allow_pickle=False)
    action,feedback,path=predictions["actions"],predictions["feedback"],predictions["paths"]
    max_feedback=max_gold=max_path=0.
    optima=[]
    for index,row in enumerate(scores["records"]):
        seed,n,method=row["seed"],row["n"],row["method"]
        case={name:observations[f"s{seed}_{name}"] for name in ("mu","u","plant","offset","goal","zstar","tutors")}
        case["radius"]=2.
        y=case["tutors"][:n]
        if method=="shuffled":
            key=f"s{seed}_shuffled_tutors"
            if key in observations:
                y=observations[key][:n]
            else:
                y=run.make_case(seed+1000000,sigma=scores["sigma"])["tutors"][:n]
        model=run.fit(y,scores["sigma"])
        x=case["offset"]+np.einsum("ni,ji->nj",action[index],case["plant"])
        reconstructed=run.evaluate(method,model,case,x)
        if scores.get("resolution",0.):
            reconstructed=np.round(reconstructed/scores["resolution"])*scores["resolution"]
        max_feedback=max(max_feedback,float(np.max(np.abs(reconstructed-feedback[index]))))
        endpoint=case["offset"]+np.einsum("ij,j->i",case["plant"],path[index,-1])
        gold=float(true_reference(case,endpoint))
        max_gold=max(max_gold,abs(gold-row["final_true_error"]))
        current=float(feedback[index,0]); a=action[index,0].copy(); step=.5
        directions=np.concatenate([np.eye(4),-np.eye(4)])
        for iteration in range(scores["rounds"]):
            begin=1+8*iteration
            expect=np.clip(a+step*directions,-1,1)
            max_path=max(max_path,float(np.max(np.abs(expect-action[index,begin:begin+8]))))
            candidate=feedback[index,begin:begin+8]
            best=int(np.argmin(candidate))
            if candidate[best]<current-1e-12:
                a=action[index,begin+best].copy(); current=float(candidate[best])
            else:
                step*=.5
            max_path=max(max_path,float(np.max(np.abs(a-path[index,iteration+1]))))
        if method in ("mean","gaussian","tangent") and not scores.get("resolution",0.):
            center,ws=weights(case["tutors"][:n],scores["sigma"])
            weight,denom=ws[method]
            optimum,opt_action=box_optimum(case["plant"],case["offset"],center,weight,denom)
            residual=endpoint-center
            actor_cost=float(np.einsum("i,ij,j->",residual,weight,residual)/denom)
            opt_x=case["offset"]+np.einsum("ij,j->i",case["plant"],opt_action)
            optima.append(dict(seed=seed,n=n,method=method,actor_cost=actor_cost,optimum_cost=optimum,
                objective_gap=actor_cost-optimum,optimum_action=opt_action.tolist(),
                optimum_true_error=float(true_reference(case,opt_x)),actor_true_error=row["final_true_error"]))
    assert max_feedback<1e-9,(label,max_feedback)
    assert max_gold<1e-9,(label,max_gold)
    assert max_path<1e-12,(label,max_path)
    pin=hashlib.sha256((directory/"predictions.npz").read_bytes()).hexdigest()
    assert pin==scores["prediction_sha256"]
    result=dict(label=label,records=len(scores["records"]),query_costs=feedback.size,
                maximum_feedback_error=max_feedback,maximum_gold_error=max_gold,maximum_path_error=max_path,
                predictions_pin_pass=True,optima=optima,
                maximum_quadratic_actor_gap=max([r["objective_gap"] for r in optima] or [0.]),
                minimum_quadratic_actor_gap=min([r["objective_gap"] for r in optima] or [0.]))
    observations.close();predictions.close()
    return result

def matching_checks(base,development):
    prefix="development" if development else "main"
    dec="development_decoupled_matched" if development else "contrary_decoupled"
    clean="development_noiseless_matched" if development else "contrary_noiseless"
    primary=np.load(base/prefix/"observations.npz",allow_pickle=False)
    decoupled=np.load(base/dec/"observations.npz",allow_pickle=False)
    noiseless=np.load(base/clean/"observations.npz",allow_pickle=False)
    seeds=range(1200,1212) if development else range(2000,2064)
    exact_checks=0; maximum_noise_residual=0.;identity_error=0.;asymptotic=[]
    for seed in seeds:
        for key in ("mu","u","goal","latent","noise","tutors","zstar"):
            name=f"s{seed}_{key}"
            assert np.array_equal(primary[name],decoupled[name]),(seed,key,"decoupled")
            exact_checks+=1
        for key in ("mu","u","goal","latent","noise","zstar","plant","offset"):
            name=f"s{seed}_{key}"
            assert np.array_equal(primary[name],noiseless[name]),(seed,key,"noiseless")
            exact_checks+=1
        residual=primary[f"s{seed}_tutors"]-noiseless[f"s{seed}_tutors"]-.08*primary[f"s{seed}_noise"]
        maximum_noise_residual=max(maximum_noise_residual,float(np.max(np.abs(residual))))
        case={key:primary[f"s{seed}_{key}"] for key in ("mu","u","goal","zstar","plant","offset")}
        p=np.eye(6)-np.einsum("ik,jk->ij",case["u"],case["u"])
        gram=np.einsum("ij,ik,kl->jl",case["plant"],p,case["plant"])
        identity_error=max(identity_error,float(np.max(np.abs(gram-np.eye(4)))))
        optimum,a=box_optimum(case["plant"],case["offset"],case["mu"],np.eye(6),6)
        x=case["offset"]+np.einsum("ij,j->i",case["plant"],a)
        c=np.einsum("ji,jk->ik",case["u"],case["plant"])
        delta=-np.linalg.solve(np.eye(4)+np.einsum("ij,ik->jk",c,c),np.einsum("ij,i->j",c,case["zstar"]))
        unconstrained=case["goal"]+delta
        interior=bool(np.all(np.abs(unconstrained)<=1.))
        asymptotic.append(dict(seed=seed,mean_infinite_tutors_true_error=float(true_reference(case,x)),
            box_action=a.tolist(),unconstrained_action=unconstrained.tolist(),interior=interior,
            formula_action_error=float(np.max(np.abs(a-unconstrained))) if interior else None,
            predicted_interior_error=float(np.dot(delta,delta)/4)))
    assert maximum_noise_residual<1e-12
    assert identity_error<1e-12
    for item in asymptotic:
        if item["interior"]:
            assert item["formula_action_error"]<1e-10
            assert abs(item["mean_infinite_tutors_true_error"]-item["predicted_interior_error"])<1e-10
    primary.close();decoupled.close();noiseless.close()
    return dict(exact_matched_arrays=exact_checks,maximum_noise_residual=maximum_noise_residual,
        maximum_motor_content_gram_error=identity_error,asymptotic_mean=asymptotic)

if __name__=="__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("--development",action="store_true")
    parser.add_argument("--reproduce",action="store_true")
    args=parser.parse_args()
    base=ROOT/"reproduction" if args.reproduce else ROOT
    labels=(["development","development_decoupled_matched","development_noiseless_matched"] if args.development else
            ["main","contrary_decoupled","contrary_noiseless","contrary_resolution"])
    audits=[audit_label(label,base) for label in labels]
    match=matching_checks(base,args.development)
    rss=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    output=dict(finished_at=run.stamp(),author_check_only=True,audits=audits,matching=match,
                peak_rss_bytes=int(rss if sys.platform=="darwin" else rss*1024))
    dest=base/("DEVELOPMENT_AUDIT.json" if args.development else "AUDIT.json")
    if dest.exists():
        raise SystemExit("Refusing to overwrite audit")
    run.write_json(dest,output)
    print(json.dumps(dict(finished_at=output["finished_at"],labels=[{key:a[key] for key in ("label","records","query_costs","maximum_feedback_error","maximum_gold_error","maximum_path_error","maximum_quadratic_actor_gap")} for a in audits],
            matching_arrays=match["exact_matched_arrays"],peak_rss_bytes=output["peak_rss_bytes"]),indent=2))
