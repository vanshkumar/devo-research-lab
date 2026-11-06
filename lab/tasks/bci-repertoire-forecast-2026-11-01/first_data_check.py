"""Reconstruct the public measured pre-learning example; no outcome fitting."""
import os
for key in ('OPENBLAS_NUM_THREADS', 'OMP_NUM_THREADS', 'MKL_NUM_THREADS', 'VECLIB_MAXIMUM_THREADS', 'NUMEXPR_NUM_THREADS'):
    os.environ[key] = '1'
import json
import hashlib
import resource
import sys
import warnings
from pathlib import Path
from datetime import datetime, timezone
ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT.parents[2] / '.venv/lib/python3.9/site-packages'))
import numpy as np
import scipy
from scipy.io import loadmat

path = ROOT / 'sources/exampleData.mat'
raw = path.read_bytes()
assert hashlib.sha256(raw).hexdigest() == 'f28fab9442dd0564aab00597796785665f1c3d4b4437e3802c4c99c9696512b1'
data = loadmat(path, simplify_cells=True, variable_names=['expParams', 'beforeLearning'])
p = data['expParams']
b = data['beforeLearning']['clouds']
intuitive = p['intuitiveMapping']
perturbed = p['perturbedMapping']
contract = lambda a, z: np.einsum('ij,jk->ik', a, z)
factor_transform = contract(contract(contract(intuitive['D'], intuitive['V'].T), intuitive['beta']), intuitive['Sigma_u'])
with warnings.catch_warnings(record=True) as caught:
    warnings.simplefilter('always')
    matmul_transform = intuitive['D'] @ intuitive['V'].T @ intuitive['beta'] @ intuitive['Sigma_u']
matrix_check = {
    'all_inputs_finite': all(bool(np.isfinite(intuitive[key]).all()) for key in ('D', 'V', 'beta', 'Sigma_u')),
    'matmul_result_finite': bool(np.isfinite(matmul_transform).all()),
    'einsum_result_finite': bool(np.isfinite(factor_transform).all()),
    'matmul_vs_explicit_contractions_max_abs': float(np.max(np.abs(matmul_transform - factor_transform))),
    'current_original_expression_warnings': [str(item.message) for item in caught],
    'first_pass_warnings_observed_in_tool_output': ['divide by zero encountered in matmul', 'overflow encountered in matmul', 'invalid value encountered in matmul'],
    'first_pass_saved': 'FIRST_DATA_CHECK_INITIAL.json and first_data_check_initial.py',
    'action': 'Use explicit einsum contractions for decoder and factor reconstruction; preserve the initial warning record.'
}
assert matrix_check['all_inputs_finite'] and matrix_check['matmul_result_finite'] and matrix_check['einsum_result_finite']
assert matrix_check['matmul_vs_explicit_contractions_max_abs'] < 1e-12
(ROOT / 'MATRIX_VALIDATION.json').write_text(json.dumps(matrix_check, indent=2) + '\n')
by_cloud = []
for idx in range(len(b['factorActivity'])):
    spikes = b['spikes'][idx].astype(float)
    factors = b['factorActivity'][idx]
    direction = b['cursorToTargetDirection'][idx]
    factors_rebuilt = contract(factor_transform, spikes - intuitive['mu_u'][:, None])
    checks = {}
    for name, mapping in [('intuitive', intuitive), ('perturbed', perturbed)]:
        raw_velocity = contract(mapping['M2'], spikes) + mapping['m0'][:, None]
        factor_decoder = contract(contract(contract(contract(mapping['K'], mapping['eta']), mapping['Sigma_z']), mapping['V']), np.diag(1 / np.diag(mapping['D'])))
        factor_velocity = contract(factor_decoder, factors) - np.einsum('ij,j->i', mapping['K'], mapping['d'])[:, None]
        stored = b['vraw_' + name][idx]
        rebuilt_progress = np.einsum('ij,ij->j', raw_velocity, direction)
        checks[name] = {
            'raw_velocity_vs_source_max_abs_mm_per_s': float(np.max(np.abs(raw_velocity - stored))),
            'factor_velocity_vs_source_max_abs_mm_per_s': float(np.max(np.abs(factor_velocity - stored))),
            'raw_vs_factor_velocity_max_abs_mm_per_s': float(np.max(np.abs(raw_velocity - factor_velocity))),
            'progress_vs_source_max_abs_mm_per_s': float(np.max(np.abs(rebuilt_progress - b[name + 'Progress'][idx]))),
            'progress_dt_scaled_vs_source_max_abs_mm_per_bin': float(np.max(np.abs(rebuilt_progress * mapping['dt'] - b[name + 'Progress'][idx]))),
            'factor_progress_dt_scaled_vs_source_max_abs_mm_per_bin': float(np.max(np.abs(np.einsum('ij,ij->j', factor_velocity, direction) * mapping['dt'] - b[name + 'Progress'][idx]))),
            'mean_progress_mm_per_s': float(rebuilt_progress.mean()),
            'stored_progress_mean': float(np.mean(b[name + 'Progress'][idx])),
            'source_progress_first5': b[name + 'Progress'][idx][:5].tolist(),
            'reconstructed_projection_first5': rebuilt_progress[:5].tolist(),
            'direction_first5': direction[:, :5].tolist(),
            'source_vraw_first5': stored[:, :5].tolist(),
            'mean_speed_mm_per_s': float(np.linalg.norm(raw_velocity, axis=0).mean()),
            'unmatched_no_offset_max_abs_mm_per_s': float(np.max(np.abs(contract(mapping['M2'], spikes) - stored)))
        }
    by_cloud.append({
        'movement_cloud_angle_degrees': int(b['angles'][idx]),
        'samples': int(spikes.shape[1]), 'units': int(spikes.shape[0]),
        'factors': int(factors.shape[0]),
        'finite_spike_values': int(np.isfinite(spikes).sum()),
        'nonnegative_integer_spikes': bool(np.all(spikes >= 0) and np.all(spikes == np.floor(spikes))),
        'factor_reconstruction_max_abs': float(np.max(np.abs(factors_rebuilt - factors))),
        'direction_norm_max_error': float(np.max(np.abs(np.linalg.norm(direction, axis=0) - 1))),
        'decoders': checks
    })
out = {
    'timestamp_utc': datetime.now(timezone.utc).isoformat(),
    'status': 'ACTUAL_MEASURED_DATA_ARITHMETIC_COMPLETE; source comparison gate still pending',
    'source_sha256': hashlib.sha256(raw).hexdigest(),
    'animal_export_name': p['monkName'], 'source_animal_label': 'monkey J (README)',
    'session': p['expDate'], 'independent_sessions': 1, 'independent_animals': 1,
    'before_trial_window_1based_export': b['windowIdx'].astype(int).tolist(),
    'dt_seconds': float(intuitive['dt']),
    'M1_intuitive': intuitive['M1'].tolist(),
    'M1_perturbed': perturbed['M1'].tolist(),
    'samples_total': sum(row['samples'] for row in by_cloud),
    'measured_spike_values': sum(row['finite_spike_values'] for row in by_cloud),
    'movement_clouds': by_cloud,
    'calculation': 'raw v = M2*spikes+m0; zorth = D*V.T*beta*Sigma_u*(spikes-mu_u); factor v = K*eta*Sigma_z*V*inv(D)*zorth-K*d',
    'interpretation': 'vraw is the unsmoothed decoder contribution in mm/s, not the full recursive cursor velocity. Both known decoders are applied to measured BEFORE-learning spikes. This mechanical counterfactual is not actual initial post-change behavior or learned improvement.',
    'source_progress_scale': 'In this actual example, stored intuitiveProgress and perturbedProgress equal dt times the projection of vraw, i.e. mm per 45-ms bin, despite the source paper defining cursor progress as speed. The initial direct mm/s comparison is preserved and fails. This finite export/codebook distinction does not invalidate the published results.',
    'phase_support': 'beforeLearning and expParams only decoded. Source run.m describes afterLearning as successful trials in the best-performance 50-trial perturbation window; trial-to-sample mapping and intermediate learning chronology are not exported in the documented example schema.',
    'auxiliary_exposure': 'The full expParams struct, including a post-learning acquisition-time scaling lambda, was decoded during schema inspection; it is excluded from every calculation here. afterLearning values remain unrequested.',
    'versions': {'python': sys.version, 'numpy': np.__version__, 'scipy': scipy.__version__},
    'resource': {'peak_rss_bytes': resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
                 'mat_file_bytes_read_this_pass_at_least': 2 * len(raw),
                 'numerical_threads_requested': 1, 'scientific_processes': 1}
}
(ROOT / 'FIRST_DATA_CHECK.json').write_text(json.dumps(out, indent=2) + '\n')
summary = {'timestamp_utc': out['timestamp_utc'], 'sessions': 1, 'samples': out['samples_total'], 'spike_values': out['measured_spike_values'], 'matrix_validation': matrix_check,
           'max_factor_error': max(row['factor_reconstruction_max_abs'] for row in by_cloud),
           'max_raw_velocity_error_mm_per_s': max(item['raw_velocity_vs_source_max_abs_mm_per_s'] for row in by_cloud for item in row['decoders'].values()),
           'max_factor_velocity_error_mm_per_s': max(item['factor_velocity_vs_source_max_abs_mm_per_s'] for row in by_cloud for item in row['decoders'].values()),
           'max_raw_dt_scaled_progress_error_mm_per_bin': max(item['progress_dt_scaled_vs_source_max_abs_mm_per_bin'] for row in by_cloud for item in row['decoders'].values()),
           'max_factor_dt_scaled_progress_error_mm_per_bin': max(item['factor_progress_dt_scaled_vs_source_max_abs_mm_per_bin'] for row in by_cloud for item in row['decoders'].values())}
assert summary['max_factor_error'] < 1e-12
assert summary['max_raw_velocity_error_mm_per_s'] < 1e-6
assert summary['max_factor_velocity_error_mm_per_s'] < 1e-10
assert summary['max_raw_dt_scaled_progress_error_mm_per_bin'] < 1e-10
# Factor-based vraw and raw-spike progress were produced by slightly different
# stored decoder representations. Cauchy-Schwarz gives this deterministic bound
# because every direction is a unit vector. Do not demand a tighter progress
# match than the already measured raw/factor decoder discrepancy permits.
summary['factor_progress_roundtrip_bound_mm_per_bin'] = float(intuitive['dt']) * np.sqrt(2) * summary['max_raw_velocity_error_mm_per_s'] + 1e-12
assert summary['max_factor_dt_scaled_progress_error_mm_per_bin'] <= summary['factor_progress_roundtrip_bound_mm_per_bin']
(ROOT / 'FIRST_DATA_CHECK_SUMMARY.json').write_text(json.dumps(summary, indent=2) + '\n')
print(json.dumps(summary, indent=2))
