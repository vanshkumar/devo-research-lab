"""Finite one-request public acquisition; task-local immutable response and ledger."""
import urllib.request, urllib.error, json, hashlib, time, resource, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parent
if len(sys.argv)==2:
    config=json.loads((ROOT/sys.argv[1]).read_text())
    url, name, cap=config['url'], config['name'],config['cap']
else:
    url, name, cap = sys.argv[1], sys.argv[2], int(sys.argv[3])
req = urllib.request.Request(url, headers={'User-Agent':'bounded-public-research/1.0'})
started = time.time()
status, headers, error = None, {}, None
try:
    with urllib.request.urlopen(req, timeout=35) as r:
        status, headers = r.status, dict(r.headers)
        data = r.read(cap+1)
        if len(data)>cap:
            error='CAP_EXCEEDED; extra byte included in charge'
except urllib.error.HTTPError as e:
    status, headers, error = e.code, dict(e.headers), repr(e)
    data=e.read(cap+1)
except Exception as e:
    data=b''; error=repr(e)
path=ROOT/name
path.parent.mkdir(parents=True,exist_ok=True)
path.write_bytes(data)
record={'url':url,'path':name,'utc_epoch':started,'status':status,'headers':headers,
        'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest(),'error':error,
        'elapsed_s':time.time()-started,'rss_bytes':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss}
with (ROOT/'ACQUISITIONS.jsonl').open('a') as f: f.write(json.dumps(record)+'\n')
print(json.dumps(record))
