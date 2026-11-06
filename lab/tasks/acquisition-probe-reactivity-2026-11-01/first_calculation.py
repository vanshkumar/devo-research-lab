"""Source-mechanism reference only; no empirical histories or target arrays.

Run from repository root using the pinned .modelenv and one numerical thread.
This file deliberately does not import campaign, readers, or fitted prefixes.
"""
from pathlib import Path
import datetime as dt
import hashlib
import importlib
import io
import json
import os
import resource
import sys
import time
import zipfile

OUT = Path(__file__).resolve().parent
ROOT = OUT.parents[2]
OLD = ROOT / "campaigns/learning_rule_transport_2026-10-28"
STOP = dt.datetime.fromisoformat("2026-11-01T16:58:30+00:00")
sys.dont_write_bytecode = True
os.environ["NUMBA_CACHE_DIR"] = str(OUT / "numba_cache")
START = time.monotonic()

PINS = {
    "code/rnn_learning.py": "9d08cb223a6e418c7d32575c5927864ccb642f89d4365b510fd9341dbc5d4023",
    "code/learning_models.py": "46090bda22320171eaca91b979476b7aefc947d0cff4b3fe3c14ae67fa818017",
    "artifacts/rnn/rnnglm32_nested_best.npz": "c7f675d18f4143891ed7d2c76d91f74be74da9565fbae5407952768e2c146940",
}
read_bytes = 0
assets = {}
for name, expected in PINS.items():
    raw = (OLD / name).read_bytes()
    read_bytes += len(raw)
    observed = hashlib.sha256(raw).hexdigest()
    if observed != expected:
        raise RuntimeError("Pinned source changed: " + name)
    assets[name] = dict(bytes=len(raw), sha256=observed)
    if name.endswith(".npz"):
        model_bytes = raw

import numpy as np

keys = {"Wih", "Whh", "bih", "bhh", "A", "a", "B", "b", "C", "cc", "scale"}
with zipfile.ZipFile(io.BytesIO(model_bytes)) as z:
    members = {p.filename for p in z.infolist()}
    if members != {k + ".npy" for k in keys | {"kind", "metadata"}}:
        raise RuntimeError("Unexpected contents in parameter-only artifact")
    decoded_parameter_bytes = sum(p.file_size for p in z.infolist() if p.filename[:-4] in keys)
with np.load(io.BytesIO(model_bytes), allow_pickle=False) as z:
    params = {k: np.asarray(z[k], float) for k in keys}
read_bytes += decoded_parameter_bytes

# Inspected imports: rnn_learning -> learning_models -> NumPy/SciPy/Numba;
# neither local module has top-level empirical IO. Do not call initial_state,
# static_fit, sequence (JIT cache), or any optimizer/reader.
sys.path.insert(0, str(OLD / "code"))
module = importlib.import_module("rnn_learning")
model = module.RNNLearningModel(params)

def clone(st):
    return {k: v.copy() for k, v in st.items()}

def sig(x):
    x = np.asarray(x)
    return 1 / (1 + np.exp(-x))

def scalar_update(st, s, choice, feedback, session_start=False):
    """Independent scalar/row-loop GRU reference, same pinned parameters."""
    w = st["w"].copy()
    h = st["h"].copy()
    if choice == 0:
        return dict(w=w, h=h)
    z = np.tanh(5 * s) / np.tanh(5.)
    inp = np.r_[w, z, 1., float(session_start), float(choice < 0), float(feedback > 0), float(z > 0)]
    gi = np.array([sum(float(v) * float(u) for v, u in zip(row, inp)) for row in params["Wih"]]) + params["bih"]
    gh = np.array([sum(float(v) * float(u) for v, u in zip(row, h)) for row in params["Whh"]]) + params["bhh"]
    H = model.hidden
    rr = sig(gi[:H] + gh[:H])
    uu = sig(gi[H:2*H] + gh[H:2*H])
    hn = (1-uu) * np.tanh(gi[2*H:] + rr * gh[2*H:]) + uu * h
    a = np.maximum(np.array([sum(float(v)*float(u) for v, u in zip(row, hn)) for row in params["A"]]) + params["a"], 0)
    b = np.maximum(np.array([sum(float(v)*float(u) for v, u in zip(row, a)) for row in params["B"]]) + params["b"], 0)
    dw = params["scale"] * (np.array([sum(float(v)*float(u) for v, u in zip(row, b)) for row in params["C"]]) + params["cc"])
    return dict(w=w+dw, h=hn)

def error(a, b):
    return max(float(np.max(np.abs(a[k]-b[k]))) for k in ("w", "h"))

def accuracy(st):
    w = st["w"]
    return float((sig(w[0]+w[2]) + sig(w[1]-w[2])) / 2)

cases = []
reference_errors = []
for w in ([0., 0., 0.], [2., 2., 0.], [2., 2., 1.]):
    state = dict(w=np.array(w), h=np.zeros(model.hidden))
    history = []
    # Explicit deterministic constructed history, not sampled/new validation.
    for j, (s, c) in enumerate([(-1., 1), (1., -1), (-.25, -1), (.25, -1)]):
        reward = 1 if c == -np.sign(s) else -1
        ref = scalar_update(state, s, c, reward, session_start=(j == 0))
        nxt = model.update(clone(state), s, c, reward, session_start=(j == 0))
        reference_errors.append(error(ref, nxt))
        history.append(dict(s=s, choice=c, feedback=reward, before=accuracy(state), after=accuracy(nxt)))
        state = nxt
    expected_after_probe = 0.
    branches = []
    zero_negative_identical = True
    omission_identity = True
    for s in (-1., 1.):
        pr = float(model.probs(state, s))
        for c, probability in ((-1, pr/2), (1, (1-pr)/2)):
            reward = 1 if c == -np.sign(s) else -1
            nxt = model.update(clone(state), s, c, reward)
            ref = scalar_update(state, s, c, reward)
            reference_errors.append(error(nxt, ref))
            zero = model.update(clone(state), s, c, 0)
            negative = model.update(clone(state), s, c, -1)
            zero_negative_identical &= error(zero, negative) == 0
            omitted = model.update(clone(state), s, 0, 0)
            omission_identity &= error(omitted, state) == 0
            expected_after_probe += probability * accuracy(nxt)
            branches.append(dict(s=s, choice=c, feedback=reward, probability=probability,
                                 common_accuracy_after=accuracy(nxt),
                                 zero_feedback_parameter_change=float(np.max(np.abs(zero["w"]-state["w"])))))
    assert abs(sum(x["probability"] for x in branches)-1) < 1e-14
    assert zero_negative_identical and omission_identity
    cases.append(dict(initial_w=w, initial_h="exact zero, privileged constructed initial condition",
                      constructed_history=history,
                      preprobe_accuracy=accuracy(state),
                      expected_after_one_full_feedback_probe=expected_after_probe,
                      expected_change=expected_after_probe-accuracy(state),
                      zero_equals_negative_feedback=zero_negative_identical,
                      omission_is_state_identity=omission_identity, branches=branches))

assert max(reference_errors) < 2e-13
assert dt.datetime.now(dt.timezone.utc) < STOP
peak = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
assert peak < 800_000_000
output = dict(
    utc=dt.datetime.now(dt.timezone.utc).isoformat(),
    purpose="Source-mechanism and scalar-reference feasibility calculation, not a new main claim",
    pins=assets, parameter_keys=sorted(keys), decoded_parameter_bytes=decoded_parameter_bytes,
    imported_local_modules=["rnn_learning", "learning_models"],
    import_semantics="Inspected source has no top-level data loading. Only parameter artifact is loaded; no reader, prefix, bank, target array or optimizer called.",
    constructed_cases=cases, max_scalar_reference_error=max(reference_errors),
    feedback_semantics="API maps feedback to feedback>0: 0 and -1 are indistinguishable; omissions skip the entire update, but an observed binary response is not an omission.",
    estimand="Balanced +/-100 first-response accuracy conditional on responding at a fixed constructed state",
    assumptions=["Zero omission probability imposed for this reference", "Full correct/incorrect feedback protocol only", "No biological validity or unknown-state calibration earned", "No elapsed-time state or separate feedback-withheld input is supplied by this code"],
    native_command="OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1 NUMEXPR_NUM_THREADS=1 NUMBA_NUM_THREADS=1 PYTHONDONTWRITEBYTECODE=1 campaigns/learning_rule_transport_2026-10-28/.modelenv/bin/python lab/tasks/acquisition-probe-reactivity-2026-11-01/first_calculation.py",
    resources=dict(explicit_read_hash_decode_bytes=read_bytes, peak_scientific_process_rss_bytes=peak,
                   wall_seconds=time.monotonic()-START, public_operations=0, empirical_rows=0,
                   physical_io_and_runtime_library_reads="unknown; charged separately in cumulative resource record"),
)
(OUT / "FIRST_CALCULATION.json").write_text(json.dumps(output, indent=2) + "\n")
print(json.dumps(dict(utc=output["utc"], max_scalar_reference_error=max(reference_errors),
                     cases=[dict(initial_w=c["initial_w"], pre=c["preprobe_accuracy"], delta=c["expected_change"]) for c in cases],
                     zero_feedback_alias_verified=True, omission_identity_verified=True,
                     explicit_read_hash_decode_bytes=read_bytes, peak_rss_bytes=peak)))
