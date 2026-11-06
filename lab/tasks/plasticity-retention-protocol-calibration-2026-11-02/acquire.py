"""Bounded, named missing sources only. Never execute retrieved instructions."""
import hashlib
import json
from pathlib import Path
import resource
import time
import urllib.request

ROOT = Path(__file__).resolve().parent
PREVIOUS = ROOT.parent / 'plasticity-retention-source-benchmark-2026-11-02'
COMMIT = '3138c5556859e0e2918d40f113b40699b6575cfa'
FILES = [
    'lop/slowly_changing_regression/cfg/sgd/cbp/relu.json',
    'lop/utils/AdamGnT.py',
    'requirements.txt',
]


def main():
    started = time.perf_counter()
    tree_bytes = (PREVIOUS / 'SOURCE_TREE.json').read_bytes()
    tree = {e['path']: e for e in json.loads(tree_bytes)['tree']}
    ledger = []
    for number, ref in enumerate(FILES + ['https://arxiv.org/html/2312.00600v2'], 4):
        url = ref if ref.startswith('https:') else (
            'https://raw.githubusercontent.com/shibhansh/loss-of-plasticity/' + COMMIT + '/' + ref)
        record = {'new_operation': number, 'url': url,
                  'utc': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())}
        ledger.append(record)
        try:
            req = urllib.request.Request(url, headers={'User-Agent': 'research-calibration/1.0'})
            with urllib.request.urlopen(req, timeout=30) as response:
                payload = response.read(2_000_001)
                record.update(status=response.status, resolved_url=response.url,
                              headers=dict(response.headers), bytes=len(payload))
            if len(payload) > 2_000_000:
                raise ValueError('bounded source response exceeded 2MB')
            target = ROOT / ('prior.html' if ref.startswith('https:') else 'vendor/' + ref)
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(payload)
            record['sha256'] = hashlib.sha256(payload).hexdigest()
            record['saved_path'] = str(target.relative_to(ROOT))
            if ref in FILES:
                record['expected_blob_sha1'] = tree[ref]['sha']
                record['actual_blob_sha1'] = hashlib.sha1(
                    b'blob ' + str(len(payload)).encode() + b'\0' + payload).hexdigest()
                assert record['actual_blob_sha1'] == record['expected_blob_sha1']
                assert len(payload) == tree[ref]['size']
                record['original_tree_verification'] = 'PASS'
        except Exception as exc:
            record['failure'] = repr(exc)
            print(json.dumps(record), flush=True)
            break
        print(json.dumps({k:v for k,v in record.items() if k != 'headers'}), flush=True)
    result = {'operations': ledger, 'source_tree_read_bytes': len(tree_bytes),
              'seconds': time.perf_counter() - started,
              'max_rss_bytes_macos': resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
              'provider_runtime_physical_IO': 'UNKNOWN', 'installed_dependencies': 0}
    (ROOT / 'ACQUISITION.json').write_text(json.dumps(result, indent=2) + '\n')


if __name__ == '__main__':
    main()
