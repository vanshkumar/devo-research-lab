"""Read and receipt helpers confined to the two independent review jobs."""
from collections import Counter
from datetime import datetime, timezone
import hashlib
import io
import json
import os
from pathlib import Path
import resource
import sys
import time

START_CPU = time.process_time()
START_WALL = time.monotonic()
HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
AUTHOR = ROOT / 'lab/tasks/independent-acquisition-confirmation-2026-11-05'
SOURCE = ROOT / 'lab/tasks/independent-acquisition-cohort-2026-11-05'
DEADLINE = datetime.fromisoformat('2026-11-05T22:32:57+00:00')
CHARGES = Counter()
PINS = {}

import numpy as np


def read(path, expected=None):
    payload = path.read_bytes()
    CHARGES['explicit_file_bytes'] += len(payload)
    digest = hashlib.sha256(payload).hexdigest()
    if expected is not None and digest != expected:
        raise ValueError(f'SHA256 mismatch for {path}')
    PINS[str(path.relative_to(ROOT))] = digest
    return payload


def read_json(path, expected=None):
    return json.loads(read(path, expected))


def read_jsonl(path):
    return [json.loads(line) for line in read(path).splitlines()]


def arrays(path, *keys):
    with np.load(io.BytesIO(read(path)), allow_pickle=False) as archive:
        result = {key: archive[key] for key in keys}
    CHARGES['decoded_npz_arrays_bytes'] += sum(arr.nbytes for arr in result.values())
    return result


def serialize(value):
    if isinstance(value, np.ndarray):
        return value.tolist()
    if isinstance(value, np.generic):
        return value.item()
    raise TypeError(type(value))


def save(filename, data):
    with (HERE / filename).open('x') as out:
        json.dump(data, out, indent=2, default=serialize, allow_nan=False)
        out.write('\n')


def check_budget(prior=0, limit=1_850_000_000):
    if prior + sum(CHARGES.values()) >= limit:
        raise RuntimeError('Conservative scoped read/decode checkpoint')
    if datetime.now(timezone.utc) >= DEADLINE or time.process_time() - START_CPU >= 3_200:
        raise RuntimeError('Scoped elapsed or CPU checkpoint')


def run(stage, fn):
    # Use a distinct tag on a permitted recovery to retain failed receipts.
    tag = sys.argv[1] if len(sys.argv) == 2 else stage
    receipt = HERE / f'{tag}_RESOURCE.json'
    assert not receipt.exists(), receipt
    error = None
    try:
        fn()
    except BaseException as exc:
        error = repr(exc)
        raise
    finally:
        save(receipt.name, dict(
            utc=datetime.now(timezone.utc).isoformat(), pid=os.getpid(), job=stage,
            status='complete' if error is None else 'failed', error=error,
            cpu_seconds=time.process_time() - START_CPU,
            process_wall_seconds=time.monotonic() - START_WALL,
            peak_RSS_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
            accounting=CHARGES, explicit_nominal_decoded_read_bytes=sum(CHARGES.values()),
            public_ingress_bytes=0, physical_provider_import_IO='unknown',
            input_sha256=PINS))
