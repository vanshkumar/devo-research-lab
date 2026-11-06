"""Bounded one-file source acquisition and measured-data schema inspection."""
import os
for key in ('OPENBLAS_NUM_THREADS', 'OMP_NUM_THREADS', 'MKL_NUM_THREADS', 'VECLIB_MAXIMUM_THREADS', 'NUMEXPR_NUM_THREADS'):
    os.environ[key] = '1'
import hashlib
import json
from pathlib import Path
import resource
import sys
import urllib.request
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parent
SOURCE = ROOT / 'sources'
SOURCE.mkdir(exist_ok=True)
URL = 'https://raw.githubusercontent.com/mattgolub/bci_learning/3e6f00c959096189dd77df57ceb9eb540da83f76/exampleData.mat'
PATH = SOURCE / 'exampleData.mat'
ledger = {'url': URL, 'timestamp_utc': datetime.now(timezone.utc).isoformat(), 'public_operations': 0}
cache_hit = PATH.exists()
if cache_hit and (ROOT / 'ACQUIRE_EXAMPLE.json').exists():
    ledger = json.loads((ROOT / 'ACQUIRE_EXAMPLE.json').read_text())
if not PATH.exists():
    ledger['public_operations'] = 1
    try:
        with urllib.request.urlopen(URL, timeout=30) as response:
            ledger['status'] = response.status
            ledger['headers'] = dict(response.headers)
            body = response.read(1000001)
            ledger['response_body_bytes'] = len(body)
            if len(body) > 1000000:
                raise RuntimeError('One-file cap exceeded')
            PATH.write_bytes(body)
    except Exception as exc:
        ledger['error'] = repr(exc)
        (ROOT / 'ACQUIRE_EXAMPLE.json').write_text(json.dumps(ledger, indent=2) + '\n')
        raise
body = PATH.read_bytes()
ledger['file_bytes'] = len(body)
ledger['sha256'] = hashlib.sha256(body).hexdigest()
ledger['git_blob_sha1'] = hashlib.sha1(('blob %d\0' % len(body)).encode() + body).hexdigest()
assert len(body) == 252829
assert ledger['git_blob_sha1'] == '8fef1e48e8515665b5a162f6ad6aeb7d2c5ada76'
if not cache_hit:
    (ROOT / 'ACQUIRE_EXAMPLE.json').write_text(json.dumps(ledger, indent=2) + '\n')

sys.path.insert(0, str(ROOT.parents[2] / '.venv/lib/python3.9/site-packages'))
import numpy as np
from scipy.io import loadmat

data = loadmat(PATH, simplify_cells=True, variable_names=['expParams', 'beforeLearning'])
def schema(value, depth=0):
    if isinstance(value, dict):
        return {key: schema(val, depth+1) for key, val in value.items() if not key.startswith('__')}
    if isinstance(value, np.ndarray):
        result = {'shape': list(value.shape), 'dtype': str(value.dtype)}
        if value.dtype == object and depth < 5:
            result['members'] = [schema(item, depth+1) for item in value.flat]
        return result
    return value if isinstance(value, (str, float, int)) else str(type(value))

out = {'timestamp_utc': datetime.now(timezone.utc).isoformat(), 'source': ledger,
       'schema': schema(data), 'numpy_version': np.__version__,
       'peak_rss_bytes': resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
       'status': 'SCHEMA_ONLY; decoder arithmetic not yet performed',
       'exposure': 'beforeLearning and expParams decoded; afterLearning not requested'}
(ROOT / 'EXAMPLE_SCHEMA.json').write_text(json.dumps(out, indent=2) + '\n')
print(json.dumps(out, indent=2))
