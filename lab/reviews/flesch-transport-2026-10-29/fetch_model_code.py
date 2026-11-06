"""One bounded lookup of the publication-linked model repository; code/metadata only."""
import hashlib
import json
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent
PER_FILE = 2_000_000
AGGREGATE = 3_000_000
BASE = 'https://api.github.com/repos/summerfieldlab/Flesch_Nagy_etal_HebbCL'
LOG = ROOT / 'model_access.json'
records = json.loads(LOG.read_text()) if LOG.exists() else []

def get(name, url):
    req = urllib.request.Request(url, headers={'User-Agent': 'bounded-independent-review/1.0', 'Accept-Encoding': 'identity'})
    used = sum(x.get('bytes', 0) for x in records)
    limit = min(PER_FILE, AGGREGATE - used)
    if limit <= 0:
        raise RuntimeError('aggregate cap')
    rec = {'name': name, 'url': url}
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            body = r.read(limit + 1)
            rec.update(status=r.status, bytes=len(body))
            if len(body) > limit:
                raise RuntimeError('byte cap exceeded; no content saved')
        rec['sha256'] = hashlib.sha256(body).hexdigest()
        (ROOT / name).write_bytes(body)
        return body
    except Exception as e:
        rec['error'] = type(e).__name__ + ': ' + str(e)
        raise
    finally:
        records.append(rec)
        LOG.write_text(json.dumps(records, indent=2) + '\n')

if len(sys.argv) == 1:
    ref = json.loads(get('model_ref.json', BASE + '/commits/HEAD'))
    sha = ref['sha']
    tree = json.loads(get('model_tree.json', BASE + '/git/trees/' + sha + '?recursive=1'))
    print('commit', sha, 'truncated', tree.get('truncated'), 'entries', len(tree.get('tree', [])))
    for item in tree.get('tree', []):
        if item['type'] == 'blob' and item['path'].lower().endswith(('.py', '.md', '.m', '.txt')):
            print(item['path'], item.get('size'), item['sha'])
else:
    ref = json.loads((ROOT / 'model_ref.json').read_text())
    entries = {x['path']: x for x in json.loads((ROOT / 'model_tree.json').read_text())['tree']}
    for path in sys.argv[1:]:
        item = entries[path]
        if item['type'] != 'blob' or not path.lower().endswith(('.py', '.md', '.m')):
            raise RuntimeError('not allowlisted source code')
        if item['size'] > PER_FILE:
            raise RuntimeError('declared per-file cap')
        name = 'model_code__' + path.replace('/', '__')
        body = get(name, 'https://raw.githubusercontent.com/summerfieldlab/Flesch_Nagy_etal_HebbCL/' + ref['sha'] + '/' + path)
        gitsha = hashlib.sha1(('blob %d\0' % len(body)).encode() + body).hexdigest()
        if gitsha != item['sha']:
            raise RuntimeError('Git blob mismatch')
        print(name, len(body), 'git_blob_ok')
print('new repository bytes', sum(x.get('bytes', 0) for x in records))
