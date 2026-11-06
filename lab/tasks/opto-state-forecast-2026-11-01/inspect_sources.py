import json, pathlib, zipfile, resource
P=pathlib.Path(__file__).resolve().parent
z=zipfile.ZipFile(P/'code_v1.1.zip')
names=z.namelist()
print('CODE candidate files:')
print('\n'.join(n for n in names if any(x in n.lower() for x in ['readme','export','funatlas.py','fconn.py','license'])))
for n in names:
    if n.endswith('README.md') and n.count('/')<=1:
        print('README',n,'\n',z.read(n).decode())
d=json.loads((P/'raw_folder100.json').read_text())
s=[{'name':x['attributes']['name'],'size':x['attributes']['size'],'url':x['links'].get('download'),'sha256':x['attributes']['extra']['hashes']['sha256']} for x in d['data']]
(P/'SOURCE_CANDIDATES.json').write_text(json.dumps({'files':s,'pagination':d['links']},indent=2)+'\n')
print('RAW100',json.dumps(s,indent=2))
print('PAGINATION',d['links'])
print('ACQUISITIONS', [(r['name'],r['bytes'],r.get('error')) for r in json.loads((P/'ACQUISITION.json').read_text())['requests']])
print('RSS',resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
