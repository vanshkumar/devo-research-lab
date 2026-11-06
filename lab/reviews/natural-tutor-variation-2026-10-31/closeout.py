"""Pin review artifacts and conservatively close the finite resource ledger."""
import datetime
import hashlib
import json
from pathlib import Path
import resource

ROOT = Path(__file__).resolve().parent
RESERVE_CHARGE = 95000000

def main():
    resource_bytes = (ROOT/'RESOURCES.json').read_bytes()
    record = json.loads(resource_bytes)
    assert not record.get('closeout_complete'), 'do not double-charge closeout'
    pins = []
    charged = 2*len(resource_bytes)
    for path in sorted(ROOT.iterdir()):
        if not path.is_file() or path.name in ['RESOURCES.json','REVIEW_MANIFEST.json','RETURN_STATUS.json']:
            continue
        b = path.read_bytes()
        charged += 2*len(b)
        pins.append({'path':path.name,'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest()})
    measured = record['scientific_read_decoded_hash_bytes']+charged
    assert measured < RESERVE_CHARGE < record['scientific_byte_cap']
    record['passes'].append({'kind':'closeout file reads/hash and resource JSON decode','bytes':charged})
    record['passes'].append({'kind':'conservative closeout/final inspection/return record allowance',
                             'bytes':RESERVE_CHARGE-measured})
    record['measured_or_explicitly_charged_subtotal_before_final_reserve'] = measured
    record['scientific_read_decoded_hash_bytes'] = RESERVE_CHARGE
    record['combined_author_review_additional_scientific_bytes'] = RESERVE_CHARGE+168914260
    record['peak_rss_bytes'] = max(record['peak_rss_bytes'],resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
    record['closeout_complete'] = True
    record['closeout_timestamp'] = datetime.datetime.now(datetime.timezone.utc).isoformat()
    record['unrun'] = ['numerical waveform/acoustic analysis','perceptual validation/reannotation',
                       'second inferential bird','population/coverage calibration','motor learning',
                       'replacement model','full rerun of new output-routing CLI']
    record['non_scientific_denial'] = 'one ordinary head CSV command denied before payload read; registered scientific script succeeded'
    (ROOT/'REVIEW_MANIFEST.json').write_text(json.dumps({'timestamp':record['closeout_timestamp'],
       'pins':pins,'exclusions':'resource ledger and terminal-delivery record are mutable closeout records'},indent=2)+'\n')
    (ROOT/'RESOURCES.json').write_text(json.dumps(record,indent=2)+'\n')
    print(json.dumps({k:record[k] for k in ['status','closeout_timestamp','scientific_read_decoded_hash_bytes',
             'measured_or_explicitly_charged_subtotal_before_final_reserve','combined_author_review_additional_scientific_bytes','peak_rss_bytes','jobs']},indent=2))
    print('Pinned review artifacts: '+str(len(pins)))

if __name__=='__main__':
    main()
