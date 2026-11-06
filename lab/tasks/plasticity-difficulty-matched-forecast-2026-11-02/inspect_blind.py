"""Bounded pre-feedback nondegeneracy record, no future labels or outcomes."""
from paired import *

t0 = time.perf_counter()
b = read('BLIND_FORECASTS.json')
c = read('SCORER_CONTINUATION.json')
rows = []
for u, r in zip(c['units'], b['forecasts']):
    p = [[core.forward(s, x)[0] for x in core.support(r['context'])] for s in u['states']]
    rows.append({'unit': u['unit'], 'states_distinct': r['states_sha256'][0] != r['states_sha256'][1],
                 'pair_prediction_mean_squared_difference': sum((a - z) ** 2 for a, z in zip(*p)) / 32,
                 'dead_fractions': [v[12] for v in r['basic']],
                 'active_fractions': [v[11] for v in r['basic']],
                 'baseline_delta_forecast': r['baseline_delta_forecast'],
                 'assay_delta_forecast': r['assay_delta_forecast'],
                 'single_function_delta_forecasts': r['single_function_delta_forecasts']})
out = {'utc': utc(), 'kind': 'before_true_future_feedback', 'rows': rows,
       'future_labels_or_scores_used': False, 'seconds': time.perf_counter() - t0,
       'rss_bytes': rss(), 'all_histories_have_100_tasks': all(len(h) == 100 for u in c['units'] for h in u['histories'])}
save('BLIND_NONDEGENERACY.json', out)
print(json.dumps(out), flush=True)
