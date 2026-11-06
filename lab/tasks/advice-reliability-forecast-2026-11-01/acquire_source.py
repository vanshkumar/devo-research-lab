"""One bounded public object per invocation; no downloaded code execution."""
import sys, urllib.request, urllib.error, json, hashlib, datetime, pathlib, resource

root = pathlib.Path(__file__).resolve().parent
name, url, bound = sys.argv[1], sys.argv[2], int(sys.argv[3])
assert pathlib.Path(name).name == name
dest = root / name
assert not dest.exists(), 'Preserve earlier acquisitions'
record = {'url':url, 'requested_bound':bound, 'started_utc':datetime.datetime.now(datetime.timezone.utc).isoformat()}
try:
    req = urllib.request.Request(url, headers={'User-Agent':'bounded-public-research/1.0'})
    with urllib.request.urlopen(req, timeout=30) as r:
        record.update(status=r.status, final_url=r.url, headers=dict(r.headers))
        body = r.read(bound+1)
    dest.write_bytes(body)
    record.update(bytes=len(body), sha256=hashlib.sha256(body).hexdigest(), bound_exceeded=len(body)>bound)
except urllib.error.HTTPError as e:
    body=e.read(bound+1)
    dest.write_bytes(body)
    record.update(error=str(e), status=e.code, bytes=len(body), sha256=hashlib.sha256(body).hexdigest())
except Exception as e:
    record.update(error=repr(e), bytes_unknown=True)
record.update(ended_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(), peak_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
(root / (name+'.request.json')).write_text(json.dumps(record, indent=2))
print(json.dumps(record,indent=2))
