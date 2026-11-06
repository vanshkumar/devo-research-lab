"""Fixed original-SCR paired-state development pilot. No old numerical reads.

Three explicit phases enforce saved blind/direct forecasts before acquisition.
Only standard-library Python; one process/thread. See PILOT_PLAN.md.
"""
import argparse
import hashlib
import importlib.util
import json
import math
from pathlib import Path
import random
import resource
import sys
import time
import traceback

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parent
CORE_PATH = ROOT.parent / 'plasticity-diagnostic-forecast-gate-2026-11-02/pilot.py'
spec = importlib.util.spec_from_file_location('equation_helpers', CORE_PATH)
core = importlib.util.module_from_spec(spec)
spec.loader.exec_module(core)  # definitions only; no old states/calibration/results read
SEEDS = [202611021, 202611022, 202611023, 202611024]
CAL = set(range(10, 100, 10))
D, H, PERIOD, NPROBES, PSTEPS, COPY_STEPS = 20, 5, 10000, 10, 2000, 20000
READ_BYTES = len(CORE_PATH.read_bytes())


def utc():
    return time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())


def encode(obj):
    return json.dumps(obj, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()


def digest(obj):
    return hashlib.sha256(encode(obj)).hexdigest()


def save(name, obj):
    raw = encode(obj) + b'\n'
    (ROOT / name).write_bytes(raw)
    return hashlib.sha256(raw).hexdigest()


def read(name):
    global READ_BYTES
    raw = (ROOT / name).read_bytes()
    READ_BYTES += len(raw)
    return json.loads(raw)


def rss():
    z = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    return z if sys.platform == 'darwin' else 1024 * z


def scalar_forward(theta, x):
    layers = [theta[j * 21:j * 21 + 20] for j in range(5)]
    biases = [theta[j * 21 + 20] for j in range(5)]
    acts = [max(0., sum(w * v for w, v in zip(row, x)) + b)
            for row, b in zip(layers, biases)]
    return sum(v * h for v, h in zip(theta[105:110], acts)) + theta[110]


def scalar_step(theta, x, y):
    layers = [theta[j * 21:j * 21 + 20] for j in range(5)]
    biases = [theta[j * 21 + 20] for j in range(5)]
    v, bias = theta[105:110], theta[110]
    pre = [sum(a * b for a, b in zip(row, x)) + bj for row, bj in zip(layers, biases)]
    h = [max(0., a) for a in pre]
    e = sum(a * b for a, b in zip(v, h)) + bias - y
    grad = []
    for j, row in enumerate(layers):
        back = 2 * e * v[j] * (pre[j] > 0.)
        grad.extend(back * xx for xx in x)
        grad.append(back)
    grad.extend(2 * e * hh for hh in h)
    grad.append(2 * e)
    return [old - .003 * g for old, g in zip(theta, grad)], grad


def scalar_risk(theta, xs, ys):
    return sum((scalar_forward(theta, x) - y) ** 2 for x, y in zip(xs, ys)) / len(xs)


def reference_check(theta, x, y, finite_difference=False):
    expected, grad = scalar_step(theta, x, y)
    actual = theta[:]
    core.learn(actual, x, y)
    gap = max(abs(a - b) for a, b in zip(actual, expected))
    assert gap < 1e-9, gap
    out = {'step_max_abs': gap, 'n_parameters': 111}
    if finite_difference and min(abs(z) for z in core.forward(theta, x)[1]) > 1e-4:
        errs = []
        for k in range(111):
            a, b = theta[:], theta[:]
            a[k] += 1e-6
            b[k] -= 1e-6
            numeric = ((scalar_forward(a, x) - y) ** 2 - (scalar_forward(b, x) - y) ** 2) / 2e-6
            errs.append(abs(numeric - grad[k]) / max(1., abs(numeric), abs(grad[k])))
        out['finite_difference_scaled_max'] = max(errs)
        assert max(errs) < 2e-6, out
    return out


def basic(theta, history, context, previous_context, age):
    """Only current parameters, known inputs and completed past history."""
    vals = [core.forward(theta, x) for x in core.support(context)]
    p, h = [v[0] for v in vals], [v[2] for v in vals]
    mean = sum(p) / 32
    previous = history[-1] if history else {'end': 0., 'online': 0., 'initial': 0.}
    recent = history[-10:]
    return [math.log1p(age), math.log1p(previous['end']), math.log1p(previous['online']),
            math.log1p(sum(r['online'] for r in recent) / len(recent)) if recent else 0.,
            math.asinh(previous['initial'] - previous['end']),
            sum(a != b for a, b in zip(context, previous_context)) / 15,
            math.sqrt(sum(theta[j * 21 + k] ** 2 for j in range(5) for k in range(20)) / 100),
            math.sqrt(sum(v * v for v in theta[105:110]) / 5), theta[110], mean,
            sum((v - mean) ** 2 for v in p) / 32,
            sum(v > 0 for row in h for v in row) / 160,
            sum(all(row[j] == 0 for row in h) for j in range(5)) / 5,
            sum(sum(row) for row in h) / 160,
            math.sqrt(sum(sum(v * v for v in row) for row in h) / 160),
            core.stable_rank(h)]


def random_assay(theta, xs, seed):
    """TEN independent source-inspired random functions; no true y argument."""
    before = digest(theta)
    offset = sum(core.forward(theta, x)[0] for x in xs) / 32
    rows = []
    for k in range(NPROBES):
        rng = random.Random(seed + k * 100003)
        net = core.initialize(rng)
        ys = [offset + math.sin(100000 * core.forward(net, x)[0]) for x in xs]
        copied = theta[:]
        initial = core.score(copied, xs, ys)
        t0 = time.perf_counter()
        for _ in range(PSTEPS):
            index = rng.randrange(32)
            core.learn(copied, xs[index], ys[index])
        final = core.score(copied, xs, ys)
        rows.append({'replicate': k, 'seed': seed + k * 100003, 'initial': initial,
                     'final': final, 'removed_fraction': (initial - final) / max(initial, 1e-12),
                     'seconds': time.perf_counter() - t0, 'label_hash': digest(ys)})
    assert digest(theta) == before
    features = [sum(math.log1p(r['final']) for r in rows) / NPROBES,
                sum(r['removed_fraction'] for r in rows) / NPROBES]
    return features, rows


def labelled_copy(theta, xs, ys, seed):
    before = digest(theta)
    copied = theta[:]
    rng = random.Random(seed)
    prefix = {'0': core.score(copied, xs, ys)}
    t0 = time.perf_counter()
    for i in range(COPY_STEPS):
        index = rng.randrange(32)
        core.learn(copied, xs[index], ys[index])
        if i + 1 in (2000, 10000, 20000):
            prefix[str(i + 1)] = core.score(copied, xs, ys)
    assert digest(theta) == before
    return [math.log1p(prefix[str(i)]) for i in (0, 2000, 10000, 20000)], {
        'prefix_mse': prefix, 'copy_steps': COPY_STEPS, 'unique_true_support_labels': 32,
        'independent_probe_seed': seed, 'seconds': time.perf_counter() - t0,
        'continuing_unchanged': True, 'end_state_hash': digest(copied)}


def difference(rows):
    return [a - b for a, b in zip(rows[0], rows[1])]


def paired_fit(rows, target):
    # Reversing pair orientation has reversed response; no arbitrary A advantage.
    xx = rows + [[-x for x in row] for row in rows]
    yy = target + [-y for y in target]
    return core.fit(xx, yy)


def paired_predict(model, row):
    # Signed log-risk difference can be negative, so do not call expm1 helper.
    return model['beta'][0] + sum(b * (x - m) / s for b, x, m, s
                                 in zip(model['beta'][1:], row, model['mean'], model['scale']))


def timed_run(theta, xs, ys, fast, checks=None):
    initial = core.score(theta, xs, ys)
    total, last = 0., 0.
    t0 = time.perf_counter()
    for i, k in enumerate(fast):
        if checks is not None and i in (0, 9999):
            checks.append(reference_check(theta, xs[k], ys[k], True))
        loss = core.learn(theta, xs[k], ys[k])
        total += loss
        if i >= 9000:
            last += loss
    assert all(math.isfinite(v) for v in theta)
    return {'initial': initial, 'end': core.score(theta, xs, ys),
            'online': total / len(fast), 'last1000_online': last / 1000,
            'seconds': time.perf_counter() - t0}


def prepare():
    started = time.perf_counter()
    source = core.source_audit()
    calibration, units, refs = [], [], []
    costs = {'history_steps': 0, 'calibration_assay_steps': 0, 'calibration_copy_steps': 0,
             'future_assay_steps': 0, 'training_seconds': 0., 'assay_seconds': 0., 'copy_seconds': 0.}
    for u, seed in enumerate(SEEDS):
        rng = random.Random(seed)
        sign = lambda: 2 * rng.randrange(2) - 1
        teacher = {'w': [[sign() for _ in range(20)] for _ in range(100)],
                   'b': [sign() for _ in range(100)], 'v': [sign() for _ in range(100)], 'c': sign()}
        contexts = [[rng.randrange(2) for _ in range(15)] for _ in range(102)]
        # Exact 100-task histories, plus next task and original extra complete block.
        fast = [[rng.randrange(32) for _ in range(10000)] for _ in contexts]
        tables = [core.teacher_targets(c, teacher) for c in contexts[:100]]
        states = [core.initialize(random.Random(202611100 + 2 * u + j)) for j in range(2)]
        initial_states = [s[:] for s in states]
        histories = [[], []]
        for task in range(100):
            xs, ys = core.support(contexts[task]), tables[task]
            cal = {'unit': u, 'task': task, 'basic': [], 'assay': [], 'replicates': [],
                   'copy': [], 'copy_details': [], 'outcomes': []} if task in CAL else None
            for j in range(2):
                theta = states[j]
                if cal is not None:
                    cal['basic'].append(basic(theta, histories[j], contexts[task], contexts[task - 1], task))
                    t0 = time.perf_counter()
                    f, rr = random_assay(theta, xs, 31000000 + u * 10000 + task * 10)
                    costs['assay_seconds'] += time.perf_counter() - t0
                    costs['calibration_assay_steps'] += 20000
                    cal['assay'].append(f)
                    cal['replicates'].append(rr)
                    f, detail = labelled_copy(theta, xs, ys, 41000000 + u * 10000 + task * 10)
                    cal['copy'].append(f)
                    cal['copy_details'].append(detail)
                    costs['copy_seconds'] += detail['seconds']
                    costs['calibration_copy_steps'] += COPY_STEPS
                checks = refs if task in (0, 49, 99) else None
                result = timed_run(theta, xs, ys, fast[task], checks)
                histories[j].append(result)
                costs['history_steps'] += 10000
                costs['training_seconds'] += result['seconds']
                if cal is not None:
                    cal['outcomes'].append(result)
            if cal is not None:
                cal['target_delta'] = math.log1p(cal['outcomes'][0]['end']) - math.log1p(cal['outcomes'][1]['end'])
                calibration.append(cal)
        units.append({'unit': u, 'seed': seed, 'teacher': teacher, 'contexts': contexts,
                      'history_input_hash': digest(fast[:100]), 'future_fast': fast[100],
                      'unused_extra_fast': fast[101], 'initial_states': initial_states,
                      'states': states, 'histories': histories})
        print(json.dumps({'phase': 'prepare', 'unit_completed': u, 'history_steps': costs['history_steps'],
                          'elapsed_seconds': time.perf_counter() - started}), flush=True)
    yy = [r['target_delta'] for r in calibration]
    baseline = paired_fit([difference(r['basic']) for r in calibration], yy)
    added = paired_fit([difference(r['basic']) + difference(r['assay']) for r in calibration], yy)
    initial = paired_fit([[difference(r['copy'])[0]] for r in calibration], yy)
    direct = paired_fit([difference(r['basic']) + difference(r['copy']) for r in calibration], yy)
    forecasts = []
    for unit in units:
        u = unit['unit']
        context = unit['contexts'][100]
        row = {'unit': u, 'context': context, 'basic': [], 'assay': [], 'replicates': [],
               'states_sha256': [digest(s) for s in unit['states']]}
        for j in range(2):
            theta = unit['states'][j]
            row['basic'].append(basic(theta, unit['histories'][j], context, unit['contexts'][99], 100))
            t0 = time.perf_counter()
            f, rr = random_assay(theta, core.support(context), 31000000 + u * 10000 + 1000)
            costs['assay_seconds'] += time.perf_counter() - t0
            costs['future_assay_steps'] += 20000
            row['assay'].append(f)
            row['replicates'].append(rr)
        row['baseline_delta_forecast'] = paired_predict(baseline, difference(row['basic']))
        row['assay_delta_forecast'] = paired_predict(added, difference(row['basic']) + difference(row['assay']))
        # Forecast variation if one of ten functions had been used; fixed fitted model.
        row['single_function_delta_forecasts'] = []
        for k in range(10):
            dd = [math.log1p(row['replicates'][0][k]['final']) - math.log1p(row['replicates'][1][k]['final']),
                  row['replicates'][0][k]['removed_fraction'] - row['replicates'][1][k]['removed_fraction']]
            row['single_function_delta_forecasts'].append(paired_predict(added, difference(row['basic']) + dd))
        forecasts.append(row)
    report = {'utc': utc(), 'source': source, 'helper_code_sha256': hashlib.sha256(CORE_PATH.read_bytes()).hexdigest(),
              'history_updates': costs['history_steps'], 'independent_units': 4, 'states_per_unit': 2,
              'baseline_model': baseline, 'assay_model': added, 'initial_model': initial, 'direct_model': direct,
              'feature_names': core.FEATURE_NAMES, 'calibration_pairs': len(calibration),
              'forecast_interface': ['states', 'completed_history', 'announced_context', 'independent_probe_seed'],
              'true_future_label_updates': 0, 'future_acquisition_scores_computed': 0,
              'forecasts': forecasts, 'costs': costs}
    blind_hash = save('BLIND_FORECASTS.json', report)
    save('CALIBRATION.json', calibration)
    save('SCORER_CONTINUATION.json', {'units': units, 'blind_hash': blind_hash})
    out = {'phase': 'prepare', 'utc': utc(), 'blind_hash': blind_hash, 'references': refs,
           'source_support_labels_verified': 4 * 100 * 32, 'costs': costs,
           'seconds': time.perf_counter() - started, 'rss_bytes': rss(),
           'explicit_read_bytes': READ_BYTES + core.READ_BYTES}
    save('PREPARE_OUTPUT.json', out)
    print(json.dumps(out), flush=True)


def direct():
    started = time.perf_counter()
    blind = read('BLIND_FORECASTS.json')
    continuation = read('SCORER_CONTINUATION.json')
    assert continuation['blind_hash'] == hashlib.sha256((ROOT / 'BLIND_FORECASTS.json').read_bytes()).hexdigest()
    forecasts = []
    for unit, br in zip(continuation['units'], blind['forecasts']):
        u = unit['unit']
        xs = core.support(unit['contexts'][100])
        ys = core.teacher_targets(unit['contexts'][100], unit['teacher'])
        feats, details = [], []
        for j in range(2):
            assert digest(unit['states'][j]) == br['states_sha256'][j]
            f, detail = labelled_copy(unit['states'][j], xs, ys, 41000000 + u * 10000 + 1000)
            feats.append(f)
            details.append(detail)
        diff = difference(feats)
        forecasts.append({'unit': u, 'copy_features': feats, 'copies': details,
                          'label_table': ys, 'initial_delta_forecast': paired_predict(blind['initial_model'], [diff[0]]),
                          'copy_delta_forecast': paired_predict(blind['direct_model'], difference(br['basic']) + diff)})
    out = {'utc': utc(), 'blind_hash': continuation['blind_hash'], 'forecasts': forecasts,
           'actual_future_acquisition_updates': 0, 'copy_steps': 4 * 2 * COPY_STEPS,
           'unique_future_support_labels': 4 * 32, 'source_support_labels_verified': 128,
           'seconds': time.perf_counter() - started, 'rss_bytes': rss(), 'explicit_read_bytes': READ_BYTES}
    sha = save('DIRECT_FORECASTS.json', out)
    print(json.dumps({'phase': 'direct', 'forecast_hash': sha, 'seconds': out['seconds'], 'rss_bytes': out['rss_bytes']}), flush=True)


def acquire():
    started = time.perf_counter()
    blind = read('BLIND_FORECASTS.json')
    direct = read('DIRECT_FORECASTS.json')
    continuation = read('SCORER_CONTINUATION.json')
    results = []
    for unit, br, dr in zip(continuation['units'], blind['forecasts'], direct['forecasts']):
        xs, ys, fast = core.support(unit['contexts'][100]), dr['label_table'], unit['future_fast']
        outcomes, refs = [], []
        for j in range(2):
            theta = unit['states'][j][:]
            assert digest(theta) == br['states_sha256'][j]
            reference = theta[:]
            initial = core.score(theta, xs, ys)
            max_gap = 0.
            for k in fast:
                core.learn(theta, xs[k], ys[k])
                reference, _ = scalar_step(reference, xs[k], ys[k])
                gap = max(abs(a - b) for a, b in zip(theta, reference))
                max_gap = max(max_gap, gap)
            end = core.score(theta, xs, ys)
            end_ref = scalar_risk(reference, xs, ys)
            assert max_gap < 1e-6, max_gap
            assert abs(end - end_ref) < 1e-6, (end, end_ref)
            outcomes.append({'initial_mse': initial, 'final_mse': end, 'reference_mse': end_ref,
                             'fraction_removed': (initial - end) / max(initial, 1e-12),
                             'final_state': theta, 'final_state_hash': digest(theta)})
            refs.append({'updates': len(fast), 'max_parameter_gap_over_entire_trajectory': max_gap,
                         'final_risk_gap': abs(end - end_ref)})
        target = math.log1p(outcomes[0]['final_mse']) - math.log1p(outcomes[1]['final_mse'])
        preds = {'baseline': br['baseline_delta_forecast'], 'assay': br['assay_delta_forecast'],
                 'initial_competence': dr['initial_delta_forecast'], 'calibrated_copy': dr['copy_delta_forecast']}
        lower = min(o['final_mse'] for o in outcomes)
        scored = {name: {'prediction': value, 'squared_delta_error': (value - target) ** 2,
                         'selected_state': int(value > 0),
                         'selection_regret_mse': outcomes[int(value > 0)]['final_mse'] - lower,
                         'correct_ranking': ((value > 0) == (target > 0))}
                  for name, value in preds.items()}
        mean = sum(ys) / 32
        results.append({'unit': unit['unit'], 'outcomes': outcomes, 'reference': refs,
                        'target_delta': target, 'forecasts_and_scores': scored,
                        'teacher_variance': sum((y - mean) ** 2 for y in ys) / 32,
                        'task_and_actual_draws_identical_within_pair': True,
                        'future_input_hash': digest(fast),
                        'initial_competence_best_state': int(outcomes[1]['initial_mse'] < outcomes[0]['initial_mse']),
                        'final_best_state': int(target > 0)})
        print(json.dumps({'phase': 'acquire', 'unit': unit['unit'], 'target_delta': target,
                          'final_mse': [o['final_mse'] for o in outcomes]}), flush=True)
    summary = {}
    for name in ('baseline', 'assay', 'initial_competence', 'calibrated_copy'):
        summary[name] = {'mean_squared_paired_logrisk_error': sum(r['forecasts_and_scores'][name]['squared_delta_error'] for r in results) / 4,
                         'mean_selection_regret_mse': sum(r['forecasts_and_scores'][name]['selection_regret_mse'] for r in results) / 4,
                         'correct_rankings': sum(r['forecasts_and_scores'][name]['correct_ranking'] for r in results)}
    out = {'utc': utc(), 'blind_hash': continuation['blind_hash'],
           'direct_hash': hashlib.sha256((ROOT / 'DIRECT_FORECASTS.json').read_bytes()).hexdigest(),
           'results': results, 'summary': summary, 'actual_acquisition_updates': 80000,
           'independently_expressed_full_trajectory_updates': 80000,
           'seconds': time.perf_counter() - started, 'rss_bytes': rss(), 'explicit_read_bytes': READ_BYTES,
           'independent_units': 4, 'status': 'development_only_no_population_or_novelty_claim'}
    save('ACQUISITION_OUTPUT.json', out)
    print(json.dumps({'phase': 'acquire_complete', 'summary': summary, 'seconds': out['seconds'], 'rss_bytes': out['rss_bytes']}), flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('phase', choices=('prepare', 'direct', 'acquire'))
    args = parser.parse_args()
    try:
        globals()[args.phase]()
    except BaseException:
        save('FAILURE_' + args.phase.upper() + '.json', {'utc': utc(), 'traceback': traceback.format_exc(),
             'rss_bytes': rss(), 'explicit_read_bytes': READ_BYTES})
        raise
