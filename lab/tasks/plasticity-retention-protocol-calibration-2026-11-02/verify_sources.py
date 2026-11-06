"""Verify only this task's provider-transcribed source against saved Git blobs."""
import ast
import hashlib
import json
from pathlib import Path
import resource
import time

ROOT = Path(__file__).resolve().parent
PREVIOUS = ROOT.parent / 'plasticity-retention-source-benchmark-2026-11-02'


def main():
    started = time.perf_counter()
    tree_bytes = (PREVIOUS / 'SOURCE_TREE.json').read_bytes()
    tree = {e['path']: e for e in json.loads(tree_bytes)['tree']}
    out = []
    for path in sorted((ROOT / 'vendor').rglob('*')):
        if not path.is_file():
            continue
        key = str(path.relative_to(ROOT / 'vendor'))
        payload = path.read_bytes()
        size = tree[key]['size']
        if len(payload) > size and not payload[size:].strip(b'\n'):
            payload = payload[:size]
            path.write_bytes(payload)
        actual = hashlib.sha1(b'blob ' + str(len(payload)).encode() + b'\0' + payload).hexdigest()
        out.append(dict(path=key, bytes=len(payload), sha256=hashlib.sha256(payload).hexdigest(),
                        actual_blob_sha1=actual, expected_blob_sha1=tree[key]['sha'],
                        verified=(actual == tree[key]['sha'])))
    imports = []
    for base, name in [(PREVIOUS / 'vendor', 'lop/algos/cbp.py'),
                       (PREVIOUS / 'vendor', 'lop/algos/gnt.py'),
                       (ROOT / 'vendor', 'lop/utils/AdamGnT.py')]:
        source = (base / name).read_text()
        imports.append({'path': name, 'imports': [ast.unparse(node) for node in ast.parse(source).body
                                                if isinstance(node, (ast.Import, ast.ImportFrom))]})
    result = dict(commit='3138c5556859e0e2918d40f113b40699b6575cfa', files=out,
                  imports=imports, dependencies_installed=0, author_torch_execution='UNRUN',
                  source_tree_read_bytes=len(tree_bytes),
                  seconds=time.perf_counter() - started,
                  max_rss_bytes_macos=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
    (ROOT / 'SOURCE_MANIFEST.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result))
    assert all(row['verified'] for row in out)


if __name__ == '__main__':
    main()
