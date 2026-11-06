"""Retrieve pinned modest public inputs; verify cached originals without executing them."""
import pathlib,urllib.request,urllib.parse,hashlib,json,zipfile
H=pathlib.Path(__file__).resolve().parent;R=H.parents[1];D=R/'data/imprinting';S=R/'sources/imprinting'
D.mkdir(parents=True,exist_ok=True);S.mkdir(parents=True,exist_ok=True)
base='https://media.springernature.com/original/springer-static/esm/art%3A10.3758%2Fs13420-024-00638-z/MediaObjects/'
expected=json.loads((H/'source_hashes.json').read_text());manifest=[]
items=[]
for i,ext in [(1,'xlsx'),(2,'xlsx'),(3,'csv'),(4,'csv')]:
 name=f'13420_2024_638_MOESM{i}_ESM.{ext}';items.append((D/name,base+name,expected[name],'sha256',300000))
for name,filename,md5,directory,size in [('Experiment 4.zip','Experiment4.zip','2a3e4d8d20836d9455a079fe75f47dfd',D,500000),('Experiment 1.zip','Experiment1.zip','5bc46590effa882e6e17db9744675177',D,1500000),('Code.zip','Code.zip','8a94a2af2e07b7b9fa69e35e04fe01af',S,4000000)]:
 url='https://zenodo.org/api/records/10869154/files/'+urllib.parse.quote(name)+'/content';items.append((directory/filename,url,md5,'md5',size))
for p,url,want,alg,cap in items:
 if not p.exists():
  with urllib.request.urlopen(url,timeout=45) as r:b=r.read(cap+1)
  assert len(b)<=cap;p.write_bytes(b)
 b=p.read_bytes();assert hashlib.new(alg,b).hexdigest()==want,(p,'hash mismatch')
 manifest.append(dict(file=str(p.relative_to(R)),url=url,bytes=len(b),sha256=hashlib.sha256(b).hexdigest(),verified_expected_algorithm=alg,verified_expected_hash=want))
(D/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
# Extract source notebook cell text only; no original code execution.
z=zipfile.ZipFile(S/'Code.zip')
for n in z.namelist():
 if n.endswith('.ipynb'):
  obj=json.loads(z.read(n));txt='\n\n'.join(''.join(c.get('source',[])) for c in obj['cells']);(S/(pathlib.Path(n).stem+'.txt')).write_text(txt)
print(json.dumps(manifest,indent=2))
