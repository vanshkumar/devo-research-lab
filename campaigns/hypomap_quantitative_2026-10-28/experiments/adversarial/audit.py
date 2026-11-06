"""Independent, offline reconstruction from original HDF5 cached byte ranges.

No acquisition/extraction/analysis function is imported. Derived CSVs are opened
only after the raw reconstruction, for disagreement checks. A cache miss fails.
"""
import csv
import hashlib
import io
import json
import math
import platform
from collections import Counter, OrderedDict, defaultdict
from fractions import Fraction
from pathlib import Path

import h5py
import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
CACHE = ROOT / 'inputs/range_cache'
URL = 'https://datasets.cellxgene.cziscience.com/af06d70d-a2bc-43c1-8378-bc545bc8ee2c.h5ad'
SIZE = 5231283640
BLOCK = 1048576


def sha(path):
    h = hashlib.sha256()
    with path.open('rb') as f:
        for b in iter(lambda: f.read(1024 * 1024), b''):
            h.update(b)
    return h.hexdigest()


class OfflineBytes(io.RawIOBase):
    def __init__(self):
        self.position = 0
        self.recent = OrderedDict()
        self.evidence = {}

    def readable(self): return True
    def seekable(self): return True
    def tell(self): return self.position

    def seek(self, offset, whence=io.SEEK_SET):
        if whence == io.SEEK_SET: new = offset
        elif whence == io.SEEK_CUR: new = self.position + offset
        elif whence == io.SEEK_END: new = SIZE + offset
        else: raise ValueError(whence)
        if new < 0: raise ValueError('negative position')
        self.position = new
        return new

    def block(self, number):
        if number in self.recent:
            self.recent.move_to_end(number)
            return self.recent[number]
        start = number * BLOCK
        end = min(start + BLOCK, SIZE) - 1
        p = CACHE / f'{start:012d}-{end:012d}.bin'
        m = p.with_suffix('.json')
        if not p.exists() or not m.exists():
            raise FileNotFoundError(f'OFFLINE cache miss: {p}')
        data = p.read_bytes()
        digest = hashlib.sha256(data).hexdigest()
        meta = json.loads(m.read_text())
        headers = {k.lower(): v for k, v in meta['headers'].items()}
        assert len(data) == end - start + 1 == meta['size']
        assert meta['start'] == start and meta['end'] == end
        assert meta['sha256'] == digest and meta['url'] == URL
        assert meta['status'] == 206
        assert headers['content-range'] == f'bytes {start}-{end}/{SIZE}'
        self.evidence[number] = dict(file=p.name, start=start, end=end,
            sha256=digest, metadata_sha256=sha(m), bytes=len(data),
            etag=headers.get('etag'), version_id=headers.get('x-amz-version-id'))
        self.recent[number] = data
        if len(self.recent) > 12: self.recent.popitem(last=False)
        return data

    def read(self, size=-1):
        stop = SIZE if size < 0 else min(SIZE, self.position + size)
        pieces = []
        while self.position < stop:
            number, offset = divmod(self.position, BLOCK)
            b = self.block(number)
            take = min(stop - self.position, len(b) - offset)
            pieces.append(b[offset:offset + take])
            self.position += take
        return b''.join(pieces)

    def readinto(self, destination):
        data = self.read(len(destination))
        destination[:len(data)] = data
        return len(data)


def scalar(x):
    if isinstance(x, bytes): return x.decode('utf-8')
    if isinstance(x, np.generic): return x.item()
    return x


def column(group, name):
    item = group[name]
    if isinstance(item, h5py.Dataset): return [scalar(x) for x in item[:]]
    cats = [scalar(x) for x in item['categories'][:]]
    return [None if code < 0 else cats[int(code)] for code in item['codes'][:]]


def qualifies(row, k=10, r='0.1', d='0'):
    # Exact rational comparisons on integer-valued data, avoiding float32 ratios.
    rr, dd = Fraction(str(r)), Fraction(str(d))
    return (row['minor'] >= k and
            row['minor'] * rr.denominator >= row['major'] * rr.numerator and
            row['minor'] * dd.denominator >= row['T'] * dd.numerator)


def summary(rows):
    n = len(rows)
    count = sum(qualifies(r) for r in rows)
    high_major = [r for r in rows if r['major'] >= 100]
    return dict(n=n, OXT_positive=sum(r['OXT'] > 0 for r in rows),
        AVP_positive=sum(r['AVP'] > 0 for r in rows),
        joint=sum(r['OXT'] > 0 and r['AVP'] > 0 for r in rows),
        primary=count, primary_depth=sum(qualifies(r, d='.001') for r in rows),
        k20_r10=sum(qualifies(r, k=20) for r in rows),
        median_minor=float(np.median([r['minor'] for r in rows])),
        minor_le5=sum(r['minor'] <= 5 for r in rows),
        median_ratio=float(np.median([r['minor'] / max(r['major'], 1) for r in rows])),
        median_major=float(np.median([r['major'] for r in rows])),
        major_lt10=sum(r['major'] < 10 for r in rows),
        major_lt100=sum(r['major'] < 100 for r in rows),
        high_major_posthoc_n=len(high_major),
        high_major_posthoc_median_minor=float(np.median([r['minor'] for r in high_major])) if high_major else None,
        high_major_posthoc_primary=sum(qualifies(r) for r in high_major),
        zero_case_one_sided_binomial_upper95=(1 - .05 ** (1/n)) if count == 0 else None,
        promotion_support=n >= 20 and count >= 10 and count/n >= .2)


def write_csv(path, records):
    if not records: return
    with path.open('w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=list(records[0]))
        w.writeheader()
        w.writerows(records)


def main():
    rf = OfflineBytes()
    cells = []
    with h5py.File(rf, 'r') as h:
        labels = column(h['obs'], 'C4_named')
        selected = [i for i, label in enumerate(labels) if str(label).startswith('C4-313 ')]
        columns = {key: column(h['obs'], key) for key in
            ['_index', 'donor_id', 'Dataset', 'Sample_ID', 'nCount_RNA', 'nFeature_RNA', 'percent_mt']}
        names = column(h['raw/var'], 'feature_name')
        ids = column(h['raw/var'], '_index')
        gene_columns = {}
        for gene in ['OXT', 'AVP']:
            hits = [i for i, name in enumerate(names) if name == gene]
            assert len(hits) == 1
            gene_columns[gene] = dict(column=hits[0], ensembl=ids[hits[0]])
        mt = {i for i, name in enumerate(names) if name.startswith('MT-')}
        raw = h['raw/X']
        assert scalar(raw.attrs['encoding-type']) == 'csr_matrix'
        ptr = raw['indptr'][:]
        assert len(ptr) == len(labels) + 1 and int(ptr[-1]) == len(raw['data'])
        assert all(int(ptr[i]) <= int(ptr[i+1]) for i in range(len(ptr)-1))
        structure = dict(shape=[int(x) for x in raw.attrs['shape']], nnz=int(ptr[-1]),
                         dtype=str(raw['data'].dtype), raw_object_address=int(h5py.h5o.get_info(raw.id).addr))
        for row in selected:
            left, right = int(ptr[row]), int(ptr[row + 1])
            ix = raw['indices'][left:right]
            val = raw['data'][left:right]
            assert len(ix) == len(set(map(int, ix))), f'duplicate column: {row}'
            assert np.all(np.isfinite(val)) and np.all(val >= 0) and np.all(val == np.floor(val))
            # Python integers sum the sparse row and independently locate each gene.
            counts = {int(j): int(v) for j, v in zip(ix, val)}
            O, A = (counts.get(gene_columns[g]['column'], 0) for g in ['OXT', 'AVP'])
            record = dict(row_index=row, barcode=columns['_index'][row],
                C4_named=labels[row], donor_id=columns['donor_id'][row],
                Dataset=columns['Dataset'][row], Sample_ID=columns['Sample_ID'][row],
                OXT=O, AVP=A, minor=min(O, A), major=max(O, A), T=sum(counts.values()),
                nFeature_actual=sum(v > 0 for v in counts.values()),
                mt_count=sum(v for j, v in counts.items() if j in mt),
                metadata_nCount=columns['nCount_RNA'][row],
                metadata_nFeature=columns['nFeature_RNA'][row],
                metadata_percent_mt=columns['percent_mt'][row],
                csr_left=left, csr_right=right,
                csr_indices_sha256=hashlib.sha256(ix.tobytes()).hexdigest(),
                csr_data_sha256=hashlib.sha256(val.tobytes()).hexdigest())
            cells.append(record)
    rf.close()
    assert len({r['barcode'] for r in cells}) == len(cells)
    write_csv(HERE / 'independent_candidate_counts.csv', cells)
    donor_groups, study_groups = defaultdict(list), defaultdict(list)
    for row in cells:
        donor_groups[row['donor_id']].append(row)
        study_groups[row['Dataset']].append(row)
    donors = {d: summary(z) | {'Dataset': z[0]['Dataset']} for d, z in donor_groups.items()}
    grid = []
    for donor, z in donor_groups.items():
        for k in [1, 2, 5, 10, 20, 50, 100]:
            for ratio in ['0', '.01', '.05', '.10', '.25', '.50']:
                for depth in ['0', '.0001', '.0005', '.001', '.005', '.01']:
                    grid.append(dict(donor_id=donor, k=k, ratio_min=ratio,
                        depth_fraction_min=depth, n=len(z), positive=sum(qualifies(r, k, ratio, depth) for r in z)))
    write_csv(HERE / 'independent_threshold_grid.csv', grid)

    # Freeze reconstructed data before consulting dependent analysis outputs.
    manifest = [rf.evidence[k] for k in sorted(rf.evidence)]
    assert len({m['etag'] for m in manifest}) == 1 and len({m['version_id'] for m in manifest}) == 1
    (HERE / 'accessed_byte_manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
    with (ROOT / 'outputs/abundance/candidate_per_cell.csv').open() as f:
        dependent = {int(r['row_index']): r for r in csv.DictReader(f)}
    mismatches = []
    if set(dependent) != {r['row_index'] for r in cells}: mismatches.append('candidate row set')
    for row in cells:
        old = dependent[row['row_index']]
        for field in ['OXT', 'AVP', 'T', 'nFeature_actual']:
            if float(old[field]) != row[field]: mismatches.append([row['row_index'], field])
        for a, b in [('barcode', '_index'), ('donor_id', 'donor_id'), ('Dataset', 'Dataset'), ('Sample_ID', 'Sample_ID'), ('C4_named', 'C4_named')]:
            if row[a] != old[b]: mismatches.append([row['row_index'], a])
        if qualifies(row) != (old['substantial'] == 'True'): mismatches.append([row['row_index'], 'primary'])
    grid_lookup = {(r['donor_id'], r['k'], Fraction(r['ratio_min']), Fraction(r['depth_fraction_min'])): r for r in grid}
    checked = 0
    with (ROOT / 'outputs/abundance/threshold_grid.csv').open() as f:
        for row in csv.DictReader(f):
            if row['cluster'] != 'C4-313': continue
            key = (row['donor_id'], int(row['k']), Fraction(row['ratio_min']), Fraction(row['depth_fraction_min']))
            actual = grid_lookup[key]
            if actual['positive'] != int(row['positive']) or actual['n'] != int(row['n']): mismatches.append(['grid', str(key)])
            checked += 1
    assert checked == len(grid)
    eligibility = []
    for d in donor_groups:
        test = donor_groups[d]
        train = [r for r in cells if r['donor_id'] != d and donors[r['donor_id']]['n'] >= 20]
        eligibility.append(dict(heldout_donor=d, test_n=len(test), test_positive=sum(qualifies(r) for r in test),
            training_n=len(train), training_positive=sum(qualifies(r) for r in train),
            train_has_both_classes=0 < sum(qualifies(r) for r in train) < len(train)))
    write_csv(HERE / 'signature_eligibility.csv', eligibility)
    result = dict(reconstruction='offline original HDF5 raw/X direct CSR; no extraction/analysis imports',
        blinded=False, source_url=URL, byte_size=SIZE, structure=structure, genes=gene_columns,
        cached_blocks_verified=len(manifest), cached_bytes_verified=sum(m['bytes'] for m in manifest),
        version_id=manifest[0]['version_id'], etag=manifest[0]['etag'],
        pooled=summary(cells), donors=donors, studies={s: summary(z) for s, z in study_groups.items()},
        primary_rows=[r for r in cells if qualifies(r)],
        signature_eligibility=eligibility,
        compared_candidate_rows=len(cells), compared_grid_rows=checked, mismatches=mismatches,
        all_target_totals_below_metadata=all(r['T'] < r['metadata_nCount'] for r in cells),
        maximum_target_count_deficit=max(r['metadata_nCount'] - r['T'] for r in cells),
        maximum_target_feature_deficit=max(r['metadata_nFeature'] - r['nFeature_actual'] for r in cells),
        mt_metadata_max_error_by_study={s: max(abs(r['mt_count']/r['metadata_nCount'] - r['metadata_percent_mt']/(100 if s == 'Tadross' else 1)) for r in z) for s, z in study_groups.items()},
        artifacts={p.name: sha(p) for p in [HERE/'audit.py', HERE/'independent_candidate_counts.csv', HERE/'independent_threshold_grid.csv', HERE/'accessed_byte_manifest.json', ROOT/'PROTOCOL.md', ROOT/'AMENDMENTS.md', ROOT/'outputs/abundance/candidate_per_cell.csv', ROOT/'outputs/abundance/threshold_grid.csv']},
        environment=dict(python=platform.python_version(), h5py=h5py.__version__, numpy=np.__version__))
    (HERE / 'audit_result.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps({k: result[k] for k in ['pooled', 'donors', 'compared_grid_rows', 'mismatches', 'cached_blocks_verified']}, indent=2))
    if mismatches: raise AssertionError(mismatches)


if __name__ == '__main__': main()
