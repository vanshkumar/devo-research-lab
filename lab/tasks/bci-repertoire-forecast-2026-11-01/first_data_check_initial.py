"""Reconstruct the public measured pre-learning example; no outcome fitting."""
import os
for key in ('OPENBLAS_NUM_THREADS', 'OMP_NUM_THREADS', 'MKL_NUM_THREADS', 'VECLIB_MAXIMUM_THREADS', 'NUMEXPR_NUM_THREADS'):
    os.environ[key] = '1'
import json
import hashlib
import resource
import sys
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
factor_transform = intuitive['D'] @ intuitive['V'].T @ intuitive['beta'] @ intuitive['Sigma_u']
by_cloud = []
for idx in range(len(b['factorActivity'])):
    spikes = b['spikes'][idx].astype(float)
    factors = b['factorActivity'][idx]
    direction = b['cursorToTargetDirection'][idx]
    factors_rebuilt = contract(factor_transform, spikes - intuitive['mu_u'][:, None])
    checks = {}
    for name, mapping in [('intuitive', intuitive), ('perturbed', perturbed)]:
        raw_velocity = contract(mapping['M2'], spikes) + mapping['m0'][:, None]
        factor_decoder = mapping['K'] @ mapping['eta'] @ mapping['Sigma_z'] @ mapping['V'] @ np.diag(1 / np.diag(mapping['D']))
        factor_velocity = contract(factor_decoder, factors) - (mapping['K'] @ mapping['d'])[:, None]
        stored = b['vraw_' + name][idx]
        rebuilt_progress = np.einsum('ij,ij->j', raw_velocity, direction)
        checks[name] = {
            'raw_velocity_vs_source_max_abs_mm_per_s': float(np.max(np.abs(raw_velocity - stored))),
            'factor_velocity_vs_source_max_abs_mm_per_s': float(np.max(np.abs(factor_velocity - stored))),
            'raw_vs_factor_velocity_max_abs_mm_per_s': float(np.max(np.abs(raw_velocity - factor_velocity))),
            'progress_vs_source_max_abs_mm_per_s': float(np.max(np.abs(rebuilt_progress - b[name + 'Progress'][idx]))),
            'mean_progress_mm_per_s': float(rebuilt_progress.mean()),
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
    'samples_total': sum(row['samples'] for row in by_cloud),
    'measured_spike_values': sum(row['finite_spike_values'] for row in by_cloud),
    'movement_clouds': by_cloud,
    'calculation': 'raw v = M2*spikes+m0; zorth = D*V.T*beta*Sigma_u*(spikes-mu_u); factor v = K*eta*Sigma_z*V*inv(D)*zorth-K*d',
    'interpretation': 'vraw is the unsmoothed decoder contribution in mm/s, not the full recursive cursor velocity. Both known decoders are applied to measured BEFORE-learning spikes. This mechanical counterfactual is not actual initial post-change behavior or learned improvement.',
    'phase_support': 'beforeLearning and expParams only decoded. Source run.m describes afterLearning as successful trials in the best-performance 50-trial perturbation window; trial-to-sample mapping and intermediate learning chronology are not exported in the documented example schema.',
    'auxiliary_exposure': 'The full expParams struct, including a post-learning acquisition-time scaling lambda, was decoded during schema inspection; it is excluded from every calculation here. afterLearning values remain unrequested.',
    'versions': {'python': sys.version, 'numpy': np.__version__, 'scipy': scipy.__version__},
    'resource': {'peak_rss_bytes': resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
                 'mat_file_bytes_read_this_pass_at_least': 2 * len(raw),
                 'numerical_threads_requested': 1, 'scientific_processes': 1}
}
(ROOT / 'FIRST_DATA_CHECK.json').write_text(json.dumps(out, indent=2) + '\n')
print(json.dumps(out, indent=2))
