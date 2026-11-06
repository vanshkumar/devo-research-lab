"""Full offline rerun in a new owned subdirectory; not run during this allocation.

Consumes fresh compute/read budget, without producing fresh validation data.
"""
import argparse
import importlib
import pathlib
import shutil
import analysis

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--name',default='offline_reproduction')
    a=ap.parse_args()
    assert pathlib.Path(a.name).name==a.name
    source=analysis.ROOT
    destination=source/a.name
    destination.mkdir(exist_ok=False)
    (destination/'sources').mkdir()
    for name in ['analysis.py','first_data_check.py','controls.py','audit.py','contrary.py',
                 'DEVELOPMENT_PLAN.md','PROTOCOL.md','SOURCE_CERTIFICATION.json','CONTRARY_PLAN.md']:
        shutil.copyfile(source/name,destination/name)
    shutil.copyfile(source/'sources/experiment2.zip',destination/'sources/experiment2.zip')
    analysis.ROOT=destination
    analysis.pilot()
    analysis.freeze()
    controls=importlib.import_module('controls')
    controls.ROOT=destination
    controls.main()
    analysis.evaluate()
    audit=importlib.import_module('audit')
    audit.ROOT=destination
    audit.main('post')
    contrary=importlib.import_module('contrary')
    contrary.ROOT=destination
    contrary.freeze()
    contrary.score()
    print('OFFLINE_REPRODUCTION_COMPLETE',destination)

if __name__=='__main__':
    main()
