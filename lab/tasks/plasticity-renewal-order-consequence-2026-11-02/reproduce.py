"""Explicit later reproduction into a new child directory, same frozen science.

Not run by the investigation. Only resets the expired operational wall deadline;
it does not change seeds, data, arms, margins, update order or earned outputs.
"""
import argparse
import hashlib
import json
from pathlib import Path
import re
import resource
import time

import run


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--label',required=True)
    args=parser.parse_args()
    if not re.fullmatch(r'[A-Za-z0-9_-]{1,60}',args.label):
        raise ValueError('label must be a short plain directory name')
    earned=Path(__file__).resolve().parent
    dest=earned/'reproductions'/args.label
    dest.mkdir(parents=True,exist_ok=False)
    receipt=json.loads((earned/'EXECUTION_RECEIPT.json').read_bytes())
    assert hashlib.sha256((earned/'FREEZE.md').read_bytes()).hexdigest()==receipt['freeze_sha256']
    for relative,expected in receipt['code'].items():
        assert hashlib.sha256((earned.parent/relative).read_bytes()).hexdigest()==expected['sha256']
    run.ROOT=dest
    run.START=time.perf_counter()
    run.DEADLINE=time.time()+1680
    (dest/'REPRODUCTION_RECEIPT.json').write_text(json.dumps(dict(
        utc=time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),source_receipt=receipt,
        change='new output directory and bounded current wall deadline only',runtime_limit_seconds=1680),indent=2)+'\n')
    checks=[]
    for seed in run.SEEDS:
        run.check_limits()
        run.one_teacher(seed)
        actual=json.loads((dest/f'OUTPUT_{seed}.json').read_bytes())
        original=json.loads((earned/f'OUTPUT_{seed}.json').read_bytes())
        fields=['realization_sha256','steps','replacements','compensation','summaries',
                'risk_matrices','learner_snapshots','online_1000_bins','cache_final','reservoir_final','sampled_events']
        equal={field:actual[field]==original[field] for field in fields}
        checks.append(dict(seed=seed,exact_scientific_fields=equal))
        (dest/'REPRODUCTION_CHECKS.json').write_text(json.dumps(dict(
            checks=checks,seconds=time.perf_counter()-run.START,
            max_rss_bytes_macos=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss),indent=2)+'\n')
        assert all(equal.values()),'Reproduction differed; preserve outputs and diagnose, do not overwrite earned results'
    print(json.dumps(dict(status='PASS',teachers=8,output=str(dest))),flush=True)


if __name__=='__main__':
    main()
