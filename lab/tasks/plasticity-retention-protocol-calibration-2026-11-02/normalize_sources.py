"""Preserve first failed source audit; extract only the named provider block."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def main():
    original = (ROOT / 'SOURCE_MANIFEST.json').read_bytes()
    (ROOT / 'SOURCE_MANIFEST_FIRST_FAILED.json').write_bytes(original)
    text = (ROOT / 'PRIOR_PROVIDER_EXCERPTS.txt').read_text()
    first = text.split('\n--------------------------------------------------------------------------------')[0]
    lines = []
    for line in first.splitlines():
        if line.startswith('L') and ': ' in line:
            prefix, rest = line.split(': ', 1)
            if prefix[1:].isdigit():
                lines.append(rest)
    payload = ('\n'.join(lines) + '\n').encode()
    target = ROOT / 'vendor/lop/slowly_changing_regression/multi_param_expr.py'
    target.write_bytes(payload)
    cfg = ROOT / 'vendor/lop/slowly_changing_regression/cfg/sgd/cbp/relu.json'
    b = cfg.read_bytes()
    candidates = [(b + b'\n' * n) for n in range(3)]
    expected = 'f19212ea528b0bdefdb275301530b4b2d04e7745'
    for candidate in candidates:
        sha = hashlib.sha1(b'blob ' + str(len(candidate)).encode() + b'\0' + candidate).hexdigest()
        if sha == expected:
            cfg.write_bytes(candidate)
            break
    print(json.dumps({'failed_audit_preserved': True, 'multi_extracted_lines': len(lines),
                      'configuration_suffix_check': sha == expected,
                      'Adam_source': 'provider transcription; byte identity not yet certified'}))


if __name__ == '__main__':
    main()
