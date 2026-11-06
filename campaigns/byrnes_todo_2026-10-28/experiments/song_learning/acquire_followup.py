import pathlib,urllib.request,hashlib,json
H=pathlib.Path(__file__).resolve().parent;C=H.parents[1];D=C/'data/song_learning';mf=D/'followup_manifest.json';old={x['file']:x for x in json.loads(mf.read_text())} if mf.exists() else {}
base='https://media.springernature.com/original/springer-static/esm/art%3A10.1038%2Fs41586-025-08729-1/MediaObjects/'
# Fig2 whole-file acquisition stopped at cap; use range_source.py for selected members.
items=[('fig1.xlsx','41586_2025_8729_MOESM3_ESM.xlsx')];out=[]
for name,tail in items:
 p=D/name;url=base+tail
 if not p.exists():
  with urllib.request.urlopen(url,timeout=45) as r:b=r.read(7_000_001)
  assert len(b)<=7_000_000;p.write_bytes(b)
 b=p.read_bytes();sha=hashlib.sha256(b).hexdigest();assert b.startswith(b'PK')
 if name in old:assert sha==old[name]['sha256']
 out.append(dict(file=name,url=url,bytes=len(b),sha256=sha));print(name,len(b),flush=True)
assert sum(x['bytes'] for x in out)+35453771<=50_000_000
mf.write_text(json.dumps(out,indent=2)+'\n')
