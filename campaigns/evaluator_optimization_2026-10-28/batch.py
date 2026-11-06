"""Run an explicit finite list of independent plants on local compute."""
import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
import json
from pathlib import Path
import subprocess
import sys
import time

HERE = Path(__file__).resolve().parent


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--plants', type=int, nargs='+', required=True)
    parser.add_argument('--rounds', type=int, choices=[64, 128], default=64)
    parser.add_argument('--jobs', type=int, choices=[1, 2, 3], default=3)
    parser.add_argument('--arms', nargs='+')
    parser.add_argument('--label', required=True)
    args = parser.parse_args()
    if len(set(args.plants)) != len(args.plants):
        raise ValueError('Repeated plant in explicit list')
    start = time.perf_counter()

    def run(plant):
        command = [sys.executable, str(HERE/'run_mixed.py'), '--plant', str(plant),
                   '--rounds', str(args.rounds), '--memoize']
        if args.arms:
            command += ['--arms', *args.arms]
        path = HERE/'logs'/f'{args.label}_{plant}.log'
        if path.exists():
            raise FileExistsError(f'Preserve prior log: {path}')
        with path.open('w') as log:
            result = subprocess.run(command, stdout=log, stderr=subprocess.STDOUT)
        print(json.dumps(dict(plant=plant, returncode=result.returncode,
                              log=str(path), elapsed_seconds=time.perf_counter()-start)), flush=True)
        return result.returncode

    failed = []
    with ThreadPoolExecutor(max_workers=args.jobs) as pool:
        futures = {pool.submit(run, plant): plant for plant in args.plants}
        for future in as_completed(futures):
            if future.result() != 0:
                failed.append(futures[future])
    if failed:
        raise SystemExit(f'Failed plants: {failed}; inspect preserved logs')


if __name__ == '__main__':
    main()
