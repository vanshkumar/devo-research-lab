"""Download only pinned public inputs, bounded to 120 MB, with hashes."""
import argparse, hashlib, json, pathlib, urllib.request
ROOT=pathlib.Path(__file__).resolve().parents[2]
p=argparse.ArgumentParser(); p.add_argument('--part',choices=['discovery','validation','all'],default='discovery'); a=p.parse_args()
m=json.loads((pathlib.Path(__file__).parent/'selection.json').read_text())
parts=['discovery','validation'] if a.part=='all' else [a.part]
out=ROOT/'data/public'; out.mkdir(parents=True,exist_ok=True)
logpath=out/'manifest.json'; log=json.loads(logpath.read_text()) if logpath.exists() else []
for part in parts:
 for item in m[part]:
  url=f"https://raw.githubusercontent.com/{m['repo']}/{m['commit']}/{item['path']}"
  dest=out/pathlib.Path(item['path']).name
  if not dest.exists():
   with urllib.request.urlopen(url,timeout=60) as r:
    data=r.read(12_000_001)
   assert len(data)<=12_000_000 and len(data)==item['size'],(url,len(data))
   assert hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest()==item['sha']
   dest.write_bytes(data)
  b=dest.read_bytes()
  assert len(b)==item['size'],('cached size mismatch',dest)
  assert hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest()==item['sha'],('cached blob mismatch',dest)
  record=dict(file=dest.name,url=url,bytes=len(b),sha256=hashlib.sha256(b).hexdigest(),git_blob=item['sha'],part=part)
  log=[x for x in log if x['file']!=dest.name]+[record]
  logpath.write_text(json.dumps(log,indent=2)+'\n'); print(record['file'],record['bytes'],part,flush=True)
