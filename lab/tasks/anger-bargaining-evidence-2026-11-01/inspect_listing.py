import json, sys
from pathlib import Path
p=Path(__file__).resolve().parent/'sources'/sys.argv[1]
d=json.loads(p.read_text())
print(json.dumps([{'id':x['id'], 'name':x['attributes']['name'],
 'size':x['attributes']['size'], 'hashes':x['attributes'].get('extra',{}).get('hashes',{}),
 'download':x['links'].get('download')} for x in d['data']],indent=2))
