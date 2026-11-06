"""Bounded public MNIST mirror acquisition. Four HEADs must precede four GETs."""
import hashlib
import json
from pathlib import Path
import resource
import sys
import time
import urllib.request

HERE = Path(__file__).resolve().parent
OBJECTS = [
    ('train-images-idx3-ubyte.gz', 9912422, 'f68b3c2dcbeaaa9fbdd348bbdeb94873'),
    ('train-labels-idx1-ubyte.gz', 28881, 'd53e105ee54ea40749a09fcbcd1e9432'),
    ('t10k-images-idx3-ubyte.gz', 1648877, '9fb629c4189551a2d022fa330f9573f3'),
    ('t10k-labels-idx1-ubyte.gz', 4542, 'ec29112dd5afa0611ce80d1b7f02629c'),
]
BASE = 'https://ossci-datasets.s3.amazonaws.com/mnist/'
phase = sys.argv[1]
assert phase in ('head','get')
if phase == 'get':
    prior = json.loads((HERE/'DATA_HEAD.json').read_text())
    assert len(prior['objects']) == 4 and all(x['ok'] for x in prior['objects'])
    (HERE/'data').mkdir(exist_ok=True)
started = time.perf_counter()
report = {'phase': phase, 'objects': [], 'public_operations': 0, 'application_ingress_bytes': 0}
try:
    for name, expected_size, expected_md5 in OBJECTS:
        url = BASE+name
        entry = {'url': url, 'expected_size': expected_size, 'expected_canonical_md5': expected_md5}
        report['objects'].append(entry)
        report['public_operations'] += 1
        with urllib.request.urlopen(urllib.request.Request(url, method='HEAD' if phase=='head' else 'GET'), timeout=30) as response:
            entry['status'] = response.status
            entry['headers'] = dict(response.headers)
            entry['final_url'] = response.url
            assert response.status == 200
            assert int(response.headers['Content-Length']) == expected_size
            if phase == 'get':
                payload = response.read(expected_size+1)
                report['application_ingress_bytes'] += len(payload)
                entry['bytes'] = len(payload)
                entry['md5'] = hashlib.md5(payload).hexdigest()
                entry['sha256'] = hashlib.sha256(payload).hexdigest()
                assert len(payload) == expected_size and entry['md5'] == expected_md5
                (HERE/'data'/name).write_bytes(payload)
            entry['ok'] = True
finally:
    report['seconds'] = time.perf_counter()-started
    report['max_rss_bytes_macos'] = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    (HERE/('DATA_'+phase.upper()+'.json')).write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps(report, indent=2))
