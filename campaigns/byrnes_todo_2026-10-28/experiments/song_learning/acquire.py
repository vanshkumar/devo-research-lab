"""Fetch only public fixed source files, each capped at15MB; hash caches too."""
import pathlib,urllib.request,json,hashlib
H=pathlib.Path(__file__).resolve().parent;C=H.parents[1];D=C/'data/song_learning';D.mkdir(parents=True,exist_ok=True)
base='https://media.springernature.com/original/springer-static/esm/art%3A10.1038%2Fs41586-025-08729-1/MediaObjects/'
files=[('fig3.xlsx','41586_2025_8729_MOESM5_ESM.xlsx'),('fig4.xlsx','41586_2025_8729_MOESM6_ESM.xlsx'),('ext8.xlsx','41586_2025_8729_MOESM7_ESM.xlsx')]
EXPECTED_SHA256={'fig3.xlsx': 'd55837992524da0a63a5c568a8fc8e139a3fa370ee308923f111e0236d5b9940', 'fig4.xlsx': '985a7f7dab24002c77fdeaed48e11cfdc40a12ea4f081cd7f39f950ed6156d7d', 'ext8.xlsx': '67782e8db08dc3987c45a9c85d7ac6ea6e54a6e042413346a0398c5fb54b2224'}
manifest=[]
for name,tail in files:
 url=base+tail;p=D/name
 if not p.exists():
  with urllib.request.urlopen(url,timeout=45) as r:
   b=r.read(15_000_001)
  assert len(b)<=15_000_000;p.write_bytes(b)
 b=p.read_bytes();assert b.startswith(b'PK');assert hashlib.sha256(b).hexdigest()==EXPECTED_SHA256[name],('Source version changed',name);manifest.append(dict(file=name,url=url,bytes=len(b),sha256=hashlib.sha256(b).hexdigest()))
 print(name,len(b),flush=True)
 assert sum(x['bytes'] for x in manifest)<=50_000_000
(D/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
