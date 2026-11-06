import json, pathlib, xml.etree.ElementTree as E
p=pathlib.Path(__file__).resolve().parent
if (p/'zenodo_meta.source').exists():
    z=json.loads((p/'zenodo_meta.source').read_text())
    print('ZENODO',z['id'],z.get('doi'),z['metadata'].get('license'))
    for x in z['files']:
        if x['key']=='cannonBehavData_forDryad.zip':
            print('BEHAVIOR_MIRROR',x)
for fn in ['dryad_files.source','dryad_files2.source','dryad_files3.source']:
    if (p/fn).exists():
        f=json.loads((p/fn).read_text())
        for v in f['_embedded']['stash:files']:
            if v['size'] < 50_000_000:
                print('FILE',json.dumps(v))
d=json.loads((p/'dryad_encoded.source').read_text())
for k,v in d.items():
    if k not in ('authors','abstract','usageNotes','relatedWorks'):
        print(k,json.dumps(v))
a=E.parse(p/'article.source')
for s in a.findall('.//sec'):
    title=s.find('title')
    if title is not None:
        name=''.join(title.itertext())
        if name.lower() in ('participants','task','behavioral task','task design','experimental task'):
            print(name, ''.join(s.itertext()))
