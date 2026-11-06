"""Hash exact admitted inputs and completed owned reproduction artifacts."""
import os,sys
sys.dont_write_bytecode=True
for k in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','VECLIB_MAXIMUM_THREADS'):os.environ[k]='2'
import json,hashlib
from common import ROOT,HERE,SOURCE,read,save,now

def main():
    records=[]
    original=[]
    for plant in (100,101,102):
        base=ROOT/('campaigns/evaluator_optimization_2026-10-28/primary_snapshots/plant_%03d'%plant)
        original.extend([base/'state.pkl',base/'inputs.npz',base/'preparation.json'])
    owned=[p for p in HERE.iterdir() if p.is_file() and p.suffix in ('.py','.md','.json') and p.name not in ('READS.json','MANIFEST.json','STATE.md')]
    owned+=sorted((HERE/'outputs').iterdir())
    owned+=[p for p in SOURCE.iterdir() if p.is_file() and p.suffix in ('.pkl','.npz')]
    for path in original+sorted(set(owned)):
        if not path.is_file():continue
        kind='admitted_input_hash' if path in original else 'owned_artifact_hash'
        data=read(path,kind);records.append({'path':str(path.relative_to(ROOT)),'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest(),'kind':kind})
    selection=json.loads(read(ROOT/'experiments/neural_dynamics/selection.json','source_selection'))
    ledger=json.loads((HERE/'READS.json').read_text())
    out={'time':now(),'artifacts':records,'original_worm_git_blob_pins':selection['discovery'],
         'source_commits':{'vocal_error_network':'8309db5b1e2abb0d937fec7a1f9d434b06a9bd7c','processed_worm_mirror':'513782b42ad77e75f35adfbc70064b7418ff674a'},
         'remote_commands':15,'remote_acquisition_accounting':'15MB conservative text allowance; exact wire counts unavailable; no numerical dataset acquisition',
         'decoded_input_read_bytes':ledger['total_bytes'],'decoded_input_read_cap':1000000000,
         'excluded_mutable_records':['STATE.md','READS.json','MANIFEST.json'],
         'license_scope':'See SOURCES.md; upstream code/mirror redistribution licenses not independently certified; locally generated artifacts remain in this workspace'}
    assert ledger['total_bytes']<=1000000000
    save('MANIFEST.json',out)
    print(json.dumps({'artifacts':len(records),'decoded_input_read_bytes':ledger['total_bytes'],'time':out['time']}))

if __name__=='__main__':main()
