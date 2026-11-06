#!/usr/bin/env python3
"""Small bounded public-object acquisition; one invocation, one process."""
import datetime, hashlib, json, pathlib, resource, sys, urllib.request, urllib.error
P = pathlib.Path(__file__).resolve().parent
L = P / 'ACQUISITION.json'
ledger = json.loads(L.read_text()) if L.exists() else {
    'search_operations': 1, 'search_ingress_reserve_bytes': 1000000,
    'search_provider_transfer_and_peak': 'unknown', 'requests': []}
name, url, cap = sys.argv[1], sys.argv[2], int(sys.argv[3])
assert '/' not in name and cap <= 49000000
assert ledger['search_operations'] + len(ledger['requests']) < 30
used = ledger['search_ingress_reserve_bytes'] + sum(x['bytes'] for x in ledger['requests'])
assert used + cap <= 50000000
rec = {'name': name, 'url': url, 'time_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(), 'cap': cap, 'bytes': 0}
buf = bytearray()
try:
    req = urllib.request.Request(url, headers={'User-Agent': 'research-data-check/1.0'})
    try:
        response = urllib.request.urlopen(req, timeout=25)
    except urllib.error.HTTPError as e:
        response = e
    rec.update(status=response.status, final_url=response.geturl(), headers=dict(response.headers))
    with response:
        while len(buf) < cap:
            chunk = response.read(min(65536, cap-len(buf)))
            if not chunk: break
            buf.extend(chunk)
    rec['bytes'] = len(buf)
    rec['at_cap'] = len(buf) == cap
    (P/name).write_bytes(buf)
    rec['sha256'] = hashlib.sha256(buf).hexdigest()
    rec['md5'] = hashlib.md5(buf).hexdigest()
except Exception as e:
    rec.update(error=repr(e), bytes=len(buf), failed_transfer_unknown=True)
    if buf: (P/name).write_bytes(buf)
rec['finished_utc'] = datetime.datetime.now(datetime.timezone.utc).isoformat()
rec['peak_rss_bytes'] = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
ledger['requests'].append(rec)
L.write_text(json.dumps(ledger, indent=2)+'\n')
print(json.dumps({k:v for k,v in rec.items() if k not in ['headers','final_url']}, indent=2))
