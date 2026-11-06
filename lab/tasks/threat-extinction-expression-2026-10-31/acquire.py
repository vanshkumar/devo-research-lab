"""Bounded, explicit single-object acquisition for this study (no automatic retries)."""
import argparse
import hashlib
import json
import resource
import time
from pathlib import Path
from urllib.request import Request, build_opener, HTTPRedirectHandler
from urllib.error import HTTPError

ROOT = Path(__file__).resolve().parent


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def main():
    p = argparse.ArgumentParser()
    p.add_argument('url')
    p.add_argument('name')
    p.add_argument('--limit', type=int, default=2_000_000)
    a = p.parse_args()
    dest = ROOT / 'sources' / a.name
    assert dest.parent == ROOT / 'sources'
    assert not dest.exists()
    dest.parent.mkdir(exist_ok=True)
    record = dict(url=a.url, name=a.name, limit=a.limit, start_utc=time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()), redirects_followed=0)
    body = b''
    try:
        try:
            response = build_opener(NoRedirect).open(Request(a.url, headers={'User-Agent': 'Research data verification; Python urllib'}), timeout=35)
        except HTTPError as e:
            response = e
        record.update(status=response.code, headers=dict(response.headers))
        body = response.read(a.limit + 1)
        record['exceeded_limit'] = len(body) > a.limit
        dest.write_bytes(body)
        record.update(bytes=len(body), sha256=hashlib.sha256(body).hexdigest())
    except Exception as e:
        record.update(error=repr(e), bytes=len(body), failed_pass_ingress_charge=a.limit)
    record['peak_rss_bytes'] = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    record['end_utc'] = time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())
    (ROOT / 'sources' / (a.name + '.request.json')).write_text(json.dumps(record, indent=2))
    print(json.dumps(record, indent=2))


if __name__ == '__main__':
    main()
