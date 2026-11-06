"""The one declared, same-person source-design check. No forecasts or fits."""
import os
for name in ('OPENBLAS_NUM_THREADS', 'OMP_NUM_THREADS', 'MKL_NUM_THREADS', 'NUMEXPR_NUM_THREADS', 'VECLIB_MAXIMUM_THREADS'):
    os.environ[name] = '1'
import datetime
import hashlib
import json
from pathlib import Path
import resource
import struct
import time
import zlib
import numpy as np
from scipy.io import loadmat

ROOT = Path(__file__).resolve().parent
started = time.monotonic()
path = ROOT / 'source' / 'kool2016_daw_data.mat'
payload = path.read_bytes()
assert hashlib.sha256(payload).hexdigest() == '47083627c365cc3130cc8f75dd2b989e51112a95b043eaf78013750381eac7d6'
raw = loadmat(path, variable_names=['data'])['data']
def identity(cell):
    return ''.join(np.asarray(cell).astype(str).reshape(-1))
first_id = identity(raw[0, 0])
rows = [i for i in range(len(raw)) if identity(raw[i, 0]) == first_id]
person = np.array([[float(np.asarray(raw[i, j]).reshape(-1)[0]) for j in range(1, 19)] for i in rows])
out = {'utc': datetime.datetime.now(datetime.timezone.utc).isoformat(), 'first_person_id_sha256': hashlib.sha256(first_id.encode()).hexdigest(), 'source_sha256': hashlib.sha256(payload).hexdigest(), 'phases': {}}
for phase, flag in [('practice', 1), ('main', 0)]:
    a = person[person[:, 12] == flag]
    ps = a[:, 13:17]
    d = np.diff(ps, axis=0)
    interior = (ps[:-1] > .35) & (ps[:-1] < .65) & (ps[1:] > .35) & (ps[1:] < .65) & (np.abs(d) < .08)
    detail = {'rows': len(a), 'initial_probabilities': ps[0].tolist(), 'probability_min': float(ps.min()), 'probability_max': float(ps.max()), 'main_trial_order_consecutive': bool(np.all(np.diff(a[:, 17]) == 1)), 'increments': int(d.size), 'interior_increments': int(interior.sum()), 'rounding_checks': {}}
    for precision in [12, 10]:
        for name, values in [('all', d.ravel()), ('interior', d[interior])]:
            unique, counts = np.unique(np.round(values, precision), return_counts=True)
            detail['rounding_checks'][name + '_' + str(precision)] = {'unique': len(unique), 'observations_beyond_first_occurrences': int(np.sum(counts - 1)), 'values_observed_more_than_once': int(np.sum(counts > 1)), 'largest_multiplicity': int(counts.max()) if len(counts) else 0}
    out['phases'][phase] = detail
main = person[person[:, 12] == 0]
out['score_check'] = {'equals_main_reward_cumulative_sum': bool(np.array_equal(main[:, 11], np.cumsum(main[:, 8]))), 'last_score': float(main[-1, 11]), 'reward_sum': float(main[:, 8].sum()), 'raw_positive_reward_codes': sorted(set(main[:, 8].tolist()))}
out['source_pins'] = {}
for f in ['index.html', 'additional-functions.js', 'jspsych-space-daw-stim.js', 'make_raw_data.m', 'MB_MF_daw_rllik.m', 'set_opts.m']:
    b = (ROOT / 'source' / f).read_bytes()
    out['source_pins'][f] = {'bytes': len(b), 'sha256': hashlib.sha256(b).hexdigest(), 'git_blob_of_saved_utf8': hashlib.sha1(('blob ' + str(len(b)) + '\0').encode() + b).hexdigest()}
index = (ROOT / 'source' / 'index.html').read_text()
plugin = (ROOT / 'source' / 'jspsych-space-daw-stim.js').read_text()
assert 'for (i = 0; i < 1000; i++)' in index
assert 'gaussian[Math.floor(Math.random()*gaussian.length)]' in index
assert 'win = Math.random()<trial.ps[state-1][choice2-1]' in plugin
assert 'trials[i].tr = params.tr || 0.7' in plugin
out['static_law'] = {'finite_bank_size': 1000, 'bank_normal_sd': .025, 'common_transition_probability': .7, 'reflection_bounds': [.25, .75], 'future_draws_occur_online_before_each_trial': True, 'state_draw_after_first_action': True, 'reward_draw_after_second_action': True, 'literal_source_assertions_pass': True, 'first_person_no_omissions_so_empirical_omission_replay_unrun': True}
assert out['score_check']['equals_main_reward_cumulative_sum']
# Independent accounting pass: measure the decompressed MAT element byte count.
tag, length = struct.unpack('<II', payload[128:136])
out['mat_compressed_element'] = {'tag': int(tag), 'compressed_bytes': int(length)}
if tag == 15:
    decoder = zlib.decompressobj()
    total = 0
    for offset in range(136, 136 + length, 65536):
        total += len(decoder.decompress(payload[offset:min(offset + 65536, 136 + length)]))
    total += len(decoder.flush())
    out['mat_compressed_element']['uncompressed_bytes'] = total
    out['mat_compressed_element']['stream_finished'] = decoder.eof
    assert decoder.eof
out['interpretation'] = 'Same-person protocol fingerprint only. Rounded repeat counts do not estimate material forecast error, prove deployed code identity or exclude every alternative teacher. New independent Gaussian draws are not the literal source bank law; forecasts before the first main trial could integrate this bank prior. No fitting, forecast, source model superiority, biological effect, impossibility or novelty is established.'
out['exit_code'] = 0
out['elapsed_seconds'] = time.monotonic() - started
out['maxrss_bytes_darwin'] = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
(ROOT / 'SOURCE_DESIGN_CHECK.json').write_text(json.dumps(out, indent=2, allow_nan=False) + '\n')
print(json.dumps(out, indent=2))
