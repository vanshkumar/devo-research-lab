"""One HypoMap H5AD metadata sample, bounded to nine MiB and total request cap.

Uses the task's acquisition routine for each explicitly verified range. Does
not inspect target expression or old range caches; no get_storage_size calls.
"""
import collections
import contextlib
import io
import json
from pathlib import Path
import resource
import re
import sys
import traceback

import h5py
import numpy as np
import acquire

ROOT = Path(__file__).resolve().parent
BLOCK = 1 << 20


def plain(x):
    if isinstance(x, bytes):
        return x.decode('utf-8')
    if isinstance(x, np.ndarray):
        return [plain(y) for y in x]
    if isinstance(x, np.generic):
        return plain(x.item())
    if isinstance(x, dict):
        return {str(k): plain(v) for k, v in x.items()}
    if isinstance(x, (list, tuple)):
        return [plain(y) for y in x]
    return x


class SampleFile(io.RawIOBase):
    def __init__(self, species, url, size, offline=False):
        self.species, self.url, self.size = species, url, size
        self.pos, self.memory, self.etag = 0, {}, None
        self.logical_read_bytes = 0
        self.offline = offline

    def readable(self):
        return True

    def seekable(self):
        return True

    def tell(self):
        return self.pos

    def seek(self, offset, whence=0):
        self.pos = offset if whence == 0 else self.pos + offset if whence == 1 else self.size + offset
        assert 0 <= self.pos <= self.size
        return self.pos

    def block(self, block_id):
        if block_id not in self.memory:
            ledger = json.loads((ROOT / 'REQUESTS.json').read_text())
            ranges = [x for x in ledger if '_block_' in x['label']]
            start, end = block_id * BLOCK, min((block_id + 1) * BLOCK, self.size) - 1
            label = self.species + '_block_' + str(block_id)
            existing = [x for x in ranges if x['label'] == label]
            if not existing:
                assert not self.offline, 'Required range absent from this offline sample: %d-%d' % (start, end)
                assert sum(x['bytes_received'] for x in ranges) + end - start + 1 <= 9 * BLOCK, 'Sample byte ceiling'
                old_argv = sys.argv
                try:
                    sys.argv = ['acquire.py', label, self.url, str(end - start + 1), 'bytes=%d-%d' % (start, end)]
                    with contextlib.redirect_stdout(io.StringIO()):
                        acquire.main()
                finally:
                    sys.argv = old_argv
                ledger = json.loads((ROOT / 'REQUESTS.json').read_text())
                existing = [x for x in ledger if x['label'] == label]
            rec = existing[0]
            assert rec.get('status') == 206, rec
            headers = {k.lower(): v for k, v in rec['response_headers'].items()}
            assert headers['content-range'] == 'bytes %d-%d/%d' % (start, end, self.size), rec
            if self.etag is None:
                self.etag = headers.get('etag')
            assert self.etag and headers.get('etag') == self.etag
            data = (ROOT / rec['saved_file']).read_bytes()
            assert len(data) == end - start + 1
            self.memory[block_id] = data
            print('sample_range', self.species, start, end, 'cached_blocks', len(self.memory), flush=True)
        return self.memory[block_id]

    def read(self, n=-1):
        assert 0 <= n <= 2_000_000, 'Reject implicit whole-file or large logical read'
        n = min(n, self.size - self.pos)
        self.logical_read_bytes += n
        end, pieces = self.pos + n, []
        while self.pos < end:
            data = self.block(self.pos // BLOCK)
            lo = self.pos % BLOCK
            take = min(end - self.pos, len(data) - lo)
            pieces.append(data[lo:lo + take])
            self.pos += take
        return b''.join(pieces)

    def readinto(self, buf):
        data = self.read(len(buf))
        buf[:len(data)] = data
        return len(data)


class FocusedUnitsFile(SampleFile):
    """Reuse inspected sample, then at most four exact donor-metadata reads."""
    def __init__(self, *args):
        super().__init__(*args)
        self.new_requests = 0

    def read(self, n=-1):
        assert 0 <= n <= 2_000_000
        n = min(n, self.size - self.pos)
        self.logical_read_bytes += n
        stop, pieces = self.pos + n, []
        while self.pos < stop:
            records = json.loads((ROOT / 'REQUESTS.json').read_text())
            available = []
            for rec in records:
                if rec['url'] != self.url or rec.get('status') != 206:
                    continue
                headers = {k.lower(): v for k, v in rec['response_headers'].items()}
                match = re.fullmatch(r'bytes (\d+)-(\d+)/(\d+)', headers.get('content-range', ''))
                assert match and int(match[3]) == self.size
                start, end = int(match[1]), int(match[2])
                assert headers.get('etag')
                if self.etag is None:
                    self.etag = headers['etag']
                assert self.etag == headers['etag']
                if start <= self.pos <= end:
                    available.append((start, end, rec))
            if not available:
                assert self.new_requests < 4, 'Four-request focused-unit ceiling'
                end = min(stop, self.pos + 1_000_000) - 1
                label = self.species + '_units_' + str(self.pos)
                old_argv = sys.argv
                try:
                    sys.argv = ['acquire.py', label, self.url, str(end - self.pos + 1), 'bytes=%d-%d' % (self.pos, end)]
                    with contextlib.redirect_stdout(io.StringIO()):
                        acquire.main()
                finally:
                    sys.argv = old_argv
                self.new_requests += 1
                print('focused_unit_range', self.pos, end, 'new_requests', self.new_requests, flush=True)
                continue
            start, end, rec = available[0]
            if rec['label'] not in self.memory:
                self.memory[rec['label']] = (ROOT / rec['saved_file']).read_bytes()
            data = self.memory[rec['label']]
            assert len(data) == end - start + 1
            take = min(stop - self.pos, end - self.pos + 1)
            pieces.append(data[self.pos - start:self.pos - start + take])
            self.pos += take
        return b''.join(pieces)


def main():
    species = sys.argv[1]
    offline_units = len(sys.argv) > 2 and sys.argv[2] == 'offline-units'
    focused_units = len(sys.argv) > 2 and sys.argv[2] == 'focused-units'
    if species == 'mouse':
        meta = json.loads((ROOT / 'sources/mouse_collection.bin').read_text())
        asset = meta['datasets'][0]['assets'][0]
        url, size = asset['url'], asset['filesize']
    else:
        assert species == 'human'
        url, size = 'https://datasets.cellxgene.cziscience.com/af06d70d-a2bc-43c1-8378-bc545bc8ee2c.h5ad', 5231283640
    rf = FocusedUnitsFile(species, url, size) if focused_units else SampleFile(species, url, size, offline=offline_units)
    out = {'species': species, 'url': url, 'size': size, 'expression_values_interpreted': 0}
    try:
        with h5py.File(rf, 'r') as h:
            out['root_keys'] = list(h)
            out['obs_keys'] = list(h['obs'])
            if not (offline_units or focused_units):
                out['var_keys'] = list(h['var'])
                out['X_attrs'] = plain(dict(h['X'].attrs))
            out['units'] = {}
            for key in ['donor_id', 'Sample_ID', 'Batch_ID', 'Dataset']:
                if key not in h['obs']:
                    out['units'][key] = {'present': False}
                    continue
                obj = h['obs'][key]
                if isinstance(obj, h5py.Group):
                    cats = plain(obj['categories'][:])
                    out['units'][key] = {'present': True, 'categories': cats, 'counts': 'not yet decoded'}
                    codes = obj['codes'][:]
                    hist = collections.Counter(map(int, codes))
                    out['units'][key] = {'present': True, 'n_rows': len(codes), 'n_categories': len(cats),
                                         'counts': {str(cats[i]) if i >= 0 else '<missing>': v for i, v in sorted(hist.items())}}
                else:
                    vals = plain(obj[:])
                    out['units'][key] = {'present': True, 'n_rows': len(vals), 'counts': dict(collections.Counter(vals))}
                print('sample_unit', key, json.dumps(out['units'][key])[:1500], flush=True)
    except Exception as err:
        out['error'] = type(err).__name__ + ': ' + str(err)
        out['traceback'] = traceback.format_exc()
        print(out['error'], flush=True)
    finally:
        out['etag'] = rf.etag
        out['logical_hdf5_read_bytes'] = rf.logical_read_bytes
        out['physical_blocks'] = sorted(rf.memory)
        out['peak_rss_bytes_macos'] = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        suffix = '_FOCUSED_UNITS_CHECK.json' if focused_units else '_UNITS_CHECK.json' if offline_units else '_SAMPLE_CHECK.json'
        (ROOT / (species.upper() + suffix)).write_text(json.dumps(out, indent=2) + '\n')
        rf.close()
        print(json.dumps(out, indent=2), flush=True)


if __name__ == '__main__':
    main()
