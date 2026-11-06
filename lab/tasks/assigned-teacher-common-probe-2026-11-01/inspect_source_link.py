"""Inspect only the public CV's source-code link for the selected paper."""
from pathlib import Path
import hashlib
import importlib.util
import re
import resource
import sys

root = Path(__file__).resolve().parent
p = root / 'gureckis-cv.pdf'
b = p.read_bytes()
out = {'file': p.name, 'bytes': len(b), 'sha256': hashlib.sha256(b).hexdigest(),
       'python': sys.version, 'packages': {k: bool(importlib.util.find_spec(k)) for k in ('pypdf','PyPDF2','fitz')}}
print(out)
reader_name = next((k for k in ('pypdf','PyPDF2') if out['packages'][k]), None)
if reader_name:
    mod = __import__(reader_name)
    reader = mod.PdfReader(str(p))
    for i, page in enumerate(reader.pages):
        t = page.extract_text() or ''
        if 'Is it better to select' in t:
            print('MATCH_PAGE', i, t)
            print('LINKS', [str(a.get_object().get('/A', {})) for a in page.get('/Annots', [])])
else:
    print('URI_ANNOTATIONS', re.findall(rb'/URI\s*\(([^)]*)\)', b))
print('ru_maxrss_native', resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
html_path = root / 'papers.html'
if html_path.exists():
    hb = html_path.read_bytes()
    print('HTML_PIN',len(hb),hashlib.sha256(hb).hexdigest())
    ht = hb.decode('utf-8')
    for match in re.finditer('markant2014better',ht):
        print('PAPER_ENTRY',ht[max(0,match.start()-1000):match.start()+6000])
