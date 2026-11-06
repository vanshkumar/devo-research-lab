"""Finite, offline independent reconstruction. No author code imports/network.

Reads only the author's saved source/range records and three authorized human
leaf files. Codes values, mouse expression and normalized human X are never
indexed. Scientific outputs are independently constructed before comparison.
"""
import csv
import datetime as dt
import hashlib
import io
import json
import os
from pathlib import Path
import re
import resource
import sys
import traceback
from html.parser import HTMLParser

import h5py
import numpy as np

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
AUTHOR = REPO / 'lab/tasks/molecular-donor-inputs-2026-10-31'
LEAF = REPO / 'campaigns/hypomap_quantitative_2026-10-28/inputs'
PROTOCOL = REPO / 'lab/tasks/molecular-correspondence-2026-10-31/PROTOCOL.md'
DEADLINE = dt.datetime(2026, 10, 31, 20, 36, 34, 468000, tzinfo=dt.timezone.utc)
CACHE, PINS = {}, []
COUNTERS = {'direct_file_bytes': 0, 'sha256_bytes_processed': 0,
            'decoded_text_utf8_bytes': 0, 'human_array_bytes': 0,
            'hdf5_logical_bytes': 0, 'category_decoded_bytes': 0}
ALLOWED_LEAVES = {LEAF / x for x in
                  ('raw_var.csv', 'peptide_obs.csv', 'normalization_check_vectors.npz')}


def now():
    return dt.datetime.now(dt.timezone.utc)


def check_limits():
    assert now() < DEADLINE, 'Review deadline reached'
    assert sum(COUNTERS.values()) < 48_000_000, 'Instrumented read/decode/hash reserve reached'
    assert resource.getrusage(resource.RUSAGE_SELF).ru_maxrss < 1_000_000_000


def sha(data):
    COUNTERS['sha256_bytes_processed'] += len(data)
    check_limits()
    return hashlib.sha256(data).hexdigest()


def read(path):
    path = path.resolve()
    assert (path.parent == AUTHOR or path.parent == AUTHOR / 'sources'
            or path in ALLOWED_LEAVES or path == PROTOCOL or path.parent == HERE)
    if path not in CACHE:
        check_limits()
        data = path.read_bytes()
        COUNTERS['direct_file_bytes'] += len(data)
        CACHE[path] = data
        PINS.append({'path': str(path.relative_to(REPO)), 'bytes': len(data),
                     'sha256': sha(data)})
    return CACHE[path]


def text_data(data):
    COUNTERS['decoded_text_utf8_bytes'] += len(data)
    check_limits()
    return data.decode('utf-8')


def load(path):
    return json.loads(text_data(read(path)))


def save(name, value):
    (HERE / name).write_text(json.dumps(value, indent=2, ensure_ascii=False) + '\n')


def plain(x):
    if isinstance(x, bytes):
        return x.decode('utf-8')
    if isinstance(x, np.generic):
        return plain(x.item())
    if isinstance(x, np.ndarray):
        return [plain(z) for z in x]
    if isinstance(x, (list, tuple)):
        return [plain(z) for z in x]
    return x


class Links(HTMLParser):
    def __init__(self):
        super().__init__()
        self.hrefs = []

    def handle_starttag(self, tag, attrs):
        if tag == 'a':
            self.hrefs.extend(v for k, v in attrs if k == 'href' and v)


def records(value, name):
    rows = value['_embedded'][name]
    assert value.get('page', {}).get('totalElements', len(rows)) == len(rows)
    return rows


def metadata_values(item):
    return {k: [v['value'] for v in vals] for k, vals in item['metadata'].items()
            if any(s in k for s in ('description', 'rights', 'relation', 'identifier', 'title'))}


class SavedRanges(io.RawIOBase):
    """Independent positional reader, immutable saved bytes, missing span fails.

    It has no acquisition fallback and imports no author helper. Reads record
    exact logical offsets; only caller's donor categories/schema are accessed.
    """
    def __init__(self, size, ranges):
        self.size, self.ranges, self.pos = size, ranges, 0
        self.calls = []

    def readable(self):
        return True

    def seekable(self):
        return True

    def tell(self):
        return self.pos

    def seek(self, offset, whence=0):
        self.pos = offset + (0 if whence == 0 else self.pos if whence == 1 else self.size)
        if not 0 <= self.pos <= self.size:
            raise OSError('Out-of-object seek')
        return self.pos

    def read(self, length=-1):
        if not 0 <= length <= 1_000_000:
            raise OSError('Unbounded or large read denied')
        length = min(length, self.size - self.pos)
        COUNTERS['hdf5_logical_bytes'] += length
        check_limits()
        begin, stop, pieces = self.pos, self.pos + length, []
        while self.pos < stop:
            matches = [r for r in self.ranges if r[0] <= self.pos <= r[1]]
            if not matches:
                raise OSError('Missing offline span at %d, length %d' % (self.pos, stop - self.pos))
            lo, hi, data, label = min(matches, key=lambda r: r[1] - r[0])
            end = min(stop, hi + 1)
            pieces.append(data[self.pos - lo:end - lo])
            self.pos = end
        self.calls.append({'start': begin, 'length': length})
        return b''.join(pieces)

    def readinto(self, target):
        data = self.read(len(target))
        target[:len(data)] = data
        return len(data)


def main():
    out = {'started_utc': now().isoformat(), 'independent_scientific_code': True,
           'author_analysis_or_provider_imports': [], 'network_requests': 0,
           'scope': 'input/unit closeout only; prediction/controls/sensitivity unrun'}
    requests = load(AUTHOR / 'REQUESTS.json')
    integrity = []
    by_label = {}
    for rec in requests:
        path = AUTHOR / rec['saved_file']
        data = read(path)
        pin = next(p for p in PINS if p['path'] == str(path.relative_to(REPO)))
        assert len(data) == rec['bytes_received'] and pin['sha256'] == rec['sha256']
        integrity.append({'label': rec['label'], 'bytes': len(data),
                          'recorded_status': rec.get('status'), 'pin_pass': True})
        by_label[rec['label']] = rec
    out['request_integrity'] = integrity
    out['request_records'] = len(requests)
    out['source_body_bytes'] = sum(r['bytes_received'] for r in requests)

    deposits = {}
    for species in ('human', 'mouse'):
        item = load(AUTHOR / ('sources/' + species + '_item.bin'))
        bundles = records(load(AUTHOR / ('sources/' + species + '_bundles.bin')), 'bundles')
        original = [b for b in bundles if b['name'] == 'ORIGINAL']
        assert len(original) == 1
        file_doc = load(AUTHOR / ('sources/' + species + '_files.bin'))
        files = records(file_doc, 'bitstreams')
        assert original[0]['uuid'] in by_label[species + '_files']['url']
        deposits[species] = {'item_uuid': item['uuid'], 'metadata': metadata_values(item),
            'original_bundle_uuid': original[0]['uuid'], 'listing_complete_by_page': True,
            'files': [{'name': f['name'], 'uuid': f['uuid'], 'size_bytes': f['sizeBytes'],
                       'declared_checksum': f['checkSum'],
                       'whole_file_digest_verified': False} for f in files]}
    out['deposits'] = deposits
    out['failed_content_responses'] = {}
    for label in ('human_readme', 'human_h5ad_prefix', 'mouse_rds_prefix'):
        payload = load(AUTHOR / by_label[label]['saved_file'])
        assert by_label[label]['status'] == 500 and payload['status'] == 500
        out['failed_content_responses'][label] = payload

    html = text_data(read(AUTHOR / 'sources/institutional_links.bin'))
    links = Links()
    links.feed(html)
    human_id, mouse_id = ('a2c833f7-b7f1-4f4d-ad31-cae478b601b7',
                           'dbb4e1ed-d820-4e83-981f-88ef7eb55a35')
    official = {key: [href for href in links.hrefs if key in href]
                for key in (human_id, mouse_id)}
    assert all(official.values())
    collection = load(AUTHOR / 'sources/mouse_collection.bin')
    dataset = [x for x in collection['datasets'] if mouse_id in json.dumps(x)][0]
    assets = [x for x in dataset['assets'] if x['filetype'].upper() == 'H5AD']
    assert len(assets) == 1
    asset = assets[0]
    index = load(AUTHOR / 'sources/cellxgene_collections.bin')
    if isinstance(index, dict):
        index = index.get('collections', index.get('data', []))
    selected_index = [c for c in index if any(identifier in json.dumps(c)
                      for identifier in (human_id, mouse_id))]
    out['official_mirror'] = {'official_links': official,
        'collection_id': collection.get('collection_id', collection.get('id')),
        'collection_version_id': collection.get('collection_version_id'),
        'dataset_id': dataset.get('dataset_id', dataset.get('id')),
        'dataset_version_id': dataset.get('dataset_version_id'), 'asset': asset,
        'source_index_selected_collections': selected_index}
    assert asset['filesize'] == 3_814_401_380

    ranges, etags = [], set()
    for rec in requests:
        if rec.get('status') != 206 or rec['url'] != asset['url']:
            continue
        headers = {k.lower(): v for k, v in rec['response_headers'].items()}
        match = re.fullmatch(r'bytes (\d+)-(\d+)/(\d+)', headers['content-range'])
        assert match and int(match[3]) == asset['filesize']
        start, end = int(match[1]), int(match[2])
        data = read(AUTHOR / rec['saved_file'])
        assert len(data) == end - start + 1
        assert headers.get('etag')
        etags.add(headers['etag'])
        ranges.append((start, end, data, rec['label']))
    assert len(etags) == 1
    out['mouse_ranges'] = {'responses': len(ranges), 'bytes': sum(len(r[2]) for r in ranges),
                            'etag': next(iter(etags)), 'new_requests': 0}
    virtual = SavedRanges(asset['filesize'], ranges)
    mouse = {'codes_values_decoded': False, 'category_cell_counts_computed': False,
             'mouse_expression_decoded': False}
    try:
        with h5py.File(virtual, 'r') as atlas:
            categories = atlas['obs/donor_id/categories'][:]
            cats = plain(categories)
            COUNTERS['category_decoded_bytes'] += categories.nbytes + sum(len(s.encode()) for s in cats)
            codes = atlas['obs/donor_id/codes']
            mouse.update({'categories': cats, 'n_categories': len(cats),
                'unique_categories': len(set(cats)),
                'single_run_labels': [s for s in cats if re.fullmatch(r'SRR[0-9]+', s)],
                'composite_run_labels': [s for s in cats if re.fullmatch(r'SRR[0-9]+(?:_SRR[0-9]+)+', s)],
                'pooled_labels': [s for s in cats if s == 'pooled'],
                'codes_schema': {'shape': list(codes.shape), 'dtype': str(codes.dtype),
                                 'chunks': plain(codes.chunks), 'compression': codes.compression}})
    except Exception as error:
        mouse['error'] = type(error).__name__ + ': ' + str(error)
        mouse['traceback'] = traceback.format_exc()
    finally:
        virtual.close()
    out['mouse_reconstruction'] = mouse
    out['mouse_logical_hdf5_reads'] = virtual.calls
    save('EARLY_DATA_CHECK.json', out)
    print(json.dumps({'checkpoint': 'independent_source_and_HDF5', 'source_responses': len(integrity),
                      'mouse': mouse, 'instrumented_bytes': COUNTERS}), flush=True)

    # Exact saved source definitions, kept separate from naming-based inference.
    datacite = load(AUTHOR / 'sources/mouse_datacite.bin')['data']['attributes']
    definitions = {'apollo_mouse_metadata': deposits['mouse']['metadata'],
        'datacite_descriptions': datacite.get('descriptions'),
        'collection_description': collection.get('description'),
        'dataset_description': dataset.get('description'),
        'dataset_named_metadata': {k: v for k, v in dataset.items()
                                   if any(s in k.lower() for s in ('donor', 'sample', 'batch', 'assay'))}}
    save('UNIT_SOURCE_DEFINITIONS.json', definitions)
    out['unit_diagnostic'] = {'evidence': 'UNIT_SOURCE_DEFINITIONS.json',
        'independent_biological_animals_certified': False,
        'missing_source_mapping': 'run/composite/pooled donor categories -> independent biological animals',
        'interpretation': 'Finite saved definitions do not establish one-category-one-mouse; no universal absence or impossibility claim.'}

    # Parse the exact frozen panel from prose; do not import the author's mask.
    protocol = text_data(read(PROTOCOL))
    panel_text = re.search(r'Fixed target set \(54 symbols, actual count checked by code\): (.*?)\. This includes',
                           protocol, re.S).group(1)
    panel = {s.strip() for s in panel_text.split(',')}
    assert len(panel) == 54
    feature_rows = list(csv.DictReader(io.StringIO(text_data(read(LEAF / 'raw_var.csv')))))
    obs_rows = list(csv.DictReader(io.StringIO(text_data(read(LEAF / 'peptide_obs.csv')))))
    assert len(feature_rows) == 36_924
    assert len({r['row_index'] for r in obs_rows}) == len(obs_rows)
    assert len({r['_index'] for r in obs_rows}) == len(obs_rows)
    assert [int(r['column_index']) for r in feature_rows] == list(range(len(feature_rows)))
    assert len({r['_index'] for r in feature_rows}) == len(feature_rows)
    obs = {int(r['row_index']): r for r in obs_rows}
    archive = read(LEAF / 'normalization_check_vectors.npz')
    human_rows = []
    with np.load(io.BytesIO(archive), allow_pickle=False) as leaf:
        row_ids = sorted(int(k[:-4]) for k in leaf.files if k.endswith('_raw'))
        assert len(row_ids) == len(set(row_ids)) == 6
        for rowid in row_ids:
            values, indices = leaf[str(rowid) + '_raw'], leaf[str(rowid) + '_indices']
            COUNTERS['human_array_bytes'] += values.nbytes + indices.nbytes
            assert values.ndim == indices.ndim == 1 and len(values) == len(indices)
            assert np.issubdtype(indices.dtype, np.integer)
            assert np.all((indices >= 0) & (indices < len(feature_rows)))
            assert np.all(np.diff(indices.astype(np.int64)) > 0), 'Noncanonical or duplicate feature index'
            # Only index identity is inspected until the receptor mask is applied.
            non_target_positions = [j for j, col in enumerate(indices)
                                    if feature_rows[int(col)]['feature_name'].upper() not in panel]
            masked = values[non_target_positions]
            assert np.all(np.isfinite(masked)) and np.all(masked > 0)
            assert np.all(masked == np.rint(masked))
            metadata = obs[rowid]
            witnesses = []
            for j in non_target_positions[:3]:
                col = int(indices[j])
                witnesses.append({'column_index': col, 'feature_id': feature_rows[col]['_index'],
                                  'feature_name': feature_rows[col]['feature_name'], 'count': float(values[j])})
            human_rows.append({'source_row_index': rowid,
                'barcode': metadata['_index'], 'donor_id': metadata['donor_id'],
                'sample_id': metadata['Sample_ID'], 'source_study': metadata['Dataset'],
                'cluster': metadata['C4_named'], 'non_target_entries': len(masked),
                'non_target_count_sum': float(np.sum(masked, dtype=np.float64)),
                'finite_positive_integer': True, 'strictly_increasing_unique_feature_indices': True,
                'first_three_non_target_entries': witnesses})
    out['human_reconstruction'] = {'features': len(feature_rows), 'feature_columns': list(feature_rows[0]),
        'all_feature_column_indices_equal_csv_positions': True,
        'feature_ids_unique': True, 'observation_row_ids_and_barcodes_unique': True,
        'observation_leaf_rows': len(obs_rows), 'target_panel_size': len(panel),
        'target_panel': sorted(panel), 'cells': human_rows,
        'n_cells': len(human_rows), 'donors': sorted({r['donor_id'] for r in human_rows}),
        'non_target_entries': sum(r['non_target_entries'] for r in human_rows),
        'new_pristine_evaluation': False, 'raw_arrays_prior_target_exposure_preserved': True,
        'normalized_X_arrays_read': False, 'receptor_scores_computed': False,
        'source_asset_link': 'Inherited prior pinned extraction; this run does not reopen original HDF5.'}
    save('RECONSTRUCTION.json', out)
    print(json.dumps({'checkpoint': 'independent_human_rows', 'human': out['human_reconstruction'],
                      'instrumented_bytes': COUNTERS}), flush=True)

    # Compare only after actual independent source/array outputs are saved.
    old = load(AUTHOR / 'INPUT_AUDIT.json')
    old_rows = {r['source_row_index']: r for r in old['human_reused_small_sample']['cells']}
    comparisons = []
    for row in human_rows:
        inherited = old_rows[row['source_row_index']]
        checks = {'barcode': row['barcode'] == inherited['barcode'],
                  'donor': row['donor_id'] == inherited['donor_id'],
                  'sample': row['sample_id'] == inherited['Sample_ID'],
                  'study': row['source_study'] == inherited['Dataset'],
                  'cluster': row['cluster'] == inherited['C4_named'],
                  'entries': row['non_target_entries'] == inherited['non_target_stored_entries'],
                  'sum': row['non_target_count_sum'] == inherited['non_target_count_sum']}
        assert all(checks.values())
        comparisons.append({'source_row_index': row['source_row_index'], 'checks': checks})
    comparison = {'human_row_comparisons': comparisons,
        'mouse_categories_equal_prior_exposed_list': mouse.get('categories') ==
            old['mouse_units']['single_SRA_run_labels'] + old['mouse_units']['pooled_labels'] + old['mouse_units']['composite_SRA_run_labels'],
        'mouse_schema_equal_author': mouse.get('codes_schema') == old['mouse_units'].get('codes_structure')}
    save('AUTHOR_COMPARISON.json', comparison)
    artifact_manifest = load(AUTHOR / 'ARTIFACT_MANIFEST.json')
    stable_checks = []
    for pin in artifact_manifest['stable_owned_artifacts']:
        data = read(AUTHOR / pin['path'])
        actual = next(p for p in PINS if p['path'] == str((AUTHOR / pin['path']).relative_to(REPO)))
        assert len(data) == pin['bytes'] and actual['sha256'] == pin['sha256']
        stable_checks.append({'path': pin['path'], 'size_and_sha256_pass': True})
    source_manifest = load(AUTHOR / 'SOURCE_MANIFEST.json')
    leaf_checks = []
    for pin in source_manifest['human_reused_small_sample']['original_leaf_file_pins']:
        actual = next(p for p in PINS if p['path'] == pin['path'])
        assert actual['bytes'] == pin['bytes'] and actual['sha256'] == pin['sha256']
        leaf_checks.append({'path': pin['path'], 'size_and_sha256_pass': True})
    out['author_stable_artifact_integrity'] = stable_checks
    out['human_leaf_pin_integrity'] = leaf_checks
    out['finished_utc'] = now().isoformat()
    out['peak_rss_bytes_macos'] = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    out['versions'] = {'python': sys.version.split()[0], 'numpy': np.__version__,
                       'h5py': h5py.__version__, 'HDF5': h5py.version.hdf5_version}
    out['thread_environment'] = {k: os.environ.get(k) for k in
        ('OPENBLAS_NUM_THREADS', 'OMP_NUM_THREADS', 'MKL_NUM_THREADS', 'VECLIB_MAXIMUM_THREADS', 'NUMEXPR_NUM_THREADS')}
    out['instrumented_bytes'] = COUNTERS.copy()
    save('RECONSTRUCTION.json', out)
    save('INPUT_PINS.json', {'files': PINS, 'all_original_files_read_only': True})
    instrumented = sum(COUNTERS.values())
    accounting = {'start_authorized_utc': '2026-10-31T20:16:34.468Z',
        'deadline_utc': DEADLINE.isoformat(), 'scientific_process_started_utc': out['started_utc'],
        'scientific_process_finished_utc': out['finished_utc'], 'instrumented_components': COUNTERS,
        'instrumented_read_decode_and_hash_bytes': instrumented,
        'conservative_extra_allowances': {'context_code_failed_commands_tool_outputs': 30_000_000,
            'unmetered_JSON_CSV_HDF5_decoding_and_temporary_copies': 10_000_000,
            'closeout_records_verification_report_and_pins': 10_000_000},
        'additional_review_bytes_charged': instrumented + 50_000_000,
        'additional_review_cap_bytes': 100_000_000,
        'exact_OS_level_metering': False, 'new_public_requests': 0,
        'one_scientific_process': True, 'numerical_threads': 1,
        'instrumented_peak_rss_bytes_macos': out['peak_rss_bytes_macos'],
        'whole_turn_continuous_RSS_profiling': False,
        'inherited_molecular_pilot_review_bytes': 264_532_918,
        'inherited_input_author_bytes': 250_000_000,
        'additive_molecular_read_decode_bytes': 514_532_918 + instrumented + 50_000_000,
        'author_operations_36_and_charged_ingress_24494128_preserved': True,
        'old_HYPOMAP_range_ingress_bytes_separate_unchanged': 3_277_786_552,
        'old_memory_read_decode_lineage_bytes_separate_unchanged': 7_774_826_112,
        'historic_full_atlas_or_range_cache_bytes_reread': 0,
        'blocked_commands': ['initial ordinary composed shell read denied before execution',
            'direct cat of source .bin denied before execution; scoped registered code uses authorized files',
            'ordinary rg across nonexistent speculative config paths denied before execution'],
        'jobs_at_completion': 0}
    assert accounting['additional_review_bytes_charged'] <= 100_000_000
    save('ACCOUNTING.json', accounting)
    print(json.dumps({'checkpoint': 'complete', 'stable_artifacts_passed': len(stable_checks),
        'leaf_pins_passed': len(leaf_checks), 'review_bytes_charged': accounting['additional_review_bytes_charged'],
        'peak_rss_bytes': out['peak_rss_bytes_macos'], 'jobs': 0}), flush=True)


if __name__ == '__main__':
    try:
        main()
    except Exception as error:
        save('FAILED_PASS.json', {'error': type(error).__name__ + ': ' + str(error),
            'traceback': traceback.format_exc(), 'instrumented_components': COUNTERS,
            'known_file_pins': PINS, 'saved_utc': now().isoformat(),
            'new_requests': 0, 'jobs_after_exit': 0})
        raise
