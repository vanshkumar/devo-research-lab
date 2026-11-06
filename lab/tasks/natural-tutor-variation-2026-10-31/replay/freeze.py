"""Hash the finite protocol/code/allocation, before evaluation. No outcome decoding."""
import datetime,hashlib,json,pathlib,resource
ROOT=pathlib.Path(__file__).resolve().parent
def main():
    assert not (ROOT/'FREEZE.json').exists()
    names=sorted(p.name for p in (ROOT/'sources/annotations').glob('*.csv'))
    assert len(names)==39
    pins=[]
    for rel in ['PROTOCOL.md','development.py','evaluate.py','freeze.py','DEVELOPMENT.json']+['sources/annotations/'+n for n in names]:
        b=(ROOT/rel).read_bytes();pins.append({'path':rel,'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest()})
    obj={'timestamp':datetime.datetime.now(datetime.timezone.utc).isoformat(),'motif':['a','b','c'],
      'teaching':names[:19],'main_evaluation':names[19:29],'revision_evaluation':names[29:],
      'pins':pins,'peak_rss_bytes':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss}
    (ROOT/'FREEZE.json').write_text(json.dumps(obj,indent=2)+'\n')
    ledger=json.loads((ROOT/'ACQUISITION.json').read_text());charge=sum(x['bytes'] for x in pins)
    ledger['scientific_read_decoded_hash_bytes']+=charge
    ledger['scientific_byte_passes'].append({'operation':'main freeze','kind':'hash pins','bytes':charge})
    (ROOT/'ACQUISITION.json').write_text(json.dumps(ledger,indent=2)+'\n')
    print(json.dumps({'timestamp':obj['timestamp'],'pins':len(pins),'hash_read_bytes':charge,
      'teaching_files':len(names[:19]),'main_files':len(names[19:29]),'revision_files':len(names[29:])}))
if __name__=='__main__':main()
