"""Bounded metadata-only projection; answers remain uninterpreted bytes."""
import os
for key in ('OPENBLAS_NUM_THREADS', 'OMP_NUM_THREADS', 'MKL_NUM_THREADS', 'VECLIB_MAXIMUM_THREADS'):
    os.environ[key] = '2'
import calendar
import argparse
from collections import Counter
import datetime as dt
import gzip
import hashlib
import json
from pathlib import Path
import resource
import sys
import tarfile
import time
import numpy as np

ROOT = Path('/Users/vanshkumar/Documents/repos/devo-research-lab')
OUT = ROOT / 'sources/memory_policy_transfer_2026-10-30'
ARCHIVE = OUT / 'stats-20191220-20200731.tar.gz'
CAP = 8_000_000_000
EXPECTED = [b'platform', b'platformversion', b'device', b'appid', b'appversion', b'flavor', b'user', b'algorithm', b'language', b'set', b'test', b'learn', b'category', b'question', b'difficulty', b'reply', b'datecreated', b'dateinstallation', b'correct', b'count', b'countsequence', b'seconds']
DTYPE = np.dtype([('uid','u4'), ('item','u4'), ('time','i8'), ('install','i8'), ('arm','u4'), ('category','u4'), ('mode','u4'), ('count','i4'), ('sequence','i4'), ('ordinal','u8')])
MONTHS = {name.encode(): i + 1 for i, name in enumerate(('Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'))}

def unquote(value):
    return value[1:-1].replace(b'""', b'"') if value.startswith(b'"') and value.endswith(b'"') else value

def fields(record):
    record = record.rstrip(b'\r\n')
    basic = record.split(b',')
    if len(basic) == len(EXPECTED):
        return [unquote(x) for x in basic]
    values, start, quoted, i = [], 0, False, 0
    while i < len(record):
        if record[i] == 34:
            if quoted and i + 1 < len(record) and record[i+1] == 34:
                i += 2
                continue
            quoted = not quoted
        elif record[i] == 44 and not quoted:
            values.append(unquote(record[start:i]))
            start = i + 1
        i += 1
    if quoted:
        raise ValueError('Unclosed quoted record')
    values.append(unquote(record[start:]))
    if len(values) != len(EXPECTED):
        raise ValueError('Schema field-count mismatch')
    return values

def timestamp(raw):
    bits = raw.split()
    if len(bits) >= 6 and bits[1] in MONTHS:
        if bits[5] != b'GMT+0000':
            raise ValueError('Non-UTC timestamp requires explicit handling')
        h, m, s = [int(x) for x in bits[4].split(b':')]
        return calendar.timegm((int(bits[3]), MONTHS[bits[1]], int(bits[2]), h, m, s))
    return int(dt.datetime.fromisoformat(raw.decode().replace('Z','+00:00')).timestamp())

def integer(raw):
    try:
        return int(raw)
    except ValueError:
        return -999999

class Counted:
    def __init__(self, stream, previous=0):
        self.stream, self.n, self.previous = stream, 0, previous
    def read(self, n=-1):
        block = self.stream.read(n)
        self.n += len(block)
        if self.n + self.previous > CAP:
            raise RuntimeError('Decoded-byte cap exceeded')
        return block

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--corrected-window', action='store_true')
    args = parser.parse_args()
    previous = 0
    if args.corrected_window:
        if (OUT/'metadata_parts_failed').exists() or not (OUT/'METADATA_FAILED.json').exists():
            raise RuntimeError('Only one accounted correction is allowed')
        failed = json.loads((OUT/'METADATA_FAILED.json').read_text())
        previous = failed['decoded_bytes']
        (OUT/'metadata_parts').rename(OUT/'metadata_parts_failed')
        (OUT/'opaque_answers').rename(OUT/'opaque_answers_failed')
    if (OUT / 'METADATA.json').exists() or (OUT / 'metadata_parts').exists():
        raise RuntimeError('Refusing a repeated metadata scan')
    (OUT / 'metadata_parts').mkdir()
    (OUT / 'opaque_answers').mkdir()
    arms, cats, modes, itemmap, usermap = {}, {}, {}, {}, {}
    selected, handles, installcache = [], {}, {}
    rows, parts, totalrows, members, armcounts, multimode = [], [], 0, [], Counter(), 0
    t0 = time.monotonic()
    def intern(mapping, value):
        if value not in mapping:
            mapping[value] = len(mapping)
        return mapping[value]
    def flush():
        if rows:
            part = 'metadata_parts/part_%03d.npy' % len(parts)
            np.save(OUT / part, np.array(rows, dtype=DTYPE), allow_pickle=False)
            parts.append({'path': part, 'rows': len(rows)})
            rows.clear()
    counted = None
    try:
        with gzip.open(ARCHIVE, 'rb') as zipped:
            counted = Counted(zipped, previous)
            with tarfile.open(fileobj=counted, mode='r|') as tar:
                for member in tar:
                    if args.corrected_window and member.name.startswith('stats_') and member.name > 'stats_20200531.csv':
                        break
                    members.append({'name': member.name, 'size': member.size, 'is_file': member.isfile()})
                    if member.size > CAP or sum(x['size'] for x in members) > CAP:
                        raise RuntimeError('Declared member sizes exceed decoded cap')
                    if not member.isfile() or not member.name.endswith('.csv'):
                        continue
                    stream = tar.extractfile(member)
                    header = fields(stream.readline())
                    if header != EXPECTED:
                        raise RuntimeError('Header differs from verified schema')
                    nfile = 0
                    for line in stream:
                        if not line.strip():
                            continue
                        # Quoted embedded newlines remain opaque until the full CSV record ends.
                        if line.count(b'"') % 2:
                            for continuation in stream:
                                line += continuation
                                if len(line) > 65536:
                                    raise RuntimeError('Oversized CSV record')
                                if not line.count(b'"') % 2:
                                    break
                        cols = fields(line)
                        totalrows += 1
                        nfile += 1
                        arm = intern(arms, cols[7])
                        armcounts[arm] += 1
                        rawuser = cols[6]
                        if rawuser not in usermap:
                            digest = hashlib.sha256(b'memory-policy-2026-10-30/' + rawuser).hexdigest()
                            if int(digest[:8], 16) % 8:
                                usermap[rawuser] = -1
                            else:
                                usermap[rawuser] = len(selected)
                                selected.append({'hash': digest, 'rows': 0, 'arms': [], 'installations': [], 'first_time': None, 'last_time': None, 'language_set': []})
                        uid = usermap[rawuser]
                        if uid < 0:
                            continue
                        if cols[17] not in installcache:
                            installcache[cols[17]] = timestamp(cols[17])
                        install = installcache[cols[17]]
                        when = timestamp(cols[16])
                        category = intern(cats, cols[12])
                        mode = intern(modes, (cols[10], cols[11]))
                        item = intern(itemmap, cols[13])
                        info = selected[uid]
                        info['rows'] += 1
                        if arm not in info['arms']: info['arms'].append(arm)
                        if install not in info['installations']: info['installations'].append(install)
                        langs = (cols[8].decode(), cols[9].decode())
                        if langs not in info['language_set']: info['language_set'].append(langs)
                        info['first_time'] = when if info['first_time'] is None else min(when, info['first_time'])
                        info['last_time'] = when if info['last_time'] is None else max(when, info['last_time'])
                        rows.append((uid,item,when,install,arm,category,mode,integer(cols[19]),integer(cols[20]),totalrows))
                        if arm not in handles:
                            handles[arm] = gzip.open(OUT / ('opaque_answers/arm_%02d.tsv.gz' % arm), 'xb', compresslevel=1)
                        # Correct/difficulty are copied as uninterpreted byte fields, not parsed.
                        handles[arm].write(str(totalrows).encode() + b'\t' + cols[18] + b'\t' + cols[14] + b'\n')
                        if len(rows) >= 100000: flush()
                    members[-1]['records'] = nfile
                    if len(members) % 20 == 0:
                        print(json.dumps({'member': member.name, 'records': nfile, 'all_records': totalrows, 'decoded_bytes': counted.n, 'seconds': round(time.monotonic()-t0,1)}), flush=True)
        flush()
        result = {'complete': True, 'answer_values_analysed': 0, 'requests_attempted': 3,
                  'rows': totalrows, 'all_users': len(usermap), 'sampled_users': len(selected),
                  'sampled_rows': sum(x['rows'] for x in selected), 'members': members,
                  'arms': {str(v): k.decode() for k,v in arms.items()},
                  'arm_row_counts_all': dict(armcounts),
                  'categories': {str(v): k.decode() for k,v in cats.items()},
                  'modes': {str(v): [x.decode() for x in k] for k,v in modes.items()},
                  'items_hashed': {str(v): hashlib.sha256(k).hexdigest() for k,v in itemmap.items()},
                  'parts': parts, 'decoded_bytes': counted.n, 'previous_failed_decoded_bytes': previous,
                  'cumulative_archive_decoded_bytes': previous + counted.n,
                  'fixed_end_date': '2020-05-31' if args.corrected_window else '2020-07-31',
                  'seconds': time.monotonic()-t0, 'python': sys.version,
                  'numpy': np.__version__, 'max_rss_bytes_macos': resource.getrusage(resource.RUSAGE_SELF).ru_maxrss}
        (OUT / 'selected_users.json').write_text(json.dumps(selected, separators=(',',':')) + '\n')
        (OUT / 'METADATA.json').write_text(json.dumps(result, indent=2) + '\n')
        print(json.dumps({k:result[k] for k in ('complete','rows','all_users','sampled_users','sampled_rows','arms','decoded_bytes','seconds','max_rss_bytes_macos')}), flush=True)
    except Exception as exc:
        failure = {'complete': False, 'error': str(exc), 'rows': totalrows, 'members': members,
                   'decoded_bytes': counted.n if counted else 0, 'answer_values_analysed': 0,
                   'seconds': time.monotonic()-t0}
        (OUT / 'METADATA_FAILED.json').write_text(json.dumps(failure, indent=2)+'\n')
        print(json.dumps(failure), flush=True)
        raise
    finally:
        for handle in handles.values(): handle.close()

if __name__ == '__main__':
    main()
