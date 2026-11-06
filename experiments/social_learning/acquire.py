"""Reacquire pinned public publisher files; verify Dryad SHA256 and Figshare MD5."""
import pathlib,urllib.request,hashlib,json
ROOT=pathlib.Path(__file__).resolve().parents[2];D=ROOT/'data/social_learning';D.mkdir(parents=True,exist_ok=True)
files=[('data_primacy.csv','https://ndownloader.figshare.com/files/46746183','0f723df5825865d214e3064c1e16f0e489211f25e45f3eb34e7dfb5c4ebf568b'),('primacy_bias_script.Rmd','https://ndownloader.figshare.com/files/46746186',None)]
log=[]
for name,url,want in files:
 p=D/name
 if not p.exists():
  with urllib.request.urlopen(url,timeout=45) as r: data=r.read(100000)
  assert len(data)<100000;p.write_bytes(data)
 b=p.read_bytes();sha=hashlib.sha256(b).hexdigest()
 if want:assert sha==want
 if name=='primacy_bias_script.Rmd':assert hashlib.md5(b).hexdigest()=='32e2651214573b21c7652874d1d20d59'
 log.append(dict(file=name,url=url,bytes=len(b),sha256=sha,md5=hashlib.md5(b).hexdigest()))
(D/'manifest.json').write_text(json.dumps(log,indent=2)+'\n')
print(json.dumps(log,indent=2))
