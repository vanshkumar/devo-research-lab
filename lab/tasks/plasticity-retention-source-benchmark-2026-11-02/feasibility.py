"""One source-faithful independent original-SCR feasibility calculation.

No third-party packages, fitted hyperparameters, renewal/replay comparison or
main effect claim. See FEASIBILITY_PLAN.md and vendor/LICENSE.
"""
import hashlib
import itertools
import json
import math
from pathlib import Path
import random
import resource
import time
import traceback

ROOT = Path(__file__).resolve().parent
SEED = 1729
D, H, TARGET_H, PERIOD, N = 20, 5, 100, 10000, 30000
STEP = .003
CHECKPOINTS = {0, 99, 9999, 10000, 19999, 20000, 29999}


def x_from(context, fast):
    return context + [(fast >> j) & 1 for j in range(5)]


def teacher_float(x, tw, tb, tv, ob):
    features = []
    for w, b in zip(tw, tb):
        tau = .7 * (D + 1) - (D - sum(w) + b) / 2
        z = sum(a * v for a, v in zip(x, w)) + b
        features.append(int(z > tau))
    return sum(v * h for v, h in zip(tv, features)) + ob


def teacher_integer(x, tw, tb, tv, ob):
    # Exact rational .7 = 7/10, independently clearing denominator in the
    # source LTU strict inequality; no presumed conventional bias correction.
    active = []
    for j in range(TARGET_H):
        lhs = 10 * (sum(tw[j][k] * x[k] for k in range(D)) + tb[j])
        rhs = 7 * (D + 1) - 5 * (D - sum(tw[j]) + tb[j])
        active.append(lhs > rhs)
    return ob + sum(tv[j] for j in range(TARGET_H) if active[j])


def forward(theta, x):
    a = x + [1.0]
    z = [sum(theta[j * 21 + k] * a[k] for k in range(21)) for j in range(H)]
    h = [max(0.0, v) for v in z]
    y = theta[110] + sum(theta[105 + j] * h[j] for j in range(H))
    return y, z, h


def loss(theta, x, y):
    return (forward(theta, x)[0] - y) ** 2


def gradient(theta, x, target):
    pred, z, h = forward(theta, x)
    delta = 2 * (pred - target)
    a = x + [1.0]
    grad = []
    for j in range(H):
        back = delta * theta[105 + j] if z[j] > 0 else 0.0
        grad.extend(back * v for v in a)
    grad.extend(delta * v for v in h)
    grad.append(delta)
    return grad


def learn(theta, x, target):
    pred, z, h = forward(theta, x)
    err = pred - target
    # Save pre-update output weights before changing hidden weights.
    old_v = theta[105:110]
    a = x + [1.0]
    for j in range(H):
        if z[j] > 0:
            scale = STEP * 2 * err * old_v[j]
            for k in range(21):
                theta[j * 21 + k] -= scale * a[k]
    for j in range(H):
        theta[105 + j] -= STEP * 2 * err * h[j]
    theta[110] -= STEP * 2 * err
    return err * err


def reference_update(theta, x, target):
    # Separately expressed unaugmented, nested scalar network.
    weights = [theta[j * 21:j * 21 + 20] for j in range(H)]
    biases = [theta[j * 21 + 20] for j in range(H)]
    outgoing, out_bias = theta[105:110], theta[110]
    pre = [sum(wi * xi for wi, xi in zip(w, x)) + b
           for w, b in zip(weights, biases)]
    hidden = [v if v > 0 else 0.0 for v in pre]
    pred = sum(a * b for a, b in zip(outgoing, hidden)) + out_bias
    residual = pred - target
    hidden_delta = [2 * residual * v * (z > 0)
                    for v, z in zip(outgoing, pre)]
    new = []
    for w, b, delta in zip(weights, biases, hidden_delta):
        new.extend(wi - STEP * delta * xi for wi, xi in zip(w, x))
        new.append(b - STEP * delta)
    new.extend(v - STEP * 2 * residual * h for v, h in zip(outgoing, hidden))
    new.append(out_bias - STEP * 2 * residual)
    return new


def finite_difference_check(theta, x, target):
    eps = 1e-6
    _, z, _ = forward(theta, x)
    if min(abs(v) for v in z) < 1e-4:
        return {'status': 'SKIP_relu_kink', 'minimum_abs_preactivation': min(abs(v) for v in z)}
    exact = gradient(theta, x, target)
    numeric = []
    for k in range(111):
        plus, minus = theta[:], theta[:]
        plus[k] += eps
        minus[k] -= eps
        numeric.append((loss(plus, x, target) - loss(minus, x, target)) / (2 * eps))
    absolute = max(abs(a - b) for a, b in zip(exact, numeric))
    scaled = max(abs(a - b) / max(1.0, abs(a), abs(b)) for a, b in zip(exact, numeric))
    assert scaled < 2e-6, (absolute, scaled)
    return {'status': 'PASS', 'parameters': 111, 'maximum_absolute_error': absolute,
            'maximum_scaled_error': scaled,
            'minimum_abs_preactivation': min(abs(v) for v in z)}


def risk(theta, context, targets):
    predictions = [forward(theta, x_from(context, fast))[0] for fast in range(32)]
    mse = sum((p - y) ** 2 for p, y in zip(predictions, targets)) / 32
    return mse, predictions


def run(N=N, prefix=''):
    started = time.perf_counter()
    rng = random.Random(SEED)
    sign = lambda: 2 * rng.randrange(2) - 1
    tw = [[sign() for _ in range(D)] for _ in range(TARGET_H)]
    tb = [sign() for _ in range(TARGET_H)]
    tv, ob = [sign() for _ in range(TARGET_H)], sign()
    # Original generator makes one more complete block than requested.
    contexts = [[rng.randrange(2) for _ in range(15)] for _ in range(N // PERIOD + 1)]
    fast_indices = [rng.randrange(32) for _ in range(len(contexts) * PERIOD)]
    tables, teacher_checks = [], 0
    for context in contexts:
        ys = []
        for fast in range(32):
            x = x_from(context, fast)
            y = teacher_float(x, tw, tb, tv, ob)
            ref = teacher_integer(x, tw, tb, tv, ob)
            assert y == ref, (y, ref)
            teacher_checks += 1
            ys.append(y)
        tables.append(ys)
    bound_in, bound_out = math.sqrt(6 / D), math.sqrt(3 / H)
    theta = []
    for _ in range(H):
        theta.extend(rng.uniform(-bound_in, bound_in) for _ in range(D))
        theta.append(0.0)
    theta.extend(rng.uniform(-bound_out, bound_out) for _ in range(H))
    theta.append(0.0)
    realization = {'seed': SEED, 'teacher_weights': tw, 'teacher_bias': tb,
                   'teacher_out_weights': tv, 'teacher_out_bias': ob,
                   'contexts': contexts, 'fast_indices': fast_indices,
                   'targets_by_context': tables, 'initial_learner': theta[:]}
    realization_bytes = json.dumps(realization, separators=(',', ':')).encode()
    (ROOT / (prefix + 'REALIZATION.json')).write_bytes(realization_bytes)
    initial = []
    for context, ys in zip(contexts[:3], tables[:3]):
        initial.append(risk(theta, context, ys)[0])
    refs, boundaries, losses = [], [], []
    old_predictions = None
    training_t0 = time.perf_counter()
    for i in range(N):
        task = i // PERIOD
        fast = fast_indices[i]
        x, y = x_from(contexts[task], fast), tables[task][fast]
        if i in CHECKPOINTS or i == N - 1:
            before = theta[:]
            expected = reference_update(before, x, y)
            fd = finite_difference_check(before, x, y)
        err = learn(theta, x, y)
        assert math.isfinite(err) and all(math.isfinite(v) for v in theta)
        losses.append(err)
        if i in CHECKPOINTS or i == N - 1:
            gap = max(abs(a - b) for a, b in zip(theta, expected))
            assert gap < 1e-11, gap
            refs.append({'before_update': i, 'scalar_update_max_abs_error': gap,
                         'finite_difference': fd})
        if (i + 1) % PERIOD == 0:
            old_mse, old_pred = risk(theta, contexts[0], tables[0])
            current_mse = risk(theta, contexts[task], tables[task])[0]
            if old_predictions is None:
                old_predictions = old_pred[:]
            drift = sum((a - b) ** 2 for a, b in zip(old_pred, old_predictions)) / 32
            boundaries.append({'examples': i + 1, 'task': task,
                               'preupdate_online_mse': sum(losses[-PERIOD:]) / PERIOD,
                               'current_exact_support_mse': current_mse,
                               'old_task0_exact_support_mse': old_mse,
                               'old_prediction_drift_from_task0_finish': drift,
                               'old_predictions': old_pred})
    training_seconds = time.perf_counter() - training_t0
    fd_passes = sum(r['finite_difference']['status'] == 'PASS' for r in refs)
    assert fd_passes >= 1
    outputs = {'utc': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
               'kind': 'original_published_task_independent_feasibility_only',
               'author_code_executed': False, 'main_comparison': 'UNRUN',
               'config': {'d': D, 'hidden': H, 'target_hidden': TARGET_H,
                          'beta': .7, 'period': PERIOD, 'updates': N,
                          'step_size': STEP, 'seed': SEED,
                          'arithmetic': 'Python float64; source uses Torch float32',
                          'randomness': 'Python RNG; source uses Torch RNG'},
               'reference': {'teacher_contexts': len(contexts),
                             'teacher_exact_integer_checks': teacher_checks,
                             'sgd_scalar_reference': refs,
                             'finite_difference_passes': fd_passes,
                             'all_finite': True},
               'generated_samples': len(fast_indices), 'unused_final_samples': PERIOD,
               'realization_sha256': hashlib.sha256(realization_bytes).hexdigest(),
               'realization_bytes': len(realization_bytes),
               'initial_mse_by_first_three_contexts': initial,
               'boundary_diagnostics': boundaries,
               'final_learner': theta,
               'learning_seconds_including_checkpoint_references': training_seconds,
               'total_seconds': time.perf_counter() - started,
               'max_rss_bytes': resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
               'parallelism': 'one process, one native Python thread',
               'provider_runtime_rss_physical_io': 'unknown'}
    (ROOT / (prefix + 'FEASIBILITY.json')).write_text(json.dumps(outputs, indent=2) + '\n')
    print(json.dumps({k: v for k, v in outputs.items()
                      if k not in ('final_learner', 'boundary_diagnostics')}))
    print(json.dumps({'boundary_first_and_last': [boundaries[0], boundaries[-1]]}))


if __name__ == '__main__':
    try:
        run()
    except BaseException:
        (ROOT / 'FEASIBILITY_FAILURE.txt').write_text(traceback.format_exc())
        raise
