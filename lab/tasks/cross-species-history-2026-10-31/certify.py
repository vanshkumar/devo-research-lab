"""Audit only authoritative old allocation/exposure metadata; no raw outcomes."""
from pathlib import Path
import json, hashlib, csv, datetime
from collections import Counter, defaultdict

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent
MOUSE = ROOT/'campaigns/learning_rule_transport_2026-10-28'
HUMAN = ROOT/'campaigns/human_learning_routes_2026-10-28'

def main():
    paths = [MOUSE/'protocols/SPLIT.json', MOUSE/'protocols/EXPOSURE.jsonl',
             MOUSE/'protocols/VALIDATION_STATUS.json', MOUSE/'data/INDEX.json',
             MOUSE/'data/ROW_COUNTS.json', HUMAN/'protocol/split_manifest.csv',
             HUMAN/'protocol/VALIDATION_OPENED.json', HUMAN/'acquisition/MANIFEST.json']
    pins = []
    for p in paths:
        b=p.read_bytes()
        pins.append(dict(path=str(p.relative_to(ROOT)),bytes=len(b),sha256=hashlib.sha256(b).hexdigest()))
    split=json.loads(paths[0].read_text())
    ev=[json.loads(x) for x in paths[1].read_text().splitlines() if x.strip()]
    opens=[x for x in ev if x.get('event')=='open_outcomes']
    consumed=defaultdict(list)
    for x in opens: consumed[x.get('split')].append(x.get('subject'))
    report=dict(pins=pins,event_counts=dict(Counter(x.get('event') for x in ev)),
                full_open_ids={k:sorted(set(v)) for k,v in consumed.items()},
                representative_open=opens[:2],representative_last=opens[-2:],
                human_files=[str(p.relative_to(ROOT)) for p in (HUMAN/'inputs').iterdir() if p.is_file()],
                mouse_processed_dirs=[dict(split=p.name,files=[f.name for f in p.glob('*.npz')])
                                      for p in (MOUSE/'data/processed').iterdir() if p.is_dir()],
                metadata_read_bytes=sum(x['bytes'] for x in pins))
    (OUT/'AUTHORITY_AUDIT.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({k:v for k,v in report.items() if k!='mouse_processed_dirs'},indent=2))
    print('processed_counts',[(r['split'],len(r['files'])) for r in report['mouse_processed_dirs']])
    full_ids={x['subject'] for x in opens if x.get('scope')=='all indexed trials for this subject'}
    assert len(full_ids)==122
    assert len(set(consumed['dev']))==74
    rows={x['eid']:int(x['rows']) for x in json.loads((MOUSE/'data/ROW_COUNTS.json').read_text())}
    index=json.loads((MOUSE/'data/INDEX.json').read_text())
    processed_events={x['subject']:x for x in ev if x.get('event')=='load_processed_outcomes'}
    allowed=[]
    for s in split['standard']:
        if s['subject'] not in full_ids:continue
        rs=sorted([x for x in index if x['subject']==s['subject'] and x['kind']=='table'],key=lambda x:(x['date'],x['number']))
        offset=0;links=[]
        for r in rs:
            n=rows[r['eid']]
            take=max(0,min(n,6000-offset))
            if take:links.append(dict(path=str((MOUSE/r['path']).relative_to(ROOT)),eid=r['eid'],dataset_id=r['dataset_id'],
                                      date=r['date'],number=r['number'],protocol=r['protocol'],rows=[0,take],global_start=offset,full_rows=n))
            offset+=n
        pe=processed_events[s['subject']]
        p=MOUSE/pe['path']
        assert p.is_file()
        allowed.append(dict(subject=s['subject'],species='mouse',old_split=s['split'],lab=s['lab'],
                            path=str(p.relative_to(ROOT)),expected_sha256=pe['sha256'],compressed_bytes=p.stat().st_size,
                            allowed_rows=[0,min(6000,offset)],indexed_total_rows=offset,
                            full_payload_previously_consumed=True,source_rows=links))
    with (HUMAN/'protocol/split_manifest.csv').open() as f:hs=list(csv.DictReader(f))
    assert len(hs)==80 and len({x['subject'] for x in hs})==80
    for s in hs:
        part=s['partition']
        path=HUMAN/'inputs'/('development_numeric.csv' if part=='development' else 'validation_numeric.csv')
        allowed.append(dict(species='human',subject=s['subject'],session=s['session'],schedule=s['schedule'],
                            condition=s['condition'],old_partition=part,path=str(path.relative_to(ROOT)),
                            allowed_rows=[0,600],derivative_linkage='old frozen extraction, split manifest; independently reconstructed prior campaign',
                            source_path=str((HUMAN/'inputs/processed_data_2026.csv').relative_to(ROOT)),
                            source_sha256='45dcce14e30edba5e38eaeaf8c40edb8cd1a0555928070b44779d0d47458bbe9'))
    manifest=dict(created_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
                  authorization='BRIEF plus explicit PI START; consumed development only; first 6000 mouse rows',
                  authority_pins=pins,subjects=allowed,
                  forbidden='All unlisted subjects/rows and protected targets; no old-file edits; no raw downloads',
                  source_metadata_reads_conservative_bytes=20000000)
    (OUT/'ALLOWED_MANIFEST.json').write_text(json.dumps(manifest,indent=2)+'\n')
    print('ALLOWED_MANIFEST saved: mouse122, human80; metadata-only certification before raw science')

if __name__=='__main__':main()
