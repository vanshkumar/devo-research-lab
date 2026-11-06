"""Recreate circuit training and independently reconstruct motor true losses."""
import contextlib
import io
import json
from pathlib import Path
import pickle
import time
import numpy as np
import preflight as p

start = time.perf_counter()
old = json.loads((p.HERE/'suppression_result.json').read_text())
(p.HERE/'FIRST_SUPPRESSION_RESULT.json').write_text(json.dumps(old, indent=2)+'\n')
old_inputs = dict(np.load(p.HERE/'inputs.npz'))
with open(p.HERE/'state.pkl', 'rb') as f:
    old_state = pickle.load(f)
with contextlib.redirect_stdout(io.StringIO()):
    p.prepare()
new = json.loads((p.HERE/'suppression_result.json').read_text())
keys = ['before_cost', 'after_cost', 'suppression_fraction', 'silence_cost',
        'before_per_syllable', 'after_per_syllable']
for k in keys:
    assert old[k] == new[k], k
for a, b in zip(old['perturbation_ordering'], new['perturbation_ordering']):
    for k in ['scale', 'circuit_cost', 'per_syllable_cost', 'true_loss']:
        assert a[k] == b[k], k
new_inputs = dict(np.load(p.HERE/'inputs.npz'))
for k in old_inputs:
    assert np.array_equal(old_inputs[k], new_inputs[k]), k
with open(p.HERE/'state.pkl', 'rb') as f:
    new_state = pickle.load(f)
for k in ['W', 'JEE', 'JEI', 'JIE', 'JII']:
    a, b = getattr(old_state['net'], k), getattr(new_state['net'], k)
    assert np.array_equal(a.data, b.data), k
    assert np.array_equal(a.indices, b.indices), k
    assert np.array_equal(a.indptr, b.indptr), k

# Independent algebra for the feature plant and target loss.
inp = new_inputs
def y(a):
    raw = a @ inp['basis'].T + inp['bias']
    raw = np.where(raw > 0, raw, 0)
    centered = raw - raw.mean(-1, keepdims=True)
    denom = np.sqrt(np.mean(centered**2, axis=-1, keepdims=True))
    return 2 * centered / np.maximum(denom, 1e-12)
target_y = y(inp['targets'])
def loss(a):
    return float(np.square(y(a)-target_y).sum() / target_y.size)
motor = json.loads((p.HERE/'motor_update_result.json').read_text())
errors = []
for row in motor['results']:
    d = dict(np.load(p.HERE/f'motor_queries_scale_{row["scale"]:g}.npz'))
    for a, reported in [(d['action'], row['original_loss']),
                        (d['circuit_next'], row['circuit_step_true_loss']),
                        (d['oracle_next'], row['oracle_step_true_loss'])]:
        errors.append(abs(loss(a)-reported))
    q = d['queries']
    gc = ((q[:,1]-q[:,2])/(2*motor['finite_difference'])).reshape(d['action'].shape)
    gl = ((q[:,3]-q[:,4])/(2*motor['finite_difference'])).reshape(d['action'].shape)
    assert np.array_equal(gc, d['circuit_gradient'])
    assert np.array_equal(gl, d['oracle_gradient'])
    assert np.allclose(d['action']-.1*gc/np.linalg.norm(gc), d['circuit_next'], atol=0, rtol=0)
    assert np.allclose(d['action']-.1*gl/np.linalg.norm(gl), d['oracle_next'], atol=0, rtol=0)
assert max(errors) < 1e-12, max(errors)
out = dict(exact_seeded_training_replay=True, exact_trained_sparse_weights=True,
           exact_input_arrays=True, gradient_query_reconstruction=True,
           independent_loss_max_abs_error=max(errors), seconds=time.perf_counter()-start,
           scope='Original circuit retraining and saved-query reconstruction; not independent scientific validation.')
(p.HERE/'VERIFICATION.json').write_text(json.dumps(out, indent=2)+'\n')
print(json.dumps(out, indent=2))
