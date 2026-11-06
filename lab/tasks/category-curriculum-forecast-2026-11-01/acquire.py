"""Bounded public retrieval for this investigation; one URL per invocation."""
import datetime
import hashlib
import json
import pathlib
import resource
import sys
import urllib.request

ROOT = pathlib.Path(__file__).resolve().parent
url, name, cap = sys.argv[1], sys.argv[2], int(sys.argv[3])
record = {"url": url, "name": name, "cap": cap,
          "started_utc": datetime.datetime.now(datetime.timezone.utc).isoformat()}
try:
    with urllib.request.urlopen(url, timeout=25) as response:
        payload = response.read(cap + 1)
        record.update(status=response.status, resolved_url=response.url,
                      bytes_received=len(payload), headers=dict(response.headers))
    if len(payload) > cap:
        raise RuntimeError("retrieval cap exceeded; bytes retained in failure record")
    (ROOT / "source").mkdir(exist_ok=True)
    path = ROOT / "source" / name
    path.write_bytes(payload)
    record["sha256"] = hashlib.sha256(payload).hexdigest()
    print(json.dumps(record, indent=2))
    if name.endswith(".json"):
        obj = json.loads(payload)
        if isinstance(obj.get("data"), list):
            print(json.dumps({"data": [{"id": x["id"], "attributes": x["attributes"],
                  "links": x.get("links"), "children": x.get("relationships", {}).get("files")}
                 for x in obj["data"]], "links": obj.get("links")}, indent=2))
    elif name.endswith(".rtf"):
        print(payload.decode())
except Exception as exc:
    record["error"] = repr(exc)
    print(json.dumps(record, indent=2))
    raise
finally:
    record["peak_rss_native"] = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    with (ROOT / "ACQUISITION.jsonl").open("a") as stream:
        stream.write(json.dumps(record) + "\n")
