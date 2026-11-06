"""Independent endpoint/error reconstruction from saved observations and actions."""
import os
for key in ("OPENBLAS_NUM_THREADS", "OMP_NUM_THREADS", "MKL_NUM_THREADS", "VECLIB_MAXIMUM_THREADS", "NUMEXPR_NUM_THREADS"):
    os.environ[key] = "1"
import io
import json
import resource
import sys
from datetime import datetime, timezone
from pathlib import Path
from zipfile import ZipFile
import numpy as np

HERE = Path(__file__).resolve().parent
AUTHOR = HERE.parents[1] / "tasks" / "variable-tutor-correction-2026-11-01"
MEMBERS = ("mu", "u", "plant", "offset", "goal", "zstar", "latent", "noise", "tutors", "coupling", "complement", "motor_rotation")
selected = {}
read_components = []
with ZipFile(AUTHOR / "main" / "observations.npz") as source:
    chosen = [source.getinfo("s%d_%s.npy" % (s, k)) for s in range(2000,2064) for k in MEMBERS]
    read_components.append(dict(path="main/observations.npz", selected_members=len(chosen),
                                conservative_bytes=sum(x.compress_size+2*x.file_size+256 for x in chosen)))
    for member in chosen:
        selected[member.filename[:-4]] = np.load(io.BytesIO(source.read(member)), allow_pickle=False)
with ZipFile(AUTHOR / "main" / "predictions.npz") as source:
    member = source.getinfo("paths.npy")
    read_components.append(dict(path="main/predictions.npz:paths", conservative_bytes=member.compress_size+2*member.file_size+256))
    paths = np.load(io.BytesIO(source.read(member)), allow_pickle=False)
index = json.loads((AUTHOR / "main" / "PREDICTION_INDEX.json").read_text())

def sqnorm(x):
    return np.sum(x*x, axis=-1)

def disk_error(x, mu, plane):
    # Direct orthogonal decomposition, not the author's true_error function.
    displacement = x-mu
    coordinates = np.einsum("...i,ij->...j", displacement, plane)
    perpendicular = displacement-np.einsum("...i,ji->...j", coordinates, plane)
    outside = np.clip(np.linalg.norm(coordinates,axis=-1)-2.0, 0.0, None)
    return (sqnorm(perpendicular)+outside*outside)/4.0

rows = []
raw_tutor_max_error = 0.0
plant_max_error = 0.0
reach_max_error = 0.0
for seed in range(2000,2064):
    c = {k:selected["s%d_%s"%(seed,k)] for k in MEMBERS}
    tutors = c["mu"] + np.einsum("ni,ji->nj",c["latent"],c["u"]) + .08*c["noise"]
    raw_tutor_max_error = max(raw_tutor_max_error,float(np.max(np.abs(tutors-c["tutors"]))))
    implied_plant = np.einsum("ij,jk->ik",c["complement"],c["motor_rotation"])+np.einsum("ij,jk->ik",c["u"],c["coupling"])
    plant_max_error = max(plant_max_error,float(np.max(np.abs(implied_plant-c["plant"]))))
    target_output = c["offset"]+np.einsum("ij,j->i",c["plant"],c["goal"])
    reach_max_error = max(reach_max_error,float(disk_error(target_output,c["mu"],c["u"])))
for i, record in enumerate(index["records"]):
    seed=record["seed"]
    c = {k:selected["s%d_%s"%(seed,k)] for k in MEMBERS}
    endpoint = c["offset"]+np.einsum("ij,j->i",c["plant"],paths[i,-1])
    initial = float(disk_error(c["offset"],c["mu"],c["u"]))
    final = float(disk_error(endpoint,c["mu"],c["u"]))
    rows.append(dict(seed=seed,n=record["n"],method=record["method"],initial=initial,final=final,
                     acquired=bool(final<=.05*initial),removal=1-final/initial,
                     endpoint_action=paths[i,-1].tolist()))
summary={}
for n in (3,8,32,128):
    summary[str(n)]={}
    for method in ("first","mean","gaussian","tangent","ball","hull","nearest","absent","shuffled","truth"):
        take=[r for r in rows if r["n"]==n and r["method"]==method]
        summary[str(n)][method]=dict(acquired=sum(r["acquired"] for r in take),
            mean_final=float(np.mean([r["final"] for r in take])),
            median_final=float(np.median([r["final"] for r in take])),mean_removal=float(np.mean([r["removal"] for r in take])))
out=dict(computed_at=datetime.now(timezone.utc).isoformat(),method="Independent direct Euclidean projection of saved actual endpoints and reconstruction of saved noisy tutors/hidden plants; no author module executed.",
         independent_tasks=64,endpoint_rows=len(rows),raw_tutor_max_abs_error=raw_tutor_max_error,
         plant_max_abs_error=plant_max_error,reachable_goal_max_true_error=reach_max_error,
         summary=summary,first_case_n32=[r for r in rows if r["seed"]==2000 and r["n"]==32 and r["method"] in ("mean","gaussian","ball","truth")],
         read_components=read_components,charged_payload_bytes=sum(r["conservative_bytes"] for r in read_components),
         peak_rss_bytes=int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*(1 if sys.platform=="darwin" else 1024)))
(HERE/"FIRST_CALCULATION.json").write_text(json.dumps(out,indent=2,allow_nan=False)+"\n")
(HERE/"ENDPOINTS.json").write_text(json.dumps(rows,indent=2,allow_nan=False)+"\n")
print(json.dumps(out,indent=2))
