"""Independent first actual count/score calculation; no campaign/author imports."""
import os
for _v in ("OPENBLAS_NUM_THREADS", "OMP_NUM_THREADS", "MKL_NUM_THREADS", "VECLIB_MAXIMUM_THREADS", "NUMEXPR_NUM_THREADS"):
    os.environ[_v] = "1"
import hashlib, io, json, math, resource, sys, time, zipfile
from datetime import datetime, timezone
from pathlib import Path
import numpy as np

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent
inputs = []

def read_npz(rel):
    raw = (ROOT / rel).read_bytes()
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        decoded = sum(x.file_size for x in z.infolist())
    with np.load(io.BytesIO(raw), allow_pickle=False) as z:
        data = {k: z[k] for k in z.files}
    inputs.append(dict(path=rel, containing_bytes=len(raw), decoded_bytes=decoded,
                       sha256=hashlib.sha256(raw).hexdigest()))
    return data

data = {}
for rel in (
    "campaigns/population_learning_transport_2026-10-28/artifacts/results/SOURCE_ARRAYS.npz",
    "lab/reviews/learning-forecast-information-audit-2026-11-01/RECONSTRUCTED_ENDPOINTS.npz",
    "campaigns/population_learning_transport_2026-10-28/artifacts/forecasts/source/CSHL056__rnn.npz",
    "campaigns/population_learning_transport_2026-10-28/artifacts/forecasts/source/CSHL056__growth.npz",
):
    data[rel] = read_npz(rel)
schemas = {p: {k:dict(shape=list(v.shape), dtype=str(v.dtype)) for k,v in d.items()} for p,d in data.items()}
calculations = {}
for p,d in data.items():
    if not p.endswith(("__rnn.npz", "__growth.npz")):
        continue
    a = d["samples"][:, :, :2]
    n = d["counts"][:, :, :2]
    k = np.rint(a*n)
    assert np.max(np.abs(k-a*n)) < 1e-10
    assert np.all(n>0) and np.all(k>=0) and np.all(k<=n)
    # Real endpoint computation independent of advertised report totals.
    calculations[p] = dict(paired_cells=int(a.size), max_integer_residual=float(np.max(np.abs(k-a*n))),
        min_N=int(n.min()), max_N=int(n.max()), first_bin_first_side_mean_ratio=float(np.mean(a[:,0,0])),
        first_bin_first_side_pooled_ratio=float(k[:,0,0].sum()/n[:,0,0].sum()))
receipt = dict(utc=datetime.now(timezone.utc).isoformat(), status="actual_original_endpoint_count_calculation",
    owner="01a1974a-e846-7e81-a7aa-ff54457bd7eb", command="campaigns/learning_rule_transport_2026-10-28/.modelenv/bin/python lab/reviews/learning-forecast-count-joint-audit-2026-11-01/schema_calculation.py",
    units="integer opportunities/successes; accuracy ratios in probability units", schemas=schemas,
    calculations=calculations, inputs=inputs, resources=dict(containing_plus_decoded_bytes=sum(x['containing_bytes']+x['decoded_bytes'] for x in inputs),
    conservative_context_runtime_margin_bytes=30000000, peak_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
    scientific_processes=1,numerical_threads=1,public_operations=0,ingress_bytes=0,raw_rows_read=0,physical_io_unknown=True),
    environment=dict(python=sys.version, numpy=np.__version__, executable=sys.executable))
native = json.dumps(dict(utc=receipt['utc'],status=receipt['status'],calculations=calculations,resources=receipt['resources']),indent=2)
receipt['native_stdout'] = native
(OUT / 'SCHEMA_CALCULATION.json').write_text(json.dumps(receipt,indent=2)+'\n')
print(native)
print(json.dumps(schemas,indent=2))
