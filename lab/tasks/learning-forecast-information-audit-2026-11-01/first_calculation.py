"""Reconstruct the saved same-24 endpoint from admitted numerical artifacts."""
from pathlib import Path
import datetime as dt
import hashlib
import io
import json
import os
import resource
import time
import zipfile

import numpy as np

OUT = Path(__file__).resolve().parent
ROOT = OUT.parents[2]
HISTORY = ROOT / 'experiments/matched_history_diagnostic_2026-10-29'
C = ROOT / 'campaigns/population_learning_transport_2026-10-28'
COMMAND = ('OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 '
           'VECLIB_MAXIMUM_THREADS=1 NUMEXPR_NUM_THREADS=1 PYTHONDONTWRITEBYTECODE=1 '
           'campaigns/learning_rule_transport_2026-10-28/.modelenv/bin/python '
           'lab/tasks/learning-forecast-information-audit-2026-11-01/first_calculation.py')


def main():
    start = time.monotonic()
    pins = {}
    compressed = decoded = 0
    data = (HISTORY / 'CURVES.npz').read_bytes()
    compressed += len(data)
    pins[str((HISTORY / 'CURVES.npz').relative_to(ROOT))] = hashlib.sha256(data).hexdigest()
    with zipfile.ZipFile(io.BytesIO(data)) as z:
        decoded += sum(x.file_size for x in z.infolist())
    with np.load(io.BytesIO(data), allow_pickle=False) as z:
        subjects, labs = z['subjects'], z['labs']
        target = z['observed_sides']
        predictions = {k: z[k] for k in ('conditional_rnn', 'autonomous_rnn',
                                        'autonomous_growth', 'autonomous_persistence')}
    assert target.shape == (24, 6, 2)
    assert len(set(subjects.tolist())) == 24
    assert not {'NYU-21', 'SWC_007'} & set(subjects.tolist())
    expected = json.loads((C / 'protocols/FREEZE.json').read_text())['source_primary_subjects']
    assert subjects.tolist() == expected
    counts = []
    max_difference = 0.
    for subject in subjects:
        p = HISTORY / (str(subject) + '__conditional.npz')
        data = p.read_bytes()
        compressed += len(data)
        pins[str(p.relative_to(ROOT))] = hashlib.sha256(data).hexdigest()
        with zipfile.ZipFile(io.BytesIO(data)) as z:
            decoded += sum(x.file_size for x in z.infolist())
        with np.load(io.BytesIO(data), allow_pickle=False) as z:
            i = len(counts)
            assert np.array_equal(z['observed'][:, :2], target[i])
            assert np.array_equal(z['conditional_sides'], predictions['conditional_rnn'][i])
            n = z['counts']
            assert n.shape == (6, 4) and np.all(n[:, :2] > 0)
            assert np.all(n[:, 2:] == 500)
            # Original observed shares have integer correct counts and include omissions.
            numerators = z['observed'][:, :2] * n[:, :2]
            difference = float(np.max(np.abs(numerators - np.rint(numerators))))
            assert difference < 1e-10
            max_difference = max(max_difference, difference)
            counts.append(n)
    metrics = {}
    for name, side in predictions.items():
        residual = target.mean(2) - side.mean(2)
        metrics[name] = dict(population_curve_mae_pp=float(100 * np.abs(residual.mean(0)).mean()),
                             individual_curve_mae_pp=float(100 * np.abs(residual).mean()),
                             individual_side_mae_pp=float(100 * np.abs(target-side).mean()))
    result = dict(utc=dt.datetime.now(dt.timezone.utc).isoformat(),
                  status='executed_saved_numeric_reconstruction',
                  command=COMMAND, units='percentage points; counts are opportunities',
                  subjects=subjects.tolist(), labs=labs.tolist(), animals=24,
                  prefix_per_animal=1000, future_per_animal=3000,
                  admitted_original_rows=96000, newly_returned_original_rows=0,
                  scored_animal_bin_side_cells=int(target.size),
                  exact100_opportunities=int(np.array(counts)[:, :, :2].sum()),
                  counts=np.array(counts).tolist(),
                  max_integer_correct_count_discrepancy=max_difference,
                  metrics=metrics, pins=pins,
                  resources=dict(compressed_bytes_read=compressed,
                                 full_zip_uncompressed_bytes_charged=decoded,
                                 additional_context_code_import_allowance_bytes=5_000_000,
                                 conservative_read_charge_bytes=compressed+decoded+5_000_000,
                                 peak_process_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
                                 peak_rss_units='bytes on Darwin', process_count=1,
                                 numerical_threads=1, network_operations=0, ingress_bytes=0,
                                 physical_io_unknown=True, elapsed_seconds=time.monotonic()-start))
    (OUT / 'FIRST_CALCULATION.json').write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps({k: result[k] for k in ('utc', 'status', 'animals',
                     'scored_animal_bin_side_cells', 'exact100_opportunities', 'metrics', 'resources')}, indent=2), flush=True)


if __name__ == '__main__':
    main()
