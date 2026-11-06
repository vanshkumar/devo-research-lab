"""Postvalidation scores of all already-saved source-fit basins; no fitting."""
import json
import pathlib
import numpy as np
import analysis as a

ROOT=pathlib.Path(__file__).resolve().parent
data=a.load_prepared()
fits=json.loads((ROOT/"FIT_P.json").read_text())
with np.load(ROOT/"evaluation_outcomes.npz") as f:y=f["y"]
prob=a.get_probs()
indices=np.random.default_rng(20261101).integers(0,len(y),size=(2000,len(y)))
out=[]
for i,run in enumerate(fits["runs"]):
    p=a.predict(np.array(run["theta"]),"P",data,"evaluation")
    out.append({"saved_run":i,"source_nll":run["nll"],
        "selected_in_original":run==fits["selected"],
        **a.decision({**prob,"P":p},y,data["evaluation_truth"],indices)})
summary={"postvalidation":True,"results":out,"resources":a.metrics_resource(),
    "source_observed_accuracy":float((data["source_y"]==data["source_truth"]).mean()),
    "interpretation":"All pre-existing basins scored, no new fit or selection; original result remains primary."}
a.save("CONTRARY.json",summary)
print(json.dumps({"runs":[{"run":r["saved_run"],"source_nll":r["source_nll"],"selected":r["selected_in_original"],
    "nll":r["nll"],"pass":r["pass"],"accuracy_bias":r["P_accuracy_bias"]} for r in out],
    "source_accuracy":summary["source_observed_accuracy"],"resources":summary["resources"]},indent=2))
