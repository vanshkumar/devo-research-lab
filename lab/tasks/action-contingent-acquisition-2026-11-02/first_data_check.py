"""Single fixed-original-person check; no fitting, target selection or other-arm reads."""
import os
for name in ('OPENBLAS_NUM_THREADS', 'OMP_NUM_THREADS', 'MKL_NUM_THREADS', 'NUMEXPR_NUM_THREADS', 'VECLIB_MAXIMUM_THREADS'):
    os.environ[name] = '1'
import datetime
import hashlib
import json
from pathlib import Path
import resource
import sys
import time
import urllib.request

ROOT = Path(__file__).resolve().parent
URL = 'https://raw.githubusercontent.com/wkool/tradeoffs/master/data/daw%20paradigm/data.mat'
EXPECTED_BYTES = 1894663
EXPECTED_BLOB = '8f6ffab4ce1e9cd2a88680078ba7c086b23a0d82'
start = time.monotonic()
record = {'started_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(), 'url': URL, 'stage': 'start'}
previous = ROOT / 'FIRST_DATA_CHECK.json'
if previous.exists():
    old = previous.read_bytes()
    (ROOT / ('FIRST_DATA_CHECK_PREVIOUS_' + hashlib.sha256(old).hexdigest()[:12] + '.json')).write_bytes(old)

def flush():
    record['finished_utc'] = datetime.datetime.now(datetime.timezone.utc).isoformat()
    record['elapsed_seconds'] = time.monotonic() - start
    record['maxrss_native'] = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    record['platform'] = sys.platform
    (ROOT / 'FIRST_DATA_CHECK.json').write_text(json.dumps(record, indent=2, allow_nan=False) + '\n')

try:
    raw_path = ROOT / 'source' / 'kool2016_daw_data.mat'
    if raw_path.exists():
        payload = raw_path.read_bytes()
        record['network_operations_this_run'] = 0
    else:
        record['network_operations_this_run'] = 1
        request = urllib.request.Request(URL, headers={'User-Agent': 'Research source inspection'})
        with urllib.request.urlopen(request, timeout=25) as response:
            record['response_url'] = response.url
            record['response_content_length'] = response.headers.get('Content-Length')
            payload = response.read(EXPECTED_BYTES + 1)
    record['acquired_bytes'] = len(payload)
    record['sha256'] = hashlib.sha256(payload).hexdigest()
    blob = hashlib.sha1(('blob ' + str(len(payload)) + '\0').encode() + payload).hexdigest()
    record['git_blob'] = blob
    assert len(payload) == EXPECTED_BYTES, 'Source length mismatch'
    assert blob == EXPECTED_BLOB, 'Pinned Git blob mismatch'
    if not raw_path.exists():
        raw_path.write_bytes(payload)
    record['stage'] = 'pinned_source'
    import numpy as np
    import scipy
    from scipy.io import loadmat, whosmat
    record['dependencies'] = {'numpy': np.__version__, 'scipy': scipy.__version__, 'python': sys.version}
    record['mat_directory'] = whosmat(raw_path)
    raw = loadmat(raw_path, variable_names=['data'])['data']
    record['decoded_shape'] = list(raw.shape)
    record['exposure'] = 'Entire data variable decompressed and typed decoded; other people numeric cells not interpreted or scored. Whole-file auxiliary/raw exposure is retained.'
    def identity(cell):
        return ''.join(np.asarray(cell).astype(str).reshape(-1))
    first_id = identity(raw[0, 0])
    rows = [i for i in range(raw.shape[0]) if identity(raw[i, 0]) == first_id]
    person = np.array([[float(np.asarray(raw[i, j]).reshape(-1)[0]) for j in range(1, 19)] for i in rows])
    record['first_person_id_sha256'] = hashlib.sha256(first_id.encode()).hexdigest()
    names = ['stim_1_left', 'stim_1_right', 'rt1', 'choice1', 'stim_2_left', 'stim_2_right', 'rt2', 'choice2', 'win', 'state2', 'common', 'score', 'practice', 'ps1a1', 'ps1a2', 'ps2a1', 'ps2a2', 'trial']
    record['column_map'] = names
    assert person.shape[1] == 18
    practice = person[:, 12] == 1
    main = person[~practice]
    record['person_total_rows'] = len(person)
    record['practice_rows'] = int(practice.sum())
    record['main_rows'] = len(main)
    record['main_trial_numbers'] = main[:, 17].tolist()
    record['main_first_five_rows'] = main[:5].tolist()
    valid = (main[:, 2] != -1) & (main[:, 6] != -1)
    v = main[valid]
    c1, c2, s2 = v[:, 3].astype(int), v[:, 7].astype(int), v[:, 9].astype(int)
    assert set(c1).issubset({1, 2}) and set(c2).issubset({1, 2}) and set(s2).issubset({1, 2})
    p = v[np.arange(len(v)), 13 + 2 * (s2 - 1) + (c2 - 1)]
    win = (v[:, 8] > 0).astype(int)
    assert np.all((p >= .25) & (p <= .75))
    assert np.array_equal((c1 == s2).astype(int), v[:, 10].astype(int))
    record['calculation'] = {
        'valid_main_responses': int(valid.sum()),
        'main_omissions': int((~valid).sum()),
        'common_transitions': int((c1 == s2).sum()),
        'rare_transitions': int((c1 != s2).sum()),
        'observed_rewards': int(win.sum()),
        'logged_chosen_probability_sum': float(p.sum()),
        'observed_reward_log_likelihood_at_logged_probabilities': float(np.sum(win * np.log(p) + (1 - win) * np.log1p(-p))),
        'mean_absolute_chosen_vs_other_alien_probability_gap': float(np.abs(p - v[np.arange(len(v)), 13 + 2 * (s2 - 1) + (2 - c2)]).mean()),
        'source_common_code_matches_action_state_mapping': True,
        'nonnegative_main_rt1': bool(np.all(v[:, 2] >= 0)),
        'nonnegative_main_rt2': bool(np.all(v[:, 6] >= 0)),
        'consecutive_main_trial_indices': bool(np.all(np.diff(main[:, 17]) == 1)),
        'scope': 'Descriptive source check at actual realized teacher probabilities; not a forecast, model fit or independent-sampling proof.'
    }
    record['stage'] = 'original_person_calculation_complete'
    record['exit_code'] = 0
    flush()
    print(json.dumps({k: record[k] for k in ['finished_utc', 'stage', 'sha256', 'decoded_shape', 'person_total_rows', 'practice_rows', 'main_rows', 'calculation', 'maxrss_native']}, indent=2))
except Exception as exc:
    record['error'] = repr(exc)
    record['exit_code'] = 1
    flush()
    raise
