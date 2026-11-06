"""Bounded public-source acquisition for this assignment only (standard library)."""
import datetime
import hashlib
import json
import pathlib
import resource
import sys
import urllib.error
import urllib.request

ROOT = pathlib.Path(__file__).resolve().parent
url, label, cap = sys.argv[1], sys.argv[2], int(sys.argv[3])
assert label.replace('_', '').replace('-', '').isalnum()
out = ROOT / 'sources'
out.mkdir(exist_ok=True)
receipt = {'url': url, 'label': label, 'cap': cap,
           'started_utc': datetime.datetime.now(datetime.timezone.utc).isoformat()}
payload = b''
try:
    req = urllib.request.Request(url, headers={'User-Agent': 'bounded-public-research/1.0'})
    try:
        response = urllib.request.urlopen(req, timeout=35)
    except urllib.error.HTTPError as e:
        response = e
    with response:
        payload = response.read(cap + 1)
        receipt.update(status=response.status, final_url=response.url,
                       headers=dict(response.headers), application_bytes=len(payload))
        if len(payload) > cap:
            receipt['over_cap'] = True
            raise RuntimeError('Source payload exceeded declared per-operation cap')
        (out / (label + '.payload')).write_bytes(payload)
        receipt.update(sha256=hashlib.sha256(payload).hexdigest(),
                       saved=str(out / (label + '.payload')))
except Exception as e:
    receipt['error'] = repr(e)
    receipt['application_bytes'] = len(payload)
finally:
    receipt.update(finished_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
                   peak_rss=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
                   physical_io='unknown; receipt records application body only')
    (out / (label + '.receipt.json')).write_text(json.dumps(receipt, indent=2) + '\n')
    print(json.dumps(receipt))
if receipt.get('error') or receipt.get('status') != 200:
    sys.exit(1)
