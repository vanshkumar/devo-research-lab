"""One predeclared original-SCR development acquisition forecast; stdlib only.

Independent float64/Python-RNG source equations, not author Torch execution.
Run phases separately so the target-blind forecast file exists before any
future task-labelled copy or continuing-learner acquisition is executed.
"""
import argparse
import hashlib
import json
import math
from pathlib import Path
import random
import resource
import sys
import time
import traceback

ROOT = Path(__file__).resolve().parent
SOURCE = ROOT.parent / 'plasticity-retention-source-benchmark-2026-11-02'
D, H, PERIOD, TASKS, PROBE_STEPS, BRANCHES = 20, 5, 10000, 100, 2000, 6
STEP, SEED, RIDGE = .003, 271828, 10.0
FEATURE_NAMES = [
    'log_age', 'log_previous_end_mse', 'log_previous_online_mse',
    'log_recent10_online_mse', 'asinh_previous_improvement',
    'slow_context_hamming_fraction', 'input_weight_rms', 'output_weight_rms',
    'output_bias', 'future_prediction_mean', 'future_prediction_variance',
    'future_active_fraction', 'future_dead_fraction', 'hidden_mean',
    'hidden_rms', 'centered_hidden_stable_rank',
]
READ_BYTES = 0


def utc():
    return time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())


def encode(obj):
    return json.dumps(obj, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()


def digest(obj):
    return hashlib.sha256(encode(obj)).hexdigest()


def save(name, obj):
    data = encode(obj)
    (ROOT / name).write_bytes(data + b'\n')
    return hashlib.sha256(data + b'\n').hexdigest()


def read(name):
    global READ_BYTES
    data = (ROOT / name).read_bytes()
    READ_BYTES += len(data)
    return json.loads(data)


def rss():
    # Darwin reports bytes, Linux reports KiB. This workspace is Darwin.
    value = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    return value if sys.platform == 'darwin' else value * 1024


def object_bytes(value):
    if isinstance(value, (list, tuple)):
        return sys.getsizeof(value) + sum(object_bytes(v) for v in value)
    if isinstance(value, dict):
        return sys.getsizeof(value) + sum(object_bytes(k) + object_bytes(v) for k, v in value.items())
    return sys.getsizeof(value)


def support(context):
    return [context + [(fast >> j) & 1 for j in range(5)] for fast in range(32)]


def initialize(rng):
    theta = []
    for _ in range(H):
        theta.extend(rng.uniform(-math.sqrt(6 / D), math.sqrt(6 / D)) for _ in range(D))
        theta.append(0.0)
    theta.extend(rng.uniform(-math.sqrt(3 / H), math.sqrt(3 / H)) for _ in range(H))
    theta.append(0.0)
    return theta


def forward(theta, x):
    z = [theta[j * 21 + 20] + sum(theta[j * 21 + k] * x[k] for k in range(D))
         for j in range(H)]
    h = [max(0.0, v) for v in z]
    pred = theta[110] + sum(theta[105 + j] * h[j] for j in range(H))
    return pred, z, h


def learn(theta, x, target):
    pred, z, h = forward(theta, x)
    err = pred - target
    old_v = theta[105:110]
    for j in range(H):
        if z[j] > 0:
            scale = STEP * 2 * err * old_v[j]
            for k in range(D):
                theta[j * 21 + k] -= scale * x[k]
            theta[j * 21 + 20] -= scale
    for j in range(H):
        theta[105 + j] -= STEP * 2 * err * h[j]
    theta[110] -= STEP * 2 * err
    return err * err


def reference(theta, x, target):
    """Independent nested scalar gradient, all old parameters used at once."""
    w = [theta[j * 21:j * 21 + 20] for j in range(H)]
    b = [theta[j * 21 + 20] for j in range(H)]
    v, c = theta[105:110], theta[110]
    a = [sum(ww * xx for ww, xx in zip(row, x)) + bb for row, bb in zip(w, b)]
    h = [aa if aa > 0 else 0.0 for aa in a]
    r = sum(vv * hh for vv, hh in zip(v, h)) + c - target
    grad = []
    for j in range(H):
        d = 2 * r * v[j] * (a[j] > 0)
        grad.extend(d * xx for xx in x)
        grad.append(d)
    grad.extend(2 * r * hh for hh in h)
    grad.append(2 * r)
    return [old - STEP * g for old, g in zip(theta, grad)], grad


def update_check(theta, x, target, finite_difference=False):
    expected, grad = reference(theta, x, target)
    changed = theta[:]
    learn(changed, x, target)
    error = max(abs(a - b) for a, b in zip(expected, changed))
    assert error < 1e-10, error
    result = {'scalar_max_abs': error, 'parameters': len(theta)}
    if finite_difference and min(abs(v) for v in forward(theta, x)[1]) > 1e-4:
        gaps = []
        for k in range(len(theta)):
            plus, minus = theta[:], theta[:]
            plus[k] += 1e-6
            minus[k] -= 1e-6
            num = ((forward(plus, x)[0] - target) ** 2
                   - (forward(minus, x)[0] - target) ** 2) / 2e-6
            gaps.append(abs(num - grad[k]) / max(1.0, abs(num), abs(grad[k])))
        result['finite_difference_scaled_max'] = max(gaps)
        assert max(gaps) < 2e-6, result
    return result


def teacher_targets(context, teacher):
    w, b, v, c = teacher['w'], teacher['b'], teacher['v'], teacher['c']
    ys = []
    for x in support(context):
        exact = c + sum(v[j] for j in range(100)
                        if 10 * (sum(a * xx for a, xx in zip(w[j], x)) + b[j])
                        > 7 * (D + 1) - 5 * (D - sum(w[j]) + b[j]))
        floating = c + sum(v[j] for j in range(100)
                           if sum(a * xx for a, xx in zip(w[j], x)) + b[j]
                           > .7 * (D + 1) - (D - sum(w[j]) + b[j]) / 2)
        assert exact == floating
        ys.append(exact)
    return ys


def score(theta, xs, ys):
    preds = [forward(theta, x)[0] for x in xs]
    return sum((p - y) ** 2 for p, y in zip(preds, ys)) / len(xs)


def stable_rank(hidden):
    means = [sum(row[j] for row in hidden) / len(hidden) for j in range(H)]
    gram = [[sum((row[j] - means[j]) * (row[k] - means[k]) for row in hidden)
             for k in range(H)] for j in range(H)]
    trace = sum(gram[j][j] for j in range(H))
    if trace < 1e-24:
        return 0.0
    # Positive semidefinite 5x5 Gram; deterministic starts avoid an orthogonal
    # eigenvector initialization. This rank is a cheap baseline, not a result.
    largest = 0.0
    for start in range(H):
        vec = [float(j == start) for j in range(H)]
        for _ in range(40):
            new = [sum(gram[j][k] * vec[k] for k in range(H)) for j in range(H)]
            norm = math.sqrt(sum(a * a for a in new))
            if norm == 0:
                break
            vec = [a / norm for a in new]
        lam = sum(vec[j] * gram[j][k] * vec[k] for j in range(H) for k in range(H))
        largest = max(largest, lam)
    return trace / largest


def blind_features(theta, history, context, previous_context, age, probe_seed):
    """No true teacher, true labels, future SGD RNG or future score argument."""
    before = digest(theta)
    started = time.perf_counter()
    xs = support(context)
    vals = [forward(theta, x) for x in xs]
    preds, hidden = [a[0] for a in vals], [a[2] for a in vals]
    mean = sum(preds) / 32
    previous = history[-1] if history else {'end': 0., 'online': 0., 'initial': 0.}
    recent = history[-10:]
    basic = [
        math.log1p(age), math.log1p(previous['end']), math.log1p(previous['online']),
        math.log1p(sum(a['online'] for a in recent) / len(recent)) if recent else 0.,
        math.asinh(previous['initial'] - previous['end']),
        sum(a != b for a, b in zip(context, previous_context)) / 15,
        math.sqrt(sum(theta[j * 21 + k] ** 2 for j in range(H) for k in range(D)) / 100),
        math.sqrt(sum(v * v for v in theta[105:110]) / H), theta[110], mean,
        sum((p - mean) ** 2 for p in preds) / 32,
        sum(hh > 0 for row in hidden for hh in row) / (32 * H),
        sum(all(row[j] == 0 for row in hidden) for j in range(H)) / H,
        sum(sum(row) for row in hidden) / (32 * H),
        math.sqrt(sum(sum(v * v for v in row) for row in hidden) / (32 * H)),
        stable_rank(hidden),
    ]
    basic_seconds = time.perf_counter() - started
    rng = random.Random(probe_seed)
    random_net = initialize(rng)
    fake_labels = [mean + math.sin(100000 * forward(random_net, x)[0]) for x in xs]
    copied = theta[:]
    initial = score(copied, xs, fake_labels)
    probe_started = time.perf_counter()
    for _ in range(PROBE_STEPS):
        k = rng.randrange(32)
        learn(copied, xs[k], fake_labels[k])
    final = score(copied, xs, fake_labels)
    probe_seconds = time.perf_counter() - probe_started
    assert digest(theta) == before, 'assay mutated continuing learner'
    assert all(math.isfinite(v) for v in basic + [initial, final])
    diagnostic = [(initial - final) / max(initial, 1e-12), final]
    return basic, diagnostic, {
        'probe_seed': probe_seed, 'initial_probe_mse': initial, 'final_probe_mse': final,
        'normalized_removed_mse': diagnostic[0], 'basic_seconds': basic_seconds,
        'probe_seconds': probe_seconds, 'continuing_learner_unchanged': True,
        'probe_label_sha256': digest(fake_labels), 'copied_state_bytes_python': object_bytes(copied),
        'copy_float64_payload_bytes': len(copied) * 8,
    }


def solve(a, b):
    n = len(b)
    rows = [a[i][:] + [b[i]] for i in range(n)]
    for j in range(n):
        pivot = max(range(j, n), key=lambda i: abs(rows[i][j]))
        rows[j], rows[pivot] = rows[pivot], rows[j]
        assert abs(rows[j][j]) > 1e-12
        value = rows[j][j]
        rows[j] = [v / value for v in rows[j]]
        for i in range(n):
            if i != j:
                factor = rows[i][j]
                rows[i] = [x - factor * y for x, y in zip(rows[i], rows[j])]
    return [row[-1] for row in rows]


def fit(rows, targets):
    n, p = len(rows), len(rows[0])
    mean = [sum(row[j] for row in rows) / n for j in range(p)]
    scale = [max(math.sqrt(sum((row[j] - mean[j]) ** 2 for row in rows) / n), 1e-10)
             for j in range(p)]
    design = [[1.0] + [(row[j] - mean[j]) / scale[j] for j in range(p)] for row in rows]
    gram = [[sum(row[j] * row[k] for row in design) + (RIDGE if j == k and j > 0 else 0.)
             for k in range(p + 1)] for j in range(p + 1)]
    rhs = [sum(row[j] * yy for row, yy in zip(design, targets)) for j in range(p + 1)]
    beta = solve(gram, rhs)
    residual = max(abs(sum(gram[j][k] * beta[k] for k in range(p + 1)) - rhs[j])
                   for j in range(p + 1))
    assert residual < 1e-7, residual
    return {'mean': mean, 'scale': scale, 'beta': beta, 'ridge': RIDGE,
            'normal_equation_max_abs_residual': residual, 'calibration_n': n}


def predict(model, row):
    standardized = [(x - m) / s for x, m, s in zip(row, model['mean'], model['scale'])]
    z = model['beta'][0] + sum(b * x for b, x in zip(model['beta'][1:], standardized))
    return {'log1p_mse': z, 'mse': max(0.0, math.expm1(z))}


def source_audit():
    global READ_BYTES
    raw = (SOURCE / 'SOURCE_MANIFEST.json').read_bytes()
    READ_BYTES += len(raw)
    manifest = json.loads(raw)
    files = []
    for item in manifest['files']:
        data = (SOURCE / 'vendor' / item['path']).read_bytes()
        READ_BYTES += len(data)
        blob = hashlib.sha1(b'blob ' + str(len(data)).encode() + b'\0' + data).hexdigest()
        assert blob == item['blob_sha1'], item['path']
        files.append({'path': item['path'], 'bytes': len(data), 'git_blob': blob,
                      'sha256': hashlib.sha256(data).hexdigest()})
    return {'commit': manifest['commit'], 'root_tree': manifest['actual_root_tree'],
            'license': manifest['license'], 'files': files}


def prepare():
    started = time.perf_counter()
    pins = source_audit()
    rng = random.Random(SEED)
    sign = lambda: 2 * rng.randrange(2) - 1
    teacher = {'w': [[sign() for _ in range(D)] for _ in range(100)],
               'b': [sign() for _ in range(100)], 'v': [sign() for _ in range(100)], 'c': sign()}
    # Match the source's unused extra full block. Six branches use contexts
    # 100..105; context 106 and its 10k indices are generated/exposed unused.
    contexts = [[rng.randrange(2) for _ in range(15)] for _ in range(TASKS + BRANCHES + 1)]
    fast = [[rng.randrange(32) for _ in range(PERIOD)] for _ in contexts]
    tables = [teacher_targets(context, teacher) for context in contexts]
    theta = initialize(rng)
    initial_theta = theta[:]
    history, calibration, refs = [], [], []
    total_training_seconds, total_probe_seconds = 0.0, 0.0
    for task in range(TASKS):
        context, xs, ys = contexts[task], support(contexts[task]), tables[task]
        basic, diag, assay = blind_features(theta, history, context,
                                           contexts[task - 1] if task else context,
                                           task, 900000 + task)
        total_probe_seconds += assay['probe_seconds']
        initial = score(theta, xs, ys)
        losses = []
        t0 = time.perf_counter()
        for i, k in enumerate(fast[task]):
            if (task, i) in {(0, 0), (0, 9999), (49, 9999), (99, 9999)}:
                refs.append({'task': task, 'update': i,
                             **update_check(theta, xs[k], ys[k], True)})
            losses.append(learn(theta, xs[k], ys[k]))
        total_training_seconds += time.perf_counter() - t0
        end = score(theta, xs, ys)
        assert all(math.isfinite(v) for v in theta + losses)
        row = {'task': task, 'initial': initial, 'end': end,
               'online': sum(losses) / PERIOD, 'last1000_online': sum(losses[-1000:]) / 1000}
        history.append(row)
        calibration.append({'task': task, 'basic': basic, 'diagnostic': diag, 'assay': assay,
                            'target_log1p_end_mse': math.log1p(end), 'outcomes': row})
        if task in (0, 49, 99):
            print(json.dumps({'phase': 'prepare', 'task_complete': task, 'end_mse': end,
                              'elapsed_seconds': time.perf_counter() - started}), flush=True)
    selected = calibration[10:100]
    targets = [row['target_log1p_end_mse'] for row in selected]
    base = fit([row['basic'] for row in selected], targets)
    added = fit([row['basic'] + row['diagnostic'] for row in selected], targets)
    frozen_state = digest(theta)
    future = []
    for branch in range(BRANCHES):
        index = TASKS + branch
        basic, diag, assay = blind_features(theta, history, contexts[index], contexts[99],
                                           TASKS, 900000 + index)
        total_probe_seconds += assay['probe_seconds']
        future.append({'branch': branch, 'context': contexts[index],
                       'basic': basic, 'diagnostic': diag, 'assay': assay,
                       'baseline_forecast': predict(base, basic),
                       'diagnostic_forecast': predict(added, basic + diag),
                       'recent10_persistence_mse': sum(row['end'] for row in history[-10:]) / 10})
    assert digest(theta) == frozen_state
    forecast = {
        'saved_utc': utc(), 'kind': 'target_blind_before_any_future_task_probe_or_continuation',
        'source': pins, 'seed': SEED, 'history_updates': TASKS * PERIOD,
        'source_equation_not_author_torch': True,
        'config': {'D': D, 'H': H, 'period': PERIOD, 'step': STEP, 'probe_steps': PROBE_STEPS},
        'feature_names': FEATURE_NAMES,
        'added_feature_names': ['probe_fraction_removed', 'probe_final_mse'],
        'mature_state_sha256': frozen_state, 'mature_state': theta,
        'calibration_tasks': [10, 99], 'baseline_model': base, 'diagnostic_model': added,
        'forecasts': future, 'continuing_or_copy_future_true_label_updates': 0,
        'future_acquisition_scores_computed': 0,
        'blind_feature_interface': ['theta', 'past_history', 'context', 'previous_context', 'age', 'probe_seed'],
    }
    forecast_sha = save('BLIND_FORECASTS.json', forecast)
    save('CALIBRATION.json', calibration)
    # Scorer continuation is persisted only AFTER blind forecasts exist.
    continuation = {'teacher': teacher, 'contexts': contexts, 'fast': fast,
                    'tables': tables, 'initial_theta': initial_theta,
                    'mature_theta': theta, 'blind_forecast_sha256': forecast_sha}
    save('SCORER_CONTINUATION.json', continuation)
    output = {'phase': 'prepare', 'utc': utc(), 'forecast_sha256': forecast_sha,
              'history_updates': TASKS * PERIOD, 'true_future_updates': 0,
              'sine_probe_updates': (TASKS + BRANCHES) * PROBE_STEPS,
              'teacher_reference_checks': len(contexts) * 32, 'scalar_references': refs,
              'training_seconds': total_training_seconds, 'probe_seconds': total_probe_seconds,
              'total_seconds': time.perf_counter() - started, 'max_rss_bytes': rss(),
              'explicit_input_bytes_this_phase': READ_BYTES,
              'generated_fast_indices': len(contexts) * PERIOD,
              'unused_extra_block_fast_indices': PERIOD,
              'float64_state_payload_bytes': 111 * 8,
              'python_state_bytes': object_bytes(theta),
              'all_future_blind_forecasts_saved_before_task_labelled_copy': True,
              'jobs_at_phase_return': 0,
              'python': sys.version, 'parallelism': 'one process, native Python thread only',
              'provider_host_rss_native_runtime_physical_io': 'unknown'}
    save('PREPARE_OUTPUT.json', output)
    print(json.dumps(output), flush=True)


def direct():
    started = time.perf_counter()
    forecasts, saved = read('BLIND_FORECASTS.json'), read('SCORER_CONTINUATION.json')
    file_sha = hashlib.sha256((ROOT / 'BLIND_FORECASTS.json').read_bytes()).hexdigest()
    assert file_sha == saved['blind_forecast_sha256']
    theta = saved['mature_theta']
    assert digest(theta) == forecasts['mature_state_sha256']
    outputs = []
    for branch in range(BRANCHES):
        j = TASKS + branch
        xs, ys = support(saved['contexts'][j]), saved['tables'][j]
        copied = theta[:]
        t0 = time.perf_counter()
        for k in saved['fast'][j][:PROBE_STEPS]:
            learn(copied, xs[k], ys[k])
        mse = score(copied, xs, ys)
        assert digest(theta) == forecasts['mature_state_sha256']
        outputs.append({'branch': branch, 'forecast_mse': mse, 'forecast_log1p_mse': math.log1p(mse),
                        'updates': PROBE_STEPS, 'up_to_32_distinct_target_labels': 32,
                        'training_label_presentations': PROBE_STEPS,
                        'additional_full_support_score_presentations': 32,
                        'seconds': time.perf_counter() - t0,
                        'copy_state_sha256': digest(copied), 'copy_state': copied})
    record = {'saved_utc': utc(), 'kind': 'privileged_task_labelled_copy_current_loss_reference',
              'blind_forecast_sha256': file_sha, 'continuing_learner_future_updates': 0,
              'continuer_state_sha256': digest(theta), 'forecasts': outputs,
              'total_seconds': time.perf_counter() - started, 'max_rss_bytes': rss(),
              'explicit_input_bytes_this_phase': READ_BYTES}
    save('DIRECT_FORECASTS.json', record)
    print(json.dumps({k: v for k, v in record.items() if k != 'forecasts'}), flush=True)


def acquire():
    started = time.perf_counter()
    blind, direct_record, saved = read('BLIND_FORECASTS.json'), read('DIRECT_FORECASTS.json'), read('SCORER_CONTINUATION.json')
    blind_sha = hashlib.sha256((ROOT / 'BLIND_FORECASTS.json').read_bytes()).hexdigest()
    direct_sha = hashlib.sha256((ROOT / 'DIRECT_FORECASTS.json').read_bytes()).hexdigest()
    assert blind_sha == saved['blind_forecast_sha256'] == direct_record['blind_forecast_sha256']
    assert digest(saved['mature_theta']) == blind['mature_state_sha256']
    records, refs = [], []
    acquisition_started = utc()
    for branch in range(BRANCHES):
        j = TASKS + branch
        theta = saved['mature_theta'][:]
        xs, ys = support(saved['contexts'][j]), saved['tables'][j]
        initial = score(theta, xs, ys)
        losses, checkpoints = [], []
        branch_start = utc()
        for i, k in enumerate(saved['fast'][j]):
            if i in (0, 9999):
                refs.append({'branch': branch, 'update': i,
                             **update_check(theta, xs[k], ys[k], finite_difference=(i == 0))})
            losses.append(learn(theta, xs[k], ys[k]))
            if i in (1999, 9999):
                checkpoints.append({'updates': i + 1, 'mse': score(theta, xs, ys), 'state_sha256': digest(theta)})
        assert checkpoints[0]['state_sha256'] == direct_record['forecasts'][branch]['copy_state_sha256']
        end = checkpoints[-1]['mse']
        mean_y = sum(ys) / 32
        variance_y = sum((y - mean_y) ** 2 for y in ys) / 32
        records.append({'branch': branch, 'started_utc': branch_start,
                        'initial_mse': initial, 'end_mse': end, 'target_log1p_mse': math.log1p(end),
                        'improvement_fraction': (initial - end) / max(initial, 1e-12),
                        'target_mean': mean_y, 'target_variance': variance_y,
                        'online_mse': sum(losses) / PERIOD,
                        'last1000_online_mse': sum(losses[-1000:]) / 1000,
                        'checkpoints': checkpoints, 'final_theta': theta})
    summary = {}
    for method in ('baseline', 'diagnostic', 'recent10_persistence', 'direct'):
        if method in ('baseline', 'diagnostic'):
            values = [f[method + '_forecast']['mse'] for f in blind['forecasts']]
        elif method == 'direct':
            values = [f['forecast_mse'] for f in direct_record['forecasts']]
        else:
            values = [f['recent10_persistence_mse'] for f in blind['forecasts']]
        errors = [(math.log1p(p) - r['target_log1p_mse']) ** 2 for p, r in zip(values, records)]
        summary[method] = {'forecasts_mse': values, 'log1p_squared_errors': errors,
                           'mean_log1p_squared_error': sum(errors) / BRANCHES,
                           'mse_scale_mae': sum(abs(p - r['end_mse']) for p, r in zip(values, records)) / BRANCHES}
    base_error = summary['baseline']['mean_log1p_squared_error']
    diag_error = summary['diagnostic']['mean_log1p_squared_error']
    output = {'phase': 'acquire', 'utc': utc(), 'acquisition_started_utc': acquisition_started,
              'blind_forecast_saved_utc': blind['saved_utc'], 'direct_forecast_saved_utc': direct_record['saved_utc'],
              'blind_forecast_file_sha256': blind_sha, 'direct_forecast_file_sha256': direct_sha,
              'baseline_relative_diagnostic_improvement': (base_error - diag_error) / base_error,
              'records': records, 'forecast_summary': summary, 'scalar_references': refs,
              'mature_state_unmodified': digest(saved['mature_theta']) == blind['mature_state_sha256'],
              'direct_2000_state_matches_continuer_all_six': True,
              'continuing_future_updates': BRANCHES * PERIOD,
              'total_seconds': time.perf_counter() - started, 'max_rss_bytes': rss(),
              'explicit_input_bytes_this_phase': READ_BYTES,
              'independent_learners': 1, 'branches_not_independent_learners': BRANCHES,
              'uncertainty': 'development feasibility only; no independent-unit interval or significance claim',
              'jobs_at_phase_return': 0}
    save('ACQUISITION_OUTPUT.json', output)
    print(json.dumps({k: v for k, v in output.items() if k not in ('records', 'scalar_references')}), flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('phase', choices=['prepare', 'direct', 'acquire'])
    args = parser.parse_args()
    try:
        globals()[args.phase]()
    except BaseException:
        (ROOT / ('FAILURE_' + args.phase + '.txt')).write_text(traceback.format_exc())
        raise
