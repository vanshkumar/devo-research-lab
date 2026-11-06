"""One explicit bounded public retrieval; never executes downloaded code."""
import sys, urllib.request, hashlib, json
from pathlib import Path

root = Path(__file__).resolve().parent
if len(sys.argv) == 2:
    url,name,cap={
      'tags':('https://api.github.com/repos/OpenNeuroDatasets/ds001612/tags','openneuro-tags.json',1000000),
      's3':('https://s3.amazonaws.com/openneuro.org?prefix=ds001612/&max-keys=1000','openneuro-s3.xml',1000000),
      'tree100':('https://api.github.com/repos/OpenNeuroDatasets/ds001612/git/trees/0d6fddd94d2ae17e74e69766c64417a1e2b353f9?recursive=1','openneuro-tree-1.0.0.json',1000000),
      'tree2017':('https://api.github.com/repos/idamomen/predictive_representations/git/trees/master?recursive=1','revaluation2017-tree.json',1000000),
      'paper2017':('https://pmc.ncbi.nlm.nih.gov/articles/PMC6941356/','paper2017.html',2000000),
      'paper2018':('https://elifesciences.org/articles/32548','paper2018.html',2000000),
    }[sys.argv[1]]
elif len(sys.argv) == 1:
    url, name, cap = 'https://api.github.com/repos/OpenNeuroDatasets/ds001612/git/trees/master?recursive=1', 'openneuro-tree.json', 1000000
else:
    url, name, cap = sys.argv[1], sys.argv[2], int(sys.argv[3])
dest = root / name
assert dest.parent == root
request = urllib.request.Request(url, headers={'User-Agent':'revaluation-source-audit'})
with urllib.request.urlopen(request, timeout=25) as response:
    body = response.read(cap + 1)
    assert len(body) <= cap, 'bounded response exceeded cap'
    metadata = {'url':url, 'final_url':response.url, 'status':response.status,
                'bytes':len(body), 'sha256':hashlib.sha256(body).hexdigest(),
                'headers':dict(response.headers)}
dest.write_bytes(body)
(root / (name+'.metadata.json')).write_text(json.dumps(metadata, indent=2))
print(json.dumps({k:metadata[k] for k in ['url','status','bytes','sha256']}))
