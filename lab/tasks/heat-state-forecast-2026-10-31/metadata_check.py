"""Outcome-blind materialization of the declared heat animal partition."""
import json, pathlib, hashlib, datetime
ROOT = pathlib.Path(__file__).resolve().parents[3]
TASK = pathlib.Path(__file__).resolve().parent
SRC = ROOT / 'sources/heat_state_forecast_2026-10-31'
m = json.loads((SRC/'heat-metadata.json').read_text())
old = json.loads((ROOT/'experiments/neural_dynamics/selection.json').read_text())
protected = {pathlib.Path(x['path']).stem.split('atanas_kim_2023-')[1] for x in old['validation']}
consumed_baseline = {pathlib.Path(x['path']).stem.split('atanas_kim_2023-')[1] for x in old['discovery']}
items=[]
for x in m['heat']:
    uid=pathlib.Path(x['path']).stem.split('atanas_kim_2023-')[1]
    assert uid not in protected and uid not in consumed_baseline
    items.append(dict(x,uid=uid,split_hash=hashlib.sha256(('heat-state-v1:'+uid).encode()).hexdigest()))
items.sort(key=lambda x:x['split_hash'])
k=2*len(items)//3
for i,x in enumerate(items): x['part']='development' if i<k else 'evaluation'
assert len(items)-k>=6
split=dict(frozen_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),repo=m['repo'],commit=m['commit'],rule='ascending SHA256(heat-state-v1:UID), first floor(2N/3) development',items=items)
(TASK/'SPLIT.json').write_text(json.dumps(split,indent=2)+'\n')
summary=dict(at_utc=split['frozen_utc'],heat_animals=len(items),development=k,evaluation=len(items)-k,overlap_protected=0,overlap_consumed_baseline=0,total_payload_bytes=sum(x['size'] for x in items),development_payload_bytes=sum(x['size'] for x in items[:k]),evaluation_payload_bytes=sum(x['size'] for x in items[k:]),development_uids=[x['uid'] for x in items[:k]],evaluation_uids=[x['uid'] for x in items[k:]],new_outcomes_decoded=0,prior_exposure='all19 published/mirror summaries; no lab-specific heat scores found in ordinary-note search; no status reset')
(TASK/'METADATA_CHECK.json').write_text(json.dumps(summary,indent=2)+'\n')
print(json.dumps(summary,indent=2))
