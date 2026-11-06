"""Bounded source retrieval; run one invocation at a time. No archive extraction here."""
import argparse, datetime, hashlib, json, pathlib, resource, urllib.request

ROOT = pathlib.Path(__file__).resolve().parent
RAW = ROOT / 'sources'
RAW.mkdir(exist_ok=True)
LEDGER = ROOT / 'ACQUISITION.json'
DEADLINE = datetime.datetime.fromisoformat('2026-11-01T01:38:45.964+00:00')

def main():
    p = argparse.ArgumentParser()
    p.add_argument('name'); p.add_argument('url'); p.add_argument('--cap', type=int, required=True)
    p.add_argument('--prefix', action='store_true')
    a = p.parse_args()
    now = datetime.datetime.now(datetime.timezone.utc)
    if now >= DEADLINE: raise RuntimeError('acquisition cutoff passed')
    ledger = json.loads(LEDGER.read_text()) if LEDGER.exists() else {
        'web_operations': 1, 'web_charged_bytes': 500000, 'web_transport_bytes': 'unavailable',
        'direct_operations': [], 'direct_ingress_bytes': 0,
        'scientific_byte_passes': [], 'scientific_read_decoded_hash_bytes': 0}
    if ledger['web_operations'] + len(ledger['direct_operations']) >= 12: raise RuntimeError('operation cap')
    if ledger['web_charged_bytes'] + ledger['direct_ingress_bytes'] + a.cap > 35000000:
        raise RuntimeError('ingress cap reservation')
    rec = {'name':a.name, 'url':a.url, 'start':now.isoformat(), 'cap':a.cap, 'prefix':a.prefix,
           'bytes':0, 'status':'failed'}
    data = bytearray()
    try:
        req = urllib.request.Request(a.url, headers={'User-Agent':'bounded-research/1.0', 'Accept-Encoding':'identity'})
        with urllib.request.urlopen(req, timeout=30) as r:
            rec['http_status'] = r.status; rec['headers'] = dict(r.headers)
            content = r.headers.get('Content-Length')
            if content and int(content) > a.cap and not a.prefix:
                raise RuntimeError('declared object exceeds requested cap; body unopened')
            while len(data) < a.cap:
                block = r.read(min(65536, a.cap-len(data)))
                if not block: break
                data.extend(block)
            rec['status'] = 'prefix' if a.prefix and len(data)==a.cap else 'complete'
        (RAW/a.name).write_bytes(data)
        rec['sha256'] = hashlib.sha256(data).hexdigest()
        rec['path'] = str((RAW/a.name).relative_to(ROOT))
    except Exception as e:
        rec['error'] = repr(e)
        if data: (RAW/(a.name+'.partial')).write_bytes(data)
    finally:
        rec['bytes'] = len(data)
        ledger['direct_ingress_bytes'] += len(data)
        ledger['direct_operations'].append(rec)
        # One body acquisition, one saved-body hashing pass; writes are not read passes.
        charged = 2*len(data)
        ledger['scientific_read_decoded_hash_bytes'] += charged
        ledger['scientific_byte_passes'].append({'operation':a.name,'kind':'acquisition+hash','bytes':charged})
        rec['peak_rss_bytes'] = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        LEDGER.write_text(json.dumps(ledger,indent=2)+'\n')
        print(json.dumps(rec,indent=2))
    if rec['status']=='failed': raise SystemExit(1)

if __name__ == '__main__': main()
