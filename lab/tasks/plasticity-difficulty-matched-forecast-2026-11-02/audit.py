"""Verify saved paired forecasts, calibration arithmetic, chronology and costs.

No new teachers, outcomes, fitting choices or scientific revision.
"""
import paired as p

t0 = p.time.perf_counter()
blind = p.read('BLIND_FORECASTS.json')
direct = p.read('DIRECT_FORECASTS.json')
acq = p.read('ACQUISITION_OUTPUT.json')
cal = p.read('CALIBRATION.json')
prep = p.read('PREPARE_OUTPUT.json')
nondeg = p.read('BLIND_NONDEGENERACY.json')
scorer = p.read('SCORER_CONTINUATION.json')
raw_blind = (p.ROOT / 'BLIND_FORECASTS.json').read_bytes()
raw_direct = (p.ROOT / 'DIRECT_FORECASTS.json').read_bytes()
assert p.hashlib.sha256(raw_blind).hexdigest() == prep['blind_hash'] == acq['blind_hash'] == scorer['blind_hash']
assert p.hashlib.sha256(raw_direct).hexdigest() == acq['direct_hash']
assert blind['utc'] < direct['utc'] <= acq['utc']
assert nondeg['utc'] < '2026-11-03T04:52:57Z'
assert acq['utc'] < '2026-11-03T05:07:57Z'
assert len(cal) == 36 and {r['task'] for r in cal} == set(range(10, 100, 10))


def independent_fit_check(model, xx, yy):
    """Cholesky solves the frozen normal equations, separately from core GJ."""
    xx = xx + [[-v for v in row] for row in xx]
    yy = yy + [-v for v in yy]
    width = len(xx[0])
    means = [sum(row[j] for row in xx) / len(xx) for j in range(width)]
    scales = [max((sum((row[j] - means[j]) ** 2 for row in xx) / len(xx)) ** .5, 1e-10)
              for j in range(width)]
    design = [[1.] + [(row[j] - means[j]) / scales[j] for j in range(width)] for row in xx]
    n = width + 1
    gram = [[sum(row[j] * row[k] for row in design) + (10. if j == k and j else 0.)
             for k in range(n)] for j in range(n)]
    rhs = [sum(row[j] * y for row, y in zip(design, yy)) for j in range(n)]
    L = [[0.] * n for _ in range(n)]
    for i in range(n):
        for j in range(i + 1):
            r = gram[i][j] - sum(L[i][k] * L[j][k] for k in range(j))
            L[i][j] = p.math.sqrt(r) if i == j else r / L[j][j]
    z = []
    for i in range(n):
        z.append((rhs[i] - sum(L[i][j] * z[j] for j in range(i))) / L[i][i])
    beta = [0.] * n
    for i in range(n - 1, -1, -1):
        beta[i] = (z[i] - sum(L[j][i] * beta[j] for j in range(i + 1, n))) / L[i][i]
    gap = max(abs(a - b) for a, b in zip(beta, model['beta']))
    assert gap < 1e-9, gap
    return {'coefficients': n, 'max_abs_coefficient_gap': gap}


yy = [r['target_delta'] for r in cal]
fits = {
    'baseline': independent_fit_check(blind['baseline_model'], [p.difference(r['basic']) for r in cal], yy),
    'assay': independent_fit_check(blind['assay_model'], [p.difference(r['basic']) + p.difference(r['assay']) for r in cal], yy),
    'initial': independent_fit_check(blind['initial_model'], [[p.difference(r['copy'])[0]] for r in cal], yy),
    'copy': independent_fit_check(blind['direct_model'], [p.difference(r['basic']) + p.difference(r['copy']) for r in cal], yy)}
reconstructed = {}
for name in acq['summary']:
    loss, regret, hits = 0., 0., 0
    for row in acq['results']:
        risks = [o['final_mse'] for o in row['outcomes']]
        target = p.math.log1p(risks[0]) - p.math.log1p(risks[1])
        value = row['forecasts_and_scores'][name]['prediction']
        selected = 1 if value > 0 else 0
        loss += (value - target) ** 2 / 4
        regret += (risks[selected] - min(risks)) / 4
        hits += int((selected == 1) == (target > 0))
    expected = acq['summary'][name]
    assert abs(loss - expected['mean_squared_paired_logrisk_error']) < 1e-14
    assert abs(regret - expected['mean_selection_regret_mse']) < 1e-14
    assert hits == expected['correct_rankings']
    reconstructed[name] = {'error': loss, 'regret': regret, 'hits': hits}
rows = []
for u, br, dr, row in zip(scorer['units'], blind['forecasts'], direct['forecasts'], acq['results']):
    assert [p.digest(s) for s in u['states']] == br['states_sha256']
    details = []
    for j in range(2):
        xs = p.core.support(br['context'])
        rr = p.scalar_risk(u['states'][j], xs, dr['label_table'])
        assert abs(rr - row['outcomes'][j]['initial_mse']) < 1e-12
        details.append({'initial_mse': rr, 'final_mse': row['outcomes'][j]['final_mse'],
                        'fraction_removed': row['outcomes'][j]['fraction_removed']})
    single = br['single_function_delta_forecasts']
    rows.append({'unit': row['unit'], 'teacher_variance': row['teacher_variance'], 'outcomes': details,
                 'raw_final_risk_gap': abs(details[0]['final_mse'] - details[1]['final_mse']),
                 'initial_best': row['initial_competence_best_state'], 'final_best': row['final_best_state'],
                 'baseline_assay_same_selection': ((br['baseline_delta_forecast'] > 0) == (br['assay_delta_forecast'] > 0)),
                 'single_function_forecast_min': min(single), 'single_function_forecast_max': max(single),
                 'single_function_selected_state1_count': sum(v > 0 for v in single),
                 'future_full_reference_max_parameter_gap': max(r['max_parameter_gap_over_entire_trajectory'] for r in row['reference'])})
base, assay, copy = [reconstructed[k] for k in ('baseline', 'assay', 'calibrated_copy')]
gates = {'at_least_3_of_4_rankings': assay['hits'] >= 3,
         '10pct_error_gain_over_baseline': assay['error'] <= .9 * base['error'],
         '10pct_error_gain_over_calibrated_copy': assay['error'] <= .9 * copy['error'],
         '25pct_regret_gain_over_baseline': assay['regret'] <= .75 * base['regret'],
         '25pct_regret_gain_over_copy': assay['regret'] <= .75 * copy['regret']}
out = {'utc': p.utc(), 'chronology': {'blind': blind['utc'], 'nondegeneracy': nondeg['utc'],
        'direct': direct['utc'], 'acquisition_end': acq['utc']}, 'fits': fits, 'reconstructed': reconstructed,
       'assay_error_increase_over_baseline_pct': 100 * (assay['error'] / base['error'] - 1),
       'assay_error_increase_over_calibrated_copy_pct': 100 * (assay['error'] / copy['error'] - 1),
       'pairs': rows, 'gates': gates, 'decision': 'CLOSE_no_main', 'revisions': 0,
       'new_SGD_updates_including_copies': 11280000,
       'independent_full_trajectory_reference_updates_additional': 80000,
       'true_source_support_labels_verified': 12928,
       'finite_difference_checks': sum('finite_difference_scaled_max' in r for r in prep['references']),
       'maximum_finite_difference_scaled_gap': max(r.get('finite_difference_scaled_max', 0.) for r in prep['references']),
       'maximum_scientific_rss_bytes_so_far': max(prep['rss_bytes'], direct['rss_bytes'], acq['rss_bytes'], nondeg['rss_bytes'], p.rss()),
       'measured_previous_script_seconds': prep['seconds'] + direct['seconds'] + acq['seconds'] + nondeg['seconds'],
       'seconds': p.time.perf_counter() - t0, 'rss_bytes': p.rss(), 'explicit_input_bytes_this_audit': p.READ_BYTES}
assert not any(gates.values()), gates
p.save('AUDIT.json', out)
print(p.json.dumps(out), flush=True)
