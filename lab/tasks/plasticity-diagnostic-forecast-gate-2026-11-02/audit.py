"""Read-only numerical audit of the saved development forecast pilot.

No predictor refit, new evaluation realization or source acquisition.
"""
import ast
import hashlib
import json
import math
from pathlib import Path
import resource
import sys
import time

import pilot

ROOT = Path(__file__).resolve().parent
READ_BYTES = 0


def read(name):
    global READ_BYTES
    raw = (ROOT / name).read_bytes()
    READ_BYTES += len(raw)
    return json.loads(raw)


def scalar_bias_reference(bias, ys, indices):
    for k in indices:
        bias = (1 - 2 * pilot.STEP) * bias + 2 * pilot.STEP * ys[k]
    return bias


def main():
    global READ_BYTES
    started = time.perf_counter()
    blind = read('BLIND_FORECASTS.json')
    acq = read('ACQUISITION_OUTPUT.json')
    direct = read('DIRECT_FORECASTS.json')
    calibration = read('CALIBRATION.json')
    saved = read('SCORER_CONTINUATION.json')
    theta = saved['mature_theta']
    assert blind['saved_utc'] < direct['saved_utc'] < acq['acquisition_started_utc']
    assert acq['blind_forecast_file_sha256'] == saved['blind_forecast_sha256']
    assert pilot.digest(theta) == blind['mature_state_sha256']
    source = (ROOT / 'pilot.py').read_bytes()
    READ_BYTES += len(source)
    tree = ast.parse(source)
    node = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == 'blind_features')
    names = sorted({n.id for n in ast.walk(node) if isinstance(n, ast.Name)})
    forbidden = set(names) & {'teacher', 'ys', 'tables', 'saved', 'continuation', 'targets', 'future_scores'}
    assert not forbidden, forbidden
    diagnostic_replay = []
    history = [row['outcomes'] for row in calibration]
    all_dead = True
    bias_refs = []
    for branch, forecast in enumerate(blind['forecasts']):
        index = pilot.TASKS + branch
        basic, diag, assay = pilot.blind_features(theta, history, forecast['context'], saved['contexts'][99],
                                                 pilot.TASKS, 900000 + index)
        gap = max(abs(x - y) for x, y in zip(basic + diag, forecast['basic'] + forecast['diagnostic']))
        assert gap < 1e-13, gap
        # Freshly generate diagnostic from permitted arguments only. Changing
        # arbitrary scorer copies cannot affect any of these arguments.
        base = pilot.predict(blind['baseline_model'], basic)
        added = pilot.predict(blind['diagnostic_model'], basic + diag)
        assert base == forecast['baseline_forecast'] and added == forecast['diagnostic_forecast']
        xs, ys = pilot.support(forecast['context']), saved['tables'][index]
        predicted = [pilot.forward(theta, x) for x in xs]
        dead = all(all(h == 0 for h in row[2]) for row in predicted)
        all_dead = all_dead and dead
        diagnostic_replay.append({'branch': branch, 'feature_max_abs_gap': gap,
                                  'dead_fraction': basic[12], 'active_fraction': basic[11],
                                  'hidden_stable_rank': basic[15], 'probe': diag,
                                  'future_input_support_all_hidden_zero': dead})
        if dead:
            expected = scalar_bias_reference(theta[110], ys, saved['fast'][index])
            observed = acq['records'][branch]['final_theta']
            gap_bias = abs(expected - observed[110])
            gap_other = max(abs(a - b) for a, b in zip(theta[:110], observed[:110]))
            expected_mse = sum((expected - y) ** 2 for y in ys) / 32
            gap_risk = abs(expected_mse - acq['records'][branch]['end_mse'])
            assert gap_bias < 1e-11 and gap_other == 0 and gap_risk < 1e-10
            mean_y = sum(ys) / 32
            var_y = sum((y - mean_y) ** 2 for y in ys) / 32
            bias_refs.append({'branch': branch, 'bias_max_abs_gap': gap_bias,
                              'nonbias_parameters_max_abs_change': gap_other,
                              'risk_max_abs_gap': gap_risk, 'teacher_variance': var_y,
                              'squared_bias_to_teacher_mean': (expected - mean_y) ** 2,
                              'risk_equals_variance_plus_bias2_gap':
                                  abs(expected_mse - var_y - (expected - mean_y) ** 2)})
    summaries = acq['forecast_summary']
    wins = sum(d < b for d, b in zip(summaries['diagnostic']['log1p_squared_errors'],
                                    summaries['baseline']['log1p_squared_errors']))
    # Exact finite score arithmetic replay; no inferential resampling of these
    # six branches as if they were six independent learner states.
    arithmetic = {}
    for method, row in summaries.items():
        errors = [(math.log1p(p) - math.log1p(rec['end_mse'])) ** 2
                  for p, rec in zip(row['forecasts_mse'], acq['records'])]
        gap = max(abs(a - b) for a, b in zip(errors, row['log1p_squared_errors']))
        assert gap < 1e-14
        arithmetic[method] = gap
    out = {'utc': pilot.utc(), 'source_sha256': hashlib.sha256(source).hexdigest(),
           'chronology_checks_pass': True, 'blind_interface_forbidden_names': list(forbidden),
           'all_six_feature_forecast_replays': diagnostic_replay,
           'all_mature_future_supports_hidden_dead': all_dead,
           'bias_only_full_60000_update_reference': bias_refs,
           'diagnostic_branches_improved_out_of_six': wins,
           'forecast_score_arithmetic_max_gaps': arithmetic,
           'history_first10_mean_end_mse': sum(r['outcomes']['end'] for r in calibration[:10]) / 10,
           'history_last10_mean_end_mse': sum(r['outcomes']['end'] for r in calibration[-10:]) / 10,
           'last10_input_dead_fractions': [r['basic'][12] for r in calibration[-10:]],
           'future_acquisition': [{k: r[k] for k in ('branch', 'initial_mse', 'end_mse', 'improvement_fraction',
                                                   'target_mean', 'target_variance')} for r in acq['records']],
           'no_new_evaluation_or_predictor_fit': True,
           'explicit_input_bytes': READ_BYTES,
           'total_seconds': time.perf_counter() - started,
           'max_rss_bytes': pilot.rss(), 'physical_io_host_runtime': 'unknown'}
    pilot.save('AUDIT.json', out)
    print(json.dumps(out), flush=True)


if __name__ == '__main__':
    main()
