import datetime, hashlib, resource, time
from model import *
t0 = time.perf_counter()
m = Circuit()
original = m.source_comparator()
mask = m.background
original.update(t_Switch=-1., transit_End=-.7, oldMask=mask, newMask=mask, Vth_Static=original["EffVth_rhs"](CURRENT, mask))
y = np.r_[m.threshold(mask) + .5 * np.sin(np.arange(N)), np.full(N, .09)]
rhs_error = float(np.max(np.abs(m.rhs(y, mask) - original["membrane_voltageRHS"](0., y))))
jac_error = float(np.max(np.abs(m.jac(y, mask).toarray() - original["compute_jacobian"](0., y))))
threshold_error = float(np.max(np.abs(m.threshold(mask) - original["EffVth_rhs"](CURRENT, mask))))
files = ["seed0_finite_equilibrium.npz", "PERIODIC_ORBIT.npz", "MONODROMY_2048.npz", "SOURCE_REFERENCE.npz", "INPUT_STATES.npz", "seed0_finite_challenge.npz", "seed0_sham_continuation.npz"]
schemas = {}
for name in files:
    with np.load(AUTHOR / name, allow_pickle=False) as z:
        schemas[name] = {k: {"shape": list(z[k].shape), "dtype": str(z[k].dtype)} for k in z.files}
pins = {}
for p in [ORIGINAL] + [ASSETS / n for n in ("Gg.npy", "Gs.npy", "emask.npy", "FWD.json", "PLM.json", "names-response.json")]:
    raw = p.read_bytes()
    pins[str(p.relative_to(ROOT))] = {"bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest(), "git_blob_local_bytes": gitblob(raw)}
answer = dict(finished_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(), source_comparator_attribution="six original 2019 functions AST extracted, no lab helper imported",
              neurons=N, states=2*N, motors=len(m.motor), gap_nonzero=len(m.gw), synapse_nonzero=len(m.sw), independent_rhs_source_maxabs=rhs_error,
              independent_jac_source_maxabs=jac_error, independent_threshold_source_maxabs=threshold_error, schema=schemas, pins=pins,
              self_elapsed_s=time.perf_counter()-t0, rss_bytes_macos=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
dump("INPUT_INSPECTION.json", answer)
print({k: v for k, v in answer.items() if k not in ("pins",)})
assert rhs_error < 1e-6 and jac_error < 1e-7 and threshold_error < 1e-7
