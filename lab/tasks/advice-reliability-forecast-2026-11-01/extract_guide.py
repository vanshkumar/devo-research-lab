import pathlib, sys, json, resource
from pypdf import PdfReader
root=pathlib.Path(__file__).resolve().parent
name=sys.argv[1]
assert pathlib.Path(name).name==name
r=PdfReader(root/name)
text='\n'.join(p.extract_text() or '' for p in r.pages)
(root/(name+'.txt')).write_text(text)
print(text)
print(json.dumps({'pages':len(r.pages),'text_bytes':len(text.encode()),'peak_rss_bytes':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss}))
