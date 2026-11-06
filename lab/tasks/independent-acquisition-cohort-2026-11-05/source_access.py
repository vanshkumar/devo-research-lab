"""Bounded anonymous public metadata acquisition; never fetches trial payloads.

All new response bytes, including failures, are logged. This is an assignment
script, not a shared access/metering service. No credentials are read or used.
"""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import resource
import time
import urllib.error
import urllib.request

HERE = Path(__file__).resolve().parent
LOG = HERE / 'PUBLIC_REQUESTS.jsonl'
_INGRESS = None
REQUEST_LOG_BYTES_READ = 0


def utc():
    return datetime.now(timezone.utc).isoformat()


def request(url, name, limit, method='GET', byte_range=None, purpose='catalogue metadata',
            metadata_range_only=False, quiet=False):
    global _INGRESS, REQUEST_LOG_BYTES_READ
    assert url.startswith(('https://ibl-brain-wide-map-public.s3.amazonaws.com/',
                           'https://docs.internationalbrainlab.org/',
                           'https://raw.githubusercontent.com/int-brain-lab/',
                           'https://raw.githubusercontent.com/cortex-lab/psychofit/'))
    assert '/' not in name and '..' not in name
    if _INGRESS is None:
        prior_bytes = LOG.read_bytes() if LOG.exists() else b''
        REQUEST_LOG_BYTES_READ += len(prior_bytes)
        _INGRESS = sum(json.loads(x).get('received_bytes', 0) for x in prior_bytes.splitlines())
    assert _INGRESS + limit <= 80_000_000
    headers = {'User-Agent': 'independent-source-qualification/1.0'}
    if byte_range:
        headers['Range'] = byte_range
    rec = dict(utc=utc(), url=url, method=method, requested_range=byte_range,
               local=name, purpose=purpose, maximum_response_bytes=limit,
               payload_values_decoded=False, received_bytes=0)
    cpu, wall = time.process_time(), time.monotonic()
    data = bytearray()
    try:
        req = urllib.request.Request(url, headers=headers, method=method)
        try:
            response = urllib.request.urlopen(req, timeout=35)
        except urllib.error.HTTPError as exc:
            response = exc
        with response:
            rec.update(status=response.status, response_headers=dict(response.headers),
                       resolved_url=response.url)
            if metadata_range_only:
                assert response.status == 206, 'Range not honored; response body not read'
                assert response.headers.get('Content-Range', '').startswith('bytes '), 'No certified range; response body not read'
            while True:
                block = response.read(min(65536, limit + 1 - len(data)))
                if not block:
                    break
                data.extend(block)
                if len(data) > limit:
                    raise RuntimeError('Bounded response limit exceeded; retained failed bytes')
        (HERE/name).write_bytes(data)
        rec['sha256'] = hashlib.sha256(data).hexdigest()
        if rec['status'] >= 400:
            rec['error'] = 'HTTP error response retained'
    except Exception as exc:
        rec['error'] = repr(exc)
        if data:
            (HERE/(name+'.failed')).write_bytes(data)
    finally:
        _INGRESS += len(data)
        rec.update(received_bytes=len(data), cpu_seconds=time.process_time()-cpu,
                   process_wall_seconds=time.monotonic()-wall,
                   peak_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
        with LOG.open('a') as f:
            f.write(json.dumps(rec, sort_keys=True)+'\n')
    if not quiet:
        print(json.dumps(rec, indent=2))
    return rec


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('url')
    p.add_argument('name')
    p.add_argument('--limit', type=int, default=1_000_000)
    p.add_argument('--head', action='store_true')
    p.add_argument('--range')
    p.add_argument('--purpose', default='catalogue metadata')
    a = p.parse_args()
    request(a.url, a.name, a.limit, 'HEAD' if a.head else 'GET', a.range, a.purpose)
