"""Replay independent work into a fresh subdirectory, keeping canonical outputs."""
import argparse
import pathlib
import re
import shutil
import review
import independent_source

ap=argparse.ArgumentParser()
ap.add_argument('--name',required=True)
ap.add_argument('--stage',choices=['audit','all'],default='audit')
args=ap.parse_args()
assert re.fullmatch(r'[a-zA-Z0-9_-]+',args.name), 'simple new directory name required'
canonical=pathlib.Path(__file__).resolve().parent
target=canonical/args.name
assert not target.exists(), 'refuse to overwrite any reproduction'
target.mkdir()
for name in ['review.py','independent_source.py','CONTRARY_PLAN.md']:
    shutil.copyfile(canonical/name,target/name)
review.HERE=target
independent_source.HERE=target
if args.stage=='all':
    independent_source.main()
review.audit()
if args.stage=='all':
    review.reconstruct_controls()
    review.freeze()
    review.diagnostic()
print('Reproduction saved under',target)
