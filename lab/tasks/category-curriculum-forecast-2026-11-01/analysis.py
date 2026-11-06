"""One-thread source-fixed curriculum forecast. See PROTOCOL.md for scope."""
import os
for variable in ("OPENBLAS_NUM_THREADS", "OMP_NUM_THREADS", "MKL_NUM_THREADS", "VECLIB_MAXIMUM_THREADS", "NUMEXPR_NUM_THREADS"):
    os.environ[variable] = "1"
import datetime
import hashlib
import json
import pathlib
import re
import resource
import sys
import time
import zipfile
import xml.etree.ElementTree as ET
import numpy as np
import scipy
from scipy.optimize import minimize
from scipy.special import logsumexp, softmax

ROOT = pathlib.Path(__file__).resolve().parent
HARD = datetime.datetime.fromisoformat("2026-11-01T10:37:04.423+00:00")
T0 = time.monotonic()

def now():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()

def check_time():
    if datetime.datetime.now(datetime.timezone.utc) >= HARD:
        raise RuntimeError("Fixed hard deadline reached")

def save(name, obj):
    (ROOT / name).write_text(json.dumps(obj, indent=2, allow_nan=False))

def metrics_resource():
    return {"utc": now(), "elapsed_seconds": time.monotonic()-T0,
            "peak_rss_bytes_macos": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
            "numpy": np.__version__, "scipy": scipy.__version__,
            "numeric_threads_requested": 1}

def geometry():
    ns = {"s": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
    with zipfile.ZipFile(ROOT / "source/Stim-struct.xlsx") as z:
        strings = ["".join(x.itertext()) for x in ET.fromstring(z.read("xl/sharedStrings.xml"))]
        result = {}
        for row in ET.fromstring(z.read("xl/worksheets/sheet2.xml")).findall("s:sheetData/s:row", ns):
            cells = {}
            for cell in row:
                value_node = cell.find("s:v", ns)
                if value_node is None:
                    continue
                value = value_node.text
                if cell.attrib.get("t") == "s":
                    value = strings[int(value)]
                cells[re.sub(r"\d", "", cell.attrib["r"])] = value
            if re.fullmatch(r"[a-f]\d\d", cells.get("I", "")):
                result[cells["I"] + ".gif"] = np.array([int(cells[c]) for c in "ABCDEFGH"])
    assert len(result) == 96
    return result

def raw_rows(z, person):
    payload = z.read(str(person) + ".dat")
    lines = payload.decode().splitlines()
    rows = [s.split() for s in lines if len(s.split()) == 12 and
            s.split()[0] == str(person) and s.split()[3].isdigit()]
    return payload, lines, rows

def prepare():
    check_time()
    geom = geometry()
    arrays, details = {}, []
    with zipfile.ZipFile(ROOT / "source/highsim-trials.zip") as z:
        for role, ids in [("source", list(range(2,45,2))),
                          ("evaluation", [i for i in range(1,45,2) if i != 41])]:
            Dall, labelsall, gapall, Eall, truthall, yall = [], [], [], [], [], []
            for person in ids:
                payload, lines, rows = raw_rows(z, person)
                assert len(rows) == 672
                mapping = {chr(97+c): k for k,c in enumerate(map(int, re.findall(r"\d+", lines[1])[:3]))}
                tr = [r for r in rows if int(r[4]) in (1,2,3,4)]
                te = [r for r in rows if int(r[4]) == 5]
                assert len(tr) == 288 and len(te) == 48
                seen = {r[9] for r in tr}
                novel = [r for r in te if int(r[9][1:3]) >= 9]
                assert len(seen) in (23,24) and len(novel) == 24
                assert all(r[9] not in seen for r in novel)
                x = np.array([geom[r[9]] for r in tr])
                q = np.array([geom[r[9]] for r in novel])
                labels = np.array([mapping[r[9][0]] for r in tr])
                assert labels.tolist() == [int(r[6]) for r in tr]
                assert ("BI" if role == "source" else "IB") in lines[2]
                switchcount = int(np.sum(labels[1:] != labels[:-1]))
                assert (switchcount < 144) == (role == "source")
                difference = (q[:,None,:] != x[None,:,:])
                kinds = np.full(x.shape, 4, dtype=int)
                samecat = labels[1:] == labels[:-1]
                samefeature = x[1:] == x[:-1]
                kinds[1:] = np.where(samecat[:,None], np.where(samefeature,0,1), np.where(samefeature,2,3))
                D = np.stack([np.sum(difference*(kinds[None,:,:] == k),axis=2) for k in range(5)],axis=2)
                hamming = difference.mean(axis=2)
                previous, gaps = {}, []
                for t,r in enumerate(tr):
                    gaps.append(t-previous[r[9]] if r[9] in previous else 1)
                    previous[r[9]] = t
                loggap = np.log1p(gaps)
                E = np.zeros((24,3,9))
                for k in range(3):
                    ix = np.flatnonzero(labels == k)
                    n = len(ix)
                    E[:,k,0] = np.log1p(n)
                    for jj,c in enumerate((1,4,16),start=1):
                        E[:,k,jj] = np.exp(-c*hamming[:,ix]).mean(axis=1)
                    E[:,k,4] = -hamming[:,ix].min(axis=1)
                    E[:,k,5] = -hamming[:,ix].mean(axis=1)
                    for d in range(8):
                        count = (q[:,d,None] == x[ix,d][None,:]).sum(axis=1)
                        E[:,k,6] += np.log((count+1)/(n+len(np.unique(x[:,d]))+1))/8
                    E[:,k,7] = -(287-ix[-1])/288
                    E[:,k,8] = loggap[ix].mean()/np.log(289)
                truth = np.array([mapping[r[9][0]] for r in novel])
                if role == "source":
                    y = np.array([int(r[5]) for r in novel])
                    assert np.all((0 <= y) & (y < 3))
                    yall.append(y)
                Dall.append(D); labelsall.append(labels); gapall.append(loggap)
                Eall.append(E); truthall.append(truth)
                details.append({"role": role,"person":person,"sha256":hashlib.sha256(payload).hexdigest(),
                    "mapping": mapping,"switches":switchcount,
                    "train_counts":np.bincount(labels,minlength=3).tolist(),
                    "novel_stimuli":[r[9] for r in novel]})
            for key,value in [("D",Dall),("labels",labelsall),("loggap",gapall),("E",Eall),("truth",truthall)]:
                arrays[role+"_"+key] = np.array(value)
            arrays[role+"_ids"] = np.array(ids)
            if role == "source": arrays["source_y"] = np.array(yall)
    np.savez_compressed(ROOT / "prepared.npz", **arrays)
    save("PREPARE.json", {"completed": now(),"people":details,"resources":metrics_resource(),
        "source_outcomes": "22 people's first new-item test responses interpreted; first-training feedback labels used; evaluation response/correctness fields uninterpreted. All DAT members decoded again in RAM.",
        "nominal_geometry": "96 explicit physical names, eight nominal features; arbitrary feature numbers are never subtracted.",
        "half2": "All acquired/decoded, unscored except participant20 pilot."})
    print(json.dumps({"source_people":len(arrays["source_ids"]),"evaluation_people":len(arrays["evaluation_ids"]),
        "source_queries":arrays["source_y"].size,"resources":metrics_resource()},indent=2))

def load_prepared():
    with np.load(ROOT / "prepared.npz") as f:
        return {k:f[k] for k in f.files}

def predict(theta, model, data, role):
    if model == "P":
        eps = np.r_[np.exp(theta[:3]),1.,1.]
        t = theta[3:]
    else:
        eps = np.ones(5); t = theta
    c,gamma = np.exp(t[:2]); decay,spacing,lapse = t[2:]
    distance = np.einsum("nqte,e->nqt",data[role+"_D"],eps,optimize=False)/8
    age = np.arange(287,-1,-1)/288
    logsim = -c*distance - decay*age[None,None,:] + spacing*data[role+"_loggap"][:,None,:]
    masses = np.stack([logsumexp(np.where(data[role+"_labels"][:,None,:] == k,logsim,-np.inf),axis=2) for k in range(3)],axis=2)
    p = softmax(gamma*masses,axis=2)
    return (1-lapse)*p+lapse/3

def nll(p,y):
    return -np.log(np.clip(np.take_along_axis(p,y[...,None],axis=2)[...,0],1e-12,1)).mean()

def fit_process(data, model, Btheta=None):
    bounds = [(-4,4),(-2,2),(0,8),(-2,2),(0,.95)]
    starts = [np.array([0.,0.,0.,0.,.2]),np.array([np.log(2),0.,1.,.3,.2])]
    if model == "P":
        bounds = [(-2,2)]*3+bounds
        starts = [np.r_[np.zeros(3),starts[0]],np.r_[[1.,-1.,-1.],starts[1]]]
        if Btheta is not None: starts.append(np.r_[np.zeros(3),Btheta])
    runs = []
    for start in starts:
        check_time()
        def objective(t):
            check_time()
            return float(nll(predict(t,model,data,"source"),data["source_y"]))
        r = minimize(objective,start,method="L-BFGS-B",bounds=bounds,
                     options={"maxiter":500,"ftol":1e-11,"gtol":1e-6,"maxls":40})
        runs.append({"start":start.tolist(),"theta":r.x.tolist(),"nll":float(r.fun),
                     "success":bool(r.success),"message":str(r.message),"nit":int(r.nit),"nfev":int(r.nfev)})
        print(model,"sourceNLL",float(r.fun),"success",r.success,"iterations",r.nit,flush=True)
    best = min(runs,key=lambda r:r["nll"])
    return np.array(best["theta"]),{"model":model,"runs":runs,"selected":best}

def standardize(E):
    mean = E.mean(axis=(0,1,2)); sd = E.std(axis=(0,1,2)); sd = np.maximum(sd,1e-8)
    return (E-mean)/sd,mean,sd

def fit_regression(X,y,penalty):
    target = np.eye(3)[y]
    def obj(w):
        logits = np.einsum("nqkf,f->nqk",X,w,optimize=False)
        p = softmax(logits,axis=2)
        loss = float((logsumexp(logits,axis=2)-np.take_along_axis(logits,y[...,None],axis=2)[...,0]).mean()+penalty*np.sum(w*w)/2)
        grad = np.einsum("nqkf,nqk->f",X,p-target,optimize=False)/y.size+penalty*w
        return loss,grad
    r = minimize(obj,np.zeros(X.shape[-1]),jac=True,method="L-BFGS-B",options={"maxiter":500,"ftol":1e-12,"gtol":1e-8})
    if not r.success: raise RuntimeError("Empirical convex optimization failed: "+str(r.message))
    return r.x

def fit_empirical(data):
    raw,y = data["source_E"],data["source_y"]
    cvs = []
    for penalty in (.001,.01,.1,1.):
        losses = []
        for i in range(len(y)):
            keep = np.arange(len(y)) != i
            X,mean,sd = standardize(raw[keep])
            w = fit_regression(X,y[keep],penalty)
            p = softmax(np.einsum("nqkf,f->nqk",(raw[i:i+1]-mean)/sd,w,optimize=False),axis=2)
            losses.append(float(nll(p,y[i:i+1])))
        cvs.append({"penalty":penalty,"person_losses":losses,"mean_nll":float(np.mean(losses))})
    selected = min(cvs,key=lambda x:x["mean_nll"])["penalty"]
    X,mean,sd = standardize(raw)
    w = fit_regression(X,y,selected)
    return {"CV":cvs,"penalty":selected,"coef":w.tolist(),"mean":mean.tolist(),"sd":sd.tolist(),
        "source_nll":float(nll(softmax(np.einsum("nqkf,f->nqk",X,w,optimize=False),axis=2),y))}

def predict_empirical(fit,data,role):
    X=(data[role+"_E"]-fit["mean"])/fit["sd"]
    return softmax(np.einsum("nqkf,f->nqk",X,np.array(fit["coef"]),optimize=False),axis=2)

def fit():
    data=load_prepared()
    Bt,B=fit_process(data,"B")
    save("FIT_B.json",B)
    Pt,P=fit_process(data,"P",Bt)
    assert P["selected"]["nll"] <= B["selected"]["nll"]+1e-7
    save("FIT_P.json",P)
    E=fit_empirical(data);save("FIT_E.json",E)
    save("FIT_RESOURCES.json",metrics_resource())
    print("empirical penalty",E["penalty"],"CV",[(x["penalty"],x["mean_nll"]) for x in E["CV"]],flush=True)
    print(json.dumps(metrics_resource()))

def forecasts():
    data=load_prepared()
    Pfit=json.loads((ROOT/"FIT_P.json").read_text())
    Bfit=json.loads((ROOT/"FIT_B.json").read_text())
    Efit=json.loads((ROOT/"FIT_E.json").read_text())
    outputs={}
    for role in ("source","evaluation"):
        outputs[role+"_P"]=predict(np.array(Pfit["selected"]["theta"]),"P",data,role)
        outputs[role+"_B"]=predict(np.array(Bfit["selected"]["theta"]),"B",data,role)
        outputs[role+"_E"]=predict_empirical(Efit,data,role)
    np.savez_compressed(ROOT/"predictions.npz",**outputs)
    p=outputs["evaluation_P"]
    disagreement={}
    expected_P=float(-np.sum(p*np.log(np.clip(p,1e-12,1)),axis=2).mean())
    for m in ("B","E"):
        b=outputs["evaluation_"+m]
        expected_B=float(-np.sum(p*np.log(np.clip(b,1e-12,1)),axis=2).mean())
        disagreement[m]={"mean_absolute_probability_difference":float(np.abs(p-b).mean()),
            "max_absolute_probability_difference":float(np.abs(p-b).max()),
            "expected_P_NLL_under_P":expected_P,"expected_baseline_NLL_under_P":expected_B,
            "expected_P_relative_gain_under_P":1-expected_P/expected_B}
    save("PREDICTION_PINS.json",{"saved_utc":now(),"predictions_sha256":hashlib.sha256((ROOT/"predictions.npz").read_bytes()).hexdigest(),
        "disagreement":disagreement,"resources":metrics_resource(),
        "real_evaluation_responses": "UNINTERPRETED"})
    print(json.dumps(disagreement,indent=2))

def person_losses(p,y):
    return -np.log(np.clip(np.take_along_axis(p,y[...,None],axis=2)[...,0],1e-12,1)).mean(axis=1)

def decision(prob,y,truth,indices):
    losses={m:person_losses(prob[m],y) for m in ("P","B","E")}
    comparisons={}
    for m in ("B","E"):
        gain=1-losses["P"].mean()/losses[m].mean()
        boot=1-losses["P"][indices].mean(axis=1)/losses[m][indices].mean(axis=1)
        lo,hi=np.quantile(boot,[.025,.975])
        comparisons[m]={"relative_gain":float(gain),"gain_interval":[float(lo),float(hi)],
            "person_nll_difference":(losses[m]-losses["P"]).tolist(),
            "passes_relative_interval":bool(gain >= .05 and lo > 0)}
    pcorrect=np.take_along_axis(prob["P"],truth[...,None],axis=2)[...,0]
    observed=float((y==truth).mean());bias=float(pcorrect.mean()-observed)
    passes=all(x["passes_relative_interval"] for x in comparisons.values()) and abs(bias)<=.10
    return {"pass":bool(passes),"comparisons":comparisons,
            "nll":{m:float(v.mean()) for m,v in losses.items()},
            "observed_accuracy":observed,"P_predicted_accuracy":float(pcorrect.mean()),"P_accuracy_bias":bias}

def get_probs():
    with np.load(ROOT/"predictions.npz") as f:
        return {m:f["evaluation_"+m] for m in ("P","B","E")}

def controls():
    data=load_prepared();prob=get_probs();truth=data["evaluation_truth"]
    rng=np.random.default_rng(20261102)
    outcomes=[];records=[]
    for generator in ("P","E"):
        for i in range(100):
            check_time()
            u=rng.random(truth.shape)
            y=(u[...,None]>np.cumsum(prob[generator],axis=2)).sum(axis=2)
            assert y.max()<3
            indices=np.random.default_rng(20261101).integers(0,len(y),size=(2000,len(y)))
            result=decision(prob,y,truth,indices)
            records.append({"generator":generator,"replicate":i,**result});outcomes.append(y)
    np.savez_compressed(ROOT/"control_outcomes.npz",y=np.array(outcomes))
    save("CONTROLS.json",{"records":records,"P_signal_candidate_passes":sum(r["pass"] for r in records[:100]),
        "E_null_passes":sum(r["pass"] for r in records[100:]),"resources":metrics_resource(),
        "scope":"Conditional on frozen fitted probabilities and fixed inputs; no source refitting, heterogeneity or boundary5%power/coverage guarantee."})
    print("P candidate passes",sum(r["pass"] for r in records[:100]),"E null passes",sum(r["pass"] for r in records[100:]),flush=True)

def score():
    data=load_prepared();prob=get_probs();truth=data["evaluation_truth"]
    all_y=[];validation=[]
    with zipfile.ZipFile(ROOT/"source/highsim-trials.zip") as z:
        for person in data["evaluation_ids"]:
            _,_,rows=raw_rows(z,int(person))
            tr=[r for r in rows if int(r[4]) in (1,2,3,4)]
            test=[r for r in rows if int(r[4])==5]
            seen={r[9] for r in tr}
            assert all((r[11]=="0")== (r[9] not in seen) for r in test)
            novel=[r for r in test if int(r[9][1:3])>=9]
            y=np.array([int(r[5]) for r in novel]); assert np.all((0<=y)&(y<3))
            all_y.append(y)
            true=np.array([int(r[6]) for r in novel]);corr=np.array([int(r[7]) for r in novel])
            assert np.array_equal(corr,y==true)
            validation.append(true)
    y=np.array(all_y);assert np.array_equal(truth,np.array(validation))
    indices=np.random.default_rng(20261101).integers(0,len(y),size=(2000,len(y)))
    result=decision(prob,y,truth,indices)
    result.update(evaluation_people=data["evaluation_ids"].tolist(),queries=int(y.size),scored_utc=now(),
        resources=metrics_resource(),per_person={},brier={},predicted_accuracy={},deletions=[])
    for m in ("P","B","E"):
        result["per_person"][m]=person_losses(prob[m],y).tolist()
        result["brier"][m]=float(np.sum((prob[m]-np.eye(3)[y])**2,axis=2).mean())
        result["predicted_accuracy"][m]=float(np.take_along_axis(prob[m],truth[...,None],axis=2).mean())
    for i,person in enumerate(data["evaluation_ids"]):
        keep=np.arange(len(y))!=i
        result["deletions"].append({"omitted_person":int(person),**{m:float(1-person_losses(prob["P"],y)[keep].mean()/person_losses(prob[m],y)[keep].mean()) for m in ("B","E")}})
    np.savez_compressed(ROOT/"evaluation_outcomes.npz",y=y,truth=truth)
    save("SCORES.json",result)
    print(json.dumps({k:result[k] for k in ("pass","nll","comparisons","observed_accuracy","predicted_accuracy","queries","resources")},indent=2))

if __name__ == "__main__":
    check_time()
    {"prepare":prepare,"fit":fit,"predict":forecasts,"controls":controls,"score":score}[sys.argv[1]]()
