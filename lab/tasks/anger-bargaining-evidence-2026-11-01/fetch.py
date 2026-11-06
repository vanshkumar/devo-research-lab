"""Bounded public-object retrieval for this finite assignment only."""
import sys, json, hashlib, urllib.request, urllib.error, datetime, resource
from pathlib import Path
P = Path(__file__).resolve().parent
url, name = sys.argv[1:3]
cap = int(sys.argv[3]) if len(sys.argv)>3 else 2000000
ledger_path = P/'FETCH_LEDGER.json'
ledger = json.loads(ledger_path.read_text()) if ledger_path.exists() else []
external=json.loads((P/'EXTERNAL_OPERATIONS.json').read_text())
# Provider traffic/redirect hops remain unknown; these are deliberate top-level operations.
if len(ledger)+len(external) >= 30: raise RuntimeError('operation cap')
if sum(x['charged_ingress_allowance_bytes'] for x in external) + sum(x['charged_ingress_bytes'] for x in ledger) + cap > 25000000:
    raise RuntimeError('ingress allowance cap')
rec = dict(url=url, name=name, requested_cap=cap, at=datetime.datetime.now(datetime.timezone.utc).isoformat())
data=b''
try:
    req=urllib.request.Request(url,headers={'User-Agent':'bounded-public-research/1.0'})
    with urllib.request.urlopen(req,timeout=35) as res:
        rec.update(status=res.status, final_url=res.url, headers=dict(res.headers))
        while len(data)<cap+1:
            chunk=res.read(min(65536,cap+1-len(data)))
            if not chunk: break
            data+=chunk
    rec['cap_exceeded']=len(data)>cap
    if rec['cap_exceeded']: raise RuntimeError('object larger than cap; prefix saved')
except Exception as e:
    rec['error']=repr(e)
rec.update(known_local_bytes=len(data),sha256=hashlib.sha256(data).hexdigest(),
           charged_ingress_bytes=len(data) if data else 1000000,
           additional_read_decode_hash_allowance_bytes=2*len(data),
           peak_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
dest=P/'sources'/name
dest.parent.mkdir(exist_ok=True)
dest.write_bytes(data)
ledger.append(rec)
ledger_path.write_text(json.dumps(ledger,indent=2)+'\n')
print(json.dumps(rec,indent=2))
if rec.get('error'): sys.exit(1)
