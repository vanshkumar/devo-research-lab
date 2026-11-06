"""Raw-record scalar reconstruction; does not import analysis.py."""
import os
for v in ("OPENBLAS_NUM_THREADS","OMP_NUM_THREADS","MKL_NUM_THREADS","VECLIB_MAXIMUM_THREADS"):
    os.environ[v]="1"
import collections
import datetime
import hashlib
import json
import math
import pathlib
import re
import resource
import zipfile
import xml.etree.ElementTree as ET
import numpy as np

ROOT=pathlib.Path(__file__).resolve().parent
freeze=json.loads((ROOT/"FREEZE.json").read_text())
pins={n:hashlib.sha256((ROOT/n).read_bytes()).hexdigest()==p["sha256"] for n,p in freeze["pins"].items()}
assert all(pins.values())
ppin=json.loads((ROOT/"PREDICTION_PINS.json").read_text())
assert hashlib.sha256((ROOT/"predictions.npz").read_bytes()).hexdigest()==ppin["predictions_sha256"]
ns={"m":"http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
with zipfile.ZipFile(ROOT/"source/Stim-struct.xlsx") as z:
    ss=["".join(e.itertext()) for e in ET.fromstring(z.read("xl/sharedStrings.xml"))]
    geom={}
    for row in ET.fromstring(z.read("xl/worksheets/sheet2.xml")).findall("m:sheetData/m:row",ns):
        cells={}
        for e in row:
            v=e.find("m:v",ns)
            if v is not None:
                cells[re.sub("[0-9]","",e.attrib["r"])]=ss[int(v.text)] if e.attrib.get("t")=="s" else v.text
        if re.fullmatch("[a-f][0-9][0-9]",cells.get("I","")):
            geom[cells["I"]+".gif"]=[int(cells[x]) for x in "ABCDEFGH"]

fits={m:json.loads((ROOT/("FIT_"+m+".json")).read_text()) for m in ("P","B","E")}
saved=dict(np.load(ROOT/"predictions.npz"))
new={};Xs={};ys={};truths={};cases={};audit=[]

def process_prediction(history,features,query,theta,model):
    if model=="P":
        eps=[math.exp(t) for t in theta[:3]]+[1.]
        t=theta[3:]
    else:
        eps=[1.]*4;t=theta
    c=math.exp(t[0]);gamma=math.exp(t[1]);decay,spacing,lapse=t[2:]
    mass=[0.,0.,0.];previous={}
    for j,(name,label) in enumerate(history):
        gap=j-previous[name] if name in previous else 1
        previous[name]=j
        distance=0.
        for d in range(8):
            if features[j][d] != query[d]:
                if j==0: weight=1.
                else:
                    sc=label==history[j-1][1];sf=features[j][d]==features[j-1][d]
                    weight=eps[(0 if sf else 1) if sc else (2 if sf else 3)]
                distance+=weight/8
        strength=math.exp(-decay*(287-j)/288+spacing*math.log1p(gap)-c*distance)
        mass[label]+=strength
    logits=[gamma*math.log(m) for m in mass]
    base=max(logits);den=sum(math.exp(a-base) for a in logits)
    return [(1-lapse)*math.exp(a-base)/den+lapse/3 for a in logits]

def empirical_features(history,features,query):
    previous={};gaps=[]
    for j,(name,label) in enumerate(history):
        gaps.append(j-previous[name] if name in previous else 1);previous[name]=j
    result=[]
    for k in range(3):
        ix=[i for i,x in enumerate(history) if x[1]==k];n=len(ix)
        distances=[sum(a!=b for a,b in zip(query,features[i]))/8 for i in ix]
        nb=0.
        for d in range(8):
            count=sum(query[d]==features[i][d] for i in ix)
            nb+=math.log((count+1)/(n+len({x[d] for x in features})+1))/8
        result.append([math.log1p(n)]+[sum(math.exp(-c*d) for d in distances)/n for c in (1,4,16)]+
            [-min(distances),-sum(distances)/n,nb,-(287-ix[-1])/288,
             sum(math.log1p(gaps[i]) for i in ix)/n/math.log(289)])
    return result

with zipfile.ZipFile(ROOT/"source/highsim-trials.zip") as z:
    for role,ids in [("source",list(range(2,45,2))),("evaluation",[i for i in range(1,45,2) if i!=41])]:
        preds={"P":[],"B":[],"E":[]};allX=[];ally=[];alltruth=[];cases[role]=[]
        for person in ids:
            text=z.read(str(person)+".dat").decode().splitlines()
            nums=[int(v) for v in re.findall(r"\d+",text[1])][:3]
            key={chr(97+a):j for j,a in enumerate(nums)}
            rows=[r.split() for r in text if len(r.split())==12 and r.split()[0]==str(person) and r.split()[3].isdigit()]
            train=[r for r in rows if int(r[3])<288]
            test=[r for r in rows if 288<=int(r[3])<336]
            queries=[r for r in test if int(r[9][1:3])>8]
            history=[(r[9],key[r[9][0]]) for r in train]
            features=[geom[r[9]] for r in train]
            assert len(queries)==24 and all(q[9] not in {x[0] for x in history} for q in queries)
            assert all(key[r[9][0]]==int(r[6]) for r in train)
            X=[];local={"P":[],"B":[],"E":[]}
            for r in queries:
                query=geom[r[9]]
                for m in ("P","B"):
                    local[m].append(process_prediction(history,features,query,fits[m]["selected"]["theta"],m))
                xf=empirical_features(history,features,query);X.append(xf)
                logits=[sum((a-b)/c*w for a,b,c,w in zip(v,fits["E"]["mean"],fits["E"]["sd"],fits["E"]["coef"])) for v in xf]
                base=max(logits);den=sum(math.exp(a-base) for a in logits)
                local["E"].append([math.exp(a-base)/den for a in logits])
            for m in local:preds[m].append(local[m])
            allX.append(X);ally.append([int(r[5]) for r in queries]);alltruth.append([key[r[9][0]] for r in queries])
            cases[role].append((history,features,[geom[r[9]] for r in queries]))
        Xs[role]=np.array(allX);ys[role]=np.array(ally);truths[role]=np.array(alltruth)
        for m in preds:
            p=np.array(preds[m]);new[role+"_"+m]=p
            error=float(np.abs(p-saved[role+"_"+m]).max())
            assert error<1e-11
            audit.append({"role":role,"model":m,"scalars":int(p.size),"max_difference":error})

def losses(p,y):
    return -np.log(np.clip(p[np.arange(len(y))[:,None],np.arange(24)[None,:],y],1e-12,1)).mean(axis=1)

source_objectives={m:float(losses(new["source_"+m],ys["source"]).mean()) for m in ("P","B","E")}
for m in ("P","B"):
    assert abs(source_objectives[m]-fits[m]["selected"]["nll"])<1e-12
assert abs(source_objectives["E"]-fits["E"]["source_nll"])<1e-12
Emean=Xs["source"].mean(axis=(0,1,2));Esd=Xs["source"].std(axis=(0,1,2))
assert np.max(np.abs(Emean-fits["E"]["mean"]))<1e-12
assert np.max(np.abs(Esd-fits["E"]["sd"]))<1e-12
EX=(Xs["source"]-Emean)/Esd
Egradient=np.einsum("nqkf,nqk->f",EX,new["source_E"]-np.eye(3)[ys["source"]],optimize=False)/ys["source"].size+fits["E"]["penalty"]*np.array(fits["E"]["coef"])
assert np.max(np.abs(Egradient))<1e-6
score=json.loads((ROOT/"SCORES.json").read_text())
score_checks={}
idx=np.random.default_rng(20261101).integers(0,21,size=(2000,21))
pl={m:losses(new["evaluation_"+m],ys["evaluation"]) for m in ("P","B","E")}
for m in pl:
    assert abs(float(pl[m].mean())-score["nll"][m])<1e-12
for m in ("B","E"):
    boot=1-pl["P"][idx].mean(axis=1)/pl[m][idx].mean(axis=1)
    interval=np.quantile(boot,[.025,.975])
    assert np.max(np.abs(interval-score["comparisons"][m]["gain_interval"]))<1e-12
    score_checks[m]={"gain":float(1-pl["P"].mean()/pl[m].mean()),"interval":interval.tolist()}

with np.load(ROOT/"control_outcomes.npz") as f:control_y=f["y"]
controls=json.loads((ROOT/"CONTROLS.json").read_text())
control_errors=[];decisions=[]
for i,y in enumerate(control_y):
    l={m:losses(new["evaluation_"+m],y) for m in ("P","B","E")}
    passloss=True
    for m in ("B","E"):
        gain=1-l["P"].mean()/l[m].mean()
        boot=1-l["P"][idx].mean(axis=1)/l[m][idx].mean(axis=1)
        low=float(np.quantile(boot,.025))
        control_errors.append(abs(gain-controls["records"][i]["comparisons"][m]["relative_gain"]))
        passloss=passloss and gain>=.05 and low>0
    bias=float(np.take_along_axis(new["evaluation_P"],truths["evaluation"][...,None],axis=2).mean()-(y==truths["evaluation"]).mean())
    passed=bool(passloss and abs(bias)<=.10);decisions.append(passed)
    assert passed==controls["records"][i]["pass"]

out={"completed_utc":datetime.datetime.now(datetime.timezone.utc).isoformat(),"freeze_pins":pins,
    "prediction_pin_pass":True,"raw_probability_reconstruction":audit,
    "total_probability_scalars":sum(x["scalars"] for x in audit),"source_objectives":source_objectives,
    "E_gradient_maxabs":float(np.max(np.abs(Egradient))),"score_checks":score_checks,
    "all200_control_decisions_match":True,"max_control_gain_error":max(control_errors),
    "control_pass_counts":[sum(decisions[:100]),sum(decisions[100:])],
    "scope":"Within-author second implementation using raw observations; no analysis imports. Not distinct independent scientific review; original nonlinear/global optimizer and source-estimation uncertainty not certified.",
    "peak_rss_bytes_macos":resource.getrusage(resource.RUSAGE_SELF).ru_maxrss}
(ROOT/"VERIFICATION.json").write_text(json.dumps(out,indent=2))
print(json.dumps(out,indent=2))
