"""One bounded request: receive the authorised public archive without decoding it."""
import datetime as dt
import argparse
import hashlib
import json
from pathlib import Path
import time
import urllib.request

ROOT = Path('/Users/vanshkumar/Documents/repos/devo-research-lab')
OUT = ROOT / 'sources/memory_policy_transfer_2026-10-30'
OUT.mkdir(parents=True, exist_ok=True)
URL = 'https://owncloud.mpi-sws.org/index.php/s/Pgn3Q9N592Z8MgZ/download'
CAP = 650_000_000
archive = OUT / 'stats-20191220-20200731.tar.gz'
ledger = OUT / 'ACQUISITION.json'
parser = argparse.ArgumentParser()
parser.add_argument('--retry-network', action='store_true')
args = parser.parse_args()
previous = None
if ledger.exists():
    previous = json.loads(ledger.read_text())
if archive.exists() or (previous and not args.retry_network):
    raise SystemExit('Refusing an unaccounted repeated acquisition')
if previous and (previous.get('complete') or previous.get('bytes_received', 0)):
    raise SystemExit('Retry is allowed only after a zero-byte failed request')
if previous:
    (OUT / 'ACQUISITION_request_01_failed.json').write_text(json.dumps(previous, indent=2) + '\n')
record = {'request_number': 2 if previous else 1, 'prior_zero_byte_failure': bool(previous), 'url': URL, 'kind': 'blind_archive_receipt',
          'started_utc': dt.datetime.now(dt.timezone.utc).isoformat(),
          'compressed_cap': CAP, 'bytes_received': 0, 'response_values_analysed': 0}
ledger.write_text(json.dumps(record, indent=2) + '\n')
t0 = time.monotonic()
h = hashlib.sha256()
try:
    with urllib.request.urlopen(urllib.request.Request(URL), timeout=45) as response:
        record['status'] = response.status
        record['final_url'] = response.geturl()
        record['headers'] = dict(response.headers)
        length = int(response.headers.get('Content-Length', '0'))
        if length > CAP:
            raise RuntimeError('Declared archive exceeds compressed receipt cap')
        with archive.open('xb') as dest:
            while True:
                block = response.read(min(1024 * 1024, CAP - record['bytes_received'] + 1))
                if not block:
                    break
                record['bytes_received'] += len(block)
                if record['bytes_received'] > CAP:
                    raise RuntimeError('Compressed receipt cap exceeded')
                dest.write(block)
                h.update(block)
                if record['bytes_received'] % (32 * 1024 * 1024) == 0:
                    ledger.write_text(json.dumps(record, indent=2) + '\n')
                    print(json.dumps({'downloaded_bytes': record['bytes_received'],
                                      'seconds': round(time.monotonic() - t0, 1)}), flush=True)
    if length and length != record['bytes_received']:
        raise RuntimeError('Content-Length mismatch')
    record['sha256'] = h.hexdigest()
    record['complete'] = True
except Exception as exc:
    record['error'] = str(exc)
    record['complete'] = False
finally:
    record['finished_utc'] = dt.datetime.now(dt.timezone.utc).isoformat()
    record['seconds'] = time.monotonic() - t0
    ledger.write_text(json.dumps(record, indent=2) + '\n')
    print(json.dumps({k: v for k, v in record.items() if k not in ('headers', 'url', 'final_url')}), flush=True)

