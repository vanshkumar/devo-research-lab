"""Sequential matched-field retrieval in ONE process, using listed exact URLs."""
import json, pathlib, runpy, sys
P=pathlib.Path(__file__).resolve().parent
mode=sys.argv[1]; ids=sys.argv[2:]
fields=['ds_name','labels','stim_neurons','stim_volume_i','t'] if mode=='metadata' else ['gcamp']
files={x['name']:x for x in json.loads((P/'SOURCE_CANDIDATES.json').read_text())['files']}
for animal in ids:
    for field in fields:
        name=animal+'_'+field+'.txt'; rec=files[name]
        assert not (P/name).exists()
        sys.argv=[str(P/'acquire.py'),name,rec['url'],str(rec['size']+1000)]
        runpy.run_path(str(P/'acquire.py'),run_name='__main__')
        actual=json.loads((P/'ACQUISITION.json').read_text())['requests'][-1]
        assert actual.get('status')==200 and actual['bytes']==rec['size'] and actual['sha256']==rec['sha256']
