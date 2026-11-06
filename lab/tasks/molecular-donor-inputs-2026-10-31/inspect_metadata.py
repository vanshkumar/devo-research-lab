"""Inspect only acquired public JSON metadata, never expression payloads."""
import hashlib
import json
from pathlib import Path
import re
import sys

root = Path(__file__).resolve().parent
out = []
for label in sys.argv[1:]:
    data = (root / 'sources' / (label + '.bin')).read_bytes()
    if data.lstrip().startswith((b'{', b'[')):
        value = json.loads(data)
    else:
        html = data.decode('utf-8', errors='replace')
        value = {'relevant_links': re.findall(r'href="([^"]*(?:cellxgene|doi.org|repository.cam)[^"]*)"', html)}
    if label == 'cellxgene_collections':
        ids = {'dbb4e1ed-d820-4e83-981f-88ef7eb55a35', 'a2c833f7-b7f1-4f4d-ad31-cae478b601b7'}
        value = {'source_index_collection_count': len(value),
                 'matched_collections': [x for x in value if ids.intersection(d.get('dataset_id') for d in x.get('datasets', []))]}
    rec = {'label': label, 'read_bytes': len(data), 'sha256': hashlib.sha256(data).hexdigest()}
    if 'data' in value and isinstance(value['data'], dict) and 'attributes' in value['data']:
        attrs = value['data']['attributes']
        rec['datacite'] = {k: attrs.get(k) for k in ('url', 'titles', 'descriptions', 'rightsList', 'sizes', 'formats', 'contentUrl')}
    else:
        rec['value'] = value
    out.append(rec)
dest = root / ('METADATA_' + '_'.join(sys.argv[1:]) + '.json')
dest.write_text(json.dumps(out, indent=2) + '\n')
compact = []
for rec in out:
    val = rec.get('value', {})
    if '_embedded' in val:
        entities = next(iter(val['_embedded'].values()))
        compact.append({'label': rec['label'], 'page': val.get('page'),
                        'entries': [{k: x.get(k) for k in ('uuid', 'name', 'sizeBytes', 'checkSum', '_links')} for x in entities]})
    elif 'metadata' in val:
        compact.append({'label': rec['label'], 'name': val.get('name'), 'handle': val.get('handle'),
                        'metadata': {k: v for k, v in val['metadata'].items() if any(s in k for s in ('description', 'format', 'rights', 'relation'))}, '_links': val.get('_links')})
    else:
        compact.append(rec)
print(json.dumps(compact, indent=2))
