"""Bounded single-request public-source retrieval for this assignment only."""
import argparse
import datetime as dt
import hashlib
import json
import pathlib
import resource
import urllib.error
import urllib.request

ROOT = pathlib.Path(__file__).resolve().parent

class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('name')
    ap.add_argument('url')
    ap.add_argument('--limit', type=int, default=1000000)
    a = ap.parse_args()
    assert a.name == pathlib.Path(a.name).name
    if a.url == '@archive-hop.bin.request.json':
        a.url = json.loads((ROOT / 'sources' / 'archive-hop.bin.request.json').read_text())['headers']['Location']
    assert a.url.startswith('https://')
    out = ROOT / 'sources'
    out.mkdir(exist_ok=True)
    assert not (out / (a.name + '.request.json')).exists()
    receipt = {'url': a.url, 'name': a.name, 'limit_bytes': a.limit,
               'started_utc': dt.datetime.now(dt.timezone.utc).isoformat(),
               'redirects_followed': 0}
    body = b''
    try:
        req = urllib.request.Request(a.url, headers={'User-Agent': 'public-research-source-check/1.0'})
        try:
            response = urllib.request.build_opener(NoRedirect()).open(req, timeout=25)
        except urllib.error.HTTPError as e:
            response = e
        with response:
            receipt['status'] = response.code
            receipt['headers'] = dict(response.headers)
            body = response.read(a.limit + 1)
        receipt['exceeded_limit'] = len(body) > a.limit
        (out / a.name).write_bytes(body)
        receipt['bytes'] = len(body)
        receipt['sha256'] = hashlib.sha256(body).hexdigest()
    except Exception as e:
        receipt['error'] = repr(e)
        receipt['bytes'] = len(body)
    receipt['peak_rss_bytes'] = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    receipt['ended_utc'] = dt.datetime.now(dt.timezone.utc).isoformat()
    (out / (a.name + '.request.json')).write_text(json.dumps(receipt, indent=2) + '\n')
    print(json.dumps(receipt, indent=2))

if __name__ == '__main__':
    main()
