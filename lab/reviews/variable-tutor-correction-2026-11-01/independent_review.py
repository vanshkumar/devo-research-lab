"""Protocol-based independent reconstruction and prespecified changed-plant test.

No author Python module is imported or called. One scientific process/thread.
"""
import os
for key in ("OPENBLAS_NUM_THREADS", "OMP_NUM_THREADS", "MKL_NUM_THREADS", "VECLIB_MAXIMUM_THREADS", "NUMEXPR_NUM_THREADS"):
    os.environ[key] = "1"
import hashlib
import io
import itertools
import json
import math
import resource
import sys
import warnings
from datetime import datetime, timezone
from pathlib import Path
from zipfile import ZipFile
import numpy as np

HERE = Path(__file__).resolve().parent
AUTHOR = HERE.parents[1] / "tasks" / "variable-tutor-correction-2026-11-01"
SEEDS = tuple(range(2000,2064))
FIELDS = ("mu", "u", "plant", "offset", "goal", "zstar", "latent", "noise", "tutors", "coupling", "complement", "motor_rotation")
START = "2026-11-01T06:28:34.197Z"
DEADLINE = datetime.fromisoformat("2026-11-01T07:08:34.197+00:00")
ALPHA = .1
read_allowances = []
warning_log = []

def stamp():
    return datetime.now(timezone.utc).isoformat()

def save(name,obj):
    (HERE/name).write_text(json.dumps(obj,indent=2,allow_nan=False)+"\n")

def load_zip(path,names):
    # This experiment-specific loader reads each chosen compressed member once.
    # Charge compressed bytes, twice the decoded payload, and a header allowance.
    with ZipFile(path) as archive:
        infos=[archive.getinfo(name+".npy") for name in names]
        charge=sum(i.compress_size+2*i.file_size+256 for i in infos)
        read_allowances.append(dict(path=str(path.relative_to(AUTHOR)),members=len(infos),
                                    conservative_bytes=charge))
        return {i.filename[:-4]:np.load(io.BytesIO(archive.read(i)),allow_pickle=False) for i in infos}

def observations(condition,wrong=False):
    names=["s%d_%s"%(s,k) for s in SEEDS for k in FIELDS]
    if wrong:
        names += ["s%d_shuffled_tutors"%s for s in SEEDS]
    return load_zip(AUTHOR/condition/"observations.npz",names)

def case(data,seed):
    return {key:data["s%d_%s"%(seed,key)] for key in FIELDS}

def render(c,actions):
    return c["offset"]+np.einsum("...j,ij->...i",actions,c["plant"])

def true_loss(c,x):
    d=x-c["mu"]
    z=np.einsum("...i,ij->...j",d,c["u"])
    orth=d-np.einsum("...j,ij->...i",z,c["u"])
    radial_excess=np.clip(np.linalg.norm(z,axis=-1)-2.,0.,None)
    return (np.sum(orth*orth,axis=-1)+radial_excess**2)/4.

def model(tutors):
    center=np.mean(tutors,axis=0)
    # SVD of the actual observation matrix, independent of author covariance eigh.
    _,singular,vt=np.linalg.svd(tutors-center,full_matrices=True)
    variances=np.zeros(6)
    variances[:len(singular)]=singular**2/(len(tutors)-1)
    effective=np.maximum(variances[:2],.08**2)
    weights=np.concatenate((1/effective,np.full(4,1/.08**2)))
    return dict(center=center,frame=vt,weights=weights,
                radius=math.sqrt(max(2.*(sum(variances[:2])-2*.08**2),0.)),tutors=tutors)

def costs(m,method,x,c=None):
    if method=="truth":
        return true_loss(c,x)
    if method=="absent":
        return np.zeros(len(x))
    if method=="first":
        return np.mean((x-m["tutors"][0])**2,axis=-1)
    if method=="mean":
        return np.mean((x-m["center"])**2,axis=-1)
    d=x-m["center"]
    coordinates=np.einsum("...i,ji->...j",d,m["frame"])
    if method=="gaussian":
        return np.sum(coordinates**2*m["weights"],axis=-1)/np.sum(m["weights"])
    residual=np.sum(coordinates[...,2:]**2,axis=-1)
    if method in ("ball","shuffled"):
        excess=np.clip(np.linalg.norm(coordinates[...,:2],axis=-1)-m["radius"],0.,None)
        residual=residual+excess**2
    if method in ("tangent","ball","shuffled"):
        return residual/4.
    raise ValueError(method)

def actor(m,method,plant_case):
    # Control policy independent of plant: it receives an opaque scalar-query closure.
    def query(actions):
        return costs(m,method,render(plant_case,actions),plant_case)
    a=np.zeros(4); step=.5
    axes=np.vstack((np.eye(4),-np.eye(4)))
    current=float(query(a[None])[0])
    history=[a.copy()]; query_actions=[a.copy()]; feedback=[current]
    for iteration in range(80):
        proposals=np.clip(a+step*axes,-1.,1.)
        values=query(proposals)
        j=int(np.argmin(values))
        if values[j]<current-1e-12:
            a=proposals[j].copy();current=float(values[j])
        else:
            step/=2
        history.append(a.copy());query_actions.extend(proposals);feedback.extend(values)
    return np.asarray(history),np.asarray(query_actions),np.asarray(feedback)

def verify_saved_actor(actions,feedback,paths):
    axes=np.vstack((np.eye(4),-np.eye(4)))
    a=np.zeros(4);step=.5;current=float(feedback[0]);max_action=0.;max_path=0.
    max_path=max(max_path,float(np.max(np.abs(paths[0]-a))))
    for t in range(80):
        proposed=np.clip(a+step*axes,-1.,1.)
        max_action=max(max_action,float(np.max(np.abs(actions[1+8*t:9+8*t]-proposed))))
        values=feedback[1+8*t:9+8*t]
        j=int(np.argmin(values))
        if values[j]<current-1e-12:
            a=proposed[j].copy();current=float(values[j])
        else:
            step/=2
        max_path=max(max_path,float(np.max(np.abs(paths[t+1]-a))))
    return max_action,max_path

def box_minimum(c,center,weight):
    # Exhaustively enumerate which coordinates lie on each face, then check KKT.
    plant=c["plant"];offset=c["offset"]-center
    h=np.einsum("ia,ij,jb->ab",plant,weight,plant)
    f=np.einsum("ia,ij,j->a",plant,weight,offset)
    best=None;bestval=math.inf;best_status=None
    for status in itertools.product((-1,0,1),repeat=4):
        status=np.array(status)
        fixed=np.flatnonzero(status);free=np.flatnonzero(status==0)
        a=status.astype(float)
        if len(free):
            rhs= -f[free]
            if len(fixed):
                rhs=rhs-np.einsum("ij,j->i",h[np.ix_(free,fixed)],a[fixed])
            a[free]=np.linalg.solve(h[np.ix_(free,free)],rhs)
        if np.max(np.abs(a))>1+1e-10:
            continue
        gradient=np.einsum("ij,j->i",h,a)+f
        if np.any(gradient[status==-1]<-1e-8) or np.any(gradient[status==1]>1e-8):
            continue
        r=offset+np.einsum("ij,j->i",plant,a)
        val=float(np.einsum("i,ij,j->",r,weight,r))
        if val<bestval:
            best=a;bestval=val;best_status=status.tolist()
    if best is None:
        raise RuntimeError("No KKT box solution")
    return best,bestval,best_status

def paired(a,b,seed=50091):
    differences=np.asarray(a,dtype=float)-np.asarray(b,dtype=float)
    indices=np.random.default_rng(seed).integers(0,64,size=(10000,64))
    means=np.mean(differences[indices],axis=1)
    return dict(point=float(np.mean(differences)),interval95=np.quantile(means,[.025,.975]).tolist(),units=64,replicates=10000,seed=seed)

def vec(rows,n,method,key):
    return np.array([r[key] for r in sorted(rows,key=lambda r:r["seed"]) if r["n"]==n and r["method"]==method])

def summarize(rows):
    out={}
    for method in sorted({r["method"] for r in rows}):
        take=[r for r in rows if r["method"]==method]
        out[method]=dict(count=len(take),acquired=sum(r["acquired"] for r in take),
                        mean_final=float(np.mean([r["final"] for r in take])),
                        median_final=float(np.median([r["final"] for r in take])),
                        mean_removal=float(np.mean([r["removal"] for r in take])))
    return out

def main():
    if datetime.now(timezone.utc)>=DEADLINE:
        raise SystemExit("Review deadline reached")
    begun=stamp()
    first=json.loads((HERE/"FIRST_CALCULATION.json").read_text())
    mainrows=json.loads((HERE/"ENDPOINTS.json").read_text())
    prior_payload=first["charged_payload_bytes"]
    freeze=json.loads((AUTHOR/"FREEZE.json").read_text())
    pins={}
    pin_bytes=0
    for name,expected in freeze["sha256"].items():
        payload=(AUTHOR/name).read_bytes();pin_bytes+=len(payload)
        actual=hashlib.sha256(payload).hexdigest()
        pins[name]=dict(expected=expected,actual=actual,match=expected==actual)
    sources={}
    for condition in ("main","contrary_decoupled","contrary_noiseless","contrary_resolution"):
        sources[condition]=json.loads((AUTHOR/condition/"SCORES.json").read_text())
        payload=(AUTHOR/condition/"predictions.npz").read_bytes();pin_bytes+=len(payload)
        digest=hashlib.sha256(payload).hexdigest()
        pins[condition+"/predictions.npz"]=dict(expected=sources[condition]["prediction_sha256"],actual=digest,
                                                match=digest==sources[condition]["prediction_sha256"])
        del payload
    save("PINS_CHECKED.json",dict(checked_at=stamp(),pins=pins,hash_read_bytes=pin_bytes,
         observation_whole_sha_not_checked=True,chronology="Current byte checks only; historical execution order not certified by hashes."))
    observed=observations("main",wrong=True)
    prediction=load_zip(AUTHOR/"main"/"predictions.npz",["actions","feedback","paths"])
    savedindex=json.loads((AUTHOR/"main"/"PREDICTION_INDEX.json").read_text())
    gold_discrepancy=0.;gold_initial=0.;binary_disagreement=0
    for ours,theirs in zip(mainrows,sources["main"]["records"]):
        assert (ours["seed"],ours["n"],ours["method"])==(theirs["seed"],theirs["n"],theirs["method"])
        gold_discrepancy=max(gold_discrepancy,abs(ours["final"]-theirs["final_true_error"]))
        gold_initial=max(gold_initial,abs(ours["initial"]-theirs["initial_true_error"]))
        binary_disagreement+=ours["acquired"]!=theirs["acquired"]
    gaussian32=vec(mainrows,32,"gaussian","acquired")
    gaussian3=vec(mainrows,3,"gaussian","acquired")
    ball32=vec(mainrows,32,"ball","acquired")
    p=float(np.mean(gaussian32));n=64;z=1.959963984540054
    den=1+z*z/n;middle=(p+z*z/(2*n))/den
    half=z*math.sqrt(p*(1-p)/n+z*z/(4*n*n))/den
    win=int(np.sum(ball32 & ~gaussian32));lose=int(np.sum(gaussian32 & ~ball32))
    assert win==0
    upper=-math.expm1(math.log(.05)/64)
    statistics=dict(gaussian32_wilson95=[middle-half,middle+half],
         exposure32_minus3=paired(gaussian32,gaussian3),ball_minus_gaussian32=paired(ball32,gaussian32),
         disk_only_wins=win,gaussian_only_wins=lose,disk_only_probability_upper95=upper,
         bound_logic="p_ball-p_gaussian=p(ball-only)-p(gaussian-only)<=p(ball-only); with 0/64, P(0|p)=(1-p)^64, giving upper 1-.05^(1/64). Conditional iid whole tasks and fixed methods only.")
    query_cost_max={};action_diff=0.;path_diff=0.;count=0;models={};primary_box=[];boundary_checks=[]
    eligible={"first","mean","gaussian","tangent","ball","absent","shuffled","truth"}
    for row_index,rec in enumerate(savedindex["records"]):
        # All rows get a literal action-policy check; selected n32 evaluators get independent costs.
        da,dp=verify_saved_actor(prediction["actions"][row_index],prediction["feedback"][row_index],prediction["paths"][row_index])
        action_diff=max(action_diff,da);path_diff=max(path_diff,dp)
        if rec["n"]!=32 or rec["method"] not in eligible:
            continue
        s=rec["seed"];method=rec["method"];c=case(observed,s)
        if s not in models:
            models[s]=model(c["tutors"][:32])
        m=models[s] if method!="shuffled" else model(observed["s%d_shuffled_tutors"%s][:32])
        x=render(c,prediction["actions"][row_index])
        recomputed=costs(m,method,x,c)
        err=float(np.max(np.abs(recomputed-prediction["feedback"][row_index])))
        query_cost_max[method]=max(query_cost_max.get(method,0.),err);count+=len(recomputed)
        if method in ("mean","gaussian","tangent"):
            if method=="mean":
                w=np.eye(6)/6
            elif method=="gaussian":
                w=np.einsum("ki,k,kj->ij",m["frame"],m["weights"]/sum(m["weights"]),m["frame"])
            else:
                w=np.einsum("ki,kj->ij",m["frame"][2:],m["frame"][2:])/4
            optimum,value,status=box_minimum(c,m["center"],w)
            endpoint=prediction["paths"][row_index,-1]
            actual=float(costs(m,method,render(c,endpoint[None]),c)[0])
            primary_box.append(dict(seed=s,method=method,objective_gap=actual-value,
                                    max_endpoint_difference=float(np.max(np.abs(endpoint-optimum))),active_set=status))
        if method=="ball":
            coordinates=np.einsum("ni,ji->nj",x-m["center"],m["frame"])
            endpoint_coordinates=np.einsum("i,ji->j",render(c,prediction["paths"][row_index,-1])-m["center"],m["frame"])
            boundary_checks.append(dict(seed=s,estimated_radius=m["radius"],
                maximum_queried_radius=float(np.max(np.linalg.norm(coordinates[:,:2],axis=1))),
                queried_outside=int(np.sum(np.linalg.norm(coordinates[:,:2],axis=1)>m["radius"])),
                endpoint_outside=bool(np.linalg.norm(endpoint_coordinates[:2])>m["radius"]),
                tangent_ball_path_identical=bool(np.array_equal(prediction["paths"][row_index],prediction["paths"][row_index-1]))))
    del prediction
    print(json.dumps(dict(stage="main_reconstruction",query_cost_max=query_cost_max,queries_checked=count,statistics=statistics)),flush=True)
    asymptotic=[]
    for s in SEEDS:
        c=case(observed,s);coupling=c["coupling"]
        delta=np.linalg.solve(np.eye(4)+np.einsum("ia,ib->ab",coupling,coupling),
                              -np.einsum("ia,i->a",coupling,c["zstar"]))
        formula=c["goal"]+delta
        optimum,value,status=box_minimum(c,c["mu"],np.eye(6)/6)
        interior=bool(np.max(np.abs(formula))<=1)
        asymptotic.append(dict(seed=s,interior=interior,box_action=optimum.tolist(),formula_action=formula.tolist(),
            interior_formula_action_discrepancy=float(np.max(np.abs(formula-optimum))) if interior else None,
            exact_box_true_error=float(true_loss(c,render(c,optimum[None]))[0]),
            formula_offplane_error=float(np.sum(delta*delta)/4),active_set=status))
    matched={};intervention_rows={};component_checks={}
    for condition in ("contrary_decoupled","contrary_noiseless","contrary_resolution"):
        other=observations(condition)
        paths=load_zip(AUTHOR/condition/"predictions.npz",["paths"])["paths"]
        ix=json.loads((AUTHOR/condition/"PREDICTION_INDEX.json").read_text())
        equal=0;different=[];schema_max=0.;tutor_max=0.
        for s in SEEDS:
            old=case(observed,s);new=case(other,s)
            invariant=FIELDS if condition=="contrary_resolution" else tuple(k for k in FIELDS if k not in (("plant","offset") if condition=="contrary_decoupled" else ("tutors",)))
            for k in invariant:
                if np.array_equal(old[k],new[k]):
                    equal+=1
                else:
                    different.append([s,k])
            if condition=="contrary_decoupled":
                expected=np.einsum("ij,jk->ik",old["complement"],old["motor_rotation"])
                schema_max=max(schema_max,float(np.max(np.abs(new["plant"]-expected))))
                expected_offset=old["mu"]+np.einsum("ij,j->i",old["u"],old["zstar"])-np.einsum("ij,j->i",expected,old["goal"])
                schema_max=max(schema_max,float(np.max(np.abs(new["offset"]-expected_offset))))
            if condition=="contrary_noiseless":
                expected=old["mu"]+np.einsum("ni,ji->nj",old["latent"],old["u"])
                tutor_max=max(tutor_max,float(np.max(np.abs(new["tutors"]-expected))))
        rows=[];max_gold=0.;binary=0
        for i,rec in enumerate(ix["records"]):
            c=case(other,rec["seed"]);initial=float(true_loss(c,c["offset"][None])[0])
            final=float(true_loss(c,render(c,paths[i,-1][None]))[0])
            rows.append(dict(seed=rec["seed"],n=rec["n"],method=rec["method"],initial=initial,final=final,
                             acquired=bool(final<=.05*initial),removal=1-final/initial))
            gold=sources[condition]["records"][i]
            max_gold=max(max_gold,abs(final-gold["final_true_error"]))
            binary+=rows[-1]["acquired"]!=gold["acquired"]
        intervention_rows[condition]=rows
        matched[condition]=dict(invariant_array_equalities=equal,differences=different,plant_offset_max_abs_error=schema_max,
            noiseless_tutor_max_abs_error=tutor_max,endpoint_gold_max_abs_discrepancy=max_gold,binary_disagreements=binary,
            summaries={str(n):summarize([r for r in rows if r["n"]==n]) for n in sorted({r["n"] for r in rows})})
        del other,paths
    matched["mean_absolute_error_improvement"]=paired(vec(mainrows,32,"mean","final"),vec(intervention_rows["contrary_decoupled"],32,"mean","final"))
    save("RECONSTRUCTION.json",dict(computed_at=stamp(),started_at=begun,
         main_endpoint_rows=len(mainrows),main_gold_max_abs_discrepancy=gold_discrepancy,
         main_initial_max_abs_discrepancy=gold_initial,main_binary_disagreements=binary_disagreement,
         all_main_policy_rows=2560,all_main_policy_slots=2560*641,max_action_difference=action_diff,max_path_difference=path_diff,
         independently_recomputed_query_costs=count,query_cost_max_abs_discrepancy=query_cost_max,
         statistics=statistics,primary_n32_quadratic_optima=primary_box,
         ball_boundary_checks=boundary_checks,matched_interventions=matched,
         asymptotic_mean=asymptotic,
         asymptotic_mean_median_error=float(np.median([r["exact_box_true_error"] for r in asymptotic])),
         asymptotic_mean_interior_cases=sum(r["interior"] for r in asymptotic)))
    if datetime.now(timezone.utc)>=DEADLINE:
        raise SystemExit("Review deadline reached before contrary")
    contrary_rows=[];contrary_queries={};contrary_boxes=[]
    for s in SEEDS:
        old=case(observed,s)
        c=dict(old)
        perpendicular=np.einsum("ij,jk->ik",old["complement"],old["motor_rotation"])
        c["plant"]=ALPHA*perpendicular+np.einsum("ij,jk->ik",old["u"],old["coupling"])
        c["offset"]=old["mu"]+np.einsum("ij,j->i",old["u"],old["zstar"])-np.einsum("ij,j->i",c["plant"],old["goal"])
        m=models[s]
        initial=float(true_loss(c,c["offset"][None])[0])
        for method in ("mean","gaussian","ball","truth"):
            history,actions,feedback=actor(m,method,c)
            final=float(true_loss(c,render(c,history[-1][None]))[0])
            contrary_rows.append(dict(seed=s,n=32,method=method,initial=initial,final=final,acquired=bool(final<=.05*initial),
                removal=1-final/initial,endpoint_action=history[-1].tolist(),last_feedback=float(feedback[-1]),
                initial_original=float(true_loss(old,old["offset"][None])[0])))
            contrary_queries["s%d_%s_actions"%(s,method)]=actions
            contrary_queries["s%d_%s_feedback"%(s,method)]=feedback
            contrary_queries["s%d_%s_paths"%(s,method)]=history
            if method in ("mean","gaussian"):
                w=np.eye(6)/6 if method=="mean" else np.einsum("ki,k,kj->ij",m["frame"],m["weights"]/sum(m["weights"]),m["frame"])
                optimum,value,status=box_minimum(c,m["center"],w)
                contrary_boxes.append(dict(seed=s,method=method,actor_objective_gap=float(costs(m,method,render(c,history[-1][None]),c)[0])-value,
                    optimal_true_error=float(true_loss(c,render(c,optimum[None]))[0]),active_set=status))
    # Save every feedback query and endpoint before constructing evaluation summaries.
    np.savez_compressed(HERE/"contrary_predictions.npz",**contrary_queries)
    ball=vec(contrary_rows,32,"ball","acquired");gauss=vec(contrary_rows,32,"gaussian","acquired")
    contrast=paired(ball,gauss,seed=68317)
    contrary_summary=dict(computed_at=stamp(),alpha=ALPHA,changed_class=True,postvalidation=True,independent_units=64,
        information="Exactly same saved main n32 noisy tutors, rank2/sigma=.08/disk semantics. Plant perpendicular gain changed .1; same coupling, goal and 641-slot actor. All old observations consumed.",
        summaries=summarize(contrary_rows),disk_minus_gaussian_acquisition=contrast,
        disk_only_wins=int(np.sum(ball & ~gauss)),gaussian_only_wins=int(np.sum(gauss & ~ball)),
        frozen_10pp_rule_met=bool(contrast["point"]>=.10 and contrast["interval95"][0]>0),
        oracle_success_at_least95percent=bool(sum(r["acquired"] for r in contrary_rows if r["method"]=="truth")/64>=.95),
        gaussian_mean_box_checks=contrary_boxes,records=contrary_rows,
        caution="Changed actuator scaling; no replacement for original frozen family, no biological result or architecture novelty. Initial true-error denominators change; absolute errors saved.")
    save("CONTRARY.json",contrary_summary)
    peak=int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*(1 if sys.platform=="darwin" else 1024))
    total=prior_payload+sum(x["conservative_bytes"] for x in read_allowances)+pin_bytes+10000000
    save("RESOURCES.json",dict(start=START,finished_at=stamp(),deadline=DEADLINE.isoformat(),
        public_operations=0,new_ingress_bytes=0,read_cap_bytes=240000000,
        initial_calculation_payload_allowance=prior_payload,later_payload_allowances=read_allowances,
        pin_hash_read_bytes=pin_bytes,text_json_directory_failed_read_and_closeout_allowance=10000000,
        conservative_total_read_decode_hash_allowance=total,allowance_below_cap=bool(total<=240000000),
        method="Preselected NPZ members read once per script, via ZipFile.read then BytesIO np.load; charge compressed + twice decoded +256 bytes/member. Total includes FIRST payloads, four prediction hash reads, eight code pins and 10MB text/JSON/metadata/closeout allowance. Not kernel IO telemetry or provider internals.",
        peak_scientific_rss_bytes=peak,rss_cap_bytes=500000000,scientific_processes=1,numerical_threads=1,
        warnings=warning_log,scientific_jobs_remaining=0,
        author_compliance="Unchanged UNCERTIFIED: author conservative allowance421697685/400MB; actual IO unknown/unrun full observation hash and second reproduction remain unrun by author. Reviewer allocation separate.",
        exposure="Saved synthetic cases, all model/plant hidden parameters/queries/summaries consumed; own changed-plant outputs consumed. No empirical/protected payloads opened. No shared coordination files edited.",
        dependencies=dict(python=sys.version,numpy=np.__version__),
        unrun=["Author second full evaluation reproduction","Author historical observation archive SHA","Independent n3/all n query-cost replay","Independent hull/nearest query-distance implementation","New biological data or unknown rank/noise/nonlinear plant inference"]))
    print(json.dumps(dict(stage="complete",computed_at=stamp(),matched=matched,
         contrary={k:v for k,v in contrary_summary.items() if k not in ("records","gaussian_mean_box_checks")},
         read_allowance=total,peak_rss_bytes=peak),indent=2),flush=True)

if __name__=="__main__":
    with warnings.catch_warnings(record=True) as captured:
        warnings.simplefilter("always")
        main()
        warning_log.extend(str(w.message) for w in captured)
    if warning_log:
        record=json.loads((HERE/"RESOURCES.json").read_text());record["warnings"]=warning_log;save("RESOURCES.json",record)
        print(json.dumps(dict(warnings=warning_log)),flush=True)
