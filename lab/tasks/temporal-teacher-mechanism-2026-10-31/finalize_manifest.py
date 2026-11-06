"""Inventory completed artifacts without rereading already hashed inputs."""
import sys
sys.dont_write_bytecode=True
import json,hashlib
from common import ROOT,HERE,SOURCE,read,save,now

def main():
    known=json.loads((HERE/'INPUT_MANIFEST.json').read_text());freeze=json.loads((HERE/'FREEZE.json').read_text())
    for name,digest in freeze['hashes'].items():
        assert hashlib.sha256(read(ROOT/name,'final_frozen_code_check')).hexdigest()==digest,name
    files=[]
    for root in (HERE,SOURCE):
        for p in sorted(root.rglob('*')):
            if not p.is_file() or any(x in p.parts for x in ('__pycache__','numba_cache','mpl_cache')):continue
            if p.name in ('MANIFEST.json','READS.json'):continue
            name=str(p.relative_to(ROOT));entry={'path':name,'bytes':p.stat().st_size}
            if name in known:entry['sha256']=known[name]['sha256'];entry['hash_from']='same-byte scientific input read'
            elif p.name.endswith('_circuits.pkl'):
                entry['sha256']=None;entry['hash_from']='unread redundant local pickle; verified numerical packs and frozen generation seeds are primary'
            else:
                ledger=json.loads((HERE/'READS.json').read_text())
                if ledger['additional_bytes']+p.stat().st_size>187000000:
                    entry['sha256']=None;entry['hash_from']='inventory only to preserve closing read reserve; not a primary held model/query input'
                else:entry['sha256']=hashlib.sha256(read(p,'artifact_manifest_hash')).hexdigest();entry['hash_from']='charged bookkeeping reopen'
            files.append(entry)
    primary=[x for x in files if '/held_' in x['path'] and not x['path'].endswith('_circuits.pkl')]
    assert all(x['sha256'] is not None for x in primary),'primary held artifact missing hash'
    ledger=json.loads((HERE/'READS.json').read_text())
    envelope=ledger['known_prior_bytes']+ledger['review_reserved_remaining_bytes']+ledger['additional_bytes']
    save('MANIFEST.json',{'utc':now(),'files':files,'primary_held_artifacts':len(primary),'source_licenses':'SOURCES.md',
                         'additional_read_bytes':ledger['additional_bytes'],'actual_lineage_read_bytes':ledger['known_prior_bytes']+ledger['additional_bytes'],
                         'lineage_with_remaining_review_reservation':envelope,'global_cap':1000000000,'main_cap':190000000,
                         'excluded_mutable_files':['MANIFEST.json','READS.json'],'excluded_runtime_caches':['__pycache__','numba_cache','mpl_cache']})
    print(json.dumps({'files':len(files),'primary_held_artifacts':len(primary),'additional_bytes':ledger['additional_bytes'],
                      'lineage_actual':ledger['known_prior_bytes']+ledger['additional_bytes'],'lineage_reserved_envelope':envelope,'global_slack':1000000000-envelope}),flush=True)
if __name__=='__main__':main()
