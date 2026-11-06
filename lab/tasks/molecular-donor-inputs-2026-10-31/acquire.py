"""Task-specific bounded public-source acquisition; never downloads a whole atlas.

Usage: python acquire.py LABEL URL MAX_RESPONSE_BYTES [RANGE]
Redirects are returned for explicit inspection, not followed invisibly.
"""
import datetime
import hashlib
import json
from pathlib import Path
import resource
import sys
import urllib.error
import urllib.request

ROOT = Path(__file__).resolve().parent
DEADLINE = datetime.datetime.fromisoformat('2026-10-31T21:51:29.229+00:00')


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def main():
    label, url, cap = sys.argv[1:4]
    cap = int(cap)
    assert label.replace('_', '').replace('-', '').isalnum()
    assert url.startswith('https://') and 0 < cap <= 10_000_000
    assert datetime.datetime.now(datetime.timezone.utc) < DEADLINE
    ledger_path = ROOT / 'REQUESTS.json'
    ledger = json.loads(ledger_path.read_text()) if ledger_path.exists() else []
    # Five already-used provider operations reserve 10 MB conservative ingress.
    assert len(ledger) + 5 < 40
    assert sum(x['bytes_received'] for x in ledger) + cap + 10_000_000 <= 1_000_000_000
    dest = ROOT / 'sources' / (label + '.bin')
    assert not dest.exists(), 'Never overwrite an acquisition or repeat it silently'
    dest.parent.mkdir(exist_ok=True)
    headers = {'User-Agent': 'Research-data-source-inspection/1.0', 'Accept-Encoding': 'identity'}
    if len(sys.argv) > 4:
        headers['Range'] = sys.argv[4]
    rec = {'label': label, 'url': url, 'started_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
           'request_headers': headers, 'response_cap': cap, 'bytes_received': 0}
    body = bytearray()
    try:
        request = urllib.request.Request(url, headers=headers)
        try:
            response = urllib.request.build_opener(NoRedirect).open(request, timeout=35)
        except urllib.error.HTTPError as err:
            response = err
        rec.update(status=response.code, response_headers=dict(response.headers), final_url=response.url)
        while len(body) < cap:
            block = response.read(min(65536, cap - len(body)))
            if not block:
                break
            body.extend(block)
        rec['at_cap'] = len(body) == cap
        response.close()
    except Exception as err:
        rec['error'] = type(err).__name__ + ': ' + str(err)
    finally:
        rec['bytes_received'] = len(body)
        rec['sha256'] = hashlib.sha256(body).hexdigest()
        rec['saved_file'] = str(dest.relative_to(ROOT))
        rec['peak_rss_bytes_macos'] = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        rec['finished_utc'] = datetime.datetime.now(datetime.timezone.utc).isoformat()
        dest.write_bytes(body)
        ledger.append(rec)
        ledger_path.write_text(json.dumps(ledger, indent=2) + '\n')
        print(json.dumps(rec, indent=2))
        if 'text' in rec.get('response_headers', {}).get('Content-Type', '').lower() or body[:1] in (b'{', b'['):
            print(bytes(body[:1800]).decode('utf-8', errors='replace'))


if __name__ == '__main__':
    main()
