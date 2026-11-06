import json, pathlib, xml.etree.ElementTree as E
p=pathlib.Path(__file__).resolve().parent
t=json.loads((p/'code_tree.source').read_text())
print('TREE',t['sha'])
for x in t['tree']:
    print(x['path'],x.get('size',''),x['sha'])
a=E.parse(p/'article.source')
for s in a.findall('.//sec'):
    title=s.find('title')
    if title is not None and any(k in ''.join(title.itertext()).lower() for k in ['participant','task','behavior','generative','model','data avail']):
        print('\nSECTION', ''.join(s.itertext())[:22000])
