"""Offline, source-linked input certification and a reused human non-target sample.

No receptor score, matching, fitting, new network or protected observations.
"""
import collections
import csv
import hashlib
import io
import json
from pathlib import Path
import re
import resource

import h5py
import numpy as np
from sample_h5ad import FocusedUnitsFile

ROOT = Path(__file__).resolve().parent
REPO = ROOT.parents[2]
OLD = REPO / 'campaigns/hypomap_quantitative_2026-10-28/inputs'
PANEL = set('OXTR AVPR1A AVPR1B AVPR2 MC3R MC4R LEPR GHSR HCRTR1 HCRTR2 NPY1R NPY2R NPY4R NPY5R CRHR1 CRHR2 GNRHR KISS1R GALR1 GALR2 GALR3 SSTR1 SSTR2 SSTR3 SSTR4 SSTR5 NTSR1 NTSR2 TACR1 TACR2 TACR3 TRHR PRLHR QRFPR NMUR1 NMUR2 RXFP1 RXFP2 SCTR CALCR CALCRL GLP1R GIPR GCGR PTH1R PTH2R OPRM1 OPRD1 OPRK1 NPBWR1 NPBWR2 UTS2R PROKR1 PROKR2'.split())
assert len(PANEL) == 54

read_files = []


def read(path):
    data = path.read_bytes()
    read_files.append({'path': str(path.relative_to(REPO)), 'bytes': len(data),
                       'sha256': hashlib.sha256(data).hexdigest()})
    return data


def table(path):
    return list(csv.DictReader(io.StringIO(read(path).decode())))


def main():
    out = {'claim': 'input certification only; primary receptor prediction unrun', 'target_panel_size': 54}
    req_bytes = read(ROOT / 'REQUESTS.json')
    requests = json.loads(req_bytes)
    integrity = []
    for rec in requests:
        data = read(ROOT / rec['saved_file'])
        okay = len(data) == rec['bytes_received'] and hashlib.sha256(data).hexdigest() == rec['sha256']
        assert okay
        integrity.append({'label': rec['label'], 'size_and_sha256_pass': okay})
    out['all_source_response_integrity'] = integrity
    mouse = json.loads(read(ROOT / 'MOUSE_FOCUSED_UNITS_CHECK.json'))
    cats = mouse['units']['donor_id']['categories']
    units = {'n_categories_observed': len(cats),
             'single_SRA_run_labels': [x for x in cats if re.fullmatch(r'SRR\d+', x)],
             'composite_SRA_run_labels': [x for x in cats if re.fullmatch(r'SRR\d+(?:_SRR\d+)+', x)],
             'pooled_labels': [x for x in cats if x == 'pooled'],
             'cell_counts_per_category': 'unrun: focused-read ceiling reached before codes decoded',
             'individual_animal_mapping_certified': False}
    out['mouse_units'] = units
    # The code array's shape is metadata; prohibit every additional HTTP read.
    rf = FocusedUnitsFile('mouse', mouse['url'], mouse['size'])
    rf.new_requests = 4
    try:
        with h5py.File(rf, 'r') as h:
            d = h['obs/donor_id/codes']
            units['codes_structure'] = {'shape': list(d.shape), 'dtype': str(d.dtype),
                                       'chunks': list(d.chunks) if d.chunks else None,
                                       'compression': d.compression}
    except Exception as err:
        units['offline_structure_error'] = type(err).__name__ + ': ' + str(err)
    finally:
        out['mouse_offline_structure_hdf5_logical_bytes'] = rf.logical_read_bytes
        out['mouse_offline_structure_cached_bytes_loaded'] = sum(len(x) for x in rf.memory.values())
        rf.close()

    # Reuse only the earlier six-cell normalization-check leaf arrays, not the
    # full selected matrix or old range cache. All six cells were already consumed.
    features = table(OLD / 'raw_var.csv')
    assert len(features) == 36924
    assert 'feature_name' in features[0]
    symbols = np.array([r['feature_name'] for r in features])
    raw_keys = list(features[0])
    cells = {r['row_index']: r for r in table(OLD / 'peptide_obs.csv')}
    archive_bytes = read(OLD / 'normalization_check_vectors.npz')
    checked = []
    decoded = 0
    with np.load(io.BytesIO(archive_bytes), allow_pickle=False) as arrays:
        row_ids = sorted(k[:-4] for k in arrays.files if k.endswith('_raw'))
        assert len(row_ids) == 6
        for row_id in row_ids:
            raw, indices = arrays[row_id + '_raw'], arrays[row_id + '_indices']
            decoded += raw.nbytes + indices.nbytes
            assert len(raw) == len(indices) and np.all(indices >= 0) and np.all(indices < len(features))
            # Redact the original panel before any expression summary. This is
            # an exclusion mask on human symbols, not a cross-species ortholog map.
            keep = np.array([str(symbols[i]).upper() not in PANEL for i in indices])
            x = raw[keep]
            chosen = np.flatnonzero(keep)[:3]
            meta = cells[row_id]
            checked.append({'source_row_index': int(row_id), 'barcode': meta['_index'],
                            'donor_id': meta['donor_id'], 'Dataset': meta['Dataset'],
                            'Sample_ID': meta['Sample_ID'], 'C4_named': meta['C4_named'],
                            'non_target_stored_entries': len(x),
                            'non_target_values_finite_positive_integer': bool(np.all(np.isfinite(x)) and np.all(x > 0) and np.all(x == np.floor(x))),
                            'non_target_count_sum': float(x.sum(dtype=np.float64)),
                            'first_three_non_target_observations': [{'source_column_index': int(indices[j]),
                                'feature_name': str(symbols[indices[j]]), 'count': float(raw[j])} for j in chosen]})
    assert all(x['non_target_values_finite_positive_integer'] for x in checked)
    out['human_reused_small_sample'] = {'source_asset': 'https://datasets.cellxgene.cziscience.com/af06d70d-a2bc-43c1-8378-bc545bc8ee2c.h5ad',
        'gene_universe_size': len(features), 'feature_columns': raw_keys, 'cells': checked,
        'n_cells': len(checked), 'donor_ids_in_these_six_cells': sorted({x['donor_id'] for x in checked}),
        'scope': 'previously consumed six-cell raw/X leaf sample; no independent evaluation or receptor scoring',
        'compressed_npz_bytes_read': len(archive_bytes), 'raw_indices_decoded_bytes': decoded}
    out['read_file_manifest'] = read_files
    out['known_direct_file_bytes_read_in_this_command'] = sum(x['bytes'] for x in read_files)
    out['peak_rss_bytes_macos'] = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    out['primary_readiness'] = {'certified': False,
       'missing': ['source-defined independent mouse animal or justified biological-sample units',
                   'compatible mouse non-target plus receptor numerical observations for those units',
                   'source-linked one-to-one ortholog table and source/processing reconciliation',
                   'frozen excluded-gene matching, training-only normalization and independent evaluation'],
       'all_prediction_controls_and_sensitivity': 'unrun', 'recommendation': 'close this acquisition route; no further searches/repairs in this tranche'}
    (ROOT / 'INPUT_AUDIT.json').write_text(json.dumps(out, indent=2) + '\n')
    print(json.dumps({'mouse_units': units, 'human_sample': out['human_reused_small_sample'],
                      'integrity_responses_passed': len(integrity), 'primary_readiness': out['primary_readiness'],
                      'direct_file_bytes_read': out['known_direct_file_bytes_read_in_this_command'],
                      'decoded_array_bytes': decoded, 'peak_rss_bytes': out['peak_rss_bytes_macos']}, indent=2))


if __name__ == '__main__':
    main()
